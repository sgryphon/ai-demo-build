/*
Creates the Azure AI Search service used by Foundry IQ knowledge bases.
*/

@description('Azure AI Search service name.')
@minLength(2)
@maxLength(60)
param searchName string

@allowed([
  'basic'
  'standard'
])
@description('Search SKU. Free is not used because it is limited to one per subscription and lacks managed identity.')
param skuName string

@description('Tags applied to all resources that support tags.')
param tags object

// Demo shortcut: API keys are enabled ("Both", as in the lab) because the
// deployer may not be able to create role assignments. For production, prefer
// keyless access: set disableLocalAuth: true, remove authOptions, and grant
// RBAC roles to the project and search managed identities.
resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: searchName
  location: resourceGroup().location
  sku: {
    name: skuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  tags: tags
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'Default'
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    semanticSearch: 'free'
  }
}

output searchId string = search.id
output searchName string = search.name
output searchEndpoint string = 'https://${search.name}.search.windows.net'
