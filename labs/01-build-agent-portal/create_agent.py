"""
Creates or updates a prompt agent in Azure AI Foundry.

Configuration is loaded from .env file, with CLI arguments as overrides.

Prerequisites:
  - Azure subscription with Foundry project deployed
  - Azure CLI authenticated: az login
  - Foundry SDK: pip install "azure-ai-projects>=2.3.0" python-dotenv
  - .env file with PROJECT_ENDPOINT and AGENT_NAME

Usage:
  python create_agent.py [--agent-name <name>] [--model <model>] [--description <desc>]
                         [--update]

Examples:
  python create_agent.py
  python create_agent.py --agent-name "my-agent"
  python create_agent.py --update
  python create_agent.py --model "gpt-6-astra" --update
"""

import argparse
import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Load environment variables from .env file
load_dotenv()

DEFAULT_MODEL = "model-router"
DEFAULT_SYSTEM_PROMPT_FILE = "data/instructions.md"


def agent_exists(
    client: AIProjectClient,
    agent_name: str,
) -> bool:
    """Check if an agent exists."""
    try:
        client.agents.get(agent_name)
        return True
    except Exception:
        return False


def get_agent(
    client: AIProjectClient,
    agent_name: str,
):
    """Get agent details."""
    return client.agents.get(agent_name)


def update_agent(
    client: AIProjectClient,
    agent_name: str,
    system_prompt: str | None = None,
    model: str | None = None,
    description: str | None = None,
):
    """Create a new version from the latest one, patching only the given changes.

    Agent versions are immutable, so the SDK has no in-place update.
    Existing settings (tools, temperature, metadata, etc.) are preserved.
    """
    latest_version = client.agents.get(agent_name).versions.latest
    definition = latest_version.definition

    if system_prompt is not None:
        definition.instructions = system_prompt
    if model is not None:
        definition.model = model

    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=definition,
        description=(
            description if description is not None else latest_version.description
        ),
        metadata=latest_version.metadata,
    )

    print(f"✓ Agent updated successfully")
    print(f"  Name: {agent.name}")
    print(f"  ID: {agent.id}")
    print(f"  Version: {agent.version}")
    print(f"  Model: {agent.definition.model}")

    return agent


def create_agent(
    client: AIProjectClient,
    agent_name: str,
    model: str,
    system_prompt: str,
    description: str = "",
):
    """Create a new prompt agent in the Foundry project."""
    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model,
            instructions=system_prompt,
        ),
        description=description,
    )

    print(f"✓ Agent created successfully")
    print(f"  Name: {agent.name}")
    print(f"  ID: {agent.id}")
    print(f"  Version: {agent.version}")
    print(f"  Model: {agent.definition.model}")

    return agent


def main():
    parser = argparse.ArgumentParser(
        description="Create or update a prompt-based agent in Azure AI Foundry"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        help="Name of the agent to create or update",
    )
    parser.add_argument(
        "--model",
        type=str,
        help=f"Model to use (default: {DEFAULT_MODEL} when creating; "
        "unchanged when updating)",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Agent description",
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        help="Custom system prompt (overrides --system-prompt-file)",
    )
    parser.add_argument(
        "--system-prompt-file",
        type=str,
        help=(
            "Path to system prompt file (default on create: "
            f"{DEFAULT_SYSTEM_PROMPT_FILE}; on update, only used when explicitly passed)"
        ),
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Create a new version of an existing agent from its latest version, "
        "preserving existing settings (keeps version history)",
    )

    args = parser.parse_args()

    agent_name = args.agent_name or os.getenv("AGENT_NAME")
    project_endpoint = os.getenv("PROJECT_ENDPOINT")

    # On update, use instructions only when explicitly supplied. Creation falls
    # back to the default instructions file.
    system_prompt = args.system_prompt
    if system_prompt is None:
        system_prompt_file = args.system_prompt_file
        if system_prompt_file is None and not args.update:
            system_prompt_file = DEFAULT_SYSTEM_PROMPT_FILE

        if system_prompt_file is not None:
            try:
                with open(system_prompt_file, 'r') as f:
                    system_prompt = f.read()
            except FileNotFoundError:
                raise ValueError(
                    f"System prompt file not found: {system_prompt_file}. "
                    "Provide --system-prompt or --system-prompt-file."
                )

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
        exists = agent_exists(client, agent_name)

        if args.update:
            if not exists:
                raise ValueError(
                    f"Agent '{agent_name}' does not exist. "
                )
            update_agent(
                client=client,
                agent_name=agent_name,
                system_prompt=system_prompt,
                model=args.model,
                description=args.description,
            )

        elif exists:
            print(f"Agent '{agent_name}' already exists.")
            print(f"Use --update to create a new version.")

        else:
            create_agent(
                client=client,
                agent_name=agent_name,
                model=args.model if args.model is not None else DEFAULT_MODEL,
                system_prompt=system_prompt,
                description=(
                    args.description if args.description is not None else ""
                ),
            )

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
