import logging
import os
import os.path

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
