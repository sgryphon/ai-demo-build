"""
Configures code interpreter for an existing Azure AI Foundry agent.

Adds the code interpreter tool to an existing agent and uploads files for analysis.

Configuration is loaded from .env file, with CLI arguments as overrides.

Prerequisites:
  - Azure subscription with Foundry project deployed
  - Azure CLI authenticated: az login
  - Foundry SDK: pip install "azure-ai-projects>=2.3.0" python-dotenv
  - .env file with PROJECT_ENDPOINT and AGENT_NAME
  - Agent must already exist (created via create_agent.py)

Usage:
  python configure_code_interpreter.py [--agent-name <name>]
                                       [--files <file1> <file2> ...]
                                       [--skip-create] [--replace]

Examples:
  python configure_code_interpreter.py
  python configure_code_interpreter.py --agent-name "my-agent"
  python configure_code_interpreter.py --files data/other.csv
  python configure_code_interpreter.py --skip-create --files data/other.csv
  python configure_code_interpreter.py --replace
  python configure_code_interpreter.py --files  (pass empty list to skip upload)
"""

import argparse
import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentDetails,
    AutoCodeInterpreterToolParam,
    CodeInterpreterTool,
)

# Load environment variables from .env file
load_dotenv()


def get_code_interpreter_tool(agent: AgentDetails) -> CodeInterpreterTool | None:
    """Return the agent's configured code interpreter tool, if any."""
    for tool in agent.versions.latest.definition.tools or []:
        if isinstance(tool, CodeInterpreterTool):
            return tool

    return None


def configure_code_interpreter(
    client: AIProjectClient,
    agent_name: str,
    skip_create: bool = False,
    replace: bool = False,
) -> None:
    """Enable and save code interpreter tool on an agent."""
    if skip_create:
        print(f"ℹ Skipping code interpreter creation.")
        return

    current_agent = client.agents.get(agent_name)
    existing_tool = get_code_interpreter_tool(current_agent)

    if existing_tool and not replace:
        print(f"⚠ Code interpreter already configured; skipping creation.")
        return
    if replace and not existing_tool:
        print(f"⚠ Code interpreter is not configured; creating it.")

    latest_version = current_agent.versions.latest
    definition = latest_version.definition
    if existing_tool:
        existing_tool.container = AutoCodeInterpreterToolParam()
    else:
        definition.tools = (definition.tools or []) + [
            CodeInterpreterTool(container=AutoCodeInterpreterToolParam())
        ]

    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=definition,
        description=latest_version.description,
        metadata=latest_version.metadata,
    )
    print(f"✓ Code interpreter tool enabled and saved")
    print(f"  Agent: {agent.name}")


def upload_files(
    client: AIProjectClient,
    agent_name: str,
    file_paths: list[str],
) -> None:
    """Upload files and attach them to the agent's configured interpreter."""
    if not file_paths:
        print(f"ℹ No files to upload")
        return

    current_agent = client.agents.get(agent_name)
    code_interpreter_tool = get_code_interpreter_tool(current_agent)

    if not code_interpreter_tool:
        raise ValueError(
            f"Agent '{agent_name}' does not have code interpreter configured. "
        )

    openai_client = client.get_openai_client()
    container = code_interpreter_tool.container
    if container is None:
        container = AutoCodeInterpreterToolParam()
        code_interpreter_tool.container = container

    print(f"Uploading files to code interpreter")
    file_ids = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            file = openai_client.files.create(purpose="assistants", file=f)

        if isinstance(container, str):
            openai_client.containers.files.create(
                container_id=container,
                file_id=file.id,
            )
        file_ids.append(file.id)
        print(f"✓ Uploaded: {file_path} (File ID: {file.id})")

    if isinstance(container, AutoCodeInterpreterToolParam):
        container.file_ids = (container.file_ids or []) + file_ids
        latest_version = current_agent.versions.latest
        client.agents.create_version(
            agent_name=agent_name,
            definition=latest_version.definition,
            description=latest_version.description,
            metadata=latest_version.metadata,
        )

    print(f"\n✓ All files attached to code interpreter ({len(file_paths)} files)")


def main():
    parser = argparse.ArgumentParser(
        description="Configure code interpreter for an Azure AI Foundry agent"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        help="Name of the agent to configure (default: AGENT_NAME from .env)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=["data/system_performance.csv"],
        help="Files to upload (default: data/system_performance.csv). "
        "Pass --files with no args to skip upload.",
    )
    parser.add_argument(
        "--skip-create",
        action="store_true",
        default=False,
        help="Skip configuration, only upload to the existing code interpreter",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Reset existing code interpreter configuration before uploading files "
        "(does not delete previously uploaded files or containers)",
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
        # Configure code interpreter on the agent
        configure_code_interpreter(
            client=client,
            agent_name=agent_name,
            skip_create=args.skip_create,
            replace=args.replace,
        )

        # Upload files to the code interpreter
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
