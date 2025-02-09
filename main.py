import logging
import threading
from src.model.utils.logger import set_logger
from flask import Flask, request, jsonify

from src.controller.controller import Controller
from src.config import Configuration
from src.model.model import Model
from src.model.core.database import SQLite
from src.model.core.vectordb import ChromaDB
from src.model.core.assistance import OpenAIAssistant
from src.model.utils.utils import extract_par_or_raise

# Set up logging configuration
set_logger()
logger = logging.getLogger()

# Initialize Flask application
app = Flask(__name__)

# Load configuration from config.json file
configuration = Configuration("config.json")
# Initialize vector database for semantic search
chroma_vdb = ChromaDB(configuration)
# Initialize SQLite database for persistent storage
db = SQLite(configuration, "data")
# Initialize OpenAI assistant
assistant = OpenAIAssistant(
    configuration=configuration,
    vectordb=chroma_vdb)

# Initialize main model with all dependencies
model = Model(
    configuration=configuration,
    vectordb=chroma_vdb,
    assistant=assistant,
    db=db,
)
# Initialize controller with model
controller = Controller(model=model)

BASE_URL = "/api/v1"

@app.route(f"{BASE_URL}/assistant/create", methods=['POST'])
def create_assistant():
    """
    Creates a new assistant with the given name.

    Expects a POST request with JSON payload containing:
    {
        "name": "assistant_name"  # Required: Name for the new assistant
    }

    Returns:
    JSON response with:
    {
        "assistant_id": "id"  # ID of the created assistant
    }

    Raises:
        Exception if required parameters are missing or creation fails
    """
    data = request.json
    logging.info(data)
    try:
        assistant_name = extract_par_or_raise(data, "name")

        assistant_id = controller.create_assistant(name = assistant_name)
        output = {
            "assistant_id": assistant_id
        }
        return jsonify(output)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": str(e)})

@app.route(f"{BASE_URL}/repo/process", methods=['POST'])
def process_repo():
    """
    Process a GitHub repository and create a new thread for conversation.

    Expects a POST request with JSON payload containing:
    {
        "assistant_id": "id",  # Required: ID of the assistant to use
        "url": "repo_url"      # Required: URL of the GitHub repository to process
    }

    Returns:
    JSON response with:
    {
        "thread_id": "id"  # ID of the created conversation thread
    }

    The repository processing is done asynchronously in a background thread.
    The thread_id can be used to check the processing status and for future conversations.

    Raises:
        Exception if required parameters are missing or processing fails
    """
    data = request.json
    logging.info(data)
    try:
        assistant_id = extract_par_or_raise(data, "assistant_id")
        url = extract_par_or_raise(data, "url")

        result = controller.create_repo_and_thread(assistant_id, url)

        thread_id = result.get("thread_id")
        repo_id = result.get("repo_id")
        user = result.get("user")
        repo = result.get("repo")

        t = threading.Thread(
            target=controller.process_repo,
            args=(user, repo, repo_id)
        )
        t.start()

        output = {
            "thread_id": thread_id
        }
        return jsonify(output)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": str(e)})

@app.route(f"{BASE_URL}/repo/check", methods=['POST'])
def check_repo_status():
    """
    Check the processing status of a repository.

    Expects a POST request with JSON payload containing:
    {
        "thread_id": "id"  # Required: ID of the conversation thread to check
    }

    Returns:
    JSON response with the current processing status of the repository:
    {
        "status": "status_string",  # Current status (e.g. "processing", "completed")
    }

    Raises:
        Exception if thread_id is missing or status check fails
    """
    data = request.json
    logging.info(data)
    try:
        thread_id = extract_par_or_raise(data, "thread_id")
        output = controller.check_repo_status(thread_id)
        return jsonify(output)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": str(e)})

@app.route(f"{BASE_URL}/conversation/message", methods=['POST'])
def make_conversation():
    """
    Send a message to an assistant in a specific conversation thread.

    Expects a POST request with JSON payload containing:
    {
        "message": "text",      # Required: Message to send to the assistant
        "assistant_id": "id",   # Required: ID of the assistant to communicate with
        "thread_id": "id"       # Required: ID of the conversation thread
    }

    Returns:
    JSON response with:
    {
        "status": "processing"  # Status of the message processing
    }

    The message processing is done asynchronously in a background thread.

    Raises:
        Exception if required parameters are missing or message processing fails
    """
    data = request.json
    logging.info(data)
    try:
        user_message = extract_par_or_raise(data, "message")
        assistant_id = extract_par_or_raise(data, "assistant_id")
        thread_id = extract_par_or_raise(data, "thread_id")

        t = threading.Thread(
            target = controller.make_conversation,
            args=(user_message, assistant_id, thread_id)
        )
        t.start()

        # status = controller.make_conversation(user_message, assistant_id, thread_id)

        status = {"status": "processing"}
        logging.info(f"Assistant {assistant_id}. Thread {thread_id}. Message status: {status}")
        return jsonify(status)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": str(e)})

@app.route(f"{BASE_URL}/conversation/result", methods=['POST'])
def get_assistant_response():
    """
    Retrieve the assistant's response from a conversation thread.

    Expects a POST request with JSON payload containing:
    {
        "thread_id": "id"  # Required: ID of the conversation thread
    }

    Returns:
    JSON response with:
    {
        "message": "text",     # The assistant's response message (not provided if status = "processing)"
        "status": "status",     # Status of the response (e.g. "completed", "processing")
    }

    Raises:
        Exception if thread_id is missing or response retrieval fails
    """
    data = request.json
    logging.info(data)

    try:
        thread_id = extract_par_or_raise(data, "thread_id")
        result = controller.get_assistant_response(thread_id)
        return jsonify(result)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)