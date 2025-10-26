"""
Tests for keyword_analyzer.py
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))

from post_conversion_validation.keyword_analyzer import KeywordAnalyzer


class TestKeywordAnalyzer:
    """Tests for KeywordAnalyzer"""

    def test_check_keyword_presence(self):
        """Test keyword detection"""
        # ARRANGE
        analyzer = KeywordAnalyzer()

        # Text with many financial keywords
        text = """
        Annual Report 2024

        Income Statement
        Revenue: $5.2 billion
        Net Income: $780 million
        EBITDA: $1.1 billion

        Balance Sheet
        Total Assets: $12 billion
        Total Liabilities: $6 billion
        Shareholder Equity: $6 billion

        Cash Flow Statement
        Operating Cash Flow: $900 million

        Risk Factors
        Material risks include credit risk, market risk, and operational risk.

        Corporate Governance
        Board of Directors oversees the audit committee and remuneration committee.
        """

        # ACT
        result = analyzer.check_keyword_presence(text)

        # ASSERT
        assert 'overall' in result
        assert result['overall']['coverage'] > 0.3
        assert result['overall']['total_found'] > 10  

    def test_check_keyword_presence_case_insensitive(self):
        """Test that keyword matching is case-insensitive"""
        # ARRANGE
        analyzer = KeywordAnalyzer()

        # Mixed case keywords
        text = "REVENUE and Net Income and balance sheet"

        # ACT
        result = analyzer.check_keyword_presence(text)

        # ASSERT
        # Should find: revenue, net income, balance sheet (3 keywords)
        assert result['overall']['total_found'] >= 3