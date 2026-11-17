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
                         [--replace | --upgrade]

Examples:
  python create_agent.py
  python create_agent.py --agent-name "my-agent"
  python create_agent.py --model "gpt-6-astra" --replace
  python create_agent.py --upgrade
"""

import argparse
import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Load environment variables from .env file
load_dotenv()


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


def update_agent_definition(
    client: AIProjectClient,
    agent_name: str,
    model: str,
    system_prompt: str,
):
    """Update an existing agent's definition (--force)."""
    agent = client.agents.update(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model,
            instructions=system_prompt,
        ),
    )

    print(f"✓ Agent updated successfully")
    print(f"  Name: {agent.name}")
    print(f"  ID: {agent.id}")
    print(f"  Version: {agent.version}")
    print(f"  Model: {agent.definition.model}")

    return agent


def create_new_version(
    client: AIProjectClient,
    agent_name: str,
    model: str,
    system_prompt: str,
):
    """Create a new version of an agent (--new-version)."""
    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model,
            instructions=system_prompt,
        ),
    )

    print(f"✓ New version created successfully")
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
):
    """Create a new prompt agent in the Foundry project."""
    agent = client.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model,
            instructions=system_prompt,
        ),
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
        default="model-router",
        help="Model to use (default: model-router)",
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
        default="data/instructions.md",
        help="Path to system prompt file (default: data/instructions.md)",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--replace",
        action="store_true",
        help="Overwrite existing agent definition in-place (requires agent to exist)",
    )
    group.add_argument(
        "--upgrade",
        action="store_true",
        help="Create a new version of an existing agent (keeps version history)",
    )

    args = parser.parse_args()

    agent_name = args.agent_name or os.getenv("AGENT_NAME")
    model = args.model
    project_endpoint = os.getenv("PROJECT_ENDPOINT")

    # Load system prompt: CLI arg overrides file
    if args.system_prompt:
        system_prompt = args.system_prompt
    else:
        try:
            with open(args.system_prompt_file, 'r') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            raise ValueError(
                f"System prompt file not found: {args.system_prompt_file}. "
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

        if exists and not args.replace and not args.upgrade:
            print(f"Agent '{agent_name}' already exists.")
            print(f"Use --replace to overwrite or --upgrade to create a new version.")
            return

        if args.replace:
            if not exists:
                raise ValueError(
                    f"Agent '{agent_name}' does not exist. "
                    "Use default behavior (without --replace or --upgrade) to create it."
                )
            update_agent_definition(
                client=client,
                agent_name=agent_name,
                model=model,
                system_prompt=system_prompt,
            )

        elif args.upgrade:
            if not exists:
                raise ValueError(
                    f"Agent '{agent_name}' does not exist. "
                    "Use default behavior (without --replace or --upgrade) to create it."
                )
            create_new_version(
                client=client,
                agent_name=agent_name,
                model=model,
                system_prompt=system_prompt,
            )

        else:
            create_agent(
                client=client,
                agent_name=agent_name,
                model=model,
                system_prompt=system_prompt,
            )

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
