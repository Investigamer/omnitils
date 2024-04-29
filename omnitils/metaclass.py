"""
* Metaclass Utilities
* General utility meta classes.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""

"""
* Meta-class Utils
"""


class Singleton(type):
    """Maintains a single instance of any child class to return for any subsequent calls."""
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
