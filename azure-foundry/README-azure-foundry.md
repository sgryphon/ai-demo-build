# Azure AI Foundry

Repeatable Bicep deployment of an Azure AI Foundry account and project with
Azure Monitor integration for agent tracing.

## Prerequisites

- Azure CLI 2.61.0 or later with Bicep support.
- PowerShell 7 or later.
- Access to a subscription and region where Azure AI Foundry is available.
- Azure permissions to create the resources in the selected deployment mode.
- Permission to create the monitoring role assignments when deploying the
  Foundry workload.
- Permission to manage deployment stacks at the selected scopes.

Sign in and, if useful, choose the subscription:

```powershell
az login
az account set --subscription <subscription-id>
```

## Initialise the resource group

Note: If you have already been provided a resource group, you can skip this step and go straight to **Deploying the workload**. This avoids requiring subscription-level permissions.

To initialise a Resource Group and Azure Monitor:

```powershell
az stack sub create `
  --name stack-demo-foundry-dev-001-init `
  --location australiaeast `
  --template-file ./azure-foundry/infrastructure/001-init-foundry-rg.bicep `
  --action-on-unmanage detachAll `
  --deny-settings-mode none `
  --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
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
az stack group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-demo-foundry-dev-001-workload `
  --template-file ./azure-foundry/infrastructure/002-deploy-foundry.bicep `
  --action-on-unmanage deleteResources `
  --deny-settings-mode none `
  --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
```

This creates the following Azure Resources (using the default settings):

| Resource                          | Default naming pattern               | Purpose                                                                    |
| --------------------------------- | ------------------------------------ | -------------------------------------------------------------------------- |
| Foundry account                   | `aif-demo-dev-{orgId}-001`           | Current `Microsoft.CognitiveServices/accounts` resource, kind `AIServices` |
| Foundry project                   | `proj-demo-dev-001`                  | Child project under the account                                            |
| Application Insights connections  | `aif-...-appinsights` and `appi-...` | Account- and project-scoped tracing connections                            |
| Project identity role assignments | On Application Insights              | Log Analytics Reader and Privileged Monitoring Data Reader                 |

You can override parameters or use an existing Azure Monitor Application
Insights resource, for example:

```powershell
az stack group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-mydemo-foundry-test-001-workload `
  --template-file ./azure-foundry/infrastructure/002-deploy-foundry.bicep `
  --parameters orgId=MyOrg purpose=MyDemo environment=Test instance=001 applicationInsightsName=appi-existing applicationInsightsResourceGroupName=rg-monitoring `
  --action-on-unmanage deleteResources `
  --deny-settings-mode none `
  --tags env=test region=australiaeast criticality=low businessunit=mydemo confidentiality=unclassified
```

## Stack lifecycle

The init stack retains resources removed from its template (`detachAll`);
the workload stack deletes removed resources but retains resource groups
(`deleteResources`). Existing Application Insights resources remain outside
workload ownership; its connections and role assignments belong to the workload.

## Cleanup

Delete the workload stack and its managed resources first. This retains the
resource group and foundation resources:

```powershell
az stack group delete `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-demo-foundry-dev-001-workload `
  --action-on-unmanage deleteResources
```

For the demo foundation only, delete the init stack and its resource group:

```powershell
az stack sub delete `
  --name stack-demo-foundry-dev-001-init `
  --action-on-unmanage deleteAll
```

Deleting the demo resource group also deletes anything else placed in it.
