import pytest

from src.model.model import Model

@pytest.fixture()
def configuration():
    pass

@pytest.fixture()
def vectordb():
    pass

@pytest.fixture()
def assistant():
    pass

@pytest.fixture()
def db():
    pass

@pytest.fixture
def valid_assistant_id():
    return "asst_123456789"

@pytest.fixture
def valid_user():
    return "test_user"

@pytest.fixture
def valid_repo():
    return "test_repo"

@pytest.fixture
def model():
    return Model(
        configuration=configuration,
        vectordb=vectordb,
        assistant=assistant,
        db=db
    )

@pytest.fixture
def mock_db(mocker):
    mock = mocker.Mock()
    return mock

@pytest.fixture
def mock_vectordb(mocker):
    mock = mocker.Mock()
    return mock

@pytest.fixture
def mock_assistant(mocker):
    mock = mocker.Mock()
    return mock

def test_create_repo_and_thread_new_repo(
        model,
        valid_assistant_id,
        valid_user,
        valid_repo,
        mock_db,
        mock_assistant,
        mock_vectordb
):
    model.db = mock_db
    model.assistant = mock_assistant
    model.vectordb = mock_vectordb

    mock_db.get_repo_by_owner_and_repo_name.return_value = None
    mock_db.create_repo.return_value = "repo_123"
    mock_db.create_thread.return_value = None
    mock_assistant.create_thread.return_value = "thread_123"
    mock_vectordb.create_collection.return_value = None

    result = model.create_repo_and_thread(
        assistant_id=valid_assistant_id,
        user=valid_user,
        repo=valid_repo
    )

    assert isinstance(result, dict)
    assert result["repo_id"] == "repo_123"
    assert result["thread_id"] == "thread_123"

def test_create_repo_and_thread_existing_repo(
        model,
        valid_assistant_id,
        valid_user,
        valid_repo,
        mock_db,
        mock_assistant,
        mock_vectordb
):
    model.db = mock_db
    model.assistant = mock_assistant
    model.vectordb = mock_vectordb

    existed_repo = {
        "repo_id": "repo_123",
        "thread_id": "thread_123",
        "collection_name": "collection_123"
    }
    mock_db.get_repo_by_owner_and_repo_name.return_value = existed_repo
    mock_db.create_repo.return_value = "repo_123"
    mock_db.update_repo_status_by_id.return_value = None
    mock_vectordb.create_collection.return_value = None

    result = model.create_repo_and_thread(
        assistant_id=valid_assistant_id,
        user=valid_user,
        repo=valid_repo
    )

    assert isinstance(result, dict)
    assert result["repo_id"] == "repo_123"
    assert result["thread_id"] == "thread_123"
