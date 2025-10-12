# Conversion Module

## Overview

The conversion module handles PDF to Markdown transformation using a **2-pass extraction system** powered by Docling. It extracts both textual content and structured table data from annual report PDFs.

## Architecture

```
MarkdownConverter (Orchestrator)
├── TextProcessor → Pass 1: Clean text extraction
└── TableProcessor → Pass 2: Structured table extraction
```

## Components

### 1. `markdown_converter.py`
**Main orchestrator** for the 2-pass PDF extraction system.

**Key Responsibilities:**
- Coordinates text and table extraction passes
- Manages Docling converter instances
- Saves markdown and table outputs
- Supports batch processing for multiple companies

**Key Methods:**
- `convert_pdf_to_markdown()` - Main entry point for single PDF
- `convert_all_companies()` - Batch process all companies in config
- `_extract_structured_tables()` - Execute Pass 2 (table extraction)

**Output Files:**
- `{company}_markdown.md` - Clean markdown text
- `{company}_tables.json` - Structured table data

### 2. `text_processor.py`
**Pass 1: Text Extraction**

**Purpose:** Extract clean textual content from PDFs without table structure (faster).

**Configuration:**
```python
PdfPipelineOptions(
    do_ocr=False,                    # Speed optimization
    do_table_structure=False,        # Skip tables in Pass 1
    generate_page_images=False       # No image generation needed
)
```

**Key Methods:**
- `extract_text()` - Extract markdown from PDF
- `_export_to_markdown()` - Convert Docling result to markdown string

**Output:** Clean markdown text optimized for text chunking.

### 3. `table_processor.py`
**Pass 2: Table Extraction**

**Purpose:** Extract structured table data with precise cell matching.

**Configuration:**
```python
PdfPipelineOptions(
    do_table_structure=True,             # Enable table extraction
    table_structure_options={
        'do_cell_matching': True,         # Accurate cell boundaries
        'mode': TableFormerMode.ACCURATE  # Highest quality
    }
)
```

**Key Methods:**
- `extract_tables()` - Extract all tables from PDF
- `_process_single_table()` - Convert table to multiple formats
- `_convert_to_dataframe()` - Table → pandas DataFrame
- `_format_table_outputs()` - Generate markdown, CSV, and JSON representations

**Table Output Structure:**
```json
{
  "table_0": {
    "dataframe": [...],        // Row-wise data
    "markdown": "...",         // Markdown table format
    "csv": "...",             // CSV format
    "shape": [rows, cols],    // Dimensions
    "location": {             // Position in PDF
      "page": 1,
      "bbox": [...]
    }
  }
}
```

## Data Flow

```
PDF Input
    ↓
[Pass 1: Text Extraction]
    ├→ Fast OCR-free extraction
    ├→ Clean markdown formatting
    └→ Output: {company}.md
    ↓
[Pass 2: Table Extraction]
    ├→ Accurate table structure detection
    ├→ Cell matching and parsing
    ├→ Multi-format export (DataFrame, markdown, CSV)
    └→ Output: {company}_tables.json
```

## Usage

### CLI - Single Company
```bash
python -m conversion.markdown_converter --company grab
```

### CLI - All Companies
```bash
python -m conversion.markdown_converter
```

### Programmatic Usage
```python
from conversion.markdown_converter import MarkdownConverter
from config_loader import load_config

config = load_config()
config.set_company('grab')

converter = MarkdownConverter(config)
output_path = converter.convert_pdf_to_markdown()
```

## Configuration

Configured via `configs/config.yaml`:

```yaml
pdf_folder: "data"
markdown_folder: "markdown_files"

pdf_files:
  grab: "Grab 2024.pdf"
  sq: "SQ 2024.pdf"
  # ... more companies
```

## Output Locations

```
markdown_files/
├── Grab 2024.md              # Pass 1: Text content
├── Grab 2024_tables.json     # Pass 2: Structured tables
├── SQ 2024.md
├── SQ 2024_tables.json
└── ...
```

## Design Decisions

### Why 2-Pass Extraction?

1. **Speed Optimization:** Pass 1 is fast (no table processing) for quick text extraction
2. **Accuracy:** Pass 2 focuses on precise table structure with cell matching
3. **Separation of Concerns:** Text and tables processed independently for better quality
4. **Flexibility:** Can re-run Pass 2 without re-extracting text

### Why Docling?

- **Best-in-class PDF parsing** for financial documents
- **Accurate table extraction** with cell-level matching
- **Multi-format output** (markdown, JSON, CSV)
- **Page-aware processing** maintains document structure

## Performance

| Company | Pages | Pass 1 (Text) | Pass 2 (Tables) | Total Tables |
|---------|-------|---------------|-----------------|--------------|
| Grab    | 297   | ~15s          | ~25s            | 145          |
| SQ      | 252   | ~12s          | ~20s            | 89           |
| SEA     | 229   | ~10s          | ~18s            | 67           |

## Logging

Conversion operations are logged to `logs/logs_{timestamp}.log` with the prefix `conversion`.

**Key Log Messages:**
- `"Initializing 2-pass extraction system..."` - Startup
- `"PASS 2: Extracting structured tables..."` - Table extraction start
- `"✓ Pass 2 complete: X tables extracted"` - Success
- `"✓ Successfully saved markdown to: ..."` - Output confirmation

## Error Handling

- **File Not Found:** Validates PDF exists before processing
- **Conversion Failures:** Logs detailed error messages with stack traces
- **Batch Processing:** Continues processing other companies on individual failures

## Dependencies

- `docling` - PDF extraction engine
- `docling.document_converter` - Document processing
- `docling.datamodel.pipeline_options` - Configuration
- `pandas` - DataFrame manipulation (indirect via Docling)

## Related Modules

- **Next Step:** `pre_extraction_validation/` - Validates extraction quality
- **Uses Config:** `config_loader.py` - Company and path configuration
- **Logs:** Standard logging configuration from `config_loader`
