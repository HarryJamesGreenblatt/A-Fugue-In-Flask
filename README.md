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

6. Set up Azure Key Vault and Managed Identity
   - Create a Key Vault
     ```bash
     az keyvault create --name flask-fugue-kv --resource-group flaskapp-rg --location westus
     ```

   - Add secrets to Key Vault
     ```bash
     SECRET_KEY=$(openssl rand -hex 32)
     az keyvault secret set --vault-name flask-fugue-kv --name "FLASK-SECRET-KEY" --value "$SECRET_KEY"
     az keyvault secret set --vault-name flask-fugue-kv --name "DB-USERNAME" --value "sqladmin"
     az keyvault secret set --vault-name flask-fugue-kv --name "DB-PASSWORD" --value "YourStrongPassword123!"
     ```

   - Enable Managed Identity for your Web App
     ```bash
     az webapp identity assign --name flask-fugue-app --resource-group flaskapp-rg
     PRINCIPAL_ID=$(az webapp identity show --name flask-fugue-app --resource-group flaskapp-rg --query principalId -o tsv)
     az keyvault set-policy --name flask-fugue-kv --object-id $PRINCIPAL_ID --secret-permissions get list
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
A-Fugue-In-Flask/
│
├── app.py                          # Application entry point
├── config.py                       # Environment-specific configurations
├── requirements.txt                # Python dependencies
├── startup_azure.sh                # Azure deployment startup script
├── gunicorn.conf.py                # Production WSGI server config
├── appsettings.json                # Database connection settings
│
├── app/                            # Main application package
│   ├── __init__.py                 # Application factory
│   ├── models/                     # Database models
│   │   ├── __init__.py
│   │   └── user.py                 # User authentication model
│   │
│   ├── routes/                     # Blueprint route definitions
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication routes
│   │   └── main.py                 # Main application routes
│   │
│   ├── templates/                  # Jinja2 templates
│   │   ├── base.html               # Base template with layout
│   │   ├── auth/
│   │   │   ├── login.html          # Login form template
│   │   │   └── register.html       # Registration form template
│   │   │
│   │   └── main/
│   │       ├── about.html          # About page template
│   │       └── index.html          # Homepage template
│   │
│   ├── static/                     # Static assets
│   │   ├── css/
│   │   │   └── style.css           # Custom stylesheets
│   │   └── img/
│   │       └── flask-logo.png      # Logo image
│   │
│   ├── forms/                      # WTForms form classes
│   │   ├── __init__.py
│   │   └── auth.py                 # Authentication forms
│   │
│   └── utils/                      # Helper functions
│       └── __init__.py
│
├── docs/                           # Enhanced documentation with Mermaid diagrams
│   ├── architecture.md             # Application architecture with component diagrams
│   ├── authentication.md           # Authentication system with sequence diagrams
│   ├── azure_deployment.md         # Azure deployment with architecture diagrams
│   ├── azure_key_vault.md          # Key Vault integration with flow diagrams
│   ├── azure_sql_database.md       # SQL Database with connection flow diagrams
│   ├── deployment.md               # General deployment instructions
│   ├── github_actions_azure.md     # GitHub Actions CI/CD setup
│   ├── setup.md                    # Setup instructions
│   └── web_architecture.md         # Web architecture diagrams
│
├── infra/                          # Azure Infrastructure as Code
│   ├── main.bicep                  # Main Bicep template
│   └── sql-server.bicep            # SQL Server resource definition
│
├── instance/                       # Instance-specific files
│   └── dev.db                      # SQLite development database
│
├── migrations/                     # Database migrations
│   ├── versions/                   # Migration versions
│   │   ├── 7f23e04989ee_increase_password_hash_column_length_to_.py
│   │   └── 9f4a4f0691fe_initial_migration.py
│   │
│   ├── alembic.ini                 # Alembic configuration
│   ├── env.py                      # Migration environment
│   └── README                      # Migration instructions
│
├── scripts/                        # Utility scripts
│   ├── advanced_connection_test.py # In-depth connection testing
│   ├── azure_sql_fix.py            # Azure SQL connectivity troubleshooter
│   ├── check_db_connection.py      # Database connection checker 
│   ├── create_tables.py            # Table creation helper
│   ├── direct_db_test.py           # Direct database initialization
│   ├── init_db.py                  # Local database initialization
│   ├── run_with_diagnostics.py     # Enhanced logging runner
│   ├── test_appsettings.py         # Configuration testing
│   ├── test_db_connection.py       # Database connectivity testing
│   ├── update_schema.py            # Schema update utility
│   └── view_local_db.py            # SQLite inspection tool
│
├── tests/                          # Test suite
│   └── ...                         # Test modules
│
└── .github/                        # GitHub configuration
    └── workflows/                  # GitHub Actions workflows
        └── azure-deploy.yml        # Azure deployment workflow
```

