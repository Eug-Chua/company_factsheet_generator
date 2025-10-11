"""
Markdown Extractor
Orchestrates extraction and chunking of markdown content for RAG processing
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from config_loader import load_config
from .markdown_cleaner import MarkdownCleaner
from .structure_analyzer import StructureAnalyzer
from .content_chunker import ContentChunker


class MarkdownExtractor:
    """Extracts and chunks markdown content with hierarchical structure"""

    def __init__(self, config=None):
        """Initialize extractor with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._load_chunking_params()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging for extraction process"""
        self.logger = self.config.setup_logger("extraction", __name__)

    def _load_chunking_params(self):
        """Load chunking parameters from config"""
        chunking_config = self.config.chunking_config
        self.min_chunk_size = chunking_config.get('min_chunk_size', 200)
        self.max_chunk_size = chunking_config.get('max_chunk_size', 2000)

    def _initialize_components(self):
        """Initialize cleaner, analyzer, and chunker components"""
        self.cleaner = MarkdownCleaner(self.logger)
        self.analyzer = StructureAnalyzer()
        self.chunker = ContentChunker(self.logger, self.min_chunk_size, self.max_chunk_size)

    def clean_markdown_artifacts(self, markdown_text: str) -> str:
        """Remove artifacts like '<!-- image -->' and normalize whitespace"""
        return self.cleaner.clean_markdown_artifacts(markdown_text)

    def _process_no_headers(self, markdown_text: str) -> List[Dict]:
        """Handle case where no headers are found"""
        self.logger.warning("No headers found, treating as single document")
        content_chunks = self.chunker.split_content(markdown_text)
        return self.chunker.create_chunks_from_content(content_chunks, 'Document', 0)

    def _has_valid_preamble(self, markdown_text: str, first_header_pos: int) -> bool:
        """Check if there's a valid preamble before first header"""
        return first_header_pos > 0 and len(markdown_text[:first_header_pos].strip()) >= self.min_chunk_size

    def _extract_preamble(self, markdown_text: str, first_header_pos: int, chunk_id: int) -> tuple[List[Dict], int]:
        """Extract preamble content before first header"""
        if not self._has_valid_preamble(markdown_text, first_header_pos): return [], chunk_id
        preamble = markdown_text[:first_header_pos].strip()
        chunk = self.chunker.create_chunk(chunk_id, 'Preamble', 0, preamble)
        return ([chunk], chunk_id + 1) if chunk else ([], chunk_id)

    def _log_section_processing(self, hierarchical_path: str, level: int):
        """Log section processing"""
        self.logger.debug(f"Processing: {hierarchical_path} (Level {level})")

    def _process_section(self, headers: List[Dict], index: int, content: str, chunk_id: int) -> tuple[List[Dict], int]:
        """Process a single section and create chunks"""
        hierarchical_path = self.analyzer.build_header_stack(headers, index)
        self._log_section_processing(hierarchical_path, headers[index]['level'])
        content_chunks = self.chunker.split_content(content)
        section_chunks = self.chunker.create_chunks_from_content(content_chunks, hierarchical_path, headers[index]['level'], chunk_id)
        return section_chunks, chunk_id + len(section_chunks)

    def _process_all_sections(self, markdown_text: str, headers: List[Dict], chunk_id: int) -> tuple[List[Dict], int]:
        """Process all sections and return chunks"""
        chunks = []
        for i in range(len(headers)):
            content = self.analyzer.get_section_content(markdown_text, headers, i)
            if content and len(content) >= self.min_chunk_size:
                section_chunks, chunk_id = self._process_section(headers, i, content, chunk_id)
                chunks.extend(section_chunks)
        return chunks, chunk_id

    def extract_hierarchical_chunks(self, markdown_text: str) -> List[Dict]:
        """Extract chunks with full hierarchical structure preservation"""
        self.logger.info("Extracting hierarchical chunks...")
        headers = self.analyzer.find_headers(markdown_text)
        if not headers: return self._process_no_headers(markdown_text)
        preamble_chunks, chunk_id = self._extract_preamble(markdown_text, headers[0]['start_pos'], 0)
        section_chunks, _ = self._process_all_sections(markdown_text, headers, chunk_id)
        chunks = preamble_chunks + section_chunks
        self.logger.info(f"Extracted {len(chunks)} chunks with hierarchical structure"); return chunks

    def _prepare_output_path(self, output_path: Optional[Path]) -> Path:
        """Prepare output path for saving"""
        output_path = Path(output_path or self.config.chunks_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def save_chunks(self, chunks: List[Dict], output_path: Optional[Path] = None) -> Path:
        """Save chunks to JSON file"""
        output_path = self._prepare_output_path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        self.logger.info(f"✓ Saved {len(chunks)} chunks to: {output_path}"); return output_path

    def _read_markdown_file(self, markdown_path: Path) -> str:
        """Read markdown file and return content"""
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        with open(markdown_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _create_semantic_chunker(self):
        """Create semantic chunker with config"""
        from semantic_chunker import SemanticChunker
        semantic_config = self.config.config.get('semantic_chunking', {})
        return SemanticChunker(config=self.config,
                              similarity_threshold=semantic_config.get('similarity_threshold', 0.70),
                              max_merged_size=semantic_config.get('max_merged_size', 3000))

    def _apply_semantic_merging(self, chunks: List[Dict]) -> List[Dict]:
        """Apply semantic merging to chunks"""
        chunker = self._create_semantic_chunker()
        return chunker.merge_similar_chunks(chunks)

    def _calculate_avg_chunk_size(self, chunks: List[Dict]) -> float:
        """Calculate average chunk size"""
        return sum(len(c['content']) for c in chunks) / len(chunks) if chunks else 0

    def _log_extraction_summary(self, chunks: List[Dict], chunks_path: Path):
        """Log extraction summary"""
        avg_size = self._calculate_avg_chunk_size(chunks)
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"Extraction Summary for {self.config.company_name}")
        self.logger.info(f"{'=' * 60}")
        self.logger.info(f"  Total chunks: {len(chunks)}")
        self.logger.info(f"  Average chunk size: {avg_size:.0f} characters")
        self.logger.info(f"  Chunks file: {chunks_path}")
        self.logger.info(f"{'=' * 60}\n")

    def _resolve_markdown_path(self, markdown_path: Optional[Path]) -> Path:
        """Resolve markdown path from argument or config"""
        return Path(markdown_path or self.config.markdown_path)

    def _read_and_log_markdown(self, markdown_path: Path) -> str:
        """Read markdown file and log"""
        self.logger.info(f"Processing: {markdown_path}")
        markdown_text = self._read_markdown_file(markdown_path)
        self.logger.info(f"Read {len(markdown_text)} characters"); return markdown_text

    def _apply_semantic_if_needed(self, chunks: List[Dict], use_semantic_merging: bool) -> List[Dict]:
        """Apply semantic merging if requested"""
        if use_semantic_merging:
            self.logger.info("Applying semantic merging...")
            return self._apply_semantic_merging(chunks)
        return chunks

    def _build_result_dict(self, chunks_path: Path, chunks: List[Dict]) -> Dict:
        """Build result dictionary"""
        return {'chunks_path': chunks_path, 'num_chunks': len(chunks),
                'avg_chunk_size': self._calculate_avg_chunk_size(chunks)}

    def process_markdown_file(self, markdown_path: Optional[Path] = None, use_semantic_merging: bool = False) -> Dict:
        """Complete pipeline: read markdown, extract chunks, save outputs"""
        markdown_path = self._resolve_markdown_path(markdown_path)
        markdown_text = self._read_and_log_markdown(markdown_path)
        cleaned_text = self.clean_markdown_artifacts(markdown_text)
        chunks = self.extract_hierarchical_chunks(cleaned_text)
        chunks = self._apply_semantic_if_needed(chunks, use_semantic_merging)
        chunks_path = self.save_chunks(chunks)
        self._log_extraction_summary(chunks, chunks_path)
        return self._build_result_dict(chunks_path, chunks)


# CLI Functions

def _create_cli_parser():
    """Create argument parser for CLI"""
    import argparse
    parser = argparse.ArgumentParser(description="Extract and chunk markdown files")
    parser.add_argument('--company', type=str,
                       help='Company to process. If not specified, uses config default.')
    parser.add_argument('--markdown', type=str,
                       help='Path to markdown file (optional)')
    parser.add_argument('--config', type=str,
                       help='Path to config.yaml file (optional)')
    parser.add_argument('--semantic', action='store_true',
                       help='Apply semantic merging after extraction')
    return parser

def _load_and_configure_config(args):
    """Load config and set company if specified"""
    config = load_config(args.config) if args.config else load_config()
    if args.company: config.set_company(args.company)
    return config

def _get_markdown_path(args):
    """Get markdown path from args"""
    return Path(args.markdown) if args.markdown else None

def _run_extraction(config, args):
    """Run extraction and log completion"""
    extractor = MarkdownExtractor(config)
    markdown_path = _get_markdown_path(args)
    extractor.process_markdown_file(markdown_path, use_semantic_merging=args.semantic)
    extractor.logger.info(f"✓ Extraction complete for {config.company_name}")

def main():
    """CLI entry point"""
    parser = _create_cli_parser()
    args = parser.parse_args()
    config = _load_and_configure_config(args)
    _run_extraction(config, args)


if __name__ == "__main__":
    main()
