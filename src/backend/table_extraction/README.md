# Table Extraction Module

## Overview

Converts structured tables from PDF extraction into **RAG-ready chunks** for retrieval. Takes table JSON output from the conversion module (Pass 2) and creates markdown-formatted chunks with metadata, enabling semantic search over financial tables.

## Architecture

```
NumericalExtractor (Orchestrator)
├── TableLoader → Load tables from JSON, provide access
├── TableSearcher → Search tables, extract numerical values
└── TableChunker → Convert tables to RAG-ready chunks
```

## Components

### 1. `table_extractor.py`
**Main orchestrator** for table processing pipeline.

**Key Responsibilities:**
- Coordinates loading, searching, and chunking operations
- Delegates to specialized components (loader, searcher, chunker)
- Provides unified interface for table operations
- Supports CLI for testing and manual exploration

**Key Methods:**
- `load_tables()` - Load tables from JSON file
- `search_tables_by_keyword()` - Find tables containing keyword
- `extract_financial_metrics()` - Extract specific metrics across all tables
- `create_table_chunks()` - Convert tables to RAG chunks
- `process_tables_to_chunks()` - Complete pipeline (load → chunk → save)

**CLI Usage:**
```bash
# Load and summarize tables
python -m table_extraction.table_extractor --company grab

# Search for tables containing keyword
python -m table_extraction.table_extractor --company grab --search "revenue"

# Extract specific metrics
python -m table_extraction.table_extractor --company grab --metrics revenue profit assets

# Export all tables to CSV
python -m table_extraction.table_extractor --company grab --export
```

### 2. `table_loader.py`
**Loads and provides access to table data from JSON files.**

**Key Responsibilities:**
- Load tables JSON from conversion output
- Provide access to tables by ID
- Convert tables to pandas DataFrames
- Export tables to CSV files

**Table JSON Structure (Input):**
```json
{
  "table_0": {
    "dataframe": [[row1], [row2], ...],
    "markdown": "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |",
    "csv": "Col1,Col2\nval1,val2",
    "shape": {"rows": 10, "columns": 5},
    "location": {"page": 42, "bbox": [...]}
  },
  "table_1": {...}
}
```

**Key Methods:**
- `load_tables()` - Load tables from JSON file
- `get_table_list()` - Get list of all tables with metadata
- `get_table_by_id()` - Get specific table as DataFrame
- `get_table_markdown()` - Get table as markdown string
- `get_table_summary()` - Get summary of all loaded tables
- `export_all_tables_to_csv()` - Export all tables to CSV files

**Auto-Detection:**
```python
# Auto-detects tables file based on markdown filename
# For: "Grab 2024.md" → looks for "Grab 2024_tables.json"
tables_path = self._auto_detect_tables_path()
```

### 3. `table_searcher.py`
**Searches tables and extracts numerical values.**

**Key Responsibilities:**
- Search tables by keyword (case-sensitive or not)
- Extract specific numerical values from tables
- Find financial metrics across all tables
- Handle row/column keyword matching

**Key Methods:**
- `search_tables_by_keyword()` - Find all tables containing keyword
- `extract_numerical_value()` - Extract specific value from table
- `extract_financial_metrics()` - Extract metrics across all tables

**Search Example:**
```python
# Find all tables with "revenue" keyword
results = searcher.search_tables_by_keyword("revenue")
# Returns: [{'table_id': 'table_12', 'page': 45, 'dataframe': ...}, ...]

# Extract specific value
value = searcher.extract_numerical_value(
    table_id="table_12",
    row_keyword="Total Revenue",
    col_keyword="2024"
)
# Returns: "45,678" (from cell matching row and column)
```

**Financial Metrics Extraction:**
```python
# Extract common metrics across all tables
metrics = searcher.extract_financial_metrics(["revenue", "profit", "assets"])
# Returns:
{
  "revenue": [
    {'table_id': 'table_12', 'page': 45, 'value': '45,678', 'context': 'Total Revenue'},
    {'table_id': 'table_23', 'page': 67, 'value': '12,345', 'context': 'Revenue Growth'}
  ],
  "profit": [...],
  "assets": [...]
}
```

