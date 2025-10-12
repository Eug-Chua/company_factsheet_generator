# Semantic Chunking Module

## Overview

Applies **semantic similarity-based merging** to adjacent chunks using OpenAI embeddings. Reduces chunk count by intelligently combining semantically related chunks while preserving table/text boundaries and respecting size constraints. Results in fewer, more coherent chunks that improve RAG retrieval quality.

## Architecture

```
SemanticChunker (Orchestrator)
├── SemanticLoader → Load chunks and table metadata
├── TableDetector → Detect and annotate table chunks
├── Embedder → Generate OpenAI embeddings
├── MergeStrategy → Determine merge decisions
└── SemanticStatistics → Calculate merge statistics
```

## Components

### 1. `semantic_chunker.py`
**Main orchestrator** for semantic merging pipeline.

**Key Responsibilities:**
- Initialize OpenAI client and embedding model
- Coordinate semantic merging components
- Process chunks through merge pipeline
- Save merged chunks and generate statistics

**Key Methods:**
- `process_markdown()` - Complete pipeline: Markdown → Basic Chunks → Semantic Merging
- `merge_chunks()` - Load chunks from file and apply semantic merging
- `_merge_similar_chunks()` - Core merging logic

**Configuration:**
```python
similarity_threshold: 0.60   # Cosine similarity threshold for merging
max_merged_size: 4000       # Maximum size of merged chunk (chars)
embedding_model: "text-embedding-3-small"  # OpenAI model
```

**Usage:**
```python
from chunking.semantic_chunking.semantic_chunker import SemanticChunker
from config_loader import load_config

config = load_config()
config.set_company('grab')

chunker = SemanticChunker(
    config=config,
    similarity_threshold=0.60,
    max_merged_size=4000
)

# Option 1: From existing chunks file
result = chunker.merge_chunks(chunks_path)

# Option 2: Complete pipeline from markdown
result = chunker.process_markdown(markdown_path)

print(f"Merged {result['original_chunks']} → {result['num_chunks']} chunks")
print(f"Reduction: {result['reduction_pct']:.1f}%")
print(f"Average size: {result['avg_chunk_size']} chars")
```

### 2. `semantic_loader.py`
**Loads chunks and table metadata for semantic processing.**

**Key Responsibilities:**
- Load chunks from JSON file
- Load companion tables JSON for table detection
- Save semantic-merged chunks to output file
- Handle multiple table data file locations

**Key Methods:**
- `load_chunks_file()` - Load and annotate chunks with table info
- `save_merged_chunks()` - Save merged chunks to file

**Table Data Loading:**
```python
# Primary path (from conversion/)
markdown_files/{company}_tables.json

# Alternate path (same directory as chunks)
outputs/{company}/{company}_tables.json

# Loads and passes to TableDetector for annotation
```

**Output Path Generation:**
```python
# Input: outputs/grab/grab_chunks.json
# Output: outputs/grab/grab_chunks_semantic.json

# Input: outputs/grab/grab_chunks_merged.json
# Output: outputs/grab/grab_chunks_merged_semantic.json
```

### 3. `table_detector.py`
**Detects and annotates chunks containing table data.**

**Key Responsibilities:**
- Detect markdown tables via pipe patterns
- Identify numeric-heavy content
- Annotate chunks with `is_table` and `contains_numerical_data` flags

**Detection Heuristics:**
```python
# Heuristic 1: Markdown table pattern
table_pattern = r'\|[\s\-]+\|[\s\-]+\|'
# Matches: "| ----- | ----- |" (table separator)

# Heuristic 2: Many pipe characters
content.count('|') > 10  # Likely a table

# Heuristic 3: Numeric density
numbers = re.findall(r'\d+[,.\d]*', content)
numeric_density = len(numbers) / len(content.split())
numeric_density > 0.15  # 15%+ numeric tokens

# Combined: is_table = has_marker OR (many_pipes AND numeric_heavy)
```

**Annotation:**
```python
# Before:
{'chunk_id': 42, 'content': '| Revenue | 2024 | ...\n', ...}

# After:
{
    'chunk_id': 42,
    'content': '| Revenue | 2024 | ...\n',
    'is_table': True,
    'contains_numerical_data': True,
    ...
}
```

### 4. `embedder.py`
**Handles OpenAI embeddings and similarity calculations.**

