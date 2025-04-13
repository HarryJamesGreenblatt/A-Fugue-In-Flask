# Deploying A Fugue In Flask to Azure

This guide provides step-by-step instructions for deploying your Flask application to Azure App Service.

## Prerequisites

- Azure account with an active subscription
- Azure CLI installed and configured
- Git installed
- Your Flask application ready for deployment

## Deployment Options

There are several ways to deploy a Flask application to Azure:

1. Azure Portal deployment
2. Azure CLI deployment
3. GitHub Actions CI/CD pipeline
4. Azure DevOps CI/CD pipeline

This guide focuses on methods 1 and 2, which are the most straightforward.

## Operating System Choice: Linux Recommendation

This guide recommends using Linux for your Azure App Service deployment for several important reasons:

1. **Cost Efficiency**: Linux App Service Plans are typically 30-40% less expensive than their Windows counterparts for the same specifications.

2. **Python Ecosystem Compatibility**: The Python ecosystem is more native to Linux environments, which can lead to fewer dependency conflicts and compatibility issues.

3. **Performance**: Flask applications often perform better on Linux-based servers due to the lightweight nature of Linux and better optimization of Python on this platform.

4. **Container Support**: If you decide to containerize your application in the future (using Docker), the Linux environment provides better and more native Docker support.

5. **Industry Standard**: Most production Flask deployments use Linux-based servers, aligning with industry best practices.

While Windows deployments are possible and may be preferred if you have specific Windows dependencies or integration requirements, this guide focuses on the Linux approach as the recommended path.

## Preparing Your Application for Azure

Before deploying, ensure your application is properly configured for Azure:

1. Create a `requirements.txt` file (already included in this template)
2. Create a `startup.sh` file in the root directory for Gunicorn configuration
3. Configure the `WEBSITES_PORT` environment variable in Azure

### Startup Script

Create a `startup.sh` file in the root of your project:

```bash
#!/bin/bash

# Make startup script executable in case it isn't:
chmod +x startup.sh

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
flask db upgrade

# Start Gunicorn
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
```

## Method 1: Azure Portal Deployment

```mermaid
flowchart TD
    A[Create Azure App Service] --> B[Configure App Settings]
    B --> C[Deploy Code via Portal]
    C --> D[Configure Custom Domain] 
    D --> E[Enable HTTPS]
```

