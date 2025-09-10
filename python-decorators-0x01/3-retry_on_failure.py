import time
import sqlite3 
import functools
import random
from datetime import datetime

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


def retry_on_failure(retries=3, delay=2):
    """
    Decorator that retries database operations if they fail due to transient errors.
    
    This decorator implements exponential backoff retry logic:
    1. Catches exceptions from the decorated function
    2. Waits for a specified delay before retrying
    3. Implements exponential backoff (delay increases with each retry)
    4. Gives up after the specified number of retries
    5. Distinguishes between retryable and non-retryable errors
    
    Args:
        retries (int): Maximum number of retry attempts (default: 3)
        delay (float): Initial delay between retries in seconds (default: 2)
        
    Returns:
        Decorator function that adds retry functionality
        
    Usage:
        @retry_on_failure(retries=5, delay=1)
        def my_db_function():
            # Database operation that might fail transiently
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            # Try the function up to (retries + 1) times
            for attempt in range(retries + 1):
                try:
                    # Attempt to execute the function
                    result = func(*args, **kwargs)
                    
                    # Success! If we had previous failures, log the recovery
                    if attempt > 0:
                        print(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a retryable error
                    if not _is_retryable_error(e):
                        print(f"❌ Non-retryable error in {func.__name__}: {e}")
                        raise e
                    
                    # If this was our last attempt, give up
                    if attempt == retries:
                        print(f"❌ {func.__name__} failed after {retries + 1} attempts. Final error: {e}")
                        raise e
                    
                    # Log the failure and prepare for retry
                    print(f"⚠️  Attempt {attempt + 1} of {func.__name__} failed: {e}")
                    print(f"🔄 Retrying in {current_delay:.1f} seconds...")
                    
                    # Wait before retrying (exponential backoff)
                    time.sleep(current_delay)
                    
                    # Increase delay for next attempt (exponential backoff)
                    current_delay *= 2
                    
                    # Add some jitter to prevent thundering herd
                    jitter = random.uniform(0.1, 0.5)
                    current_delay += jitter
            
            # This should never be reached due to the raise in the loop
            raise last_exception
        
        return wrapper
    return decorator


def _is_retryable_error(exception):
    """
    Determine if an error is worth retrying.
    
    Retryable errors are typically transient issues that might resolve
    if we try again. Non-retryable errors are usually permanent problems
    like syntax errors or constraint violations.
    
    Args:
        exception: The exception to evaluate
        
    Returns:
        bool: True if the error is retryable, False otherwise
    """
    # Convert to string for easier analysis
    error_message = str(exception).lower()
    
    # Retryable SQLite errors
    retryable_patterns = [
        'database is locked',
        'database is busy',
        'disk i/o error',
        'cannot start transaction',
        'connection failed',
        'network error',
        'timeout',
        'temporary failure',
        'deadlock',
        'connection refused',
        'connection reset'
    ]
    
    # Check if error message contains retryable patterns
    for pattern in retryable_patterns:
        if pattern in error_message:
            return True
    
    # Check specific exception types
    if isinstance(exception, (
        sqlite3.OperationalError,  # Often transient issues
        ConnectionError,           # Network problems
        TimeoutError              # Timeout issues
    )):
        return True
    
    # Non-retryable errors (permanent issues)
    non_retryable_patterns = [
        'syntax error',
        'no such table',
        'no such column',
        'unique constraint failed',
        'foreign key constraint failed',
        'not null constraint failed',
        'check constraint failed'
    ]
    
    for pattern in non_retryable_patterns:
        if pattern in error_message:
            return False
    
    # Default: assume it's retryable if we're not sure
    return True


class SimulatedFailure(Exception):
    """Custom exception to simulate transient failures for testing"""
    pass


# Global counter for simulating intermittent failures
_failure_counter = 0


def simulate_transient_failure(failure_rate=0.3, max_failures=2):
    """
    Simulate transient failures for testing purposes.
    
    Args:
        failure_rate: Probability of failure (0.0 to 1.0)
        max_failures: Maximum consecutive failures before success
    """
    global _failure_counter
    
    # Simulate failure based on probability and counter
    if _failure_counter < max_failures and random.random() < failure_rate:
        _failure_counter += 1
        raise SimulatedFailure(f"Simulated transient failure #{_failure_counter}")
    
    # Reset counter after success
    _failure_counter = 0


@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    """
    Fetch all users from database with automatic retry on failure.
    
    This function demonstrates retry behavior by simulating occasional
    transient failures.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        
    Returns:
        list: All user records from the database
    """
    # Simulate transient failures for testing
    # Comment out this line in production
    simulate_transient_failure(failure_rate=0.4, max_failures=2)
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


@with_db_connection
@retry_on_failure(retries=5, delay=0.5)
def get_user_bookings(conn, user_id):
    """
    Get all bookings for a specific user with retry logic.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        user_id: ID of the user whose bookings to fetch
        
    Returns:
        list: User's booking records
    """
    # Simulate transient failures
    simulate_transient_failure(failure_rate=0.3, max_failures=1)
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE user_id = ?", (user_id,))
    return cursor.fetchall()


@with_db_connection
@retry_on_failure(retries=2, delay=1)
def update_user_last_login(conn, user_id):
    """
    Update user's last login timestamp with retry logic.
    
    Args:
        conn: Database connection (provided by @with_db_connection)
        user_id: ID of the user to update
        
    Returns:
        bool: True if update was successful
    """
    # Simulate transient failures
    simulate_transient_failure(failure_rate=0.2, max_failures=1)
    
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    cursor.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (current_time, user_id)
    )
    conn.commit()
    return cursor.rowcount > 0


@with_db_connection
@retry_on_failure(retries=3, delay=1)  
def fetch_users_with_permanent_error(conn):
    """
    Function that demonstrates non-retryable error handling.
    This will fail immediately without retries due to syntax error.
    """
    cursor = conn.cursor()
    # Intentional syntax error - not retryable
    cursor.execute("SELCT * FROM users")  # Missing 'E' in SELECT
    return cursor.fetchall()


def setup_test_database():
    """Create and populate test database with bookings table"""
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
    
    # Create bookings table for testing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            checkin TEXT NOT NULL,
            checkout TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Clear existing data for clean testing
    cursor.execute('DELETE FROM users')
    cursor.execute('DELETE FROM bookings')
    
    # Insert sample users
    sample_users = [
        ('Alice Johnson', 'alice@example.com', 28),
        ('Bob Smith', 'bob@example.com', 35),
        ('Carol Davis', 'carol@example.com', 42)
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
        sample_users
    )
    
    # Insert sample bookings
    sample_bookings = [
        (1, 101, '2024-01-15', '2024-01-20', 'confirmed'),
        (1, 102, '2024-02-10', '2024-02-15', 'confirmed'),
        (2, 103, '2024-01-25', '2024-01-30', 'pending'),
        (3, 104, '2024-03-01', '2024-03-05', 'confirmed')
    ]
    
    cursor.executemany(
        'INSERT INTO bookings (user_id, property_id, checkin, checkout, status) VALUES (?, ?, ?, ?, ?)',
        sample_bookings
    )
    
    conn.commit()
    conn.close()
    print("Test database with bookings setup completed")


# Example usage and testing
if __name__ == "__main__":
    # Setup the test database
    setup_test_database()
    print("=" * 70)
    
    print("Testing retry_on_failure decorator:")
    print()
    
    # Test 1: Successful retry after transient failures
    print("1. Testing fetch_users_with_retry (may have transient failures):")
    try:
        #### attempt to fetch users with automatic retry on failure
        users = fetch_users_with_retry()
        print(f"   Successfully retrieved {len(users)} users:")
        for user in users[:2]:  # Show first 2 users
            print(f"     - {user}")
    except Exception as e:
        print(f"   Failed to fetch users: {e}")
    print()
    
    # Test 2: Retry with different parameters
    print("2. Testing get_user_bookings with retry (user_id=1):")
    try:
        bookings = get_user_bookings(user_id=1)
        print(f"   Successfully retrieved {len(bookings)} bookings for user 1:")
        for booking in bookings:
            print(f"     - Booking {booking[0]}: Property {booking[2]} ({booking[3]} to {booking[4]})")
    except Exception as e:
        print(f"   Failed to fetch bookings: {e}")
    print()
    
    # Test 3: Update with retry
    print("3. Testing update_user_last_login with retry:")
    try:
        success = update_user_last_login(user_id=1)
        print(f"   Last login update successful: {success}")
    except Exception as e:
        print(f"   Failed to update last login: {e}")
    print()
    
    # Test 4: Non-retryable error
    print("4. Testing non-retryable error (syntax error):")
    try:
        result = fetch_users_with_permanent_error()
        print(f"   Unexpected success: {result}")
    except Exception as e:
        print(f"   Expected failure (no retries): {e}")
    print()
    
    # Test 5: Multiple consecutive calls to show retry reset
    print("5. Testing multiple calls to demonstrate retry counter reset:")
    for i in range(3):
        try:
            users = fetch_users_with_retry()
            print(f"   Call {i+1}: Success - {len(users)} users")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print()
    print("Retry testing completed!")
    print("Notice how transient failures are automatically retried,")
    print("while permanent errors fail immediately.")
