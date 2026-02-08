"""
Search Graphs
LangGraph pipelines for indexing and searching files.

Index Graph: scan -> extract -> describe -> embed -> store
Search Graph: embed_query -> retrieve -> rank -> display
"""

from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END

from skills.search.nodes.index_files import (
    scan_and_extract,
    build_descriptions,
    embed_and_store,
)
from skills.search.nodes.search_query import (
    embed_query,
    retrieve_candidates,
)
from skills.search.nodes.format_results import rank_and_format


# ===== State Definitions =====

class IndexState(TypedDict):
    """State for the indexing pipeline."""
    input_paths: List[str]
    recursive: bool
    errors: List[str]
    warnings: List[str]
    # Populated by nodes
    file_metadata: Optional[List[Dict[str, Any]]]
    descriptions: Optional[List[Dict[str, Any]]]
    files_indexed: Optional[int]
    files_skipped: Optional[int]


class SearchState(TypedDict):
    """State for the search pipeline."""
    query: str
    content_type_filter: Optional[str]
    top_k: int
    threshold: float
    errors: List[str]
    # Populated by nodes
    query_embedding: Optional[Any]
    candidates: Optional[List[Dict[str, Any]]]
    results: Optional[List[Dict[str, Any]]]


# ===== Index Graph =====

def create_index_graph():
    """
    Create the file indexing graph.

    Pipeline: scan_and_extract -> build_descriptions -> embed_and_store
    """
    graph = StateGraph(IndexState)

    graph.add_node("scan_and_extract", scan_and_extract)
    graph.add_node("build_descriptions", build_descriptions)
    graph.add_node("embed_and_store", embed_and_store)

    graph.set_entry_point("scan_and_extract")

    graph.add_edge("scan_and_extract", "build_descriptions")
    graph.add_edge("build_descriptions", "embed_and_store")
    graph.add_edge("embed_and_store", END)

    return graph.compile()


# ===== Search Graph =====

def create_search_graph():
    """
    Create the search query graph.

    Pipeline: embed_query -> retrieve_candidates -> rank_and_format
    """
    graph = StateGraph(SearchState)

    graph.add_node("embed_query", embed_query)
    graph.add_node("retrieve_candidates", retrieve_candidates)
    graph.add_node("rank_and_format", rank_and_format)

    graph.set_entry_point("embed_query")

    graph.add_edge("embed_query", "retrieve_candidates")
    graph.add_edge("retrieve_candidates", "rank_and_format")
    graph.add_edge("rank_and_format", END)

    return graph.compile()
