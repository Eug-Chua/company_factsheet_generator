import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))

from conversion.markdown_converter import MarkdownConverter


class TestMarkdownConverter:
    """Essential tests for MarkdownConverter"""

    def test_init_creates_processors(self, mock_config, mock_logger):
        """Test that initialization creates text and table processors"""
        # ARRANGE
        mock_config.setup_logger.return_value = mock_logger

        # ACT
        converter = MarkdownConverter(mock_config)

        # ASSERT
        assert converter.text_processor is not None
        assert converter.table_processor is not None
        assert converter.table_converter is not None

    @patch('conversion.markdown_converter.TextProcessor')
    @patch('conversion.markdown_converter.DocumentConverter')
    def test_convert_pdf_creates_markdown_file(
        self,
        mock_doc_converter,  # DocumentConverter mock
        mock_text_processor, # TextProcessor mock
        mock_config,
        tmp_path
    ):
        """Test that PDF conversion creates a markdown file"""
        # ARRANGE
        mock_config.setup_logger.return_value = Mock()

        # Mock TextProcessor to return fake markdown
        mock_text_instance = Mock()
        mock_text_instance.extract_text.return_value = "# Test Document\n\nFake content."
        mock_text_processor.return_value = mock_text_instance

        # Mock DocumentConverter to return fake result with no tables
        mock_result = Mock()
        mock_result.document.tables = []  # No tables
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = mock_result
        mock_doc_converter.return_value = mock_converter_instance

        # Create fake PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")
        output_path = tmp_path / "output.md"

        # ACT
        converter = MarkdownConverter(mock_config)
        result = converter.convert_pdf_to_markdown(pdf_path, output_path)

        # ASSERT
        assert result == output_path
        assert output_path.exists(), "Markdown file should be created"

        # Check markdown content
        content = output_path.read_text()
        assert "# Test Document" in content
        assert "Fake content" in content

    def test_convert_pdf_raises_error_for_missing_file(self, mock_config):
        """Test that FileNotFoundError is raised for missing PDF"""
        # ARRANGE
        mock_config.setup_logger.return_value = Mock()
        converter = MarkdownConverter(mock_config)

        # ACT & ASSERT
        with pytest.raises(FileNotFoundError):
            converter.convert_pdf_to_markdown(
                pdf_path=Path("/this/file/does/not/exist.pdf"),
                output_path=Path("/tmp/output.md")
            )
