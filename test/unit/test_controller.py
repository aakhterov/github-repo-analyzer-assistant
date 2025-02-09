import pytest
from src.controller.controller import Controller

@pytest.fixture
def model():
    pass

@pytest.fixture
def controller():
    return Controller(model)

@pytest.mark.parametrize("url, expected", [
    # Valid cases
    ("https://github.com/owner/repo.git", True),
    ("https://github.com/microsoft/vscode.git", True),
    ("https://github.com/python/cpython.git", True),
    
    # Invalid cases
    ("", False),
    ("not_a_url", False),
    ("http://github.com/owner/repo.git", False),  # Wrong protocol
    ("https://gitlab.com/owner/repo.git", False),  # Wrong domain
    ("https://github.com/owner", False),  # Missing repo
    ("https://github.com/owner/repo/extra", False),  # Extra path
    ("https://github.com/owner/repo", False),  # Missing .git
])

def test_check_github_repo_url(controller, url, expected):
    """
    Test the GitHub repository URL validation with various inputs.
    
    Args:
        controller: The controller instance (from fixture)
        url: Input URL to test
        expected: Expected validation result
    """
    result = controller._Controller__check_github_repo_url(url)
    assert result == expected, f"URL validation failed for {url}"

def test_check_github_repo_url_type_error(controller):
    """Test that the method raises TypeError for non-string inputs"""
    with pytest.raises(TypeError):
        controller._Controller__check_github_repo_url(None)
    with pytest.raises(TypeError):
        controller._Controller__check_github_repo_url(123)


@pytest.mark.parametrize("url, expected", [
    ("https://github.com/owner/repo.git", ("owner", "repo")),
    ("https://github.com/microsoft/vscode.git", ("microsoft", "vscode")),
    ("https://github.com/python/cpython.git", ("python", "cpython")),
    ("https://github.com/organization-name/repo-with-hyphens.git", ("organization-name", "repo-with-hyphens"))
])

def test_extract_data_from_url(controller, url, expected):
    """
    Test extracting owner and repository name from GitHub URLs.

    Args:
        controller: The controller instance (from fixture)
        url: Input GitHub URL
        expected: Expected tuple of (owner, repository_name)
    """
    owner, repo = controller._Controller__extract_data_from_url(url)
    assert (owner, repo) == expected, f"Failed to extract correct data from {url}"

@pytest.fixture
def valid_assistant_id():
    return "asst_123456789"

@pytest.fixture
def mock_model(mocker):
    """Mock the model's create_repo_and_thread method"""
    mock = mocker.Mock()
    mock.create_repo_and_thread.return_value = {
        "repo_id": "repo_123",
        "thread_id": "thread_456"
    }
    return mock


def test_create_repo_and_thread_success(controller, valid_assistant_id, mock_model):
    """Test successful repository and thread creation"""
    controller.model = mock_model
    url = "https://github.com/owner/repo.git"

    result = controller.create_repo_and_thread(valid_assistant_id, url)

    assert isinstance(result, dict)
    assert result["repo_id"] == "repo_123"
    assert result["thread_id"] == "thread_456"
    assert result["user"] == "owner"
    assert result["repo"] == "repo"

@pytest.mark.parametrize("invalid_url", [
    "",
    "not_a_url",
    "http://github.com/owner/repo.git",  # Wrong protocol
    "https://gitlab.com/owner/repo.git",  # Wrong domain
    "https://github.com/owner",  # Missing repo
    "https://github.com/owner/repo/extra"  # Extra path
])

def test_create_repo_and_thread_invalid_url(controller, valid_assistant_id, invalid_url):
    """Test handling of invalid URLs"""
    with pytest.raises(ValueError) as exc_info:
        controller.create_repo_and_thread(valid_assistant_id, invalid_url)

    assert "Wrong URL" in str(exc_info.value)