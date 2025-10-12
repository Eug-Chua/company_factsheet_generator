# Pre-Extraction Validation Module

## Overview

Validates PDF extraction quality by comparing the original PDF with the extracted markdown and tables. Ensures the extraction process captured sufficient content before proceeding to downstream processing.

## Architecture

```
PDFExtractionValidator (Orchestrator)
├── PDFAnalyzer → Extract PDF text and load tables
└── KeywordAnalyzer → Verify domain keyword coverage
```

## Components

### 1. `conversion_validator.py`
**Main orchestrator** for extraction quality validation.

**Validation Pipeline (6 Steps):**
1. **Extract PDF metadata** - Page count, character count, file size
2. **Load extracted content** - Markdown + tables from conversion step
3. **Calculate extraction metrics** - Character and word extraction rates
4. **Check keyword coverage** - Verify financial domain keywords present
5. **Assess quality** - Determine quality level (Excellent/Good/Fair/Poor)
6. **Save validation report** - JSON output with recommendations

**Quality Levels:**
```python
Excellent: ≥70% extraction AND ≥85% keyword coverage
Good:      ≥70% extraction AND ≥60% keyword coverage
Fair:      ≥50% extraction AND ≥50% keyword coverage
Poor:      <50% extraction OR  <50% keyword coverage
```

**Key Methods:**
- `validate_extraction()` - Main entry point, returns validation report path
- `_assess_quality()` - Determines quality level and issues
- `calculate_extraction_metrics()` - Computes extraction rates

**Output:** `{company}_extraction_validation.json`

### 2. `pdf_analyzer.py`
**Handles PDF text extraction and table loading.**

**Key Responsibilities:**
- Extract text from original PDF using PyMuPDF
- Extract PDF metadata (pages, size, encryption status)
- Load table data from conversion output
- Combine markdown and table text for validation

**Key Methods:**
- `get_pdf_metadata()` - Extract PDF properties
- `extract_pdf_text()` - Get raw text from PDF
- `load_merged_chunks()` - Load tables JSON and combine text

**Table Loading:**
```python
# Tables JSON structure (from conversion)
{
  "table_0": {
    "markdown": "| Col1 | Col2 |...",
    "csv": "Col1,Col2,...",
    ...
  }
}

# Extracts markdown representation of all tables
# Combines with markdown text for comprehensive validation
```

### 3. `keyword_analyzer.py`
**Verifies presence of financial domain keywords.**

**Keyword Categories:**
- **Financial Statements:** income statement, balance sheet, cash flow, etc.
- **Key Metrics:** revenue, profit, assets, liabilities, equity, etc.
- **Risk Management:** risk factors, material risks, contingencies, etc.
- **Governance:** board of directors, audit committee, shareholders, etc.

**Analysis:**
```python
# Per-category coverage
{
  "financial_statements": {
    "keywords": ["income statement", "balance sheet", ...],
    "found": ["income statement", "cash flow"],
    "coverage": 0.67  # 2/3 found
  },
  "key_metrics": {...},
  "overall": {
    "total_keywords": 52,
    "total_found": 37,
    "coverage": 0.712  # 71.2%
  }
}
```

**Key Methods:**
- `check_keyword_presence()` - Analyze keyword coverage
- `_check_category_keywords()` - Check specific category
- `_calculate_overall_coverage()` - Aggregate across categories

## Data Flow

```
Original PDF
    ↓
[Step 1: Extract PDF Text]
    ├→ PyMuPDF extraction
    ├→ Character/word counts
    └→ Metadata (pages, size)
    ↓
[Step 2: Load Extracted Content]
    ├→ Markdown from conversion/
    ├→ Tables JSON from conversion/
    └→ Combine markdown + tables
    ↓
[Step 3: Calculate Metrics]
    ├→ Extraction rate: markdown_chars / pdf_chars
    └→ Word extraction rate: markdown_words / pdf_words
    ↓
[Step 4: Keyword Coverage]
    ├→ Check 52 financial keywords
    ├→ Per-category analysis
    └→ Overall coverage %
    ↓
[Step 5: Quality Assessment]
    ├→ Determine quality level
    ├→ Identify issues
    └→ Generate recommendations
    ↓
[Step 6: Save Report]
    └→ JSON output with all metrics
```

## Usage

### CLI Usage
```bash
# Validate specific company
python -m pre_extraction_validation.conversion_validator --company grab

# Use custom config
python -m pre_extraction_validation.conversion_validator --config path/to/config.yaml
```

### Programmatic Usage
```python
from pre_extraction_validation.conversion_validator import PDFExtractionValidator
from config_loader import load_config

config = load_config()
config.set_company('grab')

validator = PDFExtractionValidator(config)
report_path = validator.validate_extraction()
```

### Pipeline Integration
```python
# Automatically called in main pipeline
# Step 2 (after PDF conversion)
validation_path = pdf_validator.validate_extraction(
    pdf_path=config.pdf_path,
    markdown_path=config.markdown_path
)
```

## Output Format

