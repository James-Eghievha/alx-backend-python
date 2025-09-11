import time
import sqlite3
import functools
import hashlib
import json
from datetime import datetime, timedelta

def with_db_connection(func):
    """
    Decorator that automatically handles database connection lifecycle.
    
    This decorator:
    1. Opens a database connection
    2. Passes the connection as the first argument to the decorated function
    3. Ensures the connection is closed after function execution
    4. Handles exceptions properly to prevent connection leaks
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open database connection
        conn = sqlite3.connect('users.db')
        
        try:
            # Call the original function with connection as first argument
            result = func(conn, *args, **kwargs)
            return result
            
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Database operation failed: {e}")
            # Re-raise the exception after cleanup
            raise
            
        finally:
            # Always close the connection, even if an error occurred
            conn.close()
    
    return wrapper


# Global query cache dictionary
query_cache = {}


class CacheEntry:
    """
    Represents a cached query result with metadata.
    
    Attributes:
        result: The cached query result
        timestamp: When the result was cached
        hit_count: Number of times this cache entry was accessed
        query_hash: Hash of the original query for identification
    """
    def __init__(self, result, query_hash):
        self.result = result
        self.timestamp = datetime.now()
        self.hit_count = 0
        self.query_hash = query_hash
    
    def is_expired(self, ttl_seconds=300):
        """Check if cache entry is expired (default 5 minutes TTL)"""
        if ttl_seconds <= 0:
            return False  # Never expire
        
        expiry_time = self.timestamp + timedelta(seconds=ttl_seconds)
        return datetime.now() > expiry_time
    
    def get_age_seconds(self):
        """Get age of cache entry in seconds"""
        return (datetime.now() - self.timestamp).total_seconds()


def cache_query(ttl=300):
    """
    Decorator that caches database query results to avoid redundant calls.
    
    This decorator:
    1. Generates a unique cache key based on the SQL query and parameters
    2. Returns cached result if available and not expired
    3. Executes query and caches result if not in cache or expired
    4. Provides cache statistics and management functionality
    
    Args:
        ttl (int): Time-to-live for cached results in seconds (default: 300 = 5 minutes)
                  Set to 0 for no expiration
    
    Returns:
        Decorator function that adds caching functionality
        
    Usage:
        @cache_query(ttl=600)  # Cache for 10 minutes
        def my_query_function(conn, query, *params):
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Check if we have a cached result
            if cache_key in query_cache:
                cache_entry = query_cache[cache_key]
                
                # Check if cache entry is still valid
                if not cache_entry.is_expired(ttl):
                    cache_entry.hit_count += 1
                    age_seconds = cache_entry.get_age_seconds()
                    
                    print(f"CACHE HIT: {func.__name__} (age: {age_seconds:.1f}s, hits: {cache_entry.hit_count})")
                    return cache_entry.result
                else:
                    # Cache expired - remove it
                    print(f"CACHE EXPIRED: {func.__name__} (age: {cache_entry.get_age_seconds():.1f}s)")
                    del query_cache[cache_key]
            
            # Cache miss - execute the function
            print(f"CACHE MISS: {func.__name__} - executing query")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Cache the result
                query_hash = hashlib.md5(cache_key.encode()).hexdigest()[:8]
                cache_entry = CacheEntry(result, query_hash)
                query_cache[cache_key] = cache_entry
                
                print(f"CACHED: {func.__name__} (execution: {execution_time:.3f}s, cached {len(result) if hasattr(result, '__len__') else '?'} results)")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"QUERY FAILED: {func.__name__} after {execution_time:.3f}s - {e}")
                raise
        
        return wrapper
    
    # Handle both @cache_query and @cache_query() usage
    if callable(ttl):
        # Used as @cache_query (without parentheses)
        func = ttl
        ttl = 300  # Default TTL
        return decorator(func)
    else:
        # Used as @cache_query(ttl=600) (with parentheses)
        return decorator


