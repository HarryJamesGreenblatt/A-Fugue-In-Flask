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
- Support for multiple template applications with distinct databases
- Integration with Azure Key Vault for secure credential management

The configuration system is designed to follow the 12-Factor App methodology's principles,
particularly for configuration management, which recommends storing config in the environment.
"""
import os
import logging
import urllib.parse
from dotenv import load_dotenv

# Optional Azure Key Vault integration for secure credential management
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_KEY_VAULT_ENABLED = True
except ImportError:
    AZURE_KEY_VAULT_ENABLED = False

# Load environment variables from .env file
# This allows developers to set environment-specific variables without modifying code
load_dotenv()

# Azure Key Vault helper function to get secrets securely
def get_key_vault_secret(secret_name, default_value=None):
    """
    Retrieve a secret from Azure Key Vault using managed identity or fallback to environment variables
    
    Following Azure best practices for secure credential management and managed identities
    """
    if not AZURE_KEY_VAULT_ENABLED:
        return os.environ.get(secret_name, default_value)
    
    key_vault_url = os.environ.get('AZURE_KEY_VAULT_URL')
    if not key_vault_url:
        return os.environ.get(secret_name, default_value)
    
    try:
        # Use DefaultAzureCredential for automatic authentication in various environments
        # This supports Managed Identity, Visual Studio, Azure CLI, etc.
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_url, credential=credential)
        
        # Map environment variable names to Key Vault secret names
        # This allows for different naming conventions between code and Key Vault
        secret_name_mapping = {
            'SECRET_KEY': 'FLASK-SECRET-KEY',
            'DB_USERNAME': 'DbUsername',
            'DB_PASSWORD': 'DbPassword',
            'DB_SERVER': 'DbServer'
        }
        
        # Use the mapped name if it exists, otherwise use the original name
        kv_secret_name = secret_name_mapping.get(secret_name, secret_name)
        
        secret = client.get_secret(kv_secret_name)
        return secret.value
    except Exception as e:
        logging.warning(f"Failed to get secret {secret_name} from Key Vault: {str(e)}")
        # Fallback to environment variables if Key Vault access fails
        return os.environ.get(secret_name, default_value)

def build_mssql_connection_string(username, password, server, database):
    """
    Build a properly formatted connection string for SQL Server using best practices
    """
    # URL encode the password to handle special characters
    encoded_pwd = urllib.parse.quote_plus(password)
    
    # Build a connection string that works reliably with Azure SQL
    # Using the format proven successful in our direct connection test
    conn_str = (
        f"mssql+pyodbc://{username}:{encoded_pwd}@{server}"
        f"/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        f"&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"
    )
    return conn_str

class Config:
    """
    Base configuration class containing settings common to all environments.
    
    All environment-specific configuration classes inherit from this base class,
    allowing for a DRY (Don't Repeat Yourself) approach to configuration.
    """
    # Secret key used for cryptographic functions (session, CSRF protection, etc.)
    # In production, this should be set via environment variable or Azure Key Vault
    SECRET_KEY = get_key_vault_secret('SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production'))
    
    # SQLAlchemy setting to disable modification tracking for better performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask app name for CLI commands
    FLASK_APP = 'app.py'
    
    # Template type - used to determine which template-specific database to connect to
    # Examples: 'flask', 'react', 'blazor', etc.
    TEMPLATE_TYPE = os.environ.get('TEMPLATE_TYPE', 'flask')
    
    # Centralized database configuration for db-rg resource group
    # Following Azure best practices for shared database resources
    DB_SERVER = os.environ.get('DB_SERVER', 'sequitur-sql-server.database.windows.net')
    DB_NAME = os.environ.get('DB_NAME', 'fugue-flask-db')  # Fixed: removed self reference
    DB_NAME_PREFIX = os.environ.get('DB_NAME_PREFIX', '')  # Optional prefix for database names
    USE_CENTRALIZED_DB = os.environ.get('USE_CENTRALIZED_DB', 'True').lower() == 'true'

class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Provides settings optimized for local development, including:
    - Debug mode enabled for detailed error pages
    - SQLite database by default for simplicity
    - Development-specific settings
    """
    FLASK_ENV = 'development'
    DEBUG = True
    
    # Development database URI with SQLite fallback for easy local development
    # For template-specific databases, we append the template type to the database name
    def __init__(self):
        template_suffix = f"-{self.TEMPLATE_TYPE}" if self.TEMPLATE_TYPE != 'flask' else ""
        
        # If using centralized database in Azure, construct connection string with template-specific DB
        if self.USE_CENTRALIZED_DB and os.environ.get('DB_SERVER'):
            db_name = os.environ.get('DB_NAME', f"fugue-flask-db")
            username = get_key_vault_secret('DB_USERNAME', os.environ.get('DB_USERNAME', 'sqladmin'))
            password = get_key_vault_secret('DB_PASSWORD', os.environ.get('DB_PASSWORD', ''))
            
            # Use the centralized connection string builder with improved reliability
            self.SQLALCHEMY_DATABASE_URI = build_mssql_connection_string(
                username=username,
                password=password,
                server=self.DB_SERVER,
                database=db_name
            )
        else:
            # Fallback to local SQLite for development
            self.SQLALCHEMY_DATABASE_URI = os.environ.get(
                'DEV_DATABASE_URI', 
                f'sqlite:///instance/dev{template_suffix}.db'
            )

class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Configures the app for automated testing with:
    - Testing flag enabled for Flask test helpers
    - Separate test database to avoid affecting development/production data
    """
    TESTING = True
    
    # Testing database URI with in-memory SQLite fallback for fast tests
    def __init__(self):
        template_suffix = f"-{self.TEMPLATE_TYPE}" if self.TEMPLATE_TYPE != 'flask' else ""
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            'TEST_DATABASE_URI', 
            f'sqlite:///instance/test{template_suffix}.db'
        )

class ProductionConfig(Config):
    """
    Production environment configuration.
    
    Provides secure, performance-optimized settings for production deployment:
    - Debug mode disabled
    - Support for multiple database types (PostgreSQL, Azure SQL, SQLite)
    - Additional security and performance optimizations
    - Support for template-specific database connections
    - Integration with Azure Key Vault for secure credential management
    """
    FLASK_ENV = 'production'
    DEBUG = False
    
    def __init__(self):
        # First check for a template-specific database URI from Key Vault or environment
        template_specific_env_var = f"{self.TEMPLATE_TYPE.upper()}_DATABASE_URI"
        template_specific_uri = get_key_vault_secret(
            template_specific_env_var, 
            os.environ.get(template_specific_env_var)
        )
        
        # If centralized database architecture is enabled (db-rg with shared SQL server)
        if self.USE_CENTRALIZED_DB and not template_specific_uri:
            # Construct connection string for centralized database architecture
            db_name = os.environ.get('DB_NAME', f"fugue-flask-db")
            username = get_key_vault_secret('DB_USERNAME', os.environ.get('DB_USERNAME', 'sqladmin'))
            password = get_key_vault_secret('DB_PASSWORD', os.environ.get('DB_PASSWORD', ''))
            
            # Use the centralized connection string builder with improved reliability
            self.SQLALCHEMY_DATABASE_URI = build_mssql_connection_string(
                username=username,
                password=password,
                server=self.DB_SERVER,
                database=db_name
            )
        else:
            # Fall back to generic database URI or SQLite database with template-specific name
            template_suffix = f"-{self.TEMPLATE_TYPE}" if self.TEMPLATE_TYPE != 'flask' else ""
            
            self.SQLALCHEMY_DATABASE_URI = template_specific_uri or get_key_vault_secret(
                'DATABASE_URI',
                os.environ.get('DATABASE_URI', f'sqlite:///instance/prod{template_suffix}.db')
            )
    
    # Additional production configs like SSL, logging, etc.
    SESSION_COOKIE_SECURE = True  # Enforces HTTPS-only cookies
    PREFERRED_URL_SCHEME = 'https'  # Enforces HTTPS URL generation
    
    # Connection pooling settings for better database performance (Azure SQL optimization)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_recycle': 3600,  # Recycle connections after 1 hour
    }
    
    # Azure-specific configurations when deployed to Azure
    AZURE_INSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

# Map config environment names to config classes for easy selection
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # Fallback to development if not specified
}

# Determine active configuration from environment variable with fallback to default
active_config = config_by_name[os.environ.get('FLASK_CONFIG', 'default')]()  # Instantiate the config class