**Value Extraction Logic:**
1. Find rows matching row_keyword (case-insensitive)
2. If col_keyword provided, find column matching col_keyword
3. If no col_keyword, extract first numeric value in row
4. Handle numeric columns and string values with numbers

### 4. `table_chunker.py`
**Converts tables to RAG-ready chunks.**

**Key Responsibilities:**
- Convert tables to markdown-formatted chunks
- Handle large tables by splitting into multiple chunks
- Preserve table headers across split chunks
- Generate unique chunk IDs (starting at 10000)

**Chunking Strategy:**

**Small Table (≤ max_chunk_size):**
```json
{
  "chunk_id": 10000,
  "section_header": "Table 1 (Page 42): 10×5",
  "header_level": 0,
  "content": "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |",
  "content_type": "table",
  "table_id": "table_0",
  "table_page": 42,
  "table_shape": {"rows": 10, "columns": 5}
}
```

**Large Table (> max_chunk_size):**
```
Original Table (5000 chars):
| Header1 | Header2 | Header3 |
|---------|---------|---------|
| Row 1 data...               |
| Row 2 data...               |
... (100 rows)

Split into:
Chunk 1 (Part 1):
| Header1 | Header2 | Header3 |  ← Header preserved
|---------|---------|---------|
| Row 1 data...               |
| Row 2 data...               |
... (rows 1-30)

Chunk 2 (Part 2):
| Header1 | Header2 | Header3 |  ← Header preserved
|---------|---------|---------|
| Row 31 data...              |
| Row 32 data...              |
... (rows 31-60)

Chunk 3 (Part 3):
| Header1 | Header2 | Header3 |  ← Header preserved
|---------|---------|---------|
| Row 61 data...              |
... (rows 61-100)
```

**Key Methods:**
- `create_table_chunks()` - Convert all tables to chunks
- `save_table_chunks()` - Save chunks to JSON file
- `process_tables_to_chunks()` - Complete pipeline (load → chunk → save)

**Chunk ID Offset:**
```python
chunk_id_offset = 10000  # Avoids collision with text chunks (0-1000)
```
- Text chunks: 0-999
- Table chunks: 10000+
- Ensures unique IDs when merging text and table chunks

**Header Preservation:**
```python
# First 2 lines + separator line constitute header
def _is_header_line(self, line: str, index: int) -> bool:
    return index < 2 or line.startswith('|---')
```

## Data Flow

```
Tables JSON (from conversion/)
    ↓
[TableLoader]
    ├→ Load JSON file
    ├→ Parse table metadata
    └→ Provide DataFrame access
    ↓
[TableChunker]
    ├→ Process each table
    ├→ Check size vs max_chunk_size
    ├→ Split large tables (preserving header)
    ├→ Create chunk with metadata
    └→ Assign chunk ID (10000+)
    ↓
[Output]
    └→ {company}_table_chunks.json
```

## Usage

### CLI Usage
```bash
# Create table chunks for specific company
python -m table_extraction.table_extractor --company grab

# Search tables before chunking
python -m table_extraction.table_extractor --company grab --search "balance sheet"

# Extract specific metrics
python -m table_extraction.table_extractor --company grab --metrics revenue ebitda assets

# Export tables to CSV
python -m table_extraction.table_extractor --company grab --export
```

### Programmatic Usage
```python
from table_extraction.table_extractor import NumericalExtractor
from config_loader import load_config

config = load_config()
config.set_company('grab')

extractor = NumericalExtractor(config)

# Complete pipeline: load tables → create chunks → save
result = extractor.process_tables_to_chunks()

print(f"Extracted {result['num_tables']} tables")
print(f"Created {result['num_chunks']} chunks")
print(f"Average chunk size: {result['avg_chunk_size']:.0f} chars")
print(f"Output: {result['output_path']}")
```

