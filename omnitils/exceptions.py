"""
* Exception Utilities
* Generalized utilities for dealing with exceptions.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
from contextlib import suppress
from logging import getLogger
from typing import Callable, Any, Optional

"""
* Utility Decorators
"""


def log_on_exception(logr: Any = None) -> Callable:
    """Decorator to log any exception that occurs.

    Args:
        logr: Logger object to output any exception messages.

    Returns:
        Wrapped function.
    """
    logr = logr or getLogger()

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Final exception catch
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logr.log_exception(e)
                raise e
        return wrapper
    return decorator


def return_on_exception(response: Optional[Any] = None) -> Callable:
    """Decorator to handle any exception and return appropriate failure value.

    Args:
        response: Value to return if an exception occurs.

    Returns:
        Wrapped function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Final exception catch
            with suppress(Exception):
                return func(*args, **kwargs)
            return response
        return wrapper
    return decorator
