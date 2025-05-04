"""
Configuration Module for A Fugue In Flask

This module defines configuration classes for different environments (development, testing, production).
It implements a hierarchical configuration structure where environment-specific configs inherit from
a common base config, which follows Flask's design patterns for configuration management.

Key features:
- Environment variable loading via python-dotenv
- Hierarchical configuration classes
- Dynamic configuration selection based on FLASK_CONFIG environment variable
- Secure management of sensitive configurations (database URIs, secret keys)
- Support for centralized database architecture in Azure

The configuration system is designed to follow the 12-Factor App methodology's principles,
particularly for configuration management, which recommends storing config in the environment.
"""
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    """
    Base configuration class containing settings common to all environments.
    
    All environment-specific configuration classes inherit from this base class,
    allowing for a DRY (Don't Repeat Yourself) approach to configuration.
    """
    # Secret key used for cryptographic functions (session, CSRF protection, etc.)
    SECRET_KEY = None
    
    # SQLAlchemy setting to disable modification tracking for better performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask app name for CLI commands
    FLASK_APP = 'app.py'
    
    # Centralized database flag - determines if we're using centralized db architecture
    USE_CENTRALIZED_DB = os.environ.get('USE_CENTRALIZED_DB', 'False').lower() in ('true', 'yes', '1')
    
    # Database server name (for Azure SQL)
    DB_SERVER = None
    
    # Database name (for Azure SQL)
    DB_NAME = None
    
    # Database retry attempts for connection issues
    DB_CONNECTION_RETRIES = int(os.environ.get('DB_CONNECTION_RETRIES', '5'))
    
    # Database connection timeout (in seconds)
    DB_CONNECTION_TIMEOUT = int(os.environ.get('DB_CONNECTION_TIMEOUT', '60'))

    # Azure Key Vault configuration
    KEY_VAULT_NAME = os.environ.get('KEY_VAULT_NAME')
    KEY_VAULT_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net" if KEY_VAULT_NAME else None

    @staticmethod
    def build_mssql_uri(server, database, username, password):
        """
        Build a properly formatted connection string for Azure SQL Database.
        
        Uses the TCP format with port 1433 specification that has been proven to work reliably.
        Includes essential connection parameters like encrypt=yes and connection timeout.
        """
        # Use the TCP format with port specification that works reliably
        connection_string = (
            f"mssql+pyodbc://{username}:{password}@" + 
            f"tcp:{server},1433/{database}" +
            "?driver=ODBC+Driver+17+for+SQL+Server" +
            "&Encrypt=yes&TrustServerCertificate=yes" +
            "&Connection+Timeout=90&ConnectRetryCount=3&ConnectRetryInterval=10" +
            "&ApplicationIntent=ReadWrite"
        )
        logger.info(f"Built Azure SQL connection string from environment variables")
        logger.info(f"Added connection reliability parameters to database URI")
        return connection_string

    @staticmethod
    def get_secret(secret_name):
        """
        Retrieve a secret from Azure Key Vault.
        """
        if not Config.KEY_VAULT_URI:
            raise ValueError("KEY_VAULT_URI is not set. Cannot retrieve secrets from Key Vault.")
        
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=Config.KEY_VAULT_URI, credential=credential)
        return client.get_secret(secret_name).value

