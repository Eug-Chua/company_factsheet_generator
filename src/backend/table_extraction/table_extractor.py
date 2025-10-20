"""
Table Extractor
Orchestrates table loading and chunking for RAG pipeline
"""

from pathlib import Path
from typing import Dict, Optional
from config_loader import load_config
from .table_loader import TableLoader
from .table_chunker import TableChunker


class NumericalExtractor:
    """Extracts and processes table data from table JSON files"""

    def __init__(self, config=None):
        """Initialize extractor with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging for table extraction"""
        self.logger = self.config.setup_logger("numerical_extraction", __name__)

    def _initialize_components(self):
        """Initialize loader and chunker components"""
        self.loader = TableLoader(self.logger, self.config)
        self.chunker = TableChunker(self.logger, self.config, self.loader)

    def run(self, tables_path: Optional[Path] = None, max_chunk_size: int = 2000) -> Dict:
        """
        Execute the complete table extraction pipeline.

        This is the main entry point for table extraction. Encapsulates the
        internal workflow: load tables → create chunks → save chunks.

        Args:
            tables_path: Optional path to tables JSON. If None, auto-detects.
            max_chunk_size: Maximum size for table chunks in characters.

        Returns:
            Dict with processing statistics:
                - num_tables: Number of tables processed
                - num_chunks: Number of chunks created
                - avg_chunk_size: Average chunk size in characters
                - output_path: Path where chunks were saved
        """
        return self.chunker.process_tables_to_chunks(tables_path, max_chunk_size)
