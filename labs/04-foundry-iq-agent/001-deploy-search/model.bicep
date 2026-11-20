/*
Deploys the embedding model used by the knowledge source to vectorize documents.
*/

@description('Existing Azure AI Foundry account name.')
param foundryName string

@description('Embedding model deployment name.')
param deploymentName string

@description('Embedding model name.')
param modelName string

@description('Embedding model version.')
param modelVersion string

@description('Deployment SKU.')
param skuName string

@description('Capacity (quota) units; 1 unit is 1,000 tokens/minute.')
param skuCapacity int

@description('Tags applied to all resources that support tags.')
param tags object

resource foundry 'Microsoft.CognitiveServices/accounts@2026-03-01' existing = {
  name: foundryName
}

resource embedding 'Microsoft.CognitiveServices/accounts/deployments@2026-03-01' = {
  parent: foundry
  name: deploymentName
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  tags: tags
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

output deploymentName string = embedding.name
