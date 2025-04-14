# A Fugue In Flask

A comprehensive Flask application template with Azure deployment capabilities.

## Overview

"A Fugue In Flask" provides a production-ready Flask application template that follows best practices for organization, configuration, and deployment. It serves as a solid foundation for building web applications that can be easily deployed to Azure.

## Features

- Modular application structure using Flask blueprints
- Environment-specific configuration management
- Database integration with SQLAlchemy
- Authentication system
- Azure deployment setup with CI/CD
- Testing framework
- Comprehensive documentation

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. Clone this repository
   ```
   git clone https://github.com/HarryJamesGreenblatt/A-Fugue-In-Flask.git
   cd A-Fugue-In-Flask
   ```

2. Create a virtual environment
   ```
   python -m venv venv
   ```

3. Activate the virtual environment
   - Windows: 
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux: 
     ```
     source venv/bin/activate
     ```

4. Install dependencies
   ```
   pip install -r requirements.txt
   ```

5. Set up environment variables by creating a `.env` file (or copy from `.env.example`)
   ```
   copy .env.example .env
   ```

6. Initialize the database
   - Windows: Run the batch file
     ```
     init_db.bat
     ```
   - macOS/Linux: Run the Python script directly
     ```
     python -m scripts.init_db
     ```

7. Run the application
   ```
   flask run
   ```

8. Access the application at http://127.0.0.1:5000

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
app/                    # Application package
  ├── __init__.py       # Application factory
  ├── models/           # Database models
  ├── routes/           # Blueprint routes
  ├── templates/        # Jinja2 templates
  ├── static/           # Static files
  ├── forms/            # Form classes
  └── utils/            # Utility functions
```

### Environment Variables

Key environment variables (defined in `.env`):
- `FLASK_APP`: Main application module (default: app.py)
- `FLASK_CONFIG`: Configuration environment (development, testing, production)
- `SECRET_KEY`: Secret key for session security
- `DEV_DATABASE_URI`: Database URI for development
- `DATABASE_URI`: Database URI for production

## Documentation

### Architecture Documentation

For detailed documentation about the application architecture and implementation:

- [Architecture Documentation](./docs/architecture.md) - Comprehensive overview of application structure and patterns
- [Setup Guide](./docs/setup.md) - Detailed setup instructions for local development

### Azure Deployment Documentation

We provide extensive documentation for deploying to Azure:

- [Azure Deployment Guide](./docs/azure_deployment.md) - Complete step-by-step instructions for deploying to Azure
- [Azure Key Vault Integration](./docs/azure_key_vault.md) - Guide for securely managing secrets with Azure Key Vault
- [GitHub Actions CI/CD](./docs/github_actions_azure.md) - Setting up continuous deployment with GitHub Actions
- [Azure SQL Database Integration](./docs/azure_sql_database.md) - Connecting your Flask app to Azure SQL Database
- [PostgreSQL Guide](./docs/postgresql_guide.md) - Alternative PostgreSQL deployment options

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

## License

MIT