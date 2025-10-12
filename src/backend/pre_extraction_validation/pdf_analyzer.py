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

    def _get_tables_path(self) -> Path:
        """Get path to tables JSON file from markdown converter"""
        markdown_path = self.config.markdown_path
        return markdown_path.parent / f"{markdown_path.stem}_tables.json"

    def _check_tables_exist(self, tables_path: Path) -> bool:
        """Check if tables JSON file exists"""
        if not tables_path.exists():
            self.logger.info(f"No tables file found at {tables_path}")
            return False
        return True

    def _read_tables_from_file(self, tables_path: Path) -> dict:
        """Read tables from JSON file (returns dict with table_0, table_1, etc.)"""
        with open(tables_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract_table_text(self, table: dict) -> str:
        """Extract text content from a single table"""
        # Tables have 'markdown' or 'csv' representations
        if 'markdown' in table and table['markdown']:
            return table['markdown']
        elif 'csv' in table and table['csv']:
            return table['csv']
        return ""

    def _combine_table_content(self, tables_dict: dict) -> str:
        """Combine all table content into single text"""
        table_texts = []
        for table_id, table_data in tables_dict.items():
            text = self._extract_table_text(table_data)
            if text:
                table_texts.append(text)
        return "\n\n".join(table_texts)

    def _log_tables_loaded(self, num_tables: int, table_text: str):
        """Log tables loaded information"""
        self.logger.info(f"Loaded tables: {num_tables} tables ({len(table_text):,} chars)")

    def load_merged_chunks(self) -> str:
        """Load markdown and tables for validation (used at Step 2)"""
        tables_path = self._get_tables_path()
        if not self._check_tables_exist(tables_path):
            self.logger.info("No tables to include in validation")
            return None
        tables_dict = self._read_tables_from_file(tables_path)
        if not tables_dict:
            self.logger.info("Tables file is empty")
            return None
        table_text = self._combine_table_content(tables_dict)
        self._log_tables_loaded(len(tables_dict), table_text)
        return table_text
