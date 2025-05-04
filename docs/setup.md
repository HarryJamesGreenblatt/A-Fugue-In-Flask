# A Fugue In Flask - Setup Guide

This step-by-step guide walks you through setting up and running the Flask application with Azure SQL Database.

## Prerequisites

Before you begin, make sure you have the following installed on your system:

- **Python 3.9+**: The programming language used to build the application
- **pip**: Python package manager (usually comes with Python)
- **Git**: Version control system (optional, but recommended)
- **Microsoft ODBC Driver for SQL Server**: Required for Azure SQL connectivity
- **A code editor**: VS Code, PyCharm, Sublime Text, etc.

## Step 1: Clone or Download the Repository

### Option A: Using Git

```bash
git clone https://github.com/HarryJamesGreenblatt/A-Fugue-In-Flask.git
cd A-Fugue-In-Flask
```

### Option B: Download ZIP

1. Go to https://github.com/HarryJamesGreenblatt/A-Fugue-In-Flask
2. Click the green "Code" button and select "Download ZIP"
3. Extract the ZIP file to a folder of your choice
4. Open a terminal or command prompt and navigate to that folder

## Step 2: Install ODBC Driver for SQL Server

### Windows

1. Download the [Microsoft ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
2. Run the installer and follow the prompts

### macOS

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17
```

### Linux (Ubuntu)

```bash
sudo su
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
exit
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

## Step 3: Set Up a Virtual Environment

A virtual environment isolates your project dependencies from other Python projects.

### Windows

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

### macOS/Linux

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

> **How to tell if it worked**: Your command prompt should show `(venv)` at the beginning, indicating the virtual environment is active.

## Step 4: Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

> **What's happening**: This installs all required packages including Flask, SQLAlchemy, pyodbc for Azure SQL connectivity, and python-dotenv for environment variable management.

## Step 5: Set Up Environment Variables

Create a `.env` file in the project root based on the `.env.template` file:

```bash
# Windows
copy .env.template .env

# macOS/Linux
cp .env.template .env
```

Then edit the `.env` file with your Azure SQL Database credentials:

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

> **Security Note**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

## Step 6: Initialize the Azure SQL Database

Run the direct database initialization script to create tables in your Azure SQL database:

```bash
python -m scripts.direct_db_test
```

> **What's happening**: This creates the necessary tables in your Azure SQL database using a direct PyODBC connection rather than SQLAlchemy migrations.
>
> **Alternative**: If you prefer using SQLite for local development, run `python -m scripts.init_db` instead.

## Step 7: Run the Azure SQL Connection Fix Script

To ensure your database connection is properly configured and working:

```bash
python -m scripts.azure_sql_fix
```

> **What's happening**: This script runs diagnostics to check connectivity to your Azure SQL Database, tests multiple connection string formats, and updates your application configuration with a working connection string. It also creates a SQLite fallback if Azure SQL cannot be reached.

## Step 8: Run the Flask Application

With everything set up, you can now run the application:

```bash
# Set configuration to use Azure SQL
set FLASK_CONFIG=azure  # Windows
export FLASK_CONFIG=azure  # macOS/Linux

# Run the application
flask run
```

For enhanced diagnostics, you can use the run_with_diagnostics script:

```bash
python -m scripts.run_with_diagnostics
```

## Step 9: Access the Application

Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

You should see the home page of your Flask application. You can register a new account or log in with the default admin account (if you created one during initialization).

## Understanding the Project Structure

Here's a quick overview of the most important files and directories:

```
app.py                  # Application entry point
config.py               # Configuration settings
appsettings.json        # Database connection settings
├── app/                # Main application package
│   ├── __init__.py     # Application factory
│   ├── routes/         # URL route handlers
│   ├── models/         # Database models
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JavaScript, images
├── scripts/            # Utility scripts for database operations
│   ├── azure_sql_fix.py    # Diagnostic and fix script for Azure SQL
│   ├── direct_db_test.py   # Direct table creation script
│   └── update_schema.py    # Schema update utility
└── docs/               # Documentation
    └── azure_sql_database.md  # Azure SQL specific documentation
```

## Common Issues and Solutions

### Azure SQL Connection Issues

If you encounter connection problems with Azure SQL:

1. **Firewall Issues**: Ensure your IP address is in the Azure SQL firewall allowlist
2. **Driver Issues**: Verify the ODBC driver is installed correctly (`pyodbc.drivers()` should list SQL Server drivers)
3. **Connection String Format**: Different environments might require slightly different connection strings
4. **Credentials**: Double-check your username, password, server name, and database name

Run `python -m scripts.azure_sql_fix` to diagnose and resolve these issues automatically.

### Schema Mismatch

If your models don't match the database schema:

```bash
python -m scripts.update_schema
```

This will add any missing columns required by your models.

## Azure Deployment

For deploying to Azure App Service:

1. Create an Azure Web App
2. Set the required environment variables in the App Service configuration
3. Deploy your code using Git, GitHub Actions, or Azure DevOps

See `docs/azure_deployment.md` for detailed instructions.

## Next Steps

After getting the application running, you might want to:

1. **Explore the code**: Look through the different files to understand how they work together
2. **Make a small change**: Modify a template or add a new route to see how changes affect the app
3. **Read the architecture documentation**: See `docs/architecture.md` for a deeper understanding
4. **Deploy the application**: Follow the deployment guide at `docs/deployment.md`

## Flask Development Workflow

As you develop with Flask, you'll typically follow this workflow:

1. **Make code changes** in your editor
2. **Save the files** - the development server will usually auto-reload
3. **Refresh your browser** to see changes
4. **Check the console** for any errors
5. **Repeat** until you're satisfied with the results

> **Tip**: The Flask development server has hot-reloading enabled by default, so most changes will be reflected without restarting the server. However, some changes (like adding new files or changing the application structure) might require a manual restart.

## Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)