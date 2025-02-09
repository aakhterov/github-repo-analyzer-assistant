import logging
from typing import List, Tuple, Dict
from uuid import uuid4
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.config import Configuration
from src.interfaces.vectordb import IVectorDB

logger = logging.getLogger()

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_K = 4
DEFAULT_SCORE_THRESHOLD = 0.5

class ChromaDB(IVectorDB):
    """
    ChromaDB class implements the IVectorDB interface to provide vector database functionality using Chroma.

    This class handles document storage, retrieval and similarity search using embeddings from OpenAI.
    It provides both synchronous and asynchronous methods for adding documents and supports configurable
    similarity search parameters.

    Attributes:
        configuration (Configuration): Configuration object containing model and vector store settings
        embeddings (OpenAIEmbeddings): OpenAI embeddings model instance
        vector_store (Chroma): Chroma vector store instance

    Note:
        - Uses OpenAI embeddings with configurable model (default: text-embedding-3-small)
        - Supports similarity search with configurable k and score threshold parameters
        - Persists data to disk in data/chroma_db directory
    """

    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self.embeddings = OpenAIEmbeddings(
            model=self.configuration.models.get("embedding", DEFAULT_EMBEDDING_MODEL)
        )
        self.vector_store = None

    def create_collection(self, collection_name: str):
        """
        Creates a new Chroma vector store collection with the specified name.

        Args:
            collection_name (str): Name of the collection to create

        Returns:
            None

        Note:
            The collection is initialized with the configured embeddings model and
            persisted to the data/chroma_db directory.
        """
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory="data/chroma_db",
        )

    async def aadd_docs(self, docs: List[Document]) -> List[str]:
        """
        Asynchronously adds documents to the vector store collection.

        Args:
            docs (List[Document]): List of Document objects to add to the vector store

        Returns:
            List[str]: List of unique IDs assigned to the added documents

        Note:
            - Generates UUID for each document
            - Uses async version of add_documents from the vector store
            - Logs confirmation message with filename from first document's metadata
        """
        uuids = [str(uuid4()) for _ in range(len(docs))]
        ids = await self.vector_store.aadd_documents(documents=docs, ids=uuids)
        logging.info(f"{docs[0].metadata.get('filename')}. Document has been added to the vector store")
        return ids

    def add_docs(self, docs: List[Document]) -> List[str]:
        """
        Synchronously adds documents to the vector store collection.

        Args:
            docs (List[Document]): List of Document objects to add to the vector store

        Returns:
            List[str]: List of unique IDs assigned to the added documents

        Note:
            - Generates UUID for each document
            - Uses synchronous version of add_documents from the vector store
            - Logs confirmation message with filename from first document's metadata
        """
        uuids = [str(uuid4()) for _ in range(len(docs))]
        ids = self.vector_store.add_documents(documents=docs, ids=uuids)
        logging.info(f"{docs[0].metadata.get('filename')}. Document has been added to the vector store")
        return ids

    def reset_collection(self):
        """
        Resets/clears all documents from the current vector store collection.

        This method removes all documents and their embeddings from the collection
        while maintaining the collection structure and configuration.

        Args:
            None

        Returns:
            None

        Note:
            This is a destructive operation that cannot be undone. Use with caution.
        """
        self.vector_store.reset_collection()

    def get_docs_with_score(self, query: str) -> List[Dict]:
        """
        Retrieves documents from the vector store that are semantically similar to the query.

        Args:
            query (str): The search query text to find similar documents for

        Returns:
            List[Dict]: List of dictionaries containing matched documents with their similarity scores.
                       Each dictionary has:
                       - content: The document text content
                       - metadata: Document metadata
                       - score: Similarity score between query and document

        Note:
            - Number of results limited by 'k' config parameter (default: 4)
            - Results filtered by 'score_threshold' config parameter (default: 0.5)
        """
        results = self.vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=self.configuration.vector_store.get("k", DEFAULT_K),
            score_threshold=self.configuration.vector_store.get("score_threshold", DEFAULT_SCORE_THRESHOLD)
        )

        return [
            {
                "content": res[0].page_content,
                "metadata": res[0].metadata,
                "score": res[1]
            } for res in results
        ]