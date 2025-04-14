# Deploying A Fugue In Flask to Azure

This guide walks you through deploying your Flask application to Microsoft Azure App Service.

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
4. **Visual Studio Code** (recommended): With the Azure App Service extension

## Preparing Your Application for Production

Before deploying, let's prepare your Flask application for production:

### 1. Create a Production Configuration

Ensure your `config.py` has a production configuration:

```python
class ProductionConfig(Config):
    """Production configuration."""
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    # Use an environment variable for the database URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///prod.db')
    # Ensure a strong secret key for production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'generate-a-strong-secret-key')
```

### 2. Create a Requirements File

Ensure your `requirements.txt` file includes all dependencies. Flask applications on Azure require a production WSGI server like Gunicorn:

```
flask==2.0.1
flask-sqlalchemy==2.5.1
flask-migrate==3.1.0
flask-wtf==1.0.0
flask-login==0.5.0
python-dotenv==0.19.1
gunicorn==20.1.0
psycopg2-binary==2.9.1  # For PostgreSQL support
```

### 3. Add Web Server Configuration

Create a file named `gunicorn.conf.py` in your project root:

```python
# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"
loglevel = "info"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
```

### 4. Create a Startup Command File

Create a file named `startup.sh` in your project root:

```bash
#!/bin/bash

# Apply database migrations
flask db upgrade

# Start Gunicorn server
exec gunicorn --config gunicorn.conf.py "app:create_app()"
```

### 5. Create a Procfile for Linux

If using a Linux-based App Service (recommended), create a file named `Procfile` in your project root:

```
web: gunicorn "app:create_app()" --config gunicorn.conf.py
```

## Deployment Steps

### Option 1: Deploy via Azure Portal

