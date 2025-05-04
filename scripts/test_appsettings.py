"""
Test script to verify the connection string in appsettings.json

This script directly tests the connection string from appsettings.json
to isolate any issues with Azure SQL Database connectivity.
"""
import os
import sys
import json
import time
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
import pyodbc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mask_connection_string(conn_string):
    """Mask sensitive information in connection strings for secure logging"""
    if not conn_string:
        return "No connection string provided"
    
    try:
        # Handle mssql+pyodbc format
        if conn_string.startswith('mssql+pyodbc'):
            # Split by standard delimiters
            parts = conn_string.split('@')
            if len(parts) >= 2:
                # Get the first part with credentials
                cred_part = parts[0]
                # Find the username:password section
                if ':' in cred_part:
                    username_part = cred_part.split(':')[0]
                    # Reconstruct with masked password
                    return f"{username_part}:******@{parts[1]}"
        
        return "Masked connection string (unknown format)"
    
    except Exception as e:
        logger.warning(f"Error masking connection string: {str(e)}")
        return "Masked connection string (error)"

def check_drivers():
    """Check available ODBC drivers"""
    drivers = pyodbc.drivers()
    logger.info(f"Available ODBC drivers: {drivers}")
    sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
    if not sql_server_drivers:
        logger.error("No SQL Server drivers found! Please install the ODBC Driver for SQL Server.")
        sys.exit(1)
    logger.info(f"SQL Server drivers: {sql_server_drivers}")
    return sql_server_drivers

def load_appsettings():
    """Load connection string from appsettings.json"""
    try:
        app_settings_path = Path(__file__).parent.parent / "appsettings.json"
        logger.info(f"Loading appsettings from {app_settings_path}")
        
        with open(app_settings_path, 'r') as f:
            settings = json.load(f)
            
        if "TEMPLATE_DATABASE_URI" in settings:
            conn_string = settings["TEMPLATE_DATABASE_URI"]
            logger.info(f"Found connection string: {mask_connection_string(conn_string)}")
            return conn_string
        else:
            logger.error("No TEMPLATE_DATABASE_URI found in appsettings.json")
            return None
    except Exception as e:
        logger.error(f"Error loading appsettings.json: {e}")
        return None

def test_connection(conn_string):
    """Test connection to Azure SQL Database"""
    logger.info("Testing connection to Azure SQL Database...")
    logger.info(f"Connection string: {mask_connection_string(conn_string)}")
    
    try:
        # Create engine with echo for logging
        logger.info("Creating SQLAlchemy engine...")
        engine = create_engine(conn_string, echo=True)
        
        # Test connection with timeout and retries
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"Connection attempt {retry_count + 1}/{max_retries}...")
                with engine.connect() as connection:
                    logger.info("Connection established! Executing test query...")
                    result = connection.execute(text("SELECT @@VERSION AS version"))
                    row = result.fetchone()
                    logger.info(f"Connection successful!")
                    logger.info(f"SQL Server version: {row.version}")
                    return True
            except Exception as e:
                logger.error(f"Connection attempt {retry_count + 1} failed: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        logger.error(f"All {max_retries} connection attempts failed.")
        return False
        
    except Exception as e:
        logger.error(f"Error setting up connection: {e}")
        return False

if __name__ == "__main__":
    logger.info("========== Testing appsettings.json SQL Connection ==========")
    
    # Check ODBC drivers
    check_drivers()
    
    # Load connection string from appsettings.json
    conn_string = load_appsettings()
    if not conn_string:
        logger.error("Could not load connection string from appsettings.json")
        sys.exit(1)
    
    # Test the connection
    success = test_connection(conn_string)
    
    if success:
        logger.info("✅ Connection test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Connection test FAILED")
        sys.exit(1)