"""
Search Query Nodes
Embed the query and retrieve candidate matches from the index.
"""

import numpy as np
from typing import Dict, List, Any, Optional

from shared.providers.embedding import OllamaEmbeddingProvider
from shared.learning.embedding_store import EmbeddingStore


def embed_query(state: dict) -> dict:
    """
    Embed the natural language query using Ollama.

    Args:
        state: Search state with 'query' field

    Returns:
        Updated state with 'query_embedding'
    """
    query = state.get("query", "")
    errors = state.get("errors", []).copy()

    if not query.strip():
        errors.append("Empty search query")
        state["errors"] = errors
        state["query_embedding"] = None
        return state

    try:
        provider = OllamaEmbeddingProvider()
        embedding = provider.embed(query)
        state["query_embedding"] = embedding
    except Exception as e:
        errors.append(f"Failed to embed query: {e}")
        state["query_embedding"] = None

    state["errors"] = errors
    return state


def retrieve_candidates(state: dict) -> dict:
    """
    Retrieve candidate files by cosine similarity.

    Loads all embeddings from SQLite (optionally filtered by type),
    computes cosine similarity with the query embedding, and returns
    ranked candidates.

    Args:
        state: Search state with 'query_embedding' and filters

    Returns:
        Updated state with 'candidates' list
    """
    query_embedding = state.get("query_embedding")
    content_type_filter = state.get("content_type_filter")
    errors = state.get("errors", []).copy()

    if query_embedding is None:
        state["candidates"] = []
        return state

    store = EmbeddingStore()

    try:
        metadata, embeddings = store.get_all_embeddings(
            content_type=content_type_filter
        )
    except Exception as e:
        errors.append(f"Failed to load embeddings: {e}")
        state["candidates"] = []
        state["errors"] = errors
        return state

    if len(metadata) == 0:
        state["candidates"] = []
        return state

    # Compute cosine similarity
    scores = _cosine_similarity(query_embedding, embeddings)

    # Build candidates with scores
    candidates = []
    for i, meta in enumerate(metadata):
        candidates.append({
            **meta,
            "score": float(scores[i]),
        })

    # Sort by score (highest first)
    candidates.sort(key=lambda x: x["score"], reverse=True)

    state["candidates"] = candidates
    state["errors"] = errors
    return state


def _cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a query vector and a matrix of vectors.

    Args:
        query: Shape (dim,)
        matrix: Shape (N, dim)

    Returns:
        Array of shape (N,) with similarity scores
    """
    # Normalize query
    query_norm = query / (np.linalg.norm(query) + 1e-8)

    # Normalize each row of matrix
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-8)
    matrix_norm = matrix / norms

    # Dot product gives cosine similarity
    return matrix_norm @ query_norm
