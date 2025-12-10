"""
LangGraph State Definition
TypedDict for the state that flows through the organization graph.
"""

from typing import TypedDict, Optional, Any, List, Dict
from models.file_metadata import FileMetadata


class OrganizerState(TypedDict):
    """
    State object for the file organization LangGraph.
    
    This state flows through all nodes in the graph, accumulating data
    and results as it progresses through the workflow.
    
    Note: TypedDict doesn't support Pydantic models directly, so we use
    Any for complex objects like SuggestionResponse and ImageAnalysis.
    """
    
    # ===== INPUT =====
    input_paths: List[str]
    """List of file or directory paths to organize"""
    
    # ===== CONFIGURATION =====
    llm_provider: str
    """LLM provider to use: 'ollama' or 'api'"""
    
    llm_model: Optional[str]
    """Specific model name (e.g., 'llama3.2:3b', 'claude-sonnet-4')"""
    
    max_content_preview: Optional[int]
    """Maximum characters to preview from text files (default: 1000)"""
    
    recursive: Optional[bool]
    """Whether to scan directories recursively (default: True)"""
    
    # ===== PROCESSING DATA =====
    file_paths: Optional[List[str]]
    """List of all file paths found during scanning"""
    
    files: List[FileMetadata]
    """List of analyzed file metadata objects"""
    
    # ===== CLASSIFIED FILES =====
    image_files: Optional[List[FileMetadata]]
    """Files classified as images"""
    
    text_files: Optional[List[FileMetadata]]
    """Files classified as text/code"""
    
    document_files: Optional[List[FileMetadata]]
    """Files classified as documents (PDF, DOCX, etc.)"""
    
    other_files: Optional[List[FileMetadata]]
    """Files that don't fit other categories"""
    
    # ===== ANALYSIS RESULTS =====
    image_analysis: Optional[List[Any]]
    """Image analysis results (List of ImageAnalysis objects)"""
    
    text_analysis: Optional[List[Any]]
    """Text analysis results (List of dicts)"""
    
    document_analysis: Optional[List[Any]]
    """Document analysis results (List of dicts)"""
    
    aggregated_analysis: Optional[Dict[str, Any]]
    """Aggregated analysis from all file types"""
    
    # ===== OUTPUT =====
    suggestions: Optional[Any]
    """The final organization suggestions from the LLM (SuggestionResponse object)"""
    
    # ===== CONFIRM & ACT =====
    selected_suggestion: Optional[Any]
    """The user-selected suggestion to execute"""
    
    user_cancelled: Optional[bool]
    """Whether the user cancelled the operation"""
    
    dry_run: Optional[bool]
    """If True, preview only - don't actually move files"""
    
    use_copy: Optional[bool]
    """If True, copy files instead of moving them"""
    
    output_dir: Optional[str]
    """Custom output directory for organized files"""
    
    execution_result: Optional[Dict[str, Any]]
    """Results from file move/copy execution"""
    
    # ===== ERROR HANDLING =====
    errors: List[str]
    """List of error messages encountered during processing"""
    
    warnings: List[str]
    """List of warning messages (non-fatal issues)"""
    
    # ===== METADATA =====
    total_files_scanned: Optional[int]
    """Total number of files found during scanning"""
    
    total_size_bytes: Optional[int]
    """Total size of all files in bytes"""
    
    processing_time_seconds: Optional[float]
    """Total processing time in seconds"""


# Helper function to create initial state
def create_initial_state(
    input_paths: List[str],
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
    max_content_preview: int = 1000,
    recursive: bool = True,
    dry_run: bool = False,
    use_copy: bool = False,
    output_dir: Optional[str] = None
) -> OrganizerState:
    """
    Create an initial state for the organizer graph.
    
    Args:
        input_paths: List of file or directory paths to organize
        llm_provider: LLM provider to use ('ollama' or 'api')
        llm_model: Specific model name (optional)
        max_content_preview: Max chars for content preview
        recursive: Whether to scan directories recursively
        dry_run: Preview only, don't move files
        use_copy: Copy files instead of moving
        output_dir: Custom output directory
        
    Returns:
        Initial OrganizerState with default values
    """
    return OrganizerState(
        # Input
        input_paths=input_paths,
        
        # Configuration
        llm_provider=llm_provider,
        llm_model=llm_model,
        max_content_preview=max_content_preview,
        recursive=recursive,
        
        # Processing data (empty initially)
        file_paths=None,
        files=[],
        
        # Classified files (None initially)
        image_files=None,
        text_files=None,
        document_files=None,
        other_files=None,
        
        # Analysis results (None initially)
        image_analysis=None,
        text_analysis=None,
        document_analysis=None,
        aggregated_analysis=None,
        
        # Output (None initially)
        suggestions=None,
        
        # Confirm & Act
        selected_suggestion=None,
        user_cancelled=None,
        dry_run=dry_run,
        use_copy=use_copy,
        output_dir=output_dir,
        execution_result=None,
        
        # Error handling (empty initially)
        errors=[],
        warnings=[],
        
        # Metadata (None initially)
        total_files_scanned=None,
        total_size_bytes=None,
        processing_time_seconds=None
    )