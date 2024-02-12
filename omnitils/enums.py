"""
* Enums Utilities
* Generalized utility Enum classes.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from enum import Enum, EnumMeta
from functools import cached_property

"""
* String Enum Classes
"""


class StrEnumMeta(EnumMeta):
    """Metaclass for StrEnum."""

    def __contains__(cls, item: str) -> bool:
        return item in cls._value2member_map_


class StrEnum(str, Enum, metaclass=StrEnumMeta):
    """Enum where the value is always a string."""

    def __str__(self) -> str:
        return self.value

    @cached_property
    def value(self) -> str:
        return str(self._value_)

    @cached_property
    def Default(self) -> str:
        return "default"
