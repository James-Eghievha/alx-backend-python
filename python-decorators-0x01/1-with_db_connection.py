import sqlite3
import functools

def with_db_connection(func):
    """
    Decorator that automatically handles database connection lifecycle.
    
    This decorator:
    1. Opens a database connection
    2. Passes the connection as the first argument to the decorated function
    3. Ensures the connection is closed after function execution
    4. Handles exceptions properly to prevent connection leaks
    
    Args:
        func: The database function to be decorated
        
    Returns:
        Wrapper function that manages database connections
        
    Usage:
        @with_db_connection
        def my_db_function(conn, other_args):
            cursor = conn.cursor()
            # ... database operations
            return result
    """
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open database connection
        conn = sqlite3.connect('users.db')
        
        try:
            # Call the original function with connection as first argument
            # The connection is injected as the first parameter
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


@with_db_connection
def get_user_by_id(conn, user_id):
    """
    Fetch a user by their ID.
    
    Args:
        conn: Database connection (automatically provided by decorator)
        user_id: ID of the user to fetch
        
    Returns:
        tuple: User data or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


@with_db_connection
def get_users_by_age_range(conn, min_age, max_age):
    """
    Fetch users within a specific age range.
    
    Args:
        conn: Database connection (automatically provided by decorator)
        min_age: Minimum age
        max_age: Maximum age
        
    Returns:
        list: List of users matching the criteria
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE age BETWEEN ? AND ?", 
        (min_age, max_age)
    )
    return cursor.fetchall()


@with_db_connection
def create_user(conn, name, email, age):
    """
    Create a new user in the database.
    
    Args:
        conn: Database connection (automatically provided by decorator)
        name: User's name
        email: User's email
        age: User's age
        
    Returns:
        int: ID of the created user
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        (name, email, age)
    )
    conn.commit()  # Important: commit the transaction
    return cursor.lastrowid


@with_db_connection
def update_user_email(conn, user_id, new_email):
    """
    Update a user's email address.
    
    Args:
        conn: Database connection (automatically provided by decorator)
        user_id: ID of the user to update
        new_email: New email address
        
    Returns:
        bool: True if update was successful
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET email = ? WHERE id = ?",
        (new_email, user_id)
    )
    conn.commit()
    return cursor.rowcount > 0  # True if any rows were affected


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
            age INTEGER NOT NULL
        )
    ''')
    
    # Clear existing data for clean testing
    cursor.execute('DELETE FROM users')
    
    # Insert sample data
    sample_users = [
        ('Alice Johnson', 'alice@example.com', 28),
        ('Bob Smith', 'bob@example.com', 35),
        ('Carol Davis', 'carol@example.com', 42),
        ('David Wilson', 'david@example.com', 29),
        ('Eve Brown', 'eve@example.com', 33)
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
        sample_users
    )
    
    conn.commit()
    conn.close()
    print("Test database setup completed")


# Example usage and testing
if __name__ == "__main__":
    # Setup the test database
    setup_test_database()
    print("=" * 60)
    
    print("Testing with_db_connection decorator:")
    print()
    
    #### Fetch user by ID with automatic connection handling
    print("1. Fetching user with ID = 1:")
    user = get_user_by_id(user_id=1)
    print(f"   User: {user}")
    print()
    
    print("2. Fetching users aged 30-40:")
    users_30_40 = get_users_by_age_range(min_age=30, max_age=40)
    print(f"   Found {len(users_30_40)} users:")
    for user in users_30_40:
        print(f"     - {user}")
    print()
    
    print("3. Creating a new user:")
    new_user_id = create_user(
        name="Frank Miller",
        email="frank@example.com", 
        age=45
    )
    print(f"   Created user with ID: {new_user_id}")
    
    # Verify the user was created
    new_user = get_user_by_id(user_id=new_user_id)
    print(f"   New user details: {new_user}")
    print()
    
    print("4. Updating user email:")
    update_success = update_user_email(
        user_id=new_user_id,
        new_email="frank.miller@example.com"
    )
    print(f"   Update successful: {update_success}")
    
    # Verify the update
    updated_user = get_user_by_id(user_id=new_user_id)
    print(f"   Updated user details: {updated_user}")
    print()
    
    print("5. Testing error handling (user not found):")
    nonexistent_user = get_user_by_id(user_id=999)
    print(f"   User 999: {nonexistent_user}")
    print()
    
    print("Database operations completed successfully!")
    print("All connections were automatically managed by the decorator.")
