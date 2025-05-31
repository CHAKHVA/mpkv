import datetime
import uuid
from typing import Any

from vault.fields import ContentField, TagsField, TitleField


class Note:
    """A note in the MPKV vault system.

    This class represents a note in the vault, containing metadata such as
    title, tags, and timestamps, as well as the note's content.

    Attributes:
        id: The unique identifier for the note
        title: The title of the note
        content: The content of the note
        tags: Optional list of tags associated with the note
        created_at: Timestamp when the note was created
        last_modified: Timestamp when the note was last modified
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
    ) -> None:
        """Initialize a new Note.

        Args:
            title: The title of the note
            content: The content of the note
            tags: Optional list of tags for the note
            id: Optional unique identifier for the note
            created_at: Optional timestamp when the note was created
            last_modified: Optional timestamp when the note was last modified
            filename: Optional filename for content storage

        Raises:
            ValueError: If the title is empty or contains only whitespace
        """
        if not title or not title.strip():
            raise ValueError("Note title cannot be empty")

        self.id = id if id is not None else str(uuid.uuid4())
        self.title = title.strip()
        self.content = content
        self.tags = tags or []
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.last_modified = last_modified or self.created_at

        # Set or generate filename
        if filename is None:
            # Generate filename from id with .md extension
            self.filename = f"{self.id}.txt"
        else:
            self.filename = filename

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Note to a dictionary representation.

        This method converts the note's attributes to a dictionary format
        suitable for storage in the vault index.

        Returns:
            A dictionary containing the note's attributes
        """
        return {
            "id": self.id,
            "title": self.title,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "filename": self.filename,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], content: str) -> "Note":
        """
        Create a Note instance from dictionary data and content.

        This class method creates a new Note instance from a dictionary
        containing the note's metadata and its content.

        Args:
            data: Dictionary containing the note's metadata
            content: The note's content

        Returns:
            A new Note instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            return cls(
                title=data["title"],
                content=content,
                tags=data.get("tags"),
                id=data.get("id"),
                created_at=datetime.datetime.fromisoformat(data["created_at"]),
                last_modified=datetime.datetime.fromisoformat(data["last_modified"]),
                filename=data.get("filename"),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}") from e
        except ValueError as e:
            raise ValueError(f"Invalid data format: {e}") from e

    def __str__(self) -> str:
        """Return a string representation of the note.

        Returns:
            A string containing the note's title and content
        """
        return f"{self.title}\n\n{self.content}"

    def __repr__(self) -> str:
        """Return a detailed string representation of the note.

        Returns:
            A string containing all the note's attributes
        """
        return (
            f"Note(id='{self.id}', title='{self.title}', "
            f"tags={self.tags}, created_at={self.created_at}, "
            f"last_modified={self.last_modified})"
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
            new_tags: The new tags for the note
        """
        self.tags = new_tags
        self.last_modified = datetime.datetime.now(datetime.timezone.utc)
