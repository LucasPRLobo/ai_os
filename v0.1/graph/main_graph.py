"""
Main Organization Graph
Wires together all nodes into a complete file organization pipeline.
"""

from langgraph.graph import StateGraph, END
from models.state import OrganizerState

# Import all nodes (using correct paths)
from nodes.input_validator import validate_input
from nodes.file_scanner import scan_files
from nodes.metadata_extractor import extract_metadata
from nodes.classify_files import classify_files
from nodes.analyze_image import analyze_images
from nodes.analyze_text import analyze_text
from nodes.analyze_other import analyze_other
from nodes.aggregate_results import aggregate_results
from nodes.llm_analyzer import analyze_with_llm


def create_organization_graph():
    """
    Create the complete file organization graph.
    
    Flow:
    1. validate_input - Check paths exist
    2. scan_files - Find all files
    3. extract_metadata - Get file metadata
    4. classify_files - Separate by type
    5. [PARALLEL] analyze_images, analyze_text, analyze_other
    6. aggregate_results - Combine all analysis
    7. analyze_with_llm - Generate organization suggestions
    
    Returns:
        Compiled LangGraph application
    """
    # Create graph with our state type
    graph = StateGraph(OrganizerState)
    
    # Add all nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("scan_files", scan_files)
    graph.add_node("extract_metadata", extract_metadata)
    graph.add_node("classify_files", classify_files)
    graph.add_node("analyze_images", analyze_images)
    graph.add_node("analyze_text", analyze_text)
    graph.add_node("analyze_other", analyze_other)
    graph.add_node("aggregate_results", aggregate_results)
    graph.add_node("analyze_with_llm", analyze_with_llm)
    
    # Define the flow (edges)
    graph.set_entry_point("validate_input")
    
    # Sequential flow through preprocessing
    graph.add_edge("validate_input", "scan_files")
    graph.add_edge("scan_files", "extract_metadata")
    graph.add_edge("extract_metadata", "classify_files")
    
    # After classification, process different file types
    # Note: LangGraph executes these sequentially for now
    # True parallel processing would require async implementation
    graph.add_edge("classify_files", "analyze_images")
    graph.add_edge("analyze_images", "analyze_text")
    graph.add_edge("analyze_text", "analyze_other")
    
    # Aggregate all results
    graph.add_edge("analyze_other", "aggregate_results")
    
    # Final LLM analysis
    graph.add_edge("aggregate_results", "analyze_with_llm")
    
    # End
    graph.add_edge("analyze_with_llm", END)
    
    # Compile the graph
    app = graph.compile()
    
    return app


def run_organization(
    input_paths: list[str],
    llm_provider: str = "ollama",
    llm_model: str = None,
    recursive: bool = True,
    max_content_preview: int = 1000
) -> OrganizerState:
    """
    Run the complete file organization pipeline.
    
    Args:
        input_paths: List of file or directory paths to organize
        llm_provider: LLM provider to use ("ollama" or "api")
        llm_model: Specific model name (optional)
        recursive: Whether to scan directories recursively
        max_content_preview: Max characters for text file previews
        
    Returns:
        Final state with organization suggestions
    """
    from models.state import create_initial_state
    
    # Create initial state
    initial_state = create_initial_state(
        input_paths=input_paths,
        llm_provider=llm_provider,
        llm_model=llm_model,
        max_content_preview=max_content_preview,
        recursive=recursive
    )
    
    # Create and run graph
    app = create_organization_graph()
    final_state = app.invoke(initial_state)
    
    return final_state


# Example usage (commented out)
"""
# Run organization on a directory
result = run_organization(
    input_paths=["/home/user/Desktop/messy_files"],
    llm_provider="ollama",
    llm_model="llama3.2:3b",
    recursive=True
)

# Check results
if result.get("errors"):
    print("Errors:", result["errors"])
elif result.get("suggestions"):
    suggestions = result["suggestions"]
    print(f"\\nGot {len(suggestions.suggestions)} suggestions:")
    for i, sugg in enumerate(suggestions.suggestions, 1):
        print(f"\\n{i}. {sugg.folder_structure.base_path}")
        print(f"   Confidence: {sugg.confidence}")
        print(f"   Reasoning: {sugg.reasoning}")
else:
    print("No suggestions generated")

# Print warnings
if result.get("warnings"):
    print("\\nWarnings:")
    for warning in result["warnings"]:
        print(f"  - {warning}")
"""