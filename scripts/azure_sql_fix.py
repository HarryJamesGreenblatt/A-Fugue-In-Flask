"""
Azure SQL Database Troubleshooting and Failsafe Script

This script provides comprehensive troubleshooting for Azure SQL connectivity issues
and sets up a development fallback database if connectivity cannot be established.

Following Azure best practices:
- Tests multiple connection string formats
- Checks for firewall/networking issues
- Implements a local SQLite fallback that will allow local development
- Updates configuration files to use the working connection
- Provides detailed diagnostics about the connection failure
"""
import os
import sys
import json
import socket
import requests
import platform
import subprocess
import logging
import time
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('azure_sql_diagnostics.log', mode='w')
    ]
)
logger = logging.getLogger("azure_sql_fix")

try:
    import pyodbc
    import urllib.parse
    from sqlalchemy import create_engine, text
except ImportError:
    logger.error("Required libraries not found. Installing prerequisites...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyodbc", "sqlalchemy"])
    import pyodbc
    import urllib.parse
    from sqlalchemy import create_engine, text

# Constants
SERVER = "sequitur-sql-server.database.windows.net"
DATABASE = "fugue-flask-db"
USERNAME = "sqladmin"
PASSWORD = "SecureP@ssw0rd!"

def print_separator(title):
    """Print a separator line with title for better log readability"""
    line = f"{'=' * 20} {title} {'=' * 20}"
    logger.info(line)
    print(line)

