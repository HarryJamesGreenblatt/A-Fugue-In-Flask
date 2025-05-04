"""
Application Factory Module for A Fugue In Flask

This module implements the Application Factory pattern for Flask, which is a design pattern
that encapsulates the creation and configuration of the Flask application in a function.
This pattern allows for better organization, easier testing, and more flexible configuration.

The factory pattern enables:
1. Creating multiple application instances with different configurations
2. Easier testing by creating test-specific application instances
3. Avoiding circular imports by centralizing extension and blueprint registration
4. Cleaner application structure with separation of concerns

This module also initializes Flask extensions and registers blueprints.
"""
import os
import logging
import urllib.parse
from flask import Flask, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import text  # Import text construct
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize extensions at module level but without binding to an application yet
# This follows the Flask extension pattern for use with the application factory
db = SQLAlchemy()  # Database ORM for SQL operations
migrate = Migrate()  # Database migration management
login_manager = LoginManager()  # User authentication and session management

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
        
        # ODBC connection strings or other formats
        if 'password=' in conn_string.lower() or 'pwd=' in conn_string.lower():
            # Replace password/pwd parameter
            masked = conn_string
            import re
            masked = re.sub(r'(?i)(password|pwd)=([^;]+)', r'\1=******', masked)
            return masked
            
        return "Masked connection string (unknown format)"
    
    except Exception as e:
        logger.warning(f"Error masking connection string: {str(e)}")
        return "Masked connection string (error)"

