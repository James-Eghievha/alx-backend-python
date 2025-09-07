#!/usr/bin/env python3
"""
Memory-Efficient Age Aggregation Module
This module provides generators for streaming user ages and computing
memory-efficient aggregate statistics without loading entire datasets.
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


def stream_user_ages():
    """
    Generator function that streams user ages from the database one by one.
    
    This function implements memory-efficient streaming by yielding individual
    ages rather than loading all ages into memory. It enables processing of
    arbitrarily large datasets with constant memory usage.
    
    Yields:
        int: Individual user age from the database
        
    Example:
        >>> # Calculate average age without loading all data
        >>> total = 0
        >>> count = 0
        >>> for age in stream_user_ages():
        ...     total += age
        ...     count += 1
        >>> average = total / count if count > 0 else 0
        
        >>> # Find maximum age efficiently
        >>> max_age = 0
        >>> for age in stream_user_ages():
        ...     if age > max_age:
        ...         max_age = age
        
        >>> # Count users in age ranges
        >>> age_groups = {'young': 0, 'middle': 0, 'senior': 0}
        >>> for age in stream_user_ages():
        ...     if age < 30:
        ...         age_groups['young'] += 1
        ...     elif age < 60:
        ...         age_groups['middle'] += 1
        ...     else:
        ...         age_groups['senior'] += 1
    
    Note:
        - Uses single database query with streaming cursor
        - Memory usage remains constant regardless of dataset size
        - Processes ages in database order (typically by user_id)
        - Connection properly closed after streaming completes
        - Handles database errors gracefully
    """
    # Establish database connection
    connection = connect_to_prodev()
    
    if connection is None:
        # If connection fails, yield nothing (empty generator)
        return
    
    try:
        # Create cursor for database operations
        cursor = connection.cursor()
        
        # Execute query to fetch only ages (minimizes data transfer)
        # ORDER BY ensures consistent streaming order
        cursor.execute("SELECT age FROM user_data ORDER BY user_id")
        
        # LOOP 1: Stream ages one by one from database
        # This is our first and primary loop for streaming data
        for (age,) in cursor:
            # Yield individual age value
            # The comma in (age,) unpacks the tuple returned by cursor
            yield age
            
    except Error as e:
        print(f"Error streaming user ages: {e}")
        
    finally:
        # Always close database connection and cursor
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def calculate_average_age():
    """
    Calculate average age using memory-efficient streaming.
    
    This function demonstrates how to compute aggregate statistics using
    generators without loading the entire dataset into memory. It uses
    an online algorithm to maintain running totals.
    
    Returns:
        float: Average age of all users, or 0 if no users exist
        
    Example:
        >>> avg_age = calculate_average_age()
        >>> print(f"Average age: {avg_age:.1f}")
        
    Note:
        - Uses O(1) memory regardless of dataset size
        - Processes each age exactly once (single pass)
        - Handles empty dataset gracefully
        - Uses online algorithm for running average calculation
    """
    # Initialize aggregation variables
    total_age = 0      # Running sum of all ages
    user_count = 0     # Running count of users processed
    
    # LOOP 2: Process each streamed age for aggregation
    # This is our second loop for computing the aggregate
    for age in stream_user_ages():
        total_age += age    # Add current age to running total
        user_count += 1     # Increment user counter
    
    # Calculate and return average
    # Handle division by zero for empty dataset
    if user_count > 0:
        return total_age / user_count
    else:
        return 0.0


def demonstrate_streaming_aggregation():
    """
    Demonstrate various streaming aggregation techniques
    """
    print("🔍 Memory-Efficient Aggregation Demonstration")
    print("=" * 55)
    
    # Demonstrate basic statistics without loading all data
    print("📊 Computing statistics using streaming:")
    
    # Initialize counters for various statistics
    total_age = 0
    count = 0
    min_age = float('inf')
    max_age = 0
    age_sum_squares = 0  # For standard deviation
    
    # Age group counters
    age_groups = {
        'teens': 0,      # < 20
        'twenties': 0,   # 20-29
        'thirties': 0,   # 30-39
        'forties': 0,    # 40-49
        'seniors': 0     # 50+
    }
    
    # Single pass through data to compute multiple statistics
    print("  Processing ages stream...")
    for age in stream_user_ages():
        # Basic statistics
        total_age += age
        count += 1
        min_age = min(min_age, age)
        max_age = max(max_age, age)
        age_sum_squares += age * age
        
        # Age group classification
        if age < 20:
            age_groups['teens'] += 1
        elif age < 30:
            age_groups['twenties'] += 1
        elif age < 40:
            age_groups['thirties'] += 1
        elif age < 50:
            age_groups['forties'] += 1
        else:
            age_groups['seniors'] += 1
    
    # Calculate derived statistics
    if count > 0:
        average_age = total_age / count
        variance = (age_sum_squares / count) - (average_age ** 2)
        std_deviation = variance ** 0.5
        
        print(f"\n📈 Computed Statistics:")
        print(f"  Total users: {count}")
        print(f"  Average age: {average_age:.2f}")
        print(f"  Minimum age: {min_age}")
        print(f"  Maximum age: {max_age}")
        print(f"  Standard deviation: {std_deviation:.2f}")
        
        print(f"\n👥 Age Group Distribution:")
        for group, group_count in age_groups.items():
            percentage = (group_count / count) * 100
            print(f"  {group.capitalize()}: {group_count} users ({percentage:.1f}%)")
    else:
        print("  No users found in database")


def streaming_percentiles(percentiles=[25, 50, 75, 90, 95]):
    """
    Calculate percentiles using streaming with minimal memory usage.
    
    Note: This approach uses a sampling method for large datasets.
    For exact percentiles, you'd need to store all values or use
    specialized algorithms like P² or T-Digest.
    
    Args:
        percentiles (list): List of percentiles to calculate
        
    Returns:
        dict: Dictionary mapping percentile to estimated value
    """
    print(f"\n📊 Streaming Percentile Estimation")
    print("=" * 35)
    
    # Collect a sample for percentile estimation
    # In production, you'd use more sophisticated streaming algorithms
    sample_ages = []
    sample_size = 1000  # Limit sample size for memory efficiency
    
    count = 0
    for age in stream_user_ages():
        if len(sample_ages) < sample_size:
            sample_ages.append(age)
        else:
            # Random sampling to maintain representative sample
            import random
            if random.random() < (sample_size / count):
                sample_ages[random.randint(0, sample_size - 1)] = age
        count += 1
    
    if sample_ages:
        sample_ages.sort()
        result = {}
        
        print(f"  Estimated percentiles (based on sample of {len(sample_ages)} users):")
        for p in percentiles:
            index = int((p / 100) * (len(sample_ages) - 1))
            result[p] = sample_ages[index]
            print(f"    {p}th percentile: {sample_ages[index]}")
        
        return result
    else:
        return {}


def compare_memory_usage():
    """
    Compare memory usage between traditional and streaming approaches
    """
    print(f"\n💾 Memory Usage Comparison")
    print("=" * 30)
    
    print("🚫 Traditional Approach:")
    print("  Memory = All ages × 4 bytes (int) = N × 4 bytes")
    print("  For 1M users: ~4MB memory minimum")
    print("  For 100M users: ~400MB memory minimum") 
    print("  Plus Python object overhead (much more!)")
    
    print(f"\n✅ Streaming Approach:")
    print("  Memory = Constant (few variables)")
    print("  For any number of users: <1KB memory")
    print("  Independent of dataset size!")
    
    print(f"\n🎯 Our Implementation:")
    print("  Variables used: total_age, user_count")
    print("  Memory usage: ~16 bytes (2 integers)")
    print("  Scalability: Can process unlimited users")


def advanced_streaming_patterns():
    """
    Demonstrate advanced streaming aggregation patterns
    """
    print(f"\n🔧 Advanced Streaming Patterns")
    print("=" * 35)
    
    # Pattern 1: Moving average (last N values)
    print("1. Moving Average (last 100 users):")
    from collections import deque
    
    window_size = 100
    window = deque(maxlen=window_size)
    moving_averages = []
    
    count = 0
    for age in stream_user_ages():
        window.append(age)
        count += 1
        
        if len(window) >= 10:  # Start calculating after 10 values
            moving_avg = sum(window) / len(window)
            moving_averages.append(moving_avg)
        
        # Stop after reasonable sample for demo
        if count >= 300:
            break
    
    if moving_averages:
        print(f"   Final moving average: {moving_averages[-1]:.2f}")
        print(f"   Computed {len(moving_averages)} moving averages")
    
    # Pattern 2: Conditional aggregation
    print(f"\n2. Conditional Aggregation (adults only):")
    adult_total = 0
    adult_count = 0
    minor_count = 0
    
    for age in stream_user_ages():
        if age >= 18:
            adult_total += age
            adult_count += 1
        else:
            minor_count += 1
    
    if adult_count > 0:
        adult_average = adult_total / adult_count
        print(f"   Average age of adults: {adult_average:.2f}")
        print(f"   Adults: {adult_count}, Minors: {minor_count}")


if __name__ == "__main__":
    """
    Main execution: Calculate and display average age
    """
    # Calculate average age using streaming
    average_age = calculate_average_age()
    
    # Print the required output
    print(f"Average age of users: {average_age:.2f}")
    
    # Additional demonstrations (optional)
    print(f"\n" + "=" * 60)
    print("ADDITIONAL DEMONSTRATIONS")
    print("=" * 60)
    
    demonstrate_streaming_aggregation()
    streaming_percentiles()
    compare_memory_usage()
    advanced_streaming_patterns()
    
    print(f"\n🎉 Memory-efficient aggregation completed!")
    print(f"📊 Processed all users using minimal memory")
