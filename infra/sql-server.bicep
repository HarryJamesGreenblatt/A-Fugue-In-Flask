/*
  sql-server.bicep - SQL Server and database deployment for centralized architecture
  
  This module deploys:
  - A SQL Server instance in the db-rg resource group
  - A standalone database for the Flask application
  - Firewall rules to allow Azure services
  - Auditing and monitoring configurations
*/

// Parameters
@description('Location for all resources')
param location string

@description('Tags to apply to all resources')
param tags object

@description('SQL Server name')
param sqlServerName string

@description('SQL Server administrator login')
param sqlAdminLogin string

@description('SQL Server administrator password')
@secure()
param sqlAdminPassword string

@description('Name of the database to create')
param databaseName string

@description('Database edition')
@allowed(['Basic', 'Standard', 'Premium', 'GeneralPurpose'])
param databaseEdition string

@description('Service objective name or tier')
param databaseServiceObjectiveName string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

// SQL Server resource
resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: sqlServerName
  location: location
  tags: tags
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'  // Can be changed to 'Disabled' for private endpoint access only
  }
}

// Allow Azure services and resources to access this server
resource firewallRule 'Microsoft.Sql/servers/firewallRules@2022-05-01-preview' = {
  parent: sqlServer
  name: 'AllowAllAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// SQL Database resource
resource database 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: location
  tags: tags
  sku: {
    name: databaseServiceObjectiveName
    tier: databaseEdition
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 1073741824  // 1GB for Basic tier
    zoneRedundant: false
    readScale: 'Disabled'
    requestedBackupStorageRedundancy: 'Local'  // Options: Local, Zone, Geo
  }
}

// Enable SQL Server auditing
resource serverAudit 'Microsoft.Sql/servers/auditingSettings@2022-05-01-preview' = {
  parent: sqlServer
  name: 'default'
  properties: {
    state: 'Enabled'
    isAzureMonitorTargetEnabled: true
    storageAccountAccessKey: null  // Not using storage account
    storageEndpoint: null  // Not using storage account
  }
}

// Enable database diagnostics
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${databaseName}-diagnostics'
  scope: database
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'SQLInsights'
        enabled: true
      }
      {
        category: 'AutomaticTuning'
        enabled: true
      }
      {
        category: 'QueryStoreRuntimeStatistics'
        enabled: true
      }
      {
        category: 'QueryStoreWaitStatistics'
        enabled: true
      }
      {
        category: 'Errors'
        enabled: true
      }
      {
        category: 'DatabaseWaitStatistics'
        enabled: true
      }
      {
        category: 'Timeouts'
        enabled: true
      }
      {
        category: 'Blocks'
        enabled: true
      }
      {
        category: 'Deadlocks'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'Basic'
        enabled: true
      }
      {
        category: 'InstanceAndAppAdvanced'
        enabled: true
      }
      {
        category: 'WorkloadManagement'
        enabled: true
      }
    ]
  }
}

// Outputs
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseName string = database.name
