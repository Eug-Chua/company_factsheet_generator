import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))

from post_conversion_validation.conversion_validator import PDFExtractionValidator


class TestPDFExtractionValidator:
    """Essential tests for PDFExtractionValidator"""

    def test_init(self, mock_config):
        """Test initialization creates analyzers"""
        # ARRANGE & ACT
        validator = PDFExtractionValidator(mock_config)

        # ASSERT
        assert validator.pdf_analyzer is not None
        assert validator.keyword_analyzer is not None

    @patch('post_conversion_validation.conversion_validator.PDFAnalyzer')
    @patch('post_conversion_validation.conversion_validator.KeywordAnalyzer')
    def test_assess_quality_poor(
        self,
        mock_keyword_analyzer,
        mock_pdf_analyzer,
        mock_config
    ):
        """Test quality assessment: Poor"""
        # ARRANGE
        validator = PDFExtractionValidator(mock_config)

        extraction_metrics = {
            'char_extraction_rate': 40.0  # <50%
        }

        keyword_coverage = {
            'overall': {
                'coverage': 0.30,  # 30% (<50%)
                'total_found': 15,
                'total_keywords': 52
            }
        }

        # ACT
        result = validator._assess_quality(extraction_metrics, keyword_coverage)

        # ASSERT
        assert result['status'] == 'warning'