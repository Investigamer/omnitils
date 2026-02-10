"""
* String Utilities
* Generalized utilities for working with strings.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import codecs
from datetime import datetime
import html
import string
from typing import Optional, Union
import unicodedata
from urllib import parse

import yarl
from dateutil import parser

STR_BOOL_MAP = {
    '1': True,
    'y': True,
    't': True,
    'on': True,
    'yes': True,
    'true': True,
    '0': False,
    'n': False,
    'f': False,
    'no': False,
    'off': False,
    'false': False
}

"""
* String Comparisons
"""


def str_to_bool(text: str) -> bool:
    """Converts a truthy string value to a bool. Conversion is case-insensitive.

    Args:
        text: String to check for boolean value.

    Notes:
        - Values are not case-sensitive.
        - True values are 1, t, y, on, yes, and true.
        - False values are 0, f, n, no, off, and true.

    Returns:
        Equivalent boolean value.

    Raises:
        ValueError: If string provided isn't a recognized truthy expression.
    """
    try:
        return STR_BOOL_MAP[text.lower()]
    except KeyError:
        raise ValueError(f"Unrecognized boolean value '{text}'!")


def str_to_bool_safe(text: str, default: bool = False) -> bool:
    """Shorthand for `str_to_bool` which returns default if exception is raised."""
    try:
        return STR_BOOL_MAP[text.lower()]
    except KeyError:
        return default


"""
* String Conversions
"""


def str_to_alnum(text: str, replace_with: str = ' ') -> str:
    """Converts all characters that aren't alphanumeric to spaces or another provided character.

    Args:
        text: String to convert.
        replace_with: Character to replace non-alphanumeric characters with. Defaults to space.

    Return:
        Converted string.
    """
    return ''.join([
        n if n.isalnum() else replace_with
        for n in text
    ])


def normalize_str(text: str, no_space: bool = False) -> str:
    """Normalizes a string for safe comparison.

    Args:
        text: String to normalize.
        no_space: If True remove all spaces, otherwise just leading and trailing spaces.

    Returns:
        Normalized string.
    """
    # Ignore accents and unusual characters
    st = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf8")

    # Remove spaces?
    st = st.replace(' ', '') if no_space else st.strip()

    # Remove punctuation and make lowercase
    return st.translate(str.maketrans("", "", string.punctuation)).lower()


def normalize_datestr(
        date_str: str,
        date_fmt: str = '%Y-%m-%d',
        date_default: Optional[datetime] = None
) -> str:
    """Normalizes a date string, controlling for potential edge cases.

    Args:
        date_str: Date string to normalize.
        date_fmt: Date format for the output string.
        date_default: Datetime object providing default values for missing
            date and time components in the string

    Returns:
        Normalized date string in the provided format.
    """
    # Replace any invalid integers
    items = [n.strip() for n in str_to_alnum(date_str).split(' ')]
    normalized = ' '.join(['1' if i.isnumeric() and 1 > int(i) else i for i in items])

    # Parse into a date object
    try:
        return parser.parse(
            timestr=normalized,
            default=date_default or datetime(
                year=datetime.today().year,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0)
        ).strftime(date_fmt)
    except ValueError as e:
        print(e)
        return datetime.today().strftime(date_fmt)


def normalize_ver(st: str) -> str:
    """Normalize a version string for safe comparison.

    Args:
        st: String to normalize.

    Returns:
        Normalized version string.
    """
    return ''.join([n for n in st if n in '.0123456789'])


"""
* URL Util Funcs
"""


def decode_url(url: str) -> yarl.URL:
    """Unescapes and decodes a URL string and returns it as a URL object.

    Args:
        url: URL string to format.

    Returns:
        Formatted URL object.
    """
    st = codecs.decode(
        html.unescape(parse.unquote(url)),
        'unicode_escape')
    return yarl.URL(st)


"""
* Multiline Utils
"""


def is_multiline(text: Union[str, list[str]]) -> Union[bool, list[bool]]:
    """Check if text or list of texts given contains multiline text (a newline character).

    Args:
        text: String to check or list of strings to check.

    Returns:
        True/False or list of True/False values.
    """
    # String Given
    if isinstance(text, str):
        if '\n' in text or '\r' in text:
            return True
        return False
    # List Given
    if isinstance(text, list):
        return [bool('\n' in t or '\r' in t) for t in text]
    # Invalid data type provided
    raise Exception("Invalid type passed to 'is_multiline', can only accept a string or list of strings.\n"
                    f"Value received: {text}")


def strip_lines(text: str, num: int, sep: str = '\n') -> str:
    """Removes a number of leading or trailing lines from a multiline string.

    Args:
        text: Multiline string.
        num: Positive integer for number leading lines, negative integer for number of trailing lines.
        sep: Separator used to split lines, defaults to '\n'.

    Returns:
        String with lines stripped.
    """
    if num == 0:
        return text
    if num < 0:
        return '\n'.join(text.split(sep)[:num])
    return '\n'.join(text.split(sep)[num:])


def get_line(text: str, i: int, sep: str = '\n') -> str:
    """Get line by index from a multiline string.

    Args:
        text: Multiline string.
        i: Index of the line.
        sep: Separator used to split lines, defaults to '\n'.

    Returns:
        Isolated line.
    """
    if abs(i) > text.count('\n'):
        raise IndexError(f"Not enough lines in multiline string. Index of {i} is invalid.")
    return text.split(sep)[i]


def get_lines(text: str, num: int, sep: str = '\n') -> str:
    """Separate a number of lines from a multiline string.

    Args:
        text: Multiline string.
        num: Number of lines to separate and return, negative integer for trailing lines.
        sep: Newline separator to use for split, defaults to '\n'.

    Returns:
        Isolated lines.
    """
    if num == 0 or abs(num) > text.count('\n') + 1:
        return text
    if num < 0:
        return '\n'.join(text.split(sep)[num:])
    return '\n'.join(text.split(sep)[:num])
