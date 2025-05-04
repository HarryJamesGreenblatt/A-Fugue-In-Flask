"""
Direct database initialization script for Azure SQL Database

This script uses a direct PyODBC connection to create tables in the Azure SQL database.
It bypasses SQLAlchemy and Flask to ensure reliable connection.
"""
import sys
import json
from pathlib import Path
import logging
import pyodbc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tables_direct():
    """Initialize the database schema using direct SQL commands"""
    try:
        # Hardcoded connection parameters - safer than parsing
        server = "sequitur-sql-server.database.windows.net"
        database = "fugue-flask-db"
        username = "sqladmin"
        password = "SecureP@ssw0rd!"
        
        logger.info(f"Using connection parameters - Server: {server}, Database: {database}, Username: {username}")
        
        # Create a direct connection string in the format that worked in our test
        direct_conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=tcp:{server},1433;"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=90;"
        )
        
        logger.info(f"Connecting to SQL Server {server}...")
        conn = pyodbc.connect(direct_conn_string, timeout=60)
        cursor = conn.cursor()
        
        logger.info("Connection established successfully!")
        
        # Create users table if it doesn't exist
        logger.info("Creating users table...")
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
        BEGIN
            CREATE TABLE users (
                id INT PRIMARY KEY IDENTITY(1,1),
                username NVARCHAR(64) NOT NULL UNIQUE,
                email NVARCHAR(120) NOT NULL UNIQUE,
                password_hash NVARCHAR(256),
                created_at DATETIME DEFAULT GETDATE(),
                last_login DATETIME
            )
            PRINT 'Users table created successfully'
        END
        ELSE
        BEGIN
            PRINT 'Users table already exists'
        END
        """)
        conn.commit()
        
        # Check if the table was created
        cursor.execute("SELECT COUNT(*) FROM sys.tables WHERE name = 'users'")
        if cursor.fetchone()[0] == 1:
            logger.info("Users table exists")
        else:
            logger.error("Failed to create users table")
            return False
        
        # Check if admin user exists, create if it doesn't
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # We don't have the password hashing function from Flask-Login here,
            # so we'll use a placeholder hash that admin can reset later
            logger.info("Creating admin user...")
            cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES ('admin', 'admin@example.com', 'reset_on_first_login')
            """)
            conn.commit()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
        
        conn.close()
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting direct database initialization...")
    success = create_tables_direct()
    
    if success:
        logger.info("✅ Database tables created successfully")
        sys.exit(0)
    else:
        logger.error("❌ Database initialization failed")
        sys.exit(1)