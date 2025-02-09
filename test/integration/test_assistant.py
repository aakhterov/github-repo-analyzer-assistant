import os
import pytest

from src.model.core.assistance import OpenAIAssistant

os.environ["OPENAI_API_KEY"] = "sk-1234567890"

class MockAssistant:
    def __init__(self, assistant_id):
        self.id = assistant_id

@pytest.fixture()
def configuration():
    pass

@pytest.fixture()
def vectordb():
    pass

@pytest.fixture
def valid_assistant_name():
    return "test_assistant"

@pytest.fixture
def openai_assistant():
    return OpenAIAssistant(
        configuration=configuration,
        vectordb=vectordb
    )

@pytest.fixture
def mock_configuration(mocker):
    mock = mocker.Mock()
    return mock

@pytest.fixture
def mock_openai_client(mocker):
    mock = mocker.Mock()
    return mock

def test_create_assistant(
        openai_assistant,
        valid_assistant_name,
        mock_configuration,
        mock_openai_client
):
    openai_assistant.client = mock_openai_client
    openai_assistant.configuration = mock_configuration
    mock_configuration.models.get.return_value = "gpt-4o"
    mock_openai_client.beta.assistants.create.return_value = MockAssistant(assistant_id="asst_123")

    assistant_id = openai_assistant.create_assistant(
        name=valid_assistant_name
    )

    assert isinstance(assistant_id, str)
    assert assistant_id == "asst_123"
