"""
Table Processor
Extracts and processes tables from PDF documents
"""

import pandas as pd


class TableProcessor:
    """Handles table extraction and DataFrame processing"""

    def __init__(self, logger):
        """Initialize table processor with logger"""
        self.logger = logger

    def _fix_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Make duplicate column names unique by adding suffixes (_1, _2, etc)"""
        if len(df.columns) == len(set(df.columns)):
            return df  # No duplicates

        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            count = sum(cols == dup)
            cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(count)]

        df.columns = cols
        return df

    def _extract_page_number(self, table) -> int | None:
        """Extract page number from table provenance metadata"""
        if not table.prov:
            return None

        try:
            prov_item = table.prov[0]
            # Handle different attribute names in Docling API
            if hasattr(prov_item, 'page'):
                return prov_item.page
            elif hasattr(prov_item, 'page_no'):
                return prov_item.page_no
            return None
        except (AttributeError, IndexError):
            return None

    def _process_table(self, table, idx: int) -> dict | None:
        """
        Convert a Docling table to our metadata format.
        
        Returns:
            dict with keys: dataframe, markdown, shape, location
            None if table is empty or processing fails
        """
        try:
            # Convert to pandas DataFrame
            df = table.export_to_dataframe()
            if df.empty:
                return None

            # Fix duplicate column names
            df = self._fix_duplicate_columns(df)

            # Build metadata
            return {
                'dataframe': df.to_dict('records'),
                'markdown': df.to_markdown(index=False),
                'shape': {'rows': len(df), 'columns': len(df.columns)},
                'location': {'page': self._extract_page_number(table)}
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract table {idx}: {e}")
            return None

    def extract_tables(self, result) -> dict:
        """
        Extract all tables from Docling conversion result.
        
        Returns:
            dict: {"table_0": {...}, "table_1": {...}, ...}
        """
        try:
            tables = {}
            for idx, table in enumerate(result.document.tables):
                metadata = self._process_table(table, idx)
                if metadata:
                    tables[f"table_{idx}"] = metadata

            self.logger.info(f"Successfully extracted {len(tables)} tables from PDF")
            return tables

        except Exception as e:
            self.logger.warning(f"Table extraction encountered issues: {e}")
            return {}