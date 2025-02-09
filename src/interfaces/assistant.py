from abc import ABC, abstractmethod


class IAssistant(ABC):
    """Interface for AI Assistant implementations.

    This interface defines the core methods required for implementing an AI assistant.
    It provides functionality for creating assistants, managing conversation threads,
    conducting conversations and retrieving results.
    """

    @abstractmethod
    def create_assistant(self, name: str) -> str:
        raise NotImplementedError("Subclass must implement create_assistant method")

    @abstractmethod
    def create_thread(self) -> str:
        raise NotImplementedError("Subclass must implement create_thread method")

    @abstractmethod
    def make_conversation(self, user_message: str, **kwarg) -> str:
        raise NotImplementedError("Subclass must implement make_conversation method")

    @abstractmethod
    def get_conversation_result(self, **kwarg) -> str:
        raise NotImplementedError("Subclass must implement get_conversation_result method")