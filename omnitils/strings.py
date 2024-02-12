"""
* String Utilities
* Generalized utilities for working with strings.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import string
from typing import Optional

import unicodedata
from datetime import datetime
from dateutil import parser

"""
* String Util Funcs
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
