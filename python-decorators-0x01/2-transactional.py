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


def transactional(func):
    """
    Decorator that manages database transactions automatically.
    
    This decorator wraps database operations in a transaction:
    1. Begins a transaction before executing the function
    2. Commits the transaction if the function succeeds
    3. Rolls back the transaction if the function raises an exception
    4. Ensures data consistency and atomicity
    
    Args:
        func: The database function to be decorated (must accept conn as first param)
        
    Returns:
        Wrapper function that provides transaction management
        
    Usage:
        @with_db_connection
        @transactional
        def update_multiple_records(conn, ...):
            # All operations succeed or all fail
            cursor.execute(...)
            cursor.execute(...)
            
    Note: This decorator expects the function to receive a database connection
    as its first parameter. It's designed to work with @with_db_connection.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract connection from arguments
        # The connection should be the first argument due to @with_db_connection
        conn = args[0] if args else None
        
        if conn is None:
            raise ValueError("Transaction decorator requires a database connection as first argument")
        
        try:
            # Begin transaction explicitly
            conn.execute('BEGIN')
            
            # Execute the original function
            result = func(*args, **kwargs)
            
            # If we reach here, the function succeeded - commit the transaction
            conn.commit()
            
            print(f"Transaction committed successfully in {func.__name__}")
            return result
            
        except Exception as e:
            # Function failed - rollback all changes
            conn.rollback()
            print(f"Transaction rolled back in {func.__name__} due to error: {e}")
            
            # Re-raise the original exception
            raise
    
    return wrapper


@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    """
    Update a user's email address within a transaction.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        user_id: ID of the user to update
        new_email: New email address
        
    Returns:
        bool: True if update was successful
        
    Raises:
        ValueError: If user_id is invalid or new_email is None
    """
    if not new_email or not new_email.strip():
        raise ValueError("Email cannot be empty")
    
    cursor = conn.cursor()
    
    # First check if user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Update the email
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
    
    # Check if update was successful
    if cursor.rowcount == 0:
        raise ValueError(f"Failed to update user {user_id}")
    
    return True


@with_db_connection
@transactional
def create_user_with_profile(conn, name, email, age, bio=""):
    """
    Create a user and their profile in a single transaction.
    
    This demonstrates how transactions ensure multiple related operations
    succeed or fail together.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        name: User's name
        email: User's email
        age: User's age
        bio: User's biography
        
    Returns:
        int: ID of the created user
    """
    cursor = conn.cursor()
    
    # Create user record
    cursor.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        (name, email, age)
    )
    user_id = cursor.lastrowid
    
    # Create profile record (this would typically be in a separate profiles table)
    # For demo, we'll add bio to user record
    cursor.execute(
        "UPDATE users SET bio = ? WHERE id = ?",
        (bio, user_id)
    )
    
    # Both operations succeed or both fail
    return user_id


@with_db_connection
@transactional  
def transfer_user_data(conn, from_user_id, to_user_id, transfer_email=False):
    """
    Transfer data between users (example of complex transaction).
    
    This demonstrates a complex multi-step operation that must be atomic.
    
    Args:
        conn: Database connection
        from_user_id: Source user ID
        to_user_id: Destination user ID
        transfer_email: Whether to also transfer email
        
    Returns:
        dict: Summary of transferred data
    """
    cursor = conn.cursor()
    
    # Get source user data
    cursor.execute("SELECT name, email, age FROM users WHERE id = ?", (from_user_id,))
    source_data = cursor.fetchone()
    
    if not source_data:
        raise ValueError(f"Source user {from_user_id} not found")
    
    # Get destination user
    cursor.execute("SELECT id FROM users WHERE id = ?", (to_user_id,))
    if cursor.fetchone() is None:
        raise ValueError(f"Destination user {to_user_id} not found")
    
    name, email, age = source_data
    
    # Update destination user
    if transfer_email:
        cursor.execute(
            "UPDATE users SET name = ?, email = ?, age = ? WHERE id = ?",
            (name, email, age, to_user_id)
        )
    else:
        cursor.execute(
            "UPDATE users SET name = ?, age = ? WHERE id = ?",
            (name, age, to_user_id)
        )
    
    # Archive source user (mark as transferred)
    cursor.execute(
        "UPDATE users SET name = ?, email = ? WHERE id = ?",
        (f"[TRANSFERRED] {name}", f"transferred.{email}", from_user_id)
    )
    
    return {
        'transferred_name': name,
        'transferred_email': email if transfer_email else None,
        'transferred_age': age
    }


def setup_test_database():
    """Create and populate test database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table with bio field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            bio TEXT DEFAULT ''
        )
    ''')
    
    # Clear existing data for clean testing
    cursor.execute('DELETE FROM users')
    
    # Insert sample data
    sample_users = [
        ('Alice Johnson', 'alice@example.com', 28, 'Software engineer'),
        ('Bob Smith', 'bob@example.com', 35, 'Designer'),
        ('Carol Davis', 'carol@example.com', 42, 'Product manager'),
        ('David Wilson', 'david@example.com', 29, 'Data scientist'),
        ('Eve Brown', 'eve@example.com', 33, 'Marketing specialist')
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age, bio) VALUES (?, ?, ?, ?)',
        sample_users
    )
    
    conn.commit()
    conn.close()
    print("Test database setup completed")


def get_user_details(user_id):
    """Helper function to get user details for testing"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result


# Example usage and testing
if __name__ == "__main__":
    # Setup the test database
    setup_test_database()
    print("=" * 70)
    
    print("Testing transactional decorator:")
    print()
    
    # Test 1: Successful transaction
    print("1. Testing successful email update:")
    print(f"   Before: {get_user_details(1)}")
    
    #### Update user's email with automatic transaction handling
    try:
        update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')
        print(f"   After:  {get_user_details(1)}")
    except Exception as e:
        print(f"   Update failed: {e}")
    print()
    
    # Test 2: Failed transaction (rollback)
    print("2. Testing failed transaction (invalid user ID):")
    try:
        update_user_email(user_id=999, new_email='nonexistent@example.com')
    except Exception as e:
        print(f"   Expected failure: {e}")
    print()
    
    # Test 3: Failed transaction (empty email)
    print("3. Testing failed transaction (empty email):")
    print(f"   Before: {get_user_details(2)}")
    try:
        update_user_email(user_id=2, new_email='')
        print(f"   After:  {get_user_details(2)}")
    except Exception as e:
        print(f"   Expected failure: {e}")
        print(f"   After:  {get_user_details(2)} (unchanged)")
    print()
    
    # Test 4: Complex transaction
    print("4. Testing complex transaction (user creation with profile):")
    try:
        new_user_id = create_user_with_profile(
            name="Frank Miller",
            email="frank@example.com",
            age=45,
            bio="Travel enthusiast and photographer"
        )
        print(f"   Created user: {get_user_details(new_user_id)}")
    except Exception as e:
        print(f"   Creation failed: {e}")
    print()
    
    # Test 5: Multi-step transaction
    print("5. Testing multi-step transaction (user data transfer):")
    print(f"   Source user (ID 3): {get_user_details(3)}")
    print(f"   Target user (ID 4): {get_user_details(4)}")
    
    try:
        transfer_result = transfer_user_data(
            from_user_id=3,
            to_user_id=4, 
            transfer_email=True
        )
        print(f"   Transfer result: {transfer_result}")
        print(f"   Source after: {get_user_details(3)}")
        print(f"   Target after: {get_user_details(4)}")
    except Exception as e:
        print(f"   Transfer failed: {e}")
    
    print()
    print("All transaction tests completed!")
    print("Notice how failed operations left the database unchanged.")
