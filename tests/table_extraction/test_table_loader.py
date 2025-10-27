import pytest
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.joinpath('src', 'backend')))

from table_extraction.table_loader import TableLoader

class TestTableLoader:
    """Tests for TableLoader"""

    def test_load_tables_from_file(self, mock_logger, mock_config, tmp_path):
        """Test loading tables from a JSON file"""
        # ARRANGE
        loader = TableLoader(mock_logger, mock_config)

        # Create a test tables JSON file
        tables_data = {
            "table_0": {
                "dataframe": [{"Col1": "val1", "Col2": "val2"}],
                "markdown": "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |",
                "shape": {"rows": 1, "columns": 2},
                "location": {"page": 1}
            },
            "table_1": {
                "dataframe": [{"Col1": "val3", "Col2": "val4"}],
                "markdown": "| Col1 | Col2 |\n|------|------|\n| val3 | val4 |",
                "shape": {"rows": 1, "columns": 2},
                "location": {"page": 2}
            }
        }

        tables_path = tmp_path / "test_tables.json"
        with open(tables_path, "w") as f:
            json.dump(tables_data, f)

        # ACT
        result = loader.load_tables(tables_path)

        # ASSERT
        assert len(result) == 2
        assert "table_0" in result
        assert "table_1" in result
        assert result["table_0"]["shape"]["rows"] == 1
        assert result["table_1"]["location"]["page"] == 2