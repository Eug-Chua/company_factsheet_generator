"""
BM25 Retriever
Performs BM25 keyword search and hybrid retrieval with RRF
"""

import re
from typing import List, Dict
from rank_bm25 import BM25Okapi


class BM25Retriever:
    """BM25 search and hybrid retrieval using Reciprocal Rank Fusion"""

    def __init__(self, logger):
        """Initialize BM25 retriever"""
        self.logger = logger

    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25 search (word-level)"""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def _prepare_chunk_texts(self, chunks: List[Dict]) -> List[str]:
        """Prepare chunk texts with section headers"""
        return [f"{chunk['section_header']}\n\n{chunk['content']}" for chunk in chunks]

    def _tokenize_chunks(self, chunk_texts: List[str]):
        """Tokenize all chunks for BM25"""
        return [self._tokenize_text(text) for text in chunk_texts]

    def _create_bm25_index(self, tokenized_chunks):
        """Create BM25 index from tokenized chunks"""
        return BM25Okapi(tokenized_chunks)

    def _get_bm25_scores(self, bm25, query: str):
        """Get BM25 scores for query"""
        tokenized_query = self._tokenize_text(query)
        return bm25.get_scores(tokenized_query)

    def _get_top_indices(self, scores, top_k: int):
        """Get indices of top-k scores"""
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    def _build_result_with_score(self, chunk: Dict, score: float):
        """Build result dict with BM25 score"""
        chunk_copy = chunk.copy()
        chunk_copy['bm25_score'] = float(score)
        return chunk_copy

    def bm25_search(self, query: str, chunks: List[Dict], top_k: int = 10) -> List[Dict]:
        """Perform BM25 keyword search on chunks"""
        chunk_texts = self._prepare_chunk_texts(chunks)
        tokenized_chunks = self._tokenize_chunks(chunk_texts)
        bm25 = self._create_bm25_index(tokenized_chunks)
        bm25_scores = self._get_bm25_scores(bm25, query)
        top_indices = self._get_top_indices(bm25_scores, top_k)
        results = [self._build_result_with_score(chunks[idx], bm25_scores[idx])
                  for idx in top_indices]
        return results

    def _get_chunk_key(self, chunk: Dict):
        """Get unique key for chunk (first 100 chars)"""
        return chunk['content'][:100]

    def _calculate_rrf_score(self, rank: int, k: int = 60):
        """Calculate RRF score: 1 / (k + rank)"""
        return 1.0 / (k + rank)

    def _process_result_list(self, results: List[Dict], rrf_scores: Dict,
                            chunk_map: Dict, k: int):
        """Process a result list and update RRF scores"""
        for rank, chunk in enumerate(results, start=1):
            chunk_key = self._get_chunk_key(chunk)
            rrf_score = self._calculate_rrf_score(rank, k)
            if chunk_key in rrf_scores:
                rrf_scores[chunk_key] += rrf_score
            else:
                rrf_scores[chunk_key] = rrf_score
                chunk_map[chunk_key] = chunk

    def _sort_by_rrf_scores(self, rrf_scores: Dict):
        """Sort chunk keys by RRF scores"""
        return sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

    def _build_merged_results(self, sorted_keys: List[str], rrf_scores: Dict,
                             chunk_map: Dict):
        """Build final merged results with RRF scores"""
        merged_results = []
        for chunk_key in sorted_keys:
            chunk = chunk_map[chunk_key].copy()
            chunk['rrf_score'] = rrf_scores[chunk_key]
            merged_results.append(chunk)
        return merged_results

    def reciprocal_rank_fusion(self, semantic_results: List[Dict],
                               bm25_results: List[Dict], k: int = 60) -> List[Dict]:
        """Combine semantic and BM25 results using Reciprocal Rank Fusion"""
        rrf_scores = {}
        chunk_map = {}
        self._process_result_list(semantic_results, rrf_scores, chunk_map, k)
        self._process_result_list(bm25_results, rrf_scores, chunk_map, k)
        sorted_keys = self._sort_by_rrf_scores(rrf_scores)
        return self._build_merged_results(sorted_keys, rrf_scores, chunk_map)

    def retrieve_hybrid(self, semantic_results: List[Dict], chunks: List[Dict],
                       query: str, top_k: int = 10, bm25_top_k: int = 20) -> List[Dict]:
        """Hybrid retrieval combining semantic and BM25 using RRF"""
        self.logger.debug(f"Hybrid retrieval: semantic={len(semantic_results)}, bm25_top_k={bm25_top_k}")
        bm25_results = self.bm25_search(query, chunks, top_k=bm25_top_k)
        merged_results = self.reciprocal_rank_fusion(semantic_results, bm25_results)
        return merged_results[:top_k]
