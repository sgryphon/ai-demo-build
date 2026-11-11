/*
Creates, idempotently via Azure Resource Manager:
  - Resource group `rg-demo-foundry-dev-001`
  - Log Analytics workspace `log-demo-dev-<orgId>-001`
  - Workspace-based Application Insights `appi-demo-dev-<orgId>-001`

The organization identifier is derived deterministically from the subscription
ID and used in globally unique resource names. The resource group is created at
subscription scope; Azure Monitor resources are deployed into that group.

Notes:
  Running this requires Azure CLI and an authenticated subscription context.
  Follow Azure Cloud Adoption Framework naming and tagging conventions:
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging

Example:
  az stack sub create `
    --name 'stack-demo-foundry-dev-001-init' `
    --location 'australiaeast' `
    --template-file './azure-foundry/infrastructure/001-init-foundry-rg/main.bicep' `
    --action-on-unmanage detachAll `
    --deny-settings-mode none `
    --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
*/

targetScope = 'subscription'

@description('Workload or business-unit identifier. Use a short name-safe value.')
@minLength(1)
@maxLength(12)
param purpose string = 'Demo'

@description('Environment tag and name component.')
@minLength(1)
@maxLength(8)
param environment string = 'Dev'

@description('Azure region for the resource group and Azure Monitor resources.')
param region string = 'australiaeast'

@description('Instance suffix for resource names.')
@minLength(1)
@maxLength(8)
param instance string = '001'

@description('Organization identifier for globally unique names. Defaults deterministically from the subscription ID.')
@minLength(1)
@maxLength(6)
param orgId string = substring(uniqueString(subscription().subscriptionId), 0, 6)

@description('Override the default resource group name when required.')
param resourceGroupName string = toLower('rg-${purpose}-foundry-${environment}-${instance}')

@description('Confidentiality classification tag. Align this value with the taxonomy used by your organization.')
param confidentiality string = 'Unclassified'

@description('Criticality tag.')
param criticality string = 'low'

var tags = {
  env: toLower(environment)
  region: region
  criticality: toLower(criticality)
  businessunit: toLower(purpose)
  confidentiality: toLower(confidentiality)
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: region
  tags: tags
}

module azureMonitor './azure-monitor.bicep' = {
  name: 'init-azure-monitor'
  scope: rg
  params: {
    purpose: purpose
    environment: environment
    instance: instance
    orgId: orgId
    region: region
    tags: tags
  }
}

output resourceGroupName string = rg.name
output resourceGroupId string = rg.id
output logAnalyticsWorkspaceId string = azureMonitor.outputs.logAnalyticsWorkspaceId
output logAnalyticsWorkspaceName string = azureMonitor.outputs.logAnalyticsWorkspaceName
output applicationInsightsId string = azureMonitor.outputs.applicationInsightsId
output applicationInsightsName string = azureMonitor.outputs.applicationInsightsName
