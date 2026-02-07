"""
Analyze Other Files Node
Handles documents and other file types.
"""

from models.state import OrganizerState


def analyze_other(state: OrganizerState) -> OrganizerState:
    """
    Analyze document and other file types.
    
    For now, this is a pass-through that uses the existing metadata.
    Future enhancements could:
    - Extract PDF content
    - Read Excel/Word documents
    - Analyze archives
    
    Args:
        state: Current graph state with document_files and other_files
        
    Returns:
        Updated state with document_analysis
    """
    document_files = state.get("document_files", [])
    other_files = state.get("other_files", [])
    warnings = state.get("warnings", []).copy()
    
    # Combine documents and other files for now
    all_other = document_files + other_files
    
    # Simple pass-through with basic metadata
    document_analysis = []
    
    for file in all_other:
        analysis = {
            "file_path": file.path,
            "file_name": file.name,
            "content_type": file.content_type,
            "extension": file.extension,
            "size": file.size,
            "parent_directory": file.parent_directory,
        }
        document_analysis.append(analysis)
    
    # Store results
    state["document_analysis"] = document_analysis
    
    # Add info
    if all_other:
        warnings.append(
            f"Processed {len(document_files)} documents "
            f"and {len(other_files)} other files"
        )
    
    state["warnings"] = warnings
    
    return state


# Example usage (commented out)
"""
from models.state import create_initial_state
from models.file_metadata import FileMetadata
from datetime import datetime

# Create test state
state = create_initial_state(input_paths=[])
state["document_files"] = [
    FileMetadata(
        name="report.pdf",
        path="/tmp/report.pdf",
        extension=".pdf",
        size=4096,
        modified_date=datetime.now(),
        created_date=datetime.now(),
        content_preview=None,
        content_type="document",
        parent_directory="tmp"
    )
]
state["other_files"] = []

# Analyze
state = analyze_other(state)
print(f"Document analysis: {len(state['document_analysis'])} files")
"""