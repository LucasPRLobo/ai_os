"""
Analyze Text Node
Extracts content and basic information from text files.
"""

from models.state import OrganizerState
from typing import Dict, List


def analyze_text(state: OrganizerState) -> OrganizerState:
    """
    Analyze text files and extract content.
    
    For now, this is a simple implementation that just passes through
    the existing metadata. In the future, this could:
    - Extract topics/keywords
    - Classify document type
    - Detect entities
    - Summarize content
    
    Args:
        state: Current graph state with text_files
        
    Returns:
        Updated state with text_analysis results
    """
    text_files = state.get("text_files", [])
    warnings = state.get("warnings", []).copy()
    
    # For now, just pass through the file metadata
    # The content_preview is already extracted in metadata_extractor
    text_analysis = []
    
    for file in text_files:
        analysis = {
            "file_path": file.path,
            "file_name": file.name,
            "content_type": file.content_type,
            "extension": file.extension,
            "content_preview": file.content_preview,
            "size": file.size,
            "parent_directory": file.parent_directory,
        }
        text_analysis.append(analysis)
    
    # Store results
    state["text_analysis"] = text_analysis
    
    # Add info
    if text_files:
        warnings.append(f"Analyzed {len(text_files)} text files")
    
    state["warnings"] = warnings
    
    return state


# Example usage (commented out)
"""
from models.state import create_initial_state
from models.file_metadata import FileMetadata
from datetime import datetime

# Create test state
state = create_initial_state(input_paths=[])
state["text_files"] = [
    FileMetadata(
        name="script.py",
        path="/tmp/script.py",
        extension=".py",
        size=2048,
        modified_date=datetime.now(),
        created_date=datetime.now(),
        content_preview="print('hello world')",
        content_type="code",
        parent_directory="tmp"
    )
]

# Analyze
state = analyze_text(state)
print(f"Text analysis: {len(state['text_analysis'])} files")
"""