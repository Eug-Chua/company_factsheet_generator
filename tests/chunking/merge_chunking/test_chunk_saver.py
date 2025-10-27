import pytest
import json
from pathlib import Path
from unittest.mock import Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.joinpath("src", "backend")))

from chunking.merge_chunking.chunk_saver import ChunkSaver


class TestChunkSaver:
    """Tests for ChunkSaver"""

    def test_save_merged_chunks(self, mock_logger, mock_config, tmp_path):
        """Test saving merged chunks to JSON file"""
        # ARRANGE
        mock_config.output_dir = tmp_path
        mock_config.company_name = "test_company"

        saver = ChunkSaver(mock_logger, mock_config)

        chunks = [
            {"chunk_id": 0, "content": "Test chunk 1", "content_type": "text"},
            {"chunk_id": 1, "content": "Test chunk 2", "content_type": "table"}
        ]

        # ACT
        output_path = saver.save_merged_chunks(chunks)

        # ASSERT
        assert output_path.exists()
        assert output_path.name == "test_company_chunks_merged.json"

        # Verify content
        with open(output_path) as f:
            saved_chunks = json.load(f)

        assert len(saved_chunks) == 2
        assert saved_chunks[0]["chunk_id"] == 0
        assert saved_chunks[1]["content_type"] == "table"

    def test_save_merged_chunks_custom_path(self, mock_logger, mock_config, tmp_path):
        """Test saving chunks to a custom output path"""
        # ARRANGE
        saver = ChunkSaver(mock_logger, mock_config)
        chunks = [{"chunk_id": 0, "content": "Test"}]
        custom_path = tmp_path / "custom_output.json"

        # ACT
        output_path = saver.save_merged_chunks(chunks, custom_path)

        # ASSERT
        assert output_path == custom_path
        assert custom_path.exists()