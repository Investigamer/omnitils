"""
* Exception Utilities
* Generalized utilities for dealing with exceptions.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""

# Standard Library Imports
from contextlib import suppress
from typing import Callable, Any, ParamSpec, Protocol, TypeVar, overload

T = TypeVar("T")
V = TypeVar("V")
P = ParamSpec("P")


class ExceptionLogger(Protocol):
    def log_exception(self, error: Exception, *args: Any, **kwargs: Any) -> Any: ...


"""
* Utility Decorators
"""


def log_on_exception(
    logr: ExceptionLogger,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to log any exception that occurs.

    Args:
        logr: Logger object to output any exception messages.

    Returns:
        Wrapped function.
    """
    # Normal logger does not have log_exception function
    # so we can't default to it.
    # logr = logr or getLogger()

    def decorator(func: Callable[P, T]):
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            # Final exception catch
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logr.log_exception(e)
                raise e

        return wrapper

    return decorator


@overload
def return_on_exception(
    response: T,
) -> Callable[[Callable[P, V]], Callable[P, V | T]]: ...


@overload
def return_on_exception(
    response: T | None = None,
) -> Callable[[Callable[P, V]], Callable[P, V | T | None]]: ...


def return_on_exception(
    response: T | None = None,
) -> Callable[[Callable[P, V]], Callable[P, V | T | None]]:
    """Decorator to handle any exception and return appropriate failure value.

    Args:
        response: Value to return if an exception occurs.

    Returns:
        Wrapped function.
    """

    def decorator(func: Callable[P, V]):
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            # Final exception catch
            with suppress(Exception):
                return func(*args, **kwargs)
            return response

        return wrapper

    return decorator
