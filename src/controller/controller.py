import re
import logging
from typing import Tuple, Dict

from src.interfaces.model import IModel

logger = logging.getLogger()

GITHUB_URL_PATTERN = re.compile("^https:\/\/github.com\/\S+\/\S+\.git$") # e.g. https://github.com/aakhterov/github-repo-analyzer-assistant.git

class Controller:
    """
    Controller class that handles GitHub repository analysis and assistant conversations.

    This class provides methods for:
    - Validating and processing GitHub repository URLs
    - Creating and managing repository analysis threads
    - Creating assistants for repository analysis
    - Managing conversations between users and assistants
    - Checking repository processing status

    The controller acts as an intermediary between the user interface and the model,
    handling input validation and coordinating the flow of data and operations.

    Attributes:
        model (IModel): The model instance that implements the core repository analysis functionality
    """

    def __init__(self, model: IModel):
        self.model = model

    def __check_github_repo_url(self, url: str) -> bool:
        """
        Validates if the provided URL matches the expected GitHub repository URL pattern.

        Args:
            url (str): The URL to validate, expected format: https://github.com/{owner}/{repo_name}.git

        Returns:
            bool: True if URL matches the pattern, False otherwise
        """
        return bool(GITHUB_URL_PATTERN.fullmatch(url))

    def __extract_data_from_url(self, url: str) -> Tuple[str, str]:
        """
        Extracts the owner and repository name from a GitHub repository URL.

        Args:
            url (str): The GitHub repository URL in format https://github.com/{owner}/{repo_name}.git

        Returns:
            Tuple[str, str]: A tuple containing (owner, repository_name)
                            owner - The GitHub username/organization that owns the repository
                            repository_name - The name of the repository without the .git extension
        """
        url_parts = url.split("/")
        return url_parts[-2], url_parts[-1][:-4]

    def create_repo_and_thread(self, assistant_id: str, url: str) -> Dict:
        """
        Creates a repository and conversation thread for analyzing a GitHub repository.

        Args:
            assistant_id (str): The ID of the assistant that will analyze the repository
            url (str): The GitHub repository URL in format https://github.com/{owner}/{repo_name}.git

        Returns:
            Dict: A dictionary containing:
                - "repo_id": Inner ID of the repository
                - "thread_id": Conversation thread ID
                - "user": GitHub username/organization that owns the repository
                - "repo": Name of the repository

        Raises:
            ValueError: If the provided URL does not match the expected GitHub repository URL format
        """
        url = url.strip()
        if not self.__check_github_repo_url(url):
            raise ValueError("Wrong URL. The GitHub repository URL must be in the following format https://github.com/{owner}/{repo_name}.git ")

        user, repo = self.__extract_data_from_url(url)
        result = self.model.create_repo_and_thread(assistant_id, user, repo)

        return result | {"user": user, "repo": repo}

    def process_repo(self, user: str, repo: str, repo_id: str):
        """
        Processes a GitHub repository by calling the model's process_repo method.

        Args:
            user (str): The GitHub username/organization that owns the repository
            repo (str): The name of the repository
            repo_id (str): The inner ID of the repository to process

        Returns:
            None
        """

        self.model.process_repo(user, repo, repo_id)

    def create_assistant(self, name: str):
        """
        Creates a new assistant with the specified name by calling the model's create_assistant method.

        Args:
            name (str): The name to assign to the new assistant

        Returns:
            The assistant ID or other response from the model's create_assistant implementation
        """
        return self.model.create_assistant(name)

    def make_conversation(self, user_message: str, assistant_id: str, conversation_thread_id: str) -> str:
        """
        Initiates a conversation with the assistant by sending a user message.

        Args:
            user_message (str): The message from the user to send to the assistant
            assistant_id (str): The ID of the assistant to converse with
            conversation_thread_id (str): The ID of the conversation thread to use

        Returns:
            str: Assistant response message ID
        """
        return self.model.make_conversation(user_message, assistant_id, conversation_thread_id)

    def get_assistant_response(self, conversation_thread_id: str) -> Dict:
        """
        Retrieves the assistant's response for a given conversation thread.

        Args:
            conversation_thread_id (str): The ID of the conversation thread to get the response from

        Returns:
            Dict: A dictionary containing the assistant's response details from the model
        """
        return self.model.get_conversation_result(conversation_thread_id)

    def check_repo_status(self, thread_id: str) -> Dict:
        """
        Checks the processing status of a repository by retrieving results from the model.

        Args:
            thread_id (str): The ID of the conversation thread associated with the repository

        Returns:
            Dict: A dictionary containing the repository processing status ("processing", "completed")
        """
        return self.model.get_repo_result(thread_id)