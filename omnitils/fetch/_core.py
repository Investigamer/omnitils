"""
* Core Fetch Utilities
* General core utilities for making requests.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""

# Default chunk size when using iter_content to save a file
chunk_size_default = 1024 * 8

# Default header to pass with requests
request_header_default = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/39.0.2171.95 Safari/537.36"
}
