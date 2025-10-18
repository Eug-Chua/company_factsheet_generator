"""
Table Searcher
Handles searching tables and extracting numerical data
"""

import re
from typing import List, Dict, Optional, Any
import pandas as pd


class TableSearcher:
    """Searches tables and extracts numerical values"""

    def __init__(self, logger, table_loader):
        """Initialize searcher with logger and table loader"""
        self.logger = logger
        self.table_loader = table_loader

    def _keyword_matches_table(
        self, df_str: str, keyword: str, case_sensitive: bool
    ) -> bool:
        """Check if keyword matches in table string"""
        if case_sensitive:
            return keyword in df_str
        return keyword.lower() in df_str.lower()

    def _create_table_match_result(
        self, table_id: str, table_info: Dict, df: pd.DataFrame
    ) -> Dict:
        """Create result dictionary for matching table"""
        return {
            "table_id": table_id,
            "page": table_info["location"].get("page"),
            "shape": table_info["shape"],
            "dataframe": df,
        }

    def _search_single_table(
        self, table_id: str, table_info: Dict, keyword: str, case_sensitive: bool
    ) -> Optional[Dict]:
        """Search a single table for keyword"""
        df = pd.DataFrame(table_info["dataframe"])
        df_str = df.to_string()
        if self._keyword_matches_table(df_str, keyword, case_sensitive):
            return self._create_table_match_result(table_id, table_info, df)
        return None

    def _validate_tables_loaded(self):
        """Validate that tables are loaded"""
        if not self.table_loader.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")

    def _search_all_tables(self, keyword: str, case_sensitive: bool) -> List[Dict]:
        """Search all tables for keyword matches"""
        return [
            result
            for table_id, table_info in self.table_loader.tables_data.items()
            if (
                result := self._search_single_table(
                    table_id, table_info, keyword, case_sensitive
                )
            )
        ]

    def search_tables_by_keyword(
        self, keyword: str, case_sensitive=False
    ) -> List[Dict]:
        """Search for tables containing a keyword"""
        self._validate_tables_loaded()
        matching_tables = self._search_all_tables(keyword, case_sensitive)
        self.logger.info(f"Found {len(matching_tables)} tables matching '{keyword}'")
        return matching_tables

    def _find_matching_rows(self, df: pd.DataFrame, row_keyword: str) -> pd.DataFrame:
        """Find rows containing keyword"""
        row_mask = df.astype(str).apply(
            lambda row: row.str.contains(row_keyword, case=False, na=False).any(),
            axis=1,
        )
        return df[row_mask]

    def _find_column_by_keyword(
        self, df: pd.DataFrame, col_keyword: str
    ) -> Optional[str]:
        """Find column name matching keyword"""
        col_matches = [
            col for col in df.columns if col_keyword.lower() in str(col).lower()
        ]
        return col_matches[0] if col_matches else None

    def _extract_first_numeric_value(
        self, row: pd.Series, df: pd.DataFrame
    ) -> Optional[Any]:
        """Extract first numeric value from row"""
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            return row[numeric_cols[0]]
        return self._extract_first_number_from_strings(row)

    def _extract_first_number_from_strings(self, row: pd.Series) -> Optional[str]:
        """Extract first number found in row string values"""
        for val in row:
            numbers = re.findall(r"-?\d+[,.\d]*", str(val))
            if numbers:
                return numbers[0]
        return None

    def _get_value_by_column(
        self, row: pd.Series, df: pd.DataFrame, col_keyword: Optional[str]
    ) -> Optional[Any]:
        """Get value from row by column keyword or first numeric"""
        if col_keyword:
            col_name = self._find_column_by_keyword(df, col_keyword)
            if not col_name:
                self.logger.warning(f"No columns found matching '{col_keyword}'")
                return None
            return row[col_name]
        return self._extract_first_numeric_value(row, df)

    def _get_and_validate_dataframe(self, table_id: str) -> Optional[pd.DataFrame]:
        """Get dataframe and check if valid"""
        df = self.table_loader.get_table_by_id(table_id)
        return df if df is not None and not df.empty else None

    def _find_and_validate_rows(
        self, df: pd.DataFrame, row_keyword: str, table_id: str
    ) -> Optional[pd.DataFrame]:
        """Find matching rows and validate result"""
        matching_rows = self._find_matching_rows(df, row_keyword)
        if matching_rows.empty:
            self.logger.warning(f"No rows found matching '{row_keyword}' in {table_id}")
            return None
        return matching_rows

    def extract_numerical_value(
        self, table_id: str, row_keyword: str, col_keyword: Optional[str] = None
    ) -> Optional[Any]:
        """Extract a specific numerical value from a table"""
        df = self._get_and_validate_dataframe(table_id)
        if df is None:
            return None
        matching_rows = self._find_and_validate_rows(df, row_keyword, table_id)
        if matching_rows is None:
            return None
        return self._get_value_by_column(matching_rows.iloc[0], df, col_keyword)

    def _extract_number_from_cell(self, cell_value: Any) -> Optional[str]:
        """Extract numerical value from cell"""
        if pd.isna(cell_value):
            return None
        if isinstance(cell_value, (int, float)):
            return str(cell_value)
        cell_str = str(cell_value)
        numbers = re.findall(r"-?\d+[,.\d]*", cell_str)
        if numbers:
            return numbers[0]
        return None

    def _find_numeric_in_adjacent_cells(
        self, row: pd.Series, col_name: str
    ) -> Optional[str]:
        """Find numeric value in adjacent cells of same row"""
        for other_col, other_val in row.items():
            if other_col != col_name:
                numeric_value = self._extract_number_from_cell(other_val)
                if numeric_value:
                    return numeric_value
        return None

    def _create_metric_match_result(
        self,
        table_id: str,
        table_info: Dict,
        row_idx,
        col_name: str,
        cell_str: str,
        numeric_value,
    ) -> Dict:
        """Create result dictionary for metric match"""
        return {
            "table_id": table_id,
            "page": table_info["location"].get("page"),
            "row_index": row_idx,
            "column": col_name,
            "context": cell_str,
            "value": numeric_value,
        }

    def _process_metric_cell(
        self,
        keyword: str,
        cell_value: Any,
        row: pd.Series,
        col_name: str,
        row_idx,
        table_id: str,
        table_info: Dict,
    ) -> Optional[Dict]:
        """Process a single cell for keyword match"""
        cell_str = str(cell_value).lower()
        if keyword.lower() not in cell_str:
            return None
        numeric_value = self._extract_number_from_cell(cell_value)
        if not numeric_value:
            numeric_value = self._find_numeric_in_adjacent_cells(row, col_name)
        return self._create_metric_match_result(
            table_id, table_info, row_idx, col_name, cell_str, numeric_value
        )

    def _extract_metrics_from_table(
        self, table_id: str, table_info: Dict, metric_keywords: List[str], results: Dict
    ):
        """Extract metrics from a single table"""
        df = pd.DataFrame(table_info["dataframe"])
        for keyword in metric_keywords:
            for row_idx, row in df.iterrows():
                for col_name, cell_value in row.items():
                    match = self._process_metric_cell(
                        keyword,
                        cell_value,
                        row,
                        col_name,
                        row_idx,
                        table_id,
                        table_info,
                    )
                    if match:
                        results[keyword].append(match)

    def _log_metrics_summary(self, results: Dict):
        """Log summary of extracted metrics"""
        for keyword, matches in results.items():
            self.logger.info(f"Found {len(matches)} occurrences of '{keyword}'")

    def _initialize_results_dict(self, metric_keywords: List[str]) -> Dict[str, List]:
        """Initialize results dictionary with empty lists"""
        return {keyword: [] for keyword in metric_keywords}

    def _extract_metrics_from_all_tables(
        self, metric_keywords: List[str], results: Dict
    ):
        """Extract metrics from all loaded tables"""
        for table_id, table_info in self.table_loader.tables_data.items():
            self._extract_metrics_from_table(
                table_id, table_info, metric_keywords, results
            )

    def extract_financial_metrics(
        self, metric_keywords: List[str]
    ) -> Dict[str, List[Dict]]:
        """Extract common financial metrics across all tables"""
        self._validate_tables_loaded()
        results = self._initialize_results_dict(metric_keywords)
        self._extract_metrics_from_all_tables(metric_keywords, results)
        self._log_metrics_summary(results)
        return results
