/*
Deploys, idempotently via Azure Resource Manager:
  - Model deployment to an Azure AI Foundry account `<modelName>-<environment>-<instance>`

This template deploys a named model to an existing Azure AI Foundry account.
The target Foundry account must already exist; create it with
`azure-foundry/baseline/003-deploy-foundry/main.bicep`.

The model deployment includes configuration for the specified model with
appropriate scaling and capacity settings.

Notes:
  Running this requires Azure CLI and an authenticated subscription context.
  The organization identifier is derived deterministically from the
  subscription ID and used in globally unique resource names. The default
  model is gpt-6.1-terra; override with the modelName parameter as needed.
  
  Follow Azure Cloud Adoption Framework naming and tagging conventions:
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging

Example:
  az stack group create `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name 'stack-demo-foundry-dev-001-model' `
    --template-file './001-deploy-model/main.bicep' `
    --action-on-unmanage deleteResources `
    --deny-settings-mode none `
    --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified

View:
  $foundryName = (az cognitiveservices account list --resource-group 'rg-demo-foundry-dev-001' --query '[0].name' -o tsv)
  Write-Output $foundryName
  az cognitiveservices account deployment list `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name $foundryName

Cleanup:
  az stack group delete `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name 'stack-demo-foundry-dev-001-model' `
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

@allowed([
  'AI21 Labs'
  'Cohere'
  'Core42'
  'DeepSeek'
  'xAI'
  'Meta'
  'Microsoft'
  'Mistral AI'
  'OpenAI'
])
@description('Model format (e.g., OpenAI).')
param modelFormat string = 'OpenAI'

@description('Model identifier or name to deploy (e.g., gpt-6.1-terra, gpt-6-astra, claude-opus-5.5).')
@minLength(1)
@maxLength(64)
param modelName string = 'gpt-6.1-terra'

@description('Model version to deploy.')
@minLength(1)
@maxLength(64)
param modelVersion string = '2026-10-26'

@allowed([
  'GlobalStandard'
  'DataZoneStandard'
  'Standard'
  'GlobalProvisioned'
  'Provisioned'
])
@description('SKU (e.g., GlobalStandard).')
param skuName string = 'GlobalStandard'

@description('Capacity (quota) units for the model deployment. 1 quota unit is 1,000 tokens/minute.')
@minValue(1)
param skuCapacity int = 150

@description('Content filter policy name')
param contentFilterPolicyName string = 'Microsoft.DefaultV2'

@description('Deployment name override. Defaults to <modelName>-<environment>-<instance>.')
@minLength(2)
@maxLength(64)
param deploymentName string = toLower('${replace(modelName, '.', '-')}-${environment}-${instance}')

@description('Azure AI Foundry account name.')
@minLength(2)
@maxLength(64)
param foundryName string = toLower('aif-${purpose}-${environment}-${orgId}-${instance}')

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

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryName
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: deploymentName
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    model: {
      format: modelFormat
      name: modelName
      version: modelVersion
    }
    raiPolicyName: contentFilterPolicyName == null ? 'Microsoft.Nill' : contentFilterPolicyName
  }
  tags: tags
}

output deploymentId string = modelDeployment.id
output deploymentName string = modelDeployment.name
output modelName string = modelName
output foundryName string = foundryName
