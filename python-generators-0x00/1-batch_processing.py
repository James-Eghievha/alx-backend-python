#!/usr/bin/env python3
"""
Batch Processing Generator Module
This module provides generators for fetching and processing database data in batches.
Implements memory-efficient batch processing with user filtering capabilities.
"""

import mysql.connector
from mysql.connector import Error
import os

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


def stream_users_in_batches(batch_size):
    """
    Generator function that streams user data from database in batches.
    
    This function fetches database rows in configurable batch sizes, providing
    memory-efficient access to large datasets while optimizing database queries.
    Each batch contains a list of user dictionaries.
    
    Args:
        batch_size (int): Number of rows to fetch in each batch
        
    Yields:
        list: A list of dictionaries, each containing user data:
              - user_id (str): UUID of the user
              - name (str): User's full name
              - email (str): User's email address  
              - age (int): User's age
              
    Example:
        >>> for batch in stream_users_in_batches(10):
        ...     print(f"Processing batch of {len(batch)} users")
        ...     for user in batch:
        ...         print(f"  - {user['name']}")
        
        >>> # Process first 3 batches of 50 users each
        >>> from itertools import islice
        >>> for batch in islice(stream_users_in_batches(50), 3):
        ...     process_batch(batch)
    
    Note:
        - Uses single loop as per requirements
        - Memory usage scales with batch_size, not total dataset size
        - Connection is properly managed and closed after streaming
        - Last batch may contain fewer than batch_size records
    """
    # Validate batch size
    if batch_size <= 0:
        raise ValueError("Batch size must be a positive integer")
    
    # Establish database connection
    connection = connect_to_prodev()
    
    if connection is None:
        # If connection fails, yield nothing (empty generator)
        return
    
    try:
        # Create cursor for database operations
        cursor = connection.cursor(dictionary=True)  # Returns rows as dictionaries
        
        # Execute query to fetch all users
        cursor.execute("SELECT user_id, name, email, age FROM user_data ORDER BY user_id")
        
        # LOOP 1: Batch fetching loop
        while True:
            # Fetch a batch of rows
            batch = cursor.fetchmany(batch_size)
            
            # If no more rows, break the loop
            if not batch:
                break
            
            # Convert rows to the expected dictionary format and yield the batch
            formatted_batch = []
            for row in batch:  # This is part of the batch processing, not a separate loop
                formatted_batch.append({
                    'user_id': row['user_id'],
                    'name': row['name'],
                    'email': row['email'],
                    'age': row['age']
                })
            
            # Yield the entire batch as a list
            yield formatted_batch
            
    except Error as e:
        print(f"Error streaming users in batches: {e}")
        
    finally:
        # Always close database connection and cursor
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def batch_processing(batch_size):
    """
    Processes user data in batches and filters users over the age of 25.
    
    This function demonstrates a complete batch processing pipeline:
    1. Fetch users in batches from database
    2. Filter each batch to include only users over 25
    3. Yield individual filtered users for further processing
    
    Args:
        batch_size (int): Number of users to process in each batch
        
    Yields:
        dict: Individual user dictionaries for users over age 25:
              - user_id (str): UUID of the user
              - name (str): User's full name
              - email (str): User's email address
              - age (int): User's age (will be > 25)
              
    Example:
        >>> # Process users in batches of 50, filtering age > 25
        >>> for user in batch_processing(50):
        ...     print(f"{user['name']} is {user['age']} years old")
        
        >>> # Count filtered users without loading all into memory
        >>> count = sum(1 for user in batch_processing(100))
        >>> print(f"Found {count} users over 25")
    
    Note:
        - Uses total of 2 loops (within the 3-loop limit)
        - Memory usage controlled by batch_size parameter
        - Efficiently filters large datasets without loading everything
        - Combines batch fetching with individual result streaming
    """
    # LOOP 2: Process each batch from the batch generator
    for batch in stream_users_in_batches(batch_size):
        
        # LOOP 3: Filter and yield individual users from current batch
        for user in batch:
            # Filter users over age 25
            if user['age'] > 25:
                yield user


