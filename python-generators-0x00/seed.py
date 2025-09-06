#!/usr/bin/env python3
"""
Database seeding script for ALX_prodev database
This script sets up MySQL database, creates tables, and populates data from CSV
"""

import mysql.connector
from mysql.connector import Error
import csv
import os
import uuid
from decimal import Decimal


def connect_db():
    """
    Connects to the MySQL database server (without specifying a database)
    
    Returns:
        connection object if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Change this to your MySQL username
            password='root'  # Change this to your MySQL password
        )
        if connection.is_connected():
            print("Successfully connected to MySQL server")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def create_database(connection):
    """
    Creates the ALX_prodev database if it doesn't exist
    
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database ALX_prodev created successfully (or already exists)")
        cursor.close()
    except Error as e:
        print(f"Error creating database: {e}")


def connect_to_prodev():
    """
    Connects specifically to the ALX_prodev database
    
    Returns:
        connection object to ALX_prodev database if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='ALX_prodev',
            user='root',  # Change this to your MySQL username
            password='root'  # Change this to your MySQL password
        )
        if connection.is_connected():
            print("Successfully connected to ALX_prodev database")
            return connection
    except Error as e:
        print(f"Error connecting to ALX_prodev database: {e}")
        return None


def create_table(connection):
    """
    Creates the user_data table if it doesn't exist
    
    Args:
        connection: MySQL connection object to ALX_prodev database
    """
    try:
        cursor = connection.cursor()
        
        # SQL query to create user_data table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_data (
            user_id CHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            age DECIMAL(3,0) NOT NULL,
            INDEX idx_user_id (user_id)
        )
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        print("Table user_data created successfully")
        cursor.close()
        
    except Error as e:
        print(f"Error creating table: {e}")


def insert_data(connection, csv_file):
    """
    Inserts data from CSV file into the user_data table
    Only inserts data if it doesn't already exist (prevents duplicates)
    
    Args:
        connection: MySQL connection object to ALX_prodev database
        csv_file: path to the CSV file containing user data
    """
    try:
        cursor = connection.cursor()
        
        # First check if table already has data
        cursor.execute("SELECT COUNT(*) FROM user_data")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Table already contains {count} records. Skipping data insertion.")
            cursor.close()
            return
        
        # Read and insert data from CSV
        if not os.path.exists(csv_file):
            print(f"CSV file {csv_file} not found!")
            return
            
        insert_query = """
        INSERT IGNORE INTO user_data (user_id, name, email, age) 
        VALUES (%s, %s, %s, %s)
        """
        
        inserted_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    # Validate and process data
                    user_id = row.get('user_id', '').strip()
                    name = row.get('name', '').strip()
                    email = row.get('email', '').strip()
                    age_str = row.get('age', '').strip()
                    
                    # Skip empty rows
                    if not all([user_id, name, email, age_str]):
                        continue
                    
                    # Validate UUID format
                    try:
                        uuid.UUID(user_id)
                    except ValueError:
                        print(f"Invalid UUID format: {user_id}. Skipping row.")
                        continue
                    
                    # Validate age
                    try:
                        age = Decimal(age_str)
                        if age < 0 or age > 150:  # Basic age validation
                            print(f"Invalid age: {age}. Skipping row.")
                            continue
                    except (ValueError, TypeError):
                        print(f"Invalid age format: {age_str}. Skipping row.")
                        continue
                    
                    # Insert the record
                    cursor.execute(insert_query, (user_id, name, email, age))
                    inserted_count += 1
                    
                except Exception as row_error:
                    print(f"Error processing row: {row_error}")
                    continue
        
        connection.commit()
        print(f"Successfully inserted {inserted_count} records into user_data table")
        cursor.close()
        
    except Error as e:
        print(f"Error inserting data: {e}")
    except FileNotFoundError:
        print(f"CSV file {csv_file} not found!")
    except Exception as e:
        print(f"Unexpected error: {e}")


def validate_database_setup():
    """
    Helper function to validate that the database setup was successful
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        connection = connect_to_prodev()
        if not connection:
            return False, "Could not connect to ALX_prodev database"
        
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'ALX_prodev' 
            AND table_name = 'user_data'
        """)
        
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            return False, "user_data table does not exist"
        
        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM user_data")
        record_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return True, f"Database setup successful. {record_count} records in user_data table"
        
    except Error as e:
        return False, f"Database validation error: {e}"


# Additional utility functions for debugging and maintenance

def get_sample_data(limit=5):
    """
    Retrieves sample data from the user_data table
    
    Args:
        limit: number of records to retrieve
        
    Returns:
        list of tuples containing sample data
    """
    try:
        connection = connect_to_prodev()
        if not connection:
            return []
        
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM user_data LIMIT {limit}")
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
        
    except Error as e:
        print(f"Error retrieving sample data: {e}")
        return []


def cleanup_database():
    """
    Utility function to drop the database (use with caution!)
    """
    try:
        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DROP DATABASE IF EXISTS ALX_prodev")
            print("Database ALX_prodev dropped successfully")
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error dropping database: {e}")


if __name__ == "__main__":
    """
    Main execution block for testing the script independently
    """
    print("Setting up ALX_prodev database...")
    
    # Step 1: Connect to MySQL server
    connection = connect_db()
    if not connection:
        print("Failed to connect to MySQL server. Exiting.")
        exit(1)
    
    # Step 2: Create database
    create_database(connection)
    connection.close()
    
    # Step 3: Connect to the specific database
    connection = connect_to_prodev()
    if not connection:
        print("Failed to connect to ALX_prodev database. Exiting.")
        exit(1)
    
    # Step 4: Create table
    create_table(connection)
    
    # Step 5: Insert data (assumes user_data.csv exists in current directory)
    insert_data(connection, 'user_data.csv')
    
    # Step 6: Validate setup
    success, message = validate_database_setup()
    print(f"Setup validation: {message}")
    
    # Step 7: Show sample data
    sample_data = get_sample_data(5)
    if sample_data:
        print("Sample data:")
        for row in sample_data:
            print(row)
    
    connection.close()
    print("Database setup completed!")
