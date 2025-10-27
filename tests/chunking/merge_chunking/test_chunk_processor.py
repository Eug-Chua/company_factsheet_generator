"""
Tests for chunk_processor.py
"""
import pytest
from pathlib import Path
from unittest.mock import Mock
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.joinpath("src", "backend")))

from chunking.merge_chunking.chunk_processor import ChunkProcessor
from chunking.merge_chunking.chunk_loader import ChunkLoader


class TestChunkProcessor:
    """Tests for ChunkProcessor"""

    def test_add_content_type_to_chunks(self, mock_logger):
        """Test adding content_type field to chunks"""
        # ARRANGE
        mock_loader = Mock()
        processor = ChunkProcessor(mock_logger, mock_loader)

        chunks = [
            {"chunk_id": 0, "content": "Test 1"},
            {"chunk_id": 1, "content": "Test 2"}
        ]

        # ACT
        processor._add_content_type_to_chunks(chunks, "text")

        # ASSERT
        assert chunks[0]["content_type"] == "text"
        assert chunks[1]["content_type"] == "text"

    def test_add_content_type_preserves_existing(self, mock_logger):
        """Test that existing content_type is preserved"""
        # ARRANGE
        mock_loader = Mock()
        processor = ChunkProcessor(mock_logger, mock_loader)

        chunks = [{"chunk_id": 0, "content": "Test", "content_type": "existing"}]

        # ACT
        processor._add_content_type_to_chunks(chunks, "text")

        # ASSERT
        assert chunks[0]["content_type"] == "existing"        