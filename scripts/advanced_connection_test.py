"""
Advanced database connection test script

This script tries multiple connection string formats and provides detailed
diagnostics to help identify connectivity issues with Azure SQL Database.
"""
import os
import sys
import json
import time
import socket
import platform
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
import pyodbc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mask_connection_string(conn_string):
    """Mask sensitive information in connection strings for secure logging"""
    if not conn_string:
        return "No connection string provided"
    
    try:
        # Handle mssql+pyodbc format
        if isinstance(conn_string, str) and 'password' in conn_string.lower():
            import re
            return re.sub(r'(?i)(password|pwd)=[^;]+', r'\1=*****', conn_string)
        
        # Handle SQLAlchemy format
        if isinstance(conn_string, str) and '@' in conn_string and ':' in conn_string.split('@')[0]:
            parts = conn_string.split('@')
            auth_parts = parts[0].split(':')
            if len(auth_parts) >= 2:
                return f"{auth_parts[0]}:******@{parts[1]}"
                
        return "Masked connection string"
    except Exception as e:
        logger.warning(f"Error masking connection string: {str(e)}")
        return "Masked connection string (error)"

def system_info():
    """Collect system information for diagnostics"""
    logger.info("=== System Information ===")
    logger.info(f"OS: {platform.system()} {platform.version()}")
    logger.info(f"Python Version: {platform.python_version()}")
    
    try:
        ip = socket.gethostbyname(socket.gethostname())
        logger.info(f"Local IP Address: {ip}")
    except:
        logger.info("Could not determine local IP address")
    
    logger.info("==========================")

