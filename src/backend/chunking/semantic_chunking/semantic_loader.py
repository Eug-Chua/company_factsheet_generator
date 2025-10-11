"""
Semantic Loader
Handles loading and saving chunks for semantic processing
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class SemanticLoader:
    """Loads and saves chunks for semantic processing"""

    def __init__(self, logger, config, table_detector):
        """Initialize loader with logger, config, and table detector"""
        self.logger = logger
        self.config = config
        self.table_detector = table_detector

    def _read_chunks_json(self, chunks_path: Path) -> List[Dict]:
        """Read chunks from JSON file"""
        with open(chunks_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_primary_tables_path(self, chunks_path: Path) -> Path:
        """Get primary table data file path"""
        return chunks_path.parent.parent / "markdown_files" / f"{self.config.company_name}_tables.json"

    def _get_alternate_tables_path(self, chunks_path: Path) -> Path:
        """Get alternate table data file path"""
        return chunks_path.parent / f"{chunks_path.stem.replace('_chunks', '')}_tables.json"

    def _read_table_data_file(self, tables_path: Path) -> Optional[Dict]:
        """Read table data from file if it exists"""
        if tables_path.exists():
            self.logger.info(f"Loading table data from {tables_path}")
            with open(tables_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _load_table_data(self, chunks_path: Path) -> Optional[Dict]:
        """Load table data from companion _tables.json file"""
        tables_path = self._get_primary_tables_path(chunks_path)
        table_data = self._read_table_data_file(tables_path)
        if table_data is None:
            table_data = self._read_table_data_file(self._get_alternate_tables_path(chunks_path))
        if table_data is None:
            self.logger.info("No table data file found")
        return table_data

    def load_chunks_file(self, chunks_path: Path) -> List[Dict]:
        """Load chunks from JSON file"""
        self.logger.info(f"Loading chunks from {chunks_path}")
        chunks = self._read_chunks_json(chunks_path)
        self.logger.info(f"Loaded {len(chunks)} basic chunks")
        table_data = self._load_table_data(chunks_path)
        return self.table_detector.annotate_chunks_with_table_info(chunks, table_data)

    def _get_output_path(self, chunks_path: Path) -> Path:
        """Get output path for semantic chunks"""
        return chunks_path.parent / f"{chunks_path.stem}_semantic.json"

    def _write_chunks_json(self, merged_chunks: List[Dict], output_path: Path):
        """Write chunks to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_chunks, f, indent=2, ensure_ascii=False)

    def save_merged_chunks(self, merged_chunks: List[Dict], chunks_path: Path) -> Path:
        """Save merged chunks to file"""
        output_path = self._get_output_path(chunks_path)
        self._write_chunks_json(merged_chunks, output_path)
        self.logger.info(f"Saved {len(merged_chunks)} semantic chunks to: {output_path}")
        return output_path
