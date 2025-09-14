import asyncio
import aiosqlite
import time
from datetime import datetime
from typing import List, Dict, Any

async def async_fetch_users() -> List[Dict[str, Any]]:
    """
    Asynchronously fetch all users from the database.
    
    This function demonstrates basic async database operations:
    1. Opens async database connection using aiosqlite
    2. Executes SELECT query asynchronously
    3. Fetches all results without blocking other operations
    4. Closes connection properly
    
    Returns:
        List[Dict[str, Any]]: List of all users as dictionaries
        
    Example:
        users = await async_fetch_users()
        print(f"Found {len(users)} users")
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Starting async_fetch_users()")
    start_time = time.time()
    
    async with aiosqlite.connect('users.db') as db:
        # Configure connection for dict-like row access
        db.row_factory = aiosqlite.Row
        
        # Execute query asynchronously
        async with db.execute("SELECT * FROM users ORDER BY id") as cursor:
            # Fetch all rows asynchronously
            rows = await cursor.fetchall()
            
            # Convert sqlite3.Row objects to dictionaries for easier handling
            users = []
            for row in rows:
                user_dict = {
                    'id': row['id'],
                    'name': row['name'], 
                    'email': row['email'],
                    'age': row['age']
                }
                users.append(user_dict)
    
    execution_time = time.time() - start_time
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] async_fetch_users() completed in {execution_time:.3f}s - Found {len(users)} users")
    
    return users


async def async_fetch_older_users() -> List[Dict[str, Any]]:
    """
    Asynchronously fetch users older than 40 from the database.
    
    This function demonstrates parameterized async queries:
    1. Uses parameterized query to safely filter by age
    2. Executes query with WHERE clause asynchronously
    3. Returns filtered results
    
    Returns:
        List[Dict[str, Any]]: List of users over 40 as dictionaries
        
    Example:
        older_users = await async_fetch_older_users()
        print(f"Found {len(older_users)} users over 40")
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Starting async_fetch_older_users()")
    start_time = time.time()
    
    async with aiosqlite.connect('users.db') as db:
        # Configure connection for dict-like row access
        db.row_factory = aiosqlite.Row
        
        # Execute parameterized query asynchronously (safe from SQL injection)
        async with db.execute("SELECT * FROM users WHERE age > ? ORDER BY age DESC", (40,)) as cursor:
            rows = await cursor.fetchall()
            
            # Convert to dictionaries with additional computed fields
            older_users = []
            for row in rows:
                user_dict = {
                    'id': row['id'],
                    'name': row['name'],
                    'email': row['email'],
                    'age': row['age'],
                    'age_category': 'senior' if row['age'] >= 60 else 'middle-aged'
                }
                older_users.append(user_dict)
    
    execution_time = time.time() - start_time
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] async_fetch_older_users() completed in {execution_time:.3f}s - Found {len(older_users)} users")
    
    return older_users


async def fetch_concurrently() -> tuple:
    """
    Execute multiple database queries concurrently using asyncio.gather().
    
    This function demonstrates the core concept of concurrent async operations:
    1. Starts both query functions simultaneously
    2. Uses asyncio.gather() to wait for all to complete
    3. Returns results when all queries finish
    4. Total time is limited by the slowest query, not the sum of all queries
    
    Returns:
        tuple: (all_users, older_users) containing results from both queries
        
    Key Concepts:
        - asyncio.gather() runs coroutines concurrently
        - await waits for all coroutines to complete
        - Results are returned in the same order as input coroutines
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Starting concurrent database queries...")
    start_time = time.time()
    
    # Execute both queries concurrently using asyncio.gather()
    # This is the key line that enables concurrent execution
    all_users, older_users = await asyncio.gather(
        async_fetch_users(),        # Coroutine 1: Fetch all users
        async_fetch_older_users()   # Coroutine 2: Fetch older users
    )
    
    total_time = time.time() - start_time
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] All concurrent queries completed in {total_time:.3f}s")
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Retrieved {len(all_users)} total users and {len(older_users)} older users")
    
    return all_users, older_users


async def async_fetch_user_statistics() -> Dict[str, Any]:
    """
    Additional async function to demonstrate more complex concurrent operations.
    
    Returns:
        Dict[str, Any]: User statistics including counts, averages, etc.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Starting async_fetch_user_statistics()")
    start_time = time.time()
    
    async with aiosqlite.connect('users.db') as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT 
                COUNT(*) as total_users,
                AVG(age) as average_age,
                MIN(age) as youngest_age,
                MAX(age) as oldest_age,
                COUNT(CASE WHEN age < 30 THEN 1 END) as users_under_30,
                COUNT(CASE WHEN age BETWEEN 30 AND 50 THEN 1 END) as users_30_to_50,
                COUNT(CASE WHEN age > 50 THEN 1 END) as users_over_50
            FROM users
        """) as cursor:
            row = await cursor.fetchone()
            
            stats = {
                'total_users': row['total_users'],
                'average_age': round(row['average_age'], 1) if row['average_age'] else 0,
                'youngest_age': row['youngest_age'],
                'oldest_age': row['oldest_age'],
                'age_distribution': {
                    'under_30': row['users_under_30'],
                    '30_to_50': row['users_30_to_50'],
                    'over_50': row['users_over_50']
                }
            }
    
    execution_time = time.time() - start_time
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] async_fetch_user_statistics() completed in {execution_time:.3f}s")
    
    return stats


async def fetch_with_multiple_concurrent_operations():
    """
    Demonstrate running multiple different async operations concurrently.
    
    This shows how asyncio.gather() can handle different types of operations
    simultaneously, not just similar database queries.
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Starting multiple concurrent operations...")
    start_time = time.time()
    
    # Run three different async operations concurrently
    users, older_users, stats = await asyncio.gather(
        async_fetch_users(),           # Query 1: All users
        async_fetch_older_users(),     # Query 2: Older users  
        async_fetch_user_statistics()  # Query 3: User statistics
    )
    
    total_time = time.time() - start_time
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] All operations completed in {total_time:.3f}s")
    
    return users, older_users, stats


