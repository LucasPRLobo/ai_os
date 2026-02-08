"""
Input Validator Node
Validates that input paths exist and are accessible.
"""

from pathlib import Path
from shared.models.state import OrganizerState


def validate_input(state: OrganizerState) -> OrganizerState:
    """
    Validate that all input paths exist and are accessible.

    Checks each path and reports errors for any that don't exist
    or cannot be accessed.

    Args:
        state: Current graph state with input_paths

    Returns:
        Updated state with errors list (if any validation fails)
    """
    input_paths = state.get("input_paths", [])
    errors = state.get("errors", []).copy()
    warnings = state.get("warnings", []).copy()

    # Check if we have any input paths
    if not input_paths:
        errors.append("No input paths provided")
        state["errors"] = errors
        return state

    # Validate each path
    valid_paths = []
    for path_str in input_paths:
        path = Path(path_str)

        # Check if path exists
        if not path.exists():
            errors.append(f"Path does not exist: {path_str}")
            continue

        # Check if we can access it
        try:
            # Try to stat the path to verify access
            path.stat()
            valid_paths.append(path_str)
        except PermissionError:
            errors.append(f"Permission denied: {path_str}")
        except Exception as e:
            errors.append(f"Cannot access {path_str}: {str(e)}")

    # Update state
    state["errors"] = errors
    state["warnings"] = warnings

    # If no valid paths, stop here
    if not valid_paths:
        if not errors:
            errors.append("No valid input paths found")
            state["errors"] = errors

    return state
