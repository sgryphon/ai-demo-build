"""
Configures file search tool for an Azure AI Foundry agent.

Adds the file search tool to an existing agent and uploads files to a vector store.

Configuration is loaded from .env file, with CLI arguments as overrides.

Prerequisites:
  - Azure subscription with Foundry project deployed
  - Azure CLI authenticated: az login
  - Foundry SDK: pip install "azure-ai-projects>=1.0.0" python-dotenv
  - .env file with PROJECT_ENDPOINT and AGENT_NAME
  - Agent must already exist (created via create_agent.py)

Usage:
  python configure_filesearch.py [--agent-name <name>] [--files <file1> <file2> ...]
                                  [--skip-create] [--replace]

Examples:
  python configure_filesearch.py
  python configure_filesearch.py --agent-name "my-agent"
  python configure_filesearch.py --files data/IT_Policy.txt data/system_performance.csv
  python configure_filesearch.py --skip-create --files data/IT_Policy.txt
  python configure_filesearch.py --replace
  python configure_filesearch.py --files  (pass empty list to skip upload)
"""

import argparse
import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDetails, FileSearchTool

# Load environment variables from .env file
load_dotenv()


def get_file_search_tool(agent: AgentDetails) -> FileSearchTool | None:
    """Return the agent's configured file search tool, if any."""
    for tool in agent.versions.latest.definition.tools or []:
        if isinstance(tool, FileSearchTool) and tool.vector_store_ids:
            return tool

    return None


def configure_file_search(
    client: AIProjectClient,
    agent_name: str,
    skip_create: bool = False,
    replace: bool = False,
) -> str:
    """Enable and save file search tool on an agent. Returns vector_store_id."""
    if skip_create:
        print(f"ℹ Skipping file store creation.")
        return None

    openai_client = client.get_openai_client()
    current_agent = client.agents.get(agent_name)

    # Check if file search already exists
    existing_file_search_tool = get_file_search_tool(current_agent)

    if existing_file_search_tool:
        existing_vector_store_id = existing_file_search_tool.vector_store_ids[0]
        if not replace:
            print(f"⚠ File search already configured with vector store: {existing_vector_store_id}")
            return existing_vector_store_id

        # Replace mode: delete old store and create new one
        print(f"Replacing existing file search...")
        openai_client.vector_stores.delete(existing_vector_store_id)
        print(f"  Deleted old vector store: {existing_vector_store_id}")

    # Create new vector store
    vector_store = openai_client.vector_stores.create(name=f"{agent_name}-files")
    print(f"✓ Vector store created: {vector_store.id}")

    # Save a new agent version, reusing the tool found by the initial check.
    latest_version = current_agent.versions.latest
    definition = latest_version.definition
    if existing_file_search_tool:
        existing_file_search_tool.vector_store_ids = [vector_store.id]
    else:
        definition.tools = (definition.tools or []) + [
            FileSearchTool(vector_store_ids=[vector_store.id])
        ]

    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=definition,
        description=latest_version.description,
        metadata=latest_version.metadata,
    )

    print(f"✓ File search tool enabled and saved")
    print(f"  Agent: {agent.name}")
    print(f"  Vector store: {vector_store.id}")

    return vector_store.id


def upload_files(
    client: AIProjectClient,
    agent_name: str,
    file_paths: list[str],
):
    """Upload files to vector store attached to agent."""
    if not file_paths:
        print(f"ℹ No files to upload")
        return

    # Get agent and retrieve its vector store
    agent = client.agents.get(agent_name)
    file_search_tool = get_file_search_tool(agent)

    if not file_search_tool:
        raise ValueError(
            f"Agent '{agent_name}' does not have file search configured. "
        )

    vector_store_id = file_search_tool.vector_store_ids[0]
    openai_client = client.get_openai_client()

    print(f"Uploading files to vector store: {vector_store_id}")
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            file = openai_client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store_id,
                file=f,
            )
            print(f"✓ Uploaded: {file_path} (File ID: {file.id})")

    print(f"\n✓ All files attached to vector store ({len(file_paths)} files)")


def main():
    parser = argparse.ArgumentParser(
        description="Configure file search tool for an Azure AI Foundry agent"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        help="Name of the agent to configure",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=["data/IT_Policy.txt"],
        help="Files to upload and attach (default: data/IT_Policy.txt). Pass --files with no args to skip upload.",
    )
    parser.add_argument(
        "--skip-create",
        action="store_true",
        default=False,
        help="Skip creating/configuring file search, only upload to existing",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Replace existing file search if it already exists",
    )

    args = parser.parse_args()

    agent_name = args.agent_name or os.getenv("AGENT_NAME")
    project_endpoint = os.getenv("PROJECT_ENDPOINT")

    if not agent_name:
        raise ValueError(
            "Agent name not provided. "
            "Set AGENT_NAME in .env or pass --agent-name."
        )

    if not project_endpoint:
        raise ValueError(
            "PROJECT_ENDPOINT not set in .env."
        )

    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )

    try:
        # Configure file search on the agent
        vector_store_id = configure_file_search(
            client=client,
            agent_name=agent_name,
            skip_create=args.skip_create,
            replace=args.replace,
        )

        # Upload files to the vector store
        upload_files(
            client=client,
            agent_name=agent_name,
            file_paths=args.files,
        )
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
