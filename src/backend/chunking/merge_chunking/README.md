# Merge Chunking Module

## Overview

Combines text chunks and table chunks into a **unified chunk set** for comprehensive RAG retrieval. Ensures no chunk ID collisions, adds content type metadata, and produces a single JSON file containing both textual and tabular content.

## Architecture

```
ChunkMerger (Orchestrator)
├── ChunkLoader → Load text and table chunks from JSON files
├── ChunkProcessor → Merge chunks, renumber IDs, add metadata
├── ChunkSaver → Save merged chunks to JSON
└── ChunkStatistics → Calculate and log merge statistics
```

## Components

### 1. `chunk_merger.py`
**Main orchestrator** for merging text and table chunks.

**Key Responsibilities:**
- Coordinate loading, processing, and saving of chunks
- Resolve default paths for text and table chunks
- Calculate merge statistics

**Key Methods:**
- `run()` - Execute complete merge pipeline (main entry point)
- `_resolve_merge_paths()` - Auto-detect chunk file paths
- `_merge_and_save()` - Merge chunks and save to file
- `_finalize_merge_stats()` - Calculate and log statistics

**Usage:**
```python
from chunking.merge_chunking.chunk_merger import ChunkMerger
from config_loader import load_config

config = load_config()
config.set_company('grab')

merger = ChunkMerger(config)
result = merger.run()

# Returns:
{
    'total_chunks': 936,
    'text_chunks': 688,
    'table_chunks': 248,
    'text_avg_size': 1307,
    'table_avg_size': 1524,
    'overall_avg_size': 1365,
    'output_path': Path('outputs/grab/grab_chunks_merged.json')
}
```

### 2. `chunk_loader.py`
**Loads chunks from JSON files.**

**Key Responsibilities:**
- Validate chunk file paths exist
- Read and parse JSON chunk files
- Log loading progress

**Key Methods:**
- `load_chunks()` - Load chunks from JSON file

**Example:**
```python
loader = ChunkLoader(logger)
text_chunks = loader.load_chunks(Path('outputs/grab/grab_chunks.json'))
# Returns: List[Dict] with 688 text chunks
```

### 3. `chunk_processor.py`
**Processes and merges chunks with conflict resolution.**

**Key Responsibilities:**
- Merge text and table chunks into single list
- Renumber chunk IDs to avoid collisions
- Add content_type metadata to chunks
- Handle missing table chunks gracefully

**Key Methods:**
- `merge_chunks()` - Main merge logic
- `_renumber_chunk_ids()` - Ensure unique IDs
- `_add_content_type_to_chunks()` - Add metadata

**Content Type Metadata:**
```python
# Before merge:
Text chunks: chunk_id 0, 1, 2, ..., 687
Table chunks: chunk_id 688, 689, 670, ..., 770

# After merge: Combined list
[
    {'chunk_id': 0, 'content_type': 'text', ...},
    {'chunk_id': 1, 'content_type': 'text', ...},
    ...
    {'chunk_id': 687, 'content_type': 'text', ...},
    {'chunk_id': 688, 'content_type': 'table', ...},
    {'chunk_id': 689, 'content_type': 'table', ...},
    ...
]
```

**Missing Table Chunks:**
```python
# If table_chunks.json doesn't exist, still works
if not table_chunks_path.exists():
    logger.warning("No table chunks found, using text chunks only")
    return text_chunks  # Just text chunks with content_type added
```

### 4. `chunk_saver.py`
**Saves merged chunks to JSON file.**

**Key Responsibilities:**
- Determine output path for merged chunks
- Create output directories if needed
- Write merged chunks to JSON with proper formatting

**Key Methods:**
- `save_merged_chunks()` - Save chunks to JSON file
- `_get_default_merged_output_path()` - Get default output path
- `_prepare_merged_output_path()` - Resolve and create output path

**Output Path Resolution:**
```python
# Default: outputs/{company}/{company}_chunks_merged.json
output_path = config.output_dir / f"{config.company_name}_chunks_merged.json"
# Example: outputs/grab/grab_chunks_merged.json
```

**JSON Formatting:**
```python
# indent=2 for readability, ensure_ascii=False for Unicode support
json.dump(chunks, f, indent=2, ensure_ascii=False)
```

### 5. `chunk_statistics.py`
**Calculates and logs merge statistics.**

**Key Responsibilities:**
- Calculate total, text, and table chunk counts
- Calculate average chunk sizes by type
- Log formatted summary to console and logs

**Key Methods:**
- `get_merge_statistics()` - Calculate statistics
- `log_merge_summary()` - Log formatted summary

