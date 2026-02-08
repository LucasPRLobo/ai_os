"""
Search-Specific Prompts
Prompt templates for the search skill.

Currently unused as search relies on embeddings rather than LLM prompts,
but reserved for future query expansion or result re-ranking with LLMs.
"""

QUERY_EXPANSION_PROMPT = """Given the user's search query, generate 2-3 alternative
phrasings that capture the same intent. This helps find files that may use
different terminology.

User query: {query}

Respond with a JSON array of alternative queries:
["alternative 1", "alternative 2"]
"""
