"""
Index Files Nodes
Scan, extract metadata, build descriptions, and embed files for search.

Reuses v0.1's scanning/metadata infrastructure from shared/.
"""

import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.providers.embedding import OllamaEmbeddingProvider
from shared.learning.embedding_store import EmbeddingStore


# ===== Constants =====

SKIP_DIRECTORIES = {
    '__pycache__', 'node_modules', '.git', '.svn', '.hg',
    'venv', 'env', '.venv', '.env',
    'build', 'dist', 'target', 'out',
    '.idea', '.vscode', '.vs',
    'bin', 'obj', '.cache', '.pytest_cache',
    '.mypy_cache', '.tox', '.eggs',
}

SKIP_FILE_PATTERNS = {
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    '.gitignore', '.gitkeep',
}

TEXT_EXTENSIONS = {
    '.txt', '.md', '.markdown', '.rst', '.log',
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.sass', '.xml', '.json', '.yaml', '.yml',
    '.sh', '.bash', '.sql', '.r', '.m',
}

CODE_EXTENSIONS = TEXT_EXTENSIONS - {'.txt', '.md', '.markdown', '.rst', '.log'}

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    '.tiff', '.tif', '.ico', '.heic', '.heif',
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.odt', '.rtf',
    '.xls', '.xlsx', '.ods', '.csv',
    '.ppt', '.pptx', '.odp',
}

AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}

# Extension -> language name (for descriptions)
LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".java": "Java", ".cpp": "C++", ".c": "C", ".go": "Go",
    ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell",
    ".html": "HTML", ".css": "CSS", ".sql": "SQL",
}


# ===== Node 1: Scan and Extract =====

def scan_and_extract(state: dict) -> dict:
    """
    Scan directories and extract file metadata.

    Finds all files, computes hashes, and determines content types.
    Skips files already indexed with matching hashes.
    """
    input_paths = state.get("input_paths", [])
    recursive = state.get("recursive", True)
    errors = state.get("errors", []).copy()
    warnings = state.get("warnings", []).copy()

    store = EmbeddingStore()
    file_metadata = []
    skipped = 0

    print("  [1/3] Scanning files...")

    for path_str in input_paths:
        path = Path(path_str)
        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = _scan_directory(path, recursive)
        else:
            errors.append(f"Path does not exist: {path_str}")
            continue

        for file_path in files:
            try:
                # Compute file hash
                file_hash = _compute_hash(file_path)

                # Check if already indexed
                if store.is_indexed(str(file_path), file_hash):
                    skipped += 1
                    continue

                # Extract metadata
                meta = _extract_metadata(file_path, file_hash)
                file_metadata.append(meta)

            except Exception as e:
                warnings.append(f"Error processing {file_path.name}: {e}")

    found = len(file_metadata)
    print(f"       Found {found} new files, {skipped} already indexed")

    state["file_metadata"] = file_metadata
    state["files_skipped"] = skipped
    state["errors"] = errors
    state["warnings"] = warnings
    return state


# ===== Node 2: Build Descriptions =====

def build_descriptions(state: dict) -> dict:
    """
    Build searchable text descriptions for each file.

    Creates a single string per file that captures what the file is about,
    suitable for embedding. Uses content previews, filenames, types, and
    parent directory context.
    """
    file_metadata = state.get("file_metadata", [])

    if not file_metadata:
        state["descriptions"] = []
        return state

    print(f"  [2/3] Building descriptions for {len(file_metadata)} files...")

    descriptions = []
    for meta in file_metadata:
        desc = _build_description(meta)
        descriptions.append({
            **meta,
            "description": desc,
        })

    state["descriptions"] = descriptions
    return state


# ===== Node 3: Embed and Store =====

