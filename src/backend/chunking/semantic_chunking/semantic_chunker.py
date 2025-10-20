"""
Semantic Chunker
Orchestrates semantic merging of chunks using OpenAI embeddings
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
from config_loader import load_config
from extraction.extractor import MarkdownExtractor
from .semantic_loader import SemanticLoader
from .table_detector import TableDetector
from .embedder import Embedder
from .merge_strategy import MergeStrategy
from .semantic_statistics import SemanticStatistics

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)


class SemanticChunker:
    """Orchestrates semantic merging of chunks"""

    def __init__(self, config=None, similarity_threshold=0.60, max_merged_size=4000):
        """Initialize semantic chunker"""
        self.config = config or load_config()
        self._setup_logging()
        self._setup_chunking_parameters(similarity_threshold, max_merged_size)
        self._initialize_openai_client()
        self._log_initialization()
        self._initialize_components()
        self.extractor = MarkdownExtractor(self.config)

    def _setup_logging(self):
        """Setup logging for semantic chunking"""
        self.logger = self.config.setup_logger("semantic_chunking", __name__)

    def _setup_chunking_parameters(self, similarity_threshold: float, max_merged_size: int):
        """Setup semantic chunking parameters"""
        self.similarity_threshold = similarity_threshold
        self.max_merged_size = max_merged_size

    def _get_openai_api_key(self) -> str:
        """Get and validate OpenAI API key"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return api_key

    def _initialize_openai_client(self):
        """Initialize OpenAI client and set model"""
        api_key = self._get_openai_api_key()
        self.client = OpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-3-small"

    def _log_initialization(self):
        """Log initialization parameters"""
        self.logger.info("Initialized SemanticChunker with:")
        self.logger.info(f"  Similarity threshold: {self.similarity_threshold}")
        self.logger.info(f"  Max merged size: {self.max_merged_size}")
        self.logger.info(f"  Embedding model: {self.embedding_model}")

    def _initialize_components(self):
        """Initialize all semantic chunking components"""
        self.table_detector = TableDetector(self.logger)
        self.loader = SemanticLoader(self.logger, self.config, self.table_detector)
        self.embedder = Embedder(self.logger, self.client, self.embedding_model)
        self.merge_strategy = MergeStrategy(self.logger, self.embedder,
                                           self.similarity_threshold, self.max_merged_size)
        self.statistics = SemanticStatistics(self.logger)

    def _process_merge_chains(self, chunks: List[Dict], embeddings: List[np.ndarray]) -> tuple:
        """Process all merge chains and return merged chunks"""
        merged_chunks, i, total_merges = [], 0, 0
        while i < len(chunks):
            current_chunk, _, next_i, merges = self.merge_strategy.merge_chain(chunks, embeddings, i)
            merged_chunks.append(current_chunk)
            total_merges += merges
            i = next_i
        return merged_chunks, total_merges

    def _merge_similar_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Merge semantically similar adjacent chunks"""
        if not chunks:
            return []
        self.statistics.log_merge_start(len(chunks))
        embeddings = self.embedder.embed_chunks(chunks)
        merged_chunks, total_merges = self._process_merge_chains(chunks, embeddings)
        self.merge_strategy.renumber_chunks(merged_chunks)
        self.statistics.log_merge_summary(len(chunks), len(merged_chunks), total_merges)
        return merged_chunks

    def run(self, chunks_path: Optional[Path] = None) -> Dict:
        """
        Execute the complete semantic chunking pipeline.

        This is the main entry point for semantic chunk merging.
        Encapsulates the internal workflow: load chunks → embed → merge → save.

        Args:
            chunks_path: Optional path to chunks JSON. If None, uses config default.

        Returns:
            Dict with merge statistics:
                - num_chunks: Final number of chunks after merging
                - original_chunks: Original number of chunks before merging
                - reduction_pct: Percentage reduction in chunk count
                - avg_chunk_size: Average chunk size after merging
                - output_path: Path where merged chunks were saved
        """
        chunks_path = chunks_path or self.config.chunks_path
        basic_chunks = self.loader.load_chunks_file(chunks_path)
        self.logger.info(f"Applying semantic merging (threshold={self.similarity_threshold})...")
        merged_chunks = self._merge_similar_chunks(basic_chunks)
        output_path = self.loader.save_merged_chunks(merged_chunks, chunks_path)
        return self.statistics.calculate_chunk_stats(basic_chunks, merged_chunks, output_path)

    def _perform_basic_chunking(self, markdown_path: Path) -> Dict:
        """Perform basic chunking using MarkdownExtractor"""
        self.logger.info(f"Step 1: Basic chunking of {markdown_path}")
        return self.extractor.process_markdown_file(markdown_path)

    def process_markdown(self, markdown_path: Optional[Path] = None) -> Dict:
        """Complete pipeline: Markdown → Basic Chunks → Semantic Merging"""
        markdown_path = markdown_path or self.config.markdown_path
        basic_result = self._perform_basic_chunking(markdown_path)
        return self.run(basic_result['chunks_path'])
