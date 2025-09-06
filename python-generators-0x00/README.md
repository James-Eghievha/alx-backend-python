# Python Generators - Database Seeding Project

## Project Overview

This project is part of an advanced Python generators learning series focused on building an Airbnb clone. The current phase involves setting up a MySQL database and populating it with user data from a CSV file, which will later be used with Python generators for efficient data streaming.

## Learning Objectives

- **Database Connection Management**: Learn to establish and manage MySQL database connections
- **Schema Design**: Create databases and tables programmatically with proper data types and indexing
- **CSV Data Processing**: Efficiently read and process CSV data with validation
- **Error Handling**: Implement robust error handling for database operations
- **Data Integrity**: Ensure data consistency and prevent duplicate entries
- **Memory Efficiency**: Prepare foundation for generator-based data streaming

## Prerequisites

### Software Requirements
- Python 3.6+
- MySQL Server 8.0+
- pip package manager

### Python Dependencies
```bash
pip install mysql-connector-python
```

### MySQL Setup
1. Install MySQL Server
2. Create a user with appropriate privileges
3. Update connection credentials in `seed.py`

## Project Structure

```
python-generators-0x00/
├── seed.py              # Main database seeding script
├── 0-main.py           # Test script (provided by instructor)
├── user_data.csv       # Sample data file (downloaded from provided URL)
├── README.md           # This documentation file
└── requirements.txt    # Python dependencies
```

## Database Schema

### Database: `ALX_prodev`

### Table: `user_data`
| Column   | Type        | Constraints                    |
|----------|-------------|--------------------------------|
| user_id  | CHAR(36)    | PRIMARY KEY, UUID format       |
| name     | VARCHAR(255)| NOT NULL                       |
| email    | VARCHAR(255)| NOT NULL                       |
| age      | DECIMAL(3,0)| NOT NULL, Range: 0-150         |

### Indexes
- `idx_user_id` on `user_id` column for optimized queries

## Function Documentation

### `connect_db()`
Establishes connection to MySQL server without specifying a database.

**Returns**: 
- MySQL connection object on success
- None on failure

**Usage**: Initial connection for database creation

### `create_database(connection)`
Creates the `ALX_prodev` database if it doesn't exist.

**Parameters**:
- `connection`: MySQL connection object

**Features**:
- Uses `IF NOT EXISTS` clause to prevent errors
- Safe to run multiple times

### `connect_to_prodev()`
Establishes connection specifically to the `ALX_prodev` database.

**Returns**:
- MySQL connection object to ALX_prodev database
- None on failure

### `create_table(connection)`
Creates the `user_data` table with specified schema.

**Parameters**:
- `connection`: MySQL connection object to ALX_prodev

**Features**:
- Creates table with proper data types
- Adds index on user_id for performance
- Uses `IF NOT EXISTS` for safety

### `insert_data(connection, csv_file)`
Reads CSV file and inserts data into user_data table.

**Parameters**:
- `connection`: MySQL connection object to ALX_prodev
- `csv_file`: Path to CSV file containing user data

**Features**:
- Validates UUID format
- Checks for duplicate data before insertion
- Implements comprehensive error handling
- Validates age ranges
- Skips malformed records gracefully

## Data Validation

The script implements several validation layers:

1. **UUID Validation**: Ensures user_id follows proper UUID format
2. **Age Validation**: Checks age is numeric and within reasonable range (0-150)
3. **Required Fields**: Validates all required fields are present
4. **Duplicate Prevention**: Uses `INSERT IGNORE` to prevent duplicate entries
5. **Data Type Conversion**: Safely converts string data to appropriate types

## Error Handling

The script includes comprehensive error handling for:
- MySQL connection failures
- Database creation errors
- Table creation issues
- CSV file reading problems
- Data validation failures
- Individual record processing errors

## Usage

### Basic Usage
```python
#!/usr/bin/python3

seed = __import__('seed')

# Step 1: Connect and create database
connection = seed.connect_db()
if connection:
    seed.create_database(connection)
    connection.close()

# Step 2: Connect to ALX_prodev database
connection = seed.connect_to_prodev()
if connection:
    # Step 3: Create table
    seed.create_table(connection)
    
    # Step 4: Insert data from CSV
    seed.insert_data(connection, 'user_data.csv')
    
    connection.close()
```

### Running the Test Script
```bash
./0-main.py
```

### Running Standalone
```bash
python3 seed.py
```

## Data Source

The sample data should be downloaded from: https://savanna.alxafrica.com/rltoken/kPrtJ_hN0TXKgEfwKY4vHg

Expected CSV format:
```csv
user_id,name,email,age
00234e50-34eb-4ce2-94ec-26e3fa749796,Dan Altenwerth Jr.,Molly59@gmail.com,67
006bfede-724d-4cdd-a2a6-59700f40d0da,Glenda Wisozk,Miriam21@gmail.com,119
...
```

## Configuration

Before running the script, update the database connection parameters in `seed.py`:

```python
# In connect_db() and connect_to_prodev() functions
connection = mysql.connector.connect(
    host='localhost',          # Your MySQL host
    user='your_username',      # Your MySQL username
    password='your_password'   # Your MySQL password
)
```

## Performance Considerations

- **Indexing**: Primary key and additional index on user_id for fast lookups
- **Batch Processing**: Processes CSV data row by row to manage memory
- **Connection Management**: Proper opening and closing of database connections
- **Error Resilience**: Continues processing even if individual records fail

## Future Integration with Generators

This database setup prepares for the next phase where Python generators will be used to:
- Stream database rows one by one
- Process large datasets without loading entire result sets into memory
- Implement efficient pagination and filtering
- Handle real-time data updates

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check MySQL server is running
   - Verify connection credentials
   - Ensure user has necessary privileges

2. **CSV File Not Found**
   - Download the CSV file from the provided URL
   - Ensure file is in the correct directory
   - Check file permissions

3. **Data Type Errors**
   - Verify CSV data format matches expected schema
   - Check for special characters in data
   - Ensure age values are numeric

4. **Permission Errors**
   - Grant necessary MySQL privileges to user
   - Check file system permissions for CSV file

### Debug Mode

Enable additional logging by modifying the script:
```python
# Add at the top of seed.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When extending this project:
1. Maintain the existing function signatures
2. Add comprehensive error handling
3. Include data validation for new fields
4. Update documentation for any changes
5. Test with various data scenarios

## Next Steps

This database seeding script sets the foundation for:
1. **Generator Implementation**: Creating generators to stream database data
2. **Memory Optimization**: Processing large datasets efficiently
3. **Real-time Updates**: Handling live data updates
4. **Advanced Querying**: Implementing complex data filtering and aggregation

The focus will shift to leveraging Python's `yield` keyword to create memory-efficient data processing pipelines for the Airbnb clone application.
