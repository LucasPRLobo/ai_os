"""
Classify Files Node
Separates files into categories: images, text, and other.
"""

from pathlib import Path
from models.state import OrganizerState
from models.file_metadata import FileMetadata
from typing import List


# File type classifications
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    '.tiff', '.tif', '.ico', '.heic', '.heif', '.raw', '.cr2', '.nef'
}

TEXT_EXTENSIONS = {
    '.txt', '.md', '.markdown', '.rst', '.log',
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.sass', '.xml', '.json', '.yaml', '.yml',
    '.sh', '.bash', '.sql', '.r', '.m',
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.odt', '.rtf',
    '.xls', '.xlsx', '.ods', '.csv',
    '.ppt', '.pptx', '.odp',
}


def classify_files(state: OrganizerState) -> OrganizerState:
    """
    Classify files into categories: images, text, documents, and other.
    
    Separates the file list into different categories based on file extension.
    This allows parallel processing of different file types.
    
    Args:
        state: Current graph state with files (List[FileMetadata])
        
    Returns:
        Updated state with classified file lists:
        - image_files: List[FileMetadata]
        - text_files: List[FileMetadata]
        - document_files: List[FileMetadata]
        - other_files: List[FileMetadata]
    """
    files = state.get("files", [])
    warnings = state.get("warnings", []).copy()
    
    # Initialize categorized lists
    image_files = []
    text_files = []
    document_files = []
    other_files = []
    
    # Classify each file
    for file in files:
        extension = file.extension.lower()
        
        if extension in IMAGE_EXTENSIONS:
            image_files.append(file)
        elif extension in TEXT_EXTENSIONS:
            text_files.append(file)
        elif extension in DOCUMENT_EXTENSIONS:
            document_files.append(file)
        else:
            other_files.append(file)
    
    # Update state with classified files
    state["image_files"] = image_files
    state["text_files"] = text_files
    state["document_files"] = document_files
    state["other_files"] = other_files
    
    # Add classification summary to warnings
    total = len(files)
    if total > 0:
        summary = (
            f"Classified {total} files: "
            f"{len(image_files)} images, "
            f"{len(text_files)} text, "
            f"{len(document_files)} documents, "
            f"{len(other_files)} other"
        )
        warnings.append(summary)
    
    state["warnings"] = warnings
    
    return state


def get_file_category(file: FileMetadata) -> str:
    """
    Get the category for a single file.
    
    Args:
        file: FileMetadata object
        
    Returns:
        Category string: "image", "text", "document", or "other"
    """
    extension = file.extension.lower()
    
    if extension in IMAGE_EXTENSIONS:
        return "image"
    elif extension in TEXT_EXTENSIONS:
        return "text"
    elif extension in DOCUMENT_EXTENSIONS:
        return "document"
    else:
        return "other"


# Example usage (commented out)
"""
from models.state import create_initial_state
from models.file_metadata import FileMetadata
from datetime import datetime

# Create test state with mixed files
state = create_initial_state(input_paths=[])
state["files"] = [
    FileMetadata(
        name="photo.jpg",
        path="/tmp/photo.jpg",
        extension=".jpg",
        size=1024,
        modified_date=datetime.now(),
        created_date=datetime.now(),
        content_preview=None,
        content_type="image",
        parent_directory="tmp"
    ),
    FileMetadata(
        name="script.py",
        path="/tmp/script.py",
        extension=".py",
        size=2048,
        modified_date=datetime.now(),
        created_date=datetime.now(),
        content_preview="print('hello')",
        content_type="text",
        parent_directory="tmp"
    ),
    FileMetadata(
        name="document.pdf",
        path="/tmp/document.pdf",
        extension=".pdf",
        size=4096,
        modified_date=datetime.now(),
        created_date=datetime.now(),
        content_preview=None,
        content_type="document",
        parent_directory="tmp"
    ),
]

# Classify files
state = classify_files(state)

print(f"Images: {len(state['image_files'])}")
print(f"Text files: {len(state['text_files'])}")
print(f"Documents: {len(state['document_files'])}")
print(f"Other: {len(state['other_files'])}")
"""