"""
Diagnostic Wrapper for Flask Application

This script runs the Flask application with enhanced error monitoring and logging.
It captures detailed diagnostic information about database connections and startup errors.
Uses environment variables for credentials following Azure security best practices.
"""
import os
import sys
import time
import logging
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask_diagnostics.log', mode='w')
    ]
)
logger = logging.getLogger("diagnostics")

# Override problematic database connection with working one if needed
# This is critical - set before importing app modules
os.environ['USE_OVERRIDE_DB_URI'] = 'True'

# Import app-specific modules
try:
    from app import create_app
    import pyodbc
    import sqlalchemy
    from sqlalchemy import text
    from config import active_config
except Exception as e:
    logger.critical(f"Failed to import required modules: {str(e)}")
    logger.critical(traceback.format_exc())
    sys.exit(1)

def print_separator(title):
    """Print a separator line with a title for better log readability"""
    line = f"{'=' * 20} {title} {'=' * 20}"
    logger.info(line)
    print(line)

def check_odbc_drivers():
    """Check available ODBC drivers"""
    print_separator("ODBC DRIVERS")
    try:
        drivers = pyodbc.drivers()
        logger.info(f"Available ODBC drivers: {drivers}")
        if not drivers:
            logger.warning("No ODBC drivers found!")
        else:
            sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
            if sql_server_drivers:
                logger.info(f"SQL Server drivers found: {sql_server_drivers}")
            else:
                logger.warning("No SQL Server ODBC drivers found!")
        return drivers
    except Exception as e:
        logger.error(f"Error checking ODBC drivers: {e}")
        return []

def check_environment_variables():
    """Check critical environment variables"""
    print_separator("ENVIRONMENT VARIABLES")
    critical_vars = [
        'FLASK_CONFIG', 'USE_CENTRALIZED_DB', 'DB_SERVER', 'DB_NAME',
        'TEMPLATE_DATABASE_URI', 'DATABASE_URI', 'DEV_DATABASE_URI',
        'OVERRIDE_DB_URI', 'USE_OVERRIDE_DB_URI'
    ]
    
    for var in critical_vars:
        value = os.environ.get(var)
        masked_value = value
        # Mask sensitive information in connection strings
        if var in ['TEMPLATE_DATABASE_URI', 'DATABASE_URI', 'DEV_DATABASE_URI', 'OVERRIDE_DB_URI'] and value:
            if '@' in value and ':' in value.split('@')[0]:
                parts = value.split('@')
                auth_parts = parts[0].split(':')
                if len(auth_parts) > 1:
                    masked_value = f"{auth_parts[0]}:******@{parts[1]}"
                
        logger.info(f"{var}: {masked_value}")
    
    # Check for Azure App Service specific variables
    azure_vars = ['WEBSITE_SITE_NAME', 'WEBSITE_HOSTNAME']
    is_azure = any(os.environ.get(var) for var in azure_vars)
    logger.info(f"Running on Azure App Service: {is_azure}")