**Statistics Calculated:**
```python
{
    'total_chunks': 936,           # Total merged chunks
    'text_chunks': 688,            # Number of text chunks
    'table_chunks': 248,           # Number of table chunks
    'text_avg_size': 1307,         # Average text chunk size (chars)
    'table_avg_size': 1524,        # Average table chunk size (chars)
    'overall_avg_size': 1365,      # Overall average (chars)
    'output_path': Path('...')     # Output file location
}
```

**Log Output:**
```
============================================================
Merge Summary for grab
============================================================
  Text chunks: 688 (avg 1307 chars)
  Table chunks: 248 (avg 1524 chars)
  Total chunks: 936 (avg 1365 chars)
  Output: outputs/grab/grab_chunks_merged.json
============================================================
```

## Data Flow

```
Text Chunks JSON          Table Chunks JSON
(from extraction/)        (from table_extraction/)
    ↓                          ↓
[ChunkLoader]              [ChunkLoader]
    ├→ Load 688 chunks         ├→ Load 248 chunks
    └→ Validate                └→ Validate
    ↓                          ↓
[ChunkProcessor]
    ├→ Add content_type='text' to all text chunks
    ├→ Add content_type='table' to all table chunks
    ├→ Renumber IDs (text: 0-687, table: 688-990)
    └→ Combine into single list
    ↓
[ChunkSaver]
    ├→ Create output directory
    ├→ Write merged chunks JSON
    └→ Log save confirmation
    ↓
[ChunkStatistics]
    ├→ Calculate chunk counts
    ├→ Calculate average sizes
    └→ Log formatted summary
    ↓
[Output]
    └→ {company}_chunks_merged.json
```

## Usage

### Programmatic Usage
```python
from chunking.merge_chunking.chunk_merger import ChunkMerger
from config_loader import load_config

config = load_config()
config.set_company('grab')

merger = ChunkMerger(config)
result = merger.run()

print(f"Merged {result['total_chunks']} chunks:")
print(f"  {result['text_chunks']} text chunks")
print(f"  {result['table_chunks']} table chunks")
print(f"  Output: {result['output_path']}")
```

### Pipeline Integration
```python
# Called in main pipeline Step 5 (after text and table chunking)
merge_result = chunk_merger.run(
    text_chunks_path=text_result['chunks_path'],
    table_chunks_path=table_result['output_path']
)
# Returns: {'total_chunks': 936, 'text_chunks': 688, 'table_chunks': 248, ...}
```

## Output Format

### Merged Chunks JSON Structure
```json
[
  {
    "chunk_id": 0,
    "section_header": "Preamble",
    "header_level": 0,
    "content": "Executive summary content...",
    "content_type": "text"
  },
  {
    "chunk_id": 1,
    "section_header": "Business Overview",
    "header_level": 1,
    "content": "The company operates in three segments...",
    "content_type": "text"
  },
  ...
  {
    "chunk_id": 687,
    "section_header": "Risk Factors > Regulatory Risks",
    "header_level": 2,
    "content": "Changes in regulatory environment...",
    "content_type": "text"
  },
  {
    "chunk_id": 688,
    "section_header": "Table 1 (Page 42): 10×5",
    "header_level": 0,
    "content": "| Column1 | Column2 | Column3 |\n|---------|---------|---------|...",
    "content_type": "table"
  },
  {
    "chunk_id": 689,
    "section_header": "Table 2 (Page 45): 50×8 (Part 1)",
    "header_level": 0,
    "content": "| Header1 | Header2 | ... |\n...",
    "content_type": "table"
  }
]
```

**Key Features:**
- **Unified Structure:** All chunks have same base fields
- **Content Type Metadata:** `content_type` field distinguishes text vs table
- **Additional Metadata:** Tables retain table_id, table_page, table_shape

## Configuration

Configured via `configs/config.yaml`:

```yaml
output_folder: "outputs"

pdf_files:
  grab: "Grab 2024.pdf"
  # Company name used in output path: outputs/{company}/
```

**Input Paths (Auto-Detected):**
```python
# Text chunks path
text_chunks_path = config.chunks_path
# Example: outputs/grab/grab_chunks.json

# Table chunks path
table_chunks_path = config.output_dir / f"{config.company_name}_table_chunks.json"
# Example: outputs/grab/grab_table_chunks.json
```

**Output Path:**
```python
# Merged chunks path
output_path = config.output_dir / f"{config.company_name}_chunks_merged.json"
# Example: outputs/grab/grab_chunks_merged.json
```

## Output Locations