**Key Responsibilities:**
- Generate embeddings using OpenAI API
- Batch processing for efficiency
- Calculate cosine similarity between embeddings
- Handle text truncation for token limits

**Key Methods:**
- `embed_chunks()` - Embed all chunks in batches
- `cosine_similarity()` - Calculate similarity between vectors

**Batch Embedding:**
```python
# Process chunks in batches of 100
batch_size = 100
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    batch_texts = [chunk['content'] for chunk in batch]

    # OpenAI API call (batched for efficiency)
    response = client.embeddings.create(
        input=batch_texts,
        model="text-embedding-3-small"
    )

    embeddings.extend([np.array(item.embedding) for item in response.data])
```

**Text Truncation:**
```python
max_chars = 30000  # ~7500 tokens (with buffer)
text = text[:max_chars] if len(text) > max_chars else text
```

**Cosine Similarity:**
```python
# Formula: cos(θ) = (A · B) / (||A|| × ||B||)
dot_product = np.dot(vec1, vec2)
norm1 = np.linalg.norm(vec1)
norm2 = np.linalg.norm(vec2)
similarity = dot_product / (norm1 * norm2)
# Returns: 0.0 to 1.0 (1.0 = identical, 0.0 = orthogonal)
```

### 5. `merge_strategy.py`
**Determines merge decisions based on similarity and constraints.**

**Key Responsibilities:**
- Evaluate merge eligibility (similarity, size, type)
- Merge chunks while preserving metadata
- Track merge provenance
- Handle merge chains (merging multiple chunks sequentially)

**Key Methods:**
- `should_merge()` - Decide if two chunks should merge
- `merge_chunks()` - Merge two chunks into one
- `merge_chain()` - Merge chain of similar chunks

**Merge Decision Logic:**
```python
def should_merge(chunk1, chunk2, similarity):
    # Rule 1: Similarity threshold
    if similarity < self.similarity_threshold:
        return False  # Not similar enough

    # Rule 2: Table/non-table mismatch
    if chunk1['is_table'] != chunk2['is_table']:
        return False  # Never merge table with non-table

    # Rule 3: Stricter threshold for tables
    if chunk1['is_table'] and chunk2['is_table']:
        table_threshold = min(threshold + 0.10, 0.95)
        if similarity < table_threshold:
            return False  # Tables need higher similarity

    # Rule 4: Size constraint
    combined_size = len(chunk1['content']) + len(chunk2['content'])
    if combined_size > self.max_merged_size:
        return False  # Would exceed size limit

    return True  # All checks passed, merge!
```

**Merge Chain Example:**
```python
# Start with chunk i
chunks = [A, B, C, D, E]
embeddings = [emb_A, emb_B, emb_C, emb_D, emb_E]
i = 0  # Start at A

# Check A vs B: similarity = 0.75 → MERGE
merged_AB = merge_chunks(A, B)
merged_emb_AB = (emb_A + emb_B) / 2

# Check AB vs C: similarity = 0.68 → MERGE
merged_ABC = merge_chunks(merged_AB, C)
merged_emb_ABC = (merged_emb_AB + emb_C) / 2

# Check ABC vs D: similarity = 0.45 → STOP (below threshold)
# Return: merged_ABC, next_i=3 (continue from D)

# Result: [ABC, D, E] (reduced from 5 to 3 chunks)
```

**Merged Chunk Structure:**
```json
{
  "chunk_id": 0,
  "section_header": "Business Overview + Financial Performance",
  "header_level": 1,
  "content": "Business overview text...\n\nFinancial performance details...",
  "merged": true,
  "merged_from": [0, 1],
  "is_table": false,
  "contains_numerical_data": false
}
```

### 6. `semantic_statistics.py`
**Calculates and logs merge statistics.**

**Key Responsibilities:**
- Calculate chunk reduction metrics
- Calculate average chunk sizes
- Log formatted merge summary

**Key Methods:**
- `calculate_chunk_stats()` - Calculate statistics
- `log_merge_summary()` - Log merge summary

**Statistics Calculated:**
```python
{
    'num_chunks': 456,              # Final chunk count
    'original_chunks': 688,         # Original chunk count
    'reduction_pct': 33.7,          # Reduction percentage
    'avg_chunk_size': 2134,         # Average size after merge
    'output_path': Path('...')      # Output file path
}
```

