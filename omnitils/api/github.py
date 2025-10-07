"""
* GitHub Utilities
* Generalized utilities for accessing GitHub files or GitHub API endpoints.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
import os
import zipfile
from logging import getLogger
from pathlib import Path
from typing import Callable, Optional, Union

import requests
import yarl
from backoff import expo, on_exception
from limits import RateLimitItemPerHour
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from omnitils.fetch import download_file
from omnitils.fetch._core import chunk_size_default, request_header_default
from omnitils.files.folders import mkdir_full_perms
from omnitils.rate_limit import rate_limit

# Rate limiter to safely limit GitHub requests
_rate_limit_storage = MemoryStorage()
_rate_limiter = MovingWindowRateLimiter(_rate_limit_storage)
_github_rate_limit = RateLimitItemPerHour(60)
_github_rate_limit_authenticated = RateLimitItemPerHour(5000)

"""
* Handlers
"""


def gh_request_handler(func) -> Callable:
    """Wrapper for a GitHub request function to handle retries and rate limits on
    unauthenticated requests (60 per hour)."""
    @rate_limit(limiter=_rate_limiter, limit=_github_rate_limit)
    @on_exception(expo, requests.exceptions.RequestException, max_tries=2, max_time=1)
    def decorator(*args, **kwargs):
        return func(*args, **kwargs)
    return decorator


def gh_request_handler_authenticated(func) -> Callable:
    """Wrapper for a GitHub request function to handle retries and rate limits on
    authenticated requests (5000 per hour)."""
    @sleep_and_retry
    @rate_limit(limiter=_rate_limiter, limit=_github_rate_limit_authenticated)
    @on_exception(expo, requests.exceptions.RequestException, max_tries=2, max_time=1)
    def decorator(*args, **kwargs):
        return func(*args, **kwargs)
    return decorator


"""
* Request Utilities
"""


def gh_get_header(
    header: dict | None = None,
    auth_token: str | None = None
):
    """Uses the provided header or falls back to default, then injects auth token if valid.

    Args:
        header: Header object to pass with request, uses default if not provided.
        auth_token: Auth token to inject into header if provided.

    Returns:
        Header to pass with a request.
    """
    header = header or request_header_default.copy()
    if auth_token:
        header['Authorization'] = f'token {auth_token}'
    return header


def gh_get_data_json(
    url: Union[str, yarl.URL],
    header: dict | None = None,
    auth_token: str | None = None,
    handler: Optional[Callable] = None
) -> dict | list | tuple:
    """Request a manifest file and return its JSON loaded data.

    Args:
        url: URL to the data file resource hosted on GitHub.
        header: Header object to pass with request, uses default if not provided.
        auth_token: GitHub auth token to inject into header if provided, raises rate limits.
        handler: Decorator function to handle retries, rate limits, etc. Uses built-in `request_handler_github`
            decorator if not provided.

    Raises:
        RequestException if resource could not be returned.
    """
    # Use provided header or choose one
    handler = handler or (
        gh_request_handler if auth_token
        else gh_request_handler_authenticated)

    @handler
    def _make_request(_url, _header, _token):
        with requests.get(_url, headers=gh_get_header(_header, _token)) as r:
            r.raise_for_status()
            return r.json()
    return _make_request(url, header, auth_token)


"""
* Download Utilities
"""


def gh_download_file(
    url: str | yarl.URL,
    path: Path,
    header: dict | None = None,
    auth_token: str | None = None,
    chunk_size: int = chunk_size_default,
    handler: Optional[Callable] = None
):
    """Requests a file and saves it to a given path location.

    Args:
        url: URL to the file hosted on GitHub.
        path: Absolute path to save the file to.
        header: Header object to pass with request, uses default if not provided.
        auth_token: GitHub auth token to inject into header if provided, raises rate limits.
        chunk_size: Size of each chunk to write when using iter_content to save file.
        handler: Decorator function to handle retries, rate limits, etc. Uses built-in `request_handler_github`
            decorator if not provided.

    Returns:
        Path to the file.
    """
    # Use provided header or choose one
    handler = handler or (
        gh_request_handler if auth_token
        else gh_request_handler_authenticated)

    @handler
    def _make_request():
        return download_file(
            url=url,
            path=path,
            header=gh_get_header(header, auth_token),
            chunk_size=chunk_size)

    # Download file
    _make_request()
    return path


def gh_download_repository(
    user: str,
    repo: str,
    path: Path,
    branch: str = 'main',
    header: dict | None = None,
    auth_token: str | None = None,
    chunk_size: int = chunk_size_default,
    handler: Optional[Callable] = None
) -> Path:
    """Download a gitHub repository and extract it to the provided path.

    Args:
        user: Username of the repository owner.
        repo: Name of the GitHub repository.
        path: Path to download and extract the repository to.
        branch: Name of the repository branch to download.
        header: Header object to pass with request, uses default if not provided.
        auth_token: GitHub auth token to inject into header if provided, raises rate limits.
        chunk_size: Size of each chunk to write when using iter_content to save file.
        handler: Decorator function to handle retries, rate limits, etc. Uses built-in `request_handler_github`
            decorator if not provided.

    Returns:
        Path to the repository.
    """
    # Establish base values
    temp_file = path / 'temp.zip'
    _repo_name = f'{repo}-{branch}'

    # Download the archive
    temp_file = gh_download_file(
        url=f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip",
        path=temp_file,
        header=header,
        auth_token=auth_token,
        chunk_size=chunk_size,
        handler=handler)

    # Extract files, remove temporary zip
    with zipfile.ZipFile(temp_file, 'r') as zf:
        _repo_names = zf.namelist()
        if _repo_names:
            _repo_name = _repo_names[0].split('/')[0]
        zf.extractall(path=path)
    os.remove(temp_file)
    return Path(path, _repo_name)


def gh_download_directory_files(
    user: str,
    repo: str,
    repo_dir: str,
    path: Path,
    file_type: str | None = None,
    header: dict | None = None,
    auth_token: Optional[str] = None,
    chunk_size: int = chunk_size_default,
    handler: Optional[Callable] = None
) -> list[Path]:
    """Download all files from a specific directory in a GitHub repository to a given path.

    Args:
        user: Username of the repository owner.
        repo: Name of the GitHub repository.
        repo_dir: Directory location in the GitHub repository to download files from.
        path: Path to save the files to.
        file_type: File type files must match in order to be downloaded, if provided.
        header: Header object to pass with request, uses default if not provided.
        auth_token: Optional GitHub personal access token to use, for increasing rate limits.
        chunk_size: Size of each chunk to write when using iter_content to save file.
        handler: Decorator function to handle retries, rate limits, etc. Uses built-in `request_handler_github`
            decorator if not provided.

    returns:
        A list containing a Path to each file downloaded.
    """
    # Ensure path exists
    if not path.is_dir():
        mkdir_full_perms(path)
    url = f'https://api.github.com/repos/{user}/{repo}/contents/{repo_dir}'
    header = gh_get_header(header, auth_token)
    files: list[Path] = []

    # Get file data from API
    try:
        data = gh_get_data_json(
            url=url,
            header=header,
            auth_token=auth_token,
            handler=handler)
    except requests.RequestException:
        # Couldn't get GitHub directory info
        getLogger().warning(
            f"Couldn't retrieve GitHub directory information!\n"
            f"URL: {url}")
        return files

    # Download each file
    for file in data:
        # Is this a file?
        if not all([bool(n in file) for n in ['type', 'name', 'download_url']]):
            continue
        # Is the filetype valid?
        if file['type'] != 'file' or (file_type and not file['name'].endswith(file_type)):
            continue

        # Download file
        try:
            files.append(
                gh_download_file(
                    url=file['download_url'],
                    path=Path(path, file['name']),
                    header=header,
                    chunk_size=chunk_size,
                    handler=handler))
        except requests.RequestException:
            # Couldn't download file
            getLogger().warning(
                f"Download failed: {file['download_url']}")
            continue
    return files
