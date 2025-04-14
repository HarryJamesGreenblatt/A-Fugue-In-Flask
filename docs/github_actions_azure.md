# GitHub Actions CI/CD for Azure

This document provides a comprehensive guide for setting up continuous integration and deployment (CI/CD) using GitHub Actions to deploy your Flask application to Azure App Service.

## Benefits of GitHub Actions for Azure Deployment

- **Seamless Integration**: Direct integration between your GitHub repository and Azure
- **Automated Workflows**: Automatic deployments whenever code is pushed to specified branches
- **Testing Integration**: Run tests automatically before deployment
- **Security**: Secure handling of deployment credentials
- **Visibility**: Clear logs and status checks for each deployment

## Workflow Setup

GitHub Actions uses YAML files to define workflows. These files reside in the `.github/workflows` directory of your repository.

### Basic Azure Deployment Workflow

Here's our basic workflow file for deploying to Azure App Service:

```yaml
name: Deploy Flask app to Azure App Service

on:
  push:
    branches:
      - main
      - master  # Including both common branch names
  workflow_dispatch:  # Allows manual triggering

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

### Enhanced Workflow with Testing

For more comprehensive CI/CD, add testing before deployment:

```yaml
name: Test and Deploy Flask app to Azure

on:
  push:
    branches:
      - main
      - master
  pull_request:
    branches:
      - main
      - master
  workflow_dispatch:

jobs:
  test:
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
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=app tests/
    
  deploy:
    needs: test
    if: github.event_name != 'pull_request'
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

## Setting Up Deployment Credentials

GitHub Actions needs credentials to deploy to Azure. There are two main approaches:

### Approach 1: Using Publish Profile (Simpler)

1. **Get the publish profile**:
   ```bash
   az webapp deployment list-publishing-profiles --name flask-fugue-app --resource-group flaskapp-rg --xml > azure-publish-profile.xml
   ```

2. **Add as a GitHub Secret**:
   - Using GitHub CLI:
   ```bash
   gh secret set AZURE_WEBAPP_PUBLISH_PROFILE --body "$(cat azure-publish-profile.xml)"
   ```
   
   - Or through the web interface:
   ```
   Go to your GitHub repository → Settings → Secrets → Actions
   Click "New repository secret"
   Name: AZURE_WEBAPP_PUBLISH_PROFILE
   Value: *contents of the azure-publish-profile.xml file*
   ```

### Approach 2: Using Service Principal (More secure for production)

1. **Create Azure service principal**:
   ```bash
   az ad sp create-for-rbac --name "flask-fugue-github-actions" --role contributor \
     --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/flaskapp-rg --sdk-auth > azure_credentials.json
   ```

2. **Add credentials to GitHub Secrets**:
   - Using GitHub CLI:
   ```bash
   gh secret set AZURE_CREDENTIALS --body "$(cat azure_credentials.json)"
   ```
   
   - Or through the web interface:
   ```
   Go to your GitHub repository → Settings → Secrets → Actions
   Click "New repository secret"
   Name: AZURE_CREDENTIALS
   Value: *contents of the azure_credentials.json file*
   ```

3. **Update workflow to include Azure login**:
   ```yaml
   - name: Azure Login
     uses: azure/login@v1
     with:
       creds: ${{ secrets.AZURE_CREDENTIALS }}
   ```

4. **Delete the local credentials file for security**:
   ```bash
   rm azure_credentials.json
   ```

## How the Deployment Works

1. When code is pushed to the `main` or `master` branch, GitHub Actions automatically:
   - Checks out your code
   - Sets up Python environment
   - Installs dependencies
   - Runs tests (if configured)
   - Deploys to Azure App Service

2. The deployment process:
   - Packages your application code
   - Authenticates with Azure using the publish profile
   - Uploads the package to your App Service
   - Restarts the application

## Advanced Configurations

### Environment-Specific Deployments

Deploy to different environments based on branch:

```yaml
name: Multi-Environment Deployment

on:
  push:
    branches: [dev, staging, main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    # ... checkout and setup steps ...
    
    - name: Set environment variables
      run: |
        if [[ $GITHUB_REF == 'refs/heads/dev' ]]; then
          echo "AZURE_WEBAPP_NAME=flask-fugue-app-dev" >> $GITHUB_ENV
          echo "AZURE_PUBLISH_PROFILE=${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_DEV }}" >> $GITHUB_ENV
        elif [[ $GITHUB_REF == 'refs/heads/staging' ]]; then
          echo "AZURE_WEBAPP_NAME=flask-fugue-app-staging" >> $GITHUB_ENV
          echo "AZURE_PUBLISH_PROFILE=${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_STAGING }}" >> $GITHUB_ENV
        else
          echo "AZURE_WEBAPP_NAME=flask-fugue-app" >> $GITHUB_ENV
          echo "AZURE_PUBLISH_PROFILE=${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}" >> $GITHUB_ENV
        fi
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        publish-profile: ${{ env.AZURE_PUBLISH_PROFILE }}
        package: .
```

### Database Migrations

Add database migration steps before deployment:

```yaml
- name: Apply database migrations
  run: |
    pip install flask-migrate
    export FLASK_APP=app.py
    export DATABASE_URI=${{ secrets.DATABASE_URI }}
    flask db upgrade
```

## Best Practices

1. **Branch Protection Rules**: Require passing CI checks before merging to production branches
2. **Separate Test/Build/Deploy Stages**: Make workflow steps modular and independent
3. **Environment Secrets**: Use different secrets for different deployment environments
4. **Notification Setup**: Configure notifications for failed/successful deployments
5. **Artifact Preservation**: Store build artifacts for debugging failed deployments
6. **Deployment Approval**: For production deployments, consider requiring manual approval

## Troubleshooting

### Common Issues:

1. **Authentication Failures**:
   - "No credentials found" error: Add Azure login step to your workflow as described above
   - Verify the publish profile or credentials are correctly set
   - Ensure the service principal has sufficient permissions for the resource group

2. **Dependency Installation Failures**:
   - Check if all dependencies in `requirements.txt` are installable
   - Some packages might require system-level dependencies
   - Some packages might have platform-specific dependencies not available in GitHub Actions
   - Consider using a custom startup script in Azure that installs dependencies at runtime:
     ```bash
     #!/bin/bash
     pip install -r requirements.txt
     # Start your application
     ```

3. **Application Starts but Shows Errors**:
   - In Azure App Service, set a custom startup script:
     ```bash
     az webapp config set --name flask-fugue-app --resource-group flaskapp-rg --startup-file "startup_azure.sh"
     ```
   - View application logs to diagnose:
     ```bash
     az webapp log tail --name flask-fugue-app --resource-group flaskapp-rg
     ```

### Debugging Workflows:

1. Enable detailed logging by adding the following to your workflow:
   ```yaml
   env:
     ACTIONS_STEP_DEBUG: true
   ```

2. Use the GitHub Actions logs tab to examine detailed output from each step

## Further Reading

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Web App Deployment Action](https://github.com/Azure/webapps-deploy)
- [GitHub Actions for Azure](https://docs.microsoft.com/en-us/azure/developer/github/)