**Log Output:**
```
============================================================
Starting semantic merging on 688 chunks
============================================================

Embedding 688 chunks in batches...
  Embedded 100/688 chunks
  Embedded 200/688 chunks
  ...
  Embedded 688/688 chunks
✓ Completed embedding 688 chunks

Merging (similarity=0.753): [Business Overview...] + [Financial Performance...]
Merging (similarity=0.681): [Risk Factors...] + [Risk Management...]
...

============================================================
Semantic merging complete
============================================================
  Original chunks: 688
  Merged chunks: 456
  Merges performed: 232
  Reduction: 33.7%
============================================================
```

## Data Flow

```
Basic Chunks JSON
(from extraction/ or merge_chunking/)
    ↓
[SemanticLoader]
    ├→ Load chunks
    ├→ Load table metadata
    └→ Annotate with table detection
    ↓
[Embedder]
    ├→ Batch embed chunks (100 at a time)
    ├→ Generate embeddings via OpenAI API
    └→ Return embedding vectors
    ↓
[MergeStrategy]
    ├→ For each chunk i:
    │   ├→ Calculate similarity with chunk i+1
    │   ├→ Check merge criteria
    │   ├→ If eligible, merge and continue chain
    │   └→ If not, move to next chunk
    └→ Renumber merged chunks
    ↓
[SemanticLoader]
    ├→ Save merged chunks
    └→ Generate output path
    ↓
[SemanticStatistics]
    ├→ Calculate statistics
    └→ Log summary
    ↓
[Output]
    └→ {company}_chunks_semantic.json
```

## Usage

### CLI Usage
```bash
# Semantic merge from chunks file
python -m chunking.semantic_chunking.semantic_chunker \
    --chunks outputs/grab/grab_chunks.json \
    --threshold 0.70 \
    --max-size 3000

# Custom output path
python -m chunking.semantic_chunking.semantic_chunker \
    --chunks outputs/grab/grab_chunks.json \
    --output outputs/grab/grab_chunks_semantic_custom.json
```

### Programmatic Usage
```python
from chunking.semantic_chunking.semantic_chunker import SemanticChunker
from pathlib import Path

# Initialize with custom parameters
chunker = SemanticChunker(
    similarity_threshold=0.70,    # Higher threshold = fewer merges
    max_merged_size=3000          # Smaller max = shorter chunks
)

# Merge chunks from file
result = chunker.merge_chunks(
    chunks_path=Path('outputs/grab/grab_chunks.json')
)

print(f"Reduced {result['original_chunks']} → {result['num_chunks']} chunks")
print(f"Average chunk size: {result['avg_chunk_size']} chars")
```

### Pipeline Integration
```python
# Optional step after basic chunking (Step 3) or merge chunking (Step 5)

# Option 1: After basic text chunking
extraction_result = extractor.process_markdown_file()
semantic_result = semantic_chunker.merge_chunks(extraction_result['chunks_path'])

# Option 2: After text + table merge
merge_result = chunk_merger.process_and_merge()
semantic_result = semantic_chunker.merge_chunks(merge_result['output_path'])

# semantic_result: {'num_chunks': 456, 'reduction_pct': 33.7, ...}
```

## Output Format

### Semantic Merged Chunks JSON
```json
[
  {
    "chunk_id": 0,
    "section_header": "Preamble",
    "header_level": 0,
    "content": "Executive summary content...",
    "merged": false,
    "merged_from": [0],
    "is_table": false,
    "contains_numerical_data": false
  },
  {
    "chunk_id": 1,
    "section_header": "Business Overview + Financial Performance + Market Position",
    "header_level": 1,
    "content": "Business overview text...\n\nFinancial performance...\n\nMarket position...",
    "merged": true,
    "merged_from": [1, 2, 3],
    "is_table": false,
    "contains_numerical_data": false
  },
  {
    "chunk_id": 2,
    "section_header": "Table 1 (Page 42): 10×5",
    "header_level": 0,
    "content": "| Column1 | Column2 | Column3 |\n...",
    "merged": false,
    "merged_from": [10000],
    "is_table": true,
    "contains_numerical_data": true,
    "table_id": "table_0",
    "table_page": 42,
    "table_shape": {"rows": 10, "columns": 5}
  }
]
```

**New Fields:**
- `merged` - Boolean indicating if chunk was merged
- `merged_from` - List of original chunk IDs that were merged
- `is_table` - Boolean indicating table content
- `contains_numerical_data` - Boolean indicating numerical data

## Configuration

### Environment Variables
```bash
# Required: OpenAI API key
OPENAI_API_KEY=sk-...
```

