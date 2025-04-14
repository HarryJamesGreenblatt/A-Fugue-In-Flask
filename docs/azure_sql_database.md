# Azure SQL Database Integration

This document provides guidance on integrating Azure SQL Database with your Flask application.

## Azure SQL vs. PostgreSQL

For our Azure deployment, we chose Azure SQL Database over PostgreSQL for several reasons:

- **Cost-effectiveness**: Azure SQL's Basic tier (~$5/month) is more budget-friendly than the entry-level Azure Database for PostgreSQL options
- **Native Azure integration**: As a Microsoft product, Azure SQL Database integrates seamlessly with other Azure services
- **Performance**: SQL Server offers excellent performance characteristics for many web applications
- **Manageable transition**: SQLAlchemy abstracts much of the database-specific code, making the transition relatively painless

## Setting Up Azure SQL Database

### 1. Create an Azure SQL Server and Database

```bash
# Create SQL Server
az sql server create --name flask-template-sqlserver --resource-group flaskapp-rg \
  --location westus --admin-user sqladmin --admin-password "YourStrongPassword123!"

# Create SQL Database (Basic tier)
az sql db create --resource-group flaskapp-rg --server flask-template-sqlserver \
  --name flask-template-db --service-objective Basic

# Configure firewall to allow Azure services
az sql server firewall-rule create --resource-group flaskapp-rg \
  --server flask-template-sqlserver --name "AllowAllAzureServices" \
  --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

### 2. Connection String Format

The connection string format for Azure SQL Database in SQLAlchemy is:

```
mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server
```

For example:

```
mssql+pyodbc://sqladmin:YourStrongPassword123!@flask-template-sqlserver.database.windows.net/flask-template-db?driver=ODBC+Driver+17+for+SQL+Server
```

## Flask Application Configuration

### 1. Install Required Packages

Add these packages to your `requirements.txt`:

```
pyodbc==4.0.39
sqlalchemy-pytds==0.3.2  # Alternative for SQL Server connections
```

> **Note**: We're using the standard `pyodbc` package with SQLAlchemy's built-in MS SQL Server dialect, rather than the unavailable `sqlalchemy-pyodbc-azure` package. The `sqlalchemy-pytds` package provides an alternative SQL Server connection method if needed.

### 2. Update Database URI in Configuration

In your `config.py` file, set the production database URI:

```python
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URI', 
    'mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server'
)
```

### 3. Configure Environment Variables in Azure

Set up the connection string as an environment variable in your Azure Web App:

```bash
az webapp config appsettings set --name flask-fugue-app --resource-group flaskapp-rg \
  --settings DATABASE_URI="mssql+pyodbc://sqladmin:YourStrongPassword123!@flask-template-sqlserver.database.windows.net/flask-template-db?driver=ODBC+Driver+17+for+SQL+Server"
```

## Working with Migrations

SQLAlchemy and Flask-Migrate work with Azure SQL Database, but there are a few SQL Server-specific considerations:

### 1. Update Your Migration Scripts

SQL Server has some syntax differences from SQLite or PostgreSQL. Your migration scripts may need adjustments:

- Different data types (e.g., `NVARCHAR` instead of `VARCHAR`)
- Different constraints syntax
- Different auto-increment behavior

### 2. Handle Migrations During Deployment

Update your `startup.sh` script to detect the database type and apply migrations accordingly:

```bash
#!/bin/bash

# Check database type
if [[ $DATABASE_URI == postgresql://* ]]; then
    echo "PostgreSQL database detected, running migration script..."
    python -m scripts.migrate_postgres
elif [[ $DATABASE_URI == mssql+pyodbc://* ]]; then
    echo "Azure SQL database detected, running migration script..."
    flask db upgrade
else
    # Apply regular database migrations
    echo "Running standard database migrations..."
    flask db upgrade
fi

# Start Gunicorn server
exec gunicorn --config gunicorn.conf.py "app:create_app()"
```

## Database Operations Best Practices

### 1. Use Pooling for Connections

SQL Server connections benefit from connection pooling. Make sure your database URI includes pooling parameters:

```
mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server&pool_size=30&max_overflow=10
```

### 2. Handle Timeouts Appropriately

Azure SQL Database may enforce connection timeouts. Implement retry logic for critical operations:

```python
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def database_operation():
    try:
        # Your critical database operation
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise
```

### 3. Efficient Querying

Azure SQL Database performs best with optimized queries:

- Use indexing on commonly queried columns
- Avoid N+1 query patterns by using eager loading
- For large result sets, use pagination

## Security Considerations

### 1. Protect Connection Strings

Never hard-code connection strings:

- Store them in Azure Key Vault
- Set them as environment variables in App Service
- Use Azure Managed Identities for database access when possible

### 2. Restrict Database Access

- Use the firewall rules to limit access to necessary IP ranges
- Create database users with minimum required permissions
- Enable auditing and threat detection in Azure Portal

### 3. Enable Advanced Security Features

For production environments:

```bash
# Enable Advanced Data Security
az sql db update --resource-group flaskapp-rg --server flask-template-sqlserver \
  --name flask-template-db --set "advancedThreatProtectionSettings.state=Enabled"
```

## Monitoring and Performance

### 1. Enable Query Insights

```bash
# Enable Query Performance Insight
az sql db update --resource-group flaskapp-rg --server flask-template-sqlserver \
  --name flask-template-db --set "queryStoreOptions.queryStoreEnabled=true"
```

### 2. Add Index Recommendations

Azure SQL Database provides automatic index recommendations based on your query patterns:

1. In Azure Portal, navigate to your database
2. Select "Performance recommendations" 
3. Review and apply suggested indexes

## Cost Management

The Basic tier (~$5/month) is suitable for development and light production workloads. Monitor usage and consider:

- Scaling up during high-traffic periods
- Implementing caching strategies to reduce database load
- Using elastic pools if you have multiple databases with complementary usage patterns

## Troubleshooting Common Issues

### Connection Problems

1. **Error: "Cannot open server X requested by the login"**
   - Ensure the Azure SQL Server firewall allows Azure services (0.0.0.0)

2. **Error: "TCP Provider: The specified DSN contains an architecture mismatch"**
   - Make sure you have the correct ODBC driver installed

3. **Timeout Errors**
   - Increase connection timeout in your connection string:
     `...&connection_timeout=30`

### Migration Issues

1. **Error: "Table X already exists"**
   - Check if your migration scripts are idempotent
   - Use `db.engine.dialect.has_table()` to check existence before creating

2. **Data Type Compatibility**
   - SQL Server has stricter type enforcement; review model definitions
   - Strings typically need explicit length declarations

## Further Reading

- [Azure SQL Database Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [SQLAlchemy SQL Server Dialect](https://docs.sqlalchemy.org/en/14/dialects/mssql.html)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)