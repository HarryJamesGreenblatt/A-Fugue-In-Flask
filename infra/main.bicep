/*
  main.bicep - Cost-optimized infrastructure for multi-template application deployment
  
  This template deploys a foundation for hosting multiple template applications (Flask, React, Blazor, etc.)
  Each template gets its own database within a small cost-efficient Azure SQL Elastic Pool.
  
  Key resources:
  - Azure SQL Server - Single server to host all template databases
  - Small Azure SQL Elastic Pool - Minimum DTU capacity for template apps (~$45-50/month total)
  - Key Vault - For storing secrets and connection strings securely
  - Log Analytics Workspace - For centralized monitoring
*/

// Parameters
@description('Base name for all resources')
param baseName string = 'templates'

@description('Location for all resources')
param location string = resourceGroup().location

@description('SQL Server administrator login')
param sqlAdminLogin string

@description('SQL Server administrator password')
@secure()
param sqlAdminPassword string

@description('List of template types to create databases for')
param templateTypes array = ['flask', 'react', 'blazor']

// Small Elastic Pool configuration
@description('Elastic pool DTU capacity - minimum viable size for template applications')
param elasticPoolDtuCapacity int = 20  // Smallest Standard tier size that allows multiple dbs

@description('Elastic pool per-database min DTU')
param databaseDtuMin int = 0  // Can go down to 0 when unused to save resources

@description('Elastic pool per-database max DTU')
param databaseDtuMax int = 10  // Allow burst capacity for each template when needed

@description('Elastic pool edition - using Standard for best cost/feature balance')
@allowed(['Basic', 'Standard', 'Premium'])
param elasticPoolEdition string = 'Standard'

@description('Maximum storage size in GB for the elastic pool')
param storageLimitGB int = 10  // Standard pool with 20 DTUs includes 10GB storage

// Variables
var uniqueSuffix = uniqueString(resourceGroup().id)
var sqlServerName = '${baseName}-sql-${uniqueSuffix}'
var elasticPoolName = '${baseName}-pool'
var logAnalyticsName = '${baseName}-logs-${uniqueSuffix}'
var keyVaultName = '${baseName}-kv-${uniqueSuffix}'

// Tags for all resources
var tags = {
  Environment: 'Templates'
  Project: 'AppTemplates'
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

// Deploy SQL Server and Elastic Pool using a module
module elasticPoolDeployment 'elastic-pool.bicep' = {
  name: 'elasticPoolDeployment'
  params: {
    location: location
    tags: tags
    sqlServerName: sqlServerName
    elasticPoolName: elasticPoolName
    sqlAdminLogin: sqlAdminLogin
    sqlAdminPassword: sqlAdminPassword
    templateTypes: templateTypes
    elasticPoolEdition: elasticPoolEdition
    elasticPoolDtuCapacity: elasticPoolDtuCapacity
    databaseDtuMin: databaseDtuMin
    databaseDtuMax: databaseDtuMax
    storageLimitGB: storageLimitGB
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.id
    keyVaultName: keyVaultName
  }
}

// Outputs
output sqlServerFqdn string = elasticPoolDeployment.outputs.sqlServerFqdn
output sqlServerName string = sqlServerName
output elasticPoolName string = elasticPoolName
output keyVaultName string = keyVaultName
output logAnalyticsWorkspaceName string = logAnalyticsName
output databaseNames array = elasticPoolDeployment.outputs.databaseNames
