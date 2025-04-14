# PostgreSQL on Azure Guide

This guide walks you through setting up and deploying your Flask application with PostgreSQL on Azure.

## Setting Up PostgreSQL on Azure

### 1. Create an Azure Database for PostgreSQL

You can set up PostgreSQL on Azure using either PowerShell or the Azure Portal.

#### Using PowerShell:

```powershell
# Log in to Azure
Connect-AzAccount

# Create a resource group if you don't have one
New-AzResourceGroup -Name flask-app-rg -Location "East US"

# Create PostgreSQL server
New-AzPostgreSqlServer -ResourceGroupName flask-app-rg `
                       -Name a-fugue-in-flask-db `
                       -Location "East US" `
                       -AdministratorLogin dbadmin `
                       -AdministratorLoginPassword (ConvertTo-SecureString -String "YourSecurePassword123!" -AsPlainText -Force) `
                       -Sku GP_Gen5_2

# Create database
New-AzPostgreSqlDatabase -ResourceGroupName flask-app-rg `
                         -ServerName a-fugue-in-flask-db `
                         -Name flask_app

# Configure firewall rules to allow Azure services
New-AzPostgreSqlFirewallRule -ResourceGroupName flask-app-rg `
                             -ServerName a-fugue-in-flask-db `
                             -Name AllowAzureServices `
                             -StartIPAddress 0.0.0.0 `
                             -EndIPAddress 0.0.0.0
```

#### Using Azure Portal:

1. Log in to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" and search for "Azure Database for PostgreSQL"
3. Select "Azure Database for PostgreSQL" and click "Create"
4. Choose "Single server" or "Flexible server" (Flexible is newer and recommended)
5. Fill in the server details:
   - Server name: `a-fugue-in-flask-db`
   - Location: Choose a region close to your users
   - Version: Choose PostgreSQL 14 or 15
   - Admin username: `dbadmin`
   - Password: Create a secure password
6. Choose compute and storage:
   - For development, Basic tier is sufficient
   - For production, General Purpose or Memory Optimized
7. Click "Review + create" and then "Create"
8. Once created, go to your PostgreSQL server and:
   - Create a database named `flask_app`
   - Under "Connection security", enable "Allow Azure services to access server"

### 2. Get Connection String

After creating your PostgreSQL server, you'll need the connection string:

```
postgresql://dbadmin:YourSecurePassword@a-fugue-in-flask-db.postgres.database.azure.com:5432/flask_app
```

## Updating Your Flask App for PostgreSQL

### 1. Set Environment Variables in Azure

In your Azure App Service, add the following application settings:

#### Using PowerShell:

```powershell
$appSettings = @{
    DATABASE_URI = "postgresql://dbadmin:YourSecurePassword@a-fugue-in-flask-db.postgres.database.azure.com:5432/flask_app"
}

Set-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask -AppSettings $appSettings
```

#### Using Azure Portal:

1. Go to your App Service
2. Navigate to "Configuration" under "Settings"
3. Add a new application setting:
   - Name: `DATABASE_URI`
   - Value: `postgresql://dbadmin:YourSecurePassword@a-fugue-in-flask-db.postgres.database.azure.com:5432/flask_app`

### 2. Deploy Your App

During deployment, the `startup.sh` script will:
1. Detect the PostgreSQL connection
2. Run the migration script
3. Start the Gunicorn server

## Local Development with PostgreSQL

For local development with PostgreSQL:

### 1. Install PostgreSQL Locally

1. Download and install [PostgreSQL](https://www.postgresql.org/download/windows/)
2. During installation, note your password for the postgres user
3. After installation, create a database:
   ```
   createdb flask_app
   ```

### 2. Set Environment Variables

Set the `DATABASE_URI` environment variable:

```
set DATABASE_URI=postgresql://postgres:YourPassword@localhost:5432/flask_app
```

or create a `.env` file with:

```
DATABASE_URI=postgresql://postgres:YourPassword@localhost:5432/flask_app
```

### 3. Run Database Migrations

```
flask db upgrade
```

Or use the provided batch file:

```
init_postgres.bat
```

## PostgreSQL Tips for Flask Developers

### Database URL Format

```
postgresql://username:password@hostname:port/database
```

### Common SQLAlchemy Data Types for PostgreSQL

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID, ARRAY

class Example(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB)  # PostgreSQL-specific JSON with binary storage
    tags = Column(ARRAY(String))  # PostgreSQL-specific array type
```

### PostgreSQL-Specific Features

PostgreSQL offers several features that SQLite doesn't:

1. **JSON/JSONB Support**: Store and query JSON data
2. **Array Types**: Store arrays of values
3. **Full Text Search**: Powerful text search capabilities
4. **Concurrent Access**: Better handling of multiple simultaneous connections
5. **Transactions**: Full ACID compliance with proper transactions

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Verify the connection string format
2. Check that the firewall rules allow connections
3. Ensure your password doesn't contain special characters that need URL encoding
4. Verify that the database exists

### Migration Issues

If migrations fail:

1. Check migration scripts for any SQLite-specific syntax
2. Run migrations manually to see detailed error messages
3. Consider creating a new migration with `flask db migrate`

## Resources

- [SQLAlchemy PostgreSQL Documentation](https://docs.sqlalchemy.org/en/14/dialects/postgresql.html)
- [Azure PostgreSQL Documentation](https://docs.microsoft.com/en-us/azure/postgresql/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)