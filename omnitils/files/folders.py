"""
* Folder Utilities
* Generalized utilities for working with folders/directories.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import os
import random
import shutil
from pathlib import Path
from typing import Iterator, Optional

"""
* Creating Directories
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
    path.mkdir(parents=True, exist_ok=True)
    return path


"""
* Directory Information
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


def is_dir_empty(path: Path) -> bool:
    """Checks if the given directory is empty.

    Args:
        path: Path to the directory.

    Returns:
        True if the directory is empty, otherwise False.

    Raises:
        FileNotFoundError: If the given directory doesn't exist.
    """
    if not path.is_dir():
        raise FileNotFoundError('Directory does not exist: {}'.format(path))
    return not os.listdir(path)


"""
* Moving Directories and Contents
"""


def recur_move_dir(source: Path, target: Path, overwrite: bool = True) -> None:
    """Recursively moves a source directory to a target directory, allowing for overwriting existing
        files and directories if enabled.

    Args:
        source: The path to the directory which should be recursively moved.
        target: The path to move the directory to.
        overwrite: Whether to overwrite existing files and directories of the same name, defaults to True.

    Raises:
        FileExistsError: If overwrite is False and a move targets an existing file.
    """
    # Check if paths are the same
    if source == target:
        return

    # Check if target exists
    if target.exists() and overwrite is False:
        raise FileExistsError(f'{target} already exists!')
    if not target.exists():
        mkdir_full_perms(target)

    # Iterate over items in the source directory
    for src, dst in [(source / n, target / n) for n in os.listdir(source)]:

        # Check if destination exists
        if dst.exists() and overwrite is False:
            raise FileExistsError(f'{dst} already exists!')

        # Recurse down next directory or move file
        func = recur_move_dir if src.is_dir() else shutil.move
        func(src, dst)

    # Remove source directory if empty
    if not os.listdir(source):
        os.rmdir(source)


def recur_move_contents(source: Path, target: Path, overwrite: bool = True) -> None:
    """Recursively moves the contents of a source directory to a target directory, allowing for overwriting existing
        files and directories if enabled.

    Args:
        source: The path to the directory which should be recursively moved.
        target: The path to move the directory to.
        overwrite: Whether to overwrite existing files and directories of the same name, defaults to True.

    Raises:
        FileExistsError: If overwrite is False and a move targets an existing file.
    """
    # Check if paths are the same
    if source == target:
        return

    # Ensure target exists
    if not target.exists():
        mkdir_full_perms(target)

    # Move each item to target directory
    for src, dst in [(source / n, target / n) for n in os.listdir(source)]:

        # Handle disallowed existing files
        if dst.exists() and not overwrite:
            raise FileExistsError(f'{dst} already exists!')

        # Move file or directory recursively
        if src.is_dir():
            recur_move_dir(src, dst, overwrite=overwrite)
            continue
        shutil.move(src, dst)


def elevate_contents(path: Path, n: int = 1, overwrite: bool = False) -> Path:
    """Move the contents of a directory up 'n' levels in the directory hierarchy. If 'n' is greater than
        the amount of directories above the current directory, stop at the root.

    Args:
        path: The path to the directory whose contents are to be moved.
        n: The number of levels to move up in the directory hierarchy.
        overwrite: Whether to overwrite existing files with the same name in the target directory, defaults
            to False. If an existing file is encountered while False, raises a FileExistsError.

    Returns:
        Path to the new directory where contents are located.

    Raises:
        FileNotFoundError: If the directory provided doesn't exist.
        ValueError: If "n" was provided as a negative integer.
        FileExistsError: If overwrite is False and a move targets an existing file.
    """
    # Check for bad input
    if not path.is_dir():
        raise FileNotFoundError("The specified directory doesn't exist.")
    if n < 0:
        raise ValueError("The number of levels to raise contents cannot be negative.")

    # Select target, skip if unchanged
    target = path
    for _ in range(n):
        next_dir = target.parent
        if next_dir == target:
            break
        target = next_dir
    if n == 0 or target == path:
        return path

    # Recursively move the contents
    recur_move_contents(path, target, overwrite=overwrite)
    return target


"""
* Context Managers
"""


class DisposableDir:
    def __init__(self, path: Optional[Path] = None):
        """A context manager that creates and returns a temporary directory inside a given path (defaults to current
            directory) and disposes of that directory after the manager closes.

        Args:
            path: Path to create the disposable directory inside.
        """
        path = (path or Path.cwd()) / 'temp'
        name = path.name
        while path.exists():
            path = path.parent / f'{name}_{random.randint(1, 1000000)}'
        self._dir = path

    def __enter__(self) -> Path:
        """Create the disposable directory.

        Returns:
            Path to the disposable directory.
        """
        mkdir_full_perms(self._dir)
        return self._dir

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Remove the disposable directory."""
        shutil.rmtree(self._dir)
