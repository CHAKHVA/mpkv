import json
import logging
import os
import os.path
import uuid

from vault.errors import DuplicateTitleError, NoteNotFoundError, StorageError
from vault.models import Note

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
        with open(index_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in index file {index_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, original_error=e) from e


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
        raise StorageError(error_msg, original_error=e) from e


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
        with open(note_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise NoteNotFoundError(note_id) from None
    except OSError as e:
        error_msg = f"Failed to read note content from {note_path}: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg, original_error=e) from e


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
        raise StorageError(error_msg, original_error=e) from e


def _create_note_internal(note: Note, vault_path: str | None = None) -> None:
    """
    Create a new note in the vault.

    This internal function handles the complete process of creating a note:
    1. Writing the note's content to a file
    2. Loading the current index
    3. Adding the note's metadata to the index
    4. Saving the updated index

    Args:
        note: The Note object to create
        vault_path: Optional custom vault path (resolved if not provided)

    Raises:
        StorageError: If there are any file system errors during the process

    Examples:
        >>> note = Note(title="My Note", content="Note content")
        >>> _create_note_internal(note)
    """
    try:
        # Write note content to file
        write_note_content(note.id, note.content, vault_path)

        # Load current index
        index_data = load_index(vault_path)
        if "notes" not in index_data:
            index_data["notes"] = {}

        # Add note metadata to index
        index_data["notes"][note.id] = note.to_dict()

        # Save updated index
        save_index(index_data, vault_path)

    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(
            f"Failed to create note '{note.id}': {e}", original_error=e
        ) from e


def _get_note_internal(note_id: str, vault_path: str | None = None) -> Note:
    """
    Get a note from the vault by its ID.

    This internal function handles the complete process of retrieving a note:
    1. Loading the current index
    2. Checking if the note ID exists
    3. Reading the note's content
    4. Creating and returning a Note object

    Args:
        note_id: The unique identifier of the note to retrieve
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The retrieved Note object

    Raises:
        NoteNotFoundError: If the note doesn't exist in the index
        StorageError: If there are any file system errors during the process

    Examples:
        >>> note = _get_note_internal('123e4567-e89b-12d3-a456-426614174000')
        >>> print(note.title)
        'My Note'
    """
    try:
        # Load current index
        index_data = load_index(vault_path)
        if "notes" not in index_data or note_id not in index_data["notes"]:
            raise NoteNotFoundError(note_id)

        # Get note metadata and content
        note_data = index_data["notes"][note_id]
        content = read_note_content(note_id, vault_path)

        # Create and return Note object
        return Note.from_dict(note_data, content)

    except (NoteNotFoundError, StorageError):
        # Re-raise the original error
        raise
    except Exception as e:
        # Wrap unexpected errors in StorageError
        raise StorageError(
            f"Failed to get note '{note_id}': {e}", original_error=e
        ) from e


def _delete_note_internal(note_id: str, vault_path: str | None = None) -> None:
    """
    Delete a note from the vault.

    This internal function handles the complete process of deleting a note:
    1. Loading the current index
    2. Checking if the note ID exists
    3. Getting the note's filename
    4. Removing the note's file
    5. Removing the note from the index
    6. Saving the updated index

    Args:
        note_id: The unique identifier of the note to delete
        vault_path: Optional custom vault path (resolved if not provided)

    Raises:
        NoteNotFoundError: If the note doesn't exist in the index
        StorageError: If there are any file system errors during the process

    Examples:
        >>> _delete_note_internal('123e4567-e89b-12d3-a456-426614174000')
    """
    try:
        # Load current index
        index_data = load_index(vault_path)
        if "notes" not in index_data or note_id not in index_data["notes"]:
            raise NoteNotFoundError(note_id)

        # Get note filename and remove file
        note_data = index_data["notes"][note_id]
        filename = note_data.get("filename")
        if filename:
            note_path = _get_note_file_path(note_id, vault_path)
            try:
                os.remove(note_path)
            except FileNotFoundError:
                # Ignore if file is already gone
                pass
            except OSError as e:
                raise StorageError(
                    f"Failed to remove note file: {e}", original_error=e
                ) from e

        # Remove note from index and save
        del index_data["notes"][note_id]
        save_index(index_data, vault_path)

    except (NoteNotFoundError, StorageError):
        # Re-raise the original error
        raise
    except Exception as e:
        # Wrap unexpected errors in StorageError
        raise StorageError(
            f"Failed to delete note '{note_id}': {e}", original_error=e
        ) from e


def _find_note_id_by_title(title: str, vault_path: str | None = None) -> str | None:
    """
    Find a note's ID by its title.

    This function searches through the vault index to find a note with the
    given title. If found, returns its ID; otherwise, returns None.

    Args:
        title: The title to search for
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The ID of the note with the given title, or None if not found

    Raises:
        StorageError: If there are any file system errors during the process

    Examples:
        >>> _find_note_id_by_title("My Note")
        '123e4567-e89b-12d3-a456-426614174000'
    """
    try:
        index_data = load_index(vault_path)
        if "notes" not in index_data:
            return None

        for note_id, note_data in index_data["notes"].items():
            if note_data.get("title") == title:
                return note_id

        return None

    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(
            f"Failed to find note with title '{title}': {e}", original_error=e
        ) from e


def create_note(
    title: str,
    content: str,
    tags: str | list[str] | None = None,
    vault_path: str | None = None,
) -> Note:
    """
    Create a new note in the vault.

    This function creates a new note with the given title, content, and optional tags.
    It ensures the title is unique and handles all the necessary setup for the note.

    Args:
        title: The title of the note
        content: The content of the note
        tags: Optional tags for the note (comma-separated string or list)
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The created Note object

    Raises:
        DuplicateTitleError: If a note with the given title already exists
        ValueError: If the note data fails validation
        StorageError: If there are any file system errors during the process

    Examples:
        >>> note = create_note("My Note", "Note content", ["tag1", "tag2"])
        >>> print(note.title)
        'My Note'
    """
    try:
        # Ensure vault directory exists
        ensure_vault_dirs_exist(vault_path)

        # Check for duplicate title
        existing_id = _find_note_id_by_title(title, vault_path)
        if existing_id is not None:
            raise DuplicateTitleError(title)

        # Generate ID and create note
        note_id = generate_note_id()
        note = Note(
            title=title,
            content=content,
            tags=tags,
            id=note_id,
        )

        # Create note in vault
        _create_note_internal(note, vault_path)
        return note

    except (DuplicateTitleError, ValueError):
        # Re-raise validation errors
        raise
    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(
            f"Failed to create note with title '{title}': {e}", original_error=e
        ) from e


def get_note_by_title(title: str, vault_path: str | None = None) -> Note:
    """
    Get a note from the vault by its title.

    This function finds a note with the given title and returns it.

    Args:
        title: The title of the note to retrieve
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        The retrieved Note object

    Raises:
        NoteNotFoundError: If no note with the given title exists
        StorageError: If there are any file system errors during the process

    Examples:
        >>> note = get_note_by_title("My Note")
        >>> print(note.content)
        'Note content'
    """
    try:
        # Find note ID by title
        note_id = _find_note_id_by_title(title, vault_path)
        if note_id is None:
            raise NoteNotFoundError(title)

        # Get note by ID
        return _get_note_internal(note_id, vault_path)

    except (NoteNotFoundError, StorageError):
        # Re-raise the original error
        raise
    except Exception as e:
        # Wrap unexpected errors in StorageError
        raise StorageError(
            f"Failed to get note with title '{title}': {e}", original_error=e
        ) from e


def delete_note_by_title(title: str, vault_path: str | None = None) -> None:
    """
    Delete a note from the vault by its title.

    This function finds a note with the given title and deletes it.

    Args:
        title: The title of the note to delete
        vault_path: Optional custom vault path (resolved if not provided)

    Raises:
        NoteNotFoundError: If no note with the given title exists
        StorageError: If there are any file system errors during the process

    Examples:
        >>> delete_note_by_title("My Note")
    """
    try:
        # Find note ID by title
        note_id = _find_note_id_by_title(title, vault_path)
        if note_id is None:
            raise NoteNotFoundError(title)

        # Delete note by ID
        _delete_note_internal(note_id, vault_path)

    except (NoteNotFoundError, StorageError):
        # Re-raise the original error
        raise
    except Exception as e:
        # Wrap unexpected errors in StorageError
        raise StorageError(
            f"Failed to delete note with title '{title}': {e}", original_error=e
        ) from e


def get_all_titles(vault_path: str | None = None) -> list[str]:
    """
    Get a list of all note titles in the vault.

    This function loads the vault index and extracts all note titles.
    If there are no notes or the index is empty, returns an empty list.

    Args:
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        A list of note titles

    Raises:
        StorageError: If there are any file system errors during the process

    Examples:
        >>> get_all_titles()
        ['Note 1', 'Note 2', 'Note 3']
    """
    try:
        # Load index and extract titles
        index_data = load_index(vault_path)
        if "notes" not in index_data:
            return []

        return [
            note_data.get("title", "") for note_data in index_data["notes"].values()
        ]

    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(f"Failed to get note titles: {e}", original_error=e) from e


def search_notes(term: str, vault_path: str | None = None) -> list[Note]:
    """
    Search for notes containing the given term.

    This function searches through all notes in the vault for the given term.
    The search is case-insensitive and looks in:
    1. Note titles
    2. Note tags
    3. Note content

    Args:
        term: The search term to look for
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        A list of Note objects that match the search term

    Raises:
        StorageError: If there are any file system errors during the process

    Examples:
        >>> search_notes("important")
        [<Note title="Important Meeting", ...>, <Note title="Tasks", ...>]
    """
    try:
        # Load index
        index_data = load_index(vault_path)
        if "notes" not in index_data:
            return []

        # Convert search term to lowercase for case-insensitive search
        term_lower = term.lower()
        matching_notes = []

        # Search through each note
        for note_id, note_data in index_data["notes"].items():
            # Check title
            title = note_data.get("title", "").lower()
            if term_lower in title:
                try:
                    note = _get_note_internal(note_id, vault_path)
                    matching_notes.append(note)
                    continue
                except (NoteNotFoundError, StorageError):
                    # Skip this note if we can't read it
                    continue

            # Check tags
            tags = [tag.lower() for tag in note_data.get("tags", [])]
            if any(term_lower in tag for tag in tags):
                try:
                    note = _get_note_internal(note_id, vault_path)
                    matching_notes.append(note)
                    continue
                except (NoteNotFoundError, StorageError):
                    # Skip this note if we can't read it
                    continue

            # Check content
            try:
                content = read_note_content(note_id, vault_path).lower()
                if term_lower in content:
                    note = _get_note_internal(note_id, vault_path)
                    matching_notes.append(note)
            except (NoteNotFoundError, StorageError):
                # Skip this note if we can't read it
                continue

        return matching_notes

    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(f"Failed to search notes: {e}", original_error=e) from e


def get_all_tags_with_counts(vault_path: str | None = None) -> dict[str, int]:
    """
    Get all tags and their usage counts from the vault.

    This function loads the vault index and aggregates the count of each tag
    across all notes. Tags are returned in a dictionary where keys are tag names
    and values are the number of notes using that tag.

    Args:
        vault_path: Optional custom vault path (resolved if not provided)

    Returns:
        A dictionary mapping tag names to their usage counts

    Raises:
        StorageError: If there are any file system errors during the process

    Examples:
        >>> get_all_tags_with_counts()
        {'work': 3, 'personal': 2, 'ideas': 1}
    """
    try:
        # Load index
        index_data = load_index(vault_path)
        if "notes" not in index_data:
            return {}

        # Aggregate tag counts
        tag_counts: dict[str, int] = {}
        for note_data in index_data["notes"].values():
            for tag in note_data.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(f"Failed to get tag counts: {e}", original_error=e) from e


def export_notes(output_dir: str, vault_path: str | None = None) -> None:
    """
    Export all notes to individual text files in the specified directory.

    This function exports all notes from the vault to individual text files in
    the specified output directory. Each file is named after the note's title
    (sanitized for filesystem use) and contains the note's title and content.

    Args:
        output_dir: The directory to export notes to
        vault_path: Optional custom vault path (resolved if not provided)

    Raises:
        StorageError: If there are any file system errors during the process
        OSError: If the output directory cannot be created

    Examples:
        >>> export_notes("/path/to/export")
    """
    try:
        # Load index
        index_data = load_index(vault_path)
        if "notes" not in index_data:
            return

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Export each note
        for note_id, note_data in index_data["notes"].items():
            try:
                # Get note content
                content = read_note_content(note_id, vault_path)
                title = note_data.get("title", "Untitled")

                # Sanitize title for filename
                # Replace invalid characters with underscores
                safe_title = "".join(
                    c if c.isalnum() or c in " -_" else "_" for c in title
                )
                # Replace spaces with underscores
                safe_title = safe_title.replace(" ", "_")
                # Ensure filename is not empty
                if not safe_title:
                    safe_title = "untitled"

                # Construct output path
                output_path = os.path.join(output_dir, f"{safe_title}.txt")

                # Write note to file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"Title: {title}\n\n")
                    f.write(content)

            except (NoteNotFoundError, StorageError) as e:
                # Log error but continue with other notes
                logger.warning(f"Failed to export note '{note_id}': {e}")
                continue

    except OSError as e:
        # Re-raise OSError for directory creation issues
        raise OSError(f"Failed to create output directory '{output_dir}': {e}") from e
    except StorageError as e:
        # Re-raise StorageError with more context
        raise StorageError(f"Failed to export notes: {e}", original_error=e) from e