#### Core Application

- `app.py` - Application entry point
- `config.py` - Environment configuration (development, production, azure)
- `requirements.txt` - Python dependencies
- `startup_azure.sh` - Azure-specific startup script

#### Azure Integration

- `.github/workflows/azure-deploy.yml` - CI/CD pipeline for Azure App Service
- `infra/` - Infrastructure as Code
  - `main.bicep` - Main Azure resource template
  - `sql-server.bicep` - SQL Server resource definition

#### Application Modules

**Core Flask App (`app/`):**
- `__init__.py` - Application factory pattern implementation
- `models/` - SQLAlchemy database models
- `routes/` - Blueprint route definitions
- `forms/` - WTForms form classes
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, JavaScript, and images
- `utils/` - Helper functions

**Database Management:**
- `migrations/` - Alembic/Flask-Migrate database migrations
- `instance/` - SQLite development database location

**Diagnostic Scripts (`scripts/`):**
- Database utilities:
  - `view_local_db.py` - SQLite database inspection tool
  - `check_db_connection.py` - Connection verification
- Azure SQL helpers:
  - `azure_sql_fix.py` - Azure SQL connectivity troubleshooter
  - `advanced_connection_test.py` - Connection testing with detailed diagnostics
- Application runners:
  - `run_with_diagnostics.py` - Enhanced logging for development

**Documentation (`docs/`):**
- `architecture.md` - Application architecture with component diagrams  
- `authentication.md` - Authentication system with sequence diagrams
- `azure_deployment.md` - Azure deployment with architecture diagrams
- `azure_key_vault.md` - Key Vault integration with flow diagrams
- `azure_sql_database.md` - SQL Database with connection flow diagrams

## Documentation

The project includes comprehensive documentation with visualizations using Mermaid diagrams:

### Application Documentation

- [Architecture Overview](./docs/architecture.md) - Detailed application architecture with component diagrams
- [Authentication System](./docs/authentication.md) - Authentication flow with sequence diagrams
- [Web Architecture](./docs/web_architecture.md) - Web application architecture and patterns
- [Setup Guide](./docs/setup.md) - Local development setup instructions

### Azure Integration Documentation

- [Azure Deployment Guide](./docs/azure_deployment.md) - Complete deployment instructions with architecture diagrams
- [Azure Key Vault Integration](./docs/azure_key_vault.md) - Secret management with flow diagrams
- [Azure SQL Database Integration](./docs/azure_sql_database.md) - Database connection flow diagrams
- [GitHub Actions CI/CD](./docs/github_actions_azure.md) - Continuous deployment pipeline

### Database & Utilities

- **Local Database Tools**: Use the SQLite inspection tool for local development:
  ```
  python -m scripts.view_local_db
  ```
  
- **Connection Troubleshooting**: For connectivity issues with Azure SQL:
  ```
  python -m scripts.advanced_connection_test
  ```

- **Environment Configuration**: Review proper configuration settings:
  ```
  python -m scripts.check_db_connection
  ```

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
4. Check environment variables in your Azure Key Vault
5. For schema issues: `python -m scripts.update_schema`

## License

MIT