### Parameters
```python
# Semantic chunking parameters
similarity_threshold: 0.60     # Cosine similarity threshold (0.0-1.0)
max_merged_size: 4000          # Maximum merged chunk size (chars)
embedding_model: "text-embedding-3-small"  # OpenAI embedding model
```

### Tuning Guidelines

**Similarity Threshold:**
- `0.50-0.60` - Aggressive merging (more reduction, risk of merging dissimilar)
- `0.60-0.70` - Balanced (default, good trade-off)
- `0.70-0.80` - Conservative (fewer merges, preserve distinctness)
- `0.80+` - Very conservative (minimal merging, near-identical only)

**Max Merged Size:**
- `2000-3000` - Smaller chunks (better precision, more chunks)
- `3000-4000` - Balanced (default, good for most documents)
- `4000-6000` - Larger chunks (better context, fewer chunks)
- `6000+` - Very large (risk of exceeding embedding limits)

**Table Threshold Boost:**
```python
# Tables always get +0.10 similarity threshold
table_threshold = min(similarity_threshold + 0.10, 0.95)
# Example: If threshold=0.60, tables require 0.70
```

## Output Locations

```
outputs/
├── grab/
│   ├── grab_chunks.json                  # Basic chunks (688)
│   ├── grab_chunks_semantic.json         # ✓ Semantic merged (456)
│   ├── grab_chunks_merged.json           # Text + table merged (936)
│   └── grab_chunks_merged_semantic.json  # ✓ Fully merged + semantic (612)
├── sq/
│   └── ...
└── ...
```

## Design Decisions

### Why Semantic Merging?

**Problem:** Basic chunking creates many small, fragmented chunks.
```
Chunk 1: "The company operates in three business segments."
Chunk 2: "These segments include delivery, mobility, and fintech."
Chunk 3: "The delivery segment is the largest contributor to revenue."
```
→ Related content split across 3 chunks, requires retrieving all 3

**Solution:** Merge semantically similar adjacent chunks.
```
Merged Chunk: "The company operates in three business segments. These
segments include delivery, mobility, and fintech. The delivery segment
is the largest contributor to revenue."
```
→ Coherent narrative in single chunk, better retrieval

**Benefits:**
1. **Fewer Chunks:** Reduces embedding costs and retrieval latency
2. **More Context:** Each chunk contains more complete information
3. **Better Retrieval:** Single chunk retrieved instead of multiple fragments
4. **Improved LLM Performance:** More coherent context for answer generation

### Why Adjacent-Only Merging?

**Design Choice:** Only merge adjacent chunks (i, i+1), not distant chunks (i, i+5).

**Rationale:**
1. **Preserves Document Flow:** Maintains narrative order
2. **Prevents Context Loss:** Avoids skipping intermediate content
3. **Efficient:** O(n) complexity vs O(n²) for all-pairs comparison
4. **Hierarchical Structure:** Respects document hierarchy

**Example:**
```
✓ Valid: Merge chunks [1, 2, 3] (adjacent)
✗ Invalid: Merge chunks [1, 5, 9] (non-adjacent)
```

### Why Never Merge Table with Text?

**Problem:** Tables and text have different structure and purpose.
```
Text: "Revenue increased by 15% year-over-year..."
Table: "| Segment | Revenue | Growth |\n|---------|---------|--------|..."
```

**Solution:** Enforce type matching (`is_table` must match).

**Rationale:**
1. **Different Semantics:** Tables are structured data, text is narrative
2. **Retrieval Quality:** Users searching for tables want tables, not mixed content
3. **LLM Processing:** LLMs handle tables and text differently
4. **Metadata Preservation:** Table-specific metadata (page, shape) only applies to tables

### Why Higher Threshold for Tables?

**Design Choice:** Tables require `threshold + 0.10` similarity.

**Example:**
```python
# Text chunks: threshold = 0.60
# Table chunks: threshold = 0.70 (+0.10)
```

**Rationale:**
1. **Preserve Precision:** Tables contain precise numerical data
2. **Avoid False Merges:** Similar-looking tables may have different metrics
3. **Data Integrity:** Merging wrong tables corrupts financial data
4. **Conservative Approach:** Better to keep tables separate than merge incorrectly

**Example:**
```
Table 1: Revenue by Segment (2024)
Table 2: Revenue by Segment (2023)
→ Similar embeddings (same structure) but different data!
→ Higher threshold prevents incorrect merge
```

