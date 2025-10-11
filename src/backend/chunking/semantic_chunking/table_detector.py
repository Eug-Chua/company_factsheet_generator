"""
Table Detector
Handles detection and annotation of table chunks
"""

import re
from typing import List, Dict, Optional


class TableDetector:
    """Detects and annotates table chunks"""

    def __init__(self, logger):
        """Initialize detector with logger"""
        self.logger = logger

    def _has_table_marker(self, content: str) -> bool:
        """Check if content has markdown table pattern"""
        table_pattern = r'\|[\s\-]+\|[\s\-]+\|'
        return bool(re.search(table_pattern, content))

    def _has_many_pipes(self, content: str) -> bool:
        """Check if content has many pipe characters"""
        return content.count('|') > 10

    def _is_numeric_heavy(self, content: str) -> bool:
        """Check if content is numeric-heavy"""
        numbers = re.findall(r'\d+[,.\d]*', content)
        numeric_density = len(numbers) / max(len(content.split()), 1)
        return numeric_density > 0.15

    def is_table_chunk(self, chunk: Dict) -> bool:
        """Detect if chunk contains table data"""
        content = chunk.get('content', '')
        has_marker = self._has_table_marker(content)
        many_pipes = self._has_many_pipes(content)
        numeric_heavy = self._is_numeric_heavy(content)
        return has_marker or (many_pipes and numeric_heavy)

    def _annotate_single_chunk(self, chunk: Dict) -> Dict:
        """Annotate a single chunk with table information"""
        chunk = chunk.copy()
        chunk['is_table'] = self.is_table_chunk(chunk)
        chunk['contains_numerical_data'] = chunk['is_table']
        return chunk

    def _count_table_chunks(self, chunks: List[Dict]) -> int:
        """Count number of table chunks"""
        return sum(1 for chunk in chunks if chunk.get('is_table', False))

    def annotate_chunks_with_table_info(self, chunks: List[Dict], table_data: Optional[Dict]) -> List[Dict]:
        """Annotate chunks with table detection and data"""
        annotated = [self._annotate_single_chunk(chunk) for chunk in chunks]
        table_count = self._count_table_chunks(annotated)
        self.logger.info(f"Identified {table_count} table chunks out of {len(chunks)}")
        return annotated
