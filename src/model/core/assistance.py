import json
import logging
from openai import OpenAI

from src.interfaces.assistant import IAssistant
from src.interfaces.vectordb import IVectorDB
from src.config import Configuration

INSTRUCTION = """As a knowledgeable software development assistant, you provide insightful answers 
to questions about a concrete GitHub repository. Utilize the given functions effectively 
to extract data from the concrete GitHub repository and deliver precise and informative responses.
Important notes: Provide code snippets if code exists in the function output."""

class OpenAIAssistant(IAssistant):
    """
    OpenAI Assistant implementation that provides conversational AI capabilities.

    This class implements the IAssistant interface using OpenAI's API to create and manage
    AI assistants specialized in answering questions about GitHub repositories. It handles:
    - Creating and configuring OpenAI assistants
    - Managing conversation threads
    - Processing messages between users and the assistant
    - Integrating with vector database for repository data retrieval
    - Formatting and returning conversation results

    Attributes:
        configuration (Configuration): Configuration settings for the assistant
        vectordb (IVectorDB): Vector database interface for repository data access
        client (OpenAI): OpenAI API client instance
    """

    def __init__(self, configuration: Configuration, vectordb:IVectorDB):
        self.configuration = configuration
        self.vectordb = vectordb
        self.client = OpenAI()

    def create_assistant(self, name: str) -> str:
        """
        Creates a new OpenAI assistant with specified name and configuration.

        This method initializes an OpenAI assistant with:
        - Custom name provided as parameter
        - Model specified in configuration for "conversation"
        - Pre-defined instruction set (INSTRUCTION constant)
        - Tool for extracting GitHub repository data

        Args:
            name (str): Name to assign to the new assistant

        Returns:
            str: ID of the created assistant
        """
        assistant = self.client.beta.assistants.create(
            name=name,
            model=self.configuration.models.get("conversation"),
            instructions=INSTRUCTION,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "github_repository_data_extractor",
                        "description": "Retrieve data from a specific GitHub repository. "
                                       "Build a clear and specific query because it will be used "
                                       "for a similarity search on the GitHub repository",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Query the code you need"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            ]
        )

        logging.info(f"An OpenAI Assistance has been created. id={assistant.id}")

        return assistant.id

    def create_thread(self) -> str:
        """
        Creates a new OpenAI thread for conversation.

        This method initializes a new thread that can be used to maintain
        conversation state and history between the user and assistant.

        Returns:
            str: The ID of the created thread that can be used in subsequent
                 conversation interactions
        """
        thread = self.client.beta.threads.create()
        logging.info(f"An OpenAI thread has been created. id={thread.id}")
        return thread.id

    def __execute_conversation(self, assistant_id: str, conversation_thread_id: str) -> str:
        """
        Executes a conversation with the OpenAI assistant and handles tool outputs.

        This private method manages the conversation flow by:
        1. Creating and polling a run with the assistant
        2. Processing any required tool outputs (specifically for GitHub repository data extraction)
        3. Submitting tool outputs back to the conversation
        4. Retrieving and returning the assistant's response

        Args:
            assistant_id (str): The ID of the OpenAI assistant to use for the conversation
            conversation_thread_id (str): The ID of the conversation thread to continue

        Returns:
            str: The ID of the message containing the assistant's response. Returns None if
                 the conversation fails to complete successfully.
        """

        logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                    f"Conversation has started.")

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=conversation_thread_id,
            assistant_id=assistant_id
        )

        logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                     f"Response has been generated. Current status: {run.status}.")

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=conversation_thread_id
            )

            logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                        f"AI: {messages}.")

            return messages.data[0].id

        tool_outputs = []
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "github_repository_data_extractor":
                query = json.loads(tool.function.arguments).get("query", "")

                logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                             f"Query for the vector store: {query}.")

                docs = self.vectordb.get_docs_with_score(query=query)

                logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                             f"{len(docs)} doc(s) were found.")

                output = "\n======\n".join([json.dumps(doc) for doc in docs])
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": output
                })

        if tool_outputs:
            run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=conversation_thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                        f"Tool outputs submitted successfully.")
        else:
            logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                        f"No tool outputs to submit.")

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=conversation_thread_id
            )

            logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                        f"AI: {messages}.")

            return messages.data[0].id
        else:
            logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                        f"Something went wrong. Conversation status: {run.status}.")

    def make_conversation(self, user_message: str, **kwarg) -> str:
        """
        Initiates a conversation with the OpenAI assistant by sending a user message and
        executing the conversation flow.

        This method:
        1. Creates a new message in the specified conversation thread with the user's input
        2. Executes the conversation using the specified assistant
        3. Returns the ID of the assistant's response message

        Args:
            user_message (str): The message from the user to send to the assistant
            **kwarg: Additional keyword arguments
                assistant_id (str): The ID of the OpenAI assistant to use
                conversation_thread_id (str): The ID of the conversation thread to continue

        Returns:
            str: The ID of the message containing the assistant's response
        """
        assistant_id = kwarg.get("assistant_id")
        conversation_thread_id = kwarg.get("conversation_thread_id")

        message = self.client.beta.threads.messages.create(
            thread_id=conversation_thread_id,
            role="user",
            content=user_message,
        )

        logging.info(f"Assistant {assistant_id}. Thread {conversation_thread_id}. "
                    f"Human : {message}.")

        ai_message_id = self.__execute_conversation(assistant_id, conversation_thread_id)

        return ai_message_id

    def get_conversation_result(self, **kwarg) -> str:
        """
        Retrieves and formats the result of a conversation with the OpenAI assistant.

        This method:
        1. Retrieves the message content using the provided message ID and thread ID
        2. Extracts all text content from the message
        3. Joins the text content with newlines to create a single string response

        Args:
            **kwarg: Keyword arguments containing:
                conversation_thread_id (str): ID of the conversation thread
                ai_message_id (str): ID of the specific message to retrieve

        Returns:
            str: The formatted text content of the assistant's message, with multiple
                 text segments joined by newlines
        """
        conversation_thread_id = kwarg.get("conversation_thread_id")
        ai_message_id = kwarg.get("ai_message_id")

        message = self.client.beta.threads.messages.retrieve(
            message_id=ai_message_id,
            thread_id=conversation_thread_id,
        )

        return "\n".join([part.text.value for part in message.content if part.type=="text"])




