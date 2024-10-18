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

# Reset the loguru logger
loguru_logger.remove()
logger = copy.deepcopy(loguru_logger)

"""
* Default Logging Definitions
"""

# Pre-defined component
COMPONENT_TIME = "{time:YY}.{time:MM}.{time:DD} {time:HH}:{time:mm}:{time:ss}"
COMPONENT_LEVEL = "<lvl>{level: <8}</lvl>"
COMPONENT_LOCATION = "<pos>[{location}]</pos>"
COMPONENT_MESSAGE = "<msg>{message}</msg>"
COMPONENT_EXCEPTION = "<lr>{exception}</lr>"

# Common tags
TAGS_DEFAULT = ('<w>', '</w>')

# Pre-defined colors
LEVEL_COLORS = {
    'DEBUG': dict(
        lvl=['lm'],
        msg=['m'],
        pos=['lc']),
    'INFO': dict(
        lvl=['le'],
        msg=['e'],
        pos=['lc']),
    'SUCCESS': dict(
        lvl=['lg'],
        msg=['g'],
        pos=['lc']),
    'WARNING': dict(
        lvl=['b', 'ly'],
        msg=['y'],
        pos=['ly']),
    'ERROR': dict(
        lvl=['lr', 'b'],
        msg=['r'],
        pos=['lr']),
    'CRITICAL': dict(
        lvl=['lw', 'bg 130,0,0', 'b'],
        msg=['lr', 'b'],
        pos=['lr'])
}

"""
* Logging Handlers
"""


def colorize_log_format(log_fmt: str, log_level: str) -> str:
    """An internal utility function called by a handler to colorize custom tags in a log format string.

    Args:
        log_fmt: Log format string.
        log_level: Level of current log to be formatted.

    Returns:
        str: Colorized log format string.
    """

    # Get log level colors
    log_colors = LEVEL_COLORS.get(log_level) or LEVEL_COLORS['DEBUG']

    # Replace each tag
    for name, tag_group in log_colors.items():
        left, right = '', ''
        for tag in tag_group:

            # Open and close defined
            if isinstance(tag, (tuple, list)):
                if len(tag) > 1:
                    tag_open, tag_close = tag
                    left = f'{left}<{tag_open}>'
                    right = f'</{tag_close}>{right}'
                    continue
                elif len(tag) == 1:
                    tag = tag[0]

            # One definition
            left += f'<{tag}>'
            right = f'</{tag}>{right}'

        # Replace each opening and closing tag
        log_fmt = log_fmt.replace(f'<{name}>', left).replace(f'</{name}>', right)
    return log_fmt


def formatting_handler(record: dict[str, Any]) -> str:
    """An internal function used to return a granular format to the Loguru logger object.

    Args:
        record: Loguru logger record.

    Returns:
        str: Format to be used for logger output.
    """

    # Establish base values
    _level = record['level'].name
    _extra = record.pop('extra', {})
    _msg = record.get('message', '')
    _exception = record.get('exception')
    _fmt = ''

    # Check if exception exists and should be shown
    _main_tags = _extra.pop('main_tags', [])
    _show_time = bool(_extra.pop('show_time', True))
    _show_level = bool(_extra.pop('show_level', True))
    _show_message = bool(_extra.pop('show_message', True))
    _show_exception = bool(
        _extra.pop('show_exception', True) and
        hasattr(_exception, 'traceback') and
        _exception.traceback is not None)

    # Check for alternate separator
    _sep = _extra.pop('separator', ' <b>|</b> ')

    # Check for a continuation line
    terminator = '\n'
    if not _show_exception:
        if bool(_extra.pop('await_more', False)):
            terminator = ''
        if bool(_extra.pop('add_more', False)):
            return colorize_log_format(COMPONENT_MESSAGE, _level) + terminator

    def _add_component(_log_fmt, _component, _separator: Optional[str] = _sep) -> str:
        """Adds a component to a provided log format, with a separator."""
        if _log_fmt == '':
            return _component
        return _log_fmt + _separator + _component

    def _wrap_main_tags(_log_fmt: str):
        """Wraps the log format in the main surrounding tags."""
        _L, _R = TAGS_DEFAULT
        if _main_tags and isinstance(_main_tags, tuple) and len(_main_tags) == 2:
            _L, _R = _main_tags
        return _L + _log_fmt + _R + terminator

    # Add time
    if _show_time:
        _fmt = _add_component(_fmt, COMPONENT_TIME)

    # Add level
    if _show_level:
        _fmt = _add_component(_fmt, COMPONENT_LEVEL)

    # Add message
    if _show_message:
        _fmt = _add_component(_fmt, COMPONENT_MESSAGE)

    if _show_exception:
        _fmt = _add_component(_fmt, COMPONENT_EXCEPTION, '\n')

    # Inject color tags, wrap, terminate, and return
    return _wrap_main_tags(colorize_log_format(_fmt, _level))


