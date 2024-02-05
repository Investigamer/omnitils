"""
* File Utilities
* Generalized utilities for working with files.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import hashlib
from pathlib import Path


"""
* File Information
"""


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
