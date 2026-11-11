/*
Grants the Foundry project identity read access required for querying
Application Insights traces and GenAI trace content.
*/

@description('Application Insights resource name.')
param applicationInsightsName string

@description('Resource ID of the Foundry project.')
param projectId string

@description('Principal ID of the Foundry project system-assigned identity.')
param projectPrincipalId string

var monitoringRoleDefinitionIds = [
  '73c42c96-874c-492b-b04d-ab87d138a893'
  'dbc9c667-e97f-4491-aee6-90b9cf960190'
]

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource appInsightsReaderRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for roleDefinitionGuid in monitoringRoleDefinitionIds: {
    name: guid(projectId, roleDefinitionGuid, appInsights.id)
    scope: appInsights
    properties: {
      principalId: projectPrincipalId
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionGuid)
      principalType: 'ServicePrincipal'
    }
  }
]
