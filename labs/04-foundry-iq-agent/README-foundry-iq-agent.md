# Foundry IQ Agent example

Connects an agent to a Foundry IQ knowledge base (Azure AI Search agentic retrieval) over Contoso product PDFs.

Based on: https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/Exercises/04-integrate-agent-with-foundry-iq.html

The split follows what Microsoft supports:

- **Bicep** (`001-deploy-search`): the Azure resources behind the portal's "Connect to Foundry IQ" step. These are the AI Search service (Basic), a storage account and container, a `text-embedding-3-small` deployment, and two Foundry project connections to Search: `RemoteTool` for the knowledge base MCP endpoint, and `CognitiveSearch`.
- **Python**: data-plane objects with no ARM resource type. These are the blob upload, the knowledge source, the knowledge base, and the agent's MCP tool.

Notes:

- **API keys are a demo shortcut.** They mean no role assignments are needed: Contributor on the resource group plus Foundry project access is enough. Keyless access (managed identities + RBAC, with local auth disabled) is preferred for production.
- No secrets are output by the deployment. Retrieve them with the `az` commands in the header of [main.bicep](./001-deploy-search/main.bicep).
- **Cost:** Basic tier Search is billed hourly while it exists. Delete the stack when finished.
- **Preview APIs:** Foundry IQ requires the preview Search API (`2026-11-01-preview`) and the preview `azure-search-documents` SDK.
- **Chat model (optional):** the knowledge base chat model, used for query planning, must be one Foundry IQ supports (e.g. `gpt-5-mini`), not `model-router`. Without one, retrieval uses minimal reasoning. Deploy one with `labs/02-custom-function-agent/001-deploy-model` if needed.

## Prerequisites

- Foundry account and project deployed, see `/azure-foundry`
- Python virtual environment `.venv` with `pip install -r requirements.txt`
- Azure CLI authenticated: `az login`

## Deploy Azure resources

```powershell
az stack group create `
  --resource-group 'rg-demo-foundry-dev-001' `
  --name 'stack-demo-foundry-dev-001-search' `
  --template-file './001-deploy-search/main.bicep' `
  --action-on-unmanage deleteResources `
  --deny-settings-mode none `
  --tags env=dev region=australiaeast criticality=low businessunit=demo confidentiality=unclassified
```

## Setup environment

- Copy `.env.example` to `.env`.
- Set PROJECT_ENDPOINT (see `labs/01-build-agent` README) and AGENT_NAME.
- Run the "Retrieve values for .env" commands from the header of [main.bicep](./001-deploy-search/main.bicep) and paste the output into `.env`.
- Optionally set CHAT_DEPLOYMENT and CHAT_MODEL.

## Create and connect the agent

```powershell
python create_agent.py                # agent with product expert instructions
python configure_knowledge_base.py    # upload PDFs, create knowledge source + base, wait for ingestion
python configure_foundry_iq.py        # add knowledge base MCP tool to the agent
```

Foundry caches connection credentials for about 2 minutes, so allow a short delay after deployment or key changes.

## Test the agent

```powershell
python agent_client.py
```

Approve the `knowledge_base_retrieve` calls when prompted. Use `configure_foundry_iq.py --replace --require-approval never` to skip approvals.

For example: "What tents do you have?" or "Which backpack is best for a multi-day hike?"

## Cleanup

```powershell
az stack group delete `
  --resource-group 'rg-demo-foundry-dev-001' `
  --name 'stack-demo-foundry-dev-001-search' `
  --action-on-unmanage deleteResources `
  --yes
```
