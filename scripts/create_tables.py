"""
Database initialization script for Azure SQL Database

This script directly connects to the Azure SQL database using the connection string
from appsettings.json and creates all tables defined in SQLAlchemy models.
"""
import os
import sys
import json
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import application components
from app import create_app, db
from app.models.user import User

def load_appsettings():
    """Load connection string from appsettings.json"""
    try:
        app_settings_path = Path(__file__).parent.parent / "appsettings.json"
        logger.info(f"Loading appsettings from {app_settings_path}")
        
        with open(app_settings_path, 'r') as f:
            settings = json.load(f)
            
        if "TEMPLATE_DATABASE_URI" in settings:
            conn_string = settings["TEMPLATE_DATABASE_URI"]
            logger.info(f"Found connection string in appsettings.json")
            return conn_string
        else:
            logger.error("No TEMPLATE_DATABASE_URI found in appsettings.json")
            return None
    except Exception as e:
        logger.error(f"Error loading appsettings.json: {e}")
        return None

def initialize_database():
    """Initialize the database schema by creating all tables"""
    try:
        # Load connection string from appsettings.json
        conn_string = load_appsettings()
        if not conn_string:
            logger.error("Failed to load connection string from appsettings.json")
            return False
        
        # Set environment variable for Flask app
        os.environ['FLASK_CONFIG'] = 'azure'
        os.environ['TEMPLATE_DATABASE_URI'] = conn_string
        os.environ['USE_CENTRALIZED_DB'] = 'True'
        
        # Create Flask app with Azure configuration
        logger.info("Creating Flask application with Azure configuration...")
        app = create_app('config.AzureConfig')
        
        # Create database tables within app context
        with app.app_context():
            logger.info("Creating all database tables...")
            db.create_all()
            logger.info("Database tables created successfully")
            
            # List created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {tables}")
            
            # Check if User table was created and create admin user if needed
            if 'users' in tables and User.query.count() == 0:
                logger.info("Creating admin user...")
                admin = User(username="admin", email="admin@example.com")
                admin.set_password("AdminPass123!")  # Important: Change this in production
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created successfully")
                
                # Verify user was created
                user_count = User.query.count()
                logger.info(f"User count: {user_count}")
                
            return True
                
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting database initialization...")
    success = initialize_database()
    
    if success:
        logger.info("✅ Database initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Database initialization failed")
        sys.exit(1)