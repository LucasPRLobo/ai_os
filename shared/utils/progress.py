"""
Progress Tracker
Shows execution progress as nodes complete in the graph.
"""

import sys
from datetime import datetime
from typing import Optional


class ProgressTracker:
    """
    Tracks and displays progress through the file organization pipeline.

    Shows which node is currently executing and marks completion.
    """

    # Node execution order and labels
    NODES = [
        ("validate_input", "Validating paths"),
        ("scan_files", "Scanning files"),
        ("extract_metadata", "Extracting metadata"),
        ("classify_files", "Classifying files"),
        ("analyze_images", "Analyzing images"),
        ("analyze_text", "Analyzing text"),
        ("analyze_other", "Processing other files"),
        ("aggregate_results", "Aggregating results"),
        ("analyze_with_llm", "Generating suggestions"),
    ]

    def __init__(self, enabled: bool = True):
        """
        Initialize progress tracker.

        Args:
            enabled: Whether to show progress (False for quiet mode)
        """
        self.enabled = enabled
        self.current_step = 0
        self.total_steps = len(self.NODES)
        self.start_time = None
        self.step_times = {}

    def start(self):
        """Start tracking progress."""
        if not self.enabled:
            return

        self.start_time = datetime.now()
        print("Analyzing files...\n")

    def update(self, node_name: str, status: str = "running"):
        """
        Update progress for a node.

        Args:
            node_name: Name of the node (e.g., "scan_files")
            status: "running", "complete", or "error"
        """
        if not self.enabled:
            return

        # Find node index
        node_index = None
        label = node_name

        for i, (name, node_label) in enumerate(self.NODES):
            if name == node_name:
                node_index = i + 1
                label = node_label
                break

        if node_index is None:
            return

        if status == "running":
            # Show node starting
            print(f"  [{node_index}/{self.total_steps}] {label}...", end="", flush=True)
            self.step_times[node_name] = datetime.now()

        elif status == "complete":
            # Show node completed
            elapsed = ""
            if node_name in self.step_times:
                duration = (datetime.now() - self.step_times[node_name]).total_seconds()
                if duration > 0.1:
                    elapsed = f" ({duration:.1f}s)"

            print(f" done{elapsed}")

        elif status == "error":
            print(f" FAILED")

    def finish(self):
        """Show completion message."""
        if not self.enabled or self.start_time is None:
            return

        total_time = (datetime.now() - self.start_time).total_seconds()
        print(f"\nTotal time: {total_time:.1f}s\n")

    def show_step_summary(self, state: dict):
        """
        Show a summary after each major step.

        Args:
            state: Current state dictionary
        """
        if not self.enabled:
            return

        # Show file count after scanning
        if "total_files_scanned" in state and state["total_files_scanned"]:
            count = state["total_files_scanned"]
            size = state.get("total_size_bytes", 0)
            size_mb = size / (1024 * 1024)
            print(f"     -> Found {count} files ({size_mb:.1f} MB)")

        # Show classification after classify
        if "image_files" in state and state["image_files"] is not None:
            img_count = len(state.get("image_files", []))
            txt_count = len(state.get("text_files", []))
            doc_count = len(state.get("document_files", []))
            other_count = len(state.get("other_files", []))

            if img_count + txt_count + doc_count + other_count > 0:
                print(f"     -> {img_count} images, {txt_count} text, {doc_count} docs, {other_count} other")

        # Show image analysis count
        if "image_analysis" in state and state["image_analysis"]:
            analyzed = len(state["image_analysis"])
            total = len(state.get("image_files", []))
            if total > 0:
                print(f"     -> Analyzed {analyzed}/{total} images")


# Global progress tracker instance
_tracker = None


def get_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker


def init_progress(enabled: bool = True):
    """Initialize progress tracking."""
    global _tracker
    _tracker = ProgressTracker(enabled=enabled)
    return _tracker


def update_progress(node_name: str, status: str = "running"):
    """Update progress for a node."""
    tracker = get_tracker()
    tracker.update(node_name, status)


def show_summary(state: dict):
    """Show step summary."""
    tracker = get_tracker()
    tracker.show_step_summary(state)
