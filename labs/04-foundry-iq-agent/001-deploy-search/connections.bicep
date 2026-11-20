/*
Creates Foundry project connections to the Azure AI Search service:
  - RemoteTool (MCP) connection to the knowledge base MCP endpoint, used by
    the agent's knowledge base tool. Sends the search key as an `api-key` header.
  - CognitiveSearch connection so the search service appears under connected
    resources in the Foundry portal.

Demo shortcut: both connections use the search admin key, read in-template and
never output. For production, prefer authType 'ProjectManagedIdentity'
(audience https://search.azure.com/) with the project identity granted
Search Index Data Reader.
*/

@description('Existing Azure AI Foundry account name.')
param foundryName string

@description('Existing Foundry project name.')
param projectName string

@description('Existing Azure AI Search service name.')
param searchName string

@description('Knowledge base name; the MCP endpoint is per knowledge base.')
param knowledgeBaseName string

@description('Search data-plane API version used by the knowledge base MCP endpoint.')
param searchMcpApiVersion string

@description('Name of the RemoteTool (MCP) project connection.')
@minLength(3)
@maxLength(33)
param mcpConnectionName string

resource foundry 'Microsoft.CognitiveServices/accounts@2026-03-01' existing = {
  name: foundryName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-03-01' existing = {
  parent: foundry
  name: projectName
}

resource search 'Microsoft.Search/searchServices@2025-05-01' existing = {
  name: searchName
}

var searchEndpoint = 'https://${search.name}.search.windows.net'

resource mcpConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2026-03-01' = {
  parent: project
  name: mcpConnectionName
  properties: {
    category: 'RemoteTool'
    authType: 'CustomKeys'
    target: '${searchEndpoint}/knowledgebases/${knowledgeBaseName}/mcp?api-version=${searchMcpApiVersion}'
    isSharedToAll: true
    credentials: {
      keys: {
        'api-key': search.listAdminKeys().primaryKey
      }
    }
    metadata: {
      ApiType: 'Azure'
    }
  }
}

resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2026-03-01' = {
  parent: project
  name: search.name
  properties: {
    category: 'CognitiveSearch'
    authType: 'ApiKey'
    target: searchEndpoint
    isSharedToAll: true
    credentials: {
      key: search.listAdminKeys().primaryKey
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: search.id
    }
  }
}

output mcpConnectionName string = mcpConnection.name
output searchConnectionName string = searchConnection.name
