import datetime
import uuid
from typing import Any

from vault.fields import ContentField, TagsField, TitleField


class Note:
    """
    The core note model for storing knowledge items.

    A Note represents a single piece of knowledge in the vault, with
    metadata for organization and retrieval. Notes are stored with
    their content and metadata separated to support efficient indexing.

    Attributes:
        id (str): Unique identifier for the note (UUID)
        title (str): The title of the note (validated by TitleField)
        content (str): The main content of the note (validated by ContentField)
        tags (List[str]): List of tags associated with the note (validated by TagsField)
        created_at (datetime): Timestamp when the note was created
        last_modified (datetime): Timestamp of the last modification
        filename (str): The filename where the note content is stored
    """

    title = TitleField()
    content = ContentField()
    tags = TagsField()

    def __init__(
        self,
        title: str,
        content: str,
        tags: str | list[str] | None = None,
        id: str | None = None,
        created_at: datetime.datetime | str | None = None,
        last_modified: datetime.datetime | str | None = None,
        filename: str | None = None,
    ):
        """
        Initialize a new Note instance.

        Args:
            title: The title of the note
            content: The main content of the note
            tags: Optional tags for the note (comma-separated string or list)
            id: Optional unique identifier (generated if not provided)
            created_at: Optional creation timestamp (current time if not provided)
            last_modified: Optional modification timestamp (same as created_at if not provided)
            filename: Optional filename for content storage (generated if not provided)

        Note:
            The descriptor fields (title, content, tags) are validated
            during assignment.
        """
        # Generate or use provided identifier
        self.id = id if id is not None else str(uuid.uuid4())

        # Set descriptor fields (will be validated by descriptors)
        self.title = title
        self.content = content
        self.tags = tags

        # Set timestamps
        now = datetime.datetime.now(datetime.timezone.utc)

        # Handle creation timestamp
        if created_at is None:
            self.created_at = now
        elif isinstance(created_at, str):
            self.created_at = datetime.datetime.fromisoformat(created_at)
        else:
            self.created_at = created_at

        # Handle modification timestamp
        if last_modified is None:
            self.last_modified = self.created_at
        elif isinstance(last_modified, str):
            self.last_modified = datetime.datetime.fromisoformat(last_modified)
        else:
            self.last_modified = last_modified

        # Set or generate filename
        if filename is None:
            # Generate filename from id with .md extension
            self.filename = f"{self.id}.md"
        else:
            self.filename = filename

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Note to a dictionary representation.

        This method creates a dictionary suitable for serialization
        to JSON for the vault index.

        Returns:
            A dictionary with the note's metadata and attributes
        """
        return {
            "id": self.id,
            "title": self.title,
            "tags": self.tags if self.tags is not None else [],
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "filename": self.filename,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], content: str) -> "Note":
        """
        Create a Note instance from dictionary data and content.

        This class method constructs a Note object from separate
        metadata and content, typically loaded from storage.

        Args:
            data: Dictionary containing note metadata
            content: The note content as a string

        Returns:
            A new Note instance

        Raises:
            KeyError: If required fields are missing from the data dictionary
            ValueError: If the provided data fails validation
        """
        # Extract required fields
        id = data.get("id")
        title = data.get("title")
        if title is None:
            raise KeyError("Title is required to create a Note.")
        tags = data.get("tags", [])
        created_at = data.get("created_at")
        last_modified = data.get("last_modified")
        filename = data.get("filename")

        # Construct and return new Note object
        return cls(
            id=id,
            title=title,
            content=content,
            tags=tags,
            created_at=created_at,
            last_modified=last_modified,
            filename=filename,
        )

    def update_content(self, new_content: str) -> None:
        """
        Update the note's content and last_modified timestamp.

        Args:
            new_content: The new content for the note
        """
        self.content = new_content
        self.last_modified = datetime.datetime.now(datetime.timezone.utc)

    def update_title(self, new_title: str) -> None:
        """
        Update the note's title and last_modified timestamp.

        Args:
            new_title: The new title for the note
        """
        self.title = new_title
        self.last_modified = datetime.datetime.now(datetime.timezone.utc)

    def update_tags(self, new_tags: str | list[str]) -> None:
        """
        Update the note's tags and last_modified timestamp.

        Args:
            new_tags: The new tags for the note (comma-separated string or list)
        """
        self.tags = new_tags
        self.last_modified = datetime.datetime.now(datetime.timezone.utc)

    def __repr__(self) -> str:
        """
        Provide a string representation of the Note.

        Returns:
            A string showing the Note's class and title
        """
        return f"Note(title='{self.title}')"
