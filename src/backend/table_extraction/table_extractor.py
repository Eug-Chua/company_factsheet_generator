"""
Numerical Data Extractor
Orchestrates table loading, searching, and chunking
"""

from pathlib import Path
from typing import List, Dict, Optional
from config_loader import load_config
from .table_loader import TableLoader
from .table_searcher import TableSearcher
from .table_chunker import TableChunker


class NumericalExtractor:
    """Extracts and processes numerical data from table JSON files"""

    def __init__(self, config=None):
        """Initialize extractor with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging for numerical extraction"""
        self.logger = self.config.setup_logger("numerical_extraction", __name__)

    def _initialize_components(self):
        """Initialize loader, searcher, and chunker components"""
        self.loader = TableLoader(self.logger, self.config)
        self.searcher = TableSearcher(self.logger, self.loader)
        self.chunker = TableChunker(self.logger, self.config, self.loader)

    # Delegate to TableLoader
    def load_tables(self, tables_path: Optional[Path] = None) -> Dict:
        """Load tables from JSON file"""
        return self.loader.load_tables(tables_path)

    def get_table_list(self) -> List[Dict]:
        """Get list of all tables with metadata"""
        return self.loader.get_table_list()

    def get_table_by_id(self, table_id: str):
        """Get table as DataFrame by ID"""
        return self.loader.get_table_by_id(table_id)

    def get_table_markdown(self, table_id: str) -> Optional[str]:
        """Get table as markdown string"""
        return self.loader.get_table_markdown(table_id)

    def get_table_summary(self) -> str:
        """Get a summary of all loaded tables"""
        return self.loader.get_table_summary()

    def export_all_tables_to_csv(self, output_dir: Optional[Path] = None):
        """Export all tables to CSV files"""
        return self.loader.export_all_tables_to_csv(output_dir)

    # Delegate to TableSearcher
    def search_tables_by_keyword(self, keyword: str, case_sensitive=False) -> List[Dict]:
        """Search for tables containing a keyword"""
        return self.searcher.search_tables_by_keyword(keyword, case_sensitive)

    def extract_numerical_value(self, table_id: str, row_keyword: str,
                                col_keyword: Optional[str] = None):
        """Extract a specific numerical value from a table"""
        return self.searcher.extract_numerical_value(table_id, row_keyword, col_keyword)

    def extract_financial_metrics(self, metric_keywords: List[str]) -> Dict:
        """Extract common financial metrics across all tables"""
        return self.searcher.extract_financial_metrics(metric_keywords)

    # Delegate to TableChunker
    def create_table_chunks(self, max_chunk_size: int = 2000) -> List[Dict]:
        """Convert tables to chunks for RAG retrieval"""
        return self.chunker.create_table_chunks(max_chunk_size)

    def save_table_chunks(self, chunks: List[Dict], output_path: Optional[Path] = None) -> Path:
        """Save table chunks to JSON file"""
        return self.chunker.save_table_chunks(chunks, output_path)

    def process_tables_to_chunks(self, tables_path: Optional[Path] = None,
                                 max_chunk_size: int = 2000) -> Dict:
        """Complete pipeline: load tables → create chunks → save"""
        return self.chunker.process_tables_to_chunks(tables_path, max_chunk_size)


# CLI Functions

def _create_cli_parser():
    """Create and configure argument parser"""
    import argparse
    parser = argparse.ArgumentParser(description="Extract numerical data from table JSON files")
    parser.add_argument('--company', type=str, required=True, help='Company name (e.g., dbs, grab, capitaland)')
    parser.add_argument('--tables', type=str, help='Path to tables JSON file (optional, auto-detects from company name)')
    parser.add_argument('--search', type=str, help='Search tables for keyword')
    parser.add_argument('--metrics', type=str, nargs='+', help='Extract financial metrics (e.g., revenue profit assets)')
    parser.add_argument('--export', action='store_true', help='Export all tables to CSV files')
    parser.add_argument('--config', type=str, help='Path to config.yaml file (optional)')
    return parser

def _load_config_and_setup(args):
    """Load config and initialize extractor"""
    config = load_config(args.config) if args.config else load_config()
    config.set_company(args.company)
    extractor = NumericalExtractor(config)
    tables_path = Path(args.tables) if args.tables else None
    extractor.load_tables(tables_path)
    return extractor

def _print_search_results(extractor, keyword: str):
    """Print search results"""
    results = extractor.search_tables_by_keyword(keyword)
    print(f"\n{'='*60}\nSearch Results for '{keyword}'\n{'='*60}")
    for result in results:
        print(f"\nTable: {result['table_id']} (page {result['page']})")
        print(result['dataframe'].to_string())

def _print_metrics_results(extractor, metrics: List[str]):
    """Print metrics extraction results"""
    results = extractor.extract_financial_metrics(metrics)
    print(f"\n{'='*60}\nFinancial Metrics Extraction\n{'='*60}")
    for metric, matches in results.items():
        print(f"\n{metric.upper()}:")
        for match in matches[:5]:
            print(f"  Table {match['table_id']}, page {match['page']}: {match['value']}")
            print(f"    Context: {match['context'][:80]}...")

def main():
    """CLI entry point"""
    parser = _create_cli_parser()
    args = parser.parse_args()
    extractor = _load_config_and_setup(args)
    print(extractor.get_table_summary() + "\n")
    if args.search: _print_search_results(extractor, args.search)
    if args.metrics: _print_metrics_results(extractor, args.metrics)
    if args.export: print(f"\n✓ Exported tables to: {extractor.export_all_tables_to_csv()}")


if __name__ == "__main__":
    main()
