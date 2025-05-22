class StorageError(Exception):
    """
    Base exception for storage-related errors in the MPKV vault system.

    This exception is raised when there are problems with reading from or writing
    to the vault storage, including file system errors and data format issues.

    Attributes:
        message: A human-readable error message
        original_error: The original exception that caused this error (if any)
    """

    def __init__(self, message: str, original_error: Exception | None = None):
        """
        Initialize a new StorageError.

        Args:
            message: A human-readable error message
            original_error: The original exception that caused this error (if any)
        """
        super().__init__(message)
        self.original_error = original_error


class NoteNotFoundError(Exception):
    """
    Exception raised when a requested note file cannot be found.

    This exception is raised when attempting to read a note file that doesn't exist
    in the vault's notes directory.

    Attributes:
        note_id: The ID of the note that was not found
        message: A human-readable error message
    """

    def __init__(self, note_id: str, message: str | None = None):
        """
        Initialize a new NoteNotFoundError.

        Args:
            note_id: The ID of the note that was not found
            message: Optional custom error message
        """
        if message is None:
            message = f"Note with ID '{note_id}' not found"
        super().__init__(message)
        self.note_id = note_id
