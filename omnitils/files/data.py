"""
* Data File Utilities
* Generalized utilities for working with data files, i.e. JSON, YAML, etc.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import json
from contextlib import suppress
from pathlib import Path
from typing import Optional, TypedDict, Callable, Union
from threading import Lock

# Third Party Imports
from yaml import (
    load as yaml_load,
    dump as yaml_dump,
    Loader as yamlLoader,
    Dumper as yamlDumper)
from tomlkit import dump as toml_dump, load as toml_load

"""
* Types
"""


class DataFileType (TypedDict):
    """Data file type (json, toml, yaml, etc)."""
    load: Callable
    dump: Callable
    load_kw: dict[str, Union[Callable, bool, str]]
    dump_kw: dict[str, Union[Callable, bool, str]]


"""Data File: TOML (.toml) data type."""
DataFileTOML = DataFileType(
    load=toml_load,
    dump=toml_dump,
    load_kw={},
    dump_kw={'sort_keys': True})

"""Data File: YAML (.yaml) data type."""
DataFileYAML = DataFileType(
    load=yaml_load,
    dump=yaml_dump,
    load_kw={
        'Loader': yamlLoader},
    dump_kw={
        'allow_unicode': True,
        'Dumper': yamlDumper,
        'sort_keys': True,
        'indent': 2,
    })

"""Data File: JSON (.json) data type."""
DataFileJSON = DataFileType(
    load=json.load,
    dump=json.dump,
    load_kw={},
    dump_kw={
        'sort_keys': True,
        'indent': 2,
        'ensure_ascii': False
    })


"""
* Constants
"""

# File util locking mechanism
util_file_lock = Lock()

# Data types alias map
data_types: dict[str, DataFileType] = {
    '.toml': DataFileTOML,
    '.yaml': DataFileYAML,
    '.yml': DataFileYAML,
    '.json': DataFileJSON,
}
supported_data_types = tuple(data_types.keys())

"""
* Funcs
"""


def validate_data_type(path: Path) -> None:
    """Checks if a data file matches a supported data file type.

    Args:
        path: Path to the data file.

    Raises:
        ValueError: If data file type not supported.
    """
    # Check if data file is a supported data type
    if path.suffix.lower() not in supported_data_types:
        raise ValueError("Data file provided does not match a supported data file type.\n"
                         f"Types supported: {', '.join(supported_data_types)}\n"
                         f"Type received: {path.suffix}")


def validate_data_file(path: Path) -> None:
    """Checks if a data file exists and is a valid data file type. Raises an exception if validation fails.

    Args:
        path: Path to the data file.

    Raises:
        FileNotFoundError: If data file does not exist.
        ValueError: If data file type not supported.
    """
    # Check if file exists
    if not path.is_file():
        raise FileNotFoundError(f"Data file does not exist:\n{str(path)}")
    validate_data_type(path)


def load_data_file(
    path: Path,
    config: Optional[dict] = None
) -> Union[list, dict, tuple, set]:
    """Load data  object from a data file.

    Args:
        path: Path to the data file to be loaded.
        config: Dict data to modify DataFileType configuration for this data load procedure.

    Returns:
        Data object such as dict, list, tuple, set, etc.

    Raises:
        FileNotFoundError: If data file does not exist.
        ValueError: If data file type not supported.
        OSError: If loading data file fails.
    """
    # Check if data file is valid
    validate_data_file(path)

    # Pull the parser and insert user config into kwargs
    parser: DataFileType = data_types.get(path.suffix.lower(), {}).copy()
    if config:
        parser['load_kw'].update(config)

    # Attempt to load data
    with util_file_lock, suppress(Exception), open(path, 'r', encoding='utf-8') as f:
        data = parser['load'](f, **parser['load_kw']) or {}
        return data
    raise OSError(f"Unable to load data from data file:\n{str(path)}")


def dump_data_file(
    obj: Union[list, dict, tuple, set],
    path: Path,
    config: Optional[dict] = None
) -> None:
    """Dump data object to a data file.

    Args:
        obj: Iterable or dict object to save to data file.
        path: Path to the data file to be dumped.
        config: Dict data to modify DataFileType configuration for this data dump procedure.

    Raises:
        FileNotFoundError: If data file does not exist.
        ValueError: If data file type not supported.
        OSError: If dumping to data file fails.
    """
    # Check if data file is valid
    validate_data_type(path)

    # Pull the parser and insert user config into kwargs
    parser: DataFileType = data_types.get(path.suffix.lower(), {}).copy()
    if config:
        parser['dump_kw'].update(config)

    # Attempt to dump data
    with suppress(Exception), util_file_lock, open(path, 'w', encoding='utf-8') as f:
        parser['dump'](obj, f, **parser['dump_kw'])
        return
    raise OSError(f"Unable to dump data to data file:\n{str(path)}")


"""
* Project Files
"""


def get_project_version(path: Path) -> str:
    """Returns the version string stored in the root project file.

    Args:
        path: Path to the root project file.

    Returns:
        Current version string.

    Raises:
        FileNotFoundError: If project file does not exist.
        ValueError: If project file type not supported.
        OSError: If project file fails to load.
    """
    project = load_data_file(path)
    return project.get('tool', {}).get('poetry', {}).get('version', '1.0.0')