### Pipeline Integration
```python
# Called in main pipeline Step 4 (parallel with text chunking)
table_result = numerical_extractor.process_tables_to_chunks()
# Returns: {'num_tables': 145, 'num_chunks': 248, 'avg_chunk_size': 1523.5, 'output_path': Path}
```

## Output Format

### Table Chunks JSON Structure
```json
[
  {
    "chunk_id": 10000,
    "section_header": "Table 1 (Page 42): 10×5",
    "header_level": 0,
    "content": "| Column1 | Column2 | Column3 |\n|---------|---------|---------|...",
    "content_type": "table",
    "table_id": "table_0",
    "table_page": 42,
    "table_shape": {
      "rows": 10,
      "columns": 5
    }
  },
  {
    "chunk_id": 10001,
    "section_header": "Table 2 (Page 45): 50×8 (Part 1)",
    "header_level": 0,
    "content": "| Header1 | Header2 | ... |\n...",
    "content_type": "table",
    "table_id": "table_1",
    "table_page": 45,
    "table_shape": {
      "rows": 50,
      "columns": 8
    }
  },
  {
    "chunk_id": 10002,
    "section_header": "Table 2 (Page 45): 50×8 (Part 2)",
    "header_level": 0,
    "content": "| Header1 | Header2 | ... |\n...",
    "content_type": "table",
    "table_id": "table_1",
    "table_page": 45,
    "table_shape": {
      "rows": 50,
      "columns": 8
    }
  }
]
```

**Chunk Structure Fields:**
- `chunk_id` - Unique ID starting at 10000
- `section_header` - Descriptive header with page and shape
- `header_level` - Always 0 for tables
- `content` - Markdown table representation
- `content_type` - Always "table"
- `table_id` - Original table ID from tables JSON
- `table_page` - Page number where table appears
- `table_shape` - Original table dimensions (rows × columns)

## Configuration

Configured via `configs/config.yaml`:

```yaml
markdown_folder: "markdown_files"
output_folder: "outputs"

pdf_files:
  grab: "Grab 2024.pdf"
  # Company name used in output path: outputs/{company}/
```

**Max Chunk Size:**
```python
# Default in create_table_chunks()
max_chunk_size = 2000  # chars, matches text chunk max size
```

## Output Locations

```
outputs/
├── grab/
│   ├── grab_table_chunks.json     # 248 table chunks
│   └── grab_chunks.json           # (text chunks from extraction/)
├── sq/
│   └── sq_table_chunks.json       # 89 table chunks
└── ...
```

**Separate Files:**
- Text chunks: `{company}_chunks.json` (from extraction/)
- Table chunks: `{company}_table_chunks.json` (from table_extraction/)
- Later merged by: `chunking/merge_chunking/`

## Design Decisions

### Why Separate Table Chunks?

**Problem:** Tables have different structure than text chunks.
```
Text chunk: Paragraph with context
Table chunk: Structured data with rows/columns
```

**Solution:** Process tables separately, then merge.
1. **Better Formatting:** Preserve table structure in markdown
2. **Metadata:** Include table_id, page, shape for provenance
3. **Splitting Logic:** Split by rows (not paragraphs)
4. **Header Preservation:** Repeat headers in split chunks

### Why Start Chunk IDs at 10000?

**Problem:** Chunk ID collision when merging text and table chunks.
```
Text chunks: chunk_id 0, 1, 2, ..., 688
Table chunks: chunk_id 0, 1, 2, ..., 248
→ Collision when merged!
```

**Solution:** Offset table chunk IDs.
```
Text chunks: chunk_id 0, 1, 2, ..., 688
Table chunks: chunk_id 10000, 10001, 10002, ..., 10248
→ No collision when merged!
```

### Why Preserve Headers in Split Tables?

