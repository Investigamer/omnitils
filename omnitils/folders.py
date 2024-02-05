"""
* Folder Utilities
* Generalized utilities for working with folders/directories.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import os
from pathlib import Path

"""
* Folder Information
"""


def mkdir_full_perms(path: Path) -> Path:
    """Uses a given path to create a directory if it doesn't exist, with full permissions.

    Args:
        path: Path to the directory.

    Returns:
        The director provided.
    """
    if path.is_dir():
        return path
    os.umask(0)
    path.mkdir(mode=0o755, parents=True, exist_ok=True)
    return path

