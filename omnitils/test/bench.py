"""
* Benchmarking Utilities
* Generalized utilities for performing benchmarking tests.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from time import perf_counter
from typing import Optional, Callable, Any

# Third Party
from loguru import logger

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


def time_function(func: Callable) -> Callable:
    """Print the execution time in seconds of any decorated function.

    Args:
        func: The function to wrap.

    Returns:
        Wrapped function.
    """
    def wrapper(*args, **kwargs):
        """Wraps the function call in a `perf_counter` timer."""
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        execution_time = end_time - start_time
        logger.info(f"Executed {func.__name__} in {execution_time:.4f} seconds")
        return result
    return wrapper


"""
* Util Funcs
"""


def benchmark_funcs(
    funcs: list[tuple[Callable, list[Any]]],
    iterations: int = 1000,
    reset_func: Optional[Callable] = None
) -> None:
    """Test the execution time of a new function against an older function.

    Args:
        funcs: List of tuples containing a func to test and args to pass to it.
        iterations: Number of calls to each function to perform, must be higher than 1.
        reset_func: Optional function to call to reset app state between actions.
    """
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
