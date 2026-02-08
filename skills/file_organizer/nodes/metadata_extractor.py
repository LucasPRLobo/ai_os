"""
Metadata Extractor Node
Extracts metadata and content from files.
"""

import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional
from shared.models.state import OrganizerState
from shared.models.file_metadata import FileMetadata


# Content type mappings
TEXT_EXTENSIONS = {
    '.txt', '.md', '.markdown', '.rst', '.log',
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.sass', '.xml', '.json', '.yaml', '.yml',
    '.sh', '.bash', '.sql', '.r', '.m',
}

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    '.tiff', '.tif', '.ico', '.heic', '.heif',
}

VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv',
    '.m4v', '.mpg', '.mpeg', '.3gp',
}

AUDIO_EXTENSIONS = {
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus',
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.odt', '.rtf',
    '.xls', '.xlsx', '.ods', '.csv',
    '.ppt', '.pptx', '.odp',
}

ARCHIVE_EXTENSIONS = {
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
}

CODE_EXTENSIONS = TEXT_EXTENSIONS - {'.txt', '.md', '.markdown', '.rst', '.log'}


def extract_metadata(state: OrganizerState) -> OrganizerState:
    """
    Extract metadata and content from all scanned files.

    For each file:
    - Extracts basic metadata (name, size, dates)
    - Determines content type
    - Reads content preview for text files
    - Creates FileMetadata objects

    Args:
        state: Current graph state with file_paths

    Returns:
        Updated state with files (List[FileMetadata])
    """
    file_paths = state.get("file_paths", [])
    max_content_preview = state.get("max_content_preview", 1000)
    errors = state.get("errors", []).copy()
    warnings = state.get("warnings", []).copy()

    files = []

    for file_path_str in file_paths:
        try:
            file_metadata = _extract_file_metadata(
                file_path_str,
                max_content_preview=max_content_preview
            )
            files.append(file_metadata)
        except Exception as e:
            warnings.append(f"Cannot extract metadata from {Path(file_path_str).name}: {str(e)}")

    # Update state
    state["files"] = files
    state["errors"] = errors
    state["warnings"] = warnings

    # Check if we extracted any files
    if not files:
        if not errors:
            errors.append("No file metadata could be extracted")
        state["errors"] = errors

    return state


def _extract_file_metadata(
    file_path: str,
    max_content_preview: int = 1000
) -> FileMetadata:
    """
    Extract metadata from a single file.

    Args:
        file_path: Absolute path to file
        max_content_preview: Maximum characters for content preview

    Returns:
        FileMetadata object
    """
    path = Path(file_path)

    # Get basic file stats
    stats = path.stat()

    # Extract basic metadata
    name = path.name
    extension = path.suffix.lower()
    size = stats.st_size
    modified_date = datetime.fromtimestamp(stats.st_mtime)
    created_date = datetime.fromtimestamp(stats.st_ctime)
    parent_directory = path.parent.name

    # Determine content type
    content_type = _determine_content_type(extension)

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(str(path))

    # Read content preview for text files
    content_preview = None
    if content_type in {'text', 'code'}:
        content_preview = _read_text_preview(path, max_content_preview)

    # Create FileMetadata object
    return FileMetadata(
        name=name,
        path=str(path.absolute()),
        extension=extension,
        size=size,
        modified_date=modified_date,
        created_date=created_date,
        content_preview=content_preview,
        content_type=content_type,
        mime_type=mime_type,
        parent_directory=parent_directory,
        hash=None
    )


def _determine_content_type(extension: str) -> str:
    """
    Determine content type from file extension.

    Args:
        extension: File extension (including dot)

    Returns:
        Content type string
    """
    ext_lower = extension.lower()

    if ext_lower in CODE_EXTENSIONS:
        return 'code'
    elif ext_lower in TEXT_EXTENSIONS:
        return 'text'
    elif ext_lower in IMAGE_EXTENSIONS:
        return 'image'
    elif ext_lower in VIDEO_EXTENSIONS:
        return 'video'
    elif ext_lower in AUDIO_EXTENSIONS:
        return 'audio'
    elif ext_lower in DOCUMENT_EXTENSIONS:
        return 'document'
    elif ext_lower in ARCHIVE_EXTENSIONS:
        return 'archive'
    else:
        return 'unknown'


def _read_text_preview(path: Path, max_chars: int = 1000) -> Optional[str]:
    """
    Read a preview of text file content.

    Tries multiple encodings and handles errors gracefully.

    Args:
        path: Path to text file
        max_chars: Maximum characters to read

    Returns:
        Text preview or None if cannot read
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']

    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read(max_chars)
                # Clean up content (remove excessive whitespace)
                content = ' '.join(content.split())
                return content
        except UnicodeDecodeError:
            continue
        except Exception:
            return None

    return None
