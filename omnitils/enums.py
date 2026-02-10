"""
* Enums Utilities
* Generalized utility Enum classes.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
from enum import Enum, EnumMeta
from typing import Iterator, Any

from omnitils.properties import default_prop


"""
* String Enum Classes
"""


class ConstantMeta(EnumMeta):
    """Metaclass for constant enums."""

    def __iter__(cls) -> Iterator[Any]:
        """Iterate over the Enum collection."""
        for n in cls.__members__.values():
            yield n.value

    def __contains__(cls, item: Any) -> bool:
        """Check if item is contained in Enum collection."""
        return bool(item in cls.__members__.values())

    def items(cls) -> Iterator[tuple[str, Any]]:
        """Iterate over the names and values contained in the Enum collection."""
        for k, v in cls.__members__.items():
            yield k, v.value

    @default_prop
    def Default(cls) -> Any:
        """Allow for a 'default' Enum in the collection, overwrite this to manually define a default
            value."""
        return cls._value2member_map_.__iter__().__next__()


class StrConstantMeta(EnumMeta):
    """Metaclass for string constant enums."""

    def __contains__(cls, item: str) -> bool:
        """Check if item is contained in Enum collection."""
        return bool(item in cls.__members__.values())

    def __iter__(cls) -> Iterator[str]:
        """Iterate over the Enum collection."""
        for n in cls.__members__.values():
            yield n.value

    def items(cls) -> Iterator[tuple[str, str]]:
        """Iterate over the names and values contained in the Enum collection."""
        for k, v in cls.__members__.items():
            yield k, v.value

    @default_prop
    def Default(cls) -> str:
        """Allow for a 'default' Enum in the collection, overwrite this to manually define a default
            value."""
        return cls._value2member_map_.__iter__().__next__()


"""
* String Enum Classes
"""


class StrConstant(str, Enum, metaclass=StrConstantMeta):
    """Enum constant where the value is always a string."""

    def __str__(self) -> str:
        """Use cached value for string representation."""
        return self.value

    @default_prop
    def value(self) -> str:
        """Cache each value and cast as a string."""
        return str(self._value_)
