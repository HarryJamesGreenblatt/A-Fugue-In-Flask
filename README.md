# A Fugue In Flask

A comprehensive Flask application template with Azure SQL Database integration and Azure deployment capabilities.

## Overview

"A Fugue In Flask" provides a production-ready Flask application template that follows best practices for organization, configuration, and deployment. It serves as a solid foundation for building web applications that can be easily deployed to Azure with Azure SQL Database connectivity.

## Features

- Modular application structure using Flask blueprints
- Environment-specific configuration management
- Azure SQL Database integration with SQLAlchemy and pyodbc
- Authentication system with secure password hashing
- Azure deployment setup with CI/CD
- Testing framework
- Comprehensive documentation

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- Microsoft ODBC Driver for SQL Server

### Installation

1. Clone this repository
   ```
   git clone https://github.com/HarryJamesGreenblatt/A-Fugue-In-Flask.git
   cd A-Fugue-In-Flask
   ```

2. Install the Microsoft ODBC Driver for SQL Server
   - Windows: [Download and install ODBC Driver 17](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
   - macOS: 
     ```
     brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
     brew update
     brew install msodbcsql17
     ```
   - Linux (Ubuntu):
     ```
     sudo su
     curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
     curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
     exit
     sudo apt-get update
     sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17
     ```

3. Create a virtual environment
   ```
   python -m venv venv
   ```

4. Activate the virtual environment
   - Windows: 
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux: 
     ```
     source venv/bin/activate
     ```

5. Install dependencies
   ```
   pip install -r requirements.txt
   ```

6. Set up environment variables by creating a `.env` file (or copy from `.env.template`)
   ```
   # Windows
   copy .env.template .env
   
   # macOS/Linux
   cp .env.template .env
   ```
   
   Edit the `.env` file with your Azure SQL Database credentials:
   ```
   # Database connection information
   DB_SERVER="your-sql-server.database.windows.net"
   DB_NAME="your-database-name"
   DB_USERNAME="your-username"
   DB_PASSWORD="your-password"
   
   # Flask configuration
   FLASK_CONFIG="development"  # Options: development, production, testing, azure
   SECRET_KEY="your-secret-key-for-flask"
   
   # Set to True to use centralized database architecture
   USE_CENTRALIZED_DB="True"
   ```

7. Initialize the database
   - For Azure SQL Database:
     ```
     python -m scripts.direct_db_test
     ```
   - For local SQLite development:
     ```
     python -m scripts.init_db
     ```

8. Run the Azure SQL connection fix script:
   ```
   python -m scripts.azure_sql_fix
   ```

9. Run the application
   ```
   # Set configuration to use Azure SQL
   set FLASK_CONFIG=azure  # Windows
   export FLASK_CONFIG=azure  # macOS/Linux
   
   # Run the application
   flask run
   ```
   
   For enhanced diagnostics:
   ```
   python -m scripts.run_with_diagnostics
   ```

10. Access the application at http://flask-fugue-app.azurewebsites.net/

### Default Login

After initialization, a default admin user is created:
- Username: `admin`
- Password: `password`

**Important**: Change the default password in production.

## Development

### Project Structure

```
app.py                  # Application entry point
config.py               # Configuration settings
appsettings.json        # Database connection settings
app/                    # Application package
  ├── __init__.py       # Application factory
  ├── models/           # Database models
  ├── routes/           # Blueprint routes
  ├── templates/        # Jinja2 templates
  ├── static/           # Static files
  ├── forms/            # Form classes
  └── utils/            # Utility functions
scripts/                # Utility scripts
  ├── azure_sql_fix.py  # Azure SQL connectivity diagnostic and fix
  ├── direct_db_test.py # Direct database initialization
  └── update_schema.py  # Schema update utility
```

### Environment Variables

Key environment variables (defined in `.env`):
- `FLASK_APP`: Main application module (default: app.py)
- `FLASK_CONFIG`: Configuration environment (development, production, testing, azure)
- `SECRET_KEY`: Secret key for session security
- `DB_SERVER`: Azure SQL server address
- `DB_NAME`: Azure SQL database name
- `DB_USERNAME`: Azure SQL username
- `DB_PASSWORD`: Azure SQL password
- `USE_CENTRALIZED_DB`: Set to "True" to use Azure SQL Database

## Documentation

### Architecture Documentation

For detailed documentation about the application architecture and implementation:

- [Architecture Documentation](./docs/architecture.md) - Comprehensive overview of application structure and patterns
- [Web Architecture](./docs/web_architecture.md) - Details about the web application architecture
- [Authentication](./docs/authentication.md) - Authentication system implementation details
- [Setup Guide](./docs/setup.md) - Detailed setup instructions for local development

### Azure Deployment Documentation

We provide extensive documentation for deploying to Azure:

- [Azure Deployment Guide](./docs/azure_deployment.md) - Complete step-by-step instructions for deploying to Azure
- [Azure Key Vault Integration](./docs/azure_key_vault.md) - Guide for securely managing secrets with Azure Key Vault
- [GitHub Actions CI/CD](./docs/github_actions_azure.md) - Setting up continuous deployment with GitHub Actions
- [Azure SQL Database Integration](./docs/azure_sql_database.md) - Connecting your Flask app to Azure SQL Database

## Testing

Run tests with pytest:

```
pytest
```

For coverage reporting:

```
pytest --cov=app tests/
```

## Deployment

This template is configured for continuous deployment to Azure App Service using GitHub Actions. The deployment process includes:

1. Automated testing before deployment
2. Secure secret management with Azure Key Vault
3. Database configuration with Azure SQL Database (Basic tier)
4. CI/CD pipeline with GitHub Actions

See the [Azure Deployment Guide](./docs/azure_deployment.md) for detailed instructions.

## Azure Resources

When deployed, this application uses these Azure resources:

- **Azure App Service**: Hosts the Flask application (Free tier F1 for development)
- **Azure SQL Database**: Database backend (Basic tier, ~$5/month)
- **Azure Key Vault**: Securely stores application secrets and credentials
- **GitHub Actions**: Provides CI/CD pipeline integration

## Troubleshooting

If you encounter issues with Azure SQL connectivity:

1. Run the diagnostic script: `python -m scripts.azure_sql_fix`
2. Check if your IP is in the Azure SQL firewall allowlist
3. Verify the ODBC driver is installed: `python -c "import pyodbc; print(pyodbc.drivers())"`
4. Check environment variables in your `.env` file
5. For schema issues: `python -m scripts.update_schema`

## License

MIT
