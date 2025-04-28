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
```

> **Note**: We use a generic SQL Server name that can be reused for multiple projects, while giving each application its own database with a specific name. This approach helps manage costs by consolidating Azure resources.

### 2. Connection String Format

The connection string format for Azure SQL Database in SQLAlchemy is:

```
mssql+pyodbc://<username>:<password>@<server>.database.windows.net/<database>?driver=ODBC+Driver+17+for+SQL+Server
```

> **IMPORTANT**: Never store actual connection strings or credentials in documentation, source control, or any other public location. Always use environment variables, Azure Key Vault, or other secure methods for managing secrets.

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
    'TEMPLATE_DATABASE_URI', 
    os.environ.get('DATABASE_URI', 'sqlite:///prod.db')
)
```

### 3. Configure Environment Variables in Azure

Set up the connection string as an environment variable in your Azure Web App:

```bash
az webapp config appsettings set --name <app-name> --resource-group <resource-group> \
  --settings DATABASE_URI="<connection-string>"
```

## Working with Migrations

SQLAlchemy and Flask-Migrate work with Azure SQL Database, but there are a few SQL Server-specific considerations:

### 1. Update Your Migration Scripts

SQL Server has some syntax differences from SQLite or PostgreSQL. Your migration scripts may need adjustments:

- Different data types (e.g., `NVARCHAR` instead of `VARCHAR`)
- Different constraints syntax
- Different auto-increment behavior

### 2. Handle Migrations During Deployment

Update your `startup_azure.sh` script to detect the database type and apply migrations accordingly:

```bash
#!/bin/bash

# Check database type - use TEMPLATE_DATABASE_URI if available, otherwise fall back to DATABASE_URI
DB_URI=${TEMPLATE_DATABASE_URI:-$DATABASE_URI}

# Check database type
if [[ $DB_URI == postgresql://* ]]; then
    echo "PostgreSQL database detected, running migration script..."
    python -m scripts.migrate_postgres
elif [[ $DB_URI == mssql+pyodbc://* ]]; then
    echo "Azure SQL database detected, running migration script..."
    flask db upgrade
else
    # Apply regular database migrations
    echo "Running standard database migrations..."
    flask db upgrade
fi

# Start Gunicorn server
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 "app:create_app()"
```

### 3. Password Hash Column Size Considerations

When using modern password hashing algorithms (like scrypt, bcrypt, or Argon2), ensure your database columns are large enough to store the generated hashes:

```python
# Model definition example with sufficient column size for modern hash algorithms
class User(UserMixin, db.Model):
    # ...existing code...
    password_hash = db.Column(db.String(256), nullable=False)  # 256 characters for modern hash algorithms
    # ...existing code...
```

Common issues and solutions:

- **Error**: "String or binary data would be truncated in table" when storing password hashes
- **Solution**: Increase the column length (we use 256 characters as a safe value)
- **Migration**: Create a specific migration to alter the column size:

```python
# Migration example to increase column size
"""Increase password_hash column length

Revision ID: 7f23e04989ee
Revises: 9f4a4f0691fe
Create Date: 2025-04-28 12:34:56

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '7f23e04989ee'
down_revision = '9f4a4f0691fe'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(128),
                    type_=sa.String(256),
                    existing_nullable=False)

def downgrade():
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(256),
                    type_=sa.String(128),
                    existing_nullable=False)
```

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

## Further Reading

- [Azure SQL Database Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [SQLAlchemy SQL Server Dialect](https://docs.sqlalchemy.org/en/14/dialects/mssql.html)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)