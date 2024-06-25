"""
* Logging Utilities
* Generalized utilities for loggers and logging output.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import copy
from typing import Any, Callable, Optional
import sys

# Third Party Imports
from loguru import logger as loguru_logger
from loguru._logger import Logger

# Pre-defined formats
CONTINUE_FORMAT = '<msg>{message}</msg>'
CASUAL_FORMAT = ("<w>{time:YY}.{time:MM}.{time:DD} {time:HH}:{time:mm}:{time:ss} <b>|</b> "
                 "<lvl>{level: <8}</lvl> <b>|</b> "
                 "<msg>{message}</msg></w>")
VERBOSE_FORMAT = ("<w>{time:YY}.{time:MM}.{time:DD} {time:HH}:{time:mm}:{time:ss} <b>|</b> "
                  "<lvl>{level: <8}</lvl> <b>|</b> "
                  "<pos>[{location}]</pos> <b>|</b> <msg>{message}</msg></w>")
EXCEPTION_FORMAT = ("<w>{time:YY}.{time:MM}.{time:DD} {time:HH}:{time:mm}:{time:ss} <b>|</b> "
                    "<lvl>{level: <8}</lvl> <b>|</b> "
                    "<pos>[{location}]</pos> <b>|</b> <msg>{message}</msg>\n"
                    "<lr>{exception}</lr></w>\n")

# Continuation marker
TAG_CONTINUE = '[>]'

# Pre-defined colors
LEVEL_COLORS = {
    'INFO': dict(
        lvl=['le'],
        msg=['e'],
        pos=['lc']),
    'SUCCESS': dict(
        lvl=['lg'],
        msg=['g'],
        pos=['lc']),
    'ERROR': dict(
        lvl=['lr', 'b'],
        msg=['r'],
        pos=['lr']),
    'CRITICAL': dict(
        lvl=['lw', 'bg 130,0,0', 'b'],
        msg=['lr', 'b'],
        pos=['lr']),
    'WARNING': dict(
        lvl=['b', 'ly'],
        msg=['y'],
        pos=['ly']),
    'DEBUG': dict(
        lvl=['lm'],
        msg=['m'],
        pos=['lc']),
}


"""
* Logging Handlers
"""


def formatting_handler(record: dict[str, Any]) -> str:
    """An internal function used to return a granular format to the Loguru logger object.

    Args:
        record: Loguru logger record.

    Returns:
        Format to be used for logger output.
    """

    # Default format
    fmt = CASUAL_FORMAT
    terminator = '\n'

    # Check for special case formats
    _level = record['level'].name
    _is_verbose = bool(_level in ['WARNING', 'ERROR', 'CRITICAL'])
    _is_exception = record['exception']
    _message = record['message']

    # Check for a continuation line
    if not _is_exception:
        if _message.startswith(TAG_CONTINUE):
            _message = _message[3:]
            fmt = CONTINUE_FORMAT
        if _message.endswith(TAG_CONTINUE):
            _message = _message[:-3]
            terminator = ''
        record['message'] = _message

    # Check for verbose line
    if _is_verbose and fmt != CONTINUE_FORMAT:
        mod_func = '' if '<' in record['function'] else '.{function}'
        mod_location = '{module}' + mod_func + '.{line}'
        fmt = EXCEPTION_FORMAT if _is_exception else VERBOSE_FORMAT
        fmt = fmt.replace('{location}', mod_location)

    # Inject color tags
    for name, tag_group in LEVEL_COLORS[_level].items():
        left, right = '', ''
        for tag in tag_group:

            # Open and close defined
            if isinstance(tag, (tuple, list)):
                tag_open, tag_close = tag
                left += f'<{tag_open}>'
                right = f'</{tag_close}>{right}'
                continue

            # One definition
            left += f'<{tag}>'
            right = f'</{tag}>{right}'

        # Replace each end of the tag
        fmt = fmt.replace(f'<{name}>', left)
        fmt = fmt.replace(f'</{name}>', right)

    # Add line terminator and return
    fmt = fmt + terminator
    return fmt


"""
* Configure Main Logger
"""

# Pre-defined handlers
HANDLER_BASE = dict(
    sink=sys.stderr,
    format=formatting_handler,
    backtrace=True,
    diagnose=True,
    level='DEBUG'
)

# Reset and configure new logger
loguru_logger.remove()
logger = copy.deepcopy(loguru_logger)
logger.configure(handlers=[HANDLER_BASE])


"""
* Context Managers
"""


class TemporaryLogger:
    def __init__(
        self,
        handlers: Optional[list[dict[str, Any]]] = None
    ):
        self.logger: Logger = copy.deepcopy(loguru_logger)
        self._handlers: list[dict[str, Any]] = []
        if handlers is not None:
            for n in handlers:
                _base = HANDLER_BASE.copy()
                _base.update(n)
                self._handlers.append(_base)
        else:
            self._handlers.append(HANDLER_BASE.copy())

    def __enter__(self) -> Logger:

        # Add handlers
        for n in self._handlers:
            self.logger.add(**n)
        return self.logger

    def __exit__(self, exc_type, exc_value, traceback):

        # Remove the new sink
        del self.logger


"""
* Decorators
"""


def log_test_result(
    on_error: Optional[str] = None,
    on_success: Optional[str] = None,
    on_error_return: Optional[Any] = None,
    reraise: bool = False
) -> Callable:
    """Catch and log any errors, otherwise log a success.

    Args:
        on_error: Message to be logged if decorated function encounters an exception.
        on_success: Message to be logged if decorated function executes successfully.
        on_error_return: Return value if exception occurs, defaults to None.
        reraise: Whether to reraise an encountered exception after it is caught and logged.

    Returns:
        Wrapped function.
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            @logger.catch(reraise=True)
            def wrapped(*_arg, **_kw):
                _success, *_arg = _arg
                result = func(*_arg, **_kw)

                # Log success state
                if on_success is not None:
                    if '{return}' in _success:
                        _success = _success.replace('{return}', str(result))
                    logger.success(_success)
                return result

            # Control for error return value
            try:
                args = (on_success, *args)
                return wrapped(*args, **kwargs)
            except Exception as e:
                # Log exception state
                if on_error is not None:
                    logger.error(on_error)
                if reraise:
                    raise e
                return on_error_return

        return wrapper

    return decorator


"""
* Logger Utility Funcs
"""


def get_logger(handlers: Optional[list[dict[str, Any]]] = None) -> Logger:
    """Return a unique loguru logger object with optional provided handlers.

    Args:
        handlers: A list of handler dict definitions, otherwise will use the default handler.

    Returns:
        A unique loguru logger object.
    """
    _logger: Logger = copy.deepcopy(loguru_logger)
    _handlers: list[dict[str, Any]] = []

    # Handlers provided
    if handlers is not None:
        for n in handlers:
            _base = HANDLER_BASE.copy()
            _base.update(n)
            _handlers.append(_base)
        [_logger.add(**n) for n in _handlers]
        return _logger

    # Use default handler
    _logger.add(**HANDLER_BASE)
    return _logger
