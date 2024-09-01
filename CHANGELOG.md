## 1.3.0 (2024-09-01)

### Feat

- **logs**: Greatly optional parameters available to the logger object, add a `LogResults` context manager, add a function for reconfiguring a logger object, simplify the `log_test_result` decorator

## 1.2.6 (2024-08-24)

### Refactor

- **schema**: Deprecated unused "unify_schemas" function

## 1.2.5 (2024-08-24)

### Refactor

- **bench**: Improve benchmarking decorator "time_function"

## 1.2.4 (2024-08-14)

### Refactor

- **bench**: Use omnitils internal logger by default, implement optional logger parameter

## 1.2.3 (2024-07-06)

### Refactor

- **time_function**: Update `time_function` decorator to accept a log messaging format, tweak to allow called and uncalled modes

## 1.2.2 (2024-06-25)

### Refactor

- **logs**: Introduce support for a line continue tag. Use [>] at the end of a log message to drop the line terminator and at the beginning of a log message to continue the previous message
- **Logger**: Update typing for Logger object

## 1.2.1 (2024-05-24)

### Refactor

- **enums,fetch**: Minor docstring changes, readability improvements
- **logs**: Add new context handler `TemporaryLogger`, add new utility func `get_logger`, update logger initialization

## 1.2.0 (2024-05-21)

### Feat

- **logs**: New logging focused module for providing a plug and play, visually appealing logger, as well as supporting logger utilities

## 1.1.5 (2024-05-13)

### Refactor

- **enums,fetch,files**: Reworked enums classes, StrEnum -> StrConstant, fixed logic dealing with resuming file downloads, added new schema "ArbitrarySchema"

## 1.1.4 (2024-05-05)

### Fix

- **unify_schemas**: Retrieve schema attributes using getattr

## 1.1.3 (2024-05-05)

### Fix

- **unify_schema**: Incorrect variable used for checking if for 'use_value' key, added support for single string priority key

## 1.1.2 (2024-05-05)

### Refactor

- **schema**: Introduce utility func for joining schemas

## 1.1.1 (2024-05-05)

### Refactor

- **schemas**: Add PriorityMap type

## 1.1.0 (2024-04-29)

### Feat

- **api,fetch**: Multiple new utilities added to gdrive and download modules, implemented some major rewrites to improve clarity and modularity

### Refactor

- **api/github**: Minor syntax changes
- **files/_core**: Rewrite `get_temporary_file`
- **fetch/_core**: New `get_new_session` util for creating basic session object

## 1.0.0 (2024-04-28)

### BREAKING CHANGE

- folders.py and files_data.py will require different imports (from omnitils.files import folders, data)

### Feat

- **strings**: New utility function: decode_url (unescapes and decodes URL string, returns it as yaml.URL object)
- **properties**: Introduce new properties: auto_prop (property with automatic setter), tracked_prop (property with changes tracked in the parent object or class)
- **files**: New parent module to replace previous files.py root module, files.py largely subsumed into files/_core.py submodule, folders.py and files_data.py modules relocated here, new archive.py module introduced for working with archives
- **test**: New parent module for submodules geared towards various testing and benchmarking utilities
- **fetch**: New parent module for submodules geared towards making requests, downloading files, etc. downloads.py moved to this parent module pending deprecation of previous location
- **api**: New parent module for submodules geared towards interacting with various common live API services, github.py moved to this parent module pending deprecation of previous location
- **modules**: New module for dynamic importing of modules and their relative imports
- **metaclass**: New module for utility meta-classes
- **cli**: Preliminary implementation of internal CLI tool

### Fix

- **enums**: Correct idiosyncrasies with StrEnum class, rewrite StrEnumMeta and rename to more generic EnumCollection, introduce experimental URLEnum (enum class for yarl.URL objects)
- **download_file_with_callback**: Cover case of Content-Length not being numeric

### Refactor

- **download,github**: Deprecate moved root modules

## 0.6.2 (2024-03-01)

### Fix

- **files**: New file must be opened in write mode

## 0.6.1 (2024-02-20)

### Fix

- **invert_map_multi**: Fix return type

## 0.6.0 (2024-02-18)

### Feat

- **download**: Add new util module "download" for handling file download requests

## 0.5.0 (2024-02-18)

### Feat

- **exceptions**: New util module 'exceptions.py' for dealing with exceptions

## 0.4.0 (2024-02-14)

### Feat

- **schema**: New util module "schema" for creating and validating schemas

## 0.3.2 (2024-02-14)

### Refactor

- **files**: New util func "ensure_file"

## 0.3.1 (2024-02-14)

### Refactor

- **files_data,folders**: Add new utils "get_project_version" and "get_subdirs"

## 0.3.0 (2024-02-13)

### Feat

- **dicts**: Add dicts util module for generalized utilities working with dicts

### Refactor

- **strings**: Added new util funcs for string bool comparisons and working with multiline strings

## 0.2.0 (2024-02-12)

### Feat

- **strings**: Add new strings util for utility functions that handle string validation, normalization, etc
- **enums**: Add new "Enums" util for useful enum classes
- **github**: Introduce new github utils
- **properties**: Introduce new property decorator utils

### Refactor

- **files**: New file utilities "get_unique_filename" and "get_file_size_mb"

## 0.1.1 (2024-02-05)

### Refactor

- **pyproject.toml**: Add commitizen config

## 0.1.0 (2024-02-05)

### Feat

- **files,-files_data,-folders**: Implement new utility modules
