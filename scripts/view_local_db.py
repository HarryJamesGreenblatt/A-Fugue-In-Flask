"""
SQLite Database Inspector

This script allows you to inspect the contents of your SQLite database used for local development.
It shows tables, schema, and contents of key tables without requiring sqlite3 on your PATH.
"""
import os
import sys
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def display_header(title):
    """Display a formatted header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def inspect_sqlite_db(db_path):
    """Inspect and display contents of SQLite database"""
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    logger.info(f"Opening database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        display_header("DATABASE TABLES")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database.")
            return True
            
        print("Tables:")
        for idx, table in enumerate(tables, 1):
            print(f"{idx}. {table[0]}")
            
        # For each table, show schema and contents
        for table in tables:
            table_name = table[0]
            display_header(f"TABLE: {table_name}")
            
            # Show schema
            print("\nSchema:")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                cid, name, type_name, notnull, default_val, pk = col
                print(f"  {name} ({type_name}){' PRIMARY KEY' if pk else ''}{' NOT NULL' if notnull else ''}")
                
            # Show content (limit to 20 rows)
            print("\nContent (max 20 rows):")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 20;")
            rows = cursor.fetchall()
            
            if not rows:
                print("  No data in this table.")
                continue
                
            # Print column headers
            header = [col[1] for col in columns]  # Column names
            print("  " + " | ".join(header))
            print("  " + "-"*80)
            
            # Print rows
            for row in rows:
                # Format each value, ensuring strings for display
                formatted_row = []
                for value in row:
                    if value is None:
                        formatted_row.append("NULL")
                    else:
                        # Truncate long strings
                        str_value = str(value)
                        if len(str_value) > 30:
                            str_value = str_value[:27] + "..."
                        formatted_row.append(str_value)
                        
                print("  " + " | ".join(formatted_row))
            
            print(f"\nTotal: {len(rows)} row(s) displayed.")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Path to your SQLite database
    db_path = Path(__file__).parent.parent / "instance" / "dev.db"
    
    print(f"Inspecting SQLite database at: {db_path}")
    success = inspect_sqlite_db(str(db_path))
    
    if success:
        print("\nDatabase inspection complete.")
    else:
        print("\nDatabase inspection failed.")
        sys.exit(1)