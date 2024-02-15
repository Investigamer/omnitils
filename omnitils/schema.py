"""
* Schema Utilities
* Generalized utilities for creating and validating schemas.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Third Party Imports
from pydantic import BaseModel


class Schema(BaseModel):
    """Basic schema class allowing for defined types and default values."""


class DictSchema(Schema):
    """Dictionary schema class. Returns all new instances as a validated dictionary."""

    def __new__(cls, **data):
        """Return new instance as a dictionary."""
        new = super().__new__(cls)
        new.__init__(**data)
        return new.model_dump()
