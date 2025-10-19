from collections.abc import Callable, Iterable
from time import sleep, time
from typing import ParamSpec, TypeVar

from limits import RateLimitItem
from limits.strategies import RateLimiter

T = TypeVar("T")
P = ParamSpec("P")


class RateLimitError(Exception):
    pass


def rate_limit(
    limiter: RateLimiter,
    limit: RateLimitItem,
    reschedule: bool = True,
    identifiers: Iterable[str] = tuple(),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for rate_limiting function calls.

    Args:
        limiter: Limiting strategy.
        limit: The limit, e.g, 10 calls per second.
        reschedule: How long to sleep in seconds before reattempting. Pass 0 to raise `RateLimitError` instead when limit is exceeded.
        identifier: Identifiers that can be used to separate this limit from oters.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            if reschedule:
                while not limiter.hit(limit, *identifiers):
                    window = limiter.get_window_stats(limit, *identifiers)
                    sleep(window.reset_time - time())
            elif not limiter.hit(limit, *identifiers):
                raise RateLimitError(f"Limit exceeded for '{identifiers}' '{limit}'")
            return func(*args, **kwargs)

        return wrapper

    return decorator
