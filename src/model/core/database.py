import os
import sqlite3
from uuid import uuid4
from typing import Union, Dict

from src.config import Configuration
from src.interfaces.database import IDatabase

DEFAULT_DB_NAME = "assistants.sqlite3"
ASSISTANTS_TABLE = "assistants"
REPOS_TABLE = "repos"
THREADS_TABLE = "threads"

class SQLite(IDatabase):
    """
    SQLite is a database handler implementation that manages interactions
    with a SQLite database file. It sets up and manipulates the database
    according to the system's requirements, providing methods to create,
    retrieve, and update records for assistants, threads, and repositories.

    Attributes:
        configuration (Configuration): Configuration object providing database setup details.
        db_name (str): The name of the database, fetched from configuration or using a default.
        db_path (str): The full path to the SQLite database file.

    Methods:
        initialization(): Initializes the SQLite database by creating necessary tables if they don't exist.
        create_assistant(assistant_id, name): Inserts a new assistant record into the database.
        create_repo(owner, name, collection, assistant_id, thread_id, status): Inserts a new repository record into the database.
        create_thread(thread_id, status): Inserts a new thread record into the database.
        get_assistant_id_by_name(name): Retrieves assistant_id based on assistant name.
        get_repo_status_by_thread_id(thread_id): Retrieves repository status based on thread_id.
        get_repo_by_owner_and_repo_name(owner, repo_name): Retrieves repository information based on owner and repo name.
        get_col_name_by_assist_id_and_thread_id(assistant_id, thread_id): Retrieves collection name based on assistant_id and thread_id.
        get_thread_data_by_id(thread_id): Retrieves thread data (status and ai_message_id) based on thread_id.
        update_repo_status_by_id(repo_id, status): Updates the status of a repository based on its ID.
        update_thread_status_and_ai_message_id_by_id(thread_id, status, ai_message_id): Updates both the status and
        ai_message_id of a thread based on its ID.
    """
    def __init__(self, configuration: Configuration, db_path):
        self.configuration = configuration
        self.db_name = self.configuration.database.get('db_name', DEFAULT_DB_NAME)
        self.db_path =  os.path.join(db_path, self.db_name)
        self.initialization()

    def initialization(self):
        """
        Initialize the SQLite database by creating required tables if they don't exist.

        Creates three tables:
        - assistants: Stores assistant information with ID and name
        - threads: Stores thread information with ID, status and AI message ID
        - repos: Stores repository information including owner, name, collection,
          and foreign key references to assistants and threads

        Tables are created with appropriate columns and constraints including primary
        and foreign keys.

        :return: None
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {ASSISTANTS_TABLE} 
            (
            assistant_id VARCHAR(255) PRIMARY KEY, 
            name VARCHAR(255)
            )
            """)

            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {THREADS_TABLE} 
            (
            thread_id VARCHAR(255) PRIMARY KEY,
            status VARCHAR(255),      
            ai_message_id VARCHAR(255)      
            )
            """)

            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {REPOS_TABLE} 
            (
            id VARCHAR(36) PRIMARY KEY, 
            owner VARCHAR(255),
            name VARCHAR(255),
            collection VARCHAR(255),
            assistant_id VARCHAR(255), 
            thread_id VARCHAR(255),
            status VARCHAR(255),
            FOREIGN KEY(assistant_id) REFERENCES {ASSISTANTS_TABLE}(assistant_id)
            FOREIGN KEY(thread_id) REFERENCES {REPOS_TABLE}(thread_id)                
            )
            """)

    def create_assistant(self,
                         assistant_id: str,
                         name: str
                         ) -> str:
        """
        Creates a new assistant record in the database.

        Inserts a new row into the assistants table with the provided assistant ID and name.

        Args:
            assistant_id (str): Unique identifier for the assistant
            name (str): Name of the assistant

        Returns:
            str: The assistant_id that was inserted

        Raises:
            Exception: If the database insert operation fails
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"INSERT INTO {ASSISTANTS_TABLE} (assistant_id, name) VALUES (?, ?)",
                    (assistant_id, name)
                )
            except Exception as e:
                raise Exception(f"Failed to insert data into {ASSISTANTS_TABLE} table: {e}")

        return assistant_id

    def create_repo(self,
                    owner: str,
                    name: str,
                    collection: str,
                    assistant_id: str,
                    thread_id: str,
                    status: str
                    ) -> str:
        """
        Creates a new repository record in the database.

        Inserts a new row into the repos table with the provided repository information.
        Generates a new UUID for the repository ID.

        Args:
            owner (str): Owner/username of the repository
            name (str): Name of the repository
            collection (str): Collection name associated with the repository
            assistant_id (str): ID of the associated assistant
            thread_id (str): ID of the associated thread
            status (str): Current status of the repository

        Returns:
            str: The generated repository ID that was inserted

        Raises:
            Exception: If the database insert operation fails
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            try:
                result = cursor.execute(
                    f"INSERT INTO {REPOS_TABLE} (id, owner, name, collection, assistant_id, thread_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (id:=str(uuid4()), owner, name, collection, assistant_id, thread_id, status)
                )
            except Exception as e:
                raise Exception(f"Failed to insert data into {REPOS_TABLE} table: {e}")

        return id

    def create_thread(self,
                      thread_id: str,
                      status: str
                      ) -> str:
        """
        Creates a new thread record in the database.

        Inserts a new row into the threads table with the provided thread ID and status.
        The ai_message_id field is initialized as empty.

        Args:
            thread_id (str): Unique identifier for the thread
            status (str): Initial status of the thread

        Returns:
            str: The thread_id that was inserted

        Raises:
            Exception: If the database insert operation fails
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            try:
                result = cursor.execute(
                    f"INSERT INTO {THREADS_TABLE} (thread_id, status, ai_message_id) VALUES (?, ?, ?)",
                    (thread_id, status, "")
                )
            except Exception as e:
                raise Exception(f"Failed to insert data into {THREADS_TABLE} table: {e}")

        return thread_id

    def get_assistant_id_by_name(self, name: str) -> Union[str|None]:
        """
        Retrieves the assistant ID from the database based on the assistant name.

        Queries the assistants table to find the assistant_id that matches the provided name.

        Args:
            name (str): Name of the assistant to look up

        Returns:
            Union[str|None]: The assistant_id if found, None if no matching assistant exists

        Raises:
            Exception: If there is an error executing the database query
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            result = cursor.execute(
                f"SELECT assistant_id FROM {ASSISTANTS_TABLE} WHERE name = '{name}'"
            ).fetchone()

            if result:
                return result[0]

            return None

    def get_repo_status_by_thread_id(self,
                                     thread_id: str
                                     ) -> Union[str|None]:
        """
        Retrieves the status of a repository from the database based on its thread ID.

        Queries the repos table to find the status field that matches the provided thread_id.

        Args:
            thread_id (str): Thread ID to look up the repository status for

        Returns:
            Union[str|None]: The repository status if found, None if no matching repository exists

        Raises:
            Exception: If there is an error executing the database query
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            result = cursor.execute(
                f"SELECT status FROM {REPOS_TABLE} WHERE thread_id = '{thread_id}'"
            ).fetchone()

            if result:
                return result[0]

            return None

    def get_repo_by_owner_and_repo_name(self,
                                        owner: str,
                                        repo_name: str
                                        ) -> Union[Dict|None]:
        """
        Retrieves repository information from the database based on owner and repository name.

        Queries the repos table to find a repository matching the provided owner and name.

        Args:
            owner (str): Owner/username of the repository to look up
            repo_name (str): Name of the repository to look up

        Returns:
            Union[Dict|None]: Dictionary containing repository information if found:
                - repo_id (str): Unique identifier of the repository
                - collection_name (str): Name of the collection associated with the repository
                - thread_id (str): ID of the thread associated with the repository
                Returns None if no matching repository exists

        Raises:
            Exception: If there is an error executing the database query
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            result = cursor.execute(
                f"SELECT * FROM {REPOS_TABLE} WHERE (owner = '{owner}') AND (name = '{repo_name}') "
            ).fetchone()

            if result:
                return {
                    "repo_id": result[0],
                    "collection_name": result[3],
                    "thread_id": result[5]
                }

            return None

    def get_col_name_by_assist_id_and_thread_id(self,
                                                assistant_id: str,
                                                thread_id: str
                                                ) -> Union[str|None]:
        """
        Retrieves the collection name from the database based on assistant ID and thread ID.

        Queries the repos table to find the collection field that matches the provided assistant_id
        and thread_id combination.

        Args:
            assistant_id (str): ID of the assistant to look up
            thread_id (str): ID of the thread to look up

        Returns:
            Union[str|None]: The collection name if found, None if no matching repository exists

        Raises:
            Exception: If there is an error executing the database query
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            result = cursor.execute(
                f"SELECT collection FROM {REPOS_TABLE} WHERE (assistant_id = '{assistant_id}') AND (thread_id = '{thread_id}') "
            ).fetchone()

            if result:
                return result[0]

            return None

    def get_thread_data_by_id(self,
                              thread_id: str
                              ) -> Union[Dict|None]:
        """
        Retrieves thread data from the database based on the thread ID.

        Queries the threads table to find the status and AI message ID that matches
        the provided thread_id.

        Args:
            thread_id (str): ID of the thread to look up

        Returns:
            Union[Dict|None]: Dictionary containing thread information if found:
                - status (str): Current status of the thread
                - ai_message_id (str): ID of the AI message associated with the thread
                Returns None if no matching thread exists

        Raises:
            Exception: If there is an error executing the database query
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            result = cursor.execute(
                f"SELECT status, ai_message_id FROM {THREADS_TABLE} WHERE thread_id = '{thread_id}'"
            ).fetchone()

            if result:
                return {
                    "status": result[0],
                    "ai_message_id": result[1]
                }

            return None

    def update_repo_status_by_id(self,
                                 repo_id: str,
                                 status: str
                                 ):
        """
        Updates the status of a repository in the database based on its ID.

        Updates the status field in the repos table for the repository matching the provided ID.

        Args:
            repo_id (str): Unique identifier of the repository to update
            status (str): New status value to set for the repository

        Raises:
            Exception: If there is an error executing the database update
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"UPDATE {REPOS_TABLE} SET status = '{status}' WHERE id='{repo_id}'"
            )

    def update_thread_status_and_ai_message_id_by_id(self,
                                                     thread_id: str,
                                                     status: str,
                                                     ai_message_id: str
                                                     ):
        """
        Updates the status and AI message ID of a thread in the database based on its ID.
        :param thread_id:

        :param status:
        Updates both the status and ai_message_id fields in the threads table for the thread
        :param ai_message_id:
        matching the provided thread_id.
        :return:

        Args:
            thread_id (str): ID of the thread to update
            status (str): New status value to set for the thread
            ai_message_id (str): New AI message ID value to set for the thread

        Raises:
            Exception: If there is an error executing the database update
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"UPDATE {THREADS_TABLE} SET status = '{status}', ai_message_id = '{ai_message_id}' WHERE thread_id='{thread_id}'"
            )