def _generate_cache_key(func_name, args, kwargs):
    """
    Generate a unique cache key based on function name and arguments.
    
    Args:
        func_name (str): Name of the function being cached
        args (tuple): Positional arguments passed to function
        kwargs (dict): Keyword arguments passed to function
        
    Returns:
        str: Unique cache key
    """
    # Skip the connection object (first argument) when generating key
    relevant_args = args[1:] if args else ()
    
    # Create a deterministic representation of the arguments
    key_data = {
        'function': func_name,
        'args': relevant_args,
        'kwargs': kwargs
    }
    
    # Convert to JSON string for consistent hashing
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    
    # Create hash for shorter key
    return hashlib.md5(key_string.encode()).hexdigest()


def clear_cache():
    """Clear all cached query results"""
    global query_cache
    cleared_count = len(query_cache)
    query_cache.clear()
    print(f"Cache cleared: {cleared_count} entries removed")


def get_cache_stats():
    """Get detailed cache statistics"""
    if not query_cache:
        return {"message": "Cache is empty"}
    
    total_entries = len(query_cache)
    total_hits = sum(entry.hit_count for entry in query_cache.values())
    
    # Calculate average age
    total_age = sum(entry.get_age_seconds() for entry in query_cache.values())
    avg_age = total_age / total_entries if total_entries > 0 else 0
    
    # Find oldest and newest entries
    entries_by_age = sorted(query_cache.values(), key=lambda e: e.timestamp)
    oldest_age = entries_by_age[0].get_age_seconds() if entries_by_age else 0
    newest_age = entries_by_age[-1].get_age_seconds() if entries_by_age else 0
    
    return {
        "total_entries": total_entries,
        "total_cache_hits": total_hits,
        "average_hits_per_entry": total_hits / total_entries if total_entries > 0 else 0,
        "average_age_seconds": avg_age,
        "oldest_entry_age_seconds": oldest_age,
        "newest_entry_age_seconds": newest_age
    }


def print_cache_stats():
    """Print formatted cache statistics"""
    stats = get_cache_stats()
    
    if "message" in stats:
        print(stats["message"])
        return
    
    print("\n" + "="*50)
    print("CACHE STATISTICS")
    print("="*50)
    print(f"Total cached queries: {stats['total_entries']}")
    print(f"Total cache hits: {stats['total_cache_hits']}")
    print(f"Average hits per entry: {stats['average_hits_per_entry']:.1f}")
    print(f"Average entry age: {stats['average_age_seconds']:.1f} seconds")
    print(f"Oldest entry age: {stats['oldest_entry_age_seconds']:.1f} seconds")
    print(f"Newest entry age: {stats['newest_entry_age_seconds']:.1f} seconds")
    print("="*50)


@with_db_connection
@cache_query(ttl=300)  # Cache for 5 minutes
def fetch_users_with_cache(conn, query):
    """
    Fetch users from database with query result caching.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        query: SQL query string to execute
        
    Returns:
        list: Query results from database or cache
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


@with_db_connection
@cache_query(ttl=600)  # Cache for 10 minutes
def get_user_by_id_cached(conn, user_id):
    """
    Get a specific user by ID with caching.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        user_id: ID of user to retrieve
        
    Returns:
        tuple: User record or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


@with_db_connection
@cache_query(ttl=0)  # Never expires
def get_static_data_cached(conn, table_name):
    """
    Get static reference data with permanent caching.
    
    This is useful for data that rarely changes like categories,
    country codes, etc.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        table_name: Name of table to query
        
    Returns:
        list: All records from the specified table
    """
    cursor = conn.cursor()
    # Note: This is for demo only - in production, validate table_name to prevent SQL injection
    cursor.execute(f"SELECT * FROM {table_name}")
    return cursor.fetchall()


