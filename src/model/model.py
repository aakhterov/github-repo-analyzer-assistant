import asyncio
import chardet
import logging
from typing import List, Dict

from src.config import Configuration
from src.interfaces.model import IModel
from src.interfaces.vectordb import IVectorDB
from src.interfaces.assistant import IAssistant
from src.interfaces.database import IDatabase
from src.model.utils.async_helper import adownload_file
from src.model.core.splitter import smart_splitter
from src.model.utils.utils import (
    get_repo_metadata,
    get_branch_sha,
    get_repo_tree,
    build_metadata
)


class Model(IModel):
    """
    A model class that handles GitHub repository processing and AI assistant conversations.

    This class provides functionality to:
    - Process GitHub repositories by downloading and indexing files
    - Create and manage AI assistants
    - Manage conversation threads
    - Handle asynchronous file processing
    - Interface with vector and traditional databases

    The class implements the IModel interface and coordinates between vector database,
    AI assistant, and database components to provide a complete repository analysis
    and conversation system.

    Attributes:
        configuration (Configuration): Configuration settings for the model
        vectordb (IVectorDB): Vector database interface for document storage
        assistant (IAssistant): AI assistant interface for conversations
        db (IDatabase): Database interface for metadata storage
    """

    def __init__(self,
                 configuration: Configuration,
                 vectordb: IVectorDB,
                 assistant: IAssistant,
                 db: IDatabase
                 ):
        self.configuration = configuration
        self.vectordb = vectordb
        self.assistant = assistant
        self.db = db

    async def __aprocess_file(self, user: str, repo: str, branch: str, path_to_file: str, metadata: Dict) -> str:
        """
        Process a single file from a GitHub repository asynchronously.

        Downloads the file content, detects encoding, splits into chunks and adds to vector database.

        Args:
            user (str): GitHub username/organization
            repo (str): Repository name
            branch (str): Branch name
            path_to_file (str): Path to file within repository
            metadata (Dict): Metadata dictionary to attach to documents

        Returns:
            str: Status message indicating success or failure
                Format: "{path_to_file}: OK" on success
                        "{path_to_file}: Skipped ({error})" on failure

        Raises:
            Exception: If any error occurs during processing, exception is caught and status message returned
        """
        try:
            data = await adownload_file(user, repo, branch, path_to_file)
            encoding = chardet.detect(data)
            content = data.decode(encoding['encoding'])
            metadata["filename"] = path_to_file
            # Add a hash calculation for the updating purpose TODO
            docs = smart_splitter(content, metadata, **self.configuration.splitter)

            logging.info(f"{path_to_file} - {len(docs)} chunks")

            _ = await self.vectordb.aadd_docs(docs)

            logging.info(f"{path_to_file}: OK")
            return f"{path_to_file}: OK"
        except Exception as e:
            logging.info(f"{path_to_file}: Skipped ({e})")
            return f"{path_to_file}: Skipped ({e})"

    async def __aprocess_repo_files(self, user: str, repo: str, branch: str, paths: List[str], metadata: Dict) -> List[str]:
        """
        Process multiple files from a GitHub repository asynchronously.

        Creates concurrent tasks to process each file in the paths list and gathers results.

        Args:
            user (str): GitHub username/organization
            repo (str): Repository name
            branch (str): Branch name
            paths (List[str]): List of file paths to process
            metadata (Dict): Metadata dictionary to attach to documents

        Returns:
            List[str]: List of status messages for each processed file
                Format: ["{path}: OK", "{path}: Skipped ({error})", ...]
        """
        tasks = [self.__aprocess_file(user, repo, branch, path, metadata) for path in paths]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def create_repo_and_thread(self, assistant_id: str, user: str, repo: str) -> Dict:
        """
        Creates or retrieves repository and conversation thread for a GitHub repository.

        This method checks if a repository already exists in the database. If it does,
        retrieves the existing thread_id and repo_id. If not, creates a new thread and
        repository entry. In both cases, creates a vector database collection.

        Args:
            assistant_id (str): ID of the assistant to associate with the repository
            user (str): GitHub username/organization that owns the repository
            repo (str): Name of the GitHub repository

        Returns:
            Dict: Dictionary containing:
                - repo_id: ID of the repository in the database
                - thread_id: ID of the conversation thread
        """
        existed_repo = self.db.get_repo_by_owner_and_repo_name(user, repo)

        if existed_repo:
            thread_id = existed_repo.get("thread_id")
            repo_id = existed_repo.get("repo_id")
            collection_name = existed_repo.get("collection_name")
            self.db.update_repo_status_by_id(repo_id, "processing")
        else:
            thread_id = self.assistant.create_thread()
            collection_name = f"{user}_{repo}"

            self.db.create_thread(thread_id, "completed")
            repo_id = self.db.create_repo(
                owner=user,
                name=repo,
                collection=collection_name,
                assistant_id=assistant_id,
                thread_id=thread_id,
                status="processing"
            )

        self.vectordb.create_collection(collection_name)

        output = {
            "repo_id": repo_id,
            "thread_id": thread_id
        }
        return output

    def process_repo(self, user: str, repo: str, repo_id: str):
        """
        Process a GitHub repository by downloading and indexing its files.

        This method performs the following steps:
        1. Retrieves repository metadata and default branch
        2. Gets the SHA hash of the default branch
        3. Gets the repository file tree
        4. Downloads and processes each file in the repository
        5. Updates the repository status when complete

        Args:
            user (str): GitHub username/organization that owns the repository
            repo (str): Name of the GitHub repository
            repo_id (str): Database ID of the repository record

        Returns:
            None
        """
        logging.info(f"Getting repo metadata (owner: {user}, repo: {repo})...")
        metadata = get_repo_metadata(user, repo)
        default_branch = metadata.get("default_branch")
        logging.info(f"Default branch is '{default_branch}' (owner: {user}, repo: {repo})")

        logging.info(f"Getting an SHA of the branch '{default_branch}'  (owner: {user}, repo: {repo})...")
        branch_sha = get_branch_sha(user, repo, default_branch)

        logging.info(f"Getting a tree from the branch '{default_branch}'  (owner: {user}, repo: {repo})...")
        tree = get_repo_tree(user, repo, branch_sha)

        paths = [file.get("path") for file in tree.get("tree", []) if file.get("type") == "blob"]
        metadata = build_metadata(metadata)

        self.vectordb.reset_collection()

        logging.info(f"Processing {len(paths)} files...")
        _ = asyncio.run(self.__aprocess_repo_files(user, repo, default_branch, paths, metadata))

        self.db.update_repo_status_by_id(repo_id, "completed")
        logging.info(f"Files have been processed")

    def create_assistant(self, name: str) -> str:
        """
        Creates a new assistant or retrieves an existing one by name.

        This method checks if an assistant with the given name already exists in the database.
        If it does not exist, creates a new assistant and stores it in the database.
        If it exists, retrieves the existing assistant's ID.

        Args:
            name (str): Name of the assistant to create or retrieve

        Returns:
            str: ID of the created or existing assistant
        """
        assistant_id = self.db.get_assistant_id_by_name(name)

        if not assistant_id:
            assistant_id = self.assistant.create_assistant(name)
            self.db.create_assistant(assistant_id, name)

        return assistant_id

    def make_conversation(self, user_message: str, assistant_id: str, conversation_thread_id: str) -> str:
        """
        Creates a conversation with an AI assistant using the provided message and thread.

        This method performs the following steps:
        1. Verifies the repository status is 'completed'
        2. Updates the thread status to 'processing'
        3. Creates a vector database collection for the conversation
        4. Makes the conversation with the assistant
        5. Updates the thread status to 'completed' with the AI message ID

        Args:
            user_message (str): The message from the user to send to the assistant
            assistant_id (str): ID of the AI assistant to converse with
            conversation_thread_id (str): ID of the conversation thread

        Returns:
            str: The ID of the AI assistant's response message

        Raises:
            ValueError: If the repository status is not 'completed'
        """
        repo_status = self.db.get_repo_status_by_thread_id(conversation_thread_id)
        if repo_status != "completed":
            raise ValueError("The repository is not ready yet. Its status should be 'completed'. "
                             "Check the repo status using an appropriate request.")

        self.db.update_thread_status_and_ai_message_id_by_id(conversation_thread_id, "processing", "")

        collection_name = self.db.get_col_name_by_assist_id_and_thread_id(assistant_id, conversation_thread_id)
        self.vectordb.create_collection(collection_name)

        ai_message_id = self.assistant.make_conversation(
            user_message=user_message,
            assistant_id=assistant_id,
            conversation_thread_id=conversation_thread_id
        )

        self.db.update_thread_status_and_ai_message_id_by_id(
            thread_id=conversation_thread_id,
            status="completed",
            ai_message_id=ai_message_id
        )

        return ai_message_id

    def get_conversation_result(self, conversation_thread_id: str) -> Dict:
        """
        Retrieves the result of a conversation with the AI assistant.

        This method performs the following steps:
        1. Gets the thread data from the database using the conversation thread ID
        2. Creates a result dictionary with the thread status
        3. If the thread status is 'completed', retrieves the assistant's message
           and adds it to the result

        Args:
            conversation_thread_id (str): ID of the conversation thread to get results for

        Returns:
            Dict: - status (str): Status of the conversation thread
                  - message (str): Assistant's response message (only if status is 'completed')
        """
        thread_data = self.db.get_thread_data_by_id(conversation_thread_id)

        result = {
            "status": thread_data.get("status")
        }

        if thread_data.get("status") == "completed":
            message = self.assistant.get_conversation_result(
                conversation_thread_id=conversation_thread_id,
                ai_message_id=thread_data.get("ai_message_id")
            )
            result["message"] = message

        return result

    def get_repo_result(self, thread_id: str) -> Dict:
        """
        Retrieves the processing status of a GitHub repository.

        This method gets the current status of repository processing from the database
        using the conversation thread ID.

        Args:
            thread_id (str): ID of the conversation thread associated with the repository

        Returns:
            Dict: - status (str): Current status of repository processing ('processing' or 'completed')
        """

        status = self.db.get_repo_status_by_thread_id(thread_id)

        return {
            "status": status
        }