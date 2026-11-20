"""
Configures the Foundry IQ knowledge base in Azure AI Search.

Uploads the product PDFs to blob storage, then creates (or updates) an Azure
Blob knowledge source and a knowledge base that uses it. Search ingests the
documents (chunking + embeddings) into a generated index.

Uses API keys (demo shortcut, no role assignments needed). Keyless access with
managed identities and RBAC is preferred for production.

Configuration is loaded from .env file, with CLI arguments as overrides.

Prerequisites:
  - Resources deployed via 001-deploy-search/main.bicep
  - pip install -r requirements.txt
  - .env with SEARCH_ENDPOINT, SEARCH_API_KEY, STORAGE_CONNECTION_STRING,
    FOUNDRY_OPENAI_ENDPOINT, FOUNDRY_API_KEY (see main.bicep for az commands)
  - Optional CHAT_DEPLOYMENT / CHAT_MODEL for knowledge base query planning
    (model must be supported by Foundry IQ, e.g. gpt-5-mini)

Usage:
  python configure_knowledge_base.py [--files <file> ...] [--skip-upload]
                                     [--timeout <seconds>]

Examples:
  python configure_knowledge_base.py
  python configure_knowledge_base.py --skip-upload
  python configure_knowledge_base.py --files data/contoso-tents-catalog.pdf
"""

import argparse
import glob
import os
import time

from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureBlobKnowledgeSource,
    AzureBlobKnowledgeSourceParameters,
    AzureOpenAIVectorizerParameters,
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeSourceContentExtractionMode,
    KnowledgeSourceReference,
)
from azure.search.documents.knowledgebases.models import (
    KnowledgeRetrievalLowReasoningEffort,
    KnowledgeRetrievalMinimalReasoningEffort,
    KnowledgeRetrievalOutputMode,
    KnowledgeSourceAzureOpenAIVectorizer,
    KnowledgeSourceIngestionParameters,
)
from azure.storage.blob import BlobServiceClient

# Load environment variables from .env file
load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} not set in .env.")
    return value


def upload_files(connection_string: str, container_name: str, file_paths: list[str]):
    """Upload files to the blob container (overwrites existing blobs)."""
    if not file_paths:
        print("ℹ No files to upload")
        return

    service = BlobServiceClient.from_connection_string(connection_string)
    container = service.get_container_client(container_name)
    if not container.exists():
        container.create_container()
        print(f"✓ Container created: {container_name}")

    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "rb") as f:
            container.upload_blob(os.path.basename(file_path), f, overwrite=True)
        print(f"✓ Uploaded: {file_path}")

    print(f"✓ {len(file_paths)} file(s) in container '{container_name}'")


def openai_parameters(
    endpoint: str, api_key: str, deployment: str, model: str
) -> AzureOpenAIVectorizerParameters:
    return AzureOpenAIVectorizerParameters(
        resource_url=endpoint,
        deployment_name=deployment,
        api_key=api_key,
        model_name=model,
    )


def configure_knowledge_source(
    index_client: SearchIndexClient,
    name: str,
    connection_string: str,
    container_name: str,
    embedding: AzureOpenAIVectorizerParameters,
    chat: AzureOpenAIVectorizerParameters | None,
):
    ingestion = KnowledgeSourceIngestionParameters(
        embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
            azure_open_ai_parameters=embedding
        ),
        chat_completion_model=(
            KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=chat)
            if chat
            else None
        ),
        content_extraction_mode=KnowledgeSourceContentExtractionMode.MINIMAL,
        disable_image_verbalization=True,
    )
    source = AzureBlobKnowledgeSource(
        name=name,
        description="Contoso outdoor and camping product catalogs (PDF).",
        azure_blob_parameters=AzureBlobKnowledgeSourceParameters(
            connection_string=connection_string,
            container_name=container_name,
            is_adls_gen2=False,
            ingestion_parameters=ingestion,
        ),
    )
    index_client.create_or_update_knowledge_source(source)
    print(f"✓ Knowledge source configured: {name}")


