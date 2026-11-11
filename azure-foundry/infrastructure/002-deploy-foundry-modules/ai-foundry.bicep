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

@description('Tags applied to all resources that support tags.')
param tags object

var location = resourceGroup().location

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

output foundryId string = foundry.id
output foundryName string = foundry.name
output projectId string = project.id
output projectName string = project.name
