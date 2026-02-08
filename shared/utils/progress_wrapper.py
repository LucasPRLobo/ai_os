"""
Progress-Enabled Node Wrapper
Shows how to add progress tracking to any node.
"""

from shared.models.state import OrganizerState
from shared.utils.progress import update_progress, show_summary


def wrap_node_with_progress(node_func, node_name: str):
    """
    Wrap a node function with progress tracking.

    Args:
        node_func: The node function to wrap
        node_name: Name of the node for progress display

    Returns:
        Wrapped function with progress tracking
    """
    def wrapped(state: OrganizerState) -> OrganizerState:
        # Start progress
        update_progress(node_name, "running")

        try:
            # Execute node
            result = node_func(state)

            # Mark complete
            update_progress(node_name, "complete")

            # Show summary if relevant
            show_summary(result)

            return result

        except Exception as e:
            # Mark error
            update_progress(node_name, "error")
            raise

    return wrapped
