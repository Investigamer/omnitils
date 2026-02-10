"""
* Dict Utilities
* Generalized utilities for working with dictionaries.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
from typing import Hashable, Any

"""
* Dict Inversions
"""


def invert_map(d: dict[Hashable, Hashable]) -> dict[Hashable, Hashable]:
    """Flips the key, val in a dictionary to val, key.

    Args:
        d: Dictionary where the values are hashable.

    Returns:
        Reversed dictionary.
    """
    inverted = {}
    for k, v in d.items():
        inverted.setdefault(v, k)
    return inverted


def invert_map_multi(d: dict[Hashable, Hashable]) -> dict[Hashable, list[Hashable]]:
    """Flips the key, val in a dictionary to val, [keys], preserving cases where the same
    value is mapped to multiple keys.

    Args:
        d: Dictionary where the values are hashable.

    Returns:
        Reversed dictionary.
    """
    inverted = {}
    for k, v in d.items():
        inverted.setdefault(v, []).append(k)
    return inverted


"""
* Dict Sorting
"""


def sort_by_key(d: dict, reverse: bool = False) -> dict:
    """Sort a dictionary by its key.

    Args:
        d: Dictionary to sort by its key.
        reverse: Whether to reverse the sorting order.

    Returns:
        Key sorted dictionary.
    """
    return dict(sorted(d.items(), reverse=reverse))


def sort_by_value(d: dict, reverse: bool = False) -> dict:
    """Sort a dictionary by its value.

    Args:
        d: Dictionary to sort by its value.
        reverse: Whether to reverse the sorting order.

    Returns:
        Value sorted dictionary.
    """
    return dict(sorted(d.items(), key=lambda item: item[1], reverse=reverse))


"""
* Dict Data Utils
"""


def next_item(d: dict) -> tuple[Hashable, Any]:
    """Extract the first key, value pair from a dictionary.

    Args:
        d: Dictionary to retrieve first key, value pair from.

    Returns:
        Tuple containing key, value.
    """
    return next(iter(d.items()))


def last_item(d: dict) -> tuple[Hashable, Any]:
    """Extract the last key, value pair from a dictionary.

    Args:
        d: Dictionary to retrieve last key, value pair from.

    Returns:
        Tuple containing key, value.
    """
    return list(d.items())[-1]
