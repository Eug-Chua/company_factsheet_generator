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

    def _has_duplicate_columns(self, df):
        """Check if DataFrame has duplicate column names"""
        return len(df.columns) != len(set(df.columns))

    def _generate_unique_column_names(self, cols, dup):
        """Generate unique column names for duplicates"""
        count = sum(cols == dup)
        return [f"{dup}_{i}" if i != 0 else dup for i in range(count)]

    def _make_columns_unique(self, df):
        """Make duplicate column names unique by adding suffixes"""
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols == dup] = self._generate_unique_column_names(cols, dup)
        df.columns = cols
        return df

    def _normalize_dataframe_columns(self, df):
        """Normalize dataframe columns if needed"""
        if self._has_duplicate_columns(df):
            return self._make_columns_unique(df)
        return df

    def _get_page_from_prov(self, prov_item):
        """Get page number from provenance item"""
        if hasattr(prov_item, 'page'):
            return prov_item.page
        elif hasattr(prov_item, 'page_no'):
            return prov_item.page_no
        return None

    def _extract_page_number(self, table):
        """Extract page number from table provenance"""
        if not table.prov:
            return None
        try:
            return self._get_page_from_prov(table.prov[0])
        except (AttributeError, IndexError):
            return None

    def _create_table_shape(self, df):
        """Create shape metadata for table"""
        return {'rows': len(df), 'columns': len(df.columns)}

    def _create_table_metadata(self, df, page_info):
        """Create metadata dictionary for table"""
        return {'dataframe': df.to_dict('records'), 'markdown': df.to_markdown(index=False),
                'csv': df.to_csv(index=False), 'shape': self._create_table_shape(df),
                'location': {'page': page_info}}

    def _process_single_table(self, table, idx):
        """Process a single table and return metadata or None"""
        df = table.export_to_dataframe()
        if df.empty:
            return None
        df = self._normalize_dataframe_columns(df)
        page_info = self._extract_page_number(table)
        return self._create_table_metadata(df, page_info)

    def _try_process_table(self, table, idx, tables):
        """Try to process a single table and add to collection"""
        try:
            metadata = self._process_single_table(table, idx)
            if metadata:
                tables[f"table_{idx}"] = metadata
        except Exception as e:
            self.logger.warning(f"Failed to extract table {idx}: {e}")

    def _extract_all_tables(self, document_tables):
        """Extract all tables from document tables"""
        tables = {}
        for idx, table in enumerate(document_tables):
            self._try_process_table(table, idx, tables)
        self.logger.info(f"Successfully extracted {len(tables)} tables from PDF")
        return tables

    def extract_tables(self, result) -> dict:
        """Extract all tables from document"""
        try:
            return self._extract_all_tables(result.document.tables)
        except Exception as e:
            self.logger.warning(f"Table extraction encountered issues: {e}")
            return {}
