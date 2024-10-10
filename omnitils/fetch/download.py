"""
* Download Utilities
* Generalized utilities for downloading files.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import os
from contextlib import suppress
from typing import Union, Callable, Optional

# Third Party Imports
import requests
from requests import Response
from requests.structures import CaseInsensitiveDict
from yarl import URL

# Local Imports
from omnitils.fetch._core import request_header_default, chunk_size_default


"""
* Working With Headers
"""


def check_resume_file(
    path: Union[str, os.PathLike],
    headers: dict[str] | CaseInsensitiveDict[str]
) -> bool:
    """Checks if a file download can be resumed by looking at the file and headers.

    Args:
        path: Path to the file being downloaded.
        headers: Headers being passed in the download request.

    Returns:
        True if resuming, otherwise False.
    """
    # Check for a range header with bytes spec
    if headers.get('Range') is not None and os.path.exists(path):
        if 'bytes=' in headers['Range']:
            try:
                # Check that range and size is equivalent
                status = headers['Range'][6:].split('-')[0]
                if int(status) == os.path.getsize(path):
                    return True
            except (IndexError, KeyError, TypeError):
                return False
    return False


def estimate_content_length(response: Response, default: int = 0) -> int:
    """Attempt to get the value of the Content-Length header from a Response. Return default value if not found.

    Args:
        response: Response object.
        default: Default value to return if no Content-Length header can't be parsed.

    Returns:
        Content-Length value from Response headers.
    """
    total = response.headers.get('Content-Length', default)
    with suppress(Exception):
        if isinstance(total, str):
            total = int(''.join(n for n in total if n.isdigit()) or default)
        if isinstance(total, int):
            return total
    return default


"""
* Download Requests
"""


def download_file(
    url: Union[str, URL],
    path: Union[str, os.PathLike],
    header: Optional[dict] = None,
    callback: Optional[Callable] = None,
    chunk_size: int = chunk_size_default,
) -> Union[str, os.PathLike]:
    """Download a file in chunks from url and save to path, executing a callback
        after each chunk if provided.

    Args:
        url: URL where the file is hosted.
        path: Path to save the file to.
        header: Header object to pass with request, uses default if not provided.
        callback: Callback to execute after each chunk is written. Passes
            number of bytes written (int) and number of bytes total (int).
        chunk_size: Chunk size in bytes to download while streaming the file.

    Returns:
        Path to the saved file, if successful.

    Raises:
        RequestException: If request is unsuccessful.
        FileExistsError: If file already exists and cannot be overwritten.
    """
    has_callback = callback is not None
    header = header or request_header_default.copy()
    write_mode = 'ab' if check_resume_file(path, header) else 'wb'
    with requests.get(url, headers=header, stream=True) as r:
        r.raise_for_status()

        # Get file size total
        total = estimate_content_length(r) if has_callback else 0

        # Write the file in chunks
        with open(path, write_mode) as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    raise OSError('Bad chunk detected, likely a truncated stream!')
                f.write(chunk)

                # Execute callback if provided
                if has_callback:
                    current = f.tell()
                    callback(current, max(current, total))

    # Return path
    return path


def download_file_from_response(
    response: Response,
    path: Union[str, os.PathLike],
    callback: Optional[Callable[[int, int], None]] = None,
    chunk_size: int = chunk_size_default,
) -> Union[str, os.PathLike]:
    """Download a file in chunks using a given Request and optional Session, executing a callback
        after each chunk if provided.

    Args:
        response: Response stream to download file from.
        path: Path to save the file to.
        callback: Optional callback to execute after each chunk is written. Passes
            number of bytes written (int) and number of bytes total (int).
        chunk_size: Chunk size in bytes to download over each `iter_content` iteration, defaults to 8MB.

    Returns:
        Path to the saved file, if successful.

    Raises:
        RequestException: If request is unsuccessful.
        FileExistsError: If file already exists and cannot be overwritten.
    """
    response.raise_for_status()
    has_callback = callback is not None

    # Get file size total
    total = estimate_content_length(response) if has_callback else 0
    write_mode = 'ab' if check_resume_file(path, response.headers) else 'wb'

    # Write the file in chunks
    with open(path, write_mode) as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            # Check for bad chunks
            if not chunk:
                raise OSError('Bad chunk detected, likely a truncated stream!')
            f.write(chunk)

            # Execute callback if provided
            if has_callback:
                current = f.tell()
                callback(current, max(current, total))

    # Return path
    return path