class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Provides settings optimized for local development, including:
    - Debug mode enabled for detailed error pages
    - SQLite database by default for simplicity unless USE_CENTRALIZED_DB=True
    - Development-specific settings
    """
    FLASK_ENV = 'development'
    DEBUG = True
    
    # Define instance path for SQLite fallback
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Connection string priority for Development:
    # 1. TEMPLATE_DATABASE_URI if centralized DB is enabled (consistent with Azure)
    # 2. DATABASE_URI - General purpose database URI
    # 3. Constructed from DB_* variables if centralized DB is enabled
    # 4. DEV_DATABASE_URI for specific development database
    # 5. SQLite fallback as absolute last resort
    
    if Config.USE_CENTRALIZED_DB and os.environ.get('TEMPLATE_DATABASE_URI'):
        logger.info("Development using TEMPLATE_DATABASE_URI from environment with centralized DB")
        SQLALCHEMY_DATABASE_URI = os.environ.get('TEMPLATE_DATABASE_URI')
    elif os.environ.get('DATABASE_URI'):
        logger.info("Development using DATABASE_URI from environment")
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    elif Config.USE_CENTRALIZED_DB and all([os.environ.get(var) for var in ['DB_SERVER', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']]):
        # Build SQL connection string from components
        SQLALCHEMY_DATABASE_URI = Config.build_mssql_uri(
            server=os.environ.get('DB_SERVER'),
            database=os.environ.get('DB_NAME'),
            username=os.environ.get('DB_USERNAME'),
            password=os.environ.get('DB_PASSWORD')
        )
        logger.info(f"Development using constructed connection for {os.environ.get('DB_SERVER')}/{os.environ.get('DB_NAME')}")
    elif os.environ.get('DEV_DATABASE_URI'):
        logger.info("Development using DEV_DATABASE_URI from environment")
        SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')
    else:
        # Last resort SQLite fallback
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_path, "dev.db")}'
        logger.info("Development using local SQLite database file")
    
    # SQLAlchemy engine options with sensible defaults for development
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,  # Recycle connections after 5 minutes in development
        'pool_size': 5,
        'pool_timeout': 30
    }
    
    # Enhanced options if using Azure SQL
    if 'mssql+pyodbc' in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 600,  # Recycle connections after 10 minutes in development
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'connect_args': {
                'connect_timeout': 30,  # Lower timeout for development
                'driver': '{ODBC Driver 17 for SQL Server}'
            }
        }

    # Retrieve secrets from Azure Key Vault
    if Config.KEY_VAULT_URI:
        try:
            SECRET_KEY = Config.get_secret('FLASK-SECRET-KEY')
            DB_USERNAME = Config.get_secret('DB-USERNAME')
            DB_PASSWORD = Config.get_secret('DB-PASSWORD')
        except Exception as e:
            logger.error(f"Error retrieving secrets from Key Vault: {e}")

class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Configures the app for automated testing with:
    - Testing flag enabled for Flask test helpers
    - Separate test database to avoid affecting development/production data
    """
    TESTING = True
    
    # Testing database URI with in-memory SQLite fallback for fast tests
    # Ensure the instance folder exists for SQLite
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI', f'sqlite:///{os.path.join(instance_path, "test.db")}')
    
    # Retrieve secrets from Azure Key Vault
    if Config.KEY_VAULT_URI:
        try:
            SECRET_KEY = Config.get_secret('FLASK-SECRET-KEY')
            DB_USERNAME = Config.get_secret('DB-USERNAME')
            DB_PASSWORD = Config.get_secret('DB-PASSWORD')
        except Exception as e:
            logger.error(f"Error retrieving secrets from Key Vault: {e}")

class ProductionConfig(Config):
    """
    Production environment configuration.
    
    Provides secure, performance-optimized settings for production deployment:
    - Debug mode disabled
    - Support for multiple database types (PostgreSQL, Azure SQL, SQLite)
    - Additional security and performance optimizations
    """
    FLASK_ENV = 'production'
    DEBUG = False
    
    # Define instance path for SQLite fallback
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Connection string priority for Production:
    # 1. TEMPLATE_DATABASE_URI - Used in Azure and centralized DB architecture
    # 2. DATABASE_URI - General purpose database URI
    # 3. Constructed from DB_* variables if centralized DB is enabled
    # 4. SQLite fallback as absolute last resort
    
    if os.environ.get('TEMPLATE_DATABASE_URI'):
        logger.info("Production using TEMPLATE_DATABASE_URI from environment")
        SQLALCHEMY_DATABASE_URI = os.environ.get('TEMPLATE_DATABASE_URI')
    elif os.environ.get('DATABASE_URI'):
        logger.info("Production using DATABASE_URI from environment")
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    elif Config.USE_CENTRALIZED_DB and all([os.environ.get(var) for var in ['DB_SERVER', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']]):
        # Build SQL connection string from components
        SQLALCHEMY_DATABASE_URI = Config.build_mssql_uri(
            server=os.environ.get('DB_SERVER'),
            database=os.environ.get('DB_NAME'),
            username=os.environ.get('DB_USERNAME'),
            password=os.environ.get('DB_PASSWORD')
        )
        logger.info(f"Production using constructed connection for {os.environ.get('DB_SERVER')}/{os.environ.get('DB_NAME')}")
    else:
        # Last resort SQLite fallback
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_path, "prod.db")}'
        logger.warning("Production falling back to SQLite - NOT RECOMMENDED FOR PRODUCTION!")
    
    # Additional production configs like SSL, logging, etc.
    SESSION_COOKIE_SECURE = True  # Enforces HTTPS-only cookies
    PREFERRED_URL_SCHEME = 'https'  # Enforces HTTPS URL generation
    
    # Azure-specific configurations when deployed to Azure
    AZURE_INSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
    
    # Enhanced SQLAlchemy engine options for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,         # Verify connections before using them
        'pool_recycle': 1800,          # Recycle connections after 30 minutes
        'pool_size': 10,               # Increased connection pool size
        'max_overflow': 20,            # Allow more connections than pool_size
        'pool_timeout': 30             # Time to wait for a connection from pool
    }
    
    # If using centralized database architecture, log that we're in that mode
    if Config.USE_CENTRALIZED_DB:
        logger.info("Production config initialized with centralized database architecture")
        if Config.DB_SERVER and Config.DB_NAME:
            logger.info(f"Using database server: {Config.DB_SERVER}, database: {Config.DB_NAME}")
            
    # Add Azure SQL specific options if using SQL Server
    if 'mssql+pyodbc' in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
            'connect_timeout': 90,      # Increase connection timeout for reliability 
            'driver': '{ODBC Driver 17 for SQL Server}',  # Explicitly specify driver
            'ApplicationIntent': 'ReadWrite'  # Ensure we're connecting to primary replica
        }

    # Retrieve secrets from Azure Key Vault
    if Config.KEY_VAULT_URI:
        try:
            SECRET_KEY = Config.get_secret('FLASK-SECRET-KEY')
            DB_USERNAME = Config.get_secret('DB-USERNAME')
            DB_PASSWORD = Config.get_secret('DB-PASSWORD')
        except Exception as e:
            logger.error(f"Error retrieving secrets from Key Vault: {e}")

