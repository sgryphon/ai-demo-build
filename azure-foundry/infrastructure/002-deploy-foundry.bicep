/*
Creates, idempotently via Azure Resource Manager:
  - Azure AI Foundry account `aif-demo-dev-<orgId>-001`
  - Foundry project `demo-dev-001-proj`

This uses the current `Microsoft.CognitiveServices` account/project model,
not the legacy Azure Machine Learning Hub/Project model. The target resource
group must already exist; create it with `001-init-foundry-rg.bicep` or use a
corporate-provided resource group.

Notes:
  Running this requires Azure CLI and an authenticated subscription context.
  The organization identifier is derived deterministically from the
  subscription ID. The template creates no model deployments.
  Follow Azure Cloud Adoption Framework naming and tagging conventions:
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging

Example:
  az deployment group create `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name "deploy-foundry-$(Get-Date -Format 'yyyyMMddHHmmss')" `
    --template-file './azure-foundry/infrastructure/002-deploy-foundry.bicep'
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

@description('Override the default Foundry account name.')
@minLength(2)
@maxLength(64)
param foundryName string = toLower('aif-${purpose}-${environment}-${orgId}-${instance}')

@description('Override the default Foundry project name.')
@minLength(2)
@maxLength(64)
param projectName string = toLower('${purpose}-${environment}-${instance}-proj')

@description('Data classification tag.')
param dataClassification string = 'Non-business'

@description('Criticality tag.')
param criticality string = 'Low'

var tags = {
  DataClassification: dataClassification
  Criticality: criticality
  BusinessUnit: purpose
  Env: environment
}

module aiFoundry './002-deploy-foundry-modules/ai-foundry.bicep' = {
  name: 'deploy-ai-foundry'
  params: {
    foundryName: foundryName
    projectName: projectName
    tags: tags
  }
}

output foundryId string = aiFoundry.outputs.foundryId
output foundryName string = aiFoundry.outputs.foundryName
output projectId string = aiFoundry.outputs.projectId
output projectName string = aiFoundry.outputs.projectName
