# Extraction Module

## Overview

Extracts and chunks markdown content with **hierarchical structure preservation** for RAG retrieval. Transforms flat markdown into structured chunks that maintain document hierarchy (sections, subsections).

## Architecture

```
MarkdownExtractor (Orchestrator)
├── MarkdownCleaner → Remove artifacts, normalize whitespace
├── StructureAnalyzer → Parse headers, build hierarchy
└── ContentChunker → Split content, create chunks
```

## Components

### 1. `extractor.py`
**Main orchestrator** for hierarchical markdown chunking.

**Processing Pipeline:**
1. **Clean Markdown** - Remove artifacts, normalize spacing
2. **Analyze Structure** - Find headers, build hierarchy
3. **Extract Preamble** - Content before first header (if substantial)
4. **Process Sections** - Chunk each section with hierarchy preserved
5. **Save Chunks** - Output hierarchical chunk JSON

**Key Methods:**
- `process_markdown_file()` - Complete pipeline (main entry point)
- `extract_hierarchical_chunks()` - Core chunking logic
- `clean_markdown_artifacts()` - Preprocessing step

**Configuration:**
```python
# From config.yaml chunking section
min_chunk_size: 200    # Minimum chunk size (chars)
max_chunk_size: 2000   # Maximum chunk size (chars)
```

### 2. `markdown_cleaner.py`
**Cleans and normalizes markdown text.**

**Cleaning Operations:**
- Remove `<!-- image -->` comments
- Remove `<!-- pagebreak -->` markers
- Remove empty markdown links `[]()`
- Normalize multiple newlines → double newline
- Collapse excessive whitespace

**Key Methods:**
- `clean_markdown_artifacts()` - Main cleaning function
- `_remove_image_comments()` - Strip image placeholders
- `_normalize_whitespace()` - Consistent spacing

**Example:**
```markdown
# Section<!-- image -->

Content   with    irregular     spacing


Too many newlines

# Next Section
```
↓ Becomes ↓
```markdown
# Section

Content with irregular spacing

Too many newlines

# Next Section
```

### 3. `structure_analyzer.py`
**Parses markdown structure and builds hierarchy.**

**Header Detection:**
```markdown
# Level 1
## Level 2
### Level 3
```

**Hierarchy Building:**
```python
# For: "Parent > Child > Grandchild > Current"
headers = [
    {'level': 1, 'text': 'Parent', 'start_pos': 0},
    {'level': 2, 'text': 'Child', 'start_pos': 100},
    {'level': 3, 'text': 'Grandchild', 'start_pos': 200},
    {'level': 3, 'text': 'Current', 'start_pos': 300}
]

# build_header_stack(headers, 3) returns:
"Parent > Child > Grandchild > Current"
```

**Key Methods:**
- `find_headers()` - Extract all headers with positions
- `build_header_stack()` - Generate full hierarchical path
- `get_section_content()` - Extract content between headers

**Section Content Extraction:**
- Gets text from current header to next header of same/higher level
- Handles nested sections correctly
- Excludes header text itself

### 4. `content_chunker.py`
**Splits content into size-appropriate chunks.**

**Chunking Strategy:**
```python
# For long content exceeding max_chunk_size:
1. Try splitting by paragraph (double newline)
2. If paragraphs too large, split by single newline
3. If still too large, force-split at max_chunk_size
```

**Chunk Structure:**
```json
{
  "chunk_id": 0,
  "section_header": "Business Overview > Financial Performance",
  "header_level": 2,
  "content": "Actual text content...",
  "content_type": "text",
  "is_table": false,
  "contains_numerical_data": false
}
```

**Key Methods:**
- `split_content()` - Split text into chunks respecting boundaries
- `create_chunk()` - Build single chunk with metadata
- `create_chunks_from_content()` - Process content list → chunk list

**Chunking Example:**
```
Content: 5000 characters
max_chunk_size: 2000

Split by paragraphs:
  - Paragraph 1: 1800 chars ✓ (< 2000)
  - Paragraph 2: 2400 chars ✗ (> 2000) → split by sentences
  - Paragraph 3: 1600 chars ✓ (< 2000)

Result: 4 chunks with hierarchical headers
```

## Data Flow

```
Markdown File
    ↓
[Clean Artifacts]
    ├→ Remove <!-- image -->
    ├→ Remove empty links
    └→ Normalize whitespace
    ↓
[Analyze Structure]
    ├→ Find all headers
    ├→ Build hierarchy
    └→ Map section boundaries
    ↓
[Extract Preamble]
    ├→ Content before first header
    └→ Only if ≥ min_chunk_size
    ↓
[Process Each Section]
    ├→ Get section content
    ├→ Check if ≥ min_chunk_size
    ├→ Split into chunks
    └→ Attach hierarchical header
    ↓
[Save Chunks]
    └→ {company}_chunks.json
```

## Usage

### CLI Usage
```bash
# Extract chunks for specific company
python -m extraction.extractor --company grab

# With custom markdown file
python -m extraction.extractor --company grab --markdown path/to/file.md

# With semantic merging (optional)
python -m extraction.extractor --company grab --semantic
```

### Programmatic Usage
```python
from extraction.extractor import MarkdownExtractor
from config_loader import load_config

config = load_config()
config.set_company('grab')

extractor = MarkdownExtractor(config)
result = extractor.process_markdown_file()

print(f"Extracted {result['num_chunks']} chunks")
print(f"Average chunk size: {result['avg_chunk_size']:.0f} chars")
print(f"Output: {result['chunks_path']}")
```

