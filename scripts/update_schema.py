"""
Azure SQL Schema Update Script

This script updates the Azure SQL database schema to match the Flask SQLAlchemy models.
It adds missing columns to existing tables.
"""
import os
import sys
import pyodbc
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("schema_update")

# Azure SQL connection parameters
SERVER = "sequitur-sql-server.database.windows.net"
DATABASE = "fugue-flask-db"
USERNAME = "sqladmin"
PASSWORD = "SecureP@ssw0rd!"

def connect_to_db():
    """Create a connection to the Azure SQL database"""
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD}"
    )
    
    try:
        logger.info(f"Connecting to {SERVER}/{DATABASE}...")
        conn = pyodbc.connect(conn_str)
        logger.info("Connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def check_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        AND COLUMN_NAME = '{column_name}'
        """)
        result = cursor.fetchone()[0]
        return result > 0
    except Exception as e:
        logger.error(f"Error checking if column exists: {e}")
        return False

def add_column_if_missing(conn, table_name, column_name, column_type, default_value=None):
    """Add a column to a table if it doesn't already exist"""
    try:
        if not check_column_exists(conn, table_name, column_name):
            cursor = conn.cursor()
            
            # Build the ALTER TABLE statement
            sql = f"ALTER TABLE {table_name} ADD {column_name} {column_type}"
            
            # Add default value if specified
            if default_value is not None:
                if isinstance(default_value, str):
                    sql += f" DEFAULT '{default_value}'"
                else:
                    sql += f" DEFAULT {default_value}"
            
            cursor.execute(sql)
            conn.commit()
            logger.info(f"Added column {column_name} to table {table_name}")
            return True
        else:
            logger.info(f"Column {column_name} already exists in table {table_name}")
            return False
    except Exception as e:
        logger.error(f"Error adding column: {e}")
        conn.rollback()
        return False

def main():
    """Main function to update the database schema"""
    logger.info("Starting schema update...")
    
    # Connect to the database
    conn = connect_to_db()
    if not conn:
        logger.error("Failed to connect to database. Exiting.")
        return
    
    try:
        # Add missing columns to users table
        add_column_if_missing(conn, "users", "is_active", "BIT", 1)
        
        # Additional columns can be added here as needed
        
        logger.info("Schema update completed successfully!")
        
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main()