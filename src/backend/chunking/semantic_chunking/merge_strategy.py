"""
Merge Strategy
Handles merge decision logic and chunk merging operations
"""

from typing import List, Dict
import numpy as np


class MergeStrategy:
    """Determines if and how chunks should be merged"""

    def __init__(self, logger, embedder, similarity_threshold: float, max_merged_size: int):
        """Initialize merge strategy with parameters"""
        self.logger = logger
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.max_merged_size = max_merged_size

    def _get_combined_size(self, chunk1: Dict, chunk2: Dict) -> int:
        """Get combined size of two chunks"""
        return len(chunk1['content']) + len(chunk2['content'])

    def _check_size_constraint(self, chunk1: Dict, chunk2: Dict) -> bool:
        """Check if merged size would exceed limit"""
        combined_size = self._get_combined_size(chunk1, chunk2)
        if combined_size > self.max_merged_size:
            self.logger.debug(f"Skipping merge (size {combined_size} > {self.max_merged_size}): "
                            f"{chunk1['section_header'][:50]} + {chunk2['section_header'][:50]}")
            return False
        return True

    def _check_table_type_mismatch(self, chunk1: Dict, chunk2: Dict) -> bool:
        """Check if chunks have table/non-table type mismatch"""
        is_table1 = chunk1.get('is_table', False)
        is_table2 = chunk2.get('is_table', False)
        if is_table1 != is_table2:
            self.logger.debug(f"Skipping merge (table/non-table mismatch): "
                            f"{chunk1['section_header'][:50]} (table={is_table1}) + "
                            f"{chunk2['section_header'][:50]} (table={is_table2})")
            return True
        return False

    def _check_table_similarity_threshold(self, chunk1: Dict, chunk2: Dict, similarity: float) -> bool:
        """Check if table chunks meet stricter similarity threshold"""
        if chunk1.get('is_table', False) and chunk2.get('is_table', False):
            table_threshold = min(self.similarity_threshold + 0.10, 0.95)
            if similarity < table_threshold:
                self.logger.debug(f"Skipping table merge (similarity {similarity:.3f} < {table_threshold:.3f})")
                return False
        return True

    def should_merge(self, chunk1: Dict, chunk2: Dict, similarity: float) -> bool:
        """Determine if two chunks should be merged"""
        if similarity < self.similarity_threshold:
            return False
        if self._check_table_type_mismatch(chunk1, chunk2):
            return False
        if not self._check_table_similarity_threshold(chunk1, chunk2, similarity):
            return False
        return self._check_size_constraint(chunk1, chunk2)

    def _build_merged_chunk_dict(self, chunk1: Dict, chunk2: Dict) -> Dict:
        """Build dictionary for merged chunk"""
        return {
            'chunk_id': chunk1['chunk_id'],
            'section_header': f"{chunk1['section_header']} + {chunk2['section_header']}",
            'header_level': min(chunk1['header_level'], chunk2['header_level']),
            'content': f"{chunk1['content']}\n\n{chunk2['content']}",
            'merged_from': [chunk1['chunk_id'], chunk2['chunk_id']],
            'merged': True,
            'is_table': chunk1.get('is_table', False),
            'contains_numerical_data': chunk1.get('contains_numerical_data', False)
        }

    def merge_chunks(self, chunk1: Dict, chunk2: Dict) -> Dict:
        """Merge two chunks into one, preserving table metadata"""
        return self._build_merged_chunk_dict(chunk1, chunk2)

    def _add_merge_tracking(self, chunk: Dict):
        """Add merge tracking fields if missing"""
        if 'merged' not in chunk:
            chunk['merged'] = False
            chunk['merged_from'] = [chunk['chunk_id']]

    def _ensure_table_metadata(self, chunk: Dict):
        """Ensure table metadata fields exist"""
        if 'is_table' not in chunk:
            chunk['is_table'] = False
        if 'contains_numerical_data' not in chunk:
            chunk['contains_numerical_data'] = False

    def initialize_chunk(self, chunk: Dict) -> Dict:
        """Initialize chunk with merge tracking fields"""
        chunk = chunk.copy()
        self._add_merge_tracking(chunk)
        self._ensure_table_metadata(chunk)
        return chunk

    def _log_merge(self, current_chunk: Dict, next_chunk: Dict, similarity: float):
        """Log merge operation"""
        self.logger.info(
            f"Merging (similarity={similarity:.3f}): "
            f"[{current_chunk['section_header'][:40]}...] + "
            f"[{next_chunk['section_header'][:40]}...]"
        )

    def _perform_single_merge(self, current_chunk: Dict, current_embedding: np.ndarray,
                              next_chunk: Dict, next_embedding: np.ndarray) -> tuple:
        """Perform a single merge operation"""
        similarity = self.embedder.cosine_similarity(current_embedding, next_embedding)
        self._log_merge(current_chunk, next_chunk, similarity)
        merged_chunk = self.merge_chunks(current_chunk, next_chunk)
        merged_embedding = (current_embedding + next_embedding) / 2
        return merged_chunk, merged_embedding

    def merge_chain(self, chunks: List[Dict], embeddings: List[np.ndarray], i: int) -> tuple:
        """Merge a chain of similar chunks starting at index i"""
        current_chunk = self.initialize_chunk(chunks[i])
        current_embedding = embeddings[i]
        j, merges_performed = i + 1, 0
        while j < len(chunks):
            similarity = self.embedder.cosine_similarity(current_embedding, embeddings[j])
            if self.should_merge(current_chunk, chunks[j], similarity):
                current_chunk, current_embedding = self._perform_single_merge(
                    current_chunk, current_embedding, chunks[j], embeddings[j])
                merges_performed += 1
                j += 1
            else:
                break
        return current_chunk, current_embedding, j, merges_performed

    def renumber_chunks(self, chunks: List[Dict]):
        """Renumber chunk IDs sequentially"""
        for idx, chunk in enumerate(chunks):
            chunk['chunk_id'] = idx
