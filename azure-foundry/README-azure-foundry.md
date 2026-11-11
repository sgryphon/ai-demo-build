# Azure AI Foundry

Repeatable Bicep deployment for the current Azure AI Foundry account/project
model. It creates a Foundry account and one project without deploying models or
adding networking and other optional workload components.

## Prerequisites

- Azure CLI with Bicep support.
- PowerShell 7 or later.
- Access to a subscription and region where Azure AI Foundry is available.
- Azure permissions to create the resources in the selected deployment mode.

Sign in and, if useful, choose the subscription:

```powershell
az login
az account set --subscription <subscription-id>
```

## Initialise the resource group

Note: If you have already been provided a resource group, you can skip this step and go straight to **Deploying the workload**. This avoids requiring subscription-level permissions.

To initialise a Resource Group and Azure Monitor:

```powershell
az deployment sub create `
  --name "init-foundry-rg-$(Get-Date -Format 'yyyyMMddHHmmss')" `
  --location australiaeast `
  --template-file ./azure-foundry/infrastructure/001-init-foundry-rg.bicep `
  --parameters purpose=Demo environment=Dev region=australiaeast instance=001
```

This creates the following Azure Resources (using the default settings):

| Resource                | Default naming pattern      | Purpose                                     |
| ----------------------- | --------------------------- | ------------------------------------------- |
| Resource group          | `rg-demo-foundry-dev-001`   | Demo deployment boundary                    |
| Log Analytics workspace | `log-demo-dev-{orgId}-001`  | Workspace backing demo Application Insights |
| Application Insights    | `appi-demo-dev-{orgId}-001` | Optional observability foundation           |

The default `orgId` is derived deterministically from the subscription ID.
Both phases apply the lowercase tag keys `env`, `region`, `criticality`,
`businessunit`, and `confidentiality`. The default confidentiality value is
`unclassified`; change it to match your organization's classification taxonomy.

### Deploying the workload: Foundry account and project

```powershell
az deployment group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name "deploy-foundry-$(Get-Date -Format 'yyyyMMddHHmmss')" `
  --template-file ./azure-foundry/infrastructure/002-deploy-foundry.bicep `
  --parameters purpose=Demo environment=Dev instance=001
```

This creates the following Azure Resources (using the default settings):

| Resource        | Default naming pattern     | Purpose                                                                    |
| --------------- | -------------------------- | -------------------------------------------------------------------------- |
| Foundry account | `aif-demo-dev-{orgId}-001` | Current `Microsoft.CognitiveServices/accounts` resource, kind `AIServices` |
| Foundry project | `proj-demo-dev-001`        | Child project under the account                                            |

You can also override parameters, for example:

```powershell
az deployment group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name "deploy-foundry-$(Get-Date -Format 'yyyyMMddHHmmss')" `
  --template-file ./azure-foundry/infrastructure/002-deploy-foundry.bicep `
  --parameters orgid=MyOrg purpose=MyDemo environment=Test instance=001
```

## Cleanup

For the default demo resource group created by Phase 1, remove the group and its
resources:

```powershell
az group delete --name rg-demo-foundry-dev-001 --yes --no-wait
```

Replace the example name with the resource group name used in Phase 1. Do not
delete a corporate-provided resource group.
