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
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

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
        
    return app