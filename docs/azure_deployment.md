# Deploying A Fugue In Flask to Azure

This guide walks you through deploying your Flask application to Microsoft Azure App Service with an Azure SQL Database backend.

## Why Azure App Service?

Azure App Service is Microsoft's Platform-as-a-Service (PaaS) offering that's ideal for Flask applications:

- **Easy to deploy**: Streamlined deployment from Git or through CI/CD pipelines
- **Managed environment**: No need to worry about server management or patches
- **Built-in scaling**: Easily scale your application as needed
- **Integrated with Azure ecosystem**: Simple integration with other Azure services
- **Security**: Built-in authentication, HTTPS, and security features

## Prerequisites

Before deploying, ensure you have:

1. **Azure Account**: Create one at [portal.azure.com](https://portal.azure.com) (free tier available)
2. **Azure CLI** or **Azure PowerShell**: 
   - CLI: Install from [Microsoft's website](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
   - PowerShell: Install from [PowerShell Gallery](https://docs.microsoft.com/en-us/powershell/azure/install-az-ps)
3. **Git**: Your project should be tracked in a Git repository
4. **GitHub Account**: For GitHub Actions CI/CD integration

## Deployment Architecture

Our deployment uses the following Azure services:

```mermaid
flowchart TD
    subgraph "User's Browser"
        A[Browser Requests]
    end
    
    subgraph "Azure Services"
        B[Azure App Service]
        C[Azure SQL Database]
        D[Azure Key Vault]
        E[GitHub Actions]
    end
    
    A <-->|HTTPS| B
    B <-->|ODBC| C
    B <-->|Secure Access| D
    E -->|Continuous Deployment| B
```

## Step-By-Step Deployment Guide

### 1. Azure Login and Subscription Selection

Login to Azure and select the appropriate subscription:

```bash
# Login to Azure
az login

# List available subscriptions
az account list --output table

# Set active subscription (replace with your subscription name)
az account set --subscription "Visual Studio Enterprise Subscription"
```

### 2. Resource Group Creation

Create a resource group to contain all of your application's Azure resources:

```bash
# Create a resource group
az group create --name flaskapp-rg --location westus
```

### 3. App Service Plan Creation

Create an App Service plan. This example uses the Free tier (F1) for testing:

```bash
# Create an App Service plan
az appservice plan create --name flask-free-plan --resource-group flaskapp-rg --location westus --sku F1 --is-linux
```

For production, consider using at least a Basic (B1) or Standard (S1) tier.

### 4. Web App Creation

Create a Web App using the App Service plan:

```bash
# Create a Web App
az webapp create --name flask-fugue-app --resource-group flaskapp-rg --plan flask-free-plan --runtime "PYTHON:3.9"
```

### 5. Key Vault Setup

Set up Azure Key Vault to securely store secrets like your database credentials:

```bash
# Create a Key Vault
az keyvault create --name flask-fugue-kv --resource-group flaskapp-rg --location westus

# Generate and store a secret key
SECRET_KEY=$(openssl rand -hex 32)
az keyvault secret set --vault-name flask-fugue-kv --name "FLASK-SECRET-KEY" --value "$SECRET_KEY"
```

### 6. Azure SQL Database Setup

Create an Azure SQL Server and Database:

```bash
# Create SQL Server
az sql server create --name flask-template-sqlserver --resource-group flaskapp-rg --location westus --admin-user sqladmin --admin-password "YourStrongPassword123!"

# Create SQL Database (Basic tier)
az sql db create --resource-group flaskapp-rg --server flask-template-sqlserver --name flask-template-db --service-objective Basic

# Configure firewall to allow Azure services
az sql server firewall-rule create --resource-group flaskapp-rg --server flask-template-sqlserver --name "AllowAllAzureServices" --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

### 7. Application Settings Configuration

Configure your web app settings to include connection strings and environment variables:

```bash
# Get the secret key from Key Vault
SECRET_KEY=$(az keyvault secret show --vault-name flask-fugue-kv --name "FLASK-SECRET-KEY" --query value -o tsv)

# Set application settings
az webapp config appsettings set --name flask-fugue-app --resource-group flaskapp-rg --settings \
    FLASK_CONFIG="production" \
    SECRET_KEY="$SECRET_KEY" \
    DATABASE_URI="mssql+pyodbc://sqladmin:YourStrongPassword123!@flask-template-sqlserver.database.windows.net/flask-template-db?driver=ODBC+Driver+17+for+SQL+Server"
```

### 8. Continuous Deployment with GitHub Actions

Set up GitHub Actions for continuous deployment:

1. Create a `.github/workflows/azure-deploy.yml` file:

```yaml
name: Deploy Flask app to Azure App Service

on:
  push:
    branches:
      - main
      - master
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'flask-fugue-app'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        package: .
```

2. Get the publish profile from Azure:

```bash
# Download publish profile
az webapp deployment list-publishing-profiles --name flask-fugue-app --resource-group flaskapp-rg --xml > azure-publish-profile.xml
```

3. Add the publish profile as a GitHub secret:

```bash
# Using GitHub CLI
gh secret set AZURE_WEBAPP_PUBLISH_PROFILE --body "$(cat azure-publish-profile.xml)"
```
****
### 9. Code Modifications for Azure SQL Support

Ensure your application is configured for Azure SQL:

1. Add the required dependencies to `requirements.txt`:
```
pyodbc==4.0.39
sqlalchemy-pytds==0.3.2  # Alternative for SQL Server connections
```

> **Note**: We use the standard `pyodbc` package with SQLAlchemy's built-in MS SQL Server dialect instead of the `sqlalchemy-pyodbc-azure` package (which may not be available in all Python environments).

2. Update `startup.sh` to handle Azure SQL connections:
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

## Monitoring and Management

### Viewing Application Logs

```bash
# View logs in real-time
az webapp log tail --name flask-fugue-app --resource-group flaskapp-rg
```

### Monitoring Application Performance

Consider adding Azure Application Insights for more detailed monitoring:

```bash
# Create Application Insights
az monitor app-insights component create --app flask-app-insights --location westus --resource-group flaskapp-rg

# Get the instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show --app flask-app-insights --resource-group flaskapp-rg --query instrumentationKey -o tsv)

# Add to app settings
az webapp config appsettings set --name flask-fugue-app --resource-group flaskapp-rg --settings APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSTRUMENTATION_KEY"
```

## Cost Management and Optimization

Our deployment uses cost-effective services:

- **App Service Plan**: Free tier (F1) for development, consider Basic (B1) for production (~$13/month)
- **Azure SQL Database**: Basic tier (~$5/month)
- **Azure Key Vault**: Free tier for up to 10,000 operations/month

To further optimize costs:

1. Use the App Service's auto-scaling in production to scale based on demand
2. Consider shared compute resources for non-critical applications
3. Set up budget alerts to monitor spending

## Troubleshooting Common Issues

### Deployment Failures

1. Check GitHub Actions workflow logs for errors
2. Verify the publish profile is correctly set in GitHub Secrets
3. Ensure your application runs locally before deployment

### GitHub Actions Authentication Issues

If you encounter an error like "No credentials found. Add an Azure login action before this action" in your GitHub Actions workflow, you need to:

1. Create a service principal for Azure authentication:
   ```bash
   az ad sp create-for-rbac --name "flask-fugue-github-actions" --role contributor --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/flaskapp-rg --sdk-auth > azure_credentials.json
   ```

2. Add the output JSON as a GitHub secret:
   ```bash
   # Using GitHub CLI
   gh secret set AZURE_CREDENTIALS --body "$(cat azure_credentials.json)"
   
   # Or through the GitHub web interface:
   # Settings > Secrets > Actions > New repository secret
   # Name: AZURE_CREDENTIALS
   # Value: [paste entire JSON output]
   ```

3. Update your GitHub Actions workflow to include an Azure login step:
   ```yaml
   - name: Azure Login
     uses: azure/login@v1
     with:
       creds: ${{ secrets.AZURE_CREDENTIALS }}
   ```

4. Delete the local credentials file for security:
   ```bash
   rm azure_credentials.json
   ```

### Application Startup Errors

If your application deploys successfully but shows an "Application Error" when you try to access it, the most common issues are:

1. **Missing dependencies**: Azure may not automatically install dependencies during deployment
2. **Incorrect startup command**: Azure might not identify the correct way to start your Flask app
3. **Database connection issues**: The connection string may be incorrect or inaccessible

To fix these issues:

1. Create an Azure-specific startup script (`startup_azure.sh`):
   ```bash
   #!/bin/bash
   
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Check database type and run migrations
   if [[ $DATABASE_URI == postgresql://* ]]; then
       echo "PostgreSQL database detected, running migration script..."
       python -m scripts.migrate_postgres
   elif [[ $DATABASE_URI == mssql+pyodbc://* ]]; then
       echo "Azure SQL database detected, running migration script..."
       flask db upgrade
   else
       echo "Running standard database migrations..."
       flask db upgrade
   fi
   
   # Start Gunicorn server
   exec gunicorn --bind=0.0.0.0:8000 --timeout 600 "app:create_app()"
   ```

2. Configure Azure App Service to use your custom startup script:
   ```bash
   az webapp config set --name flask-fugue-app --resource-group flaskapp-rg --startup-file "startup_azure.sh"
   ```

3. View application logs to diagnose specific issues:
   ```bash
   az webapp log tail --name flask-fugue-app --resource-group flaskapp-rg
   ```

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure SQL Database Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)