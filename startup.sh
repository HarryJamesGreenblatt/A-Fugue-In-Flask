#!/bin/bash

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
exec gunicorn --config gunicorn.conf.py "app:create_app()"