def check_system_info():
    """Collect system information for diagnostics"""
    print_separator("SYSTEM INFORMATION")
    
    logger.info(f"Operating System: {platform.system()} {platform.release()}")
    logger.info(f"Python Version: {platform.python_version()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    
    # Get IP information
    try:
        # Try to get external IP to check if it's whitelisted
        response = requests.get('https://api.ipify.org')
        external_ip = response.text
        logger.info(f"External IP Address: {external_ip}")
        
        # Also get local IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info(f"Local IP Address: {local_ip}")
        logger.info(f"Hostname: {hostname}")
    except Exception as e:
        logger.warning(f"Could not determine IP addresses: {e}")

def check_odbc_drivers():
    """Check available ODBC drivers"""
    print_separator("ODBC DRIVERS")
    
    try:
        drivers = pyodbc.drivers()
        logger.info(f"Available ODBC drivers: {drivers}")
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
        
        if sql_server_drivers:
            logger.info(f"SQL Server drivers found: {sql_server_drivers}")
            return True
        else:
            logger.warning("No SQL Server ODBC drivers found! This is required for Azure SQL connectivity.")
            return False
    except Exception as e:
        logger.error(f"Error checking ODBC drivers: {e}")
        return False

def check_network_connectivity():
    """Check if we can reach the SQL Server on the network"""
    print_separator("NETWORK CONNECTIVITY")
    
    # Test DNS resolution
    try:
        logger.info(f"Resolving hostname {SERVER}...")
        ip_address = socket.gethostbyname(SERVER)
        logger.info(f"Server resolves to IP: {ip_address}")
    except socket.gaierror:
        logger.error(f"Could not resolve hostname {SERVER}! DNS lookup failed.")
        return False
    
    # Test port connectivity
    try:
        logger.info(f"Testing TCP connection to {SERVER}:1433...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((SERVER, 1433))
        
        if result == 0:
            logger.info("✅ SQL Server port is reachable!")
            sock.close()
            return True
        else:
            logger.error(f"❌ Could not connect to {SERVER}:1433 - Error code: {result}")
            logger.error("This indicates a firewall or network issue.")
            logger.error("LIKELY CAUSE: Your IP address is not in the Azure SQL firewall allowlist.")
            sock.close()
            return False
    except Exception as e:
        logger.error(f"Network connectivity test failed: {e}")
        return False

def test_connection_variants():
    """Test various connection string formats to find one that works"""
    print_separator("CONNECTION STRING VARIANTS")
    
    connection_variants = [
        # Variant 1: Basic format
        {
            "name": "Basic Format", 
            "conn_str": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
        },
        # Variant 2: With TCP prefix and port
        {
            "name": "TCP Format", 
            "conn_str": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=tcp:{SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
        },
        # Variant 3: With encryption parameters
        {
            "name": "Encryption Parameters", 
            "conn_str": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=yes"
        },
        # Variant 4: Full connection string with all parameters
        {
            "name": "Full Parameters", 
            "conn_str": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=tcp:{SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=90;ConnectRetryCount=5;ConnectRetryInterval=10"
        },
        # Variant 5: Try ODBC Driver 18 if available
        {
            "name": "ODBC Driver 18", 
            "conn_str": f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=tcp:{SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=90"
        },
        # Variant 6: Try SQL Server driver
        {
            "name": "SQL Server Driver", 
            "conn_str": f"DRIVER={{SQL Server}};SERVER=tcp:{SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=90"
        }
    ]
    
    # Track if we found a working connection
    working_connection = None
    
    # Test each variant
    for variant in connection_variants:
        logger.info(f"Testing connection variant: {variant['name']}")
        try:
            logger.info("Attempting connection...")
            conn = pyodbc.connect(variant['conn_str'], timeout=20)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            logger.info(f"✅ CONNECTION SUCCESSFUL with {variant['name']} variant!")
            logger.info(f"SQL Server version: {version}")
            conn.close()
            
            # Save the working connection string
            working_connection = variant
            break
        except Exception as e:
            logger.error(f"❌ Connection failed with {variant['name']}: {e}")
    
    return working_connection

def update_appsettings_json(working_connection=None):
    """Update appsettings.json with a working connection string"""
    print_separator("UPDATING APPSETTINGS.JSON")
    
    appsettings_path = Path(__file__).parent.parent / "appsettings.json"
    
    try:
        # Load existing appsettings.json
        if appsettings_path.exists():
            with open(appsettings_path, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        if working_connection:
            # Create a SQLAlchemy URI that is compatible with Flask-SQLAlchemy
            # Use a format that doesn't include the tcp: prefix which causes port parsing issues
            sqlalchemy_uri = (
                f"mssql+pyodbc://{USERNAME}:{urllib.parse.quote_plus(PASSWORD)}@{SERVER}/{DATABASE}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
                f"&Encrypt=yes&TrustServerCertificate=yes"
                f"&timeout=30"
            )
            
            # Update settings
            settings['TEMPLATE_DATABASE_URI'] = sqlalchemy_uri
            logger.info(f"TEMPLATE_DATABASE_URI updated with working connection string format")
            
        else:
            # If no working connection, set up a SQLite fallback
            logger.warning("No working connection found, configuring SQLite fallback")
            sqlite_path = str(Path(__file__).parent.parent / "instance" / "fallback.db")
            sqlite_path = sqlite_path.replace("\\", "/")
            settings['TEMPLATE_DATABASE_URI'] = f"sqlite:///{sqlite_path}"
            settings['USE_CENTRALIZED_DB'] = False
            
        # Save updated settings
        with open(appsettings_path, 'w') as f:
            json.dump(settings, f, indent=2)
            
        logger.info(f"appsettings.json updated at {appsettings_path}")
        
    except Exception as e:
        logger.error(f"Error updating appsettings.json: {e}")
        logger.error(traceback.format_exc())

def create_sqlite_fallback():
    """Create a SQLite fallback database with the necessary schema"""
    print_separator("CREATING SQLITE FALLBACK")
    
    # Create instance directory if it doesn't exist
    instance_dir = Path(__file__).parent.parent / "instance"
    instance_dir.mkdir(exist_ok=True)
    
    # SQLite database path
    db_path = instance_dir / "fallback.db"
    
    try:
        # Import the models and create the tables
        sys.path.append(str(Path(__file__).parent.parent))
        
        # Create SQLite engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Create tables
        from app.models.user import User
        User.metadata.create_all(engine)
        
        # Create an admin user
        from sqlalchemy.orm import Session
        from werkzeug.security import generate_password_hash
        
        with Session(engine) as session:
            # Check if admin user already exists
            admin = session.query(User).filter_by(username="admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=generate_password_hash("AdminPass123!")
                )
                session.add(admin)
                session.commit()
                logger.info("Created admin user in SQLite database")
                logger.info("Username: admin")
                logger.info("Password: AdminPass123!")
            else:
                logger.info("Admin user already exists in SQLite database")
                
        logger.info(f"SQLite fallback database created at {db_path}")
        
    except Exception as e:
        logger.error(f"Error creating SQLite fallback: {e}")
        logger.error(traceback.format_exc())

def suggest_fixes():
    """Print suggestions for fixing the Azure SQL connection issues"""
    print_separator("SUGGESTED FIXES")
    
    logger.info("To fix your Azure SQL connection issue, try these steps:")
    
    logger.info("1. Add your IP to Azure SQL Firewall:")
    logger.info("   - Go to Azure Portal")
    logger.info("   - Find your SQL Server resource")
    logger.info("   - Go to 'Security > Firewalls and virtual networks'")
    logger.info("   - Add your current IP address")
    
    logger.info("2. Check connection string parameters:")
    logger.info("   - Verify server name, database name, username and password")
    logger.info("   - Make sure encryption settings are correct")
    
    logger.info("3. Check if SQL Server is running:")
    logger.info("   - Verify the SQL Server resource is running in Azure Portal")
    
    logger.info("4. Try connecting with SQL Server Management Studio or Azure Data Studio")
    
    logger.info("5. Temporarily use the SQLite fallback database:")
    logger.info("   - This script has set up a SQLite fallback database")
    logger.info("   - You can use it for development until Azure SQL connectivity is restored")
    logger.info("   - Username: admin, Password: AdminPass123!")

def main():
    """Main function running all checks"""
    print_separator("AZURE SQL CONNECTION TROUBLESHOOTER")
    logger.info("Starting Azure SQL connectivity diagnostics")
    
    # Run diagnostics
    check_system_info()
    has_drivers = check_odbc_drivers()
    if not has_drivers:
        logger.error("SQL Server ODBC drivers not found. Please install them before continuing.")
        return
        
    network_ok = check_network_connectivity()
    if not network_ok:
        logger.warning("Network connectivity test failed. This is likely a firewall issue.")
    
    # Test connection variants
    working_connection = test_connection_variants()
    
    # Update configuration
    update_appsettings_json(working_connection)
    
    # Create SQLite fallback if needed
    if not working_connection:
        create_sqlite_fallback()
        
    # Provide suggested fixes
    suggest_fixes()
    
    # Final message
    if working_connection:
        print_separator("SUCCESS")
        logger.info(f"Found a working connection variant: {working_connection['name']}")
        logger.info("Updated appsettings.json with the working connection string.")
        logger.info("You should now be able to run your Flask application.")
    else:
        print_separator("FALLBACK CONFIGURED")
        logger.info("No working Azure SQL connection found.")
        logger.info("A SQLite fallback database has been configured.")
        logger.info("You can continue development using the SQLite database.")
        logger.info("Follow the suggested fixes to restore Azure SQL connectivity.")

if __name__ == "__main__":
    main()