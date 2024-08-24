"""
* Benchmarking Utilities
* Generalized utilities for performing benchmarking tests.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
import functools
# Standard Library Imports
from time import perf_counter
from typing import Optional, Callable, Any

# Third Party
from omnitils.logs import logger as _logger

# Local Imports
from omnitils.schema import Schema

"""
* Types
"""


class BenchmarkResult(Schema):
    """Represents a benchmarking result."""
    value: Any
    average: float
    times: list = []
    name: str


"""
* Util Decorators
"""


class time_function:
    """Print the execution time in seconds of any decorated function.

    Args:
        msg_or_func:
            * If the decorator is not called, this serves as the decorated function which is cached for
                use in the wrapper.
            * If the decorator is called, you may provide a string used to format the logger output which
                that prints the execution time. This string supports optional format variables {f} and {t}.
                "f" will be formatted with the function name, "t" will be formatted with the execution time.
            * Example: "Function `{f}` completed in {t:.2f} seconds."
        logger: Logging object to use.
    """

    def __init__(self, msg_or_func: Optional[str | Callable] = None, logger: Any = None):
        self._func = None
        self._msg = 'Function `{f}` completed in {t:.4f} seconds.'
        self._logger = logger or _logger

        # Use argument as function or log format
        if callable(msg_or_func):
            self._func = msg_or_func
        elif isinstance(msg_or_func, str):
            self._msg = msg_or_func

    def __call__(
        self,
        *args,
        **kw
    ) -> Any:
        """Print the execution time in seconds of any decorated function.

        Returns:
            Wrapped function.
        """
        is_wrapped: bool = bool(self._func is None)
        _func: Callable = [*args].pop() if is_wrapped else self._func
        _func_name: str = _func.__name__

        @functools.wraps(_func)
        def wrapper(*_args, **_kwargs):
            """Wrapped function."""
            s = perf_counter()
            result = _func(*_args, **_kwargs)
            self._logger.info(
                self._msg.format(
                    f=_func_name,
                    t=(perf_counter() - s)))
            return result

        # Return result or wrapped function
        return wrapper if is_wrapped else wrapper(*args, **kw)


"""
* Util Funcs
"""


def benchmark_funcs(
    funcs: list[tuple[Callable, list[Any]]],
    iterations: int = 1000,
    reset_func: Optional[Callable] = None,
    logger: Any = None
) -> None:
    """Test the execution time of a new function against an older function.

    Args:
        funcs: List of tuples containing a func to test and args to pass to it.
        iterations: Number of calls to each function to perform, must be higher than 1.
        reset_func: Optional function to call to reset app state between actions.
        logger: Logging object to use.
    """
    logger = logger or _logger

    # Skip if no funcs provided
    if not funcs:
        return logger.critical('No functions provided for benchmarking.')
    if iterations < 1:
        return logger.critical('Iterations must be 1 or higher.')

    # Test configuration
    results: list[BenchmarkResult] = []
    best: float = 0

    # Test each function
    for func, args in funcs:
        times, value = [], None

        # Track the execution time across iterations
        for i in range(iterations):
            s = perf_counter()
            try:
                value = func(*args)
            except Exception as e:
                logger.error(f'Encountered an error in function "{func.__name__}"!')
                return logger.exception(e)
            times.append(perf_counter()-s)
            if reset_func:
                reset_func()

        # Append result and value
        results.append(
            BenchmarkResult(
                value=value,
                average=sum(times)/len(times),
                times=times,
                name=func.__name__))

    # Report results
    for i, r in enumerate(sorted(results, key=lambda item: item.average)):

        # Best result
        if i == 0:
            best = r.average
            logger.success(f'{r.name}: {r.average}')
            continue

        # Slower results
        pct_slower = round(((r.average - best) / ((r.average + best) / 2)) * 100, 2)
        logger.warning(f"{r.name}: {r.average} ({pct_slower}% Slower)")

    # Check if all values match
    if not results:
        return logger.warning('No results were found to compare.')
    if all(n.value == results[0].value for n in results):
        return logger.success('Values are identical!')

    # Values don't match
    logger.error("Values don't appear to be identical! See values below.")
    [logger.info(n.value) for n in results]
    return
