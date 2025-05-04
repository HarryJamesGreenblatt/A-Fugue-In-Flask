#!/bin/bash

# Install ODBC driver for SQL Server (critical for Azure SQL connections)
if ! dpkg -s unixodbc-dev &> /dev/null || ! dpkg -s msodbcsql17 &> /dev/null; then
    echo "Installing ODBC drivers for SQL Server..."
    apt-get update
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev
fi

# Install Python dependencies
pip install -r requirements.txt

# Check database type - use TEMPLATE_DATABASE_URI if available, otherwise fall back to DATABASE_URI
DB_URI=${TEMPLATE_DATABASE_URI:-$DATABASE_URI}

# Check database type
if [[ $DB_URI == postgresql://* ]]; then
    echo "PostgreSQL database detected, running migration script..."
    python -m scripts.migrate_postgres
elif [[ $DB_URI == mssql+pyodbc://* ]]; then
    echo "Azure SQL database detected, running migration script..."
    # Azure SQL may need special handling for migrations
    echo "Testing SQL Server connection before migrations..."
    python -c "from app import create_app; app = create_app(); from flask_sqlalchemy import SQLAlchemy; db = SQLAlchemy(app); engine = db.engine; with engine.connect() as conn: result = conn.execute('SELECT 1'); print('Database connection successful!')"
    flask db upgrade
else
    # Apply regular database migrations
    echo "Running standard database migrations..."
    flask db upgrade
fi

# Start Gunicorn server
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 "app:create_app()"