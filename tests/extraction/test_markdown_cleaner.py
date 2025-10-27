import pytest
from pathlib import Path
from unittest.mock import Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath('src', 'backend')))

from extraction.markdown_cleaner import MarkdownCleaner

class TestMarkdownCleaner:
    """Tests for markdown cleaner"""

    def test_remove_image_comments(self, mock_logger):
        """Test removal of image tags"""
        # Arrange
        cleaner = MarkdownCleaner(mock_logger)
        text = "# Header<!-- image -->\n\nContent with <!-- image --> markers."
        
        # Act
        result = cleaner.clean_markdown_artifacts(text)

        # Assert
        assert '<!-- image -->' not in result
        assert '# Header' in result
        assert 'Content with' in result

    def test_normalize_whitespace(self, mock_logger):
        """Test normalization of extra whitespace"""
        # Arrange
        cleaner = MarkdownCleaner(mock_logger)
        text = "Line 1\n\nLine 2"

        # Act
        result = cleaner.clean_markdown_artifacts(text)

        # Assert
        assert '\n\n' not in result
        assert "Line 1" in result