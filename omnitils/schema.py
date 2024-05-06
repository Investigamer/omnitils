"""
* Schema Utilities
* Generalized utilities for creating and validating schemas.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from typing import Any

# Third Party Imports
from pydantic import BaseModel

"""
* Types
"""


PriorityMap = dict[str, list[tuple[str, str] | tuple[None, Any]]]


"""
* Schema Classes
"""


class Schema(BaseModel):
    """Basic schema class, extending the Pydantic BaseModel."""


class DictSchema(Schema):
    """Dictionary schema class. Returns all new instances as a dictionary."""

    def __new__(cls, **data):
        """Return new instance as a dictionary."""
        new = super().__new__(cls)
        new.__init__(**data)
        return new.model_dump()
