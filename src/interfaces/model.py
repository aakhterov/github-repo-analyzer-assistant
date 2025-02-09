from abc import ABC, abstractmethod
from typing import Dict


class IModel(ABC):
    """Interface for AI model interactions.

    This interface defines the contract for AI model implementations to handle:
    - Creating AI assistants
    - Managing repository analysis threads
    - Processing repositories
    - Conducting conversations
    - Retrieving conversation and repository analysis results
    """

    @abstractmethod
    def create_assistant(self, name: str) -> str:
        raise NotImplementedError("Subclass must implement create_assistance method")

    @abstractmethod
    def create_repo_and_thread(self, assistant_id: str, user: str, repo: str) -> Dict:
        raise NotImplementedError("Subclass must implement create_repo_and_thread method")

    @abstractmethod
    def process_repo(self, user: str, repo: str, repo_id: str):
        raise NotImplementedError("Subclasses must implement process_repo method")

    @abstractmethod
    def make_conversation(self, user_message: str, assistant_id: str, conversation_thread_id: str) -> str:
        raise NotImplementedError("Subclasses must implement make_conversation method")

    @abstractmethod
    def get_conversation_result(self, conversation_thread_id: str) -> Dict:
        raise NotImplementedError("Subclasses must implement make_conversation method")

    @abstractmethod
    def get_repo_result(self, thread_id: str) -> Dict:
        raise NotImplementedError("Subclasses must implement get_repo_result method")