async def demonstrate_async_context_manager():
    """
    Demonstrate using async context managers for database operations.
    
    This shows how to create reusable async database connections
    that can be shared across multiple operations.
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Demonstrating async context manager...")
    
    async with aiosqlite.connect('users.db') as db:
        db.row_factory = aiosqlite.Row
        
        # Multiple queries using the same connection
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Executing multiple queries with shared connection...")
        
        # Query 1: Count users by domain
        async with db.execute("""
            SELECT 
                CASE 
                    WHEN email LIKE '%@gmail.com' THEN 'Gmail'
                    WHEN email LIKE '%@yahoo.com' THEN 'Yahoo'
                    WHEN email LIKE '%@outlook.com' THEN 'Outlook'
                    ELSE 'Other'
                END as email_domain,
                COUNT(*) as user_count
            FROM users
            GROUP BY email_domain
            ORDER BY user_count DESC
        """) as cursor:
            domain_stats = await cursor.fetchall()
        
        # Query 2: Get age distribution
        async with db.execute("""
            SELECT 
                CASE 
                    WHEN age < 25 THEN 'Young (18-24)'
                    WHEN age < 35 THEN 'Adult (25-34)'
                    WHEN age < 50 THEN 'Middle (35-49)'
                    ELSE 'Senior (50+)'
                END as age_group,
                COUNT(*) as count
            FROM users
            GROUP BY age_group
            ORDER BY MIN(age)
        """) as cursor:
            age_distribution = await cursor.fetchall()
    
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Email domain distribution:")
    for row in domain_stats:
        print(f"    {row['email_domain']}: {row['user_count']} users")
    
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Age distribution:")
    for row in age_distribution:
        print(f"    {row['age_group']}: {row['count']} users")


def setup_test_database():
    """
    Create and populate test database for async demonstrations.
    Note: This uses synchronous sqlite3 for setup, then async aiosqlite for queries.
    """
    import sqlite3
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM users')
    
    # Insert sample users with varied ages (including users over 40)
    sample_users = [
        ('Alice Johnson', 'alice@gmail.com', 28),
        ('Bob Smith', 'bob@yahoo.com', 35),
        ('Carol Davis', 'carol@gmail.com', 42),      # Over 40
        ('David Wilson', 'david@outlook.com', 29),
        ('Eve Brown', 'eve@gmail.com', 33),
        ('Frank Miller', 'frank@yahoo.com', 45),     # Over 40
        ('Grace Taylor', 'grace@gmail.com', 31),
        ('Henry Clark', 'henry@outlook.com', 38),
        ('Ivy Adams', 'ivy@gmail.com', 52),          # Over 40
        ('Jack White', 'jack@yahoo.com', 41),        # Over 40
        ('Karen Brown', 'karen@gmail.com', 26),
        ('Liam Davis', 'liam@outlook.com', 48),      # Over 40
        ('Mia Wilson', 'mia@gmail.com', 55),         # Over 40
        ('Noah Johnson', 'noah@yahoo.com', 39),
        ('Olivia Smith', 'olivia@gmail.com', 47)     # Over 40
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
        sample_users
    )
    
    conn.commit()
    conn.close()
    print("Test database setup completed with 15 sample users (7 over age 40)")


def compare_sync_vs_async_performance():
    """
    Compare synchronous vs asynchronous database query performance.
    This demonstrates the time savings achieved with concurrent execution.
    """
    import sqlite3
    
    print(f"\n{'='*70}")
    print("PERFORMANCE COMPARISON: SYNCHRONOUS VS ASYNCHRONOUS")
    print(f"{'='*70}")
    
    # Synchronous version
    print("Testing SYNCHRONOUS execution...")
    sync_start = time.time()
    
    # Query 1 (synchronous)
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id")
    sync_all_users = cursor.fetchall()
    conn.close()
    
    # Query 2 (synchronous)
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE age > ? ORDER BY age DESC", (40,))
    sync_older_users = cursor.fetchall()
    conn.close()
    
    sync_time = time.time() - sync_start
    print(f"Synchronous execution completed in {sync_time:.3f}s")
    print(f"Results: {len(sync_all_users)} total users, {len(sync_older_users)} older users")
    
    # Asynchronous version
    print(f"\nTesting ASYNCHRONOUS execution...")
    async_start = time.time()
    
    # Run async version
    async_all_users, async_older_users = asyncio.run(fetch_concurrently())
    
    async_time = time.time() - async_start
    print(f"Asynchronous execution completed in {async_time:.3f}s")
    
    # Calculate performance improvement
    if sync_time > 0:
        improvement = ((sync_time - async_time) / sync_time) * 100
        print(f"\nPerformance improvement: {improvement:.1f}% faster with async")
        print(f"Time saved: {sync_time - async_time:.3f} seconds")
    
    return sync_time, async_time


# Main execution
if __name__ == "__main__":
    # Setup test database
    setup_test_database()
    
    print(f"\n{'='*70}")
    print("CONCURRENT ASYNCHRONOUS DATABASE QUERIES DEMONSTRATION")
    print(f"{'='*70}")
    
    # Main demonstration: Use asyncio.run() to execute concurrent fetch
    print("\n1. Basic concurrent query execution:")
    all_users, older_users = asyncio.run(fetch_concurrently())
    
    print(f"\nResults Summary:")
    print(f"- Total users retrieved: {len(all_users)}")
    print(f"- Users over 40: {len(older_users)}")
    
    if older_users:
        print(f"- Oldest user: {max(older_users, key=lambda x: x['age'])['name']} (age {max(older_users, key=lambda x: x['age'])['age']})")
        print(f"- Older users by category:")
        middle_aged = [u for u in older_users if u['age_category'] == 'middle-aged']
        seniors = [u for u in older_users if u['age_category'] == 'senior']
        print(f"  * Middle-aged (41-59): {len(middle_aged)}")
        print(f"  * Senior (60+): {len(seniors)}")
    
    # Advanced demonstration: Multiple different operations
    print(f"\n2. Multiple different concurrent operations:")
    users, older_users_2, stats = asyncio.run(fetch_with_multiple_concurrent_operations())
    
    print(f"\nUser Statistics:")
    print(f"- Average age: {stats['average_age']} years")
    print(f"- Age range: {stats['youngest_age']} - {stats['oldest_age']} years")
    print(f"- Age distribution:")
    for category, count in stats['age_distribution'].items():
        print(f"  * {category.replace('_', ' ').title()}: {count} users")
    
    # Async context manager demonstration
    print(f"\n3. Async context manager usage:")
    asyncio.run(demonstrate_async_context_manager())
    
    # Performance comparison
    print(f"\n4. Performance comparison:")
    sync_time, async_time = compare_sync_vs_async_performance()
    
    print(f"\n{'='*70}")
    print("CONCURRENT QUERIES DEMONSTRATION COMPLETED")
    print(f"{'='*70}")
    print(f"\nKey Benefits Demonstrated:")
    print(f"✓ Concurrent execution reduces total query time")
    print(f"✓ Multiple database operations run simultaneously")
    print(f"✓ asyncio.gather() coordinates multiple coroutines")
    print(f"✓ Async context managers provide clean resource management")
    print(f"✓ Significant performance improvement over synchronous code")
    print(f"✓ Better resource utilization and user experience")
    
    print(f"\nAsync programming implementation complete!")
