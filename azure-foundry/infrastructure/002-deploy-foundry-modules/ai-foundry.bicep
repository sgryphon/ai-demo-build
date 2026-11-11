/*
Creates the current Azure AI Foundry account and its first project.
*/

@description('Azure AI Foundry account name.')
@minLength(2)
@maxLength(64)
param foundryName string

@description('Azure AI Foundry project name.')
@minLength(2)
@maxLength(64)
param projectName string

@description('Application Insights resource name to connect to the Foundry account and project.')
param applicationInsightsName string

@description('Resource group containing the Application Insights resource.')
param applicationInsightsResourceGroupName string

@description('Tags applied to all resources that support tags.')
param tags object

var location = resourceGroup().location

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
  scope: resourceGroup(applicationInsightsResourceGroupName)
}

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: foundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  tags: tags
  properties: {
    allowProjectManagement: true
    customSubDomainName: foundryName
    disableLocalAuth: false
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: projectName
  parent: foundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  tags: tags
  properties: {}
}

resource foundryAppInsightsConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: '${foundry.name}-appinsights'
  parent: foundry
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: appInsights.properties.ConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsights.id
    }
  }
}

resource projectAppInsightsConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  name: applicationInsightsName
  parent: project
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: appInsights.properties.ConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsights.id
    }
  }
}

output foundryId string = foundry.id
output foundryName string = foundry.name
output projectId string = project.id
output projectName string = project.name
output projectPrincipalId string = project.identity.principalId
