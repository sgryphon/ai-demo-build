# Azure AI Foundry

Repeatable Bicep deployment of an Azure AI Foundry account and project with
Azure Monitor integration for agent tracing.

## Prerequisites

- Azure CLI 2.61.0 or later with Bicep support.
- PowerShell 7 or later.
- Access to a subscription and region where Azure AI Foundry is available.
- Azure permissions to create the resources in the selected deployment mode.
- Permission to manage deployment stacks at the selected scopes.

Sign in and, if useful, choose the subscription:

```powershell
az login --tenant <tenant-id>
az account set --subscription <subscription-id>
```

## Initialise the resource group

Note: If you have already been provided a resource group, you can skip this step and go straight to **Deploying shared observability**. This avoids requiring subscription-level permissions.

To initialise a Resource Group:

```powershell
az stack sub create `
  --name stack-demo-foundry-dev-001-init `
  --location australiaeast `
  --template-file ./azure-foundry/baseline/001-init-foundry-rg/main.bicep `
  --action-on-unmanage detachAll `
  --deny-settings-mode none `
  --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
```

This creates the following Azure Resources (using the default settings):

| Resource       | Default naming pattern    | Purpose            |
| -------------- | ------------------------- | ------------------ |
| Resource group | `rg-demo-foundry-dev-001` | Demo deployment RG |

The default `orgId` is derived deterministically from the subscription ID.
All stacks apply the lowercase tag keys `env`, `region`, `criticality`,
`businessunit`, and `confidentiality`. The default confidentiality value is
`unclassified`; change it to match your organization's classification taxonomy.

## Deploying shared services: Azure Monitor

Deploy the shared Azure Monitor resources within the resource group:

```powershell
az stack group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-demo-foundry-dev-001-shared `
  --template-file ./azure-foundry/baseline/002-deploy-shared/main.bicep `
  --action-on-unmanage deleteResources `
  --deny-settings-mode none `
  --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
```

This creates the following Azure Resources (using the default settings):

| Resource                | Default naming pattern      | Purpose                                |
| ----------------------- | --------------------------- | -------------------------------------- |
| Log Analytics workspace | `log-demo-dev-{orgId}-001`  | Workspace backing Application Insights |
| Application Insights    | `appi-demo-dev-{orgId}-001` | Observability foundation for workloads |

## Deploying the workload: Foundry account and project

```powershell
az stack group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-demo-foundry-dev-001-workload `
  --template-file ./azure-foundry/baseline/003-deploy-foundry/main.bicep `
  --action-on-unmanage deleteResources `
  --deny-settings-mode none `
  --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
```

This creates the following Azure Resources (using the default settings):

| Resource                         | Default naming pattern               | Purpose                                                                    |
| -------------------------------- | ------------------------------------ | -------------------------------------------------------------------------- |
| Foundry account                  | `aif-demo-dev-{orgId}-001`           | Current `Microsoft.CognitiveServices/accounts` resource, kind `AIServices` |
| Foundry project                  | `proj-demo-dev-001`                  | Child project under the account                                            |
| Application Insights connections | `aif-...-appinsights` and `appi-...` | Account- and project-scoped tracing connections                            |

You can override parameters or use an existing Azure Monitor Application
Insights resource, for example:

```powershell
az stack group create `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-mydemo-foundry-test-001-workload `
  --template-file ./azure-foundry/baseline/003-deploy-foundry/main.bicep `
  --parameters orgId=MyOrg purpose=MyDemo environment=Test instance=001 applicationInsightsName=appi-existing applicationInsightsResourceGroupName=rg-monitoring `
  --action-on-unmanage deleteResources `
  --deny-settings-mode none `
  --tags env=test region=australiaeast criticality=low businessunit=mydemo confidentiality=unclassified
```

## Stack lifecycle

The init stack retains resources removed from its template (`detachAll`);
the shared and workload stacks delete removed resources but retain resource groups
(`deleteResources`). Application Insights and connections belong to the shared and workload stacks respectively.

## Cleanup

If you want to delete everything, just skip to the last step.

Otherwise you can delete stacks individually.

Delete the workload stack and its managed resources first:

```powershell
az stack group delete `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-demo-foundry-dev-001-workload `
  --action-on-unmanage deleteResources
```

Then delete the shared stack:

```powershell
az stack group delete `
  --resource-group rg-demo-foundry-dev-001 `
  --name stack-demo-foundry-dev-001-shared `
  --action-on-unmanage deleteResources
```

Finally, delete the init stack and resource group (this also deletes anything else that has not already been deleted):

```powershell
az stack sub delete `
  --name stack-demo-foundry-dev-001-init `
  --action-on-unmanage deleteAll
```

The AI Foundry will soft delete, so you need to purge if you want to re-run:

```
az cognitiveservices account purge `
  --resource-group rg-demo-foundry-dev-001 `
  --name aif-demo-dev-buf5ue-001 `
  --location australiaeast
```

## Issues

While you may have Contributor role, e.g. in the subscription to create a Foundry resource, that doesn't mean you can actually use it.

e.g. When you try to access tools like Agents, you get an error:

"You don't have permission to build agents in this project.
To get access, please ask your administrator to assign you the Foundry User role for the resource:
proj-default"

You can modify or even delete the Foundry resource, but to actually use it you need admin permissions (that you may not have) to assign roles.

Try getting your training subscription administrator to assign the role as the subscription level:

```
az role assignment create `
  --role "Foundry User" `
  --assignee "<your-user-id>" `
  --scope "/subscriptions/419ddfc4-e365-4b55-9364-eb45b8f256b1"
```

## Notes

In Azure Portal, when creating Foundry:

- Can link to Key Vault
- Can link to App Insights
- Can set inbound and outbound networking
- Can set User-assigned identity (or System-assigned)

## Ideas: deployment

- Break up into stacks 001, 002, 003, etc
- Have deployments 20261112*, yyyymmdd*,etc (could add hhmm\_)
- A deployment only replaces the stacks it has defined, run in numerical order.
- Have pre-incremental-deployment and post-incremental-deployment scripts

- A clean one-shot deployment just combines the latest version of each stack, in order
- Has pre- and post- full deployment scripts

- Define a store (storage account ?) for completed scripts.
- Stores the completed incremental deployments
- Incremental deployment runs the missing ones, one at a time.

- Overkill for demo scripts ... demo scripts count as the first deployment, with all stacks.
