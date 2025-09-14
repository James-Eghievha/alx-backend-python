import sqlite3
import os
from datetime import datetime

class DatabaseConnection:
    """
    A context manager class for handling database connections automatically.
    
    This class implements the context manager protocol using __enter__ and __exit__
    methods to ensure proper database connection handling:
    
    1. __enter__: Opens database connection and returns it
    2. __exit__: Closes database connection and handles exceptions
    
    Usage:
        with DatabaseConnection('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
        # Connection automatically closed here
    
    Benefits:
    - Guaranteed connection cleanup
    - Exception-safe resource management
    - Clean, readable code
    - Follows Python best practices
    """
    
    def __init__(self, db_name='users.db'):
        """
        Initialize the database connection context manager.
        
        Args:
            db_name (str): Name of the database file to connect to
        """
        self.db_name = db_name
        self.connection = None
        self.start_time = None
        
    def __enter__(self):
        """
        Enter the context manager - called when entering 'with' block.
        
        This method:
        1. Opens the database connection
        2. Sets connection properties for better performance
        3. Records start time for connection duration tracking
        4. Returns the connection object for use in the 'with' block
        
        Returns:
            sqlite3.Connection: The database connection object
            
        Raises:
            sqlite3.Error: If database connection fails
        """
        try:
            # Record when connection was opened
            self.start_time = datetime.now()
            
            # Open database connection
            self.connection = sqlite3.connect(self.db_name)
            
            # Configure connection for better performance and debugging
            self.connection.row_factory = sqlite3.Row  # Return rows as dict-like objects
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            
            print(f"[{self.start_time.strftime('%H:%M:%S')}] Database connection opened: {self.db_name}")
            
            # Return the connection for use in the 'with' block
            return self.connection
            
        except sqlite3.Error as e:
            print(f"Failed to connect to database {self.db_name}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error opening database connection: {e}")
            raise
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager - called when leaving 'with' block.
        
        This method:
        1. Handles any exceptions that occurred in the 'with' block
        2. Commits or rolls back transactions as appropriate
        3. Closes the database connection
        4. Provides detailed logging of connection usage
        
        Args:
            exc_type: Type of exception that occurred (None if no exception)
            exc_value: Exception instance (None if no exception)
            traceback: Exception traceback (None if no exception)
            
        Returns:
            bool: False to propagate exceptions, True to suppress them
        """
        if self.connection:
            try:
                # Calculate connection duration
                if self.start_time:
                    duration = (datetime.now() - self.start_time).total_seconds()
                    duration_str = f"{duration:.3f}s"
                else:
                    duration_str = "unknown"
                
                # Handle exceptions that occurred in the 'with' block
                if exc_type is not None:
                    # An exception occurred - rollback any pending transactions
                    self.connection.rollback()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Transaction rolled back due to {exc_type.__name__}: {exc_value}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Database connection closed (duration: {duration_str}) - WITH ERRORS")
                else:
                    # No exception - commit any pending transactions
                    self.connection.commit()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Transaction committed successfully")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Database connection closed (duration: {duration_str}) - SUCCESS")
                
                # Close the connection
                self.connection.close()
                self.connection = None
                
            except sqlite3.Error as e:
                print(f"Error closing database connection: {e}")
            except Exception as e:
                print(f"Unexpected error during connection cleanup: {e}")
        
        # Return False to propagate any exceptions that occurred
        # This allows calling code to handle exceptions appropriately
        return False
    
    def __repr__(self):
        """String representation of the context manager"""
        status = "open" if self.connection else "closed"
        return f"DatabaseConnection(db_name='{self.db_name}', status='{status}')"


class DatabaseConnectionPool:
    """
    Advanced context manager with connection pooling capabilities.
    
    This demonstrates a more sophisticated context manager that could
    be used in production applications with high database usage.
    """
    
    def __init__(self, db_name='users.db', pool_size=5):
        """
        Initialize connection pool.
        
        Args:
            db_name (str): Database file name
            pool_size (int): Maximum number of connections in pool
        """
        self.db_name = db_name
        self.pool_size = pool_size
        self.active_connections = 0
        self.connection_history = []
        
    def __enter__(self):
        """Enter with connection pool management"""
        if self.active_connections >= self.pool_size:
            print(f"Warning: Connection pool limit ({self.pool_size}) reached")
        
        self.active_connections += 1
        connection_id = len(self.connection_history) + 1
        
        try:
            connection = sqlite3.connect(self.db_name)
            connection.row_factory = sqlite3.Row
            
            # Track connection usage
            self.connection_history.append({
                'id': connection_id,
                'opened_at': datetime.now(),
                'status': 'active'
            })
            
            print(f"Pool connection #{connection_id} opened (active: {self.active_connections}/{self.pool_size})")
            
            # Store connection ID for use in __exit__
            self._current_connection_id = connection_id
            return connection
            
        except Exception as e:
            self.active_connections -= 1
            raise
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Exit with connection pool cleanup"""
        self.active_connections -= 1
        
        # Update connection history
        if hasattr(self, '_current_connection_id'):
            for conn_info in self.connection_history:
                if conn_info['id'] == self._current_connection_id:
                    conn_info['closed_at'] = datetime.now()
                    conn_info['status'] = 'closed'
                    conn_info['had_error'] = exc_type is not None
                    
                    duration = (conn_info['closed_at'] - conn_info['opened_at']).total_seconds()
                    status = "ERROR" if exc_type else "SUCCESS"
                    
                    print(f"Pool connection #{self._current_connection_id} closed - {status} (duration: {duration:.3f}s)")
                    break
        
        return False
    
    def get_pool_stats(self):
        """Get connection pool statistics"""
        total_connections = len(self.connection_history)
        successful_connections = sum(1 for conn in self.connection_history if not conn.get('had_error', False))
        
        if total_connections > 0:
            success_rate = (successful_connections / total_connections) * 100
            avg_duration = sum(
                (conn.get('closed_at', datetime.now()) - conn['opened_at']).total_seconds() 
                for conn in self.connection_history
            ) / total_connections
        else:
            success_rate = 0
            avg_duration = 0
        
        return {
            'total_connections': total_connections,
            'active_connections': self.active_connections,
            'success_rate': success_rate,
            'average_duration': avg_duration
        }