# Pre-defined handlers
HANDLER_DEFAULT = dict(
    sink=sys.stderr,
    format=formatting_handler,
    backtrace=True,
    diagnose=True,
    level='DEBUG'
)


"""
* Configure Logger
"""


def reconfigure_logger(
    obj: Logger = logger,
    handlers: Optional[list[dict[str, Any]]] = None,
    opt_args: Optional[dict[str, Any]] = None,
    **kwargs
) -> Logger:
    """Returns a configured loguru logger object."""
    if not handlers:
        handlers = [HANDLER_DEFAULT]
    obj.configure(handlers=handlers, **kwargs)
    if opt_args is not None:
        return obj.opt(**opt_args)
    return obj


def get_logger(handlers: Optional[list[dict[str, Any]]] = None, **kwargs) -> Logger:
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
            _base = HANDLER_DEFAULT.copy()
            _base.update(n)
            _handlers.append(_base)
        return reconfigure_logger(_logger, _handlers, **kwargs)
    return reconfigure_logger(_logger, **kwargs)


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
                _base = HANDLER_DEFAULT.copy()
                _base.update(n)
                self._handlers.append(_base)
        else:
            self._handlers.append(HANDLER_DEFAULT.copy())

    def __enter__(self) -> Logger:

        # Add handlers
        self.logger = reconfigure_logger(self.logger, handlers=self._handlers)
        return self.logger

    def __exit__(self, exc_type, exc_value, traceback):

        # Remove the new sink
        del self.logger


class LogResults:
    """Context manager to log the success, failure, and/or exceptions within the context being executed. A success
    message (if provided) will be logged if the context completes without raising an exception, otherwise an error
    message (if provided) will be logged, and/or the exception itself if requested.

    Args:
        on_failure: Message to log if context encounters an exception, if provided.
        on_success: Message to log if context executes successfully, if provided.
        reraise: Whether to reraise an encountered exception after it is caught and logged.
        log_trace: Whether to log the traceback of any exception that occurs.
        log_obj: Logger object to use, defaults to the main omnitils logger.
    """

    def __init__(
        self,
        on_failure: Optional[str] = None,
        on_success: Optional[str] = None,
        reraise: bool = False,
        log_trace: bool = True,
        log_obj: Logger = logger
    ):
        self._on_failure = on_failure
        self._on_success = on_success
        self._reraise = reraise
        self._log_trace = log_trace
        self._logger = log_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):

        # Log error message and/or traceback
        if exc_type:
            if self._log_trace:
                if self._on_failure is None:
                    self._on_failure = 'The following exception occurred:'
                self._logger.exception(self._on_failure)
            elif self._on_failure:
                self._logger.error(self._on_failure)
            # Re-raise the exception
            return False if self._reraise else True

        # Context executed without errors
        if self._on_success:
            self._logger.success(self._on_success)


"""
* Decorators
"""


def log_test_result(
    on_failure: Optional[str] = None,
    on_success: Optional[str] = None,
    on_failure_return: Optional[Any] = None,
    reraise: bool = False,
    log_trace: bool = True,
    log_obj: Logger = logger
) -> Callable:
    """Catch and log any errors, otherwise log a success.

    Args:
        on_failure: Message to be logged if decorated function encounters an exception.
        on_success: Message to be logged if decorated function executes successfully.
        on_failure_return: Return value if exception occurs, defaults to None.
        reraise: Whether to reraise an encountered exception after it is caught and logged.
        log_trace: Whether to log the traceback of any exception that occurs.
        log_obj: Logger object to use, defaults to the main omnitils logger. Must be a loguru logger object.

    Returns:
        Wrapped function.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                with LogResults(
                    on_success=on_success,
                    on_failure=on_failure,
                    reraise=True,
                    log_trace=log_trace,
                    log_obj=log_obj
                ):
                    return func(*args, **kwargs)
            except Exception as e:
                if reraise:
                    raise e
                return on_failure_return
        return wrapper
    return decorator


# Configure main logger object
logger = reconfigure_logger(
    opt_args=dict(
        colors=True))
