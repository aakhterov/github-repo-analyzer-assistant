from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from langchain_core.documents import Document


class IVectorDB(ABC):
    """Interface for Vector Database operations.

    This interface defines the standard operations for managing document collections
    in a vector database, including creating collections, adding documents,
    resetting collections, and retrieving documents with similarity scores.

    Methods:
        create_collection(collection_name: str): Creates a new collection
        aadd_docs(docs: List[Document]) -> List[str]: Asynchronously adds documents
        add_docs(docs: List[Document]) -> List[str]: Adds documents
        reset_collection(): Resets/clears the current collection
        get_docs_with_score(query: str) -> List[Dict]: Retrieves similar documents with scores
    """

    @abstractmethod
    def create_collection(self, collection_name: str):
        raise NotImplementedError("Subclasses must implement create_collection method")

    @abstractmethod
    async def aadd_docs(self, docs: List[Document]) -> List[str]:
        raise NotImplementedError("Subclasses must implement aadd_docs method")

    @abstractmethod
    def add_docs(self, docs: List[Document]) -> List[str]:
        raise NotImplementedError("Subclasses must implement add_docs method")

    @abstractmethod
    def reset_collection(self):
        raise NotImplementedError("Subclasses must implement reset_collection method")

    @abstractmethod
    def get_docs_with_score(self, query: str) -> List[Dict]:
        raise NotImplementedError("Subclasses must implement get_docs_with_score method")