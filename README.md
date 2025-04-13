# A Fugue In Flask

A comprehensive Flask application template with Azure deployment capabilities.

## Overview

"A Fugue In Flask" provides a production-ready Flask application template that follows best practices for organization, configuration, and deployment. It serves as a solid foundation for building web applications that can be easily deployed to Azure.

## Features

- Modular application structure using Flask blueprints
- Environment-specific configuration management
- Database integration with SQLAlchemy
- Authentication system
- Azure deployment setup
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

For detailed documentation about the architecture, implementation, and deployment, see the [docs](./docs) directory:

- [Architecture Documentation](./docs/architecture.md)
- [Deployment Guide](./docs/deployment.md)

## Testing

Run tests with pytest:

```
pytest
```

## Deployment

This template includes configuration for deploying to Azure App Service. See the [deployment guide](./docs/deployment.md) for detailed instructions.

## License

MIT