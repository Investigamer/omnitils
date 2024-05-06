"""
* Schema Utilities
* Generalized utilities for creating and validating schemas.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
from typing import Any, Optional

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


"""
* Schema Utility Functions
"""


def unify_schemas(
    data: dict[str, Optional[BaseModel | Schema]],
    schema: type[BaseModel] | type[Schema],
    priority_map: PriorityMap
) -> BaseModel | Schema:
    """Combines data from one or more Schemas into a unified map, using a priority map to decide which
        competing keys carry over.

    Args:
        data: Dictionary of schemas provided as input data.
        schema: Schema to combine data into.
        priority_map: Maps schema keys to an ordered list of data source priorities.

    Returns:
        New object of the provided schema.
    """
    imported_data = {}
    for key, sources in priority_map.items():
        for (source, value) in sources:

            # Fallback value
            if source is None:
                imported_data[key] = value

            # Try to get value from data source
            source_schema = data.get(source)
            if source_schema is not None:
                source_value = source_schema.get(value)
                if source_value is not None:
                    imported_data[key] = source_value

    # Return new Schema object
    return schema(**imported_data)
