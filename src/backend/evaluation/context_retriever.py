"""
Context Retriever
Retrieves relevant contexts for questions using embeddings
"""

from typing import List, Dict
from sentence_transformers import util
import torch


class ContextRetriever:
    """Retrieves relevant contexts using semantic similarity"""

    def __init__(self, embedder):
        """Initialize context retriever"""
        self.embedder = embedder

    def _prepare_chunk_texts(self, chunks: List[Dict]) -> List[str]:
        """Prepare chunk texts with headers"""
        return [f"{chunk['section_header']}\n{chunk['content']}" for chunk in chunks]

    def _get_top_k_indices(self, question_emb, chunk_embs, top_k: int, num_chunks: int):
        """Get top-k indices based on similarity"""
        similarities = util.cos_sim(question_emb, chunk_embs)[0]
        return torch.topk(similarities, k=min(top_k, num_chunks)).indices

    def get_relevant_contexts(self, question: str, chunks: List[Dict], top_k: int = 5) -> List[str]:
        """Retrieve most relevant chunks for a question"""
        chunk_texts = self._prepare_chunk_texts(chunks)
        question_emb = self.embedder.encode(question, convert_to_tensor=True)
        chunk_embs = self.embedder.encode(chunk_texts, convert_to_tensor=True, show_progress_bar=False)
        top_indices = self._get_top_k_indices(question_emb, chunk_embs, top_k, len(chunks))
        return [chunk_texts[idx.item()] for idx in top_indices]

    def prepare_contexts_from_chunks(self, retrieved_chunks: List[Dict]) -> List[str]:
        """Prepare context strings from retrieved chunks"""
        return [f"{chunk['section_header']}\n\n{chunk['content']}" for chunk in retrieved_chunks[:5]]
