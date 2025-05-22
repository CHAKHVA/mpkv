import json
import logging
import os
import os.path
import uuid

from vault.errors import NoteNotFoundError, StorageError

# Configure logging
logger = logging.getLogger(__name__)

# Constants for directory and file names
VAULT_DIR_NAME = ".mpkv"
NOTES_SUBDIR_NAME = "notes"
INDEX_FILENAME = "index.json"


def get_vault_path(custom_path: str | None = None) -> str:
    """
    Get the path to the MPKV vault directory.

    This function resolves the vault directory path, either using a custom path
    if provided or defaulting to a directory in the user's home directory.

    Args:
        custom_path: Optional custom path to use for the vault directory

    Returns:
        The absolute path to the vault directory

    Examples:
        >>> get_vault_path()
        '/home/user/.mpkv'
        >>> get_vault_path('/data/my-vault')
        '/data/my-vault'
    """
    if custom_path:
        # Use the provided custom path
        vault_path = os.path.abspath(os.path.expanduser(custom_path))
    else:
        # Default to a directory in the user's home
        home_dir = os.path.expanduser("~")
        vault_path = os.path.join(home_dir, VAULT_DIR_NAME)

    return vault_path


def get_vault_subdirs(vault_path: str | None = None) -> tuple[str, str]:
    """
    Get the paths to the vault's subdirectories.

    Args:
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        A tuple containing the vault path and notes directory path

    Examples:
        >>> get_vault_subdirs()
        ('/home/user/.mpkv', '/home/user/.mpkv/notes')
    """
    vault_dir = get_vault_path(vault_path)
    notes_dir = os.path.join(vault_dir, NOTES_SUBDIR_NAME)

    return vault_dir, notes_dir


def ensure_vault_dirs_exist(vault_path: str | None = None) -> tuple[str, str]:
    """
    Ensure that the vault directory structure exists.

    This function creates the main vault directory and its subdirectories
    if they don't already exist.

    Args:
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        A tuple containing the vault path and notes directory path

    Raises:
        OSError: If the directories cannot be created due to permission issues or other OS errors

    Examples:
        >>> ensure_vault_dirs_exist()
        ('/home/user/.mpkv', '/home/user/.mpkv/notes')
    """
    vault_dir, notes_dir = get_vault_subdirs(vault_path)

    try:
        # Create the main vault directory if it doesn't exist
        os.makedirs(vault_dir, exist_ok=True)
        logger.debug(f"Vault directory confirmed at: {vault_dir}")

        # Create the notes subdirectory if it doesn't exist
        os.makedirs(notes_dir, exist_ok=True)
        logger.debug(f"Notes directory confirmed at: {notes_dir}")

    except OSError as e:
        logger.error(f"Failed to create vault directories: {e}")
        raise

    return vault_dir, notes_dir


def get_index_path(vault_path: str | None = None) -> str:
    """
    Get the path to the vault index file.

    Args:
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The absolute path to the index file

    Examples:
        >>> get_index_path()
        '/home/user/.mpkv/index.json'
    """
    vault_dir = get_vault_path(vault_path)
    return os.path.join(vault_dir, INDEX_FILENAME)


def load_index(vault_path: str | None = None) -> dict:
    """
    Load the vault index from the index file.

    This function reads the JSON index file and returns its contents as a dictionary.
    If the file doesn't exist, returns an empty dictionary. If the file exists but
    contains invalid JSON, raises a StorageError.

    Args:
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        A dictionary containing the index data

    Raises:
        StorageError: If the index file contains invalid JSON

    Examples:
        >>> load_index()
        {'notes': {'note1': {'title': 'My Note', 'tags': ['tag1', 'tag2']}}}
    """
    index_path = get_index_path(vault_path)

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.debug(f"Index file not found at {index_path}, returning empty dict")
        return {}
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in index file {index_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, original_error=e)


def save_index(index_data: dict, vault_path: str | None = None) -> None:
    """
    Save the vault index to the index file.

    This function ensures the vault directory exists, then writes the index data
    as formatted JSON to the index file. The JSON is written with an indent of 4
    spaces for readability.

    Args:
        index_data: The dictionary containing the index data to save
        vault_path: Optional custom vault path (resolved if not provided)

    Raises:
        StorageError: If the index file cannot be written due to permission issues
            or other OS errors

    Examples:
        >>> save_index({'notes': {'note1': {'title': 'My Note'}}})
    """
    # Ensure vault directory exists
    ensure_vault_dirs_exist(vault_path)
    index_path = get_index_path(vault_path)

    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=4)
        logger.debug(f"Index saved to {index_path}")
    except OSError as e:
        error_msg = f"Failed to save index to {index_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, original_error=e)


def generate_note_id() -> str:
    """
    Generate a unique identifier for a new note.

    This function uses UUID4 to generate a unique identifier that can be used
    as a note's ID. The ID is returned as a string.

    Returns:
        A unique string identifier

    Examples:
        >>> generate_note_id()
        '123e4567-e89b-12d3-a456-426614174000'
    """
    return str(uuid.uuid4())


def _get_note_file_path(note_id: str, vault_path: str | None = None) -> str:
    """
    Get the path to a note's content file.

    This function constructs the full path to a note's content file based on
    its ID and the vault path.

    Args:
        note_id: The unique identifier of the note
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The absolute path to the note's content file

    Examples:
        >>> _get_note_file_path('123e4567-e89b-12d3-a456-426614174000')
        '/home/user/.mpkv/notes/123e4567-e89b-12d3-a456-426614174000.txt'
    """
    _, notes_dir = get_vault_subdirs(vault_path)
    return os.path.join(notes_dir, f"{note_id}.txt")


def read_note_content(note_id: str, vault_path: str | None = None) -> str:
    """
    Read the content of a note from its file.

    This function reads the content of a note's file and returns it as a string.
    If the file doesn't exist, raises NoteNotFoundError. If there are other
    file system errors, raises StorageError.

    Args:
        note_id: The unique identifier of the note
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The content of the note as a string

    Raises:
        NoteNotFoundError: If the note file doesn't exist
        StorageError: If there are file system errors while reading

    Examples:
        >>> read_note_content('123e4567-e89b-12d3-a456-426614174000')
        'This is the note content'
    """
    note_path = _get_note_file_path(note_id, vault_path)

    try:
        with open(note_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise NoteNotFoundError(note_id)
    except OSError as e:
        error_msg = f"Failed to read note content from {note_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, original_error=e)


def write_note_content(
    note_id: str, content: str, vault_path: str | None = None
) -> None:
    """
    Write content to a note's file.

    This function ensures the vault directory exists, then writes the note's
    content to its file. If there are file system errors, raises StorageError.

    Args:
        note_id: The unique identifier of the note
        content: The content to write to the note's file
        vault_path: Optional custom vault path (resolved if not provided)

    Raises:
        StorageError: If there are file system errors while writing

    Examples:
        >>> write_note_content('123e4567-e89b-12d3-a456-426614174000', 'New content')
    """
    # Ensure vault directory exists
    ensure_vault_dirs_exist(vault_path)
    note_path = _get_note_file_path(note_id, vault_path)

    try:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"Note content written to {note_path}")
    except OSError as e:
        error_msg = f"Failed to write note content to {note_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, original_error=e)
