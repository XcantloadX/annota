class AnnotaCliError(Exception):
    """Base class for all Annota CLI errors."""
    pass


class InvalidFileError(AnnotaCliError):
    """Raised when an invalid file is encountered."""
    pass