def embed_and_store(state: dict) -> dict:
    """
    Embed file descriptions and store in SQLite.

    Batches texts through Ollama embedding API for efficiency.
    """
    descriptions = state.get("descriptions", [])
    errors = state.get("errors", []).copy()

    if not descriptions:
        state["files_indexed"] = 0
        return state

    print(f"  [3/3] Embedding and storing {len(descriptions)} files...")

    provider = OllamaEmbeddingProvider()
    store = EmbeddingStore()

    # Batch embed
    texts = [d["description"] for d in descriptions]
    batch_size = 32
    indexed = 0

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_descs = descriptions[i:i + batch_size]

        try:
            embeddings = provider.embed_batch(batch_texts)

            for j, (desc, embedding) in enumerate(zip(batch_descs, embeddings)):
                store.save_embedding(
                    file_path=desc["file_path"],
                    file_name=desc["file_name"],
                    embedding=embedding,
                    content_type=desc.get("content_type"),
                    summary=desc["description"][:200],
                    file_hash=desc.get("file_hash"),
                    file_modified=desc.get("file_modified"),
                )
                indexed += 1

        except Exception as e:
            errors.append(f"Embedding batch {i // batch_size + 1} failed: {e}")

        # Progress
        done = min(i + batch_size, len(texts))
        print(f"       Embedded {done}/{len(texts)} files", end="\r")

    print(f"       Embedded {indexed}/{len(texts)} files    ")

    state["files_indexed"] = indexed
    state["errors"] = errors
    return state


# ===== Helper Functions =====

def _scan_directory(directory: Path, recursive: bool = True) -> List[Path]:
    """Recursively scan a directory for files."""
    results = []

    try:
        items = list(directory.iterdir())
    except PermissionError:
        return results

    for item in items:
        if item.name.startswith('.'):
            continue
        if item.name in SKIP_FILE_PATTERNS:
            continue

        if item.is_file():
            results.append(item)
        elif item.is_dir() and recursive:
            if item.name not in SKIP_DIRECTORIES:
                results.extend(_scan_directory(item, recursive))

    return results


def _compute_hash(file_path: Path) -> str:
    """Compute a fast hash of a file (first 8KB + size)."""
    hasher = hashlib.md5()
    try:
        size = file_path.stat().st_size
        hasher.update(str(size).encode())
        with open(file_path, 'rb') as f:
            hasher.update(f.read(8192))
    except Exception:
        hasher.update(str(file_path).encode())
    return hasher.hexdigest()


def _determine_content_type(ext: str) -> str:
    """Determine content type from extension."""
    ext = ext.lower()
    if ext in CODE_EXTENSIONS:
        return 'code'
    elif ext in TEXT_EXTENSIONS:
        return 'text'
    elif ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in VIDEO_EXTENSIONS:
        return 'video'
    elif ext in AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'unknown'


def _extract_metadata(file_path: Path, file_hash: str) -> Dict[str, Any]:
    """Extract metadata from a single file."""
    stats = file_path.stat()
    ext = file_path.suffix.lower()
    content_type = _determine_content_type(ext)

    # Read text preview for text files
    content_preview = None
    if content_type in ('text', 'code'):
        content_preview = _read_preview(file_path)

    return {
        "file_path": str(file_path.absolute()),
        "file_name": file_path.name,
        "extension": ext,
        "size": stats.st_size,
        "content_type": content_type,
        "content_preview": content_preview,
        "parent_directory": file_path.parent.name,
        "file_hash": file_hash,
        "file_modified": datetime.fromtimestamp(stats.st_mtime),
    }


def _read_preview(path: Path, max_chars: int = 500) -> Optional[str]:
    """Read a preview of text file content."""
    for encoding in ['utf-8', 'latin-1']:
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read(max_chars)
                return ' '.join(content.split())
        except (UnicodeDecodeError, Exception):
            continue
    return None


def _build_description(meta: Dict[str, Any]) -> str:
    """
    Build a searchable description for a file.

    Combines filename, type, content preview, and context
    into a single string suitable for embedding.
    """
    parts = []
    name = meta["file_name"]
    ext = meta.get("extension", "")
    content_type = meta.get("content_type", "unknown")
    preview = meta.get("content_preview", "")
    parent = meta.get("parent_directory", "")

    # File name and type
    parts.append(f"File: {name}")
    parts.append(f"Type: {content_type}")

    # Parent directory context
    if parent:
        parts.append(f"Located in: {parent}")

    # Language for code files
    if ext in LANG_MAP:
        parts.append(f"Language: {LANG_MAP[ext]}")

    # Content preview for text/code
    if preview:
        parts.append(f"Content: {preview[:300]}")

    # For images, include filename-derived context
    if content_type == "image":
        # Extract meaningful words from filename
        stem = Path(name).stem
        words = stem.replace('_', ' ').replace('-', ' ').replace('.', ' ')
        parts.append(f"Image described by filename: {words}")

    # For documents
    if content_type == "document":
        stem = Path(name).stem
        words = stem.replace('_', ' ').replace('-', ' ')
        parts.append(f"Document: {words}")

    return ". ".join(parts)
