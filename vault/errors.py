class VaultError(Exception):
    """Base exception class for all MPKV vault errors.

    This class serves as the base for all custom exceptions in the MPKV
    vault system. It provides a consistent interface for error handling
    and message formatting.

    Attributes:
        message: A human-readable error message
        original_error: The original exception that caused this error (if any)
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize a new VaultError.

        Args:
            message: A human-readable error message
            original_error: The original exception that caused this error (if any)
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class StorageError(VaultError):
    """Exception raised for vault storage-related errors.

    This exception is raised when there are issues with file system operations,
    such as reading or writing files, creating directories, or managing the
    vault index.

    Attributes:
        message: A human-readable error message
        original_error: The original exception that caused this error (if any)
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize a new StorageError.

        Args:
            message: A human-readable error message
            original_error: The original exception that caused this error (if any)
        """
        super().__init__(message, original_error)


class NoteNotFoundError(VaultError):
    """Exception raised when a requested note cannot be found.

    This exception is raised when attempting to access a note that doesn't
    exist in the vault, either by ID or title.

    Attributes:
        note_id: The ID of the note that wasn't found
        message: A human-readable error message
    """

    def __init__(self, note_id: str) -> None:
        """Initialize a new NoteNotFoundError.

        Args:
            note_id: The ID of the note that wasn't found
        """
        message = f"Note '{note_id}' not found"
        super().__init__(message)
        self.note_id = note_id


class DuplicateTitleError(VaultError):
    """Exception raised when attempting to create a note with a duplicate title.

    This exception is raised when trying to create a new note with a title
    that already exists in the vault.

    Attributes:
        title: The duplicate title that caused the error
        message: A human-readable error message
    """

    def __init__(self, title: str) -> None:
        """Initialize a new DuplicateTitleError.

        Args:
            title: The duplicate title that caused the error
        """
        message = f"A note with title '{title}' already exists"
        super().__init__(message)
        self.title = title
