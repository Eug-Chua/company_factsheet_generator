"""
Embedder
Handles embeddings and semantic similarity search
"""

from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
import torch


class Embedder:
    """Manages embeddings and semantic retrieval"""

    def __init__(self, config, logger):
        """Initialize embedder with model"""
        self.config = config
        self.logger = logger
        self._load_embedding_model()

    def _load_embedding_model(self):
        """Load sentence transformer embedding model"""
        self.logger.info(f"Loading embedding model: {self.config.embedding_model}")
        self.embedder = SentenceTransformer(self.config.embedding_model)

    def _prepare_chunk_texts(self, chunks: List[Dict]) -> List[str]:
        """Prepare chunk texts with section headers"""
        return [f"{chunk['section_header']}\n\n{chunk['content']}" for chunk in chunks]

    def _encode_question(self, question: str):
        """Encode question as embedding"""
        return self.embedder.encode(question, convert_to_tensor=True)

    def _encode_chunks(self, chunk_texts: List[str]):
        """Encode chunks as embeddings"""
        return self.embedder.encode(chunk_texts, convert_to_tensor=True, show_progress_bar=False)

    def encode_embeddings(self, question: str, chunk_texts: List[str]):
        """Encode question and chunks as embeddings"""
        question_emb = self._encode_question(question)
        chunk_embs = self._encode_chunks(chunk_texts)
        return question_emb, chunk_embs

    def _calculate_similarities(self, question_emb, chunk_embs):
        """Calculate cosine similarities"""
        return util.cos_sim(question_emb, chunk_embs)[0]

    def _get_top_indices(self, similarities, top_k: int, num_chunks: int):
        """Get indices of top-k similar chunks"""
        return torch.topk(similarities, k=min(top_k, num_chunks)).indices

    def _build_chunk_with_score(self, chunk: Dict, similarity_score: float):
        """Build chunk dict with similarity score"""
        chunk_copy = chunk.copy()
        chunk_copy['similarity_score'] = similarity_score
        return chunk_copy

    def get_top_chunks(self, chunks: List[Dict], similarities, top_k: int) -> List[Dict]:
        """Get top-k chunks with similarity scores"""
        top_indices = self._get_top_indices(similarities, top_k, len(chunks))
        relevant_chunks = []
        for idx in top_indices:
            chunk = self._build_chunk_with_score(chunks[idx], similarities[idx].item())
            relevant_chunks.append(chunk)
        return relevant_chunks

    def retrieve_relevant_chunks(self, question: str, chunks: List[Dict],
                                 top_k: int = 10, similarities=None) -> List[Dict]:
        """Retrieve most relevant chunks for a question using embeddings"""
        chunk_texts = self._prepare_chunk_texts(chunks)
        if similarities is None:
            question_emb, chunk_embs = self.encode_embeddings(question, chunk_texts)
            similarities = self._calculate_similarities(question_emb, chunk_embs)
        return self.get_top_chunks(chunks, similarities, top_k)
