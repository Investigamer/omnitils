"""
* Schema Utilities
* Generalized utilities for creating and validating schemas.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
from typing import Any

from pydantic import BaseModel

"""
* Types
"""


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


class DictSchema(Schema):
    """Dictionary schema class. Returns all new instances as a dictionary."""

    def __new__(cls, **data):
        """Return new instance as a dictionary."""
        new = super().__new__(cls)
        new.__init__(**data)
        return new.model_dump()


class ArbitraryDictSchema(DictSchema):
    """Dictionary schema class allowing for arbitrary types."""

    class Config:
        arbitrary_types_allowed = True
