"""
* Schema Utilities
* Generalized utilities for creating and validating schemas.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from typing import Any, Generic, TypeVar

# Third Party Imports
from pydantic import BaseModel

"""
* Types
"""

T = TypeVar("T", bound=dict[str,Any])

PriorityMap = dict[str, list[str | tuple[str, str] | tuple[None, Any] | None]]


"""
* Schema Classes
"""


class Schema(BaseModel):
    """Basic schema class, extending the Pydantic BaseModel."""


class ArbitrarySchema(BaseModel):
    """Schema class allowing for arbitrary types."""

    class Config:
        arbitrary_types_allowed = True


class DictSchema(Schema, Generic[T]):
    """Dictionary schema class. Returns all new instances as a dictionary."""

    def __new__(cls, **data: Any) -> T:
        """Return new instance as a dictionary."""
        new: BaseModel = super().__new__(cls)
        new.__init__(**data)
        return new.model_dump() # pyright: ignore[reportReturnType]


class ArbitraryDictSchema(DictSchema[T]):
    """Dictionary schema class allowing for arbitrary types."""

    class Config:
        arbitrary_types_allowed = True
