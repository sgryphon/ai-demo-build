# Build Agent example

Agents are created via the API (not via Azure resources).

They need a deployed model, but you can use 'model-router' as a default, to auto-select models.

If Azure commands don't work, make sure you have the latest CLI via `winget install --id Microsoft.AzureCLI`.

## Setup environment

- Get the endpoint for the first Project of the first Foundry in the resource group:

```
$foundryName = (az cognitiveservices account list --resource-group 'rg-demo-foundry-dev-001' --query '[0].name' -o tsv)
$projects = az cognitiveservices account project list -g 'rg-demo-foundry-dev-001' --name $foundryName | ConvertFrom-Json
$projects[0].properties.endpoints
```

- Copy `.env.example` to `.env`
- Insert the endpoint into PROJECT_ENDPOINT

## Python venv

- Right click `01-build-agent-portal` folder and select 'Open in Integrated Terminal'
- Create venv, activate it, and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

## Agent creation

(Check: do we need `az login`)

```powershell
python create_agent.py
```
