"""
* Google Drive Utilities
* Generalized utilities for accessing Google Drive files or Google Drive API endpoints.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""

import os
import re
import shutil
from collections.abc import Callable, MutableMapping
from contextlib import suppress
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import NotRequired, TypedDict

import requests
import yarl
from requests import Response, Session

from omnitils.fetch import (
    chunk_size_default,
    download_file_from_response,
    get_new_session,
    request_header_default,
)
from omnitils.files import dump_data_file, get_temporary_file, mkdir_full_perms
from omnitils.strings import decode_url

_logger = getLogger(__name__)

"""
* Enums
"""


@dataclass
class GoogleReg:
    """Defined Google URL regex patterns."""

    URL: re.Pattern[str] = re.compile(r'"downloadUrl":"([^"]+)')
    FORM: re.Pattern[str] = re.compile(r'id="download-form" action="(.+?)"')
    EXPORT: re.Pattern[str] = re.compile(r'href="(/uc\?export=download[^"]+)')
    ERROR: re.Pattern[str] = re.compile(r'<p class="uc-error-subcaption">(.*)</p>')


"""
* Types
"""


class GoogleDriveMetadata(TypedDict):
    """Relevant metadata for a file hosted on Google Drive."""

    description: NotRequired[str]
    name: str
    size: int


"""
* Google Drive Utils
"""


def gdrive_get_confirmation_url(contents: str) -> yarl.URL:
    """Get the correct URL for downloading a Google Drive file from a potential
        confirmation page contents.

    Args:
        contents: Google Drive page contents.

    Returns:
        URL object targeting the hosted file.
    """
    for line in contents.splitlines():
        if m := GoogleReg.EXPORT.search(line):
            # Google Docs URL
            return decode_url(f"https://docs.google.com{m.groups()[0]}")
        if m := GoogleReg.FORM.search(line):
            # Download URL from Form
            return decode_url(m.groups()[0])
        if m := GoogleReg.URL.search(line):
            # Download URL from JSON
            return decode_url(m.groups()[0])
        if m := GoogleReg.ERROR.search(line):
            # Error Returned
            raise OSError(m.groups()[0])
    raise OSError(
        "Google Drive file has been made private or has reached its daily request limit."
    )


def gdrive_process_url(
    url: str | yarl.URL,
    sess: Session | None = None,
    headers: MutableMapping[str, str | bytes] | None = None,
    path_cookies: Path | None = None,
) -> tuple[Session, Response] | None:
    """Tests a Gdrive file URL to ensure it is the absolute download URL. If it isn't,
        attempt to redirect to the absolute URL based on Google Drive confirmation. Return a valid session and
        response object if successful, otherwise None.

    Args:
        url: Url to Google Drive asset.
        sess: Session object to use for requests, create one if not provided.
        headers: Headers to pass when creating a new Session object, if provided.
        path_cookies: Path to cookies file to load saved cookies from, will skip cookies if not provided.

    Returns:
        A tuple containing the Session object and Response from correct URL, if successful. Returns None if
            a working URL couldn't be established or Google Drive denies access to the file.
    """
    # Ensure session object, then initialize request
    if not sess:
        sess = get_new_session(headers=headers, stream=True, path_cookies=path_cookies)
    res = sess.get(str(url))

    # Update cookies
    if path_cookies:
        gdrive_update_cookies(sess, path_cookies)

    # Is this the right file?
    if "Content-Disposition" in res.headers:
        return sess, res

    # Try again with updated URL from confirmation
    try:
        return gdrive_process_url(
            url=gdrive_get_confirmation_url(res.text),
            sess=sess,
            headers=headers,
            path_cookies=path_cookies,
        )
    except Exception:
        _logger.exception(f"Google Drive denied access to the file at URL: {url}")
        res.close()
        sess.close()


"""
* Manage Gdrive Sessions
"""


def gdrive_update_cookies(sess: Session, path_cookies: Path) -> None:
    """Update cookies file using Gdrive session.

    Args:
        sess: Session object to pull cookies from.
        path_cookies: Path to local cookies file.
    """
    dump_data_file(
        obj=[
            (k, v)
            for k, v in sess.cookies.items()
            if not k.startswith("download_warning_")
        ],
        path=path_cookies,
    )


"""
* Fetching Metadata
"""


def gdrive_get_metadata(
    file_id: str, api_key: str, header: MutableMapping[str, str | bytes] | None = None
) -> GoogleDriveMetadata | None:
    """Get the metadata of a given template file.

    Args:
        file_id: ID of the Google Drive file.
        api_key: Google Drive API key.
        header: Optional header to pass with request.

    Returns:
        Metadata of the Google Drive file.
    """
    if header is None:
        header = request_header_default.copy()
    with (
        suppress(Exception),
        requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            headers=header,
            params={"alt": "json", "fields": "description,name,size", "key": api_key},
        ) as req,
    ):
        if req.status_code != 200:
            return
        result = req.json()
        if "name" in result and "size" in result:
            return result

    # Request was unsuccessful
    return


"""
* Downloading Files
"""


def gdrive_download_file(
    url: yarl.URL | str,
    path: Path,
    callback: Callable[[int, int], None] | None = None,
    headers: MutableMapping[str, str | bytes] | None = None,
    path_cookies: Path | None = None,
    allow_resume: bool = True,
    chunk_size: int = chunk_size_default,
) -> Path | None:
    """Download a file from Google Drive using its file ID.

    Note:
        Ideal file URL: https://drive.google.com/uc?id={file_id}

    Args:
        url: Google Drive file ID.
        path: Path to save downloaded file.
        callback: Function to call on each chunk downloaded.
        headers: Headers object to pass with request, uses default if not provided.
        path_cookies: Path to cookies file, don't use cookies if not provided.
        allow_resume: Whether to allow resuming a previous download.
        chunk_size: Chunk size in bytes when downloading the file with `iter_content`. Defaults to 8MB.

    Returns:
        Path to the downloaded file if successful, otherwise None.
    """
    # Ensure path and load a temporary file
    mkdir_full_perms(path.parent)
    file = get_temporary_file(path=path, ext=".drive", allow_existing=allow_resume)
    size = file.stat().st_size

    # Add range header if file is partially downloaded
    headers = headers or request_header_default.copy()
    if size > 0:
        headers["Range"] = f"bytes={size}-"

    # Attempt to create a session and request from URL
    check = gdrive_process_url(url=url, headers=headers, path_cookies=path_cookies)
    if not check:
        # gdrive_process_url logs its own errors
        return
    sess, res = check

    # Attempt to download the file
    try:
        _result = download_file_from_response(
            response=res, path=file, callback=callback, chunk_size=chunk_size
        )
    except Exception:
        # Exception occurred
        _logger.exception(f"Google Drive download failed:\n{path.name} | {url}")
        return
    finally:
        res.close()
        sess.close()

    # Rename temporary file
    if not (path.is_file() and os.path.samefile(file, path)):
        shutil.move(file, path)

    return path
