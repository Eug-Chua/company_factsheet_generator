import pytest
import json
from pathlib import Path
from unittest.mock import Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.joinpath("src", "backend")))

from chunking.merge_chunking.chunk_loader import ChunkLoader


class TestChunkLoader:
    """Tests for ChunkLoader"""

    def test_load_chunks_from_valid_file(self, mock_logger, tmp_path):
        """Test loading chunks from a valid JSON file"""
        # ARRANGE
        loader = ChunkLoader(mock_logger)

        chunks_data = [
            {"chunk_id": 0, "content": "Test chunk 1", "section_header": "Header 1"},
            {"chunk_id": 1, "content": "Test chunk 2", "section_header": "Header 2"}
        ]

        chunks_path = tmp_path / "test_chunks.json"
        with open(chunks_path, "w") as f:
            json.dump(chunks_data, f)

        # ACT
        result = loader.load_chunks(chunks_path)

        # ASSERT
        assert len(result) == 2
        assert result[0]["chunk_id"] == 0
        assert result[1]["content"] == "Test chunk 2"