### Validation Report JSON
```json
{
  "company": "grab",
  "pdf_path": "/path/to/Grab 2024.pdf",
  "markdown_path": "/path/to/Grab 2024.md",

  "pdf_metadata": {
    "page_count": 297,
    "file_size_mb": 15.4,
    "encrypted": false,
    "pdf_char_count": 1031487,
    "pdf_word_count": 158449
  },

  "extraction_metrics": {
    "markdown_char_count": 1212740,
    "markdown_word_count": 167481,
    "char_extraction_rate": 117.6,      // Can exceed 100% (formatting)
    "word_extraction_rate": 105.7
  },

  "keyword_coverage": {
    "financial_statements": {
      "keywords": [...],
      "found": [...],
      "coverage": 0.83
    },
    // ... other categories
    "overall": {
      "total_keywords": 52,
      "total_found": 37,
      "coverage": 0.712
    }
  },

  "quality_assessment": {
    "quality": "Good",
    "status": "pass",
    "char_extraction_rate": 117.6,
    "keyword_coverage_rate": 71.2,
    "issues": [
      "None - extraction quality is good"
    ],
    "recommendation": "Extraction quality is good. Proceed with semantic chunking."
  }
}
```

## Configuration

Configured via `configs/config.yaml`:

```yaml
outputs_folder: "outputs"

pdf_files:
  grab: "Grab 2024.pdf"
  # Company name used in output path: outputs/{company}/
```

## Output Locations

```
outputs/
├── grab/
│   └── grab_extraction_validation.json
├── sq/
│   └── sq_extraction_validation.json
└── ...
```

## Design Decisions

### Why Validate After Extraction?

1. **Early Detection:** Catch extraction issues before investing in downstream processing
2. **Quality Assurance:** Ensures financial keywords are present (completeness check)
3. **Debugging Aid:** Validation report helps diagnose PDF-specific extraction problems
4. **Pipeline Safety:** Prevents garbage data from propagating through pipeline

### Why Include Tables in Validation?

Originally, validation only checked markdown text, **excluding tables**. This caused artificially low extraction rates for table-heavy documents.

**Fix Applied:** Now loads `{company}_tables.json` and includes table markdown in validation metrics. This gives accurate extraction quality scores for financial reports (which are table-heavy).

### Extraction Rate >100%?

Yes, this is normal! Markdown formatting adds characters:
- **Markdown syntax:** `**bold**`, `# headers`, `| tables |`
- **URLs:** Full URLs vs. hyperlinked text in PDF
- **Spacing:** Consistent spacing in markdown vs. variable in PDF

Example: "Revenue" in PDF becomes "**Total Revenue**" in markdown (more characters).

## Keyword Categories

### 1. Financial Statements (12 keywords)
- income statement, balance sheet, cash flow statement
- statement of financial position, statement of profit or loss
- statement of changes in equity, statement of comprehensive income
- consolidated financial statements, notes to financial statements
- auditor's report, independent auditor, financial highlights

### 2. Key Metrics (15 keywords)
- revenue, profit, loss, earnings, EBITDA, operating income
- net income, gross profit, assets, liabilities, equity, debt
- cash flow, shareholder, dividend

### 3. Risk Management (13 keywords)
- risk factors, material risks, principal risks, risk management
- credit risk, market risk, operational risk, liquidity risk
- contingent liabilities, commitments, litigation
- regulatory compliance, internal controls

### 4. Governance (12 keywords)
- board of directors, corporate governance, audit committee
- remuneration committee, nomination committee
- related party transactions, shareholder rights
- code of conduct, ethics, compliance
- management discussion, MD&A

**Total: 52 financial keywords**

## Logging

Validation operations logged to `logs/logs_{timestamp}.log` with prefix `pdf_validation`.

**Key Log Messages:**
- `"Validating Docling extraction for: {company}"` - Start
- `"Step 2: Loading markdown and tables..."` - Table inclusion
- `"Loaded tables: X tables (Y chars)"` - Table loading success
- `"✓ PDF validation complete: {quality} quality ({X}% extraction, {Y}% keywords)"` - Result

## Error Handling

- **Missing PDF:** Raises `FileNotFoundError` with clear message
- **Missing Markdown:** Falls back to markdown-only validation with warning
- **Missing Tables:** Continues without tables (logs info message)
- **Invalid JSON:** Catches and logs JSON parsing errors

## Performance

| Company | Pages | Validation Time | Keywords Found |
|---------|-------|-----------------|----------------|
| Grab    | 297   | ~2s             | 37/52 (71%)    |
| SQ      | 252   | ~1.5s           | 34/52 (65%)    |
| SEA     | 229   | ~1.2s           | 31/52 (60%)    |

## Dependencies

- `PyMuPDF` (fitz) - PDF text extraction
- `json` - Report saving/loading
- `pathlib` - Path handling
- `config_loader` - Configuration management

## Related Modules

- **Previous Step:** `conversion/` - PDF to markdown + tables
- **Next Step:** `extraction/` - Text chunking
- **Uses:** `conversion/` output (markdown + tables JSON)
- **Outputs to:** `outputs/{company}/` folder
