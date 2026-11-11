/*
Creates workspace-based Application Insights and its Log Analytics workspace.
These are demo observability resources. The Foundry workload deployment
connects the Application Insights resource to the account and project.
*/

@description('Workload or business-unit identifier.')
param purpose string

@description('Environment name component.')
param environment string

@description('Instance suffix for resource names.')
param instance string

@description('Organization identifier derived deterministically from the subscription ID.')
param orgId string

@description('Azure region for the monitor resources.')
param region string

@description('Tags applied to all resources that support tags.')
param tags object

var logAnalyticsWorkspaceName = toLower('log-${purpose}-${environment}-${orgId}-${instance}')
var applicationInsightsName = toLower('appi-${purpose}-${environment}-${orgId}-${instance}')

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: region
  tags: tags
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: region
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output applicationInsightsId string = applicationInsights.id
output applicationInsightsName string = applicationInsights.name
