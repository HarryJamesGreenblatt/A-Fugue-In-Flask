@echo off
:: PostgreSQL initialization script for Windows
echo Setting up PostgreSQL database connection...

:: Check if DATABASE_URI environment variable is set
if "%DATABASE_URI%"=="" (
    echo ERROR: DATABASE_URI environment variable not set
    echo Example: set DATABASE_URI=postgresql://username:password@localhost:5432/flask_app
    exit /b 1
)

:: Run Flask database migrations
echo Running database migrations...
flask db upgrade

echo PostgreSQL database setup completed successfully