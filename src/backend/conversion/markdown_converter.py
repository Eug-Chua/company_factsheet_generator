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
    """Orchestrates PDF to Markdown conversion with table extraction"""

    def __init__(self, config=None):
        """Initialize converter with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_processors()

    def _setup_logging(self):
        """Setup logging for conversion process"""
        self.logger = self.config.setup_logger("conversion", __name__)

    def _initialize_processors(self):
        """Initialize text and table processors"""
        self.logger.info("Initializing 2-pass extraction system...")
        self.text_processor = TextProcessor(self.logger)
        self.table_processor = TableProcessor(self.logger)
        self.table_converter = self._init_table_converter()
        self.logger.info("✓ Pass 2: Table converter ready (structured data)")

    def _create_table_pipeline_options(self):
        """Create pipeline options for table extraction"""
        options = PdfPipelineOptions()
        options.do_table_structure = True
        options.table_structure_options.do_cell_matching = True
        options.table_structure_options.mode = TableFormerMode.ACCURATE
        return options

    def _create_pdf_format_option(self, pipeline_options):
        """Create PDF format option with given pipeline settings"""
        return PdfFormatOption(
            pipeline_options=pipeline_options,
            backend=DoclingParseDocumentBackend
        )

    def _init_table_converter(self):
        """Initialize converter for table extraction only"""
        pipeline_options = self._create_table_pipeline_options()
        pdf_options = self._create_pdf_format_option(pipeline_options)
        return DocumentConverter(format_options={InputFormat.PDF: pdf_options})

    def _validate_pdf_exists(self, pdf_path: Path):
        """Validate that PDF file exists"""
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    def _extract_structured_tables(self, pdf_path):
        """Extract structured tables separately (Pass 2)"""
        self.logger.info("PASS 2: Extracting structured tables...")
        result = self.table_converter.convert(pdf_path)
        tables = self.table_processor.extract_tables(result)
        self.logger.info(f"✓ Pass 2 complete: {len(tables)} tables extracted")
        return tables

    def _convert_to_markdown(self, pdf_path: Path) -> tuple[str, dict]:
        """Convert PDF using 2-pass extraction"""
        markdown_content = self.text_processor.extract_text(pdf_path)
        tables_data = self._extract_structured_tables(pdf_path)
        return markdown_content, tables_data

    def _get_tables_path(self, output_path):
        """Generate path for tables JSON file"""
        return output_path.parent / f"{output_path.stem}_tables.json"

    def _write_tables_json(self, tables_data, tables_path):
        """Write tables data to JSON file"""
        with open(tables_path, 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved {len(tables_data)} tables to: {tables_path}")

    def _save_tables(self, tables_data: dict, output_path: Path) -> Path:
        """Save extracted tables to separate JSON file"""
        if not tables_data:
            self.logger.info("No tables to save")
            return None
        tables_path = self._get_tables_path(output_path)
        self._write_tables_json(tables_data, tables_path)
        return tables_path

    def _save_markdown(self, markdown_content: str, output_path: Path) -> Path:
        """Save markdown content to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        return output_path

    def _log_success(self, output_path: Path):
        """Log successful conversion"""
        file_size = output_path.stat().st_size
        self.logger.info(f"✓ Successfully saved markdown to: {output_path}")
        self.logger.info(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    def _resolve_paths(self, pdf_path, output_path):
        """Resolve input and output paths from arguments or config"""
        pdf_path = Path(pdf_path or self.config.pdf_path)
        output_path = Path(output_path or self.config.markdown_path)
        return pdf_path, output_path

    def _log_conversion_start(self, pdf_path, output_path):
        """Log conversion start information"""
        self.logger.info(f"Starting enhanced conversion: {pdf_path.name}")
        self.logger.info(f"Output path: {output_path}")

    def _log_tables_output(self, tables_path):
        """Log tables output path if tables were saved"""
        if tables_path:
            self.logger.info(f"  Tables file: {tables_path}")

    def _perform_conversion(self, pdf_path, output_path):
        """Perform the conversion and save outputs"""
        markdown_content, tables_data = self._convert_to_markdown(pdf_path)
        self._save_markdown(markdown_content, output_path)
        tables_path = self._save_tables(tables_data, output_path)
        self._log_success(output_path)
        self._log_tables_output(tables_path)

    def _prepare_for_conversion(self, pdf_path, output_path):
        """Prepare and validate paths for conversion"""
        pdf_path, output_path = self._resolve_paths(pdf_path, output_path)
        self._validate_pdf_exists(pdf_path)
        self._log_conversion_start(pdf_path, output_path)
        return pdf_path, output_path

    def convert_pdf_to_markdown(self, pdf_path: Path = None, output_path: Path = None) -> Path:
        """Convert a PDF file to Markdown with table extraction"""
        pdf_path, output_path = self._prepare_for_conversion(pdf_path, output_path)
        try:
            self._perform_conversion(pdf_path, output_path); return output_path
        except Exception as e:
            self.logger.error(f"✗ Enhanced conversion failed: {str(e)}"); raise

    def _get_companies_list(self) -> list:
        """Get list of companies from config"""
        return list(self.config.config['pdf_files'].keys())

    def _log_company_header(self, company):
        """Log company processing header"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Processing: {company.upper()}")
        self.logger.info(f"{'='*60}")

    def _convert_single_company(self, company: str, results: dict):
        """Convert PDF for a single company"""
        self._log_company_header(company)
        try:
            self.config.set_company(company)
            results[company] = self.convert_pdf_to_markdown()
        except Exception as e:
            self.logger.error(f"Failed to convert {company}: {e}"); results[company] = None

    def _log_batch_summary(self, results: dict):
        """Log batch conversion summary"""
        successful = sum(1 for v in results.values() if v is not None)
        total = len(results)
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Conversion complete: {successful}/{total} successful")
        self.logger.info(f"{'='*60}")

    def _process_all_companies(self, companies):
        """Process all companies and return results"""
        results = {}
        for company in companies:
            self._convert_single_company(company, results)
        return results

    def convert_all_companies(self) -> dict:
        """Convert PDFs for all companies in config"""
        companies = self._get_companies_list()
        self.logger.info(f"Converting {len(companies)} companies: {', '.join(companies)}")
        results = self._process_all_companies(companies)
        self._log_batch_summary(results)
        return results


# CLI Functions

def _create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(description="Convert PDF annual reports to Markdown")
    parser.add_argument('--company', type=str,
                       help='Company to convert (capitaland, dbs, grab, sq). If not specified, converts all.')
    parser.add_argument('--config', type=str,
                       help='Path to config.yaml file (optional)')
    return parser


def _convert_single_company(converter, config, company):
    """Convert a single company's PDF"""
    config.set_company(company)
    output_path = converter.convert_pdf_to_markdown()
    converter.logger.info(f"\n✓ Conversion complete: {output_path}")


def _log_batch_results(converter, results):
    """Log results from batch conversion"""
    converter.logger.info("\n✓ Batch conversion complete")
    for company, path in results.items():
        status = "✓" if path else "✗"
        converter.logger.info(f"  {status} {company}: {path if path else 'FAILED'}")


def _convert_all_companies(converter):
    """Convert all companies' PDFs"""
    results = converter.convert_all_companies()
    _log_batch_results(converter, results)


def _load_config_from_args(args):
    """Load configuration from arguments"""
    return load_config(args.config) if args.config else load_config()


def _run_conversion(converter, config, args):
    """Run conversion based on arguments"""
    if args.company:
        _convert_single_company(converter, config, args.company)
    else:
        _convert_all_companies(converter)


def main():
    """CLI entry point"""
    parser = _create_argument_parser()
    args = parser.parse_args()
    config = _load_config_from_args(args)
    converter = MarkdownConverter(config)
    _run_conversion(converter, config, args)


if __name__ == "__main__":
    main()