1. **Create an App Service**:
   - Log in to the [Azure Portal](https://portal.azure.com)
   - Click on "Create a resource"
   - Search for "Web App" and select it
   - Fill in the details:
     - Subscription: Your subscription
     - Resource Group: Create new or use existing
     - Name: Unique app name (e.g., fugue-in-flask)
     - Publish: Code
     - Runtime stack: Python 3.9 or later
     - Operating System: Linux (recommended)
     - Region: Choose a region close to your users
   - Click "Review + create" and then "Create"

2. **Configure App Settings**:
   - Once the App Service is created, go to it
   - Navigate to "Settings" > "Configuration"
   - Add the following application settings:
     - `FLASK_APP`: app.py
     - `FLASK_CONFIG`: production
     - `SECRET_KEY`: [Generate a secure random key]
     - `DATABASE_URI`: [Your database connection string]
     - `WEBSITES_PORT`: 8000
   - Save the settings

3. **Deploy Your Code**:
   - Navigate to "Deployment Center"
   - Choose your source control system (GitHub, Azure Repos, Local Git)
   - Follow the wizard to connect your repository
   - Azure will automatically deploy your application

## Method 2: Azure CLI Deployment

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CLI as Azure CLI
    participant Azure as Azure App Service
    
    Dev->>CLI: az login
    Dev->>CLI: az group create
    Dev->>CLI: az appservice plan create
    Dev->>CLI: az webapp create
    Dev->>CLI: az webapp config set
    Dev->>CLI: az webapp config appsettings set
    CLI->>Azure: Create and configure resources
    Dev->>Azure: git push azure main
```

1. **Log in to Azure**:
   ```bash
   az login
   ```

2. **Create a Resource Group**:
   ```bash
   az group create --name myResourceGroup --location "East US"
   ```

3. **Create an App Service Plan**:
   ```bash
   az appservice plan create --name myAppServicePlan --resource-group myResourceGroup --sku B1 --is-linux
   ```

4. **Create a Web App**:
   ```bash
   az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name fugue-in-flask --runtime "PYTHON:3.9"
   ```

5. **Configure the Web App**:
   ```bash
   az webapp config set --resource-group myResourceGroup --name fugue-in-flask --startup-file "startup.sh"
   ```

6. **Set Environment Variables**:
   ```bash
   az webapp config appsettings set --resource-group myResourceGroup --name fugue-in-flask --settings FLASK_APP=app.py FLASK_CONFIG=production SECRET_KEY=your-secret-key DATABASE_URI=your-database-uri WEBSITES_PORT=8000
   ```

7. **Deploy Your Code**:
   ```bash
   cd /path/to/your/project
   az webapp deployment source config-local-git --name fugue-in-flask --resource-group myResourceGroup
   git remote add azure <git-url-from-previous-command>
   git push azure main
   ```

## Database Configuration

For production deployments, you'll want to use a managed database service:

### Azure Database for PostgreSQL

1. **Create a PostgreSQL Server**:
   - In the Azure Portal, create a new Azure Database for PostgreSQL
   - Configure server name, admin credentials, and other settings
   - Allow access from Azure services

2. **Update Your Application Configuration**:
   - Set your `DATABASE_URI` environment variable to the PostgreSQL connection string
   - Format: `postgresql://username:password@server-name.postgres.database.azure.com:5432/database-name`

## Setting Up CI/CD with GitHub Actions

```mermaid
graph TD
    A[GitHub Repository] --> B[GitHub Actions Workflow]
    B --> C[Build and Test]
    C --> D[Deploy to Azure]
    B --> E[Azure App Service]
```

1. **Create GitHub Actions Workflow**:
   - Create a `.github/workflows` directory in your project
   - Add a `main_deploy.yml` file with the following content:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run tests
        run: |
          pytest
          
      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'fugue-in-flask'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

2. **Add GitHub Secret**:
   - In your GitHub repository, go to Settings > Secrets
   - Add a new secret named `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Paste the publish profile from your Azure Web App

## Alternative: Windows Deployment

While Linux is recommended for the reasons outlined above, if you have specific Windows dependencies or preferences, you can deploy to a Windows-based App Service. Key differences include:

1. **Setup**:
   - When creating the App Service, select "Windows" as the operating system
   - Use a web.config file instead of startup.sh for application configuration
   - Install the wfastcgi package: `pip install wfastcgi`

2. **Configuration file** (web.config):
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <configuration>
     <system.webServer>
       <handlers>
         <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" scriptProcessor="D:\Python39\python.exe|D:\Python39\Lib\site-packages\wfastcgi.py" resourceType="Unspecified" requireAccess="Script" />
       </handlers>
       <appSettings>
         <add key="PYTHONPATH" value="D:\home\site\wwwroot" />
         <add key="WSGI_HANDLER" value="app.app" />
         <add key="WSGI_LOG" value="D:\home\LogFiles\wfastcgi.log" />
       </appSettings>
     </system.webServer>
   </configuration>
   ```

3. **Azure CLI commands**:
   - Create App Service Plan: `az appservice plan create --name myAppServicePlan --resource-group myResourceGroup --sku B1`
   - Create Web App: `az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name fugue-in-flask --runtime "python:3.9"`

Consider using Windows deployment only if you have specific Windows dependencies or integration requirements that cannot be accommodated in a Linux environment.

## Monitoring and Troubleshooting

After deployment, monitor your application using Azure's tools:

1. **Application Insights**:
   - Enable Application Insights in your App Service
   - Monitor performance, errors, and user behavior

2. **Log Streaming**:
   - Go to your App Service > Monitoring > Log stream
   - View real-time logs from your application

3. **Troubleshooting Common Issues**:
   - If your app doesn't start, check the logs for errors
   - Verify environment variables are set correctly
   - Ensure database connection is working
   - Check if your `startup.sh` file is executable

## Security Best Practices

1. **Enable HTTPS Only**:
   - In your App Service, go to Settings > TLS/SSL settings
   - Set "HTTPS Only" to On

2. **Store Secrets in Key Vault**:
   - Create an Azure Key Vault
   - Store your secrets there
   - Access them in your application using the Azure SDK

3. **Configure Managed Identity**:
   - Enable system-assigned managed identity for your App Service
   - Use it to access Azure resources securely without credentials

## Scaling Your Application

As your application grows, you may need to scale:

1. **Vertical Scaling**:
   - Increase the resources (CPU, memory) of your App Service Plan

2. **Horizontal Scaling**:
   - Add more instances of your application
   - Configure auto-scaling based on metrics

## Conclusion

By following this guide, you should be able to successfully deploy your "A Fugue In Flask" application to Azure App Service. The Linux deployment approach is recommended for most use cases due to its cost-effectiveness, performance benefits, and better alignment with the Python ecosystem. Remember to always test your deployment in a staging environment before pushing to production.

For more information and advanced deployment scenarios, refer to the [Azure App Service documentation](https://docs.microsoft.com/en-us/azure/app-service/).