def check_database_connection():
    """Test database connection with several methods"""
    print_separator("DATABASE CONNECTION TEST")
    
    # Use the override URI from environment if available, or build one from components
    db_uri = os.environ.get('OVERRIDE_DB_URI')
    if not db_uri:
        # Get credentials from environment variables
        server = os.environ.get('DB_SERVER', 'sequitur-sql-server.database.windows.net')
        database = os.environ.get('DB_NAME', 'fugue-flask-db')
        username = os.environ.get('DB_USERNAME', 'sqladmin')
        password = os.environ.get('DB_PASSWORD')
        
        if not password:
            logger.error("DB_PASSWORD environment variable is not set. Please create a .env file based on .env.template")
            return False
            
        # Build a standard connection string
        db_uri = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&timeout=30"
    
    # Mask password in connection string for logging
    masked_uri = db_uri
    if '@' in db_uri and ':' in db_uri.split('@')[0]:
        parts = db_uri.split('@')
        auth_parts = parts[0].split(':')
        if len(auth_parts) > 1:
            masked_uri = f"{auth_parts[0]}:******@{parts[1]}"
    
    logger.info(f"Testing connection to: {masked_uri}")
    
    # Get database parameters if using SQL Server
    if 'mssql' in db_uri:
        try:
            # Parse the connection string to extract server, database, etc.
            if '@' in db_uri:
                server_part = db_uri.split('@')[1].split('/')[0]
                database = db_uri.split('/')[1].split('?')[0] if '/' in db_uri else None
                logger.info(f"Server: {server_part}")
                logger.info(f"Database: {database}")
                
                # Check if we're using the tcp: prefix format
                if 'tcp:' in server_part:
                    logger.info("Using TCP format with explicit port")
                else:
                    logger.warning("Not using TCP format with explicit port - this might cause connection issues")
        except Exception as e:
            logger.error(f"Error parsing connection string: {e}")
    
    # Try SQLAlchemy connection
    try:
        logger.info("Trying SQLAlchemy connection...")
        engine = sqlalchemy.create_engine(
            db_uri,
            connect_args={
                "connect_timeout": 90,
                "driver": "{ODBC Driver 17 for SQL Server}",
                "TrustServerCertificate": "yes",
                "ApplicationIntent": "ReadWrite"
            },
            echo=True
        )
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 AS test_value")).fetchone()
            logger.info(f"SQLAlchemy connection success! Test value: {result.test_value}")
            return True
    except Exception as e:
        logger.error(f"SQLAlchemy connection failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        # If SQLAlchemy fails, try direct PyODBC connection for SQL Server
        if 'mssql' in db_uri:
            try:
                logger.info("Trying direct PyODBC connection...")
                
                # Extract connection parameters from environment variables
                server = os.environ.get('DB_SERVER', 'sequitur-sql-server.database.windows.net')
                database = os.environ.get('DB_NAME', 'fugue-flask-db')
                username = os.environ.get('DB_USERNAME', 'sqladmin')
                password = os.environ.get('DB_PASSWORD')
                
                if not password:
                    logger.error("DB_PASSWORD environment variable is not set")
                    return False
                
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER=tcp:{server},1433;"
                    f"DATABASE={database};"
                    f"UID={username};"
                    f"PWD={password};"
                    f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=90;"
                )
                
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                row = cursor.execute("SELECT 1 AS test_value").fetchone()
                logger.info(f"Direct connection success! Test value: {row.test_value}")
                conn.close()
                
                logger.info("The SQLAlchemy connection failed but direct PyODBC connection worked!")
                logger.info("This suggests an issue with the SQLAlchemy connection string format.")
            except Exception as e:
                logger.error(f"Direct connection also failed: {str(e)}")
                logger.error(traceback.format_exc())
    
    return False

def apply_db_override_patch():
    """
    Patch the config module to use our known working connection string.
    This ensures the Flask app uses the connection string we know works.
    """
    print_separator("APPLYING DATABASE CONNECTION PATCH")
    
    from config import config_by_name, active_config
    
    # Define a patching function for each config class
    def patch_config_class(config_class):
        if os.environ.get('USE_OVERRIDE_DB_URI') == 'True':
            logger.info(f"Patching {config_class.__name__} to use override database URI")
            
            # Use environment variables to get credentials
            server = os.environ.get('DB_SERVER', 'sequitur-sql-server.database.windows.net')
            database = os.environ.get('DB_NAME', 'fugue-flask-db')
            username = os.environ.get('DB_USERNAME', 'sqladmin')
            password = os.environ.get('DB_PASSWORD')
            
            if not password:
                logger.error("DB_PASSWORD environment variable is not set")
                # We won't override with an invalid connection string
                return
                
            # Build a working URI
            override_uri = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&timeout=30"
            
            # Override the database URI
            setattr(config_class, 'SQLALCHEMY_DATABASE_URI', override_uri)
            
            # Set appropriate engine options that work with Azure SQL
            engine_options = {
                'pool_pre_ping': True,
                'pool_recycle': 300, 
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'connect_args': {
                    'connect_timeout': 90,
                    'driver': '{ODBC Driver 17 for SQL Server}',
                    'TrustServerCertificate': 'yes',
                    'Encrypt': 'yes'
                }
            }
            
            setattr(config_class, 'SQLALCHEMY_ENGINE_OPTIONS', engine_options)
            logger.info(f"Database URI and engine options patched for {config_class.__name__}")
    
    # Patch all config classes
    try:
        for config_name, config_class in config_by_name.items():
            patch_config_class(config_class)
        
        logger.info("All configuration classes have been patched with working database connection")
    except Exception as e:
        logger.error(f"Failed to patch config classes: {e}")
        logger.error(traceback.format_exc())

def run_flask_app_with_monitoring():
    """Run the Flask app with enhanced error monitoring"""
    print_separator("STARTING FLASK APPLICATION")
    
    try:
        # Check environment before starting app
        check_odbc_drivers()
        check_environment_variables()
        
        # Apply the patch to use the working connection string
        apply_db_override_patch()
        
        # Test the connection after patching
        check_database_connection()
        
        # Create and run the Flask app
        logger.info("Creating Flask app with config: " + os.environ.get('FLASK_CONFIG', 'default'))
        app = create_app()
        
        # Run the app
        logger.info("Starting Flask application...")
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        logger.critical(f"Flask application failed to start: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    print_separator("FLASK DIAGNOSTICS TOOL")
    logger.info("Starting diagnostic wrapper for Flask application")
    run_flask_app_with_monitoring()