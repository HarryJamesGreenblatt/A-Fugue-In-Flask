#!/usr/bin/env python
"""
Database Initialization Script for A Fugue In Flask

This script initializes the SQLite database for development and creates
the first migration. Run this script once to set up your local development
environment after cloning the repository.
"""
import os
import sys
from flask_migrate import init, migrate, upgrade, Migrate
from app import create_app, db
from app.models.user import User

def initialize_database():
    """Initialize the database and perform the first migration."""
    print("Creating Flask application instance...")
    app = create_app()
    
    with app.app_context():
        migrate_instance = Migrate(app, db)
        
        # Check if migrations directory exists
        if not os.path.exists("migrations"):
            print("Initializing migrations directory...")
            init(directory="migrations")
            
            print("Creating initial migration...")
            migrate(directory="migrations", message="Initial migration")
            
            print("Applying migration to the database...")
            upgrade(directory="migrations")
        else:
            print("Migrations directory already exists. Applying migrations...")
            upgrade(directory="migrations")
        
        # Create a default admin user if it doesn't exist
        if not User.query.filter_by(username="admin").first():
            print("Creating default admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash="pbkdf2:sha256:150000$q8LAcDU7$a0c0292054ae6fd1a9086d306651c0eae5200123d42d00069c38c95abba13054"  # 'password'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created successfully.")
        
        print("Database initialization completed successfully!")
        print("\nYou can now run the application with:")
        print("  flask run")
        print("\nDefault admin credentials:")
        print("  Username: admin")
        print("  Password: password")

if __name__ == "__main__":
    initialize_database()