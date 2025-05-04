"""
Database Connection Diagnostic Script

This script checks which database connection string is actually being used by your application.
It loads all available configuration settings and prints out the connection details.

Usage:
    python scripts/check_db_connection.py
"""
import os
import sys
from pathlib import Path
import pyodbc

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config import active_config, Config, AzureConfig, DevelopmentConfig, ProductionConfig
import logging

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
        
        # Handle standard connection strings with username/password
        if '@' in conn_string:
            parts = conn_string.split('@')
            if len(parts) < 2:
                return "Masked connection string (invalid format)"
            
            auth_parts = parts[0].split(':')
            if len(auth_parts) >= 2:  # username:password
                return f"{auth_parts[0]}:******@{parts[1]}"
        
        # SQLite connections
        if conn_string.startswith('sqlite:'):
            return conn_string  # No sensitive data to mask
            
        return "Masked connection string (unknown format)"
    
    except Exception as e:
        logger.warning(f"Error masking connection string: {str(e)}")
        return "Masked connection string (error)"

def check_driver_availability():
    """Check if ODBC drivers for SQL Server are available"""
    try:
        drivers = pyodbc.drivers()
        logger.info(f"Available ODBC drivers: {drivers}")
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
        
        if sql_server_drivers:
            logger.info(f"SQL Server drivers found: {sql_server_drivers}")
            return True
        else:
            logger.warning("No SQL Server ODBC drivers found!")
            return False
    except Exception as e:
        logger.error(f"Error checking ODBC drivers: {str(e)}")
        return False

def print_env_vars():
    """Print relevant environment variables"""
    relevant_vars = [
        'FLASK_CONFIG', 
        'USE_CENTRALIZED_DB', 
        'DB_SERVER', 
        'DB_NAME', 
        'DEV_DATABASE_URI', 
        'TEST_DATABASE_URI',
    ]
    
    logger.info("Environment Variables:")
    for var in relevant_vars:
        # Don't log actual passwords
        if var != 'DB_PASSWORD':
            value = os.environ.get(var, 'Not set')
            logger.info(f"  {var}: {value}")

def test_database_connections():
    """Test various database connections to identify which one works"""
    
    # Get the actual connection string from active config
    active_uri = active_config.SQLALCHEMY_DATABASE_URI
    logger.info(f"Active config class: {active_config.__class__.__name__}")
    logger.info(f"Active SQLALCHEMY_DATABASE_URI: {mask_connection_string(active_uri)}")
    
    # Check centralized DB flag
    centralized = getattr(active_config, 'USE_CENTRALIZED_DB', False)
    logger.info(f"USE_CENTRALIZED_DB flag: {centralized}")
    
    # Try the direct DATABASE_URI from environment
    env_uri = os.environ.get('DATABASE_URI')
    if env_uri:
        logger.info(f"DATABASE_URI from environment: {mask_connection_string(env_uri)}")
        try_connection(env_uri, "Direct DATABASE_URI from environment")
    else:
        logger.info("DATABASE_URI not set in environment")
    
    # Check SQL components
    if all([os.environ.get(var) for var in ['DB_SERVER', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']]):
        server = os.environ.get('DB_SERVER')
        database = os.environ.get('DB_NAME')
        username = os.environ.get('DB_USERNAME')
        password = os.environ.get('DB_PASSWORD')
        
        # Construct test string
        test_uri = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
        logger.info(f"Constructed URI: {mask_connection_string(test_uri)}")
        try_connection(test_uri, "Constructed from DB_* variables")
    
    # Try the active config's URI
    try_connection(active_uri, "Active Config's SQLALCHEMY_DATABASE_URI")
    
    # Specific case for centralized DB in DevelopmentConfig
    if isinstance(active_config, DevelopmentConfig) and centralized:
        logger.info("Note: DevelopmentConfig with centralized=True might still use SQLite if DATABASE_URI is not in env")

def try_connection(uri, description):
    """Try to connect to a database with the given URI"""
    logger.info(f"\nTrying connection: {description}")
    logger.info(f"URI: {mask_connection_string(uri)}")
    
    try:
        engine = create_engine(uri)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 AS test"))
            for row in result:
                logger.info(f"✅ Connection SUCCESSFUL: {description}")
                logger.info(f"   Result: {row.test}")
                return True
    except Exception as e:
        logger.error(f"❌ Connection FAILED: {description}")
        logger.error(f"   Error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("===== Database Connection Diagnostics =====")
    
    # Print environment info
    print_env_vars()
    
    # Check ODBC drivers
    check_driver_availability()
    
    # Test connections
    test_database_connections()