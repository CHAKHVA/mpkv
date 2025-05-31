import argparse
import io
import sys
from typing import Any

import vault.core as vault
from vault.errors import DuplicateTitleError, NoteNotFoundError, StorageError


def handle_add(args: argparse.Namespace) -> None:
    """
    Handle the 'add' command to create a new note.

    This function creates a new note with the given or prompted title, content, and tags.
    If any of these are not provided as arguments, it will interactively prompt the user.

    Args:
        args: Parsed command line arguments containing title, content, and tags
    """
    # Get title
    title = args.title
    while not title:
        title = input("Enter note title: ").strip()
        if not title:
            print("Title cannot be empty. Please try again.")

    # Get tags
    tags = args.tags
    if tags is None:
        tags_input = input("Enter tags (comma-separated, optional): ").strip()
        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else None

    # Get content
    content = args.content
    if content is None:
        print("\nEnter note content (empty line to finish):")
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break
        content = "\n".join(lines)

    try:
        # Create the note
        note = vault.create_note(title, content, tags)
        print(f"\nNote '{note.title}' created successfully!")

    except ValueError as e:
        print(f"Error: Invalid note data - {e}")
        sys.exit(1)
    except DuplicateTitleError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except StorageError as e:
        print(f"Error: Failed to create note - {e}")
        sys.exit(1)


def handle_view(args: argparse.Namespace) -> None:
    """
    Handle the 'view' command to display a note.

    This function retrieves and displays a note by its title. If the note is not found
    or there are storage errors, appropriate error messages are displayed.

    Args:
        args: Parsed command line arguments containing the note title
    """
    try:
        # Get the note
        note = vault.get_note_by_title(args.title)
        print(f"\n{note.content}")

    except NoteNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except StorageError as e:
        print(f"Error: Failed to retrieve note - {e}")
        sys.exit(1)


def handle_list(args: argparse.Namespace) -> None:
    """
    Handle the 'list' command to display all notes.

    This function retrieves and displays all note titles in the vault.
    If there are no notes, displays an appropriate message.

    Args:
        args: Parsed command line arguments
    """
    try:
        # Get all titles
        titles = vault.get_all_titles()

        # Display results
        if titles:
            print("\nNotes:")
            for title in titles:
                print(f"- {title}")
        else:
            print("\nNo notes found.")

    except StorageError as e:
        print(f"Error: Failed to list notes - {e}")
        sys.exit(1)


def handle_search(args: argparse.Namespace) -> None:
    """
    Handle the 'search' command to find notes.

    This function searches through all notes for the given term, looking in
    titles, tags, and content. Results are displayed as a list of matching
    note titles.

    Args:
        args: Parsed command line arguments containing the search term
    """
    try:
        # Search for notes
        matching_notes = vault.search_notes(args.term)

        # Display results
        if matching_notes:
            print("\nMatching notes:")
            for note in matching_notes:
                print(f"- {note.title}")
        else:
            print("\nNo matching notes found.")

    except StorageError as e:
        print(f"Error: Failed to search notes - {e}")
        sys.exit(1)


def handle_delete(args: argparse.Namespace) -> None:
    """
    Handle the 'delete' command to remove a note.

    This function deletes a note by its title. If the note is not found
    or there are storage errors, appropriate error messages are displayed.

    Args:
        args: Parsed command line arguments containing the note title
    """
    try:
        # Delete the note
        vault.delete_note_by_title(args.title)
        print(f"\nNote '{args.title}' deleted successfully!")

    except NoteNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except StorageError as e:
        print(f"Error: Failed to delete note - {e}")
        sys.exit(1)


def handle_export(args: argparse.Namespace) -> None:
    """
    Handle the 'export' command to export notes to files.

    This function exports all notes from the vault to individual text files
    in the specified output directory. Each file is named after the note's
    title and contains both the title and content.

    Args:
        args: Parsed command line arguments containing the output directory
    """
    try:
        # Get output directory
        output_dir = args.output_dir or "mpkv_export"

        # Export notes
        vault.export_notes(output_dir)
        print(f"\nNotes exported successfully to: {output_dir}")

    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except StorageError as e:
        print(f"Error: Failed to export notes - {e}")
        sys.exit(1)


def handle_tags(args: argparse.Namespace) -> None:
    """
    Handle the 'tags' command to display tag statistics.

    This function retrieves all tags and their usage counts from the vault,
    then displays them in alphabetical order. If there are no tags,
    displays an appropriate message.

    Args:
        args: Parsed command line arguments
    """
    try:
        # Get tag counts
        tag_counts = vault.get_all_tags_with_counts()

        # Display results
        if tag_counts:
            print("\nTags:")
            for tag in sorted(tag_counts.keys()):
                count = tag_counts[tag]
                print(f"- {tag} ({count} note{'s' if count != 1 else ''})")
        else:
            print("\nNo tags found.")

    except StorageError as e:
        print(f"Error: Failed to get tags - {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the MPKV CLI.

    This function sets up the argument parser and routes commands to their
    respective handlers.
    """
    parser = argparse.ArgumentParser(
        description="MPKV - A simple note-taking system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Command to execute"
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new note")
    add_parser.add_argument("title", help="Title of the note")
    add_parser.add_argument("content", nargs="?", help="Content of the note")
    add_parser.add_argument("--tags", "-t", help="Tags for the note (comma-separated)")
    add_parser.set_defaults(func=handle_add)

    # View command
    view_parser = subparsers.add_parser("view", help="View a note")
    view_parser.add_argument("title", help="Title of the note to view")
    view_parser.set_defaults(func=handle_view)

    # List command
    list_parser = subparsers.add_parser("list", help="List all notes")
    list_parser.set_defaults(func=handle_list)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search notes")
    search_parser.add_argument("term", help="Search term to look for in notes")
    search_parser.set_defaults(func=handle_search)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a note")
    delete_parser.add_argument("title", help="Title of the note to delete")
    delete_parser.set_defaults(func=handle_delete)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export notes to text files")
    export_parser.add_argument(
        "--output-dir",
        help="Directory to export notes to (default: mpkv_export)",
    )
    export_parser.set_defaults(func=handle_export)

    # Tags command
    tags_parser = subparsers.add_parser(
        "tags", help="List all tags and their usage counts"
    )
    tags_parser.set_defaults(func=handle_tags)

    # Parse arguments and execute command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
