"""
Interactive client for the Contoso product expert agent with Foundry IQ.

Completed version of the lab 04 starter (agent_client.py). Uses the
conversations API and handles MCP approval requests for knowledge base access.

Prerequisites:
  - Agent configured via configure_foundry_iq.py
  - Azure CLI authenticated: az login
  - .env with PROJECT_ENDPOINT and AGENT_NAME

Usage:
  python agent_client.py
"""

import json
import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
agent_name = os.getenv("AGENT_NAME")

# Validate configuration
if not project_endpoint or not agent_name:
    raise ValueError("PROJECT_ENDPOINT and AGENT_NAME must be set in .env file")

print(f"Connecting to project: {project_endpoint}")
print(f"Using agent: {agent_name}\n")

# Connect to the project and agent
credential = DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_managed_identity_credential=True,
)
project_client = AIProjectClient(credential=credential, endpoint=project_endpoint)

openai_client = project_client.get_openai_client()

agent = project_client.agents.get(agent_name=agent_name)
print(f"Connected to agent: {agent.name} (id: {agent.id})\n")

conversation = openai_client.conversations.create(items=[])
print(f"Created conversation (id: {conversation.id})\n")

agent_reference = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

# Conversation history for context (client-side tracking)
conversation_history = []


def create_response():
    return openai_client.responses.create(
        conversation=conversation.id,
        extra_body=agent_reference,
        input="",
    )


def request_approvals(approval_requests) -> list[dict]:
    """Prompt the user to approve or deny each MCP tool call."""
    approval_items = []
    for approval_request in approval_requests:
        print(f"[Approval required for: {approval_request.name}]\n")
        print(f"Server: {approval_request.server_label}")

        try:
            args = json.loads(approval_request.arguments)
            print(f"Arguments: {json.dumps(args, indent=2)}\n")
        except Exception:
            print(f"Arguments: {approval_request.arguments}\n")

        approval_input = input("Approve this action? (yes/no): ").strip().lower()
        approved = approval_input in ["yes", "y"]
        print("Approving action...\n" if approved else "Action denied.\n")

        approval_items.append(
            {
                "type": "mcp_approval_response",
                "approval_request_id": approval_request.id,
                "approve": approved,
            }
        )
    return approval_items


def send_message_to_agent(user_message):
    """
    Send a message to the agent and handle the response using the conversations API.
    """
    try:
        print("\nAgent: ", end="", flush=True)

        openai_client.conversations.items.create(
            conversation_id=conversation.id,
            items=[{"type": "message", "role": "user", "content": user_message}],
        )
        conversation_history.append({"role": "user", "content": user_message})

        response = create_response()

        # Loop until a response has no pending approval requests (zero, one, or many)
        while True:
            approval_requests = [
                item
                for item in (getattr(response, "output", None) or [])
                if getattr(item, "type", None) == "mcp_approval_request"
            ]
            if not approval_requests:
                break

            openai_client.conversations.items.create(
                conversation_id=conversation.id,
                items=request_approvals(approval_requests),
            )
            response = create_response()

        if response and response.output_text:
            response_text = response.output_text

            print(f"{response_text}\n")

            if hasattr(response, "citations") and response.citations:
                print("\nSources:")
                for citation in response.citations:
                    print(
                        f"  - {citation.content if hasattr(citation, 'content') else 'Knowledge Base'}"
                    )

            conversation_history.append({"role": "assistant", "content": response_text})

            return response_text
        else:
            print("No response received.\n")
            return None
    except Exception as e:
        print(f"\n\nError: {str(e)}\n")
        return None


def display_conversation_history():
    """
    Display the full conversation history.
    """
    print("\n" + "=" * 60)
    print("CONVERSATION HISTORY")
    print("=" * 60 + "\n")

    for turn in conversation_history:
        role = turn["role"].upper()
        content = turn["content"]
        print(f"{role}: {content}\n")

    print("=" * 60 + "\n")


def main():
    """
    Main interaction loop.
    """
    print("Contoso Product Expert Agent")
    print("Ask questions about our outdoor and camping products.")
    print("Type 'history' to see conversation history, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\nEnding conversation...")
                break

            if user_input.lower() == "history":
                display_conversation_history()
                continue

            send_message_to_agent(user_input)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}\n")

    print("\nConversation ended.")


if __name__ == "__main__":
    main()