class AzureConfig(ProductionConfig):
    """
    Azure-specific production configuration.
    
    Extends the production configuration with Azure-specific settings:
    - Specialized database connection handling for Azure SQL
    - Integration with Azure monitoring services
    - Support for Azure App Service environment variables
    """
    # Enable centralized DB architecture by default for Azure
    USE_CENTRALIZED_DB = True
    
    # Set Azure-specific database server variables if they exist
    DB_SERVER = os.environ.get('DB_SERVER')
    DB_NAME = os.environ.get('DB_NAME')
    DB_USERNAME = os.environ.get('DB_USERNAME')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    
    # Build connection string from components if environment variables are set 
    # but TEMPLATE_DATABASE_URI is not set
    if DB_SERVER and DB_NAME and DB_USERNAME and DB_PASSWORD and not os.environ.get('TEMPLATE_DATABASE_URI'):
        # Use the build_mssql_uri helper from the base Config class
        SQLALCHEMY_DATABASE_URI = Config.build_mssql_uri(
            server=DB_SERVER, 
            database=DB_NAME, 
            username=DB_USERNAME, 
            password=DB_PASSWORD
        )
        logger.info(f"Built Azure SQL connection string from environment variables")
    
    # Enhanced SQLAlchemy engine options specifically for Azure SQL in centralized architecture
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,         # Verify connections before using them
        'pool_recycle': 1800,          # Recycle connections after 30 minutes (prevent stale)
        'pool_size': 10,               # Increased connection pool size
        'max_overflow': 20,            # Allow more extra connections
        'pool_timeout': 30,            # Timeout waiting for connection from pool
        'connect_args': {
            'connect_timeout': 90,      # Increase connection timeout for reliability
            'application_intent': 'ReadWrite',  # Ensure we're connecting to primary replica
            'driver': '{ODBC Driver 17 for SQL Server}'  # Explicitly specify driver
        }
    }
    
    # Log Azure configuration details
    logger.info("Azure config initialized with centralized database architecture")

    # Retrieve secrets from Azure Key Vault
    if Config.KEY_VAULT_URI:
        try:
            SECRET_KEY = Config.get_secret('FLASK-SECRET-KEY')
            DB_USERNAME = Config.get_secret('DB-USERNAME')
            DB_PASSWORD = Config.get_secret('DB-PASSWORD')
        except Exception as e:
            logger.error(f"Error retrieving secrets from Key Vault: {e}")

# Map config environment names to config classes for easy selection
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'azure': AzureConfig,
    'default': DevelopmentConfig  # Fallback to development if not specified
}

# Check if we're running on Azure App Service
running_on_azure = os.environ.get('WEBSITE_SITE_NAME') is not None

# Determine active configuration from environment variable with special handling for Azure
if running_on_azure:
    logger.info("Detected Azure App Service environment, using AzureConfig")
    active_config_class = AzureConfig
else:
    # Use environment variable with fallback to default
    active_config_name = os.environ.get('FLASK_CONFIG', 'default')
    active_config_class = config_by_name[active_config_name]
    logger.info(f"Using configuration: {active_config_name}")

# Instantiate the config class
active_config = active_config_class()
