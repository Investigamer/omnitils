"""
* Utils: GitHub
"""
# Standard Library Imports
import os
import zipfile
from logging import getLogger
from pathlib import Path
import requests
from typing import Optional

# Third Party Imports
from omnitils.folders import mkdir_full_perms

"""
* Utility Funcs
"""


def download_repository(repo: str, path: Path) -> None:
    """Download a gitHub repository and extract it to the provided path.

    Args:
        repo: Name of the GitHub repository.
        path: Path to download and extract the repository to.
    """

    # Establish base values
    chunk_size = 1024 * 1024 * 8
    temp_file = path / 'temp.zip'
    if '/' not in repo:
        raise ValueError('Invalid repository name provided: {}'
                         'Must provide `user/repository` format.'.format(repo))
    _, repo_name, *_ = repo.split('/')
    url = f"https://github.com/{repo}/archive/refs/heads/main.zip"

    # Download the archive
    with requests.get(url, stream=True) as response:
        response.raise_for_status()

        # Write the content in chunks to a temporary zip file
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)

    # Extract the zip
    with zipfile.ZipFile(temp_file, 'r') as zip_ref:
        zip_ref.extractall()

    # Remove the temporary zip
    os.remove(temp_file)


def download_directory_files(repo: str, repo_dir: str, path: Path, token: Optional[str] = None) -> None:
    """Download all files from a specific directory in a GitHub repository to a given path.

    Args:
        repo: Name of the GitHub repository.
        repo_dir: Directory location in the GitHub repository to download files from.
        path: Path to save the files to.
        token: Optional GitHub personal access token to use, for increasing rate limits.
    """

    # Check if token was provided
    headers = {'Authorization': f'token {token}'} if token else {}

    # Ensure path exists
    if not path.is_dir():
        mkdir_full_perms(path)

    # Get file data from API
    url = f'https://api.github.com/repos/{repo}/contents/{repo_dir}'
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        getLogger().warning(
            f"Couldn't retrieve file manifest from GitHub!\n"
            f"URL: {url}")
        return

    # Download each file
    for file in res.json():
        if not all([
            bool(n in file) for n in
            ['type', 'name', 'download_url']
        ]):
            continue
        if file['type'] == 'file' and file['name'].endswith('.json'):
            file_res = requests.get(file['download_url'], headers=headers)
            if file_res.status_code != 200:
                getLogger().warning(
                    f"Download failed: {file['download_url']}")
                continue
            with open(Path(path, file['name']), 'wb') as f:
                f.write(file_res.content)
