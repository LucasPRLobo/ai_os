"""
Models Package
Pydantic models and state definitions for the AI File Organizer.
"""

from models.file_metadata import FileMetadata, BatchMetadata
from models.suggestions import (
    FolderNode,
    FolderStructure,
    Suggestion,
    SuggestionResponse
)
from models.analysis import ImageAnalysis
from models.state import OrganizerState, create_initial_state

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