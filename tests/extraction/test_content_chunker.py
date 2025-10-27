import pytest
from pathlib import Path
from unittest.mock import Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))

from extraction.content_chunker import ContentChunker

class TestContentChunker:
    """Tests for ContentChunker"""

    def test_split_content_by_paragraphs(self, mock_logger):
        """Test splitting content by paragraph breaks"""

        # arrange
        chunker = ContentChunker(mock_logger, min_chunk_size=10, max_chunk_size=50)
        content = "Revenue was USD100mn in the fiscal year 2024. Net income was up 10% year on year. \n\n Debt increased 5% to USD3mn, of which, USD1mn matures in the next 12 months."

        # act
        result = chunker.split_content(content)

        # assert
        assert result[0] == "Revenue was USD100mn in the fiscal year 2024. Net income was up 10% year on year."
        assert result[1] == "Debt increased 5% to USD3mn, of which, USD1mn matures in the next 12 months."

    def test_create_chunk(self, mock_logger):
        """Test creating a single chunk with metadata"""
        # arrange
        chunker = ContentChunker(mock_logger, min_chunk_size=100, max_chunk_size=1000)
        chunk_id = 5
        section_header = "Financial Performance"
        header_level = 2
        content = "Revenue increased by 15% to $5.2 billion in 2024, driven by strong performance across all business segments and favorable market conditions throughout the year."

        # act
        result = chunker.create_chunk(chunk_id, section_header, header_level, content)

        # assert
        assert result['chunk_id'] == 5
        assert result['section_header'] == "Financial Performance"
        assert result['header_level'] == 2
        assert result['content'] == content
    