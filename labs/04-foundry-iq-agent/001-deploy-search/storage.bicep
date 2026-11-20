/*
Creates the storage account and blob container holding the knowledge source documents.
*/

@description('Storage account name.')
@minLength(3)
@maxLength(24)
param storageName string

@description('Blob container for the source documents.')
@minLength(3)
@maxLength(63)
param containerName string

@description('Tags applied to all resources that support tags.')
param tags object

// Demo shortcut: shared key access stays enabled so the knowledge source can
// use a connection string. For production, disable shared keys and grant the
// search managed identity Storage Blob Data Reader instead.
resource storage 'Microsoft.Storage/storageAccounts@2025-08-01' = {
  name: storageName
  location: resourceGroup().location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  tags: tags
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-08-01' = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-08-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
  }
}

output storageId string = storage.id
output storageName string = storage.name
output containerName string = container.name
