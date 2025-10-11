"""
Database Connection Test Script

This script tests the connection to the centralized database in Azure.
It uses the configuration from config.py which handles both local environment
variables and Azure Key Vault integration.

Usage:
    python scripts/test_db_connection.py
"""
import os
import sys
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config import active_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test connection to the database using current configuration"""
    try:
        # Determine which connection string to use based on configuration
        if active_config.USE_CENTRALIZED_DB:
            # If using centralized DB, ensure we're using the DATABASE_URI or constructed URI
            if os.environ.get('DATABASE_URI'):
                db_uri = os.environ.get('DATABASE_URI')
                logger.info("Using DATABASE_URI environment variable for centralized database")
            elif all([os.environ.get(var) for var in ['DB_SERVER', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']]):
                # Construct connection string from components
                server = os.environ.get('DB_SERVER')
                database = os.environ.get('DB_NAME')
                username = os.environ.get('DB_USERNAME')
                password = os.environ.get('DB_PASSWORD')
                logger.info(f"Constructing connection string for {server}/{database}")
                db_uri = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
            else:
                # Fall back to config's URI which may still be SQLite for dev environment
                db_uri = active_config.SQLALCHEMY_DATABASE_URI
                logger.info("Using SQLALCHEMY_DATABASE_URI from active config")
        else:
            # Not using centralized DB, use standard config URI
            db_uri = active_config.SQLALCHEMY_DATABASE_URI
            logger.info("Using standard SQLALCHEMY_DATABASE_URI from config")
        
        logger.info(f"Database URI from config: {type(db_uri)}")
        
        # Mask password for logging if present
        masked_uri = db_uri
        if '@' in db_uri and ':' in db_uri.split('@')[0]:
            parts = db_uri.split('@')
            credentials = parts[0].split(':')
            if len(credentials) > 2:  # username:password:
                masked_uri = f"{credentials[0]}:******@{parts[1]}"
            else:
                masked_uri = f"{credentials[0]}:******@{parts[1]}"
        
        logger.info(f"Testing connection to: {masked_uri}")
        
        # Create engine with connection pooling settings for better performance
        logger.info("Creating SQLAlchemy engine...")
        engine = create_engine(db_uri, pool_size=5, max_overflow=10, pool_timeout=30, echo=True)
        
        # Test connection with a simple query
        logger.info("Attempting to connect to database...")
        with engine.connect() as connection:
            logger.info("Connection established, executing test query...")
            result = connection.execute(text("SELECT 1 AS test"))
            for row in result:
                logger.info(f"Connection successful! Test result: {row.test}")
                
        logger.info("Database connection test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Starting database connection test...")
    
    # Print current configuration
    logger.info(f"Active config: {active_config.__class__.__name__}")
    logger.info(f"USE_CENTRALIZED_DB: {active_config.USE_CENTRALIZED_DB}")
    logger.info(f"DB_SERVER: {active_config.DB_SERVER}")
    logger.info(f"DB_NAME: {active_config.DB_NAME}")
    
    # For Azure configurations, log additional info
    if hasattr(active_config, 'USE_CENTRALIZED_DB') and active_config.USE_CENTRALIZED_DB:
        if os.environ.get('TEMPLATE_DATABASE_URI'):
            logger.info("Using TEMPLATE_DATABASE_URI from environment")
        elif all([os.environ.get(var) for var in ['DB_SERVER', 'DB_NAME', 'DB_USERNAME']]):
            logger.info("Using DB_SERVER, DB_NAME and DB_USERNAME environment variables")
    
    # Test the connection
    result = test_connection()
    
    if result:
        logger.info("✅ Database connection test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Database connection test FAILED")
        sys.exit(1)