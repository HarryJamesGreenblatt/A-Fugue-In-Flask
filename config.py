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

The configuration system is designed to follow the 12-Factor App methodology's principles,
particularly for configuration management, which recommends storing config in the environment.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows developers to set environment-specific variables without modifying code
load_dotenv()

class Config:
    """
    Base configuration class containing settings common to all environments.
    
    All environment-specific configuration classes inherit from this base class,
    allowing for a DRY (Don't Repeat Yourself) approach to configuration.
    """
    # Secret key used for cryptographic functions (session, CSRF protection, etc.)
    # In production, this should be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # SQLAlchemy setting to disable modification tracking for better performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask app name for CLI commands
    FLASK_APP = 'app.py'

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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI', 'sqlite:///dev.db')

class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Configures the app for automated testing with:
    - Testing flag enabled for Flask test helpers
    - Separate test database to avoid affecting development/production data
    """
    TESTING = True
    
    # Testing database URI with in-memory SQLite fallback for fast tests
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI', 'sqlite:///test.db')

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
    
    # Production database URI with fallback for different providers
    # This URI should be set as an environment variable with a descriptive name
    # that doesn't tie it to any specific template project, allowing reuse across templates
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEMPLATE_DATABASE_URI', os.environ.get('DATABASE_URI', 'sqlite:///prod.db'))
    
    # Additional production configs like SSL, logging, etc. can be added here
    SESSION_COOKIE_SECURE = True  # Enforces HTTPS-only cookies
    PREFERRED_URL_SCHEME = 'https'  # Enforces HTTPS URL generation
    
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
active_config = config_by_name[os.environ.get('FLASK_CONFIG', 'default')]