@with_db_connection
@cache_query(ttl=60)  # Short cache for frequently changing data
def get_active_users_count(conn):
    """
    Get count of active users with short-term caching.
    
    This demonstrates caching for metrics that change frequently
    but don't need real-time accuracy.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        
    Returns:
        int: Count of active users
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_login > datetime('now', '-30 days')")
    result = cursor.fetchone()
    return result[0] if result else 0


def setup_test_database():
    """Create and populate test database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            last_login TEXT DEFAULT NULL
        )
    ''')
    
    # Create categories table for static data demo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Clear existing data for clean testing
    cursor.execute('DELETE FROM users')
    cursor.execute('DELETE FROM categories')
    
    # Insert sample users
    sample_users = [
        ('Alice Johnson', 'alice@example.com', 28, datetime.now().isoformat()),
        ('Bob Smith', 'bob@example.com', 35, datetime.now().isoformat()),
        ('Carol Davis', 'carol@example.com', 42, None),
        ('David Wilson', 'david@example.com', 29, datetime.now().isoformat()),
        ('Eve Brown', 'eve@example.com', 33, datetime.now().isoformat())
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age, last_login) VALUES (?, ?, ?, ?)',
        sample_users
    )
    
    # Insert sample categories (static data)
    sample_categories = [
        ('Apartment', 'Entire apartment or flat'),
        ('House', 'Entire house'),
        ('Room', 'Private room in shared space'),
        ('Studio', 'Studio apartment')
    ]
    
    cursor.executemany(
        'INSERT INTO categories (name, description) VALUES (?, ?)',
        sample_categories
    )
    
    conn.commit()
    conn.close()
    print("Test database setup completed")


# Example usage and testing
if __name__ == "__main__":
    # Setup the test database
    setup_test_database()
    print("=" * 70)
    
    print("Testing cache_query decorator:")
    print()
    
    # Test 1: Basic caching behavior
    print("1. Testing basic query caching:")
    
    #### First call will cache the result
    print("   First call (should be cache miss):")
    users = fetch_users_with_cache(query="SELECT * FROM users")
    print(f"   Retrieved {len(users)} users")
    
    print("\n   Second call (should be cache hit):")
    #### Second call will use the cached result
    users_again = fetch_users_with_cache(query="SELECT * FROM users")
    print(f"   Retrieved {len(users_again)} users")
    
    print("\n   Third call with same query (should be cache hit):")
    users_third = fetch_users_with_cache(query="SELECT * FROM users")
    print(f"   Retrieved {len(users_third)} users")
    print()
    
    # Test 2: Different queries create different cache entries
    print("2. Testing different queries:")
    
    print("   Query for young users (cache miss):")
    young_users = fetch_users_with_cache(query="SELECT * FROM users WHERE age < 35")
    print(f"   Retrieved {len(young_users)} young users")
    
    print("\n   Same young users query (cache hit):")
    young_users_again = fetch_users_with_cache(query="SELECT * FROM users WHERE age < 35")
    print(f"   Retrieved {len(young_users_again)} young users")
    print()
    
    # Test 3: Parameterized queries
    print("3. Testing parameterized queries:")
    
    print("   Get user ID 1 (cache miss):")
    user1 = get_user_by_id_cached(user_id=1)
    print(f"   User 1: {user1}")
    
    print("\n   Get user ID 1 again (cache hit):")
    user1_again = get_user_by_id_cached(user_id=1)
    print(f"   User 1: {user1_again}")
    
    print("\n   Get user ID 2 (cache miss - different parameter):")
    user2 = get_user_by_id_cached(user_id=2)
    print(f"   User 2: {user2}")
    print()
    
    # Test 4: Static data caching (never expires)
    print("4. Testing static data caching (never expires):")
    
    print("   Get categories (cache miss):")
    categories = get_static_data_cached(table_name="categories")
    print(f"   Categories: {len(categories)} found")
    
    print("\n   Get categories again (cache hit):")
    categories_again = get_static_data_cached(table_name="categories")
    print(f"   Categories: {len(categories_again)} found")
    print()
    
    # Test 5: Short-term cache
    print("5. Testing short-term cache (60 seconds TTL):")
    
    print("   Get active user count (cache miss):")
    active_count = get_active_users_count()
    print(f"   Active users: {active_count}")
    
    print("\n   Get active user count again (cache hit):")
    active_count_again = get_active_users_count()
    print(f"   Active users: {active_count_again}")
    print()
    
    # Show cache statistics
    print_cache_stats()
    
    # Test 6: Cache clearing
    print("\n6. Testing cache clearing:")
    clear_cache()
    
    print("\n   After clearing - same query should be cache miss:")
    users_after_clear = fetch_users_with_cache(query="SELECT * FROM users")
    print(f"   Retrieved {len(users_after_clear)} users")
    
    print_cache_stats()
    
    print("\n" + "="*70)
    print("Cache testing completed!")
    print("Notice how identical queries use cached results,")
    print("while different queries or parameters create new cache entries.")
