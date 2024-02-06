"""
* Property Utilities
* General property decorator utilities.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
from typing import Callable


def default_property(func: Callable) -> property:
    """Alternative to the `@cached_property` decorator which:
        - Uses the wrapped function as a default value for the property.
        - Caches the default value when it is first accessed.
        - Allows the value to be changed later and caches the new value.
        - Allows the value to be deleted, which reroutes it to the default value.
    """
    attr_type = func.__annotations__.get('return', str) if (
        hasattr(func, '__annotations__')) else str
    cache_name = f"_{func.__name__}"

    def getter(self) -> attr_type:
        """Wrapper for getting cached value. If value doesn't exist, initialize it."""
        try:
            return getattr(self, cache_name)
        except AttributeError:
            value = func(self)
            setattr(self, cache_name, value)
            return value

    def setter(self, value: attr_type) -> None:
        """Setter for invalidating the property cache and caching a new value."""
        setattr(self, cache_name, value)

    def deleter(self) -> None:
        """Deleter for invalidating the property cache."""
        if hasattr(self, cache_name):
            delattr(self, cache_name)

    # Return complete property
    return property(getter, setter, deleter, getattr(func, '__doc__', ''))
