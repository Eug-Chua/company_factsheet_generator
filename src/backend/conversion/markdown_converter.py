
"""
PDF Converter
Orchestrates PDF to Markdown conversion using 2-pass extraction
"""

import argparse
import json
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from config_loader import load_config
from .text_processor import TextProcessor
from .table_processor import TableProcessor


class MarkdownConverter:
    """
    Orchestrates PDF to Markdown conversion with table extraction.
    
    Uses a 2-pass approach:
    - Pass 1: Extract clean text (tables OFF) → markdown file
    - Pass 2: Extract structured tables (tables ON) → JSON file
    """

    def __init__(self, config=None):
        """Initialize converter with text and table processors"""
        self.config = config or load_config()
        self.logger = self.config.setup_logger("conversion", __name__)

        self.logger.info("Initializing 2-pass extraction system...")
        self.text_processor = TextProcessor(self.logger)
        self.table_processor = TableProcessor(self.logger)
        self.table_converter = self._init_table_converter()
        self.logger.info("✓ Pass 2: Table converter ready (structured data)")

    def _init_table_converter(self):
        """
        Initialize Docling converter for accurate table extraction.
        
        Configured with:
        - do_table_structure: True (enable table detection)
        - do_cell_matching: True (match cells to table structure)
        - mode: ACCURATE (slower but more accurate)
        """
        # Configure pipeline for accurate table extraction
        options = PdfPipelineOptions()
        options.do_table_structure = True
        options.table_structure_options.do_cell_matching = True
        options.table_structure_options.mode = TableFormerMode.ACCURATE

        # Create PDF format options with our pipeline settings
        pdf_options = PdfFormatOption(
            pipeline_options=options,
            backend=DoclingParseDocumentBackend
        )

        return DocumentConverter(format_options={InputFormat.PDF: pdf_options})

    def _extract_tables(self, pdf_path: Path) -> dict:
        """
        Extract structured tables from PDF (Pass 2).
        
        Returns:
            dict: {"table_0": {...}, "table_1": {...}, ...}
        """
        self.logger.info("PASS 2: Extracting structured tables...")
        result = self.table_converter.convert(pdf_path)
        tables = self.table_processor.extract_tables(result)
        self.logger.info(f"✓ Pass 2 complete: {len(tables)} tables extracted")
        return tables

    def convert_pdf_to_markdown(self, pdf_path: Path = None, output_path: Path = None) -> Path:
        """
        Convert PDF to markdown with separate table extraction.
        
        Creates two files:
        - {output_path}.md - Clean markdown text
        - {output_path}_tables.json - Structured table data
        
        Args:
            pdf_path: Path to PDF file (uses config default if None)
            output_path: Path for markdown output (uses config default if None)
            
        Returns:
            Path to saved markdown file
        """
        # Resolve paths from args or config
        pdf_path = Path(pdf_path or self.config.pdf_path)
        output_path = Path(output_path or self.config.markdown_path)

        # Validate input
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.logger.info(f"Starting enhanced conversion: {pdf_path.name}")
        self.logger.info(f"Output path: {output_path}")

        try:
            # Pass 1: Extract clean text
            markdown_content = self.text_processor.extract_text(pdf_path)

            # Pass 2: Extract structured tables
            tables_data = self._extract_tables(pdf_path)

            # Save markdown file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            file_size = output_path.stat().st_size
            self.logger.info(f"✓ Successfully saved markdown to: {output_path}")
            self.logger.info(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

            # Save tables JSON if any tables found
            if tables_data:
                tables_path = output_path.parent / f"{output_path.stem}_tables.json"
                with open(tables_path, 'w', encoding='utf-8') as f:
                    json.dump(tables_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"  Tables file: {tables_path}")
            else:
                self.logger.info("No tables to save")

            return output_path

        except Exception as e:
            self.logger.error(f"✗ Enhanced conversion failed: {str(e)}")
            raise

    def convert_all_companies(self) -> dict:
        """
        Convert PDFs for all companies defined in config.
        
        Returns:
            dict: {company_name: output_path or None if failed}
        """
        companies = list(self.config.config['pdf_files'].keys())
        self.logger.info(f"Converting {len(companies)} companies: {', '.join(companies)}")

        results = {}
        for company in companies:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing: {company.upper()}")
            self.logger.info(f"{'='*60}")

            try:
                self.config.set_company(company)
                results[company] = self.convert_pdf_to_markdown()
            except Exception as e:
                self.logger.error(f"Failed to convert {company}: {e}")
                results[company] = None

        # Log summary
        successful = sum(1 for v in results.values() if v is not None)
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Conversion complete: {successful}/{len(companies)} successful")
        self.logger.info(f"{'='*60}")

        return results


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point for PDF conversion"""
    parser = argparse.ArgumentParser(
        description="Convert PDF annual reports to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
# Convert all companies in config
python markdown_converter.py

# Convert specific company
python markdown_converter.py --company dbs

# Use custom config
python markdown_converter.py --config /path/to/config.yaml
        """
    )

    parser.add_argument('--company', type=str,
                        help='Company to convert. If not specified, converts all.')
    parser.add_argument('--config', type=str,
                        help='Path to config.yaml file (optional)')

    args = parser.parse_args()

    # Load config and initialize converter
    config = load_config(args.config) if args.config else load_config()
    converter = MarkdownConverter(config)

    # Run conversion
    if args.company:
        # Single company
        config.set_company(args.company)
        output_path = converter.convert_pdf_to_markdown()
        converter.logger.info(f"\n✓ Conversion complete: {output_path}")
    else:
        # All companies
        results = converter.convert_all_companies()
        converter.logger.info("\n✓ Batch conversion complete")
        for company, path in results.items():
            status = "✓" if path else "✗"
            converter.logger.info(f"  {status} {company}: {path if path else 'FAILED'}")


if __name__ == "__main__":
    main()