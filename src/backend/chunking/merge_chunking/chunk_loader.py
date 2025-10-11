"""
Chunk Loader
Handles loading chunks from JSON files
"""

import json
from pathlib import Path
from typing import List, Dict


class ChunkLoader:
    """Loads chunks from JSON files"""

    def __init__(self, logger):
        """Initialize loader with logger"""
        self.logger = logger

    def _validate_chunks_path(self, chunks_path: Path):
        """Validate chunks path exists"""
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    def _read_chunks_from_file(self, chunks_path: Path) -> List[Dict]:
        """Read chunks from JSON file"""
        with open(chunks_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_chunks(self, chunks_path: Path) -> List[Dict]:
        """Load chunks from JSON file"""
        self._validate_chunks_path(chunks_path)
        chunks = self._read_chunks_from_file(chunks_path)
        self.logger.info(f"Loaded {len(chunks)} chunks from {chunks_path.name}")
        return chunks
