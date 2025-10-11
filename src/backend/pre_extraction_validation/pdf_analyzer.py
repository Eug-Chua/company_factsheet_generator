"""
PDF Analyzer
Handles PDF text extraction, metadata extraction, and merged chunks loading
"""

import json
from pathlib import Path
from typing import Dict
import fitz  # PyMuPDF


class PDFAnalyzer:
    """Analyzes PDF documents and extracts text/metadata"""

    def __init__(self, logger, config):
        """Initialize PDF analyzer"""
        self.logger = logger
        self.config = config

    def _extract_pdf_text(self, doc) -> str:
        """Extract all text from PDF document"""
        pdf_text = ""
        for page in doc:
            pdf_text += page.get_text("text")
        return pdf_text

    def _build_metadata_dict(self, doc, pdf_path: Path, pdf_text: str) -> Dict:
        """Build metadata dictionary from PDF"""
        return {
            'page_count': len(doc),
            'file_size_mb': round(pdf_path.stat().st_size / (1024 * 1024), 2),
            'encrypted': doc.is_encrypted,
            'pdf_version': doc.metadata.get('format', 'Unknown'),
            'title': doc.metadata.get('title', ''),
            'pdf_char_count': len(pdf_text),
            'pdf_word_count': len(pdf_text.split())
        }

    def get_pdf_metadata(self, pdf_path: Path) -> Dict:
        """Extract metadata and text statistics from PDF"""
        doc = fitz.open(pdf_path)
        pdf_text = self._extract_pdf_text(doc)
        metadata = self._build_metadata_dict(doc, pdf_path, pdf_text)
        doc.close()
        return metadata

    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        doc = fitz.open(pdf_path)
        pdf_text = self._extract_pdf_text(doc)
        doc.close()
        return pdf_text

    def _get_merged_chunks_path(self) -> Path:
        """Get path to merged chunks file"""
        return self.config.output_dir / f"{self.config.company_name}_chunks_merged.json"

    def _check_merged_chunks_exist(self, merged_chunks_path: Path) -> bool:
        """Check if merged chunks file exists"""
        if not merged_chunks_path.exists():
            self.logger.warning(f"Merged chunks not found at {merged_chunks_path}, falling back to markdown only")
            return False
        return True

    def _read_chunks_from_file(self, merged_chunks_path: Path) -> list:
        """Read chunks from JSON file"""
        with open(merged_chunks_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _combine_chunk_content(self, chunks: list) -> str:
        """Combine all chunk content into single text"""
        return "\n\n".join(chunk['content'] for chunk in chunks)

    def _log_chunks_loaded(self, chunks: list, combined_text: str):
        """Log chunks loaded information"""
        self.logger.info(f"Loaded merged chunks: {len(chunks)} chunks ({len(combined_text):,} chars)")

    def load_merged_chunks(self) -> str:
        """Load and combine all merged chunks into single text for validation"""
        merged_chunks_path = self._get_merged_chunks_path()
        if not self._check_merged_chunks_exist(merged_chunks_path): return None
        chunks = self._read_chunks_from_file(merged_chunks_path)
        combined_text = self._combine_chunk_content(chunks)
        self._log_chunks_loaded(chunks, combined_text); return combined_text
