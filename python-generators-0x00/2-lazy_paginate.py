#!/usr/bin/env python3
"""
Lazy Pagination Generator Module
This module provides generators for lazily loading paginated data from the database.
Implements memory-efficient pagination that fetches pages only when needed.
"""

import mysql.connector
from mysql.connector import Error
import os

# Import seed module for database connection
try:
    import seed
except ImportError:
    print("Warning: seed module not found. Make sure seed.py is in the same directory.")
    seed = None

# Load environment variables for database connection
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use default values
    pass


def connect_to_prodev():
    """
    Establishes connection to the ALX_prodev database
    
    Returns:
        connection object to ALX_prodev database if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            database='ALX_prodev',
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to ALX_prodev database: {e}")
        return None


def paginate_users(page_size, offset):
    """
    Fetch a single page of users from the database using LIMIT and OFFSET.
    
    This function implements traditional pagination by fetching a specific page
    of results from the database. It's used by the lazy pagination generator
    to fetch individual pages on demand.
    
    Args:
        page_size (int): Number of users to fetch per page
        offset (int): Number of records to skip (page_size * page_number)
        
    Returns:
        list: List of user dictionaries for the requested page:
              - user_id (str): UUID of the user
              - name (str): User's full name
              - email (str): User's email address
              - age (int): User's age
              
    Example:
        >>> # Get first page (page 0)
        >>> page_1 = paginate_users(10, 0)  # First 10 users
        >>> 
        >>> # Get second page (page 1)
        >>> page_2 = paginate_users(10, 10)  # Next 10 users
        >>> 
        >>> # Get third page (page 2)
        >>> page_3 = paginate_users(10, 20)  # Users 21-30
    
    Note:
        - Uses LIMIT for page size control
        - Uses OFFSET for page positioning
        - Returns empty list if no more data available
        - Properly closes database connection after fetch
    """
    # Use seed module connection if available, otherwise use local connection
    if seed and hasattr(seed, 'connect_to_prodev'):
        connection = seed.connect_to_prodev()
    else:
        connection = connect_to_prodev()
    
    if connection is None:
        print("Error: Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Execute paginated query with LIMIT and OFFSET
        # ORDER BY user_id ensures consistent pagination across calls
        query = "SELECT user_id, name, email, age FROM user_data ORDER BY user_id LIMIT %s OFFSET %s"
        cursor.execute(query, (page_size, offset))
        
        # Fetch all rows for this page
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries (if not already)
        result = []
        for row in rows:
            result.append({
                'user_id': row['user_id'],
                'name': row['name'],
                'email': row['email'],
                'age': row['age']
            })
        
        return result
        
    except Error as e:
        print(f"Error fetching paginated users: {e}")
        return []
        
    finally:
        # Always close the connection
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def lazy_paginate(page_size):
    """
    Generator function that lazily loads pages of user data on demand.
    
    This function implements lazy pagination by yielding pages only when
    requested. It maintains internal state to track the current offset
    and automatically fetches the next page when the iterator continues.
    
    Args:
        page_size (int): Number of users per page
        
    Yields:
        list: A list of user dictionaries for each page:
              - user_id (str): UUID of the user
              - name (str): User's full name
              - email (str): User's email address
              - age (int): User's age
              
    Example:
        >>> # Iterate through all pages lazily
        >>> for page in lazy_paginate(10):
        ...     print(f"Processing page with {len(page)} users")
        ...     for user in page:
        ...         print(f"  - {user['name']}")
        ...     if some_condition:
        ...         break  # Can stop early, remaining pages never loaded
        
        >>> # Get only first 3 pages
        >>> from itertools import islice
        >>> first_three_pages = list(islice(lazy_paginate(50), 3))
        
        >>> # Process pages with different logic
        >>> paginator = lazy_paginate(25)
        >>> first_page = next(paginator)  # Load first page only
        >>> second_page = next(paginator)  # Load second page only when needed
    
    Note:
        - Uses only ONE loop as required
        - Memory usage is constant (only one page loaded at a time)
        - Stops automatically when no more data is available
        - Tracks offset internally across iterations
        - Each page is fetched on-demand, not pre-loaded
    """
    # Validate page size
    if page_size <= 0:
        raise ValueError("Page size must be a positive integer")
    
    # Initialize pagination state
    offset = 0  # Start at the beginning (page 0)
    
    # SINGLE LOOP: Continue until no more pages are available
    while True:
        # Fetch the current page using the paginate_users function
        # This is the lazy part - page is only fetched when needed
        page = paginate_users(page_size, offset)
        
        # If page is empty, we've reached the end of data
        if not page:
            break
        
        # Yield the current page to the caller
        # Execution pauses here until the next page is requested
        yield page
        
        # Update offset for the next page
        # This maintains pagination state across yields
        offset += page_size
        
        # If page is smaller than page_size, it's the last page
        # We can break here for efficiency (optional optimization)
        if len(page) < page_size:
            break


# Alternative name for compatibility with test script
lazy_pagination = lazy_paginate


def demonstrate_lazy_pagination():
    """
    Demonstrates the benefits and usage of lazy pagination
    """
    print("🔍 Lazy Pagination Demonstration")
    print("=" * 50)
    
    # Show pagination with different page sizes
    print("📊 Demonstrating different page sizes:")
    
    page_sizes = [5, 10, 20]
    
    for page_size in page_sizes:
        print(f"\n📄 Page size: {page_size}")
        page_count = 0
        total_users = 0
        
        for page in lazy_paginate(page_size):
            page_count += 1
            total_users += len(page)
            
            print(f"  Page {page_count}: {len(page)} users")
            
            # Show first user in each page
            if page:
                first_user = page[0]
                print(f"    First user: {first_user['name']} (ID: {first_user['user_id'][:8]}...)")
            
            # Only show first 3 pages to avoid spam
            if page_count >= 3:
                print(f"    ... (stopping after 3 pages)")
                break
        
        print(f"  Processed {page_count} pages, {total_users} total users")


def pagination_statistics(page_size):
    """
    Generate statistics about pagination without loading all data into memory
    
    Args:
        page_size (int): Size of each page
        
    Returns:
        dict: Statistics about the paginated data
    """
    stats = {
        'total_pages': 0,
        'total_users': 0,
        'average_page_size': 0,
        'last_page_size': 0
    }
    
    total_size = 0
    
    for page in lazy_paginate(page_size):
        stats['total_pages'] += 1
        page_size_actual = len(page)
        stats['total_users'] += page_size_actual
        total_size += page_size_actual
        stats['last_page_size'] = page_size_actual
    
    if stats['total_pages'] > 0:
        stats['average_page_size'] = total_size / stats['total_pages']
    
    return stats


def compare_pagination_strategies():
    """
    Compare lazy pagination with traditional all-at-once loading
    """
    print("\n⚡ Comparing Pagination Strategies")
    print("=" * 40)
    
    # Strategy 1: Lazy pagination (good)
    print("🚀 Lazy Pagination (Memory Efficient):")
    page_count = 0
    
    for page in lazy_paginate(10):
        page_count += 1
        print(f"  Loaded page {page_count} with {len(page)} users")
        
        # We can stop anytime without loading remaining data
        if page_count >= 3:
            print("  ✅ Stopped early - remaining pages never loaded!")
            break
    
    # Strategy 2: Traditional approach (demonstrates the problem)
    print(f"\n💾 Traditional Approach (Memory Intensive):")
    print("  ❌ Would load ALL pages at once into memory")
    print("  ❌ Memory usage grows with dataset size")
    print("  ❌ Cannot stop early to save resources")
    print("  ✅ Lazy pagination solves all these problems!")


def advanced_pagination_examples():
    """
    Show advanced pagination patterns
    """
    print(f"\n🔧 Advanced Pagination Patterns")
    print("=" * 35)
    
    # Pattern 1: Page-by-page processing with early termination
    print("1. Early termination when condition is met:")
    
    for page_num, page in enumerate(lazy_paginate(15), 1):
        print(f"   Processing page {page_num} ({len(page)} users)")
        
        # Look for a specific condition
        adults_in_page = sum(1 for user in page if user['age'] >= 30)
        print(f"   Found {adults_in_page} adults in this page")
        
        # Stop if we find a page with many adults
        if adults_in_page >= 10:
            print(f"   ✅ Found page with {adults_in_page} adults - stopping!")
            break
        
        if page_num >= 5:  # Safety limit for demo
            break
    
    # Pattern 2: Skip pages based on criteria
    print(f"\n2. Conditional page processing:")
    
    for page_num, page in enumerate(lazy_paginate(20), 1):
        avg_age = sum(user['age'] for user in page) / len(page) if page else 0
        
        if avg_age > 40:
            print(f"   Processing page {page_num} (avg age: {avg_age:.1f})")
            # Process this page
        else:
            print(f"   Skipping page {page_num} (avg age: {avg_age:.1f})")
        
        if page_num >= 3:  # Limit for demo
            break


if __name__ == "__main__":
    """
    Test the lazy pagination functions
    """
    print("🚀 Testing Lazy Pagination Generator")
    print("=" * 60)
    
    # Test basic pagination function
    print("📋 Testing paginate_users(5, 0):")
    first_page = paginate_users(5, 0)
    print(f"First page contains {len(first_page)} users")
    
    if first_page:
        print("First user:", first_page[0])
    
    # Test lazy pagination
    print(f"\n📋 Testing lazy_paginate(3) - first 4 pages:")
    
    page_count = 0
    for page in lazy_paginate(3):
        page_count += 1
        print(f"Page {page_count}: {len(page)} users")
        
        if page_count >= 4:  # Show first 4 pages
            break
    
    # Show demonstrations
    demonstrate_lazy_pagination()
    compare_pagination_strategies()
    advanced_pagination_examples()
    
    # Show statistics
    print(f"\n📊 Pagination Statistics (page_size=25):")
    stats = pagination_statistics(25)
    for key, value in stats.items():
        if 'average' in key:
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
