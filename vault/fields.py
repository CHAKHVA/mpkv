from typing import Any


class BaseField:
    """
    Base descriptor class for field validation.

    This class serves as the foundation for all field validators in the system.
    It manages the storage of field values in instance dictionaries and provides
    hooks for validation.

    Attributes:
        name (str): The name of the field in the owning class
        required (bool): Whether the field is required (cannot be None)
    """

    def __init__(self, required: bool = True):
        """
        Initialize a new field descriptor.

        Args:
            required: Whether the field is required (cannot be None)
        """
        self.name = ""  # Will be set when descriptor is assigned to a class
        self.required = required

    def __set_name__(self, owner: type, name: str):
        """
        Set the name of the descriptor when it's assigned as a class attribute.

        Args:
            owner: The class that owns this descriptor
            name: The name of the attribute this descriptor is assigned to
        """
        self.name = name

    def __get__(self, instance: Any, owner: type) -> Any:
        """
        Get the value of the field from the instance.

        Args:
            instance: The instance containing the field value
            owner: The class that owns this descriptor

        Returns:
            The value of the field
        """
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance: Any, value: Any):
        """
        Set the value of the field after validation.

        Args:
            instance: The instance to set the field on
            value: The value to set the field to

        Raises:
            ValueError: If the value fails validation
        """
        # Validate that the field is not None if required
        if value is None and self.required:
            raise ValueError(f"{self.name} is required and cannot be None")

        # Perform additional validation if value is not None
        if value is not None:
            value = self.validate(value)

        # Store the value in the instance dictionary
        instance.__dict__[self.name] = value

    def validate(self, value: Any) -> Any:
        """
        Validate the value according to field-specific rules.

        This method should be overridden by subclasses to provide specific validation.

        Args:
            value: The value to validate

        Returns:
            The validated (and possibly transformed) value

        Raises:
            ValueError: If the value fails validation
        """
        return value


class TitleField(BaseField):
    """
    Field descriptor for title validation.

    Validates that a title is a string with:
    - Required (by default)
    - Maximum length
    - Only contains allowed characters (alphanumeric and spaces)

    Attributes:
        max_length (int): Maximum allowed length of the title
    """

    def __init__(self, required: bool = True, max_length: int = 100):
        """
        Initialize a new title field descriptor.

        Args:
            required: Whether the field is required
            max_length: Maximum allowed length of the title
        """
        super().__init__(required)
        self.max_length = max_length

    def validate(self, value: Any) -> str:
        """
        Validate that the value is a proper title.

        Args:
            value: The value to validate

        Returns:
            The validated title string

        Raises:
            ValueError: If the value is not a string, exceeds max_length,
                or contains invalid characters
        """
        if not isinstance(value, str):
            raise ValueError(
                f"{self.name} must be a string, not {type(value).__name__}"
            )

        if len(value) > self.max_length:
            raise ValueError(
                f"{self.name} must not exceed {self.max_length} characters (got {len(value)})"
            )

        # Check for alphanumeric characters and spaces
        for char in value:
            if not (char.isalnum() or char.isspace()):
                raise ValueError(
                    f"{self.name} contains invalid character '{char}', "
                    "only alphanumeric characters and spaces are allowed"
                )

        return value


class ContentField(BaseField):
    """
    Field descriptor for content validation.

    Validates that content is a string with:
    - Required (by default)
    - Minimum length
    - Maximum length

    Attributes:
        min_length (int): Minimum allowed length of the content
        max_length (int): Maximum allowed length of the content
    """

    def __init__(
        self, required: bool = True, min_length: int = 10, max_length: int = 10000
    ):
        """
        Initialize a new content field descriptor.

        Args:
            required: Whether the field is required
            min_length: Minimum allowed length of the content
            max_length: Maximum allowed length of the content
        """
        super().__init__(required)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any) -> str:
        """
        Validate that the value is proper content.

        Args:
            value: The value to validate

        Returns:
            The validated content string

        Raises:
            ValueError: If the value is not a string, is too short,
                or exceeds max_length
        """
        if not isinstance(value, str):
            raise ValueError(
                f"{self.name} must be a string, not {type(value).__name__}"
            )

        if len(value) < self.min_length:
            raise ValueError(
                f"{self.name} must be at least {self.min_length} characters (got {len(value)})"
            )

        if len(value) > self.max_length:
            raise ValueError(
                f"{self.name} must not exceed {self.max_length} characters (got {len(value)})"
            )

        return value


class TagsField(BaseField):
    """
    Field descriptor for tags validation.

    Validates and processes tags input:
    - Optional by default
    - Accepts a comma-separated string or a list of strings
    - Converts to a list of stripped strings
    - Removes empty tags

    Attributes:
        max_tags (int): Maximum number of tags allowed
        max_tag_length (int): Maximum length of each individual tag
    """

    def __init__(
        self, required: bool = False, max_tags: int = 20, max_tag_length: int = 30
    ):
        """
        Initialize a new tags field descriptor.

        Args:
            required: Whether the field is required
            max_tags: Maximum number of tags allowed
            max_tag_length: Maximum length of each individual tag
        """
        super().__init__(required)
        self.max_tags = max_tags
        self.max_tag_length = max_tag_length

    def validate(self, value: str | list[str]) -> list[str]:
        """
        Validate and process tags input.

        Args:
            value: The value to validate, either a comma-separated string
                or a list of strings

        Returns:
            A list of validated tag strings

        Raises:
            ValueError: If the value is not a string or list, contains too many tags,
                or contains tags that are too long
        """
        # Handle string input (comma-separated)
        if isinstance(value, str):
            tags = [tag.strip() for tag in value.split(",")]
        # Handle list input
        elif isinstance(value, list):
            if not all(isinstance(tag, str) for tag in value):
                raise ValueError(f"All tags in {self.name} must be strings")
            tags = [tag.strip() for tag in value]
        else:
            raise ValueError(
                f"{self.name} must be a string or list, not {type(value).__name__}"
            )

        # Filter out empty tags
        tags = [tag for tag in tags if tag]

        # Check for maximum number of tags
        if len(tags) > self.max_tags:
            raise ValueError(
                f"{self.name} cannot have more than {self.max_tags} tags (got {len(tags)})"
            )

        # Check for maximum tag length
        for tag in tags:
            if len(tag) > self.max_tag_length:
                raise ValueError(
                    f"Tag '{tag}' in {self.name} exceeds maximum length of {self.max_tag_length}"
                )

        return tags
