"""
Chunk Processor
Handles merging and transforming chunks
"""

from pathlib import Path
from typing import List, Dict


class ChunkProcessor:
    """Processes and merges chunks"""

    def __init__(self, logger, chunk_loader):
        """Initialize processor with logger and chunk loader"""
        self.logger = logger
        self.chunk_loader = chunk_loader

    def _add_content_type_to_chunks(self, chunks: List[Dict], content_type: str):
        """Add content_type field to chunks if missing"""
        for chunk in chunks:
            if 'content_type' not in chunk:
                chunk['content_type'] = content_type

    def _handle_missing_table_chunks(self, text_chunks: List[Dict]) -> List[Dict]:
        """Handle case where table chunks are missing"""
        self._add_content_type_to_chunks(text_chunks, 'text')
        return text_chunks

    def _renumber_chunk_ids(self, text_chunks: List[Dict], table_chunks: List[Dict]):
        """Renumber chunk IDs to avoid conflicts"""
        for i, chunk in enumerate(text_chunks):
            chunk['chunk_id'] = i
        for i, chunk in enumerate(table_chunks):
            chunk['chunk_id'] = 10000 + i

    def _combine_and_log_chunks(self, text_chunks: List[Dict], table_chunks: List[Dict]) -> List[Dict]:
        """Combine chunks and log merge statistics"""
        merged_chunks = text_chunks + table_chunks
        self.logger.info(f"Merged chunks: {len(text_chunks)} text + {len(table_chunks)} table = {len(merged_chunks)} total")
        return merged_chunks

    def merge_chunks(self, text_chunks_path: Path, table_chunks_path: Path) -> List[Dict]:
        """Merge text and table chunks"""
        text_chunks = self.chunk_loader.load_chunks(text_chunks_path)
        if not table_chunks_path.exists():
            self.logger.warning(f"No table chunks found at {table_chunks_path}, using text chunks only")
            return self._handle_missing_table_chunks(text_chunks)
        table_chunks = self.chunk_loader.load_chunks(table_chunks_path)
        self._add_content_type_to_chunks(text_chunks, 'text')
        self._renumber_chunk_ids(text_chunks, table_chunks)
        return self._combine_and_log_chunks(text_chunks, table_chunks)