def setup_test_database():
    """Create and populate test database for demonstrations"""
    # Use basic connection for setup (not context manager to avoid recursion)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT DEFAULT NULL
        )
    ''')
    
    # Clear existing data for clean testing
    cursor.execute('DELETE FROM users')
    
    # Insert sample users
    sample_users = [
        ('Alice Johnson', 'alice@example.com', 28),
        ('Bob Smith', 'bob@example.com', 35),
        ('Carol Davis', 'carol@example.com', 42),
        ('David Wilson', 'david@example.com', 29),
        ('Eve Brown', 'eve@example.com', 33),
        ('Frank Miller', 'frank@example.com', 45),
        ('Grace Taylor', 'grace@example.com', 31),
        ('Henry Clark', 'henry@example.com', 38)
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
        sample_users
    )
    
    conn.commit()
    conn.close()
    print("Test database setup completed with 8 sample users")


def demonstrate_basic_context_manager():
    """Demonstrate basic context manager usage"""
    print("\n" + "="*60)
    print("BASIC CONTEXT MANAGER DEMONSTRATION")
    print("="*60)
    
    # Use the context manager with the 'with' statement
    with DatabaseConnection('users.db') as conn:
        cursor = conn.cursor()
        
        # Perform the required query: SELECT * FROM users
        print("Executing: SELECT * FROM users")
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        
        print(f"\nQuery Results ({len(results)} users found):")
        print("-" * 50)
        
        # Print the results
        for user in results:
            # Since we set row_factory = sqlite3.Row, we can access columns by name
            print(f"ID: {user['id']:2d} | Name: {user['name']:20s} | Email: {user['email']:25s} | Age: {user['age']:2d}")
    
    # Connection is automatically closed here due to context manager
    print("\nContext manager automatically closed the database connection")


def demonstrate_exception_handling():
    """Demonstrate context manager with exception handling"""
    print("\n" + "="*60)
    print("EXCEPTION HANDLING DEMONSTRATION")
    print("="*60)
    
    try:
        with DatabaseConnection('users.db') as conn:
            cursor = conn.cursor()
            
            print("Executing valid query first...")
            cursor.execute("SELECT COUNT(*) as user_count FROM users")
            count_result = cursor.fetchone()
            print(f"Total users in database: {count_result['user_count']}")
            
            print("\nNow executing invalid query to trigger exception...")
            # This will cause an exception due to invalid SQL
            cursor.execute("SELECT * FROM nonexistent_table")
            
    except sqlite3.Error as e:
        print(f"Database error caught: {e}")
        print("Notice that the connection was still properly closed due to __exit__ method")
    
    print("\nEven with the exception, the database connection was properly managed")


def demonstrate_multiple_operations():
    """Demonstrate multiple database operations in one context"""
    print("\n" + "="*60)
    print("MULTIPLE OPERATIONS DEMONSTRATION")  
    print("="*60)
    
    with DatabaseConnection('users.db') as conn:
        cursor = conn.cursor()
        
        # Operation 1: Get user statistics
        print("1. Getting user statistics...")
        cursor.execute('''
            SELECT 
                COUNT(*) as total_users,
                AVG(age) as average_age,
                MIN(age) as youngest_age,
                MAX(age) as oldest_age
            FROM users
        ''')
        stats = cursor.fetchone()
        print(f"   Total users: {stats['total_users']}")
        print(f"   Average age: {stats['average_age']:.1f}")
        print(f"   Age range: {stats['youngest_age']}-{stats['oldest_age']}")
        
        # Operation 2: Get users by age group
        print("\n2. Getting users by age group...")
        cursor.execute("SELECT * FROM users WHERE age < 35 ORDER BY age")
        young_users = cursor.fetchall()
        print(f"   Users under 35: {len(young_users)} found")
        
        # Operation 3: Update a user's last login
        print("\n3. Updating user's last login...")
        current_time = datetime.now().isoformat()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = 1",
            (current_time,)
        )
        print(f"   Updated user ID 1 last login to: {current_time}")
        
        # Operation 4: Verify the update
        print("\n4. Verifying the update...")
        cursor.execute("SELECT name, last_login FROM users WHERE id = 1")
        updated_user = cursor.fetchone()
        print(f"   User: {updated_user['name']} | Last login: {updated_user['last_login']}")
    
    print("\nAll operations completed successfully within a single database connection context")


def demonstrate_connection_pool():
    """Demonstrate advanced connection pool context manager"""
    print("\n" + "="*60)
    print("CONNECTION POOL DEMONSTRATION")
    print("="*60)
    
    pool = DatabaseConnectionPool('users.db', pool_size=3)
    
    # Simulate multiple concurrent operations
    print("Simulating multiple database operations with connection pool:")
    
    for i in range(5):  # More operations than pool size to show pool management
        try:
            with pool as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE age > ?", (30 + i * 2,))
                result = cursor.fetchone()
                print(f"   Operation {i+1}: Found {result['count']} users over age {30 + i * 2}")
                
                # Simulate some processing time
                import time
                time.sleep(0.1)
                
        except Exception as e:
            print(f"   Operation {i+1} failed: {e}")
    
    # Show pool statistics
    print("\nConnection Pool Statistics:")
    stats = pool.get_pool_stats()
    print(f"   Total connections used: {stats['total_connections']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    print(f"   Average connection duration: {stats['average_duration']:.3f}s")


# Main execution and testing
if __name__ == "__main__":
    # Setup test database
    setup_test_database()
    
    # Run demonstrations
    demonstrate_basic_context_manager()
    demonstrate_exception_handling() 
    demonstrate_multiple_operations()
    demonstrate_connection_pool()
    
    print("\n" + "="*60)
    print("CONTEXT MANAGER DEMONSTRATIONS COMPLETED")
    print("="*60)
    print("\nKey Benefits Demonstrated:")
    print("✓ Automatic resource cleanup")
    print("✓ Exception-safe database operations")
    print("✓ Clean, readable code structure")
    print("✓ Proper transaction handling")
    print("✓ Connection duration tracking")
    print("✓ Advanced features like connection pooling")
    
    # Clean up test database file
    if os.path.exists('users.db'):
        print(f"\nTest database 'users.db' remains available for further testing")
    
    print("\nContext manager implementation complete!")