### Pipeline Integration
```python
# Called in main pipeline Step 3
extraction_result = extractor.process_markdown_file(markdown_path)
# Returns: {'chunks_path': Path, 'num_chunks': int, 'avg_chunk_size': float}
```

## Output Format

### Chunks JSON Structure
```json
[
  {
    "chunk_id": 0,
    "section_header": "Preamble",
    "header_level": 0,
    "content": "Executive summary content before first header...",
    "content_type": "text",
    "is_table": false,
    "contains_numerical_data": false
  },
  {
    "chunk_id": 1,
    "section_header": "Business Overview",
    "header_level": 1,
    "content": "The company operates in three segments...",
    "content_type": "text",
    "is_table": false,
    "contains_numerical_data": false
  },
  {
    "chunk_id": 2,
    "section_header": "Business Overview > Financial Performance",
    "header_level": 2,
    "content": "Revenue for FY2024 increased by 15%...",
    "content_type": "text",
    "is_table": false,
    "contains_numerical_data": false
  }
]
```

## Configuration

Configured via `configs/config.yaml`:

```yaml
chunking:
  min_chunk_size: 200      # Minimum viable chunk size
  max_chunk_size: 2000     # Maximum chunk size before splitting

# File paths
markdown_folder: "markdown_files"
output_folder: "outputs"
```

## Output Locations

```
outputs/
├── grab/
│   └── grab_chunks.json     # ~688 chunks
├── sq/
│   └── sq_chunks.json       # ~530 chunks
└── ...
```

## Design Decisions

### Why Hierarchical Structure?

**Problem:** Flat chunks lose context.
```
Chunk: "Revenue increased 15%"
Question: "Where?" "Which segment?"
```

**Solution:** Hierarchical headers provide context.
```
Chunk: "Business Overview > Asia Pacific > Revenue increased 15%"
Answer: Revenue increased 15% in Asia Pacific segment.
```

### Why Variable Chunk Sizes?

**Rigid Chunking:**
```
Chunk 1: "The company's primary strategy is to | [SPLIT]
Chunk 2: expand into emerging markets through..."
```
→ Breaks sentences mid-thought

**Adaptive Chunking:**
```
Chunk 1: "The company's primary strategy is to expand into emerging markets through strategic partnerships."
Chunk 2: "Market Entry Timeline: Q1 2024..."
```
→ Respects natural boundaries

### Chunk Size Parameters

**min_chunk_size: 200 chars**
- Filters out tiny sections (e.g., just a header with 1 sentence)
- Ensures chunks have substantial content for embedding

**max_chunk_size: 2000 chars**
- Embedding model sweet spot (~300 tokens)
- Large enough for context, small enough for precision
- Can still retrieve 10-20 chunks = 20K-40K chars of context

## Chunk Statistics

| Company | Pages | Markdown Size | Chunks | Avg Chunk Size | Processing Time |
|---------|-------|---------------|--------|----------------|-----------------|
| Grab    | 297   | 955 KB        | 688    | 1307 chars     | ~1s             |
| SQ      | 252   | 812 KB        | 530    | 1445 chars     | ~0.8s           |
| SEA     | 229   | 743 KB        | 498    | 1402 chars     | ~0.7s           |

## Hierarchical Header Examples

### Real Examples from Grab Annual Report:
```
"Preamble"
"Table of Contents"
"Risk Factors"
"Risk Factors > Risks Relating to Our Business"
"Risk Factors > Risks Relating to Our Business > Competitive Risks"
"Financial Statements"
"Financial Statements > Consolidated Balance Sheet"
"Financial Statements > Consolidated Balance Sheet > Assets"
```

### Benefits for Retrieval:
1. **Section Filtering:** Can boost/filter by section keywords
2. **Context Preservation:** LLM knows which section chunk came from
3. **Hierarchical Search:** Can search within specific report sections
4. **Better Prompts:** Can tell LLM "From the Risk Factors section..."

## Logging

Extraction operations logged to `logs/logs_{timestamp}.log` with prefix `extraction`.

**Key Log Messages:**
- `"Extracting hierarchical chunks..."` - Start
- `"Extracted X chunks with hierarchical structure"` - Success
- `"Processing: Parent > Child > Current (Level 3)"` - Section processing
- `"✓ Saved X chunks to: {path}"` - Output confirmation

## Error Handling

- **Missing Markdown:** Raises `FileNotFoundError`
- **No Headers Found:** Creates single "Document" chunk from all content
- **Empty Sections:** Skips sections < min_chunk_size
- **Oversized Content:** Force-splits at max_chunk_size as last resort

## Performance Optimization

1. **Minimal Regex:** Uses simple string operations where possible
2. **Single Pass:** One pass through markdown for header detection
3. **Lazy Splitting:** Only splits content when exceeding max size
4. **No LLM Calls:** Pure algorithmic chunking (fast, deterministic)

## Dependencies

- `pathlib` - Path handling
- `json` - Chunk serialization
- `re` - Header pattern matching
- `config_loader` - Configuration management

## Related Modules

- **Previous Step:** `conversion/` - Markdown generation
- **Next Step:** `table_extraction/` - Table chunks (parallel)
- **Then:** `chunking/merge_chunking/` - Merge text + table chunks
- **Outputs to:** `outputs/{company}/{company}_chunks.json`

## Future Enhancements

- **Semantic Boundary Detection:** Use embeddings to find better split points
- **List Handling:** Special handling for bulleted/numbered lists
- **Table Detection:** Flag chunks containing inline tables
- **Overlap:** Add configurable chunk overlap for context continuity
