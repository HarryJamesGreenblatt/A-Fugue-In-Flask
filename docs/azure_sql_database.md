# Azure SQL Database Integration

This document provides guidance on integrating Azure SQL Database with your Flask application.

## Why Azure SQL Database

For our Azure deployment, we chose Azure SQL Database for several reasons:

- **Cost-effectiveness**: Azure SQL's Basic tier (~$5/month) is more budget-friendly than many other database options
- **Native Azure integration**: As a Microsoft product, Azure SQL Database integrates seamlessly with other Azure services
- **Performance**: SQL Server offers excellent performance characteristics for many web applications
- **SQLAlchemy support**: SQLAlchemy provides a robust dialect for SQL Server via pyodbc

## Setting Up Azure SQL Database

### 1. Create an Azure SQL Server and Database

```bash
# Create SQL Server with a reusable generic name
az sql server create --name <server-name> --resource-group <resource-group> \
  --location <location> --admin-user <username> --admin-password "<password>"

# Create SQL Database (Basic tier) with application-specific name
az sql db create --resource-group <resource-group> --server <server-name> \
  --name <database-name> --service-objective Basic

# Configure firewall to allow Azure services
az sql server firewall-rule create --resource-group <resource-group> \
  --server <server-name> --name "AllowAllAzureServices" \
  --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
  
# Add your client IP for development access
az sql server firewall-rule create --resource-group <resource-group> \
  --server <server-name> --name "AllowMyClientIP" \
  --start-ip-address <your-ip-address> --end-ip-address <your-ip-address>
```

> **Note**: We use a generic SQL Server name that can be reused for multiple projects, while giving each application its own database with a specific name. This approach helps manage costs by consolidating Azure resources.

### 2. Connection String Format

Azure SQL Database supports several connection string formats with ODBC. The most reliable format for use with Flask-SQLAlchemy is:

```
mssql+pyodbc://<username>:<password>@<server>.database.windows.net/<database>?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&timeout=30
```

> **IMPORTANT**: Never store actual connection strings or credentials in source code or documentation. Always use environment variables, Azure Key Vault, or other secure methods for managing secrets as described in our security improvements.

## Flask Application Configuration

### 1. Install Required Packages

Add these packages to your `requirements.txt`:

```
pyodbc==4.0.39
python-dotenv==1.0.1
```

### 2. ODBC Driver Requirements

The Microsoft ODBC Driver for SQL Server must be installed on the development machine and deployment environment:

- **Windows**: [Download ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- **Linux**: [Install ODBC Driver on Linux](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- **Azure App Service**: Already pre-installed

### 3. Using Environment Variables for Configuration

We use a `.env` file for local development and environment variables for production. Create a `.env` file based on the provided `.env.template`:

```bash
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

### 4. Database URI Configuration

In `config.py`, we set the database URI using environment variables:

```python
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'TEMPLATE_DATABASE_URI', 
    os.environ.get('DATABASE_URI', 'sqlite:///prod.db')
)
```

### 3. Configure Environment Variables in Azure

Set up the connection string as an environment variable in your Azure Web App:

```bash
python scripts/direct_db_test.py
```

## Working with Migrations

SQLAlchemy and Flask-Migrate work with Azure SQL Database, but there are SQL Server-specific considerations:

### 1. SQL Server-Specific Data Types

SQL Server uses different data types from SQLite:
- Use `NVARCHAR` instead of `VARCHAR` for text fields
- Column size limits are strictly enforced (e.g., password hashes)
- Boolean values are represented as BIT (0/1) instead of BOOLEAN

### 2. Password Hash Column Size Considerations

Ensure your database columns are large enough to store modern password hashes:

```python
# Model definition example with sufficient column size for modern hash algorithms
class User(UserMixin, db.Model):
    # ...existing code...
    password_hash = db.Column(db.String(256), nullable=False)  # 256 characters for modern hash algorithms
    # ...existing code...
```

## Security Best Practices

### 1. Secure Credential Management

Following Azure best practices, we've implemented secure credential handling:

- Store credentials in `.env` file locally (excluded from Git)
- Use environment variables in production
- Implement credential masking in logs
- Consider Azure Key Vault for production deployments

### 2. Connection Security

Our connection string ensures secure communication:

- `Encrypt=yes`: Encrypts data in transit
- `TrustServerCertificate=yes`: Required for some environments
- `timeout=30`: Reasonable timeout to prevent hanging connections

### 3. Firewall Configuration

- Add your development machine's IP to Azure SQL firewall
- Limit production access to necessary services only

## Database Operations Best Practices

### 1. Use Pooling for Connections

SQL Server connections benefit from connection pooling. Consider adding pooling parameters to your connection string (pool_size, max_overflow).

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

For production environments, consider enabling Advanced Data Security and threat protection.

## Monitoring and Performance

### 1. Enable Query Insights

Enable Query Performance Insight to monitor and optimize query performance.

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
   - Increase connection timeout in your connection string

### Migration Issues

1. **Error: "Table X already exists"**
   - Check if your migration scripts are idempotent
   - Use `db.engine.dialect.has_table()` to check existence before creating

2. **Data Type Compatibility**
   - SQL Server has stricter type enforcement; review model definitions
   - Strings typically need explicit length declarations

##### 3. Efficient Querying

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

For production environments, consider enabling Advanced Data Security and threat protection.

## Monitoring and Performance

### 1. Enable Query Insights

Enable Query Performance Insight to monitor and optimize query performance.

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
   - Increase connection timeout in your connection string

### Migration Issues

1. **Error: "Table X already exists"**
   - Check if your migration scripts are idempotent
   - Use `db.engine.dialect.has_table()` to check existence before creating

2. **Data Type Compatibility**
   - SQL Server has stricter type enforcement; review model definitions
   - Strings typically need explicit length declarations

 Further Reading

- [Azure SQL Database Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [SQLAlchemy SQL Server Dialect](https://docs.sqlalchemy.org/en/14/dialects/mssql.html)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [Microsoft ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server)