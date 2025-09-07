#!/usr/bin/env python3
"""
Database Row Streaming Generator
This module provides a generator function to stream user data from MySQL database one row at a time.
Uses Python's yield keyword for memory-efficient data processing.
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


def stream_users():
    """
    Generator function that streams user data from the database one row at a time.
    
    This function uses Python's yield keyword to create a generator that fetches
    and yields database rows on-demand, providing memory-efficient access to
    potentially large datasets.
    
    Yields:
        dict: A dictionary containing user data with keys:
              - user_id (str): UUID of the user
              - name (str): User's full name  
              - email (str): User's email address
              - age (int): User's age
    
    Example:
        >>> for user in stream_users():
        ...     print(user['name'])
        ...     if some_condition:
        ...         break  # Can stop iteration anytime
        
        >>> # Get only first 5 users
        >>> from itertools import islice
        >>> first_five = list(islice(stream_users(), 5))
    
    Note:
        - Uses only one loop as required
        - Memory usage remains constant regardless of database size
        - Connection is properly closed after iteration
        - Handles database connection errors gracefully
    """
    # Establish database connection
    connection = connect_to_prodev()
    
    if connection is None:
        # If connection fails, yield nothing (empty generator)
        return
    
    try:
        # Create cursor for database operations
        cursor = connection.cursor(dictionary=True)  # dictionary=True returns rows as dicts
        
        # Execute query to fetch all users
        # Note: We're not using LIMIT here because the generator handles streaming
        cursor.execute("SELECT user_id, name, email, age FROM user_data")
        
        # This is the single loop required - fetch and yield one row at a time
        for row in cursor:
            # The yield keyword makes this function a generator
            # Each yield pauses execution and returns one row
            # Execution resumes from this point when the next item is requested
            yield {
                'user_id': row['user_id'],
                'name': row['name'], 
                'email': row['email'],
                'age': row['age']
            }
            
    except Error as e:
        print(f"Error streaming users from database: {e}")
        
    finally:
        # Always close database connection and cursor
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Alternative implementation using fetchone() for even more control
def stream_users_alternative():
    """
    Alternative implementation using fetchone() for maximum memory efficiency.
    This version fetches one row at a time from the database cursor.
    """
    connection = connect_to_prodev()
    
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, name, email, age FROM user_data")
        
        # Single loop using fetchone() - fetches one row at a time
        while True:
            row = cursor.fetchone()  # Fetch only one row
            if row is None:  # No more rows
                break
            
            # Yield the row as a dictionary
            yield {
                'user_id': row[0],
                'name': row[1],
                'email': row[2], 
                'age': row[3]
            }
            
    except Error as e:
        print(f"Error streaming users from database: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Utility function to demonstrate generator usage
def demonstrate_generator_benefits():
    """
    Demonstrates the benefits of using generators for database streaming
    """
    print("🔍 Generator Benefits Demonstration")
    print("=" * 50)
    
    # Show that we can process data without loading everything
    print("📊 Processing users one by one:")
    count = 0
    
    for user in stream_users():
        count += 1
        print(f"  {count}. Processing {user['name']} (Age: {user['age']})")
        
        # We can stop anytime without loading remaining data
        if count >= 3:
            print("  ⏹️  Stopping early - remaining data never loaded into memory!")
            break
    
    print(f"\n✅ Processed {count} users using minimal memory")
    
    # Show how to get specific slices
    print(f"\n🔢 Getting users 5-8 using islice:")
    from itertools import islice
    
    users_5_to_8 = list(islice(stream_users(), 4, 8))  # Skip first 4, take next 4
    for i, user in enumerate(users_5_to_8, 5):
        print(f"  {i}. {user['name']}")


if __name__ == "__main__":
    """
    Test the generator function
    """
    print("🚀 Testing Database Streaming Generator")
    print("=" * 60)
    
    # Test basic functionality
    print("📋 First 6 users from stream_users():")
    from itertools import islice
    
    for user in islice(stream_users(), 6):
        print(user)
    
    # Demonstrate generator benefits
    print(f"\n")
    demonstrate_generator_benefits()
