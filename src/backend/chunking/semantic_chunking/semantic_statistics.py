"""
Semantic Statistics
Handles statistics calculation and logging for semantic merging
"""

from pathlib import Path
from typing import List, Dict


class SemanticStatistics:
    """Calculates and logs statistics for semantic merging"""

    def __init__(self, logger):
        """Initialize statistics calculator with logger"""
        self.logger = logger

    def _calculate_avg_size(self, chunks: List[Dict]) -> float:
        """Calculate average chunk size"""
        return sum(len(c['content']) for c in chunks) / len(chunks) if chunks else 0

    def _calculate_reduction_pct(self, original_count: int, merged_count: int) -> float:
        """Calculate chunk reduction percentage"""
        return ((original_count - merged_count) / original_count * 100) if original_count else 0

    def calculate_chunk_stats(self, basic_chunks: List[Dict], merged_chunks: List[Dict], output_path: Path) -> Dict:
        """Calculate statistics for merged chunks"""
        return {
            'num_chunks': len(merged_chunks),
            'output_path': output_path,
            'avg_chunk_size': int(self._calculate_avg_size(merged_chunks)),
            'original_chunks': len(basic_chunks),
            'reduction_pct': self._calculate_reduction_pct(len(basic_chunks), len(merged_chunks))
        }

    def _log_merge_header(self):
        """Log merge summary header"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("Semantic merging complete")
        self.logger.info(f"{'='*60}")

    def _log_merge_stats(self, original_count: int, merged_count: int, merges_performed: int, reduction_pct: float):
        """Log merge statistics"""
        self.logger.info(f"  Original chunks: {original_count}")
        self.logger.info(f"  Merged chunks: {merged_count}")
        self.logger.info(f"  Merges performed: {merges_performed}")
        self.logger.info(f"  Reduction: {reduction_pct:.1f}%")
        self.logger.info(f"{'='*60}\n")

    def log_merge_summary(self, original_count: int, merged_count: int, merges_performed: int):
        """Log merge operation summary"""
        self._log_merge_header()
        reduction_pct = self._calculate_reduction_pct(original_count, merged_count)
        self._log_merge_stats(original_count, merged_count, merges_performed, reduction_pct)

    def log_merge_start(self, chunk_count: int):
        """Log merge operation start"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Starting semantic merging on {chunk_count} chunks")
        self.logger.info(f"{'='*60}")
