import os
from typing import Generator
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

# ChromaDB Client
# Using persistent storage in the backend directory for now
CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")

def get_chroma_client():
    """
    Get or create a ChromaDB client.
    """
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client

def get_vector_store():
    """
    Get the specific collection for TruthScan.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="truthscan_vectors")
    return collection

# PostgreSQL Connection (Placeholder for now, using Chroma primarily for RAG)
# In a full prod setup, we'd use SQLAlchemy or Tortoise-ORM here.
# For this phase, we'll focus on the Vector DB for the AI agents.
def get_db():
    """
    Dependency for getting DB session.
    """
    # TODO: Implement SQLAlchemy session
    pass
