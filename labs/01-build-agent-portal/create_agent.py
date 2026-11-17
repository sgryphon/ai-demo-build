"""
Creates a prompt agent in Azure AI Foundry.

Configuration is loaded from .env file, with CLI arguments as overrides.

Prerequisites:
  - Azure subscription with Foundry project deployed
  - Azure CLI authenticated: az login
  - Foundry SDK: pip install "azure-ai-projects>=2.3.0" python-dotenv
  - .env file with PROJECT_ENDPOINT and AGENT_NAME

Usage:
  python create_agent.py [--agent-name <name>] [--model <model>] [--description <desc>]

Examples:
  python create_agent.py
  python create_agent.py --agent-name "my-agent"
  python create_agent.py --model "gpt-6-astra" --description "My custom agent"
"""

import argparse
import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Load environment variables from .env file
load_dotenv()


def create_agent(
    agent_name: str,
    model: str,
    project_endpoint: str,
    system_prompt: str,
):
    """Creates a prompt agent in the Foundry project."""
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )

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
        description="Create a prompt-based agent in Azure AI Foundry"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        help="Name of the agent to create",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (e.g., gpt-6-astra, gpt-6.1-terra, model-router)",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Agent description",
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        help="Custom system prompt",
    )

    args = parser.parse_args()

    agent_name = args.agent_name or os.getenv("AGENT_NAME")
    model = args.model or "model-router"
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

    try:
        create_agent(
            agent_name=agent_name,
            model=model,
            project_endpoint=project_endpoint,
            system_prompt=args.system_prompt,
        )
    except Exception as e:
        print(f"Error creating agent: {e}")
        raise


if __name__ == "__main__":
    main()
