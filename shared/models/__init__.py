"""
Models Package
Pydantic models and state definitions for AI-OS.
"""

from shared.models.file_metadata import FileMetadata, BatchMetadata
from shared.models.suggestions import (
    FolderNode,
    FolderStructure,
    Suggestion,
    SuggestionResponse
)
from shared.models.analysis import ImageAnalysis
from shared.models.state import OrganizerState, create_initial_state

__all__ = [
    # File metadata
    "FileMetadata",
    "BatchMetadata",

    # Suggestions
    "FolderNode",
    "FolderStructure",
    "Suggestion",
    "SuggestionResponse",

    # Analysis
    "ImageAnalysis",

    # State
    "OrganizerState",
    "create_initial_state",
]