# Add connection retry decorator based on Azure best practices for transient fault handling
def retry_connection(max_retries=5, initial_delay=2, max_delay=60):
    """
    Decorator that implements retry logic with exponential backoff for database operations
    
    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (int): Initial delay in seconds before first retry
        max_delay (int): Maximum delay between retries in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OperationalError, SQLAlchemyError) as e:
                    last_exception = e
                    # Calculate backoff with jitter (avoid simultaneous reconnection storms)
                    wait_time = min(initial_delay * (2 ** retries) + (time.time() % 1), max_delay)
                    error_msg = str(e).replace('\n', ' ')
                    logger.warning(f"Database connection attempt {retries+1}/{max_retries} failed. "
                                  f"Retrying in {wait_time:.1f}s. Error: {error_msg}")
                    time.sleep(wait_time)
                    retries += 1
            
            # If we get here, all retries failed
            logger.error(f"All database connection attempts failed after {max_retries} retries")
            raise last_exception
        
        return wrapper
    return decorator

# Update: Function to test database connection - extracted from decorator for Flask 2.3+ compatibility
@retry_connection(max_retries=5, initial_delay=2, max_delay=60)
def test_database_connection(app):
    """Test the database connection - compatible with Flask 2.3+ when called from within a request context"""
    try:
        logger.info("Testing database connection before handling first request...")
        with app.app_context():
            # Try a simple query to validate the connection
            engine = db.engine
            with engine.connect() as connection:
                # Wrap the raw SQL string in text()
                result = connection.execute(text("SELECT 1 AS test")) 
                for row in result:
                    logger.info(f"Database connection test successful: {row.test}")
                    return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        logger.error(f"Connection string (masked): {mask_connection_string(app.config.get('SQLALCHEMY_DATABASE_URI', ''))}")
        logger.error(f"Database server: {app.config.get('DB_SERVER', 'Not configured')}")
        logger.error(f"Database name: {app.config.get('DB_NAME', 'Not configured')}")
        raise
    
    return False

def create_app(config_object='config.active_config'):
    """
    Application factory function that creates and configures a Flask application instance.
    
    This function handles:
    1. Creating the Flask app instance
    2. Loading configuration from an object or module
    3. Initializing and configuring extensions with the app
    4. Registering blueprints for modular routing
    5. Setting up Flask CLI shell context for easier debugging
    
    Args:
        config_object (str): Import path to a configuration object to load
                            Defaults to 'config.active_config' which dynamically
                            selects configuration based on environment.
    
    Returns:
        Flask: A configured Flask application instance ready to run
    """
    # Create the Flask application instance
    app = Flask(__name__)
    
    # Special handling for Azure App Service and appsettings.json
    # This needs to be done before loading the config object
    try:
        # Try to load TEMPLATE_DATABASE_URI from appsettings.json if it exists
        # This is critical for Azure App Service deployments
        appsettings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'appsettings.json')
        if os.path.exists(appsettings_path):
            import json
            with open(appsettings_path, 'r') as f:
                appsettings = json.load(f)
                
            if 'TEMPLATE_DATABASE_URI' in appsettings:
                os.environ['TEMPLATE_DATABASE_URI'] = appsettings['TEMPLATE_DATABASE_URI']
                logger.info("Loaded TEMPLATE_DATABASE_URI from appsettings.json")
    except Exception as e:
        logger.warning(f"Error loading appsettings.json: {e}")
    
    # Load configuration from the specified object or module
    app.config.from_object(config_object)
    
    # Check for centralized database configuration
    if app.config.get('USE_CENTRALIZED_DB'):
        logger.info("Initializing with centralized database configuration")
        
        # Check for template override in app settings (Azure App Service)
        if os.environ.get('TEMPLATE_DATABASE_URI'):
            logger.info("Using TEMPLATE_DATABASE_URI from environment")
            template_uri = os.environ.get('TEMPLATE_DATABASE_URI')
            
            # Azure best practice: Ensure all necessary connection parameters are set
            # Fix for connection string params that might be missing
            if 'mssql+pyodbc' in template_uri:
                # Add required parameters for SQL Server connections
                params_to_add = {}
                
                # Check and add Encrypt parameter if missing
                if 'Encrypt=' not in template_uri and '&Encrypt=' not in template_uri:
                    params_to_add['Encrypt'] = 'yes'
                    
                if 'TrustServerCertificate=' not in template_uri and '&TrustServerCertificate=' not in template_uri:
                    params_to_add['TrustServerCertificate'] = 'no'
                    
                # Increase default timeouts for better reliability
                if 'Connection+Timeout=' not in template_uri and '&Connection+Timeout=' not in template_uri:
                    params_to_add['Connection Timeout'] = '90'
                
                if 'Command+Timeout=' not in template_uri and '&Command+Timeout=' not in template_uri:
                    params_to_add['Command Timeout'] = '30'
                
                # Add parameters to URI
                if params_to_add:
                    # Check if we already have parameters
                    if '?' in template_uri:
                        separator = '&'
                    else:
                        separator = '?'
                        
                    # Add each parameter
                    for param, value in params_to_add.items():
                        template_uri += f"{separator}{param}={value}"
                        separator = '&'  # After first param, always use &
                
                logger.info(f"Enhanced connection string with Azure SQL best practices parameters")
            
            app.config['SQLALCHEMY_DATABASE_URI'] = template_uri
            logger.info(f"Set SQLALCHEMY_DATABASE_URI from TEMPLATE_DATABASE_URI")
            
            # Azure best practice: Add SQLAlchemy engine configuration for reliable database connections
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_pre_ping': True,         # Verify connections before using them
                'pool_recycle': 1800,          # Recycle connections after 30 minutes (prevent stale)
                'pool_size': 10,               # Increased connection pool size (default is 5)
                'max_overflow': 20,            # Allow more extra connections (default is 10)
                'pool_timeout': 30,            # Timeout waiting for connection from pool
                'connect_args': {
                    'connect_timeout': 90,     # 90 second connection timeout (up from 60)
                    'retry_timeout': 30,       # Retry for up to 30 seconds (up from 20)
                    'retry_interval': 1,       # Retry every 1 second
                    'ApplicationIntent': 'ReadWrite'  # Ensure connecting to primary replica
                }
            }
        
        # Log database connection info (without credentials)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        masked_uri = mask_connection_string(db_uri)
        logger.info(f"Database URI: {masked_uri}")
        
        logger.info(f"DB_SERVER: {app.config.get('DB_SERVER', 'Not configured')}")
        logger.info(f"DB_NAME: {app.config.get('DB_NAME', 'Not configured')}")
        logger.info(f"USE_CENTRALIZED_DB: {app.config.get('USE_CENTRALIZED_DB')}")
    
    # Silence SQLAlchemy logs in production
    if not app.debug:
        import logging
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Initialize extensions with the application instance
    # This binds previously initialized extensions to this specific app
    db.init_app(app)  # Connect SQLAlchemy to this application
    migrate.init_app(app, db)  # Connect Alembic migrations to this application and database
    
    # Add a health check endpoint for Azure
    @app.route('/health')
    def health_check():
        """Health check endpoint for Azure monitoring"""
        try:
            # Try a quick database connection test
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                db.session.commit()
            return jsonify({"status": "healthy", "database": "connected"}), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy", "error": str(e)}), 500
    
    # Handle Azure's special health probe endpoint
    @app.route('/robots933456.txt')
    def azure_health_probe():
        """Special endpoint for Azure's platform health probes"""
        return "I'm healthy", 200
    
    # Update: Replaced before_first_request with a middleware pattern that's compatible with Flask 2.3+
    # Database connection testing using a middleware pattern
    @app.before_request
    def before_request_middleware():
        """Middleware to run before each request to ensure database connectivity"""
        # Check if we need to test the database connection
        if not hasattr(app, '_database_connection_tested'):
            try:
                # Test database connection the first time
                test_database_connection(app)
                # Mark connection as tested so we don't repeat for every request
                app._database_connection_tested = True
            except Exception as e:
                logger.error(f"Database connection test failed in middleware: {str(e)}")
                # Don't set the flag - will retry on next request
    
    # Configure Flask-Login for authentication
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Specify the route for the login page
    
    # Register blueprints for modular routing
    # Blueprints allow organizing routes into logical groups
    from app.routes.main import main_bp  # Main routes (home, about, etc.)
    from app.routes.auth import auth_bp  # Authentication routes (login, register, etc.)
    
    # Register blueprints with the application
    app.register_blueprint(main_bp)  # Main blueprint at root URL
    app.register_blueprint(auth_bp, url_prefix='/auth')  # Auth blueprint with /auth prefix
    
    # Set up Flask CLI shell context for easier debugging
    # This makes certain objects automatically available in the Flask shell
    @app.shell_context_processor
    def shell_context():
        """Adds key objects to Flask shell context for interactive debugging."""
        return {'app': app, 'db': db}
    
    # Register error handlers
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return "Internal Server Error", 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.error(f"Unhandled exception: {e}")
        return "Internal Server Error", 500
        
    return app