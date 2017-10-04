# Exception messages
FILE_EXISTS = "file exists: '{path}'"
FILE_NOT_FOUND = "no such file or directory: '{path}'"
FILE_NOT_TRACKED = "file not tracked by Carton: '{path}'"
MODULE_EXPECTED = "expected a Module subclass or instance thereof, got '{bad_type}'"
PERMISSION_ERROR = "invalid permissions on '{path}'"
NOT_A_DIRECTORY = "not a directory: '{path}'"
MODULE_LOADED = "module '{module}' is already loaded"
MODULE_OFFLINE = "module '{module}' is not loaded"
RESOURCE_LOCKED = "resource '{resource}' is owned by '{owner}'"
RESOURCE_FREE = "resource '{resource}' is not locked"
COMMAND_NOT_FOUND = "command '{command}' not found"
PYTHON_MODULE_EXPECTED = "expected a Python module or 'str', got '{bad_type}'"
DECORATED_NOT_CALLABLE = "decorated value is not callable"
WRONG_TYPE = "expected {expected} but got {bad_type}"
INVALID_CONFIGURATION = "configuration element '{element}' has an unexpected format"

# Command-line messages
CORRUPT_FILE = "Warning! File '{file}' could not be loaded as expected. The original file was moved to {file}.bak, and empty data is used instead."
