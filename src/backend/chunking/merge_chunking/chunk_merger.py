"""
Chunk Merger
Orchestrates merging of text chunks and table chunks into unified chunk set for RAG
"""

from pathlib import Path
from typing import Dict
from config_loader import load_config
from .chunk_loader import ChunkLoader
from .chunk_processor import ChunkProcessor
from .chunk_saver import ChunkSaver
from .chunk_statistics import ChunkStatistics


class ChunkMerger:
    """Orchestrates merging of text and table chunks for comprehensive RAG retrieval"""

    def __init__(self, config=None):
        """Initialize chunk merger with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging"""
        self.logger = self.config.setup_logger("chunk_merger", __name__)

    def _initialize_components(self):
        """Initialize loader, processor, saver, and statistics components"""
        self.loader = ChunkLoader(self.logger)
        self.processor = ChunkProcessor(self.logger, self.loader)
        self.saver = ChunkSaver(self.logger, self.config)
        self.statistics = ChunkStatistics(self.logger)

    def _get_default_text_chunks_path(self) -> Path:
        """Get default text chunks path"""
        return self.config.chunks_path

    def _get_default_table_chunks_path(self) -> Path:
        """Get default table chunks path"""
        return self.config.output_dir / f"{self.config.company_name}_table_chunks.json"

    def _resolve_merge_paths(self, text_chunks_path: Path = None, table_chunks_path: Path = None) -> tuple:
        """Resolve text and table chunks paths"""
        text_path = text_chunks_path or self._get_default_text_chunks_path()
        table_path = table_chunks_path or self._get_default_table_chunks_path()
        return text_path, table_path

    def _merge_and_save(self, text_path: Path, table_path: Path) -> tuple:
        """Merge chunks and save to file"""
        merged_chunks = self.processor.merge_chunks(text_path, table_path)
        output_path = self.saver.save_merged_chunks(merged_chunks)
        return merged_chunks, output_path

    def _finalize_merge_stats(self, merged_chunks, output_path: Path) -> Dict:
        """Calculate and log merge statistics"""
        stats = self.statistics.get_merge_statistics(merged_chunks)
        stats['output_path'] = output_path
        self.statistics.log_merge_summary(stats, output_path, self.config.company_name)
        return stats

    def process_and_merge(self, text_chunks_path: Path = None,
                          table_chunks_path: Path = None) -> Dict:
        """Complete merge pipeline"""
        text_path, table_path = self._resolve_merge_paths(text_chunks_path, table_chunks_path)
        merged_chunks, output_path = self._merge_and_save(text_path, table_path)
        return self._finalize_merge_stats(merged_chunks, output_path)


# CLI Functions

def _create_cli_parser():
    """Create and configure argument parser"""
    import argparse
    parser = argparse.ArgumentParser(description="Merge text and table chunks")
    parser.add_argument('--company', type=str, required=True, help='Company name')
    parser.add_argument('--text-chunks', type=str, help='Path to text chunks JSON (optional, auto-detects)')
    parser.add_argument('--table-chunks', type=str, help='Path to table chunks JSON (optional, auto-detects)')
    parser.add_argument('--config', type=str, help='Path to config.yaml file (optional)')
    return parser

def _load_config_and_setup(args):
    """Load config and initialize merger"""
    config = load_config(args.config) if args.config else load_config()
    config.set_company(args.company)
    return ChunkMerger(config)

def _resolve_chunk_paths(args):
    """Resolve chunk paths from arguments"""
    text_path = Path(args.text_chunks) if args.text_chunks else None
    table_path = Path(args.table_chunks) if args.table_chunks else None
    return text_path, table_path

def main():
    """CLI entry point"""
    parser = _create_cli_parser()
    args = parser.parse_args()
    merger = _load_config_and_setup(args)
    text_path, table_path = _resolve_chunk_paths(args)
    merger.process_and_merge(text_path, table_path)
    merger.logger.info(f"✓ Merge complete for {merger.config.company_name}")


if __name__ == "__main__":
    main()
