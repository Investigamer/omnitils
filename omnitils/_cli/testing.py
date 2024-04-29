"""
* CLI Commands: Testing
* Internal testing utility commands.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import os
import shutil
from pathlib import Path

# Third Party Imports
import click
from loguru import logger

# Local Imports
from omnitils.api.github import (
    gh_download_repository,
    gh_download_directory_files)

# Test resources
temp_dir = Path(os.getcwd(), 'temp')

"""
* Test Group: Github
"""


@click.command()
def test_gh_download_repository():
    """Tests the use of `omnitils.fetch.gh_download_repository`."""

    # Setup test
    # Todo: Create context handler for creating and disposing of temporary directory
    if not temp_dir.is_dir():
        os.mkdir(temp_dir)

    # Perform test
    extracted = gh_download_repository(
        user='Investigamer',
        repo='omnitils',
        path=temp_dir)
    check_file = extracted / 'poetry.lock'
    try:
        # Check repo directory
        assert extracted.is_dir()
        try:
            # Check test file
            assert check_file.is_file()
            logger.success('Test passed!')
        except AssertionError:
            logger.error('Test file missing from downloaded repo!')
        shutil.rmtree(extracted)
    except AssertionError:
        logger.error('Repo directory not downloaded!')

    # Test completed
    shutil.rmtree(temp_dir)


@click.command()
def test_gh_download_directory_files():
    """Tests the user of `omnitils.fetch.gh_download_directory_files`."""

    # Setup test
    if not temp_dir.is_dir():
        os.mkdir(temp_dir)

    # Perform test
    files_downloaded = gh_download_directory_files(
        user='Investigamer',
        repo='omnitils',
        repo_dir='omnitils',
        path=temp_dir)
    try:
        # Check repo directory
        assert len(files_downloaded) > 0
        [os.remove(n) for n in files_downloaded]
        logger.success('Test passed!')
    except AssertionError:
        return logger.error('No files downloaded from repo!')

    # Test completed
    shutil.rmtree(temp_dir)


@click.group(
    commands={
        'files': test_gh_download_directory_files,
        'repo': test_gh_download_repository
    }
)
def github_group():
    """Command group for testing the `fetch.github` module."""
    pass


"""
* Main Testing Group
"""


@click.group(commands={'fetch-gh': github_group})
def testing_group():
    """Command group for performing tests."""
    pass
