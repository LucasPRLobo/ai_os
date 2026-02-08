"""
Analyze Text Node
Extracts content and metadata from text files using LLM analysis
with extension-based heuristic fallback.
"""

import json
import requests
from shared.models.state import OrganizerState
from typing import Dict, List, Optional
from shared.utils.progress import update_progress


# Extension -> language mapping for code files
EXTENSION_LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript",
    ".java": "java", ".cpp": "c++", ".c": "c", ".h": "c",
    ".cs": "c#", ".go": "go", ".rs": "rust", ".rb": "ruby",
    ".php": "php", ".swift": "swift", ".kt": "kotlin",
    ".scala": "scala", ".r": "r", ".R": "r",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell", ".bat": "batch",
    ".html": "html", ".css": "css", ".scss": "scss",
    ".sql": "sql", ".lua": "lua", ".pl": "perl",
    ".dart": "dart", ".ex": "elixir", ".exs": "elixir",
    ".hs": "haskell", ".ml": "ocaml", ".clj": "clojure",
    ".vue": "vue", ".svelte": "svelte",
}

# Extension -> document type mapping
EXTENSION_DOCTYPE_MAP = {
    # Code
    **{ext: "code" for ext in EXTENSION_LANGUAGE_MAP},
    # Config
    ".json": "config", ".yaml": "config", ".yml": "config",
    ".toml": "config", ".ini": "config", ".cfg": "config",
    ".env": "config", ".xml": "config", ".properties": "config",
    ".editorconfig": "config",
    # Readme/docs
    ".md": "readme", ".rst": "readme", ".adoc": "readme",
    # Logs
    ".log": "log",
    # Data
    ".csv": "data", ".tsv": "data", ".jsonl": "data",
    ".ndjson": "data",
    # Notes
    ".txt": "notes", ".text": "notes",
    # Other text
    ".gitignore": "config", ".dockerignore": "config",
    "Makefile": "config", "Dockerfile": "config",
}


def analyze_text(state: OrganizerState) -> OrganizerState:
    """
    Analyze text files using LLM with heuristic fallback.

    Attempts LLM-based analysis for richer metadata (topics, summary).
    Falls back to extension-based heuristics if LLM is unavailable.

    Args:
        state: Current graph state with text_files

    Returns:
        Updated state with text_analysis results
    """
    update_progress("analyze_text", "running")

    text_files = state.get("text_files", [])
    warnings = state.get("warnings", []).copy()

    if not text_files:
        state["text_analysis"] = []
        state["warnings"] = warnings
        update_progress("analyze_text", "complete")
        return state

    # Try LLM-based analysis, fall back to heuristics
    llm_available = _check_llm_available(state)

    text_analysis = []
    for file in text_files:
        analysis = _build_base_analysis(file)

        # Apply heuristic classification (always runs)
        analysis.update(_heuristic_classify(file))

        # Enrich with LLM if available and file has content
        if llm_available and file.content_preview:
            llm_result = _llm_analyze(file, state)
            if llm_result:
                if llm_result.get("topics"):
                    analysis["topics"] = llm_result["topics"]
                if llm_result.get("summary"):
                    analysis["summary"] = llm_result["summary"]
                if llm_result.get("document_type"):
                    analysis["document_type"] = llm_result["document_type"]

        text_analysis.append(analysis)

    state["text_analysis"] = text_analysis

    if text_files:
        llm_note = " (LLM-enriched)" if llm_available else " (heuristic)"
        warnings.append(f"Analyzed {len(text_files)} text files{llm_note}")

    state["warnings"] = warnings
    update_progress("analyze_text", "complete")
    return state


def _build_base_analysis(file) -> Dict:
    """Build base analysis dict from file metadata."""
    return {
        "file_path": file.path,
        "file_name": file.name,
        "content_type": file.content_type,
        "extension": file.extension,
        "content_preview": file.content_preview,
        "size": file.size,
        "parent_directory": file.parent_directory,
        "topics": [],
        "document_type": "other",
        "language": None,
        "summary": None,
    }


def _heuristic_classify(file) -> Dict:
    """Classify text file using extension-based heuristics."""
    result = {}
    ext = file.extension.lower() if file.extension else ""

    # Detect language
    if ext in EXTENSION_LANGUAGE_MAP:
        result["language"] = EXTENSION_LANGUAGE_MAP[ext]

    # Detect document type
    if ext in EXTENSION_DOCTYPE_MAP:
        result["document_type"] = EXTENSION_DOCTYPE_MAP[ext]
    elif file.content_type == "code":
        result["document_type"] = "code"

    return result


def _check_llm_available(state: OrganizerState) -> bool:
    """Check if Ollama LLM is available for text analysis."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def _llm_analyze(file, state: OrganizerState) -> Optional[Dict]:
    """
    Analyze a single text file using the LLM.

    Uses a lightweight prompt to extract topics, document type, and summary
    from the content preview.
    """
    model = state.get("llm_model", "llama3.2:3b")
    # Use the text model, not the vision model
    if "llava" in model:
        model = "llama3.2:3b"

    preview = (file.content_preview or "")[:500]
    if not preview.strip():
        return None

    prompt = (
        f"Analyze this file and respond with ONLY a JSON object.\n\n"
        f"File: {file.name} ({file.extension})\n"
        f"Content preview:\n```\n{preview}\n```\n\n"
        f"Respond with this exact JSON structure:\n"
        f'{{"topics": ["topic1", "topic2"], '
        f'"document_type": "code|notes|config|data|readme|log|other", '
        f'"summary": "one sentence description"}}'
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 200,
                },
            },
            timeout=30,
        )

        if response.status_code != 200:
            return None

        raw = response.json().get("response", "")

        # Extract JSON from response
        return _parse_llm_json(raw)
    except Exception:
        return None


def _parse_llm_json(raw: str) -> Optional[Dict]:
    """Extract and parse JSON from LLM response."""
    # Try direct parse
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in response
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return None
