"""
* CLI Commands: Testing
* Internal testing utility commands.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import os
import shutil

from loguru import logger
import typer

from omnitils.api.github import (
    gh_download_repository,
    gh_download_directory_files)
from omnitils.files import DisposableDir

# Command group
app = typer.Typer(
    name='test',
    help="A suite of commands for testing omnitils."
)

"""
* Test Group: Github
"""


@app.command("gh-repo")
def test_gh_download_repository():
    """Tests the use of `omnitils.fetch.gh_download_repository`."""

    # Setup test directory
    with DisposableDir() as temp_dir:

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


@app.command("gh-files")
def test_gh_download_directory_files():
    """Tests the user of `omnitils.fetch.gh_download_directory_files`."""

    # Setup test directory
    with DisposableDir() as temp_dir:

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
