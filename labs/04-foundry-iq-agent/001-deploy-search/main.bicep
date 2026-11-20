/*
Deploys, idempotently via Azure Resource Manager:
  - Azure AI Search service `srch-<purpose>-<environment>-<orgId>-<instance>` (Basic, semantic ranker)
  - Storage account `st<purpose><environment><orgId><instance>` with container `contosoproducts`
  - Embedding model deployment `text-embedding-3-small-<environment>-<instance>` on the Foundry account
  - Foundry project connections to Search: RemoteTool (knowledge base MCP) and CognitiveSearch

These are the Azure resources behind the lab's "Connect to Foundry IQ" portal
steps. The knowledge source, knowledge base and agent tool are data-plane
objects created afterwards by the Python scripts in this lab.

The Foundry account and project must already exist; create them with
`azure-foundry/baseline/003-deploy-foundry/main.bicep`.

Notes:
  Demo shortcut: this uses API keys (search admin key, storage connection
  string, Foundry key) so that no role assignments are needed; Contributor on
  the resource group is enough. Keyless access (managed identities + RBAC, with
  local auth disabled) is preferred for production.

  No secrets are output. Retrieve them with the commands below after deployment.

  The knowledge base chat model (query planning) must be a model supported by
  Foundry IQ (e.g. gpt-5 family, gpt-6-astra). Deploy one with
  `labs/02-custom-function-agent/001-deploy-model/main.bicep` if needed.

  Follow Azure Cloud Adoption Framework naming and tagging conventions:
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging

Example:
  az stack group create `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name 'stack-demo-foundry-dev-001-search' `
    --template-file './001-deploy-search/main.bicep' `
    --action-on-unmanage deleteResources `
    --deny-settings-mode none `
    --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified

Retrieve values for .env (prints KEY=value lines to paste):
  $rg = 'rg-demo-foundry-dev-001'
  $searchName = (az search service list --resource-group $rg --query '[0].name' -o tsv)
  $storageName = (az storage account list --resource-group $rg --query "[?starts_with(name, 'st')].name | [0]" -o tsv)
  $foundryName = (az cognitiveservices account list --resource-group $rg --query '[0].name' -o tsv)
  "SEARCH_ENDPOINT=https://$searchName.search.windows.net"
  "SEARCH_API_KEY=$(az search admin-key show --resource-group $rg --service-name $searchName --query primaryKey -o tsv)"
  "STORAGE_CONNECTION_STRING=$(az storage account show-connection-string --resource-group $rg --name $storageName --query connectionString -o tsv)"
  "FOUNDRY_OPENAI_ENDPOINT=https://$foundryName.openai.azure.com"
  "FOUNDRY_API_KEY=$(az cognitiveservices account keys list --resource-group $rg --name $foundryName --query key1 -o tsv)"

View:
  az search service list --resource-group 'rg-demo-foundry-dev-001' -o table
  az storage account list --resource-group 'rg-demo-foundry-dev-001' -o table
  az stack group show --resource-group 'rg-demo-foundry-dev-001' --name 'stack-demo-foundry-dev-001-search' --query outputs

Cleanup:
  az stack group delete `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name 'stack-demo-foundry-dev-001-search' `
    --action-on-unmanage deleteResources `
    --yes
*/

@description('Workload or business-unit identifier. Use a short name-safe value.')
@minLength(1)
@maxLength(12)
param purpose string = 'Demo'

@description('Environment tag and name component.')
@minLength(1)
@maxLength(8)
param environment string = 'Dev'

@description('Instance suffix for resource names.')
@minLength(1)
@maxLength(8)
param instance string = '001'

@description('Organization identifier for globally unique names. Defaults deterministically from the subscription ID.')
@minLength(1)
@maxLength(6)
param orgId string = substring(uniqueString(subscription().subscriptionId), 0, 6)

