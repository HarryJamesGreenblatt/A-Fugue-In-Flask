"""
Direct Database Connection Test Script

This script tests a direct connection to Azure SQL Database using pyodbc.
It bypasses SQLAlchemy to help diagnose connection issues.
"""
import os
import sys
import pyodbc
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_direct_connection():
    """Test direct connection to the database using pyodbc"""
    try:
        # Connection parameters
        server = os.environ.get('DB_SERVER', 'sequitur-sql-server.database.windows.net')
        database = os.environ.get('DB_NAME', 'fugue-flask-db')
        username = os.environ.get('DB_USERNAME', 'sqladmin')
        password = os.environ.get('DB_PASSWORD', 'SecureP@ssw0rd!')
        
        # Log connection attempt (with masked password)
        logger.info(f"Connecting to {server}, database: {database}, user: {username}")
        
        # Connection string
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        # Establish connection
        logger.info("Establishing connection...")
        conn = pyodbc.connect(conn_str)
        
        # Execute a simple query
        cursor = conn.cursor()
        logger.info("Executing test query...")
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        
        # Print result
        if row:
            logger.info(f"Connection successful! SQL Server version: {row[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        logger.info("Connection closed properly")
        return True
    
    except Exception as e:
        logger.error(f"Direct database connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting direct database connection test...")
    
    # Test the connection
    result = test_direct_connection()
    
    if result:
        logger.info("✅ Direct database connection test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Direct database connection test FAILED")
        sys.exit(1)