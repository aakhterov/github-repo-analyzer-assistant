import requests
from typing import Dict

def extract_par_or_raise(body: Dict, key: str):
    """
    Extract a parameter from a dictionary or raise KeyError if not found.

    Args:
        body (Dict): Dictionary to extract parameter from
        key (str): Key to look up in the dictionary

    Returns:
        The value associated with the key in the dictionary

    Raises:
        KeyError: If the key is not found in the dictionary
    """
    output = body.get(key)
    if output:
        return output
    raise KeyError(f"The parameter '{key}' is required")

def get_repo_metadata(user, repo):
    """
    Get metadata for a GitHub repository.

    Makes a GET request to the GitHub API to retrieve repository metadata.

    Args:
        user (str): GitHub username or organization name that owns the repository
        repo (str): Name of the repository

    Returns:
        dict: Repository metadata from the GitHub API response

    Raises:
        Exception: If the API request fails, with the status code in the error message
    """
    url = f"https://api.github.com/repos/{user}/{repo}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to retrieve repository details: {response.status_code}")

def get_branch_sha(user, repo, branch):
    """
    Get the SHA hash of a branch in a GitHub repository.

    Makes a GET request to the GitHub API to retrieve the SHA hash of the latest commit
    on the specified branch.

    Args:
        user (str): GitHub username or organization name that owns the repository
        repo (str): Name of the repository
        branch (str): Name of the branch to get the SHA for

    Returns:
        str: The SHA hash of the latest commit on the branch

    Raises:
        Exception: If the API request fails, with the status code in the error message
    """
    url = f"https://api.github.com/repos/{user}/{repo}/branches/{branch}"
    response = requests.get(url)
    if response.status_code == 200:
        branch_data = response.json()
        return branch_data['commit']['sha']
    else:
        raise Exception(f"Failed to get branch SHA: {response.status_code}")

def get_repo_tree(user, repo, sha, recursive=True):
    """
    Get the file tree for a GitHub repository at a specific commit.

    Makes a GET request to the GitHub API to retrieve the repository file tree
    at the specified commit SHA. Can optionally get the tree recursively.

    Args:
        user (str): GitHub username or organization name that owns the repository
        repo (str): Name of the repository
        sha (str): SHA hash of the commit to get the tree for
        recursive (bool, optional): Whether to get the tree recursively. Defaults to True.

    Returns:
        dict: Repository tree data from the GitHub API response

    Raises:
        Exception: If the API request fails, with the status code in the error message
    """
    url = f"https://api.github.com/repos/{user}/{repo}/git/trees/{sha}"
    if recursive:
        url += "?recursive=1"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get repo tree: {response.status_code}")

def build_metadata(metadata: Dict) -> Dict:
    """
    Build a dictionary of repository metadata with standardized keys.

    Takes a dictionary of repository metadata from the GitHub API and extracts specific fields,
    prefixing their keys with 'repo_' in the output dictionary.

    Args:
        metadata (Dict): Dictionary containing repository metadata from GitHub API
    """

    KEYS = ["stargazers_count", "subscribers_count", "size", "pushed_at", "open_issues", "created_at"]

    return {f"repo_{key}": metadata.get(key, "") for key in KEYS}
