"""
Connects an Azure AI Foundry agent to a Foundry IQ knowledge base.

Adds the knowledge base MCP tool (knowledge_base_retrieve) to an existing agent
as a new agent version. The tool authenticates via the RemoteTool project
connection created by 001-deploy-search/main.bicep.

Configuration is loaded from .env file, with CLI arguments as overrides.

Prerequisites:
  - Resources deployed via 001-deploy-search/main.bicep
  - Knowledge base created via configure_knowledge_base.py
  - Agent created via create_agent.py
  - Azure CLI authenticated: az login
  - .env with PROJECT_ENDPOINT, AGENT_NAME and SEARCH_ENDPOINT

Usage:
  python configure_foundry_iq.py [--agent-name <name>] [--replace]
                                 [--require-approval {always,never}]

Examples:
  python configure_foundry_iq.py
  python configure_foundry_iq.py --replace --require-approval never
"""

import argparse
import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDetails, MCPTool

# Load environment variables from .env file
load_dotenv()

SERVER_LABEL = "knowledge-base"
SEARCH_API_VERSION = "2026-11-01-preview"


def get_knowledge_base_tool(agent: AgentDetails) -> MCPTool | None:
    """Return the agent's knowledge base MCP tool, if any."""
    for tool in agent.versions.latest.definition.tools or []:
        if isinstance(tool, MCPTool) and tool.server_label == SERVER_LABEL:
            return tool

    return None


def configure_foundry_iq(
    client: AIProjectClient,
    agent_name: str,
    server_url: str,
    connection_name: str,
    require_approval: str,
    replace: bool = False,
):
    current_agent = client.agents.get(agent_name)
    latest_version = current_agent.versions.latest
    definition = latest_version.definition

    existing_tool = get_knowledge_base_tool(current_agent)
    if existing_tool:
        if not replace:
            print(
                f"⚠ Knowledge base tool already configured: {existing_tool.server_url}"
            )
            return
        print("Replacing existing knowledge base tool...")

    tool = MCPTool(
        server_label=SERVER_LABEL,
        server_url=server_url,
        allowed_tools=["knowledge_base_retrieve"],
        require_approval=require_approval,
        project_connection_id=connection_name,
    )
    definition.tools = [t for t in definition.tools or [] if t is not existing_tool] + [
        tool
    ]

    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=definition,
        description=latest_version.description,
        metadata=latest_version.metadata,
    )

    print("✓ Knowledge base tool enabled and saved")
    print(f"  Agent: {agent.name} (version {agent.version})")
    print(f"  MCP server: {server_url}")
    print(f"  Connection: {connection_name}")
    print(f"  Require approval: {require_approval}")


def main():
    parser = argparse.ArgumentParser(
        description="Connect an Azure AI Foundry agent to a Foundry IQ knowledge base"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        help="Name of the agent to configure",
    )
    parser.add_argument(
        "--require-approval",
        choices=["always", "never"],
        default="always",
        help="Whether tool calls need client approval (default: always, as in the lab)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Replace the knowledge base tool if it already exists",
    )
    args = parser.parse_args()

    agent_name = args.agent_name or os.getenv("AGENT_NAME")
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    search_endpoint = os.getenv("SEARCH_ENDPOINT")
    base_name = os.getenv("KNOWLEDGE_BASE_NAME", "kb-contosoproducts")
    connection_name = os.getenv("MCP_CONNECTION_NAME", f"{base_name}-mcp")

    if not agent_name:
        raise ValueError(
            "Agent name not provided. Set AGENT_NAME in .env or pass --agent-name."
        )
    if not project_endpoint:
        raise ValueError("PROJECT_ENDPOINT not set in .env.")
    if not search_endpoint:
        raise ValueError("SEARCH_ENDPOINT not set in .env.")

    server_url = (
        f"{search_endpoint.rstrip('/')}/knowledgebases/{base_name}/mcp"
        f"?api-version={SEARCH_API_VERSION}"
    )

    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )

    configure_foundry_iq(
        client=client,
        agent_name=agent_name,
        server_url=server_url,
        connection_name=connection_name,
        require_approval=args.require_approval,
        replace=args.replace,
    )


if __name__ == "__main__":
    main()
