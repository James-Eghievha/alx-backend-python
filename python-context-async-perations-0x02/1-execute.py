import sqlite3
import time
from datetime import datetime

class ExecuteQuery:
    """
    A reusable context manager for executing database queries with automatic 
    connection management and query execution.
    
    This context manager:
    1. Takes a SQL query and parameters as input
    2. Opens database connection in __enter__
    3. Executes the query with parameters
    4. Returns query results
    5. Closes connection in __exit__
    6. Handles exceptions and provides detailed logging
    
    Usage:
        with ExecuteQuery("SELECT * FROM users WHERE age > ?", (25,)) as results:
            for user in results:
                print(user)
    
    Benefits:
    - Automatic connection management
    - SQL injection protection via parameterized queries
    - Consistent error handling
    - Query performance logging
    - Reusable for any SELECT query
    """
    
    def __init__(self, query, parameters=None, db_name='users.db', fetch_method='fetchall'):
        """
        Initialize the query execution context manager.
        
        Args:
            query (str): SQL query to execute (with ? placeholders for parameters)
            parameters (tuple/list): Parameters to bind to query placeholders
            db_name (str): Database file name (default: 'users.db')
            fetch_method (str): Method to fetch results ('fetchall', 'fetchone', 'fetchmany')
        
        Examples:
            # Fetch all users over age 25
            ExecuteQuery("SELECT * FROM users WHERE age > ?", (25,))
            
            # Fetch one specific user
            ExecuteQuery("SELECT * FROM users WHERE id = ?", (1,), fetch_method='fetchone')
            
            # Fetch users with email containing pattern
            ExecuteQuery("SELECT * FROM users WHERE email LIKE ?", ('%@gmail.com',))
        """
        self.query = query
        self.parameters = parameters if parameters is not None else ()
        self.db_name = db_name
        self.fetch_method = fetch_method
        
        # State tracking
        self.connection = None
        self.cursor = None
        self.start_time = None
        self.query_result = None
        
        # Validate fetch method
        valid_fetch_methods = ['fetchall', 'fetchone', 'fetchmany']
        if fetch_method not in valid_fetch_methods:
            raise ValueError(f"fetch_method must be one of {valid_fetch_methods}")
    
    def __enter__(self):
        """
        Enter the context manager - establish connection and execute query.
        
        This method:
        1. Opens database connection
        2. Configures connection properties
        3. Creates cursor and executes query
        4. Fetches results using specified method
        5. Returns query results
        
        Returns:
            Query results (list, tuple, or None depending on fetch_method)
            
        Raises:
            sqlite3.Error: If database operations fail
            ValueError: If query parameters are invalid
        """
        try:
            # Record start time for performance tracking
            self.start_time = datetime.now()
            
            # Open database connection
            self.connection = sqlite3.connect(self.db_name)
            
            # Configure connection for better usability
            self.connection.row_factory = sqlite3.Row  # Return dict-like rows
            
            # Create cursor
            self.cursor = self.connection.cursor()
            
            # Log query execution (helpful for debugging)
            param_str = str(self.parameters) if self.parameters else "no parameters"
            print(f"[{self.start_time.strftime('%H:%M:%S')}] Executing query: {self.query}")
            print(f"[{self.start_time.strftime('%H:%M:%S')}] Parameters: {param_str}")
            
            # Execute query with parameters (safe from SQL injection)
            self.cursor.execute(self.query, self.parameters)
            
            # Fetch results based on specified method
            if self.fetch_method == 'fetchall':
                self.query_result = self.cursor.fetchall()
            elif self.fetch_method == 'fetchone':
                self.query_result = self.cursor.fetchone()
            elif self.fetch_method == 'fetchmany':
                self.query_result = self.cursor.fetchmany()
            
            # Log execution success
            execution_time = (datetime.now() - self.start_time).total_seconds()
            result_count = len(self.query_result) if hasattr(self.query_result, '__len__') else (1 if self.query_result else 0)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Query executed successfully")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Results: {result_count} rows, Execution time: {execution_time:.3f}s")
            
            # Return results for use in 'with' block
            return self.query_result
            
        except sqlite3.Error as e:
            execution_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Database error after {execution_time:.3f}s: {e}")
            raise
        except Exception as e:
            execution_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Unexpected error after {execution_time:.3f}s: {e}")
            raise
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager - cleanup resources and handle exceptions.
        
        This method:
        1. Handles any exceptions that occurred during query execution
        2. Closes cursor and database connection
        3. Provides detailed logging of operation outcome
        4. Ensures proper resource cleanup
        
        Args:
            exc_type: Exception type (None if no exception)
            exc_value: Exception instance (None if no exception)
            traceback: Exception traceback (None if no exception)
            
        Returns:
            bool: False to propagate exceptions
        """
        try:
            # Calculate total operation time
            if self.start_time:
                total_time = (datetime.now() - self.start_time).total_seconds()
            else:
                total_time = 0
            
            # Close cursor if it exists
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            
            # Close connection if it exists
            if self.connection:
                self.connection.close()
                self.connection = None
            
            # Log operation outcome
            if exc_type is not None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Query operation failed: {exc_type.__name__}: {exc_value}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection closed (total time: {total_time:.3f}s) - WITH ERRORS")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Query operation completed successfully")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection closed (total time: {total_time:.3f}s) - SUCCESS")
            
        except Exception as cleanup_error:
            print(f"Error during resource cleanup: {cleanup_error}")
        
        # Return False to propagate any exceptions that occurred
        return False
    
    def __repr__(self):
        """String representation of the query context manager"""
        return f"ExecuteQuery(query='{self.query[:50]}...', db_name='{self.db_name}')"


class ExecuteQueryAdvanced:
    """
    Advanced version of ExecuteQuery with additional features like
    query caching, retry logic, and batch operations.
    """
    
    def __init__(self, query, parameters=None, db_name='users.db', **options):
        """
        Initialize advanced query executor with additional options.
        
        Args:
            query (str): SQL query to execute
            parameters (tuple/list): Query parameters
            db_name (str): Database file name
            **options: Additional options:
                - fetch_method: 'fetchall', 'fetchone', 'fetchmany'
                - timeout: Query timeout in seconds
                - retry_count: Number of retry attempts
                - cache_results: Whether to cache query results
        """
        self.query = query
        self.parameters = parameters or ()
        self.db_name = db_name
        
        # Parse options with defaults
        self.fetch_method = options.get('fetch_method', 'fetchall')
        self.timeout = options.get('timeout', 30)
        self.retry_count = options.get('retry_count', 0)
        self.cache_results = options.get('cache_results', False)
        
        # State tracking
        self.connection = None
        self.cursor = None
        self.start_time = None
        self.query_result = None
        
        # Cache storage
        if not hasattr(ExecuteQueryAdvanced, '_query_cache'):
            ExecuteQueryAdvanced._query_cache = {}
    
    def _get_cache_key(self):
        """Generate cache key for query"""
        import hashlib
        import json
        
        cache_data = {
            'query': self.query,
            'parameters': self.parameters,
            'fetch_method': self.fetch_method
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def __enter__(self):
        """Execute query with advanced features"""
        # Check cache first if caching is enabled
        if self.cache_results:
            cache_key = self._get_cache_key()
            if cache_key in ExecuteQueryAdvanced._query_cache:
                cached_result = ExecuteQueryAdvanced._query_cache[cache_key]
                print(f"[CACHE HIT] Returning cached result for query")
                return cached_result
        
        # Record start time
        self.start_time = datetime.now()
        
        # Attempt query execution with retry logic
        last_exception = None
        for attempt in range(self.retry_count + 1):
            try:
                # Open connection with timeout
                self.connection = sqlite3.connect(self.db_name, timeout=self.timeout)
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                
                if attempt > 0:
                    print(f"[RETRY {attempt}] Attempting query execution")
                
                # Execute query
                self.cursor.execute(self.query, self.parameters)
                
                # Fetch results
                if self.fetch_method == 'fetchall':
                    self.query_result = self.cursor.fetchall()
                elif self.fetch_method == 'fetchone':
                    self.query_result = self.cursor.fetchone()
                else:
                    self.query_result = self.cursor.fetchmany()
                
                # Cache results if caching is enabled
                if self.cache_results:
                    cache_key = self._get_cache_key()
                    ExecuteQueryAdvanced._query_cache[cache_key] = self.query_result
                    print(f"[CACHED] Query result cached for future use")
                
                # Log success
                execution_time = (datetime.now() - self.start_time).total_seconds()
                result_count = len(self.query_result) if hasattr(self.query_result, '__len__') else (1 if self.query_result else 0)
                print(f"[SUCCESS] Query executed: {result_count} rows in {execution_time:.3f}s")
                
                return self.query_result
                
            except Exception as e:
                last_exception = e
                if attempt < self.retry_count:
                    print(f"[RETRY {attempt + 1}] Query failed, retrying: {e}")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    print(f"[FAILED] Query failed after {self.retry_count + 1} attempts: {e}")
                    raise
        
        # Should not reach here
        raise last_exception
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Cleanup with advanced logging"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        
        if self.start_time:
            total_time = (datetime.now() - self.start_time).total_seconds()
            status = "SUCCESS" if exc_type is None else f"ERROR ({exc_type.__name__})"
            print(f"[CLEANUP] Query operation completed - {status} (total: {total_time:.3f}s)")
        
        return False


def setup_test_database():
    """Create and populate test database for demonstrations"""
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
    
    # Insert sample users with varied ages
    sample_users = [
        ('Alice Johnson', 'alice@example.com', 28),
        ('Bob Smith', 'bob@gmail.com', 35),
        ('Carol Davis', 'carol@yahoo.com', 42),
        ('David Wilson', 'david@gmail.com', 29),
        ('Eve Brown', 'eve@example.com', 33),
        ('Frank Miller', 'frank@outlook.com', 45),
        ('Grace Taylor', 'grace@gmail.com', 31),
        ('Henry Clark', 'henry@example.com', 38),
        ('Ivy Adams', 'ivy@gmail.com', 24),  # Under 25
        ('Jack White', 'jack@yahoo.com', 22)   # Under 25
    ]
    
    cursor.executemany(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
        sample_users
    )
    
    conn.commit()
    conn.close()
    print("Test database setup completed with 10 sample users")


def demonstrate_basic_query_execution():
    """Demonstrate basic ExecuteQuery usage"""
    print("\n" + "="*70)
    print("BASIC QUERY EXECUTION DEMONSTRATION")
    print("="*70)
    
    # Required task: Execute "SELECT * FROM users WHERE age > ?" with parameter 25
    print("Executing required query: SELECT * FROM users WHERE age > 25")
    
    with ExecuteQuery("SELECT * FROM users WHERE age > ?", (25,)) as results:
        print(f"\nQuery returned {len(results)} users over age 25:")
        print("-" * 60)
        
        for user in results:
            print(f"ID: {user['id']:2d} | Name: {user['name']:20s} | Email: {user['email']:25s} | Age: {user['age']:2d}")
    
    print("\nQuery execution completed with automatic connection management")


def demonstrate_different_fetch_methods():
    """Demonstrate different fetch methods"""
    print("\n" + "="*70)
    print("DIFFERENT FETCH METHODS DEMONSTRATION")
    print("="*70)
    
    # Fetch all results
    print("1. Using fetchall() - get all matching users:")
    with ExecuteQuery("SELECT * FROM users WHERE age > ?", (30,), fetch_method='fetchall') as results:
        print(f"   Found {len(results)} users over age 30")
    
    # Fetch one result
    print("\n2. Using fetchone() - get first matching user:")
    with ExecuteQuery("SELECT * FROM users WHERE age > ? ORDER BY age DESC", (30,), fetch_method='fetchone') as result:
        if result:
            print(f"   Oldest user over 30: {result['name']} (age {result['age']})")
        else:
            print("   No users found")
    
    # Fetch specific number of results
    print("\n3. Using fetchmany() - get limited results:")
    with ExecuteQuery("SELECT * FROM users ORDER BY name", (), fetch_method='fetchmany') as results:
        print(f"   Retrieved {len(results)} users (default fetchmany limit)")


def demonstrate_parameterized_queries():
    """Demonstrate various parameterized queries"""
    print("\n" + "="*70)
    print("PARAMETERIZED QUERIES DEMONSTRATION")
    print("="*70)
    
    # Query by age range
    print("1. Users in age range (25-35):")
    with ExecuteQuery("SELECT * FROM users WHERE age BETWEEN ? AND ?", (25, 35)) as results:
        print(f"   Found {len(results)} users between ages 25-35")
    
    # Query by email pattern
    print("\n2. Users with Gmail accounts:")
    with ExecuteQuery("SELECT name, email FROM users WHERE email LIKE ?", ('%@gmail.com',)) as results:
        print(f"   Found {len(results)} Gmail users:")
        for user in results:
            print(f"     - {user['name']}: {user['email']}")
    
    # Query specific user by ID
    print("\n3. Specific user by ID:")
    with ExecuteQuery("SELECT * FROM users WHERE id = ?", (1,), fetch_method='fetchone') as result:
        if result:
            print(f"   User ID 1: {result['name']} ({result['email']})")
    
    # Count query
    print("\n4. Count users over specific age:")
    with ExecuteQuery("SELECT COUNT(*) as user_count FROM users WHERE age > ?", (30,), fetch_method='fetchone') as result:
        print(f"   Users over age 30: {result['user_count']}")


def demonstrate_error_handling():
    """Demonstrate error handling in ExecuteQuery"""
    print("\n" + "="*70)
    print("ERROR HANDLING DEMONSTRATION")
    print("="*70)
    
    # Test with invalid SQL
    print("1. Testing invalid SQL query:")
    try:
        with ExecuteQuery("SELCT * FROM users", ()) as results:  # Typo in SELECT
            print("This should not print")
    except sqlite3.Error as e:
        print(f"   Caught expected SQL error: {e}")
    
    # Test with invalid table name
    print("\n2. Testing non-existent table:")
    try:
        with ExecuteQuery("SELECT * FROM nonexistent_table", ()) as results:
            print("This should not print")
    except sqlite3.Error as e:
        print(f"   Caught expected table error: {e}")
    
    print("\nNotice that connections were properly closed even after errors")


def demonstrate_advanced_features():
    """Demonstrate advanced ExecuteQuery features"""
    print("\n" + "="*70)
    print("ADVANCED FEATURES DEMONSTRATION")
    print("="*70)
    
    # Query with caching
    print("1. Testing query result caching:")
    
    print("   First execution (cache miss):")
    with ExecuteQueryAdvanced("SELECT * FROM users WHERE age > ?", (25,), cache_results=True) as results:
        print(f"   Retrieved {len(results)} users")
    
    print("\n   Second execution (cache hit):")
    with ExecuteQueryAdvanced("SELECT * FROM users WHERE age > ?", (25,), cache_results=True) as results:
        print(f"   Retrieved {len(results)} users from cache")
    
    # Query with retry logic
    print("\n2. Testing retry logic (simulated):")
    with ExecuteQueryAdvanced("SELECT COUNT(*) as count FROM users", (), retry_count=2, fetch_method='fetchone') as result:
        print(f"   Total users: {result['count']}")


# Main execution and testing
if __name__ == "__main__":
    # Setup test database
    setup_test_database()
    
    # Run demonstrations
    demonstrate_basic_query_execution()
    demonstrate_different_fetch_methods()
    demonstrate_parameterized_queries() 
    demonstrate_error_handling()
    demonstrate_advanced_features()
    
    print("\n" + "="*70)
    print("QUERY EXECUTION CONTEXT MANAGER DEMONSTRATIONS COMPLETED")
    print("="*70)
    print("\nKey Benefits Demonstrated:")
    print("- Automatic connection and cursor management")
    print("- SQL injection protection via parameterized queries")
    print("- Flexible fetch methods (fetchall, fetchone, fetchmany)")
    print("- Comprehensive error handling and logging")
    print("- Query performance tracking")
    print("- Advanced features (caching, retry logic)")
    print("- Reusable for any SELECT query")
    
    print(f"\nTest database 'users.db' remains available for further testing")
    print("ExecuteQuery context manager implementation complete!")
