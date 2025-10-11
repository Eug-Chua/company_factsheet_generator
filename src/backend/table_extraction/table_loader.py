"""
Table Loader
Handles loading and accessing table data from JSON files
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import pandas as pd


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
        with open(tables_path, 'r', encoding='utf-8') as f:
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

    def _create_table_metadata(self, table_id: str, table_info: Dict) -> Dict:
        """Create metadata dict for a table"""
        return {'table_id': table_id, 'rows': table_info['shape']['rows'],
                'columns': table_info['shape']['columns'],
                'page': table_info['location'].get('page')}

    def get_table_list(self) -> List[Dict[str, Any]]:
        """Get list of all tables with metadata"""
        if not self.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")
        return [self._create_table_metadata(tid, tinfo)
                for tid, tinfo in self.tables_data.items()]

    def get_table_by_id(self, table_id: str) -> Optional[pd.DataFrame]:
        """Get table as DataFrame by ID"""
        if not self.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")
        if table_id not in self.tables_data:
            self.logger.warning(f"Table {table_id} not found")
            return None
        table_data = self.tables_data[table_id]['dataframe']
        return pd.DataFrame(table_data)

    def get_table_markdown(self, table_id: str) -> Optional[str]:
        """Get table as markdown string"""
        if not self.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")
        if table_id not in self.tables_data:
            return None
        return self.tables_data[table_id]['markdown']

    def _format_table_summary_line(self, table_id: str, table_info: Dict) -> str:
        """Format a single table summary line"""
        shape = table_info['shape']
        page = table_info['location'].get('page', 'unknown')
        return f"  {table_id}: {shape['rows']} rows × {shape['columns']} cols (page {page})"

    def _build_summary_lines(self) -> List[str]:
        """Build list of summary lines for all tables"""
        summary = [f"Loaded {len(self.tables_data)} tables:\n"]
        for table_id, table_info in self.tables_data.items():
            summary.append(self._format_table_summary_line(table_id, table_info))
        return summary

    def get_table_summary(self) -> str:
        """Get a summary of all loaded tables"""
        if not self.tables_data:
            return "No tables loaded"
        return "\n".join(self._build_summary_lines())

    def _get_default_export_dir(self) -> Path:
        """Get default export directory"""
        return self.tables_path.parent / "extracted_tables"

    def _resolve_export_dir(self, output_dir: Optional[Path]) -> Path:
        """Resolve and create export directory"""
        output_dir = Path(output_dir or self._get_default_export_dir())
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _export_single_table_csv(self, table_id: str, table_info: Dict, output_dir: Path):
        """Export a single table to CSV file"""
        csv_path = output_dir / f"{table_id}.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(table_info['csv'])

    def _export_all_table_files(self, output_dir: Path):
        """Export all table data to CSV files"""
        for table_id, table_info in self.tables_data.items():
            self._export_single_table_csv(table_id, table_info, output_dir)

    def export_all_tables_to_csv(self, output_dir: Optional[Path] = None):
        """Export all tables to CSV files"""
        if not self.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")
        output_dir = self._resolve_export_dir(output_dir)
        self.logger.info(f"Exporting {len(self.tables_data)} tables to {output_dir}")
        self._export_all_table_files(output_dir)
        self.logger.info(f"✓ Exported all tables to {output_dir}")
        return output_dir
