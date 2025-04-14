"""
PostgreSQL Database Migration Script for Azure

This script handles database initialization and migration for PostgreSQL 
when deployed to Azure. It ensures the database schema is up-to-date
by running the appropriate Flask-Migrate commands.

Usage:
    python -m scripts.migrate_postgres
"""
import os
import subprocess
import sys
import time
from urllib.parse import urlparse

def wait_for_postgres(db_url, max_retries=10, retry_interval=2):
    """
    Wait for PostgreSQL to be available.
    
    Args:
        db_url: Database connection URL
        max_retries: Maximum number of connection attempts
        retry_interval: Time between retries in seconds
    
    Returns:
        True if connection successful, False otherwise
    """
    print(f"Checking PostgreSQL connection at {db_url}...")
    
    # Parse the connection URL to get host, port
    parsed = urlparse(db_url)
    host = parsed.hostname
    port = parsed.port or 5432
    
    # Try to connect to PostgreSQL
    import psycopg2
    
    retries = 0
    while retries < max_retries:
        try:
            # Just try to connect, no need to do anything else
            conn = psycopg2.connect(db_url)
            conn.close()
            print("Successfully connected to PostgreSQL.")
            return True
        except psycopg2.OperationalError as e:
            retries += 1
            print(f"Connection attempt {retries}/{max_retries} failed: {e}")
            if retries < max_retries:
                print(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print("Max retries reached. Could not connect to PostgreSQL.")
                return False

def run_migrations():
    """
    Run database migrations to update the schema.
    """
    try:
        print("Running database migrations...")
        # Use subprocess to run Flask-Migrate commands
        subprocess.run([sys.executable, "-m", "flask", "db", "upgrade"], check=True)
        print("Migrations completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        return False

def main():
    """
    Main function to run migrations on PostgreSQL.
    """
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URI')
    
    if not db_url:
        print("ERROR: DATABASE_URI environment variable not set.")
        sys.exit(1)
    
    if not db_url.startswith('postgresql://'):
        print(f"WARNING: Not a PostgreSQL database URL: {db_url}")
        print("Continuing anyway, but this script is designed for PostgreSQL.")
    
    # Wait for PostgreSQL to be available
    if not wait_for_postgres(db_url):
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    print("Database setup completed successfully.")

if __name__ == "__main__":
    main()