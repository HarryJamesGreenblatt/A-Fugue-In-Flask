#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Check database type
if [[ $DATABASE_URI == postgresql://* ]]; then
    echo "PostgreSQL database detected, running migration script..."
    python -m scripts.migrate_postgres
elif [[ $DATABASE_URI == mssql+pyodbc://* ]]; then
    echo "Azure SQL database detected, running migration script..."
    # Azure SQL may need special handling for migrations
    flask db upgrade
else
    # Apply regular database migrations
    echo "Running standard database migrations..."
    flask db upgrade
fi

# Start Gunicorn server
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 "app:create_app()"