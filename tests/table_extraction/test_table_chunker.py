import pytest
from pathlib import Path
from unittest.mock import Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))

from table_extraction.table_chunker import TableChunker


class TestTableChunker:
    """Tests for TableChunker"""

    def test_split_header_from_data(self, mock_logger, mock_config):
        """Test splitting table into header and data rows"""
        # ARRANGE
        mock_loader = Mock()
        chunker = TableChunker(mock_logger, mock_config, mock_loader)
        markdown = "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |\n| val3 | val4 |"

        # ACT
        header, data_rows = chunker._split_header_from_data(markdown)

        # ASSERT
        assert "| Col1 | Col2 |" in header
        assert "|------|------|" in header
        assert len(data_rows) == 2
        assert data_rows[0] == "| val1 | val2 |"
        assert data_rows[1] == "| val3 | val4 |"

    def test_process_small_table_single_chunk(self, mock_logger, mock_config):
        """Test processing a small table that fits in one chunk"""
        # ARRANGE
        mock_loader = Mock()
        chunker = TableChunker(mock_logger, mock_config, mock_loader)
        chunks = []

        table_info = {
            "markdown": "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |",
            "shape": {"rows": 1, "columns": 2},
            "location": {"page": 1}
        }

        # ACT
        chunker._process_single_table_to_chunks(0, table_info, chunks, max_chunk_size=2000)

        # ASSERT
        assert len(chunks) == 1
        assert chunks[0]["section_header"] == "Table 1 (Page 1): 1×2"
        assert "| Col1 | Col2 |" in chunks[0]["content"]

    def test_create_table_chunks_from_multiple_tables(self, mock_logger, mock_config):
        """Test creating chunks from multiple tables"""
        # ARRANGE
        mock_loader = Mock()
        mock_loader.tables_data = {
            "table_0": {
                "markdown": "| A |\n|---|\n| 1 |",
                "shape": {"rows": 1, "columns": 1},
                "location": {"page": 1}
            },
            "table_1": {
                "markdown": "| B |\n|---|\n| 2 |",
                "shape": {"rows": 1, "columns": 1},
                "location": {"page": 2}
            }
        }
        chunker = TableChunker(mock_logger, mock_config, mock_loader)

        # ACT
        chunks = chunker.create_table_chunks()

        # ASSERT
        assert len(chunks) == 2
        assert chunks[0]["chunk_id"] == 0
        assert chunks[1]["chunk_id"] == 1
        assert "Table 1 (Page 1)" in chunks[0]["section_header"]
        assert "Table 2 (Page 2)" in chunks[1]["section_header"]