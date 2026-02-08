"""
File Scanner Node
Recursively scans directories and collects file paths.
"""

from pathlib import Path
from shared.models.state import OrganizerState


# System directories and files to skip
SKIP_DIRECTORIES = {
    '__pycache__', 'node_modules', '.git', '.svn', '.hg',
    'venv', 'env', '.venv', '.env',
    'build', 'dist', 'target', 'out',
    '.idea', '.vscode', '.vs',
    'bin', 'obj', '.cache', '.pytest_cache',
    '.mypy_cache', '.tox', '.eggs',
}

SKIP_FILE_PATTERNS = {
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    '.gitignore', '.gitkeep',
}


def scan_files(state: OrganizerState) -> OrganizerState:
    """
    Scan directories recursively and collect all file paths.

    For each input path:
    - If it's a file, add it directly
    - If it's a directory, scan recursively (if recursive=True)

    Skips hidden files, system directories, and large files.

    Args:
        state: Current graph state with validated input_paths

    Returns:
        Updated state with file_paths list
    """
    from shared.utils.progress import update_progress, show_summary

    update_progress("scan_files", "running")

    input_paths = state.get("input_paths", [])
    recursive = state.get("recursive", True)
    errors = state.get("errors", []).copy()
    warnings = state.get("warnings", []).copy()

    all_file_paths = []
    total_size = 0
    max_file_size = 500 * 1024 * 1024  # 500 MB limit

    for path_str in input_paths:
        path = Path(path_str)

        if path.is_file():
            # Single file
            try:
                size = path.stat().st_size

                # Check file size
                if size > max_file_size:
                    warnings.append(f"Skipping large file (>{max_file_size//1024//1024}MB): {path.name}")
                    continue

                all_file_paths.append(str(path.absolute()))
                total_size += size
            except Exception as e:
                warnings.append(f"Cannot read file {path.name}: {str(e)}")

        elif path.is_dir():
            # Directory - scan recursively
            try:
                scanned_files, scanned_size = _scan_directory(
                    path,
                    recursive=recursive,
                    max_file_size=max_file_size,
                    warnings=warnings
                )
                all_file_paths.extend(scanned_files)
                total_size += scanned_size
            except Exception as e:
                errors.append(f"Error scanning directory {path.name}: {str(e)}")

    # Update state
    state["file_paths"] = all_file_paths
    state["total_files_scanned"] = len(all_file_paths)
    state["total_size_bytes"] = total_size
    state["errors"] = errors
    state["warnings"] = warnings

    # Check if we found any files
    if not all_file_paths:
        if not errors:
            warnings.append("No files found to organize")
        state["warnings"] = warnings

    update_progress("scan_files", "complete")
    show_summary(state)

    return state


def _scan_directory(
    directory: Path,
    recursive: bool = True,
    max_file_size: int = 500 * 1024 * 1024,
    warnings: list = None
) -> tuple[list[str], int]:
    """
    Recursively scan a directory for files.

    Args:
        directory: Directory path to scan
        recursive: Whether to scan subdirectories
        max_file_size: Maximum file size to include (bytes)
        warnings: List to append warnings to

    Returns:
        Tuple of (file_paths, total_size)
    """
    if warnings is None:
        warnings = []

    file_paths = []
    total_size = 0

    try:
        items = list(directory.iterdir())
    except PermissionError:
        warnings.append(f"Permission denied: {directory.name}")
        return file_paths, total_size
    except Exception as e:
        warnings.append(f"Cannot read directory {directory.name}: {str(e)}")
        return file_paths, total_size

    for item in items:
        # Skip hidden files (starting with .)
        if item.name.startswith('.'):
            continue

        # Skip system files
        if item.name in SKIP_FILE_PATTERNS:
            continue

        try:
            if item.is_file():
                # Check file size
                size = item.stat().st_size

                if size > max_file_size:
                    warnings.append(f"Skipping large file (>{max_file_size//1024//1024}MB): {item.name}")
                    continue

                file_paths.append(str(item.absolute()))
                total_size += size

            elif item.is_dir() and recursive:
                # Skip system directories
                if item.name in SKIP_DIRECTORIES:
                    continue

                # Recursively scan subdirectory
                sub_files, sub_size = _scan_directory(
                    item,
                    recursive=recursive,
                    max_file_size=max_file_size,
                    warnings=warnings
                )
                file_paths.extend(sub_files)
                total_size += sub_size

        except PermissionError:
            warnings.append(f"Permission denied: {item.name}")
        except Exception as e:
            warnings.append(f"Error processing {item.name}: {str(e)}")

    return file_paths, total_size
