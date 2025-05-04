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
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy.exc import OperationalError
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
    if not conn_string or '@' not in conn_string:
        return conn_string
    
    parts = conn_string.split('@')
    if len(parts) < 2:
        return conn_string
    
    auth_parts = parts[0].split(':')
    if len(auth_parts) >= 3:  # username:password:
        masked = f"{auth_parts[0]}:******@{parts[1]}"
    elif len(auth_parts) == 2:  # username:password
        masked = f"{auth_parts[0]}:******@{parts[1]}"
    else:
        masked = conn_string
    
    return masked

# Add connection retry decorator based on Azure best practices for transient fault handling
def retry_connection(max_retries=3, delay=1):
    """Decorator that implements retry logic with exponential backoff for database operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_exception = e
                    wait_time = delay * (2 ** retries)  # Exponential backoff
                    logger.warning(f"Database connection attempt {retries+1} failed. Retrying in {wait_time}s. Error: {str(e)}")
                    time.sleep(wait_time)
                    retries += 1
            
            # If we get here, all retries failed
            logger.error(f"All database connection attempts failed after {max_retries} retries")
            raise last_exception
        
        return wrapper
    return decorator

# Update: Function to test database connection - extracted from decorator for Flask 2.3+ compatibility
@retry_connection(max_retries=5, delay=2)
def test_database_connection(app):
    """Test the database connection - compatible with Flask 2.3+ when called from within a request context"""
    try:
        logger.info("Testing database connection before handling first request...")
        with app.app_context():
            # Try a simple query to validate the connection
            engine = db.engine
            with engine.connect() as connection:
                result = connection.execute("SELECT 1 AS test")
                for row in result:
                    logger.info(f"Database connection test successful: {row.test}")
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        logger.error(f"Connection string (masked): {mask_connection_string(app.config.get('SQLALCHEMY_DATABASE_URI', ''))}")
        raise

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
    
    # Load configuration from the specified object or module
    app.config.from_object(config_object)
    
    # Check for centralized database configuration
    if app.config.get('USE_CENTRALIZED_DB'):
        logger.info("Initializing with centralized database configuration")
        
        # Check for template override in app settings (Azure App Service)
        if os.environ.get('TEMPLATE_DATABASE_URI'):
            logger.info("Using TEMPLATE_DATABASE_URI from app settings")
            template_uri = os.environ.get('TEMPLATE_DATABASE_URI')
            
            # Fix for connection string params that might be missing
            if 'Encrypt=' not in template_uri and '&Encrypt=' not in template_uri:
                if '?' in template_uri:
                    template_uri += '&Encrypt=yes'
                else:
                    template_uri += '?Encrypt=yes'
                    
            if 'TrustServerCertificate=' not in template_uri and '&TrustServerCertificate=' not in template_uri:
                template_uri += '&TrustServerCertificate=no'
                
            if 'Connection+Timeout=' not in template_uri and '&Connection+Timeout=' not in template_uri:
                template_uri += '&Connection+Timeout=60'
                
            app.config['SQLALCHEMY_DATABASE_URI'] = template_uri
            
            # Azure best practice: Add SQLAlchemy engine configuration for reliable database connections
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_pre_ping': True,         # Verify connections before using them
                'pool_recycle': 1800,          # Recycle connections after 30 minutes
                'pool_size': 5,                # Default connection pool size
                'max_overflow': 10,            # Allow up to 10 extra connections
                'connect_args': {
                    'connect_timeout': 60,     # 60 second connection timeout
                    'retry_timeout': 20,       # Retry for up to 20 seconds
                    'retry_interval': 1        # Retry every 1 second
                }
            }
            
        # Log database connection info (without credentials)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        masked_uri = mask_connection_string(db_uri)
        logger.info(f"Database URI: {masked_uri}")
        
        logger.info(f"DB_SERVER: {app.config.get('DB_SERVER')}")
        logger.info(f"DB_NAME: {app.config.get('DB_NAME')}")
        logger.info(f"USE_CENTRALIZED_DB: {app.config.get('USE_CENTRALIZED_DB')}")

    # Initialize extensions with the application instance
    # This binds previously initialized extensions to this specific app
    db.init_app(app)  # Connect SQLAlchemy to this application
    migrate.init_app(app, db)  # Connect Alembic migrations to this application and database
    
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