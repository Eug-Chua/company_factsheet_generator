"""
Text Processor
Extracts clean text from PDF documents without table processing
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend


class TextProcessor:
    """Handles clean text extraction from PDFs (Pass 1: No tables)"""

    def __init__(self, logger):
        """Initialize text processor with logger"""
        self.logger = logger
        self.converter = self._init_text_converter()
        self.logger.info("Text processor initialized (clean extraction)")

    def _create_text_pipeline_options(self):
        """Create pipeline options for clean text extraction"""
        options = PdfPipelineOptions()
        options.do_table_structure = False
        return options

    def _create_pdf_format_option(self, pipeline_options):
        """Create PDF format option with given pipeline settings"""
        return PdfFormatOption(
            pipeline_options=pipeline_options,
            backend=DoclingParseDocumentBackend
        )

    def _init_text_converter(self):
        """Initialize converter for clean text extraction only"""
        pipeline_options = self._create_text_pipeline_options()
        pdf_options = self._create_pdf_format_option(pipeline_options)
        return DocumentConverter(format_options={InputFormat.PDF: pdf_options})

    def extract_text(self, pdf_path):
        """Extract clean text without tables (Pass 1)"""
        self.logger.info("PASS 1: Extracting clean text (no table processing)...")
        result = self.converter.convert(pdf_path)
        content = result.document.export_to_markdown()
        self.logger.info(f"Pass 1 complete: {len(content):,} characters extracted")
        return content
