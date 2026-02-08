"""
Format Results Node
Rank, filter, and format search results for display.
"""

from typing import Dict, List, Any


def rank_and_format(state: dict) -> dict:
    """
    Apply threshold and top-k filtering to candidates.

    Args:
        state: Search state with 'candidates', 'threshold', 'top_k'

    Returns:
        Updated state with 'results' (filtered and ranked)
    """
    candidates = state.get("candidates", [])
    threshold = state.get("threshold", 0.3)
    top_k = state.get("top_k", 10)

    # Filter by threshold
    results = [c for c in candidates if c["score"] >= threshold]

    # Take top-k
    results = results[:top_k]

    state["results"] = results
    return state