```
outputs/
├── grab/
│   ├── grab_chunks.json           # Text chunks (688)
│   ├── grab_table_chunks.json     # Table chunks (248)
│   └── grab_chunks_merged.json    # ✓ Merged chunks (936)
├── sq/
│   ├── sq_chunks.json             # Text chunks (530)
│   ├── sq_table_chunks.json       # Table chunks (142)
│   └── sq_chunks_merged.json      # ✓ Merged chunks (672)
└── ...
```

## Design Decisions

### Why Merge Text and Table Chunks?

**Problem:** Separate chunk files require two retrieval passes.
```
Query: "What is the company's total revenue?"

Without merge:
1. Search text_chunks.json → finds narrative about revenue
2. Search table_chunks.json → finds revenue table
3. Combine results → return to LLM

With merge:
1. Search chunks_merged.json → finds both narrative and table
2. Return to LLM
```

**Solution:** Single unified chunk file for simpler retrieval.

**Benefits:**
1. **Simpler Retrieval:** One search instead of two
2. **Better Ranking:** Can compare text vs table relevance directly
3. **Unified Format:** All chunks have same structure
4. **Easier Embedding:** Embed all chunks together


### Why Add content_type Metadata?

**Problem:** Can't tell if chunk is text or table from structure alone.

**Solution:** Add explicit `content_type` field.
```python
{'chunk_id': 0, 'content_type': 'text', ...}
{'chunk_id': 10000, 'content_type': 'table', ...}
```

**Benefits:**
1. **Explicit Type:** No ambiguity about chunk type
2. **Easy Filtering:** Filter by content_type
3. **Analytics:** Track text vs table retrieval separately
4. **Future-Proof:** Can add more content types (e.g., 'image', 'chart')

### Why Handle Missing Table Chunks Gracefully?

**Problem:** Not all documents have tables.

**Solution:** Continue with text chunks only if table chunks missing.
```python
if not table_chunks_path.exists():
    logger.warning("No table chunks found, using text chunks only")
    return text_chunks
```

**Benefits:**
1. **Robustness:** Doesn't fail if tables missing
2. **Flexibility:** Works with text-only documents
3. **Clear Logging:** Warns user about missing tables

## Merge Statistics

| Company | Text Chunks | Table Chunks | Total Chunks | Text Avg | Table Avg | Overall Avg |
|---------|-------------|--------------|--------------|----------|-----------|-------------|
| Grab    | 688         | 248          | 936          | 1307     | 1524      | 1365        |
| SQ      | 530         | 142          | 672          | 1445     | 1456      | 1448        |
| SEA     | 498         | 98           | 596          | 1402     | 1389      | 1398        |

**Observations:**
- Table chunks typically 10-20% larger than text chunks
- ~26-36% of total chunks are tables
- Financial reports are table-heavy documents

## Logging

Merge operations logged to `logs/logs_{num}.log` with prefix `chunk_merger`.

**Key Log Messages:**
- `"Loaded X chunks from {filename}"` - Load confirmation (2x, text + table)
- `"Merged chunks: X text + Y table = Z total"` - Merge confirmation
- `"✓ Saved X merged chunks to: {path}"` - Save confirmation
- `"============================================================"` - Summary header
- `"Merge Summary for {company}"` - Summary section
- `"  Text chunks: X (avg Y chars)"` - Text statistics
- `"  Table chunks: X (avg Y chars)"` - Table statistics
- `"  Total chunks: X (avg Y chars)"` - Overall statistics

## Error Handling

- **Missing Text Chunks:** Raises `FileNotFoundError` with clear message
- **Missing Table Chunks:** Logs warning and continues with text chunks only
- **Empty Chunks:** Handles empty lists gracefully (no division by zero)
- **Invalid JSON:** Catches and logs JSON parsing errors

## Dependencies

- `json` - JSON loading and saving
- `pathlib` - Path handling
- `config_loader` - Configuration management
- No external libraries required (stdlib only!)

## Related Modules

- **Previous Steps:**
  - `extraction/` - Creates text chunks
  - `table_extraction/` - Creates table chunks
- **Next Step:**
  - `chunking/semantic_chunking/` - Optional semantic merging
  - `generation/` - Factsheet generation with RAG
- **Inputs from:**
  - `outputs/{company}/{company}_chunks.json`
  - `outputs/{company}/{company}_table_chunks.json`
- **Outputs to:**
  - `outputs/{company}/{company}_chunks_merged.json`

## Future Enhancements

- **Chunk Deduplication:** Detect and remove duplicate chunks
- **Smart Interleaving:** Interleave text and table chunks by page number
- **Metadata Enrichment:** Add page numbers, source files, timestamps
- **Validation:** Check for chunk ID collisions, missing fields
- **Compression:** Optionally compress large merged files