def check_host_connectivity(hostname, port=1433):
    """Check if we can reach the host on the given port"""
    logger.info(f"Testing TCP connectivity to {hostname}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        if result == 0:
            logger.info(f"✅ Successfully connected to {hostname}:{port}")
            return True
        else:
            logger.error(f"❌ Could not connect to {hostname}:{port} - Error code: {result}")
            return False
    except socket.gaierror:
        logger.error(f"❌ Could not resolve hostname {hostname}")
        return False
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False
    finally:
        sock.close()

def load_appsettings():
    """Load connection string from appsettings.json"""
    try:
        app_settings_path = Path(__file__).parent.parent / "appsettings.json"
        logger.info(f"Loading appsettings from {app_settings_path}")
        
        with open(app_settings_path, 'r') as f:
            settings = json.load(f)
            
        if "TEMPLATE_DATABASE_URI" in settings:
            conn_string = settings["TEMPLATE_DATABASE_URI"]
            logger.info(f"Found connection string: {mask_connection_string(conn_string)}")
            return conn_string
        else:
            logger.error("No TEMPLATE_DATABASE_URI found in appsettings.json")
            return None
    except Exception as e:
        logger.error(f"Error loading appsettings.json: {e}")
        return None

def parse_connection_string(conn_string):
    """Parse connection string to extract components"""
    logger.info("Parsing connection string components...")
    
    # Handle SQLAlchemy URI format
    if conn_string.startswith('mssql+pyodbc://'):
        try:
            # Extract basic components
            auth_part = conn_string.split('@')[0].replace('mssql+pyodbc://', '')
            server_part = conn_string.split('@')[1].split('?')[0]
            
            # Extract username and password
            username, password = auth_part.split(':')
            
            # Extract server and database
            if '/' in server_part:
                server, database = server_part.split('/')
            else:
                server = server_part
                database = None
                
            # Extract params if they exist
            params = {}
            if '?' in conn_string:
                param_string = conn_string.split('?')[1]
                param_pairs = param_string.split('&')
                for pair in param_pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        params[key] = value
            
            logger.info(f"Server: {server}")
            logger.info(f"Database: {database}")
            logger.info(f"Username: {username}")
            logger.info("Password: [MASKED]")
            logger.info(f"Params: {params}")
            
            return {
                'server': server,
                'database': database,
                'username': username,
                'password': password,
                'params': params
            }
        except Exception as e:
            logger.error(f"Error parsing SQLAlchemy URI: {e}")
            return None
    else:
        logger.error("Unsupported connection string format")
        return None

def try_direct_pyodbc_connection(conn_info):
    """Try a direct connection using pyodbc"""
    logger.info("Attempting direct connection with pyodbc...")
    
    try:
        server = conn_info['server']
        database = conn_info['database']
        username = conn_info['username']
        password = conn_info['password']
        
        # Try different connection formats
        connection_strings = [
            # Format 1: Standard with server name
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=60;",
            
            # Format 2: TCP format with port 1433
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=tcp:{server},1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=60;",
            
            # Format 3: With driver specified in SQLAlchemy format
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=60;Driver={{ODBC Driver 17 for SQL Server}}",
        ]
        
        for i, conn_string in enumerate(connection_strings, 1):
            logger.info(f"Trying connection format {i}...")
            logger.info(f"Connection string: {mask_connection_string(conn_string)}")
            
            try:
                with pyodbc.connect(conn_string, timeout=30) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT @@VERSION")
                    row = cursor.fetchone()
                    logger.info(f"✅ Connection format {i} successful!")
                    logger.info(f"SQL Server version: {row[0]}")
                    return True
            except Exception as e:
                logger.error(f"❌ Connection format {i} failed: {e}")
                continue
                
        logger.error("All connection formats failed")
        return False
        
    except Exception as e:
        logger.error(f"Error in direct pyodbc connection attempt: {e}")
        return False

def try_sqlalchemy_connection(conn_string):
    """Try connection using SQLAlchemy"""
    logger.info("Attempting SQLAlchemy connection...")
    
    # Try original connection string
    logger.info(f"Original connection string: {mask_connection_string(conn_string)}")
    
    try:
        # Add options that might help with connection issues
        if '?' in conn_string:
            enhanced_conn_string = conn_string + "&timeout=60&trusted_connection=no&driver=ODBC+Driver+17+for+SQL+Server"
        else:
            enhanced_conn_string = conn_string + "?timeout=60&trusted_connection=no&driver=ODBC+Driver+17+for+SQL+Server"
            
        logger.info(f"Enhanced connection string: {mask_connection_string(enhanced_conn_string)}")
        
        engine = create_engine(
            enhanced_conn_string,
            connect_args={
                'connect_timeout': 60,
                'timeout': 60
            }
        )
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT @@VERSION AS version"))
            row = result.fetchone()
            logger.info("✅ SQLAlchemy connection successful!")
            logger.info(f"SQL Server version: {row.version}")
            return True
            
    except Exception as e:
        logger.error(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("======== Advanced Azure SQL Database Connection Test ========")
    
    # Show system information
    system_info()
    
    # Load connection string from appsettings.json
    conn_string = load_appsettings()
    if not conn_string:
        logger.error("Could not load connection string from appsettings.json")
        sys.exit(1)
    
    # Parse connection string
    conn_info = parse_connection_string(conn_string)
    if not conn_info:
        logger.error("Could not parse connection string")
        sys.exit(1)
        
    # Check connectivity to host
    server = conn_info['server']
    if '.' not in server:
        logger.warning(f"Server name '{server}' does not look like a FQDN")
        server = f"{server}.database.windows.net"
        logger.info(f"Using fully qualified domain name: {server}")
    
    # Update the connection info with potentially modified server name
    conn_info['server'] = server
    
    # Check basic connectivity
    check_host_connectivity(server)
    
    # Try direct pyodbc connection
    pyodbc_success = try_direct_pyodbc_connection(conn_info)
    
    # Try SQLAlchemy connection
    sqlalchemy_success = try_sqlalchemy_connection(conn_string)
    
    # Overall result
    if pyodbc_success or sqlalchemy_success:
        logger.info("✅ At least one connection method succeeded!")
        sys.exit(0)
    else:
        logger.error("❌ All connection attempts failed")
        logger.info("Common troubleshooting steps:")
        logger.info("1. Verify the SQL Server firewall allows your IP address")
        logger.info("2. Check that the server name is correct")
        logger.info("3. Verify your username and password are correct")
        logger.info("4. Make sure the database exists and is online")
        sys.exit(1)