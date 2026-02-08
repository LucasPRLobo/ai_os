"""
Embedding Store
SQLite-backed embedding storage for file search indexing.

Stores file embeddings at ~/.ai_os/embeddings.db for fast
similarity search across indexed files.
"""

import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any


DEFAULT_DB_PATH = Path.home() / ".ai_os" / "embeddings.db"


class EmbeddingStore:
    """
    SQLite-backed embedding storage at ~/.ai_os/embeddings.db

    Stores file embeddings as binary blobs alongside metadata
    for efficient retrieval and similarity search.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize embedding store.

        Args:
            db_path: Custom path for database (default: ~/.ai_os/embeddings.db)
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create the database schema if it doesn't exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_embeddings (
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    content_type TEXT,
                    content_summary TEXT,
                    embedding BLOB NOT NULL,
                    embedding_dim INTEGER NOT NULL,
                    file_hash TEXT,
                    file_modified TIMESTAMP,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path
                ON file_embeddings(file_path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_type
                ON file_embeddings(content_type)
            """)
            conn.commit()

    def save_embedding(
        self,
        file_path: str,
        file_name: str,
        embedding: np.ndarray,
        content_type: str = None,
        summary: str = None,
        file_hash: str = None,
        file_modified: datetime = None
    ):
        """
        Save or update an embedding for a file.

        Args:
            file_path: Absolute path to the file
            file_name: File name
            embedding: numpy array (float32)
            content_type: File content type (image, text, code, etc.)
            summary: Brief description for display
            file_hash: Hash to detect changes
            file_modified: File modification timestamp
        """
        embedding_bytes = embedding.astype(np.float32).tobytes()
        embedding_dim = len(embedding)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_embeddings
                (file_path, file_name, content_type, content_summary,
                 embedding, embedding_dim, file_hash, file_modified, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                file_name,
                content_type,
                summary,
                embedding_bytes,
                embedding_dim,
                file_hash,
                file_modified.isoformat() if file_modified else None,
                datetime.now().isoformat()
            ))
            conn.commit()

    def get_embedding(self, file_path: str) -> Optional[np.ndarray]:
        """
        Get the embedding for a specific file.

        Args:
            file_path: Absolute path to the file

        Returns:
            numpy array or None if not indexed
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT embedding, embedding_dim FROM file_embeddings WHERE file_path = ?",
                (file_path,)
            ).fetchone()

        if row is None:
            return None

        embedding_bytes, dim = row
        return np.frombuffer(embedding_bytes, dtype=np.float32).copy()

    def get_all_embeddings(
        self, content_type: str = None
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Get all stored embeddings, optionally filtered by content type.

        Args:
            content_type: Filter by type (e.g., "image", "text", "code")

        Returns:
            Tuple of (file_metadata_list, embeddings_matrix)
            where embeddings_matrix is shape (N, dim)
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            if content_type:
                rows = conn.execute(
                    """SELECT file_path, file_name, content_type, content_summary,
                              embedding, embedding_dim
                       FROM file_embeddings WHERE content_type = ?""",
                    (content_type,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT file_path, file_name, content_type, content_summary,
                              embedding, embedding_dim
                       FROM file_embeddings"""
                ).fetchall()

        if not rows:
            return [], np.array([], dtype=np.float32)

        metadata = []
        embeddings = []

        for file_path, file_name, ctype, summary, emb_bytes, dim in rows:
            metadata.append({
                "file_path": file_path,
                "file_name": file_name,
                "content_type": ctype,
                "content_summary": summary,
            })
            emb = np.frombuffer(emb_bytes, dtype=np.float32).copy()
            embeddings.append(emb)

        return metadata, np.stack(embeddings)

    def is_indexed(self, file_path: str, file_hash: str = None) -> bool:
        """
        Check if a file is already indexed (optionally with matching hash).

        Args:
            file_path: Absolute path to the file
            file_hash: If provided, also checks hash matches

        Returns:
            True if file is indexed (and hash matches if provided)
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            if file_hash:
                row = conn.execute(
                    "SELECT 1 FROM file_embeddings WHERE file_path = ? AND file_hash = ?",
                    (file_path, file_hash)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM file_embeddings WHERE file_path = ?",
                    (file_path,)
                ).fetchone()

        return row is not None

    def remove_stale(self, existing_paths: set):
        """
        Remove entries for files that no longer exist.

        Args:
            existing_paths: Set of file paths that currently exist
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            all_paths = conn.execute(
                "SELECT file_path FROM file_embeddings"
            ).fetchall()

            stale_paths = [
                row[0] for row in all_paths
                if row[0] not in existing_paths
            ]

            if stale_paths:
                conn.executemany(
                    "DELETE FROM file_embeddings WHERE file_path = ?",
                    [(p,) for p in stale_paths]
                )
                conn.commit()

        return len(stale_paths) if 'stale_paths' in dir() else 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with count, size, last indexed time, type breakdown
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM file_embeddings"
            ).fetchone()[0]

            last_indexed = conn.execute(
                "SELECT MAX(indexed_at) FROM file_embeddings"
            ).fetchone()[0]

            type_counts = conn.execute(
                "SELECT content_type, COUNT(*) FROM file_embeddings GROUP BY content_type"
            ).fetchall()

        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "total_files": count,
            "database_size_bytes": db_size,
            "database_size_human": self._format_size(db_size),
            "last_indexed": last_indexed,
            "type_breakdown": {t: c for t, c in type_counts},
        }

    def clear(self):
        """Remove all entries from the store."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM file_embeddings")
            conn.commit()

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
