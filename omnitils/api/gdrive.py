"""
* Google Drive Utilities
* Generalized utilities for accessing Google Drive files or Google Drive API endpoints.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from contextlib import suppress
import json
from dataclasses import dataclass
from pathlib import Path
import re
import textwrap
from typing import Optional, Callable, TypedDict, NotRequired, Union

# Third Party Imports
import requests
import yarl

# Local Imports
from omnitils.fetch import request_header_default
from omnitils.fetch.download import download_file_with_callback
from omnitils.files import mkdir_full_perms, get_temporary_file, dump_data_file
from omnitils.strings import decode_url

"""
* Enums
"""


@dataclass
class GoogleReg:
    """Defined Google URL regex patterns."""
    URL: re.Pattern = re.compile(r'"downloadUrl":"([^"]+)')
    FORM: re.Pattern = re.compile(r'id="download-form" action="(.+?)"')
    EXPORT: re.Pattern = re.compile(r'href="(/uc\?export=download[^"]+)')
    ERROR: re.Pattern = re.compile(r'<p class="uc-error-subcaption">(.*)</p>')


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


def get_url_from_gdrive_confirmation(contents: str) -> yarl.URL:
    """Get the correct URL for downloading Google Drive file.

    Args:
        contents: Google Drive page data.

    Returns:
        URL object pointing to the hosted file resource.
    """
    for line in contents.splitlines():
        if m := GoogleReg.EXPORT.search(line):
            # Google Docs URL
            return decode_url(f'https://docs.google.com{m.groups()[0]}')
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
        "Google Drive file has been made private or has reached its daily request limit.")


"""
* Request Funcs
"""


def get_google_drive_metadata(
    file_id: str,
    api_key: str,
    header: Optional[dict] = None
) -> Optional[GoogleDriveMetadata]:
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
    with suppress(Exception):
        with requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            headers=header,
            params={
                'alt': 'json',
                'fields': 'description,name,size',
                'key': api_key}
        ) as req:
            if not req.status_code == 200:
                return
            result = req.json()
            if 'name' in result and 'size' in result:
                return result

    # Request was unsuccessful
    return


def download_google_drive(
    url: Union[yarl.URL, str],
    path: Path,
    callback: Callable,
    path_cookies: Optional[Path] = None
) -> bool:
    """Download a file from Google Drive using its file ID.

    Note:
        URL example: https://drive.google.com/uc?id={file_id}

    Args:
        url: Google Drive file ID.
        path: Path to save downloaded file.
        callback: Function to call on each chunk downloaded.
        path_cookies: Path to cookies file, don't use cookies if not provided.

    Returns:
        True if download successful, otherwise False.
    """

    # Ensure path and load a temporary file
    mkdir_full_perms(path.parent)
    file, size = get_temporary_file(
        path=path, ext='.drive')

    # Add range header if file is partially downloaded
    header = request_header_default.copy()
    if size > 0:
        header["Range"] = f"bytes={str(size)}-"

    # Create initial session
    sess = requests.session()

    # Load cookies if provided and exists
    if path_cookies and path_cookies.is_file():
        with open(path_cookies, 'r', encoding='utf-8') as f:
            for k, v in json.load(f):
                sess.cookies[k] = v

    # Get file resource
    while True:
        res = sess.get(str(url), headers=header, stream=True)

        # Save cookies
        if path_cookies:
            dump_data_file([
                (k, v) for k, v in sess.cookies.items()
                if not k.startswith("download_warning_")
            ], path_cookies)

        # Is this the right file?
        if "Content-Disposition" in res.headers:
            break

        # Need to redirect with confirmation
        try:
            url = get_url_from_gdrive_confirmation(res.text)
        except Exception as e:
            sess.close()
            err = '\n'.join(textwrap.wrap(str(e)))
            print(f'Access denied with the following error:\n{err}')
            return False

    # Start the download
    result = download_file_with_callback(
        file=file,
        res=res,
        path=path,
        callback=callback)
    sess.close()
    return result