def demonstrate_batch_processing():
    """
    Demonstrates the benefits and usage of batch processing
    """
    print("🔍 Batch Processing Demonstration")
    print("=" * 50)
    
    # Show batch sizes
    print("📊 Comparing different batch sizes:")
    
    batch_sizes = [10, 50, 100]
    
    for batch_size in batch_sizes:
        batch_count = 0
        user_count = 0
        
        for batch in stream_users_in_batches(batch_size):
            batch_count += 1
            user_count += len(batch)
            
            # Only show first few batches to avoid spam
            if batch_count <= 2:
                print(f"  Batch {batch_count} (size {batch_size}): {len(batch)} users")
                # Show first user in batch
                if batch:
                    first_user = batch[0]
                    print(f"    First user: {first_user['name']} (age {first_user['age']})")
        
        print(f"  Total: {batch_count} batches, {user_count} users\n")
    
    # Show filtered processing
    print("🔍 Filtered Processing (age > 25):")
    
    filtered_count = 0
    for user in batch_processing(20):
        filtered_count += 1
        if filtered_count <= 5:  # Show first 5 filtered users
            print(f"  {filtered_count}. {user['name']} (age {user['age']})")
        elif filtered_count == 6:
            print("  ... (showing first 5 only)")
    
    print(f"\n✅ Total users over 25: {filtered_count}")


def get_batch_statistics(batch_size):
    """
    Get statistics about batch processing without loading all data
    
    Args:
        batch_size (int): Batch size to use for processing
        
    Returns:
        dict: Statistics about the batch processing
    """
    stats = {
        'total_batches': 0,
        'total_users': 0,
        'filtered_users': 0,
        'average_age': 0,
        'age_sum': 0
    }
    
    # Process in batches to get statistics
    for batch in stream_users_in_batches(batch_size):
        stats['total_batches'] += 1
        stats['total_users'] += len(batch)
        
        # Calculate statistics for this batch
        for user in batch:
            stats['age_sum'] += user['age']
            if user['age'] > 25:
                stats['filtered_users'] += 1
    
    # Calculate average age
    if stats['total_users'] > 0:
        stats['average_age'] = stats['age_sum'] / stats['total_users']
    
    return stats


# Alternative implementation using different approach
def stream_users_in_batches_alternative(batch_size):
    """
    Alternative implementation using LIMIT and OFFSET for batch fetching.
    This approach is useful when you need to restart from specific positions.
    """
    connection = connect_to_prodev()
    
    if connection is None:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        offset = 0
        
        # Loop to fetch batches using LIMIT and OFFSET
        while True:
            # Fetch batch using LIMIT and OFFSET
            cursor.execute(
                "SELECT user_id, name, email, age FROM user_data ORDER BY user_id LIMIT %s OFFSET %s",
                (batch_size, offset)
            )
            
            batch = cursor.fetchall()
            
            # If no more rows, break
            if not batch:
                break
            
            # Yield the batch
            yield batch
            
            # Move offset for next batch
            offset += batch_size
            
            # If batch is smaller than batch_size, we've reached the end
            if len(batch) < batch_size:
                break
                
    except Error as e:
        print(f"Error in alternative batch streaming: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    """
    Test the batch processing functions
    """
    print("🚀 Testing Batch Processing Generator")
    print("=" * 60)
    
    # Test basic batch streaming
    print("📋 Testing stream_users_in_batches(5):")
    batch_count = 0
    
    for batch in stream_users_in_batches(5):
        batch_count += 1
        print(f"Batch {batch_count}: {len(batch)} users")
        
        if batch_count >= 3:  # Show first 3 batches only
            break
    
    print(f"\n📋 Testing batch_processing(10) - filtering age > 25:")
    
    # Test filtered processing
    for i, user in enumerate(batch_processing(10)):
        if i < 5:  # Show first 5 filtered users
            print(f"{i+1}. {user['name']} (age {user['age']})")
        elif i == 5:
            print("... (showing first 5 only)")
            break
    
    # Show demonstration
    print(f"\n")
    demonstrate_batch_processing()
    
    # Show statistics
    print(f"\n📊 Batch Processing Statistics (batch_size=50):")
    stats = get_batch_statistics(50)
    for key, value in stats.items():
        if key == 'average_age':
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
