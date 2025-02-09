from abc import ABC, abstractmethod
from typing import Union, Dict


class IDatabase(ABC):
    """Interface for database operations.

    This abstract base class defines the interface for database operations related to
    assistants, repositories, and threads. It provides methods for creating, retrieving
    and updating database records.

    Methods:
        create_assistant: Creates a new assistant record
        create_repo: Creates a new repository record
        create_thread: Creates a new thread record
        get_assistant_id_by_name: Retrieves assistant ID by name
        get_repo_status_by_thread_id: Gets repository status by thread ID
        get_repo_by_owner_and_repo_name: Retrieves repository by owner and name
        get_col_name_by_assist_id_and_thread_id: Gets collection name by assistant and thread IDs
        get_thread_data_by_id: Retrieves thread data by ID
        update_repo_status_by_id: Updates repository status
        update_thread_status_and_ai_message_id_by_id: Updates thread status and message ID
    """

    @abstractmethod
    def create_assistant(self,
                         assistant_id: str,
                         name: str
                         ) -> str:
        raise NotImplementedError("Subclass must implement create_assistant method")

    @abstractmethod
    def create_repo(self,
                    owner: str,
                    name: str,
                    collection: str,
                    assistant_id: str,
                    thread_id: str,
                    status: str
                    ) -> str:
        raise NotImplementedError("Subclass must implement create_repo method")

    @abstractmethod
    def create_thread(self,
                      thread_id: str,
                      status: str
                      ) -> str:
        raise NotImplementedError("Subclass must implement create_thread method")

    @abstractmethod
    def get_assistant_id_by_name(self,
                                 name: str
                                 ) -> Union[str|None]:
        raise NotImplementedError("Subclass must implement get_assistant_id_by_name method")

    @abstractmethod
    def get_repo_status_by_thread_id(self,
                                     thread_id: str
                                     ) -> Union[str|None]:
        raise NotImplementedError("Subclass must implement get_repo_status_by_thread_id method")

    @abstractmethod
    def get_repo_by_owner_and_repo_name(self,
                                        owner: str,
                                        repo_name: str
                                        ) -> Union[Dict|None]:
        raise NotImplementedError("Subclass must implement get_repo_by_owner_and_repo_name method")

    @abstractmethod
    def get_col_name_by_assist_id_and_thread_id(self,
                                                assistant_id: str,
                                                thread_id: str
                                                ) -> Union[str|None]:
        raise NotImplementedError("Subclass must implement get_col_name_by_assist_id_and_thread_id method")

    @abstractmethod
    def get_thread_data_by_id(self,
                              thread_id: str
                              ) -> Union[Dict|None]:
        raise NotImplementedError("Subclass must implement get_thread_data_by_id method")

    @abstractmethod
    def update_repo_status_by_id(self,
                                 repo_id: str,
                                 status: str
                                 ):
        raise NotImplementedError("Subclass must implement update_repo_status_by_id method")

    @abstractmethod
    def update_thread_status_and_ai_message_id_by_id(self,
                                                     thread_id: str,
                                                     status: str,
                                                     ai_message_id: str
                                                     ):
        raise NotImplementedError("Subclass must implement update_thread_status_and_ai_message_id_by_id method")