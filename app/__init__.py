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
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize extensions at module level but without binding to an application yet
# This follows the Flask extension pattern for use with the application factory
db = SQLAlchemy()  # Database ORM for SQL operations
migrate = Migrate()  # Database migration management
login_manager = LoginManager()  # User authentication and session management

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
                template_uri += '&Connection+Timeout=30'
                
            app.config['SQLALCHEMY_DATABASE_URI'] = template_uri
            
        # Log database connection info (without credentials)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if '@' in db_uri:
            parts = db_uri.split('@')
            masked_uri = f"***:***@{parts[1]}" if len(parts) > 1 else db_uri
            logger.info(f"Database URI: {masked_uri}")
        
        logger.info(f"DB_SERVER: {app.config.get('DB_SERVER')}")
        logger.info(f"DB_NAME: {app.config.get('DB_NAME')}")
        logger.info(f"USE_CENTRALIZED_DB: {app.config.get('USE_CENTRALIZED_DB')}")

    # Initialize extensions with the application instance
    # This binds previously initialized extensions to this specific app
    db.init_app(app)  # Connect SQLAlchemy to this application
    migrate.init_app(app, db)  # Connect Alembic migrations to this application and database
    
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