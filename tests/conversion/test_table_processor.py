"""
Tests for table_processor.py    
"""
import pytest
import pandas as pd
from unittest.mock import Mock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath("src", "backend")))
from conversion.table_processor import TableProcessor

class TestTableProcessor:
    """Tests for TableProcessor"""

    def test_fix_duplicate_columns_no_duplicates(self):
        """Test that columns without duplicates remain unchanged"""
        mock_logger = Mock()
        processor = TableProcessor(mock_logger)
        
        df = pd.DataFrame({
            'Property, plant and equipment': ['US$50,000', 'US$220,000'],
            'Intangible assets': ['US$100,000', 'US$500,000'],
            'Investment properties': ['US$200,000', 'US$600,000']
        })

        result = processor._fix_duplicate_columns(df)
        expected_columns = ['Property, plant and equipment',
                            'Intangible assets',
                            'Investment properties']
        
        assert list(result.columns) == expected_columns

    def test_fix_duplicate_columns_with_duplicates(self):
        """Test that duplicate columns get renamed with suffixes"""
        mock_logger = Mock()
        processor = TableProcessor(mock_logger)

        df = pd.DataFrame([['US$100,000', 'US$500,000', 'US$100,000']],
                          columns=['Intangible assets','Intangible assets','Intangible assets'])
        
        result = processor._fix_duplicate_columns(df)

        expected_columns = ['Intangible assets',
                            'Intangible assets_1',
                            'Intangible assets_2']
        
        assert list(result.columns) == expected_columns
 
    def test_extract_page_number_with_page_attribute(self):
        """Test page number extraction when prov has 'page' attribute"""
        mock_logger = Mock()
        processor = TableProcessor(mock_logger)

        mock_table = Mock()
        mock_prov = Mock()
        mock_prov.page = 150
        mock_table.prov = [mock_prov]

        result = processor._extract_page_number(mock_table)

        assert result == 150