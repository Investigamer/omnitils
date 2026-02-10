"""
* Core Fetch Utilities
* General core utilities for making requests.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import json
from pathlib import Path
from typing import Optional

import requests
from requests import Session

# Default chunk size when using iter_content to save a file
chunk_size_default = 1024 * 1024 * 8

# Default header to pass with requests
request_header_default = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/39.0.2171.95 Safari/537.36"
}


"""
* Session Utility Funcs
"""


def get_new_session(
    headers: Optional[dict] = None,
    stream: bool = False,
    path_cookies: Optional[Path] = None
) -> Session:
    """Returns a Session object equipped with provided features.

    Args:
        headers: Headers object to pass with requests, uses default if not provided.
        stream: Whether to use "stream" when downloading assets.
        path_cookies: Path to cookies file to load saved cookies from, will skip cookies if not provided.

    Returns:
          Session object.
    """
    # Create the Session object
    sess: Session = requests.session()
    if headers is None:
        headers = request_header_default.copy()
    sess.headers = headers
    if stream:
        sess.stream = True

    # Load cookies if provided, return the Session
    if path_cookies and path_cookies.is_file():
        with open(path_cookies, 'r', encoding='utf-8') as f:
            for k, v in json.load(f):
                sess.cookies[k] = v
    return sess
