"""
Embedder
Handles OpenAI embeddings and similarity calculations
"""

from typing import List, Dict
import numpy as np
from openai import OpenAI


class Embedder:
    """Handles OpenAI embeddings and similarity calculations"""

    def __init__(self, logger, client: OpenAI, embedding_model: str):
        """Initialize embedder with logger and OpenAI client"""
        self.logger = logger
        self.client = client
        self.embedding_model = embedding_model

    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within token limits"""
        max_chars = 30000  # ~7500 tokens, leaving buffer
        return text[:max_chars] if len(text) > max_chars else text

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get OpenAI embedding for text"""
        text = self._truncate_text(text)
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return np.array(response.data[0].embedding)

    def _calculate_vector_norms(self, vec1: np.ndarray, vec2: np.ndarray) -> tuple:
        """Calculate norms of two vectors"""
        return np.linalg.norm(vec1), np.linalg.norm(vec2)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1, norm2 = self._calculate_vector_norms(vec1, vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _log_embedding_progress(self, i: int, total: int, batch_size: int):
        """Log embedding progress"""
        if (i + batch_size) % 50 == 0 or (i + batch_size) >= total:
            self.logger.info(f"  Embedded {min(i + batch_size, total)}/{total} chunks")

    def _get_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Get OpenAI embeddings for a batch of texts"""
        truncated_texts = [self._truncate_text(text) for text in texts]
        response = self.client.embeddings.create(
            input=truncated_texts,
            model=self.embedding_model
        )
        return [np.array(item.embedding) for item in response.data]

    def _process_embedding_batch(self, batch: List[Dict]) -> List[np.ndarray]:
        """Process a single batch of chunks for embedding"""
        batch_texts = [chunk['content'] for chunk in batch]
        return self._get_batch_embeddings(batch_texts)

    def embed_chunks(self, chunks: List[Dict]) -> List[np.ndarray]:
        """Get embeddings for all chunks in batches"""
        self.logger.info(f"Embedding {len(chunks)} chunks in batches...")
        embeddings, batch_size = [], 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings.extend(self._process_embedding_batch(batch))
            self._log_embedding_progress(i, len(chunks), len(batch))
        self.logger.info(f"✓ Completed embedding {len(chunks)} chunks")
        return embeddings
