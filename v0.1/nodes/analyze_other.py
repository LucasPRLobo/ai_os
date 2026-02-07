"""
Analyze Other Files Node
Enriches metadata for documents and other file types with
heuristic classification.
"""

from models.state import OrganizerState
from collections import Counter
from utils.progress import update_progress


# Extension → detailed document type mapping
EXTENSION_DOCTYPE_MAP = {
    # Documents
    ".pdf": "pdf", ".doc": "word", ".docx": "word",
    ".odt": "word", ".rtf": "word",
    # Spreadsheets
    ".xls": "spreadsheet", ".xlsx": "spreadsheet",
    ".ods": "spreadsheet", ".numbers": "spreadsheet",
    # Presentations
    ".ppt": "presentation", ".pptx": "presentation",
    ".odp": "presentation", ".key": "presentation",
    # Archives
    ".zip": "archive", ".tar": "archive", ".gz": "archive",
    ".bz2": "archive", ".xz": "archive", ".7z": "archive",
    ".rar": "archive", ".tar.gz": "archive",
    # Executables
    ".exe": "executable", ".msi": "executable",
    ".dmg": "executable", ".app": "executable",
    ".deb": "executable", ".rpm": "executable",
    ".appimage": "executable",
    # Fonts
    ".ttf": "font", ".otf": "font", ".woff": "font",
    ".woff2": "font",
    # 3D / Design
    ".blend": "3d", ".obj": "3d", ".stl": "3d",
    ".psd": "design", ".ai": "design", ".sketch": "design",
    ".fig": "design", ".xd": "design",
    # Database
    ".db": "database", ".sqlite": "database",
    ".sqlite3": "database", ".mdb": "database",
    # Video
    ".mp4": "video", ".avi": "video", ".mov": "video",
    ".mkv": "video", ".webm": "video", ".flv": "video",
    # Audio
    ".mp3": "audio", ".wav": "audio", ".flac": "audio",
    ".aac": "audio", ".ogg": "audio", ".m4a": "audio",
}


def analyze_other(state: OrganizerState) -> OrganizerState:
    """
    Analyze document and other file types with heuristic enrichment.

    Adds size categorization, detailed document type classification,
    and parent directory grouping.

    Args:
        state: Current graph state with document_files and other_files

    Returns:
        Updated state with document_analysis
    """
    update_progress("analyze_other", "running")

    document_files = state.get("document_files", [])
    other_files = state.get("other_files", [])
    warnings = state.get("warnings", []).copy()

    all_other = document_files + other_files

    document_analysis = []
    parent_dirs = []

    for file in all_other:
        analysis = {
            "file_path": file.path,
            "file_name": file.name,
            "content_type": file.content_type,
            "extension": file.extension,
            "size": file.size,
            "parent_directory": file.parent_directory,
            "size_category": _categorize_size(file.size),
            "detailed_type": _classify_document(file),
        }
        document_analysis.append(analysis)
        parent_dirs.append(file.parent_directory)

    # Add directory group info
    dir_counts = Counter(parent_dirs)
    for analysis in document_analysis:
        group_size = dir_counts.get(analysis["parent_directory"], 1)
        analysis["directory_group_size"] = group_size

    state["document_analysis"] = document_analysis

    if all_other:
        warnings.append(
            f"Processed {len(document_files)} documents "
            f"and {len(other_files)} other files"
        )

    state["warnings"] = warnings
    update_progress("analyze_other", "complete")
    return state


def _categorize_size(size_bytes: int) -> str:
    """Categorize file size into human-friendly buckets."""
    if size_bytes < 10 * 1024:
        return "tiny"
    elif size_bytes < 100 * 1024:
        return "small"
    elif size_bytes < 1024 * 1024:
        return "medium"
    elif size_bytes < 10 * 1024 * 1024:
        return "large"
    else:
        return "huge"


def _classify_document(file) -> str:
    """Classify document by extension into a detailed type."""
    ext = file.extension.lower() if file.extension else ""
    return EXTENSION_DOCTYPE_MAP.get(ext, file.content_type or "unknown")
