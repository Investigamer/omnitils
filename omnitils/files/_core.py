"""
* Core File Utilities
* Generalized utilities for working with files.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Union

"""
* Generating Files
"""


def ensure_file(path: Path, encoding: str = 'utf-8', boilerplate: str = '') -> None:
    """If a file doesn't exist, create an empty file there.

    Args:
        path: Path to the file.
        encoding: Encoding to use when opening the new file.
        boilerplate: Data to write to the new file.
    """
    if path.is_file():
        return
    with open(path, 'w', encoding=encoding) as f:
        f.write(boilerplate)
    return


def get_temporary_file(path: Path, ext: str = '.tmp', allow_existing: bool = False) -> Path:
    """Check for an existing temporary file representing a provided file path and extension, creates a
        new temporary file if one doesn't exist.

    Args:
        path: Path to the file we plan to download.
        ext: File extension to use when naming the temporary file, defaults to `.tmp`.
        allow_existing: Whether to use existing temporary file if found, defaults to False.

    Returns:
        Path to the temporary file.
    """

    # Look for an existing file
    temp = path.with_suffix(ext)
    if allow_existing:
        for p in os.listdir(path.parent):
            file = path.parent / p
            if file.is_dir() or os.path.samefile(file, path):
                continue
            if temp.name in file.name:
                return file

    # Create a new temporary file
    f = NamedTemporaryFile(prefix=temp.name, dir=temp.parent, delete=False)
    file = f.name
    f.close()
    return Path(file)


"""
* File Naming
"""


def get_unique_filename(path: Path, increment_template: str = '({})') -> Path:
    """If a filepath exists, number the file according to the lowest number that doesn't exist.

    Args:
        path: Path to the file.
        increment_template: String that contains the numeric increment which is increased to arrive at
            a unique filename. Defaults to (i).

    Returns:
        A unique file path.
    """
    stem, i = path.stem, 1
    while path.is_file():
        path = path.with_stem(f'{stem} {increment_template.format(i)}')
        i += 1
    return path


"""
* File Information
"""


def get_file_size_mb(file_path: Union[str, os.PathLike], decimal: int = 1) -> float:
    """Get a file's size in megabytes rounded.

    Args:
        file_path: Path to the file.
        decimal: Number of decimal places to allow when rounding.

    Returns:
        Float representing the filesize in megabytes rounded to decimal length provided.
    """
    return round(os.path.getsize(file_path) / (1024 * 1024), decimal)


def get_sha256(path: Path, chunk_size: int = 4096) -> str:
    """Calculate the SHA-256 hash of a file.

    Args:
        path: Path to the file.
        chunk_size: Max bytes to read from the file on each iteration.

    Returns:
        The SHA-256 hash of this file.
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