@description('Existing Azure AI Foundry account name.')
@minLength(2)
@maxLength(64)
param foundryName string = toLower('aif-${purpose}-${environment}-${orgId}-${instance}')

@description('Existing Foundry project name.')
@minLength(2)
@maxLength(64)
param projectName string = toLower('proj-${purpose}-${environment}-${instance}')

@description('Azure AI Search service name (globally unique).')
@minLength(2)
@maxLength(60)
param searchName string = toLower('srch-${purpose}-${environment}-${orgId}-${instance}')

@allowed([
  'basic'
  'standard'
])
@description('Azure AI Search SKU.')
param searchSku string = 'basic'

@description('Storage account name (globally unique, 3-24 lowercase letters and digits).')
@minLength(3)
@maxLength(24)
#disable-next-line BCP334 // Always at least 'st' + purpose + environment + orgId + instance, so >= 3 characters.
param storageName string = take(toLower(replace('st${purpose}${environment}${orgId}${instance}', '-', '')), 24)

@description('Blob container for the knowledge source documents.')
param containerName string = 'contosoproducts'

@description('Knowledge base name; must match KNOWLEDGE_BASE_NAME used by the Python scripts.')
param knowledgeBaseName string = 'kb-contosoproducts'

@description('Search data-plane API version for the knowledge base MCP endpoint.')
param searchMcpApiVersion string = '2026-11-01-preview'

@description('Name of the RemoteTool (MCP) project connection.')
@minLength(3)
@maxLength(33)
param mcpConnectionName string = toLower('${knowledgeBaseName}-mcp')

@description('Embedding model name.')
param embeddingModelName string = 'text-embedding-3-small'

@description('Embedding model version.')
param embeddingModelVersion string = '1'

@description('Embedding model deployment SKU.')
param embeddingSkuName string = 'GlobalStandard'

@description('Embedding capacity (quota) units; 1 unit is 1,000 tokens/minute.')
@minValue(1)
param embeddingSkuCapacity int = 50

@description('Embedding deployment name.')
@minLength(2)
@maxLength(64)
param embeddingDeploymentName string = toLower('${embeddingModelName}-${environment}-${instance}')

@description('Confidentiality classification tag. Align this value with the taxonomy used by your organization.')
param confidentiality string = 'Unclassified'

@description('Criticality tag.')
param criticality string = 'low'

var tags = {
  env: toLower(environment)
  region: resourceGroup().location
  criticality: toLower(criticality)
  businessunit: toLower(purpose)
  confidentiality: toLower(confidentiality)
}

module search './search.bicep' = {
  name: 'deploy-search'
  params: {
    searchName: searchName
    skuName: searchSku
    tags: tags
  }
}

module storage './storage.bicep' = {
  name: 'deploy-storage'
  params: {
    storageName: storageName
    containerName: containerName
    tags: tags
  }
}

module embedding './model.bicep' = {
  name: 'deploy-embedding-model'
  params: {
    foundryName: foundryName
    deploymentName: embeddingDeploymentName
    modelName: embeddingModelName
    modelVersion: embeddingModelVersion
    skuName: embeddingSkuName
    skuCapacity: embeddingSkuCapacity
    tags: tags
  }
}

module connections './connections.bicep' = {
  name: 'deploy-search-connections'
  params: {
    foundryName: foundryName
    projectName: projectName
    searchName: search.outputs.searchName
    knowledgeBaseName: knowledgeBaseName
    searchMcpApiVersion: searchMcpApiVersion
    mcpConnectionName: mcpConnectionName
  }
}

output searchName string = search.outputs.searchName
output searchEndpoint string = search.outputs.searchEndpoint
output storageName string = storage.outputs.storageName
output containerName string = storage.outputs.containerName
output embeddingDeploymentName string = embedding.outputs.deploymentName
output knowledgeBaseName string = knowledgeBaseName
output mcpConnectionName string = connections.outputs.mcpConnectionName
