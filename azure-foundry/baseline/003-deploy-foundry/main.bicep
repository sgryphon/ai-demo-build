/*
Creates, idempotently via Azure Resource Manager:
  - Azure AI Foundry account `aif-demo-dev-<orgId>-001`
  - Foundry project `proj-demo-dev-001`

This uses the current `Microsoft.CognitiveServices` account/project model,
not the legacy Azure Machine Learning Hub/Project model. The target resource
group must already exist; create it with `001-init-foundry-rg/main.bicep` or use a
corporate-provided resource group.

The Application Insights resource should be deployed via `002-deploy-shared`
before deploying this workload stack.

Notes:
  Running this requires Azure CLI and an authenticated subscription context.
  The organization identifier is derived deterministically from the
  subscription ID. The template creates no model deployments.
  Follow Azure Cloud Adoption Framework naming and tagging conventions:
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging

Example:
  az stack group create `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name 'stack-demo-foundry-dev-001-workload' `
    --template-file './azure-foundry/baseline/003-deploy-foundry/main.bicep' `
    --action-on-unmanage deleteResources `
    --deny-settings-mode none `
    --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
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
param projectName string = toLower('proj-${purpose}-${environment}-${instance}')

@description('Application Insights resource name to connect to the Foundry account and project.')
param applicationInsightsName string = toLower('appi-${purpose}-${environment}-${orgId}-${instance}')

@description('Resource group containing the Application Insights resource.')
param applicationInsightsResourceGroupName string = resourceGroup().name

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

module aiFoundry './ai-foundry.bicep' = {
  name: 'deploy-ai-foundry'
  params: {
    foundryName: foundryName
    projectName: projectName
    applicationInsightsName: applicationInsightsName
    applicationInsightsResourceGroupName: applicationInsightsResourceGroupName
    tags: tags
  }
}

output foundryId string = aiFoundry.outputs.foundryId
output foundryName string = aiFoundry.outputs.foundryName
output projectId string = aiFoundry.outputs.projectId
output projectName string = aiFoundry.outputs.projectName
