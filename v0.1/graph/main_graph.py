"""
Main Organization Graph
Wires together all nodes into a complete file organization pipeline.

Optimized with:
- Conditional routing (skip analysis if no files of that type)
- Smart sequencing (only run necessary analyzers)
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from models.state import OrganizerState

# Import all nodes
from nodes.input_validator import validate_input
from nodes.file_scanner import scan_files
from nodes.metadata_extractor import extract_metadata
from nodes.classify_files import classify_files
from nodes.analyze_image import analyze_images
from nodes.analyze_text import analyze_text
from nodes.analyze_other import analyze_other
from nodes.aggregate_results import aggregate_results
from nodes.llm_analyzer import analyze_with_llm


def route_after_classify(state: OrganizerState) -> Literal["analyze_images", "analyze_text", "analyze_other", "aggregate_results"]:
    """Route to first needed analyzer or skip to aggregate."""
    if state.get("image_files"):
        return "analyze_images"
    elif state.get("text_files"):
        return "analyze_text"
    elif state.get("other_files"):
        return "analyze_other"
    else:
        return "aggregate_results"


def route_after_images(state: OrganizerState) -> Literal["analyze_text", "analyze_other", "aggregate_results"]:
    """After images, check if we need text or other analysis."""
    if state.get("text_files"):
        return "analyze_text"
    elif state.get("other_files"):
        return "analyze_other"
    else:
        return "aggregate_results"


def route_after_text(state: OrganizerState) -> Literal["analyze_other", "aggregate_results"]:
    """After text, check if we need other analysis."""
    if state.get("other_files"):
        return "analyze_other"
    else:
        return "aggregate_results"


def create_organization_graph():
    """Create the complete file organization graph."""
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
    
    # Entry point
    graph.set_entry_point("validate_input")
    
    # Sequential preprocessing
    graph.add_edge("validate_input", "scan_files")
    graph.add_edge("scan_files", "extract_metadata")
    graph.add_edge("extract_metadata", "classify_files")
    
    # Conditional routing after classification - skip empty analyzers
    graph.add_conditional_edges(
        "classify_files",
        route_after_classify,
        {
            "analyze_images": "analyze_images",
            "analyze_text": "analyze_text",
            "analyze_other": "analyze_other",
            "aggregate_results": "aggregate_results",
        }
    )
    
    # Conditional routing after image analysis
    graph.add_conditional_edges(
        "analyze_images",
        route_after_images,
        {
            "analyze_text": "analyze_text",
            "analyze_other": "analyze_other",
            "aggregate_results": "aggregate_results",
        }
    )
    
    # Conditional routing after text analysis
    graph.add_conditional_edges(
        "analyze_text",
        route_after_text,
        {
            "analyze_other": "analyze_other",
            "aggregate_results": "aggregate_results",
        }
    )
    
    # Other always goes to aggregate
    graph.add_edge("analyze_other", "aggregate_results")
    
    # Final LLM analysis
    graph.add_edge("aggregate_results", "analyze_with_llm")
    graph.add_edge("analyze_with_llm", END)
    
    return graph.compile()