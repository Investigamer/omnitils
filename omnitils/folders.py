"""
* Folder Utilities
* Generalized utilities for working with folders/directories.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import os
from pathlib import Path
from typing import Iterator

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


"""
* Directory Listing
"""


def get_subdirs(path: Path) -> Iterator[Path]:
    """Yields each subdirectory of a given folder.

    Args:
        path: Path to the folder to iterate over.

    Yields:
        A subdirectory of the given folder.
    """
    for dir_path, dir_names, filenames in os.walk(path):
        for dirname in dir_names:
            yield Path(dir_path) / dirname