**Problem:** Split table loses context.
```
Chunk 1 (Part 1):
| Header1 | Header2 |
| Row 1   | Data 1  |

Chunk 2 (Part 2):
| Row 2   | Data 2  |  ← No headers! What are these columns?
```

**Solution:** Repeat headers in each chunk.
```
Chunk 1 (Part 1):
| Header1 | Header2 |
| Row 1   | Data 1  |

Chunk 2 (Part 2):
| Header1 | Header2 |  ← Headers preserved!
| Row 2   | Data 2  |
```

### Why Markdown Format for Tables?

**Advantages:**
1. **Human-Readable:** Easy to inspect chunks manually
2. **LLM-Friendly:** LLMs understand markdown tables well
3. **Embedding-Ready:** Can be embedded directly as text
4. **Preserves Structure:** Maintains row/column relationships

**Example:**
```markdown
| Segment | Revenue 2024 | Revenue 2023 | Growth % |
|---------|-------------|-------------|----------|
| Delivery | $1,234M     | $987M       | 25%      |
| Mobility | $678M       | $543M       | 25%      |
| Fintech  | $234M       | $123M       | 90%      |
```

## Table Statistics

| Company | Tables | Table Chunks | Avg Chunk Size | Largest Table (chunks) |
|---------|--------|--------------|----------------|------------------------|
| Grab    | 145    | 248          | 1524 chars     | 18 chunks              |
| SQ      | 89     | 142          | 1456 chars     | 12 chunks              |
| SEA     | 67     | 98           | 1389 chars     | 8 chunks               |

**Multi-Part Tables:**
- Tables exceeding max_chunk_size (2000 chars) are split
- Grab: ~40% of tables split into multiple chunks
- Large financial statements often split into 5-10 chunks

## Logging

Table extraction operations logged to `logs/logs_{timestamp}.log` with prefix `numerical_extraction`.

**Key Log Messages:**
- `"Loading tables from: {path}"` - Start
- `"Loaded X tables"` - Load success
- `"Creating chunks from X tables..."` - Chunking start
- `"✓ Created X table chunks from Y tables"` - Chunking complete
- `"✓ Saved X table chunks to: {path}"` - Save confirmation

## Error Handling

- **Missing Tables JSON:** Raises `FileNotFoundError` with clear message
- **No Tables Loaded:** Raises `ValueError` when trying to chunk before loading
- **Empty Tables:** Logs warning and skips empty tables
- **Invalid JSON:** Catches and logs JSON parsing errors

## Performance

| Company | Tables | Processing Time | Memory Usage |
|---------|--------|----------------|--------------|
| Grab    | 145    | ~2s            | ~50 MB       |
| SQ      | 89     | ~1.5s          | ~30 MB       |
| SEA     | 67     | ~1s            | ~20 MB       |

**Optimization:**
- Processes tables sequentially (deterministic order)
- Minimal string operations (efficient splitting)
- No LLM calls (pure algorithmic processing)

## Dependencies

- `pandas` - DataFrame manipulation and CSV export
- `json` - JSON loading and saving
- `pathlib` - Path handling
- `re` - Numerical value extraction
- `config_loader` - Configuration management

## Related Modules

- **Previous Step:** `conversion/` - Creates tables JSON (Pass 2)
- **Parallel Step:** `extraction/` - Text chunking (runs simultaneously)
- **Next Step:** `chunking/merge_chunking/` - Merge text + table chunks
- **Inputs from:** `markdown_files/{company}_tables.json`
- **Outputs to:** `outputs/{company}/{company}_table_chunks.json`

## Future Enhancements

- **Table Type Detection:** Classify tables (financial statement, metrics, etc.)
- **Column-Based Splitting:** Split very wide tables by columns
- **Table Summarization:** Generate text summary for each table
- **Numerical Extraction:** Automatic extraction of key financial metrics
- **Cross-Table Validation:** Check consistency of values across tables
