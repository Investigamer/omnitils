"""
* Enums Utilities
* Generalized utility Enum classes.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from enum import Enum, EnumMeta
from functools import cached_property
from typing import Iterator, Any

# Local Imports
from omnitils.properties import default_prop

"""
* Enum Meta-classes
"""


class EnumCollection(EnumMeta):
    """Metaclass for StrEnum."""

    def __iter__(cls) -> Iterator[Any]:
        """Iterate over the Enum collection."""
        for n in cls._member_map_.values():
            yield n.value

    def __contains__(cls, item: Any) -> bool:
        """Check if item is contained in Enum collection."""
        return bool(item in cls._member_map_.values())

    @default_prop
    def Default(cls) -> Any:
        return cls._value2member_map_.__iter__().__next__()


"""
* String Enum Classes
"""


class StrEnum(str, Enum, metaclass=EnumCollection):
    """Enum where the value is always a string."""

    def __str__(self) -> str:
        return self.value

    @cached_property
    def value(self) -> str:
        return str(self._value_)


class URLEnum(Enum, metaclass=EnumCollection):
    """Enum where the value is always a URL object with an HTTPS scheme.

    Todo:
        Robustly test this Enum class.
    """

    def __str__(self):
        return str(self.value)

    def __truediv__(self, value):
        return self.value / value

    def __getattr__(self, item: str) -> Any:
        """Access anything except _value_, value, and __contains__ from the URL object."""
        if item not in ['_value_', 'value', '__contains__']:
            return self.value.__getattribute__(item)
        return self.__getattribute__(item)