def configure_knowledge_base(
    index_client: SearchIndexClient,
    name: str,
    source_name: str,
    chat: AzureOpenAIVectorizerParameters | None,
):
    # Without a chat model the knowledge base can only do minimal reasoning
    # (no query planning) and return extracted data rather than synthesized answers.
    if chat:
        models = [KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=chat)]
        reasoning = KnowledgeRetrievalLowReasoningEffort()
    else:
        models = None
        reasoning = KnowledgeRetrievalMinimalReasoningEffort()

    knowledge_base = KnowledgeBase(
        name=name,
        description="Contoso product information for the product expert agent.",
        knowledge_sources=[KnowledgeSourceReference(name=source_name)],
        models=models,
        retrieval_reasoning_effort=reasoning,
        output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
    )
    index_client.create_or_update_knowledge_base(knowledge_base)
    print(f"✓ Knowledge base configured: {name}")
    print(f"  Reasoning effort: {reasoning.kind}")


def wait_for_ingestion(index_client: SearchIndexClient, source_name: str, timeout: int):
    """Poll until the knowledge source has completed a synchronization run."""
    print("Waiting for ingestion...")
    deadline = time.monotonic() + timeout
    while True:
        status = index_client.get_knowledge_source_status(source_name)
        last = status.last_synchronization_state
        if last and not status.current_synchronization_state:
            print(
                f"✓ Ingestion complete: {last.items_updates_processed} processed, "
                f"{last.items_updates_failed} failed, {last.items_skipped} skipped"
            )
            return
        if time.monotonic() > deadline:
            print(
                f"⚠ Ingestion still running after {timeout}s "
                f"(status: {status.synchronization_status}); check again later."
            )
            return
        time.sleep(10)


def main():
    parser = argparse.ArgumentParser(
        description="Configure the Foundry IQ knowledge base in Azure AI Search"
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=sorted(glob.glob("data/*.pdf")),
        help="Files to upload (default: data/*.pdf).",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        default=False,
        help="Skip uploading files to blob storage",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Seconds to wait for ingestion to complete (default: 600)",
    )
    args = parser.parse_args()

    search_endpoint = require_env("SEARCH_ENDPOINT")
    search_api_key = require_env("SEARCH_API_KEY")
    connection_string = require_env("STORAGE_CONNECTION_STRING")
    foundry_endpoint = require_env("FOUNDRY_OPENAI_ENDPOINT")
    foundry_api_key = require_env("FOUNDRY_API_KEY")
    container_name = os.getenv("STORAGE_CONTAINER", "contosoproducts")
    source_name = os.getenv("KNOWLEDGE_SOURCE_NAME", "ks-contosoproducts")
    base_name = os.getenv("KNOWLEDGE_BASE_NAME", "kb-contosoproducts")

    embedding = openai_parameters(
        foundry_endpoint,
        foundry_api_key,
        os.getenv("EMBEDDING_DEPLOYMENT", "text-embedding-3-small-dev-001"),
        os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    chat_deployment = os.getenv("CHAT_DEPLOYMENT")
    chat = (
        openai_parameters(
            foundry_endpoint,
            foundry_api_key,
            chat_deployment,
            require_env("CHAT_MODEL"),
        )
        if chat_deployment
        else None
    )

    if not args.skip_upload:
        upload_files(connection_string, container_name, args.files)

    index_client = SearchIndexClient(
        endpoint=search_endpoint, credential=AzureKeyCredential(search_api_key)
    )

    configure_knowledge_source(
        index_client, source_name, connection_string, container_name, embedding, chat
    )
    configure_knowledge_base(index_client, base_name, source_name, chat)
    wait_for_ingestion(index_client, source_name, args.timeout)


if __name__ == "__main__":
    main()
