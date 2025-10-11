"""
Chunk Saver
Handles saving chunks to JSON files
"""

import json
from pathlib import Path
from typing import List, Dict


class ChunkSaver:
    """Saves chunks to JSON files"""

    def __init__(self, logger, config):
        """Initialize saver with logger and config"""
        self.logger = logger
        self.config = config

    def _get_default_merged_output_path(self) -> Path:
        """Get default output path for merged chunks"""
        return self.config.output_dir / f"{self.config.company_name}_chunks_merged.json"

    def _prepare_merged_output_path(self, output_path: Path = None) -> Path:
        """Prepare output path and create parent directories"""
        output_path = Path(output_path or self._get_default_merged_output_path())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def _write_merged_chunks(self, chunks: List[Dict], output_path: Path):
        """Write merged chunks to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

    def save_merged_chunks(self, chunks: List[Dict], output_path: Path = None) -> Path:
        """Save merged chunks to JSON"""
        output_path = self._prepare_merged_output_path(output_path)
        self._write_merged_chunks(chunks, output_path)
        self.logger.info(f"✓ Saved {len(chunks)} merged chunks to: {output_path}")
        return output_path
