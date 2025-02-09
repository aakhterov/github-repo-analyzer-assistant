import aiohttp

async def aget_repo_metadata(user, repo):
    """
    Asynchronously retrieves metadata for a GitHub repository.

    Args:
        user (str): GitHub username or organization name
        repo (str): Repository name

    Returns:
        dict: Repository metadata including details like description, stars, forks etc.

    Raises:
        Exception: If the API request fails, with status code in the error message
    """
    url = f"https://api.github.com/repos/{user}/{repo}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                raise Exception(f"Failed to retrieve repository details: {response.status}")

async def aget_branch_sha(user, repo, branch):
    """
    Asynchronously retrieves the SHA hash for a specific branch in a GitHub repository.

    Args:
        user (str): GitHub username or organization name
        repo (str): Repository name
        branch (str): Branch name to get SHA for

    Returns:
        str: The SHA hash of the latest commit on the specified branch

    Raises:
        Exception: If the API request fails, with status code in the error message
    """
    url = f"https://api.github.com/repos/{user}/{repo}/branches/{branch}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                branch_data = await response.json()
                return branch_data['commit']['sha']
            else:
                raise Exception(f"Failed to get branch SHA: {response.status}")

async def aget_repo_tree(user, repo, sha, recursive=True):
    """
    Asynchronously retrieves the Git tree for a repository at a specific commit SHA.

    Args:
        user (str): GitHub username or organization name
        repo (str): Repository name
        sha (str): Commit SHA to get tree for
        recursive (bool, optional): Whether to get the tree recursively. Defaults to True.

    Returns:
        dict: Repository tree data containing files and directories

    Raises:
        Exception: If the API request fails, with status code in the error message
    """
    url = f"https://api.github.com/repos/{user}/{repo}/git/trees/{sha}"
    if recursive:
        url += "?recursive=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                response = await response.json()
                return response
            else:
                raise Exception(f"Failed to get repo tree: {response.status}")

async def adownload_file(user: str, repo: str, branch: str, path_to_file: str) -> bytes:
    """
    Asynchronously downloads a file from a GitHub repository.

    Args:
        user (str): GitHub username or organization name
        repo (str): Repository name
        branch (str): Branch name
        path_to_file (str): Path to the file within the repository

    Returns:
        bytes: Raw content of the downloaded file

    Raises:
        Exception: If the download fails, with status code in the error message
    """
    url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path_to_file}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                return data
            else:
                raise Exception(f"Failed to download {url}. Status code: {response.status}")
