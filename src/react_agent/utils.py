"""Utility & helper functions."""
import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
import numpy as np
from dotenv import load_dotenv
import logging
from openai import AzureOpenAI
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from langgraph.store.postgres import PostgresStore
from psycopg import Connection
from lightrag.kg.shared_storage import initialize_pipeline_status

logging.basicConfig(level=logging.INFO)

load_dotenv()

AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION")
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")

WORKING_DIR = "./intellidesign"
DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable"
EMBEDDINGS_DIMENSION = 1536

def get_llm():
    return AzureChatOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        api_version=AZURE_OPENAI_API_VERSION
    )

def get_embeddings():
    return AzureOpenAIEmbeddings(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_EMBEDDING_ENDPOINT,
        azure_deployment=AZURE_EMBEDDING_DEPLOYMENT,
        api_version=AZURE_EMBEDDING_API_VERSION
    )

async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT, 
        messages=messages,
        temperature=kwargs.get("temperature", 0),
        top_p=kwargs.get("top_p", 1),
        n=kwargs.get("n", 1),
    )
    return chat_completion.choices[0].message.content


async def embedding_func(texts: list[str]) -> np.ndarray:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_EMBEDDING_API_VERSION,
        azure_endpoint=AZURE_EMBEDDING_ENDPOINT,
    )
    embedding = client.embeddings.create(model=AZURE_EMBEDDING_DEPLOYMENT, input=texts)

    embeddings = [item.embedding for item in embedding.data]
    return np.array(embeddings)

def load_postgres_store():
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }

    conn = Connection.connect(DB_URI, **connection_kwargs)

    postgres_store = PostgresStore(
        conn,
        index={
            "dims": EMBEDDINGS_DIMENSION,
            "embed": get_embeddings()
        }
    )
    postgres_store.setup()
    return postgres_store

async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDINGS_DIMENSION,
            max_token_size=8192,
            func=embedding_func,
        ),
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

def load_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDINGS_DIMENSION,
            max_token_size=8192,
            func=embedding_func,
        ),
    )
    return rag

def data_formatter(data):
    """
    Converts a list of dictionaries with 'namespace', 'date', and 'contents'
    keys into a structured string for LLM parsing.

    Parameters:
        data_list (list): A list of dictionaries. Each dictionary should have
                          the keys 'namespace', 'date', and 'contents', where
                          'contents' is a string.

    Returns:
        str: A structured string with the formatted data.
    """
    formatted_entries = []
    
    for entry in data:
        namespace = entry.get("namespace", "N/A")
        date = entry.get("date", "N/A")
        contents = entry.get("content", "N/A")
        
        # Format each entry as a structured block
        formatted_entry = (
            f"Namespace: {namespace}\n"
            f"Date: {date}\n"
            "Contents:\n"
            f"{contents}\n"
        )
        formatted_entries.append(formatted_entry)
    
    # Combine all entries with a separating newline between each entry
    return "\n".join(formatted_entries)

def get_episodic_memory(namespace, instructions, data, store):
        similar = store.search(
            ("episodes", namespace),
            query=f"Instructions: {instructions}\n\nData:\n{data}",
            limit=1,
        )

        # Step 2: Build system message with relevant experience
        episodic_memory = "" 
        if similar:
            episodic_memory += "\n\n### EPISODIC MEMORY:"
            for i, item in enumerate(similar, start=1):
                episode = item.value["content"]
                episodic_memory += f"""
                    Episode {i}:
                    When: {episode['observation']}
                    Thought: {episode['thoughts']}
                    Did: {episode['action']}
                    Result: {episode['result']}
                """
        return episodic_memory