### Why Average Embeddings When Merging?

**Design Choice:** Merged embedding = (emb1 + emb2) / 2

**Rationale:**
1. **Computational Efficiency:** No need to re-embed merged content
2. **Approximate Representation:** Average roughly captures combined semantics
3. **Consistency:** Used in semantic search literature
4. **Chain Merging:** Allows iterative merging without re-embedding

**Limitation:**
- Not perfectly accurate (merged embedding ≠ embedding of merged text)
- Good enough for chain merging decisions
- Final chunks are re-embedded during factsheet generation anyway

## Merge Statistics

| Company | Original Chunks | Merged Chunks | Reduction | Avg Size Before | Avg Size After |
|---------|-----------------|---------------|-----------|-----------------|----------------|
| Grab    | 688             | 456           | 33.7%     | 1307            | 2134           |
| SQ      | 530             | 367           | 30.8%     | 1445            | 2287           |
| SEA     | 498             | 342           | 31.3%     | 1402            | 2198           |

**Observations:**
- **~30-35% reduction** in chunk count
- **~60-70% increase** in average chunk size
- Tables rarely merge (strict threshold)
- Most merges in narrative sections (CEO letter, business overview)

## Logging

Semantic merging operations logged to `logs/logs_{timestamp}.log` with prefix `semantic_chunking`.

**Key Log Messages:**
- `"Initialized SemanticChunker with: ..."` - Configuration
- `"Identified X table chunks out of Y"` - Table detection
- `"Embedding X chunks in batches..."` - Embedding start
- `"  Embedded X/Y chunks"` - Progress (every 50 chunks)
- `"✓ Completed embedding X chunks"` - Embedding complete
- `"Merging (similarity=X.XXX): [...]"` - Each merge operation
- `"Original chunks: X"` - Summary
- `"Merged chunks: Y"` - Summary
- `"Reduction: Z%"` - Summary

## Error Handling

- **Missing OpenAI API Key:** Raises `ValueError` with clear message
- **Missing Chunks File:** Raises `FileNotFoundError`
- **API Rate Limits:** Batch processing respects OpenAI rate limits
- **Token Limit Exceeded:** Truncates content to 30,000 chars (~7500 tokens)
- **Empty Chunks:** Handles gracefully (no merges performed)

## Performance

| Company | Chunks | Embedding Time | Merge Time | Total Time | API Cost |
|---------|--------|----------------|------------|------------|----------|
| Grab    | 688    | ~15s           | ~3s        | ~18s       | $0.003   |
| SQ      | 530    | ~12s           | ~2s        | ~14s       | $0.002   |
| SEA     | 498    | ~11s           | ~2s        | ~13s       | $0.002   |

**Cost Calculation:**
- OpenAI text-embedding-3-small: $0.00002 per 1K tokens
- Average chunk: ~300 tokens
- 688 chunks × 300 tokens = 206,400 tokens
- Cost: 206.4 × $0.00002 = $0.004

**Optimization:**
- Batch embedding (100 chunks per API call)
- Minimal re-embedding (average vectors for chains)
- Efficient similarity calculation (numpy vectorization)

## Dependencies

- `openai` - OpenAI API client
- `numpy` - Vector operations and similarity calculations
- `dotenv` - Environment variable loading
- `pathlib` - Path handling
- `json` - JSON I/O
- `re` - Regular expressions for table detection

## Related Modules

- **Previous Step:**
  - `extraction/` - Basic text chunking
  - `chunking/merge_chunking/` - Text + table merging
- **Next Step:**
  - `generation/` - Factsheet generation with RAG retrieval
- **Inputs from:**
  - `outputs/{company}/{company}_chunks.json` OR
  - `outputs/{company}/{company}_chunks_merged.json`
- **Outputs to:**
  - `outputs/{company}/{company}_chunks_semantic.json` OR
  - `outputs/{company}/{company}_chunks_merged_semantic.json`

## Future Enhancements

- **Bidirectional Merging:** Consider merging with previous chunks (not just next)
- **Hierarchical Clustering:** Group semantically similar non-adjacent chunks
- **Dynamic Thresholds:** Adjust threshold based on document section
- **Embedding Caching:** Cache embeddings to avoid re-computation
- **Multi-Modal Embeddings:** Use multi-modal models for tables and images
- **Quality Metrics:** Measure merge quality using held-out validation set
