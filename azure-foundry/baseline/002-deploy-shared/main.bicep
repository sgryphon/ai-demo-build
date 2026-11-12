/*
Creates, idempotently via Azure Resource Manager:
  - Log Analytics workspace `log-demo-dev-<orgId>-001`
  - Workspace-based Application Insights `appi-demo-dev-<orgId>-001`

This stack deploys shared observability resources at the resource group level.
These resources can be referenced by other workload deployments within the same
resource group, particularly the Azure AI Foundry workload.

The organization identifier is derived deterministically from the subscription
ID and used in globally unique resource names.

Notes:
  Running this requires Azure CLI and an authenticated subscription context.
  The target resource group must already exist; create it with
  `001-init-foundry-rg/main.bicep` or use a corporate-provided resource group.
  Follow Azure Cloud Adoption Framework naming and tagging conventions:
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging

Example:
  az stack group create `
    --resource-group 'rg-demo-foundry-dev-001' `
    --name 'stack-demo-foundry-dev-001-shared' `
    --template-file './azure-foundry/baseline/002-deploy-shared/main.bicep' `
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

module azureMonitor './azure-monitor.bicep' = {
  name: 'deploy-shared-monitor'
  params: {
    purpose: purpose
    environment: environment
    instance: instance
    orgId: orgId
    region: resourceGroup().location
    tags: tags
  }
}

output logAnalyticsWorkspaceId string = azureMonitor.outputs.logAnalyticsWorkspaceId
output logAnalyticsWorkspaceName string = azureMonitor.outputs.logAnalyticsWorkspaceName
output applicationInsightsId string = azureMonitor.outputs.applicationInsightsId
output applicationInsightsName string = azureMonitor.outputs.applicationInsightsName
