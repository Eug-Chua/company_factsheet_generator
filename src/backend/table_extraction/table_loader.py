"""
Table Loader
Handles loading and accessing table data from JSON files
"""

import json
from pathlib import Path
from typing import Dict, Optional


class TableLoader:
    """Loads and provides access to table data"""

    def __init__(self, logger, config):
        """Initialize table loader with logger and config"""
        self.logger = logger
        self.config = config
        self.tables_data = None
        self.tables_path = None

    def _auto_detect_tables_path(self) -> Path:
        """Auto-detect tables file based on markdown filename"""
        markdown_path = Path(self.config.markdown_path)
        return markdown_path.parent / f"{markdown_path.stem}_tables.json"

    def _load_tables_from_file(self, tables_path: Path):
        """Load tables JSON from file"""
        with open(tables_path, "r", encoding="utf-8") as f:
            self.tables_data = json.load(f)
        self.tables_path = tables_path

    def _resolve_tables_path(self, tables_path: Optional[Path]) -> Path:
        """Resolve tables path from input or auto-detect"""
        return Path(tables_path or self._auto_detect_tables_path())

    def _validate_tables_path_exists(self, tables_path: Path):
        """Validate that tables path exists"""
        if not tables_path.exists():
            raise FileNotFoundError(f"Tables file not found: {tables_path}")

    def load_tables(self, tables_path: Optional[Path] = None) -> Dict:
        """Load tables from JSON file"""
        tables_path = self._resolve_tables_path(tables_path)
        self._validate_tables_path_exists(tables_path)
        self.logger.info(f"Loading tables from: {tables_path}")
        self._load_tables_from_file(tables_path)
        self.logger.info(f"Loaded {len(self.tables_data)} tables")
        return self.tables_data

