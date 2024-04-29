"""
* Module Utilities
* General utilities for dynamically loading and managing Python modules.
* Copyright (c) Hexproof Systems <hexproofsystems@gmail.com>
* LICENSE: Mozilla Public License 2.0
"""
# Standard Library Imports
import importlib
import os
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys
from types import ModuleType
from typing import Union, Optional

"""
* Types
"""

ModuleTree = dict[str, Union[ModuleType, 'ModuleTree']]

"""
* Sys Utils
"""


def add_python_path(path: Union[str, os.PathLike]) -> None:
    """Add a path to 'sys.path', allowing relative import discovery.

    Args:
        path: Directory path to add to `sys.path`.
    """
    p = str(path)
    if p not in sys.path:
        sys.path.append(p)


def remove_python_path(path: Union[str, os.PathLike]) -> None:
    """Remove a path from 'sys.path' to keep the namespace clean.

    Args:
        path: Directory path to remove from `sys.path`.
    """
    p = str(path)
    if p in sys.path:
        sys.path.remove(p)


"""
* Packages
"""


def import_package(name: str, path: Path, hotswap: bool = False) -> Optional[ModuleType]:
    """Loads a module package using importlib or from 'sys.modules', allowing for forced reloads.

    Args:
        name: Name of the module.
        path: Path to the module.
        hotswap: Whether to force the module to be reloaded fresh.

    Returns:
        The loaded module.
    """
    # Return previously loaded module
    if name in sys.modules:
        if not hotswap:
            return sys.modules[name]
        del sys.modules[name]

    # Add parent folder to path
    add_python_path(str(path))

    # Collect nested modules before importing and executing
    import_nested_modules(
        name=name,
        path=path,
        recursive=True,
        hotswap=hotswap,
        ignored=['__init__.py'])

    # Return None if init module not found
    init_module = path / '__init__.py'
    if not init_module.is_file():
        remove_python_path(str(path))
        return

    # Import and execute the init module
    module = import_module_from_path(name=name, path=init_module, hotswap=hotswap)

    # Reset system paths and return
    remove_python_path(str(path))
    return module


"""
* Dynamic Modules
"""


def import_nested_modules(
    name: str,
    path: Path,
    recursive: bool = True,
    hotswap: bool = False,
    ignored: Optional[list[str]] = None
) -> ModuleTree:
    """Imports modules nested inside a directory.

    Args:
        name: Module name to give the directory.
        path: Path to a directory to import as a module.
        recursive: Whether to recursively import nested directories as submodules.
        hotswap: Whether to force modules to be imported fresh, if any were imported previously.
        ignored: Submodules to ignore when importing.

    Returns:
        A dictionary tree of modules imported.
    """
    ignored = ignored or []
    imported = {name: []}
    for item in os.listdir(path):
        if item in ['__pycache__', *ignored]:
            continue

        # Establish submodule path and name
        p = path / item
        n = '.'.join([name, p.stem])

        # Nested folder or python file?
        if p.is_dir() and recursive:
            # Import directory
            add_python_path(str(p))
            module = import_nested_modules(
                name=n, path=p, hotswap=hotswap, ignored=ignored)
            if module:
                imported[n] = module
            remove_python_path(str(p))
        elif p.is_file() and p.suffix == '.py':
            # Import module
            imported[n] = import_module_from_path(name=n, path=p, hotswap=hotswap)
    return imported


def import_module_from_path(name: str, path: Path, hotswap: bool = False) -> ModuleType:
    """Import a module from a given path.

    Args:
        name: Name of the module.
        path: Path to the module.
        hotswap: Whether to

    Returns:
        Loaded and executed module.
    """
    # Return previously loaded module
    if name in sys.modules:
        if not hotswap:
            return sys.modules[name]
        del sys.modules[name]

    # Import and execute the module
    spec = spec_from_file_location(name=name, location=path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


"""
* Local Modules
"""


def get_local_module(module_path: str, hotswap: bool = False) -> ModuleType:
    """Lookup a local module, import it if no previously imported or hotswap is enabled, then return it.

    Args:
        module_path: Path to the module in module notation, e.g. "src.templates"
        hotswap: If True, always re-import module if previously loaded.

    Returns:
        ModuleType: Loaded module.

    Raises:
        ImportError: If module couldn't be loaded successfully.
    """
    # Check if the module has already been loaded
    if module_path in sys.modules:
        if not hotswap:
            return sys.modules[module_path]
        del sys.modules[module_path]

    # Load the module fresh and cache it
    module = importlib.import_module(module_path)
    sys.modules[module_path] = module
    return module
