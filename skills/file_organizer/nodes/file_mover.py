"""
File Mover Node
Executes the selected organization by moving/copying files.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from shared.models.state import OrganizerState
from shared.models.suggestions import Suggestion, FolderStructure


def execute_organization(state: OrganizerState) -> OrganizerState:
    """
    Execute the selected organization suggestion.

    Args:
        state: Current graph state with selected_suggestion

    Returns:
        Updated state with execution results
    """
    selected = state.get("selected_suggestion")
    files = state.get("files", [])
    errors = state.get("errors", []).copy()

    if state.get("user_cancelled"):
        state["execution_result"] = {"status": "cancelled"}
        return state

    if not selected:
        errors.append("No suggestion selected for execution")
        state["errors"] = errors
        state["execution_result"] = {"status": "error", "message": "No suggestion selected"}
        return state

    # Build file path lookup
    file_lookup = {f.name: f.path for f in files}

    # Get configuration
    dry_run = state.get("dry_run", False)
    use_copy = state.get("use_copy", False)
    output_dir = state.get("output_dir")

    # Determine base output path
    if output_dir:
        base_path = Path(output_dir) / selected.folder_structure.base_path
    else:
        if files:
            common_parent = Path(files[0].path).parent
            base_path = common_parent / selected.folder_structure.base_path
        else:
            base_path = Path.cwd() / selected.folder_structure.base_path

    # Show preview
    operations = _build_operations(selected.folder_structure, file_lookup, base_path)

    if not operations:
        errors.append("No valid file operations to execute")
        state["errors"] = errors
        state["execution_result"] = {"status": "error", "message": "No valid operations"}
        return state

    _show_preview(operations, dry_run, use_copy)

    # Confirm execution
    if not dry_run:
        if not _confirm_execution(len(operations)):
            state["execution_result"] = {"status": "cancelled"}
            state["user_cancelled"] = True
            return state

    # Execute operations
    result = _execute_operations(operations, dry_run, use_copy)

    state["execution_result"] = result
    state["errors"] = errors

    return state


def _build_operations(
    folder_structure: FolderStructure,
    file_lookup: Dict[str, str],
    base_path: Path
) -> List[Tuple[str, Path]]:
    """Build list of (source, destination) operations."""
    operations = []

    for folder in folder_structure.folders:
        folder_path = base_path / folder.name

        for filename in folder.files:
            if filename in file_lookup:
                source = file_lookup[filename]
                dest = folder_path / filename
                operations.append((source, dest))

        # Handle subfolders recursively
        if folder.subfolders:
            for subfolder in folder.subfolders:
                subfolder_path = folder_path / subfolder.name
                for filename in subfolder.files:
                    if filename in file_lookup:
                        source = file_lookup[filename]
                        dest = subfolder_path / filename
                        operations.append((source, dest))

    return operations


def _show_preview(
    operations: List[Tuple[str, Path]],
    dry_run: bool,
    use_copy: bool
):
    """Show preview of file operations."""
    action = "COPY" if use_copy else "MOVE"
    mode = "[DRY RUN] " if dry_run else ""

    print(f"\n{mode}  FILE {action} PREVIEW")
    print("=" * 60)

    # Group by destination folder
    by_folder: Dict[str, List[Tuple[str, str]]] = {}
    for source, dest in operations:
        folder = str(dest.parent)
        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append((Path(source).name, str(dest)))

    for folder, files in sorted(by_folder.items()):
        print(f"\n  {folder}/")
        for filename, dest in files:
            print(f"    <- {filename}")

    print(f"\n{'_' * 60}")
    print(f"Total: {len(operations)} files to {action.lower()}")

    if dry_run:
        print("(Dry run - no files will be modified)")


def _confirm_execution(num_files: int) -> bool:
    """Ask user to confirm execution."""
    print(f"\n  This will move {num_files} files to new locations.")
    print("   Original files will be relocated (not copied).")

    try:
        response = input("\nProceed? [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def _execute_operations(
    operations: List[Tuple[str, Path]],
    dry_run: bool,
    use_copy: bool
) -> Dict:
    """Execute the file operations."""
    if dry_run:
        return {
            "status": "dry_run",
            "would_process": len(operations),
            "message": f"Dry run complete. Would process {len(operations)} files."
        }

    success_count = 0
    error_count = 0
    errors = []
    created_dirs = set()

    action_verb = "Copying" if use_copy else "Moving"
    action_past = "copied" if use_copy else "moved"

    print(f"\n  {action_verb} files...")
    print("-" * 60)

    for source, dest in operations:
        try:
            dest_dir = dest.parent
            if dest_dir not in created_dirs:
                dest_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.add(dest_dir)

            if not os.path.exists(source):
                errors.append(f"Source not found: {source}")
                error_count += 1
                continue

            if dest.exists():
                stem = dest.stem
                suffix = dest.suffix
                timestamp = datetime.now().strftime("%H%M%S")
                dest = dest.parent / f"{stem}_{timestamp}{suffix}"

            if use_copy:
                shutil.copy2(source, dest)
            else:
                shutil.move(source, dest)

            success_count += 1
            print(f"    + {Path(source).name}")

        except PermissionError:
            errors.append(f"Permission denied: {source}")
            error_count += 1
            print(f"    x {Path(source).name} (permission denied)")
        except Exception as e:
            errors.append(f"Error with {source}: {str(e)}")
            error_count += 1
            print(f"    x {Path(source).name} ({str(e)})")

    print("-" * 60)

    status = "success" if error_count == 0 else "partial"
    result = {
        "status": status,
        "files_processed": success_count,
        "files_failed": error_count,
        "directories_created": len(created_dirs),
        "action": action_past
    }

    if errors:
        result["errors"] = errors

    print(f"\n  {success_count} files {action_past}")
    if error_count > 0:
        print(f"  {error_count} files failed")
    print(f"  {len(created_dirs)} directories created")

    return result


def dry_run_organization(state: OrganizerState) -> OrganizerState:
    """Preview organization without executing."""
    state["dry_run"] = True
    return execute_organization(state)