1. **Log in to Azure Portal**:
   Go to [portal.azure.com](https://portal.azure.com)

2. **Create a Resource Group**:
   - Click "Create a resource"
   - Search for "Resource Group" and create it
   - Give it a name like "flask-app-rg"

3. **Create an App Service Plan**:
   - Click "Create a resource"
   - Search for "App Service Plan" and create it
   - Choose the pricing tier (B1 is a good starting point)

4. **Create a Web App**:
   - Click "Create a resource"
   - Search for "Web App" and create it
   - Connect it to your App Service Plan
   - Choose Python 3.9 or later as the runtime stack
   - Choose Linux as the operating system (recommended)

5. **Configure Deployment Source**:
   - In your Web App, go to "Deployment Center"
   - Choose your source (GitHub, Azure Repos, etc.)
   - Configure the repository details
   - Set up continuous deployment if desired

6. **Configure Environment Variables**:
   - In your Web App, go to "Configuration"
   - Add the following application settings:
     - `FLASK_APP`: app.py
     - `FLASK_ENV`: production
     - `SECRET_KEY`: [generate a secure random string]

7. **Deploy Your Application**:
   - If using GitHub, push your changes to trigger deployment
   - If using local Git, push to the Azure remote

### Option 2: Deploy via Azure CLI (Cross-Platform)

1. **Log in to Azure CLI**:
   ```bash
   az login
   ```

2. **Create a Resource Group**:
   ```bash
   az group create --name flask-app-rg --location eastus
   ```

3. **Create an App Service Plan**:
   ```bash
   az appservice plan create --name flask-app-plan --resource-group flask-app-rg --sku B1 --is-linux
   ```

4. **Create a Web App**:
   ```bash
   az webapp create --resource-group flask-app-rg --plan flask-app-plan --name a-fugue-in-flask --runtime "PYTHON|3.9"
   ```

5. **Configure Deployment Source**:
   For GitHub:
   ```bash
   az webapp deployment source config --name a-fugue-in-flask --resource-group flask-app-rg --repo-url https://github.com/yourusername/A-Fugue-In-Flask --branch main
   ```

   For local Git:
   ```bash
   az webapp deployment source config-local-git --name a-fugue-in-flask --resource-group flask-app-rg
   ```

6. **Configure Environment Variables**:
   ```bash
   az webapp config appsettings set --name a-fugue-in-flask --resource-group flask-app-rg --settings FLASK_APP=app.py FLASK_ENV=production SECRET_KEY=your-secret-key
   ```

7. **Deploy Your Application**:
   If using local Git:
   ```bash
   git remote add azure <git-url-from-previous-step>
   git push azure main
   ```

### Option 3: Deploy via PowerShell (Windows)

1. **Install Azure PowerShell Module** (if not already installed):
   ```powershell
   Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force
   ```

2. **Log in to Azure**:
   ```powershell
   Connect-AzAccount
   ```

3. **Create a Resource Group**:
   ```powershell
   New-AzResourceGroup -Name flask-app-rg -Location "East US"
   ```

4. **Create an App Service Plan**:
   ```powershell
   New-AzAppServicePlan -ResourceGroupName flask-app-rg -Name flask-app-plan -Location "East US" -Tier Basic -WorkerSize Small -Linux
   ```

5. **Create a Web App**:
   ```powershell
   New-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask -AppServicePlan flask-app-plan -RuntimeStack "PYTHON|3.9"
   ```

6. **Configure Deployment Source**:
   For GitHub:
   ```powershell
   $Properties = @{
       repoUrl = "https://github.com/yourusername/A-Fugue-In-Flask";
       branch = "main";
       isManualIntegration = "true";
   }
   
   Set-AzResource -ResourceGroupName flask-app-rg -ResourceType Microsoft.Web/sites/sourcecontrols -ResourceName a-fugue-in-flask/web -PropertyObject $Properties -ApiVersion 2015-08-01 -Force
   ```

   For local Git, first get publishing credentials:
   ```powershell
   $publishingCredentials = Invoke-AzResourceAction -ResourceGroupName flask-app-rg -ResourceType Microsoft.Web/sites/config -ResourceName a-fugue-in-flask/publishingcredentials -Action list -ApiVersion 2015-08-01 -Force
   
   $username = $publishingCredentials.Properties.publishingUserName
   $password = $publishingCredentials.Properties.publishingPassword
   
   # The Git remote URL will be:
   # https://$username:$password@a-fugue-in-flask.scm.azurewebsites.net/a-fugue-in-flask.git
   ```

7. **Configure Environment Variables**:
   ```powershell
   $appSettings = @{
       FLASK_APP = "app.py";
       FLASK_ENV = "production";
       SECRET_KEY = "your-secret-key";
   }
   
   Set-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask -AppSettings $appSettings
   ```

8. **Deploy Your Application** (local Git):
   ```powershell
   # Add the Azure remote to your Git repository
   git remote add azure https://$username:$password@a-fugue-in-flask.scm.azurewebsites.net/a-fugue-in-flask.git
   
   # Push to Azure
   git push azure main
   ```

### Option 4: Deploy via Visual Studio Code

1. **Install the Azure App Service extension**

2. **Sign in to Azure**:
   - In VS Code, open the Azure tab
   - Click "Sign in to Azure..."

3. **Create a Web App**:
   - In the Azure tab, find "App Service"
   - Click the "+" icon to create a new Web App
   - Follow the prompts to create a new Web App

4. **Deploy Your Application**:
   - Right-click on your Web App
   - Select "Deploy to Web App..."
   - Choose your project folder
   - Confirm the deployment

## Adding a Database

For production use, it's recommended to use Azure Database for PostgreSQL instead of SQLite:

### Using Azure CLI:

```bash
# Create PostgreSQL server
az postgres server create --resource-group flask-app-rg --name a-fugue-in-flask-db --location eastus --admin-user dbadmin --admin-password "SecurePassword123!" --sku-name GP_Gen5_2

# Create database
az postgres db create --resource-group flask-app-rg --server-name a-fugue-in-flask-db --name flask_app

# Configure firewall rules
az postgres server firewall-rule create --resource-group flask-app-rg --server-name a-fugue-in-flask-db --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0

# Update application settings
az webapp config appsettings set --name a-fugue-in-flask --resource-group flask-app-rg --settings DATABASE_URL="postgresql://dbadmin:SecurePassword123!@a-fugue-in-flask-db.postgres.database.azure.com:5432/flask_app"
```

### Using PowerShell:

```powershell
# Create PostgreSQL server
New-AzPostgreSqlServer -ResourceGroupName flask-app-rg -Name a-fugue-in-flask-db -Location "East US" -AdministratorLogin dbadmin -AdministratorLoginPassword (ConvertTo-SecureString -String "SecurePassword123!" -AsPlainText -Force) -Sku GP_Gen5_2

# Create database (uses Az.PostgreSql module)
New-AzPostgreSqlDatabase -ResourceGroupName flask-app-rg -ServerName a-fugue-in-flask-db -Name flask_app

# Configure firewall rules
New-AzPostgreSqlFirewallRule -ResourceGroupName flask-app-rg -ServerName a-fugue-in-flask-db -Name AllowAzureServices -StartIPAddress 0.0.0.0 -EndIPAddress 0.0.0.0

# Update application settings
$appSettings = @{
    DATABASE_URL = "postgresql://dbadmin:SecurePassword123!@a-fugue-in-flask-db.postgres.database.azure.com:5432/flask_app"
}

Set-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask -AppSettings $appSettings
```

## Setting up CI/CD with GitHub Actions

To automate deployments, create a file at `.github/workflows/deploy-to-azure.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

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
        # Add test commands here
        
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'a-fugue-in-flask'
        slot-name: 'production'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

To set up the secret:
1. In the Azure Portal, go to your Web App
2. Navigate to "Get publish profile" and download the file
3. In your GitHub repository, go to Settings > Secrets
4. Create a new secret named `AZURE_WEBAPP_PUBLISH_PROFILE` with the contents of the file

## Monitoring Your Application

### Using Azure CLI:

```bash
# Create Application Insights
az monitor app-insights component create --app a-fugue-in-flask-insights --location eastus --resource-group flask-app-rg --application-type web

# Add connection string to Web App
az webapp config appsettings set --name a-fugue-in-flask --resource-group flask-app-rg --settings APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."

# View logs
az webapp log tail --name a-fugue-in-flask --resource-group flask-app-rg
```

### Using PowerShell:

```powershell
# Create Application Insights
New-AzApplicationInsights -ResourceGroupName flask-app-rg -Name a-fugue-in-flask-insights -Location "East US"

# Get the instrumentation key
$instrumentationKey = (Get-AzApplicationInsights -ResourceGroupName flask-app-rg -Name a-fugue-in-flask-insights).InstrumentationKey

# Add connection string to Web App
$appSettings = @{
    APPLICATIONINSIGHTS_CONNECTION_STRING = "InstrumentationKey=$instrumentationKey"
}

Set-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask -AppSettings $appSettings

# View logs (PowerShell version of log streaming)
Get-AzWebAppLogStream -ResourceGroupName flask-app-rg -Name a-fugue-in-flask
```

## Custom Domain and HTTPS

### Using Azure CLI:

```bash
# Add custom domain
az webapp config hostname add --webapp-name a-fugue-in-flask --resource-group flask-app-rg --hostname www.yourdomainname.com

# Add SSL certificate
az webapp config ssl bind --certificate-thumbprint THUMBPRINT --ssl-type SNI --name a-fugue-in-flask --resource-group flask-app-rg

# Enable HTTPS only
az webapp update --name a-fugue-in-flask --resource-group flask-app-rg --https-only true
```

### Using PowerShell:

```powershell
# Add custom domain
New-AzWebAppHostNameBinding -ResourceGroupName flask-app-rg -WebAppName a-fugue-in-flask -Name www.yourdomainname.com -Hostname www.yourdomainname.com

# Add SSL certificate (requires certificate to be uploaded to App Service first)
New-AzWebAppSSLBinding -ResourceGroupName flask-app-rg -WebAppName a-fugue-in-flask -Name www.yourdomainname.com -Thumbprint THUMBPRINT -SslState SniEnabled

# Enable HTTPS only
Set-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask -HttpsOnly $true
```

## Scaling Your Application

### Using Azure CLI:

```bash
# Manual scaling
az appservice plan update --name flask-app-plan --resource-group flask-app-rg --number-of-workers 3

# Auto scaling
az monitor autoscale create --resource-group flask-app-rg --resource a-fugue-in-flask --resource-type Microsoft.Web/sites --name autoscaleconfig --min-count 1 --max-count 5 --count 1

# Add auto scale rule
az monitor autoscale rule create --resource-group flask-app-rg --autoscale-name autoscaleconfig --scale out 1 --condition "CpuPercentage > 75 avg 5m"
```

### Using PowerShell:

```powershell
# Manual scaling
Set-AzAppServicePlan -ResourceGroupName flask-app-rg -Name flask-app-plan -NumberofWorkers 3

# Auto scaling (requires more complex setup in PowerShell)
# First create an autoscale profile
$targetResourceId = (Get-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask).Id

$scaleRule = New-AzAutoscaleRule -MetricName "CpuPercentage" -MetricResourceId $targetResourceId -Operator GreaterThan -MetricStatistic Average -Threshold 75 -TimeGrain 00:01:00 -TimeWindow 00:05:00 -ScaleActionCooldown 00:05:00 -ScaleActionDirection Increase -ScaleActionScaleType ChangeCount -ScaleActionValue 1

$profile = New-AzAutoscaleProfile -DefaultCapacity 1 -MaximumCapacity 5 -MinimumCapacity 1 -Rule $scaleRule -Name "autoscaleprofile"

Add-AzAutoscaleSetting -Location "East US" -Name "autoscalesetting" -ResourceGroup flask-app-rg -TargetResourceId $targetResourceId -AutoscaleProfile $profile
```

## Troubleshooting

### Using Azure CLI:

```bash
# View application logs
az webapp log tail --name a-fugue-in-flask --resource-group flask-app-rg

# Check app settings
az webapp config appsettings list --name a-fugue-in-flask --resource-group flask-app-rg

# Restart the web app
az webapp restart --name a-fugue-in-flask --resource-group flask-app-rg
```

### Using PowerShell:

```powershell
# View application logs
Get-AzWebAppLogStream -ResourceGroupName flask-app-rg -Name a-fugue-in-flask

# Check app settings
Get-AzWebAppSetting -ResourceGroupName flask-app-rg -Name a-fugue-in-flask

# Restart the web app
Restart-AzWebApp -ResourceGroupName flask-app-rg -Name a-fugue-in-flask
```

## Cost Management

To monitor and control costs:

### Using Azure CLI:

```bash
# Set up budget alerts
az consumption budget create --name "flask-app-budget" --amount 50 --time-grain monthly --resource-group flask-app-rg
```

### Using PowerShell:

```powershell
# Set up budget alerts (requires Az.Consumption module)
New-AzConsumptionBudget -Name "flask-app-budget" -Amount 50 -Category Cost -TimeGrain Monthly -ResourceGroupName flask-app-rg -StartDate (Get-Date) -EndDate (Get-Date).AddYears(1)
```

## Next Steps

- **Set up a staging slot** for blue-green deployments
- **Implement Azure Front Door** for global distribution
- **Add Azure Cache for Redis** for session management
- **Integrate with Azure Active Directory** for authentication