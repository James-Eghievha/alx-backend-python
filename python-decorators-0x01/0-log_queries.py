import sqlite3
import functools
from datetime import datetime

#### decorator to log SQL queries

def log_queries(func):
    """
    Decorator that logs SQL queries before execution.
    
    This decorator wraps database functions to automatically log:
    - The SQL query being executed
    - Timestamp of execution
    - Function name that executed the query
    
    Args:
        func: The database function to be decorated
        
    Returns:
        Wrapper function that adds logging functionality
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from function arguments
        # Assume the first argument or 'query' keyword argument contains the SQL
        query = None
        
        # Check positional arguments for query
        if args:
            query = args[0]  # Assume first argument is the query
        
        # Check keyword arguments for query
        if 'query' in kwargs:
            query = kwargs['query']
        
        # Log the query with timestamp and function info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        function_name = func.__name__
        
        print(f"[{timestamp}] Executing SQL Query in {function_name}():")
        print(f"Query: {query}")
        print("-" * 50)
        
        # Execute the original function
        result = func(*args, **kwargs)
        
        # Optionally log completion
        print(f"[{timestamp}] Query completed successfully")
        print("=" * 50)
        
        return result
    
    return wrapper


@log_queries
def fetch_all_users(query):
    """
    Fetch all users from the database.
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        list: Query results
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


# Example usage and testing
if __name__ == "__main__":
    # Create a sample database for testing
    def setup_test_database():
        """Create a test database with sample data"""
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER
            )
        ''')
        
        # Insert sample data
        sample_users = [
            ('Alice Johnson', 'alice@example.com', 28),
            ('Bob Smith', 'bob@example.com', 35),
            ('Carol Davis', 'carol@example.com', 42),
            ('David Wilson', 'david@example.com', 29),
            ('Eve Brown', 'eve@example.com', 33)
        ]
        
        cursor.executemany(
            'INSERT OR IGNORE INTO users (name, email, age) VALUES (?, ?, ?)',
            sample_users
        )
        
        conn.commit()
        conn.close()
        print("Test database setup completed")
        print("=" * 50)
    
    # Setup test database
    setup_test_database()
    
    # Test the decorated function
    print("Testing log_queries decorator:")
    print()
    
    #### fetch users while logging the query
    users = fetch_all_users(query="SELECT * FROM users")
    
    print(f"Retrieved {len(users)} users:")
    for user in users:
        print(f"  - {user}")
    
    print()
    print("Testing with different queries:")
    print()
    
    # Test with different queries to show logging in action
    young_users = fetch_all_users(query="SELECT * FROM users WHERE age < 35")
    print(f"Found {len(young_users)} young users")
    
    print()
    older_users = fetch_all_users(query="SELECT name, email FROM users WHERE age >= 35")
    print(f"Found {len(older_users)} older users")
