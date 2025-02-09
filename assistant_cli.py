import os
from time import sleep
import argparse
from typing import Dict, Callable, Tuple

import requests
from tenacity import retry, wait_exponential, stop_after_attempt
from urllib.parse import urljoin

CREATE_ASSISTANT_URI = "/api/v1/assistant/create"
PROCESS_REPO_URI = "/api/v1/repo/process"
CHECK_REPO_STATUS_URI = "/api/v1/repo/check"
ADD_MESSAGE_URI = "/api/v1/conversation/message"
CHECK_MESSAGE_STATUS_URI = "/api/v1/conversation/result"
MAX_RETRIES_RATE_LIMIT = 5
CHECKIG_MESSAGE_STATUS_INTERVAL = 3
MAX_RETRY_MESSAGE_STATUS = 10

class CLIInterface:
    """
    A command-line interface for interacting with an AI assistant system.

    This class provides functionality to:
    - Create and manage AI assistants
    - Process and analyze GitHub repositories
    - Start interactive conversations with assistants

    The interface is structured with three main command groups:
    - assistant: Commands for creating new assistants
    - repo: Commands for processing and checking repository status
    - conversation: Commands for starting interactive conversations

    Environment Variables:
        ASSISTANT_API_URL: Base URL for the assistant API endpoints

    Attributes:
        base_url (str): Base URL for API requests
        parser (ArgumentParser): Command line argument parser

    Example Usage:
        cli = CLIInterface()
        cli.run()
    """

    def __init__(self):
        if not os.environ.get("ASSISTANT_API_URL"):
            print("Error: Add ASSISTANT_API_URL env. variable")
            exit()

        self.base_url = os.environ["ASSISTANT_API_URL"]

        self.parser = argparse.ArgumentParser(description="GitHub Analyzer Command-Line Interface")
        subparsers = self.parser.add_subparsers(dest='command', help='Object to perform actions')

        # Assistant command and its subcommands
        parser_assistant = subparsers.add_parser('assistant', help='Assistant related commands')
        assistant_subparsers = parser_assistant.add_subparsers(dest='subcommand', help='Assistant sub-command help')

        # Assistant "create" subcommand
        parser_create = assistant_subparsers.add_parser('create', help='Create an assistant')
        parser_create.add_argument('--name', required=True, help='Name of the assistant')

        # Repo command and its subcommands
        parser_repo = subparsers.add_parser('repo', help='Repo related commands')
        repo_subparsers = parser_repo.add_subparsers(dest='subcommand', help='Repo sub-command help')

        # Repo "process" subcommand
        parser_process = repo_subparsers.add_parser('process', help='Process a repository')
        parser_process.add_argument('--assistant_id', required=True, help='ID of the assistant')
        parser_process.add_argument('--url', required=True, help='URL of the repository')

        # Repo "check" subcommand
        parser_check = repo_subparsers.add_parser('check', help='Check repository status')
        parser_check.add_argument('--thread_id', required=True, help='ID of the thread')

        # Conversation command and its subcommands
        parser_conversation = subparsers.add_parser('conversation', help='Conversation related commands')
        conversation_subparsers = parser_conversation.add_subparsers(dest='subcommand',
                                                                     help='Conversation sub-command help')

        # Conversation "start" subcommand
        parser_start = conversation_subparsers.add_parser('start', help='Start a conversation')
        parser_start.add_argument('--assistant_id', required=True, help='ID of the assistant')
        parser_start.add_argument('--thread_id', required=True, help='ID of the thread')

    @retry(wait=wait_exponential(multiplier=1, min=0, max=20), stop=stop_after_attempt(MAX_RETRIES_RATE_LIMIT))
    def __request_with_retry(self, url: str, payload: Dict) -> Dict:
        """
        Makes a POST request to the specified URL with automatic retries on HTTP 429 error.

        Args:
            url (str): The URL endpoint to send the request to
            payload (Dict): The request payload/body to send as JSON

        Returns:
            Dict: The JSON response from the server

        Raises:
            Exception: If rate limit is exceeded (HTTP 429)
            requests.exceptions.HTTPError: If the HTTP request fails
        """
        response = requests.post(url, json=payload)
        if response.status_code == 429:
            raise Exception("Rate limit exceeded")
        response.raise_for_status()
        return response.json()

    def __run_func(self, func: Callable, args: Tuple):
        """
        Executes a function with given arguments and handles exceptions.

        Args:
            func (Callable): The function to execute
            args (Tuple): Arguments to pass to the function

        Returns:
            None

        Prints:
            The response from the function if successful
            Error message if an exception occurs
        """
        try:
            response = func(*args)
            print(response)
        except Exception as e:
            print(f"Error: {e}")

    def __create_assistant(self, name: str) -> Dict:
        """
        Creates a new assistant with the given name by making a POST request to the assistant creation endpoint.

        Args:
            name (str): The name to assign to the new assistant

        Returns:
            Dict: The JSON response from the server containing the created assistant details
        """
        url = urljoin(self.base_url, CREATE_ASSISTANT_URI)
        payload = {
            "name": name
        }
        result = self.__request_with_retry(url, payload)
        return result

    def __process_repo(self, assistant_id, repo_url):
        """
        Processes a repository by making a POST request to the repository processing endpoint.

        Args:
            assistant_id (str): The ID of the assistant that will process the repository
            repo_url (str): The URL of the repository to process

        Returns:
            Dict: The JSON response from the server containing the processing result
        """
        url = urljoin(self.base_url, PROCESS_REPO_URI)
        payload = {
            "assistant_id": assistant_id,
            "url": repo_url
        }
        result = self.__request_with_retry(url, payload)
        return result

    def __check_repo(self, thread_id: str):
        """
        Checks the status of a repository processing task by making a POST request to the repository status endpoint.

        Args:
            thread_id (str): The ID of the thread associated with the repository processing task

        Returns:
            Dict: The JSON response from the server containing the repository processing status
        """
        url = urljoin(self.base_url, CHECK_REPO_STATUS_URI)
        payload = {
            "thread_id": thread_id
        }
        result = self.__request_with_retry(url, payload)
        return result

    def __start_conversation(self, assistant_id: str, thread_id: str):
        """
        Starts an interactive conversation session with the AI assistant.

        This method initiates a continuous conversation loop where the user can input messages
        and receive responses from the AI assistant. The conversation continues until the user
        types 'exit'.

        Args:
            assistant_id (str): The unique identifier of the AI assistant to converse with
            thread_id (str): The unique identifier of the conversation thread

        Returns:
            str: A farewell message when the conversation is ended by the user

        Inner Functions:
            fetch_result(thread_id: str) -> str:
                Polls the message status endpoint until a response is received or max retries reached
        """

        def fetch_result(thread_id: str) -> str:
            for _ in range(MAX_RETRY_MESSAGE_STATUS):
                sleep(CHECKIG_MESSAGE_STATUS_INTERVAL)
                result = self.__request_with_retry(check_message_status_url, payload)
                if result.get("status") == "completed":
                    return result.get("message")
            return "Something went wrong :( Try once again"

        add_message_url = urljoin(self.base_url, ADD_MESSAGE_URI)
        check_message_status_url = urljoin(self.base_url, CHECK_MESSAGE_STATUS_URI)

        while True:
            message = input(f"{'='*20} Human {'='*20}\nEnter your question (or type 'exit' to stop): ").strip()
            if message.lower() == 'exit':
                return "Bye! See you again."
            payload = {
                "message": message,
                "assistant_id": assistant_id,
                "thread_id": thread_id
            }
            _ = self.__request_with_retry(add_message_url, payload)
            print(f"\n{'='*20} Assistant {'='*20}\nWaiting for response...")
            ai_message = fetch_result(thread_id)

            print(f"{ai_message}\n")

    def run(self):
        """
        Main entry point that parses command line arguments and executes the appropriate command.

        The method handles three main command groups:
        - assistant: For creating new assistants
        - repo: For processing and checking repository status
        - conversation: For starting interactive conversations

        Each command group has specific subcommands:
        - assistant create: Creates a new assistant with given name
        - repo process: Processes a repository with given assistant ID and URL
        - repo check: Checks status of repository processing with thread ID
        - conversation start: Starts interactive conversation with given assistant and thread IDs

        Returns:
            None
        """
        args = self.parser.parse_args()

        if args.command == 'assistant':
            if args.subcommand == 'create':
                self.__run_func(self.__create_assistant, (args.name,))

        elif args.command == 'repo':
            if args.subcommand == 'process':
                self.__run_func(self.__process_repo, (args.assistant_id, args.url))
            elif args.subcommand == 'check':
                self.__run_func(self.__check_repo, (args.thread_id,))

        elif args.command == 'conversation':
            if args.subcommand == 'start':
                self.__run_func(self.__start_conversation, (args.assistant_id, args.thread_id))
if __name__ == "__main__":
    cli = CLIInterface()
    cli.run()





