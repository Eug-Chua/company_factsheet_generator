"""
Tests for pdf_analyzer.py
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))

from post_conversion_validation.pdf_analyzer import PDFAnalyzer


class TestPDFAnalyzer:
    """Tests for PDFAnalyzer"""

    def test_init(self, mock_logger, mock_config):
        """Test initialization"""
        analyzer = PDFAnalyzer(mock_logger, mock_config)

        assert analyzer.logger == mock_logger
        assert analyzer.config == mock_config

    @patch('fitz.open')
    def test_extract_pdf_text(self, mock_fitz_open, mock_logger, mock_config, tmp_path):
        """Test PDF text extraction with mocked PyMuPDF"""
        # ARRANGE
        # Create mock PDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2  # 2 pages

        # Create mock pages
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content\n"

        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content\n"

        mock_doc.__iter__.return_value = [mock_page1, mock_page2]
        mock_fitz_open.return_value = mock_doc

        # Create fake PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        analyzer = PDFAnalyzer(mock_logger, mock_config)

        # ACT
        result = analyzer.extract_pdf_text(pdf_path)

        # ASSERT
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        mock_fitz_open.assert_called_once_with(pdf_path)
        mock_doc.close.assert_called_once()

    def test_load_merged_chunks_with_tables(self, mock_logger, mock_config, tmp_path):
        """Test loading and merging table chunks"""
        # ARRANGE
        # Create fake tables JSON
        tables_data = {
            "table_0": {
                "markdown": "| Col1 | Col2 |\n|------|------|\n| A    | B    |"
            },
            "table_1": {
                "markdown": "| X | Y |\n|---|---|\n| 1 | 2 |"
            }
        }

        tables_path = tmp_path / "test_tables.json"
        with open(tables_path, 'w') as f:
            json.dump(tables_data, f)

        # Mock config to return our test path
        mock_config.markdown_path = tmp_path / "test.md"

        analyzer = PDFAnalyzer(mock_logger, mock_config)

        # ACT
        result = analyzer.load_merged_chunks()

        # ASSERT
        assert "Col1" in result
        assert "Col2" in result
        assert len(result) > 0

    def test_load_merged_chunks_no_tables(self, mock_logger, mock_config, tmp_path):
        """Test loading when tables file doesn't exist"""
        # ARRANGE
        mock_config.markdown_path = tmp_path / "test.md"
        analyzer = PDFAnalyzer(mock_logger, mock_config)

        # ACT
        result = analyzer.load_merged_chunks()

        # ASSERT
        assert result == None