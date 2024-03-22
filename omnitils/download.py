"""
* Download Utilities
* Generalized utilities for downloading files.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from os import PathLike
from typing import Union, Callable

# Third Party Imports
import requests
from yarl import URL

# Default chunk size (8MB)
default_chunk_size = 1024 * 1024 * 8

"""
* Download Requests
"""


def download_file(
    url: Union[str, URL],
    path: Union[str, PathLike],
    chunk_size: int = default_chunk_size
) -> None:
    """Download a file in chunks from url and save to path.

    Args:
        url: URL where the file is hosted.
        path: Path to save the file to.
        chunk_size: Chunk size in bytes to download while streaming the file.

    Raises:
        RequestException: If request is unsuccessful.
        FileExistsError: If file already exists and cannot be overwritten.
    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        # Write the file in chunks
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)


def download_file_with_callback(
    url: Union[str, URL],
    path: Union[str, PathLike],
    callback: Callable,
    chunk_size: int = default_chunk_size,
) -> None:
    """Download a file in chunks from url and save to path, executing a callback
        after each chunk is written.

    Args:
        url: URL where the file is hosted.
        path: Path to save the file to.
        callback: Callback to execute after each chunk is written. Passes
            url, path, number of bytes written, and number of bytes total.
        chunk_size: Chunk size in bytes to download while streaming the file.

    Raises:
        RequestException: If request is unsuccessful.
        FileExistsError: If file already exists and cannot be overwritten.
    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        # Get file size total
        total = r.headers.get('Content-Length', chunk_size)
        if isinstance(total, str):
            total = int(''.join([n for n in total if n.isnumeric()]) or 0)
        elif not isinstance(total, (int, float)):
            total = 0

        # Write the file in chunks
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                current = f.tell()
                if total < current:
                    total = current + 1
                callback(url, path, current, total)
