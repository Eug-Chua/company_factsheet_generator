# Table Extraction Module

## Overview

Converts structured tables from PDF extraction into **RAG-ready chunks** for retrieval. Takes table JSON output from the conversion module (Pass 2) and creates markdown-formatted chunks with metadata, enabling semantic search over financial tables.

## Architecture

```
NumericalExtractor (Initializer)
├── loader (TableLoader) → Load tables from JSON
└── chunker (TableChunker) → Convert tables to RAG-ready chunks

Usage:
extractor.chunker.process_tables_to_chunks()
```

## Components

### 1. `table_extractor.py`
**Lightweight orchestrator** that initializes table processing components.

**Key Responsibilities:**
- Initialize and expose two specialized components: `loader`, `chunker`
- Components are accessed directly (no wrapper methods)

**Public Components:**
- `loader` - TableLoader instance for loading tables from JSON
- `chunker` - TableChunker instance for converting tables to chunks

**Design Note:** Direct component access (no wrappers) reduces indirection and makes the code more maintainable.

### 2. `table_loader.py`
**Loads table data from JSON files.**

**Key Responsibilities:**
- Load tables JSON from conversion output
- Store tables data for chunker to process

**Table JSON Structure (Input):**
```json
{
  "table_0": {
    "dataframe": [
      {"Col1": "val1", "Col2": "val2"},
      {"Col1": "val3", "Col2": "val4"}
    ],
    "markdown": "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |\n| val3 | val4 |",
    "shape": {"rows": 2, "columns": 2},
    "location": {"page": 3}
  },
  "table_1": {...}
}
```

**Key Methods:**
- `load_tables()` - Load tables from JSON file

**Auto-Detection:**
```python
# Auto-detects tables file based on markdown filename
# For: "Grab 2024.md" → looks for "Grab 2024_tables.json"
tables_path = self._auto_detect_tables_path()
```

### 3. `table_chunker.py`
**Converts tables to RAG-ready chunks.**

**Key Responsibilities:**
- Convert tables to markdown-formatted chunks
- Handle large tables by splitting into multiple chunks
- Preserve table headers across split chunks
- Generate sequential chunk IDs (starting at 0)

**Chunking Strategy:**

**Small Table (≤ max_chunk_size):**
```json
{
  "chunk_id": 0,
  "section_header": "Table 1 (Page 42): 10×5",
  "header_level": 0,
  "content": "| Col1 | Col2 |\n|------|------|\n| val1 | val2 |",
  "content_type": "table"
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
- `create_table_chunks()` - Convert all tables to chunks (IDs start at 0)
- `save_table_chunks()` - Save chunks to JSON file
- `process_tables_to_chunks()` - Complete pipeline (load → chunk → save)

**Chunk ID Management:**
- Table chunks are created with IDs starting at 0
- During merge (in `chunking/merge_chunking/`), IDs are renumbered sequentially:
  - Text chunks: 0, 1, 2, ..., N
  - Table chunks: N+1, N+2, N+3, ...
- This ensures unique sequential IDs across all chunks

**Header Preservation:**
- First 2 lines + separator line (|---|) constitute the header
- When splitting large tables, each chunk gets a complete header
- This preserves column context in every chunk part

## Data Flow

```
Tables JSON (from conversion/)
    ↓
[NumericalExtractor.loader]
    ├→ Load JSON file
    ├→ Parse table metadata
    └→ Provide DataFrame access
    ↓
[NumericalExtractor.chunker]
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

### Programmatic Usage
```python
from table_extraction.table_extractor import NumericalExtractor
from config_loader import load_config

config = load_config()
config.set_company('grab')

extractor = NumericalExtractor(config)

# Complete pipeline: load tables → create chunks → save
result = extractor.chunker.process_tables_to_chunks()
print(f"Extracted {result['num_tables']} tables")
print(f"Created {result['num_chunks']} chunks")
print(f"Average chunk size: {result['avg_chunk_size']:.0f} chars")
print(f"Output: {result['output_path']}")
```

### Pipeline Integration
```python
# Called in main pipeline Step 4 (parallel with text chunking)
table_result = numerical_extractor.chunker.process_tables_to_chunks()
# Returns: {'num_tables': 145, 'num_chunks': 248, 'avg_chunk_size': 1523.5, 'output_path': Path}
```

## Output Format

### Table Chunks JSON Structure
```json
[
  {
    "chunk_id": 0,
    "section_header": "Table 1 (Page 42): 10×5",
    "header_level": 0,
    "content": "| Column1 | Column2 | Column3 |\n|---------|---------|---------|...",
    "content_type": "table"
  },
  {
    "chunk_id": 1,
    "section_header": "Table 2 (Page 45): 50×8 (Part 1)",
    "header_level": 0,
    "content": "| Header1 | Header2 | ... |\n...",
    "content_type": "table"
  },
  {
    "chunk_id": 2,
    "section_header": "Table 2 (Page 45): 50×8 (Part 2)",
    "header_level": 0,
    "content": "| Header1 | Header2 | ... |\n...",
    "content_type": "table"
  }
]
```

**Chunk Structure Fields:**
- `chunk_id` - Sequential ID starting at 0 (renumbered during merge)
- `section_header` - Descriptive header with page and shape (e.g., "Table 1 (Page 42): 10×5")
- `header_level` - Always 0 for tables
- `content` - Markdown table representation
- `content_type` - Always "table"

**Note:** Page and shape information are embedded in the `section_header` field for display purposes. The original table metadata (table_id, page, shape) is not stored in chunks as it's not needed for retrieval or generation.

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
2. **Context in Headers:** Include page and shape info in section_header for readability
3. **Splitting Logic:** Split by rows (not paragraphs)
4. **Header Preservation:** Repeat headers in split chunks

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

Table extraction operations logged to `logs/logs_{num}.log` with prefix `numerical_extraction`.

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

- `pandas` - DataFrame manipulation
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
