#!/bin/bash

# Check if we're using PostgreSQL
if [[ $DATABASE_URI == postgresql://* ]]; then
    echo "PostgreSQL database detected, running migration script..."
    python -m scripts.migrate_postgres
else
    # Apply regular database migrations
    echo "Running standard database migrations..."
    flask db upgrade
fi

# Start Gunicorn server
exec gunicorn --config gunicorn.conf.py "app:create_app()"