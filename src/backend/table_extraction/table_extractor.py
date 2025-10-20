"""
Table Extractor
Orchestrates table loading and chunking for RAG pipeline
"""

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
