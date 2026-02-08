"""
Ollama Embedding Provider
Local embedding generation via Ollama using nomic-embed-text.
"""

import requests
import numpy as np
from typing import List, Optional


class OllamaEmbeddingProvider:
    """
    Local embedding generation via Ollama.

    Uses nomic-embed-text (768 dimensions, 137M params) for generating
    embeddings of file descriptions and search queries.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        timeout: int = 60
    ):
        """
        Initialize embedding provider.

        Args:
            model: Embedding model name (default: nomic-embed-text)
            base_url: Ollama API base URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/embed"
        self.timeout = timeout

    def is_available(self) -> bool:
        """
        Check if Ollama is running and the embedding model is available.

        Returns:
            True if embedding generation is available
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code != 200:
                return False

            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            # Check for exact model or partial match
            for name in model_names:
                if self.model in name:
                    return True

            return False
        except Exception:
            return False

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            numpy array of shape (dim,) with float32 values

        Raises:
            RuntimeError: If embedding generation fails
        """
        result = self._call_embed_api([text])
        return np.array(result[0], dtype=np.float32)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            numpy array of shape (N, dim) with float32 values

        Raises:
            RuntimeError: If embedding generation fails
        """
        if not texts:
            return np.array([], dtype=np.float32)

        result = self._call_embed_api(texts)
        return np.array(result, dtype=np.float32)

    def _call_embed_api(self, texts: List[str]) -> List[List[float]]:
        """
        Call Ollama's /api/embed endpoint.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            RuntimeError: If API call fails
        """
        payload = {
            "model": self.model,
            "input": texts,
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
        except requests.Timeout:
            raise RuntimeError(
                f"Embedding request timed out after {self.timeout}s. "
                f"Try with fewer texts."
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama embed API error (status {response.status_code}): "
                f"{response.text[:200]}"
            )

        try:
            result = response.json()
        except ValueError:
            raise RuntimeError(f"Invalid JSON from Ollama: {response.text[:200]}")

        embeddings = result.get("embeddings")
        if embeddings is None:
            raise RuntimeError(f"No 'embeddings' field in response: {result}")

        return embeddings
