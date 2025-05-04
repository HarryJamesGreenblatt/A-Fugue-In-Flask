/*
  main.bicep - Cost-optimized infrastructure for Flask application deployment
  
  This template deploys a foundation for hosting the Flask application with a centralized database architecture.
  The SQL Server is deployed in a separate resource group (db-rg) with the application database.
  
  Key resources:
  - Azure SQL Server - Deployed in db-rg resource group
  - Azure SQL Database - A standalone database for the Flask application
  - Key Vault - For storing secrets and connection strings securely
  - Log Analytics Workspace - For centralized monitoring
*/

// Parameters
@description('Base name for all resources')
param baseName string = 'flask-fugue'

@description('Location for all resources')
param location string = resourceGroup().location

@description('SQL Server administrator login')
param sqlAdminLogin string

@description('SQL Server administrator password')
@secure()
param sqlAdminPassword string

@description('Name of the database for the Flask application')
param databaseName string = 'flaskapp-db'

@description('Resource group name for database resources')
param dbResourceGroupName string = 'db-rg'

@description('SQL Server name - specify if using an existing server')
param sqlServerName string = '${baseName}-sql-${uniqueSuffix}'

@description('Database edition')
@allowed(['Basic', 'Standard', 'Premium', 'GeneralPurpose'])
param databaseEdition string = 'Basic'

@description('Database service objective name or tier')
param databaseServiceObjectiveName string = 'Basic'

// Variables
var uniqueSuffix = uniqueString(resourceGroup().id)
var logAnalyticsName = '${baseName}-logs-${uniqueSuffix}'
var keyVaultName = '${baseName}-kv-${uniqueSuffix}'
var sqlServerFqdn = '${sqlServerName}.database.windows.net'

// Tags for all resources
var tags = {
  Environment: 'Production'
  Project: 'FlaskFugue'
  CreatedBy: 'Bicep'
}

// Resources
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Deploy SQL Server and Database using a module
module sqlServerDeployment 'sql-server.bicep' = {
  name: 'sqlServerDeployment'
  scope: resourceGroup(dbResourceGroupName)
  params: {
    location: location
    tags: tags
    sqlServerName: sqlServerName
    sqlAdminLogin: sqlAdminLogin
    sqlAdminPassword: sqlAdminPassword
    databaseName: databaseName
    databaseEdition: databaseEdition
    databaseServiceObjectiveName: databaseServiceObjectiveName
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.id
  }
}

// Store database connection string in Key Vault
resource connectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  name: '${keyVaultName}/TemplateConnectionString'
  properties: {
    value: 'mssql+pyodbc://${sqlAdminLogin}:${sqlAdminPassword}@${sqlServerFqdn}/${databaseName}?driver=ODBC+Driver+17+for+SQL+Server'
  }
  dependsOn: [
    keyVault
    sqlServerDeployment
  ]
}

// Outputs
output sqlServerFqdn string = sqlServerFqdn
output sqlServerName string = sqlServerName
output databaseName string = databaseName
output keyVaultName string = keyVaultName
output logAnalyticsWorkspaceName string = logAnalyticsName
