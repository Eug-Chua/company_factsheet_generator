"""
Chunk Statistics
Handles calculating merge statistics
"""

from pathlib import Path
from typing import List, Dict


class ChunkStatistics:
    """Calculates statistics about merged chunks"""

    def __init__(self, logger):
        """Initialize statistics calculator with logger"""
        self.logger = logger

    def _filter_chunks_by_type(self, merged_chunks: List[Dict], content_type: str) -> List[Dict]:
        """Filter chunks by content type"""
        return [c for c in merged_chunks if c.get('content_type') == content_type]

    def _calculate_avg_chunk_size(self, chunks: List[Dict]) -> float:
        """Calculate average chunk size"""
        return sum(len(c['content']) for c in chunks) / len(chunks) if chunks else 0

    def _build_statistics_dict(self, merged_chunks: List[Dict], text_chunks: List[Dict],
                               table_chunks: List[Dict]) -> Dict:
        """Build statistics dictionary"""
        return {
            'total_chunks': len(merged_chunks),
            'text_chunks': len(text_chunks),
            'table_chunks': len(table_chunks),
            'text_avg_size': self._calculate_avg_chunk_size(text_chunks),
            'table_avg_size': self._calculate_avg_chunk_size(table_chunks),
            'overall_avg_size': self._calculate_avg_chunk_size(merged_chunks)
        }

    def get_merge_statistics(self, merged_chunks: List[Dict]) -> Dict:
        """Calculate statistics about merged chunks"""
        text_chunks = self._filter_chunks_by_type(merged_chunks, 'text')
        table_chunks = self._filter_chunks_by_type(merged_chunks, 'table')
        return self._build_statistics_dict(merged_chunks, text_chunks, table_chunks)

    def _log_summary_header(self, company_name: str):
        """Log summary header"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Merge Summary for {company_name}")
        self.logger.info(f"{'='*60}")

    def _log_summary_stats(self, stats: Dict, output_path: Path):
        """Log summary statistics"""
        self.logger.info(f"  Text chunks: {stats['text_chunks']} (avg {stats['text_avg_size']:.0f} chars)")
        self.logger.info(f"  Table chunks: {stats['table_chunks']} (avg {stats['table_avg_size']:.0f} chars)")
        self.logger.info(f"  Total chunks: {stats['total_chunks']} (avg {stats['overall_avg_size']:.0f} chars)")
        self.logger.info(f"  Output: {output_path}")
        self.logger.info(f"{'='*60}\n")

    def log_merge_summary(self, stats: Dict, output_path: Path, company_name: str):
        """Log merge summary statistics"""
        self._log_summary_header(company_name)
        self._log_summary_stats(stats, output_path)
