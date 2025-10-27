# Generation Module

## Overview

Core module for **credit analysis factsheet generation** using Retrieval-Augmented Generation (RAG). Implements advanced retrieval strategies including Multi-HyDE (Multiple Hypothetical Document Embeddings), 2-stage re-ranking with cross-encoder, hybrid search (semantic + BM25), section-aware boosting, and batch processing to answer key financial questions from annual reports.

## Architecture

```
FactsheetGenerator (Orchestrator)
├── DataLoader → Load questions and chunks
├── CategoryParser → Parse question set structure dynamically
├── TerminologyMapper → Auto-detect company-specific financial terms
├── Embedder → Semantic search (Sentence Transformers)
├── BM25Retriever → Keyword search + Reciprocal Rank Fusion
├── SectionBooster → Section-aware + position-based boosting
├── LLMClient → Unified LLM interface (Claude/OpenAI/Ollama)
├── PromptBuilder → Build prompts and parse responses
├── AnswerGenerator → Generate answers (single/batch)
└── FactsheetFormatter → Format Q&A into markdown
```

## Components

### 1. `factsheet_generator.py`
**Main orchestrator** for adaptive RAG factsheet generation.

**Key Responsibilities:**
- Coordinate all generation components
- Execute 2-stage retrieval (broad retrieval → re-ranking)
- Process questions by category with batch answering
- Apply adaptive retrieval strategies (hybrid, section boosting)
- Save factsheet and detailed evaluation data

**Retrieval Strategy:**

```python
# Stage 1: Broad retrieval (50-60 chunks)
def _retrieve_for_category(category, question, keywords, chunks):
    1. Semantic search (50 chunks)
    2. Hybrid RRF (20 semantic + 30 BM25 → merge to 50)
    3. Section-aware boosting (boost relevant sections by 80%)
    4. Document structure boosting (early chunks get exponential boost)
    5. Return top 50-60 chunks

# Stage 2: Re-ranking for precision (30 chunks)
def _rerank_chunks_for_precision(retrieved_chunks, category_questions):
    1. Combine all category questions into single query
    2. Re-compute similarities against combined query
    3. Re-rank based on new scores
    4. Return top 30 most relevant chunks
```

**Adaptive Retrieval:**
```python
# Different strategies for different question types

# Business Fundamentals (Q1-Q9): Hybrid + Section + Position Boosting
- Use hybrid search (semantic + BM25)
- Boost CEO/Chairman sections (80% boost)
- Boost early document chunks (exponential decay)

# Financial Data (Q10-Q35): Pure Semantic Search
- Use semantic search only
- No keyword search (relies on context understanding)

# Calculated Metrics (Q36-Q60): Pure Semantic Search
- Use semantic search only
- Relies on finding relevant data points
```

**Key Methods:**
- `generate_factsheet()` - Complete pipeline (load → retrieve → generate → save)
- `_process_category()` - Process single category with 2-stage retrieval
- `_retrieve_for_category()` - Stage 1: Broad retrieval
- `_rerank_chunks_for_precision()` - Stage 2: Re-ranking
- `_detect_and_substitute_terms()` - Auto-detect company terminology

### 2. `data_loader.py`
**Loads questions from markdown and chunks from JSON.**

**Key Responsibilities:**
- Parse question set markdown (extract question numbers and text)
- Load chunks (text and table) from JSON files
- Detect merged/semantic chunk files
- Combine text and table chunks if separate

**Question Parsing:**
```python
# Extracts questions from markdown format
### 1. What industries does the company operate in?
### 2. What geographic markets does the company operate in?

# Returns:
[
    {'number': 1, 'text': 'What industries does the company operate in?'},
    {'number': 2, 'text': 'What geographic markets does the company operate in?'}
]
```

**Chunk Loading:**
```python
# Detects file type and loads appropriately

# Merged file (text + tables): grab_chunks_merged.json
→ Load as single file (contains both)

# Separate files:
# grab_chunks.json (text only)
# grab_table_chunks.json (tables only)
→ Load both and combine
```

### 3. `llm_client.py`
**Unified LLM interface for Claude, OpenAI, and Ollama.**

**Supported Providers:**
```yaml
# Claude (Anthropic)
llm_provider: claude
claude_model: claude-3-haiku-20240307
CLAUDE_API_KEY: sk-ant-...

# OpenAI
llm_provider: openai
openai_model: gpt-4o-mini
OPENAI_API_KEY: sk-...

# Ollama (local)
llm_provider: ollama
ollama_url: http://localhost:11434
ollama_model: qwen2.5:32b
```

**Key Methods:**
- `call_llm()` - Unified interface for all providers
- `_call_claude()` - Claude API call
- `_call_openai()` - OpenAI API call
- `_call_ollama()` - Ollama local call

**Usage:**
```python
llm_client = LLMClient(config, logger)
response = llm_client.call_llm(prompt, max_tokens=2000)
# Automatically routes to configured provider
```

### 4. `multi_hyde.py`
**Multi-HyDE (Multiple Hypothetical Document Embeddings) for enhanced retrieval.**

**Purpose:** Improves retrieval accuracy by generating multiple query variants and hypothetical documents, then reranking with cross-encoder.

**6-Step Process:**
```python
1. Generate N diverse query variants from original question (default: 5)
   Example: "What is the company's revenue?" →
   - "What were the company's total sales in the fiscal year?"
   - "How much income did the company generate?"
   - "What is the company's top-line financial performance?"

2. Generate hypothetical document for each variant
   - LLM generates what an ideal answer would look like
   - These are more similar to actual document chunks than questions

3. Embed each hypothetical document
   - Uses same embedder as chunks (all-mpnet-base-v2)
   - Creates semantic representations in embedding space

4. Retrieve top-k chunks per hypothetical document (default: k=10)
   - Semantic search using hypothetical doc embeddings
   - Each variant retrieves potentially different relevant chunks

5. Aggregate and deduplicate results
   - Combine all retrieved chunks
   - Remove duplicates
   - Typically results in 30-50 unique chunks

6. Cross-encoder reranking using original question
   - MS-MARCO MiniLM cross-encoder
   - Scores each chunk against original question
   - Returns top-30 most relevant chunks
```

**Configuration:**
```yaml
# From config.yaml
multi_hyde:
  enabled: true
  num_variants: 5                              # Number of query variants to generate
  k_per_hypothetical: 10                       # Chunks to retrieve per variant
  cross_encoder_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
```

**Key Methods:**
- `retrieve_with_multi_hyde()` - Main entry point for Multi-HyDE retrieval
- `_generate_query_variants()` - Generate diverse query variants via LLM
- `_generate_hypothetical_document()` - Generate hypothetical answer for variant
- `_retrieve_per_variant()` - Retrieve chunks using hypothetical doc embedding
- `_aggregate_and_deduplicate()` - Combine and deduplicate results
- `_cross_encoder_rerank()` - Rerank with cross-encoder using original question

**Why it Works:**
1. **Query Expansion:** Multiple variants capture different semantic angles
2. **HyDE Effect:** Hypothetical documents are more similar to actual chunks than questions
3. **Diversity:** Different variants retrieve different but relevant chunks
4. **Cross-Encoder Precision:** Final reranking ensures highest quality results

**Performance Impact:**
- **Time:** ~12-14 minutes per company (60 questions × 5 variants = 300 LLM calls)
- **Quality:** +2.8% overall improvement, +7.0% context precision improvement
- **Trade-off:** Slower but significantly more accurate retrieval

See [MULTI_HYDE_FLOW_WITH_EXAMPLES.md](MULTI_HYDE_FLOW_WITH_EXAMPLES.md) for detailed examples.

### 5. `embedder.py`
**Semantic search using Sentence Transformers.**

**Embedding Model:**
```python
model: "sentence-transformers/all-mpnet-base-v2"
# 768-dimensional embeddings
# Trained on semantic similarity tasks
```

**Key Methods:**
- `retrieve_relevant_chunks()` - Main semantic search
- `encode_embeddings()` - Encode question and chunks
- `_calculate_similarities()` - Cosine similarity calculation
- `get_top_chunks()` - Extract top-k chunks

**Semantic Retrieval Process:**
```python
1. Prepare chunk texts (section_header + content)
2. Encode question as embedding vector
3. Encode all chunks as embedding vectors
4. Calculate cosine similarities
5. Return top-k chunks sorted by similarity
```

**Chunk Text Preparation:**
```python
# Prepends section header for better context
chunk_text = f"{chunk['section_header']}\n\n{chunk['content']}"

# Example:
"Business Overview > Financial Performance\n\n
Revenue for FY2024 increased by 15%..."
```

### 6. `bm25_retriever.py`
**Keyword search using BM25 with Reciprocal Rank Fusion (RRF).**

**BM25 Algorithm:**
```python
# Token-based keyword matching with TF-IDF weighting
# BM25Okapi variant (state-of-the-art)

1. Tokenize query and chunks (word-level)
2. Calculate BM25 scores (TF-IDF with length normalization)
3. Return top-k chunks by score
```

**Reciprocal Rank Fusion (RRF):**
```python
# Combines semantic and BM25 results

def rrf_score(rank, k=60):
    return 1.0 / (k + rank)

# For each chunk:
rrf_score = rrf_from_semantic_results + rrf_from_bm25_results

# Example:
Chunk A: semantic_rank=1 (score=1/61), bm25_rank=5 (score=1/65)
→ rrf_score = 0.0164 + 0.0154 = 0.0318

Chunk B: semantic_rank=10, bm25_rank=1
→ rrf_score = 0.0143 + 0.0164 = 0.0307

# Chunk A wins (appears high in both rankings)
```

**Key Methods:**
- `bm25_search()` - Pure BM25 keyword search
- `reciprocal_rank_fusion()` - Combine two result lists
- `retrieve_hybrid()` - Hybrid semantic + BM25 retrieval

### 7. `section_booster.py`
**Applies section-aware and position-based boosting.**

**Section-Aware Boosting:**
```python
# Boost chunks from relevant sections based on question type

# Industry questions → boost:
['chairman', 'ceo', 'message', 'letter', 'strategic',
 'business review', 'overview', 'business model', 'our business']

# Risk questions → boost:
['risk', 'principal risk', 'risk factor', 'risk management']

# Governance questions → boost:
['ownership', 'shareholders', 'capital structure']

# Boost factor: 0.8 (80% increase)
boosted_similarity = original_similarity * (1 + 0.8)
# Example: 0.5 → 0.9
```

**Document Structure Boosting:**
```python
# Early chunks get exponential decay boost
# Assumption: Important info appears early in annual reports

boost_factor = base_boost * exp(-decay_rate * normalized_position)

# Parameters:
base_boost = 0.3     # 30% boost for chunk 0
decay_rate = 3.0     # Exponential decay rate

# Example boosts:
Chunk 0 (position=0.00): boost = 0.30 → 30% increase
Chunk 100 (position=0.15): boost = 0.19 → 19% increase
Chunk 500 (position=0.73): boost = 0.03 → 3% increase
Chunk 687 (position=1.00): boost = 0.01 → 1% increase
```

**Key Methods:**
- `boost_by_section_relevance()` - Section-aware boosting
- `apply_document_structure_boost()` - Position-based boosting
- `get_section_patterns_for_question()` - Determine relevant sections

### 8. `category_parser.py`
**Dynamically parses question set structure from markdown.**

**Key Responsibilities:**
- Parse PART markers (Business Fundamentals, Financial Data, Calculated Metrics)
- Detect subsections (Income Statement, Cash Flow, Balance Sheet, etc.)
- Extract question numbers and group into categories
- Merge related categories (Balance Sheet Assets + Liabilities)
- Extract financial keywords from question text

**Category Structure:**
```python
{
    "Business Fundamentals": {
        "range": range(1, 10),  # Q1-Q9
        "keywords": "industry sector operations business model..."
    },
    "Income Statement Data": {
        "range": range(10, 19),  # Q10-Q18
        "keywords": "revenue income profit EBITDA 'income statement'..."
    },
    "Calculated Metrics - Profitability": {
        "range": range(39, 46),  # Q39-Q45
        "keywords": "margin profit gross EBITDA ROE ROA..."
    }
}
```

**Keyword Extraction:**
```python
# Automatically extracts financial terms from questions

Question: "What is total revenue for fiscal years 2024, 2023, and 2022?"
→ Extracted keywords: revenue "income statement"

Question: "Calculate free cash flow for 2024, 2023, 2022"
→ Extracted keywords: "cash flow" capex FCF "cash flow statement"
```

### 9. `terminology_mapper.py`
**Auto-detects company-specific financial terminology.**

**Problem:**
```
Standard term: "EBITDA"
Company A uses: "Adjusted EBITDA"
Company B uses: "EBIT"
Company C uses: "Operating Profit"

→ Need to detect what each company uses!
```

**Detection Strategy:**
```python
# Count occurrences in chunks (weighted by source type)

term_count = (table_count × 3) + text_count

# Tables weighted 3x (more reliable for exact terms)
# Returns top 2 most common variants
```

**Example Detection:**
```python
# Grab Annual Report

Standard term: "debt"
Detected variants: ["total borrowings", "debt obligations"]

Standard term: "capex"
Detected variants: ["capital expenditure", "additions to property"]

# Substitution:
Original keywords: "debt capex EBITDA"
Substituted keywords: 'debt "total borrowings" "debt obligations" capex "capital expenditure" EBITDA "adjusted EBITDA"'
```

**Key Methods:**
- `detect_company_terminology()` - Detect all terminology
- `substitute_terms()` - Apply substitutions to keywords

### 10. `prompt_builder.py`
**Builds prompts for LLM and parses responses.**

**Prompt Structure:**
```
1. System message (role: senior credit analyst)
2. Category name
3. Source data (relevant chunks with section headers)
4. Questions to answer
5. Critical instructions:
   - Question type guidance (qualitative/data/calculations)
   - Length requirements
   - Data extraction guidelines
   - Calculation guidelines
   - Output format examples
6. Start answering
```

**Batch Processing:**
```python
# Answer multiple questions in one LLM call

Category: "Income Statement Data"
Questions: Q10-Q18 (9 questions)
Context: 30 relevant chunks

→ Single LLM call with all questions
→ Parse response into individual answers
```

**Response Parsing:**
```python
# Regex pattern to extract answers

Pattern: r'\*\*Question (\d+):[^\n]*\*\*\s*(.*?)(?=\*\*Question \d+:|\Z)'

# Example response:
**Question 10: What is total revenue?**
- 2024: $2,797M, 2023: $2,359M, 2022: $1,433M

**Question 11: What is operating income?**
- 2024: $348M, 2023: $213M, 2022: $(641)M

# Parsed:
{10: "- 2024: $2,797M, 2023: $2,359M, 2022: $1,433M",
 11: "- 2024: $348M, 2023: $213M, 2022: $(641)M"}
```

### 11. `answer_generator.py`
**Generates answers using LLM (single/batch).**

**Key Methods:**
- `generate_batch_answers()` - Batch processing for category
- `generate_answer()` - Single question answering (fallback)

**Batch Processing:**
```python
# Used for all questions (primary method)
1. Build batch prompt with category questions
2. Call LLM (max_tokens=4000)
3. Parse response into individual answers
4. Return {question_num: answer} dictionary
```

**Context Preparation:**
```python
# Format chunks for LLM

[Chunk 1 - Business Overview]
The company operates in three business segments...

---

[Chunk 2 - Financial Performance]
Revenue for FY2024 increased by 15%...

---
...
```

### 12. `factsheet_formatter.py`
**Formats Q&A pairs into structured markdown.**

**Output Format:**
```markdown
# GRAB - Credit Analysis Factsheet

*Generated from annual report using RAG system*

---

## Business Fundamentals

### 1. What industries does the company operate in?
- Delivery: Food delivery and grocery delivery
- Mobility: Ride-hailing and transport services
- Fintech: Digital payments and financial services

### 2. What geographic markets does the company operate in?
- Southeast Asia: Singapore, Indonesia, Malaysia, Thailand, Philippines, Vietnam
- Primary focus on urban centers across 500+ cities

---

## Income Statement Data

### 10. What is total revenue for fiscal years 2024, 2023, and 2022?
- 2024: $2,797M, 2023: $2,359M, 2022: $1,433M

...
```

## Data Flow

```
Question Set (MD) → Parse → Categories + Ranges
Chunks (JSON) → Load → All Chunks (text + tables)
    ↓                         ↓
    ↓                 Detect Terminology
    ↓                         ↓
    ├─────────────┬───────────┴──────────────────┐
    ↓             ↓                              ↓
[For each category]
    │
    ├→ Get category questions (Q10-Q18)
    │
    ├→ Extract keywords dynamically
    │
    ├→ Substitute company-specific terms
    │
    ├→ STAGE 1: Broad Retrieval (50-60 chunks)
    │   ├→ Semantic search (50 chunks)
    │   ├→ BM25 search (30 chunks)  # For Q1-Q9 only
    │   ├→ RRF merge (hybrid)
    │   ├→ Section-aware boost
    │   └→ Document structure boost
    │
    ├→ STAGE 2: Re-ranking (30 chunks)
    │   ├→ Combine all category questions
    │   ├→ Re-compute similarities
    │   └→ Select top 30
    │
    ├→ Build batch prompt
    │   ├→ Format 30 chunks as context
    │   └→ Include all category questions
    │
    ├→ Call LLM (single batch)
    │
    ├→ Parse response → Q&A pairs
    │
    └→ Add to results
    ↓
[Format factsheet]
    ├→ Group by categories
    ├→ Format as markdown
    └→ Save factsheet.md
    ↓
[Save evaluation data]
    ├→ Save detailed Q&A with chunks
    └→ {company}_evaluation.json
```

## Usage

### CLI Usage
```bash
# Generate factsheet for specific company
python -m generation.factsheet_generator --company grab

# With custom chunks file
python -m generation.factsheet_generator \
    --company grab \
    --chunks outputs/grab/grab_chunks_semantic.json

# Use different LLM provider
# (configured in config.yaml)
python -m generation.factsheet_generator --company grab
```

### Programmatic Usage
```python
from generation.factsheet_generator import FactsheetGenerator
from config_loader import load_config

config = load_config()
config.set_company('grab')

generator = FactsheetGenerator(config)
result = generator.generate_factsheet()

print(f"Generated factsheet: {result['output_path']}")
print(f"Answered {len(result['qa_pairs'])} questions")
```

### Pipeline Integration
```python
# Called in main pipeline Step 6 (final step)
generation_result = factsheet_generator.generate_factsheet()
# Returns: {'output_path': Path, 'qa_pairs': List[Dict], ...}
```

## Output Format

### Factsheet Markdown
```markdown
# GRAB - Credit Analysis Factsheet

*Generated from annual report using RAG system*

---

## Business Fundamentals

### 1. What industries does the company operate in?
...

## Income Statement Data

### 10. What is total revenue for fiscal years 2024, 2023, and 2022?
...

## Calculated Metrics - Profitability

### 39. Calculate gross profit and gross profit margin for 2024, 2023, 2022
...
```

### Evaluation JSON
```json
{
  "company": "grab",
  "questions": [
    {
      "number": 1,
      "text": "What industries does the company operate in?",
      "answer": "- Delivery: Food delivery...",
      "contexts": ["chunk_content_1", "chunk_content_2", ...],
      "ground_truth": "",
      "category": "Business Fundamentals",
      "chunk_ids": [0, 1, 5, 12, ...],
      "retrieval_method": "hybrid",
      "similarity_scores": [0.89, 0.82, 0.78, ...]
    }
  ]
}
```

## Configuration

### config.yaml
```yaml
# LLM Provider
llm_provider: claude  # claude, openai, or ollama

# Claude
claude_model: claude-3-haiku-20240307

# OpenAI
openai_model: gpt-4o-mini

# Ollama
ollama_url: http://localhost:11434
ollama_model: qwen2.5:32b

# Embedding Model
embedding_model: sentence-transformers/all-mpnet-base-v2

# Retrieval Strategy
retrieval_strategy: hybrid  # semantic, bm25, or hybrid

# Question Set
question_set_path: question_set.md
```

### Environment Variables
```bash
# Required for Claude
CLAUDE_API_KEY=sk-ant-...

# Required for OpenAI
OPENAI_API_KEY=sk-...

# Ollama requires local server running
# ollama serve
```

### Tuning Parameters

**Retrieval:**
```python
# Stage 1: Broad retrieval
top_k_stage1 = 50-60  # Number of chunks to retrieve
hybrid_bm25_k = 30    # BM25 chunks for hybrid

# Stage 2: Re-ranking
final_k = 30          # Final chunks for LLM

# Section boosting
section_boost = 0.8   # 80% boost for relevant sections

# Position boosting
base_boost = 0.3      # 30% boost for early chunks
decay_rate = 3.0      # Exponential decay rate
```

**LLM:**
```python
# Batch answering
max_tokens_batch = 4000   # For category batch

# Single answering (fallback)
max_tokens_single = 1000  # For single question

# Temperature
temperature = 0  # Deterministic output
```

## Output Locations

```
outputs/
├── grab/
│   ├── grab_factsheet.md            # ✓ Final factsheet
│   └── grab_evaluation.json         # ✓ Detailed evaluation data
├── sq/
│   ├── sq_factsheet.md
│   └── sq_evaluation.json
└── ...
```

## Design Decisions

### Why 2-Stage Retrieval?

**Problem:** Retrieving too few chunks misses context, too many dilutes signal.

**Solution:** Two-stage approach
```
Stage 1: Cast wide net (50-60 chunks)
→ Ensures relevant content is captured

Stage 2: Refine to top 30
→ Removes noise, focuses on most relevant
→ Uses ALL category questions for better precision
```

**Benefits:**
1. **Higher Recall:** Stage 1 captures diverse relevant content
2. **Higher Precision:** Stage 2 filters to most relevant
3. **Better Ranking:** Re-ranking with combined query improves relevance

### Why Batch Processing?

**Problem:** 60 questions × single API call = 60 calls (slow + expensive)

**Solution:** Batch by category
```
9 categories × 1 batch call = 9 calls total
→ 6x fewer API calls
→ 6x faster generation
→ 6x lower cost
```

**Benefits:**
1. **Efficiency:** Fewer API calls
2. **Context Sharing:** Related questions share same context
3. **Consistency:** Answers within category are more consistent

### Why Hybrid Search?

**Problem:** Pure semantic misses exact keyword matches, pure BM25 misses semantic similarity.

**Example:**
```
Question: "What is the company's primary business?"

Semantic Search:
✓ "The company operates in three business segments..."
✓ "Our core operations include delivery, mobility..."
✗ Misses: "Business model: Platform connecting consumers..."
   (uses "business model" instead of "primary business")

BM25 Search:
✓ "Business model: Platform connecting consumers..."
✓ "Primary revenue streams include..."
✗ Misses semantic variations ("core operations", "main activities")

Hybrid (RRF):
✓ Gets both semantic and keyword matches
→ Best of both worlds
```

### Why Section Boosting?

**Problem:** Business fundamentals info (Q1-Q9) usually occur in the first few sections.

**Solution:** Boost sections known to contain relevant info.
```
Question: "What industries does the company operate in?"

Without boost:
Top chunks: Random high-similarity chunks
May miss: CEO Letter section (contains overview)

With boost:
Top chunks: CEO Letter, Business Overview, Strategic Review
→ Contains exact info needed
```

**Rationale:**
- Annual reports follow a rough standard structure
- Certain sections reliably contain certain info types
- Boosting leverages document structure knowledge

### Why Dynamic Category Parsing?

**Problem:** Hard-coded category ranges break when question set changes.

**Solution:** Parse question set markdown dynamically.
```markdown
## PART 1: BUSINESS FUNDAMENTALS (Q1-Q9)
### INCOME STATEMENT
### 10. What is total revenue?
### 11. What is operating income?

→ Auto-detects: "Income Statement Data" = Q10-18
→ Extracts keywords: "revenue", "income", "profit"
```

**Benefits:**
1. **Flexibility:** Works with any question set structure
2. **No Maintenance:** No manual config updates
3. **Automatic Keywords:** Extracts relevant terms from questions

### Why Auto-Detect Terminology?

**Problem:** Companies use different terms for same concepts.
```
EBITDA vs Adjusted EBITDA vs Operating Profit
Total Debt vs Total Borrowings vs Debt Obligations
Capex vs Capital Expenditure vs Additions to Property
```

**Solution:** Scan chunks and detect which terms company uses.
```python
# Grab uses:
"total borrowings" (not "total debt")
"capital expenditure" (not "capex")

# Keyword expansion:
"debt" → "debt total borrowings"
"capex" → "capex capital expenditure"

→ Better keyword matching in BM25
```

### Optimization Strategies

**Current optimizations:**
- Batch processing (6x reduction in API calls)
- 2-stage retrieval (reduces context size)
- Embeddings cached during first category
- Terminology detection done once

**Potential optimizations:**
- Cache embeddings across runs (save ~5s)
- Parallel category processing (requires async LLM)
- Smaller embedding model (faster encoding)
- Streaming LLM responses (perceived speed)

## Logging

Generation operations logged to `logs/logs_{num}.log` with prefix `generation`.

**Key Log Messages:**
- `"Loading questions and chunks..."` - Data loading
- `"✓ Auto-detected terminology for {company}"` - Terminology detection
- `"Processing category: {category} (Q{start}-Q{end})"` - Category processing
- `"  Keywords: {keywords}"` - Retrieval keywords
- `"Stage 1: Broad retrieval..."` - Stage 1 start
- `"  Retrieved {N} chunks using {strategy}"` - Stage 1 result
- `"Stage 2: Re-ranking..."` - Stage 2 start
- `"  ✓ Re-ranked to {N} most relevant chunks"` - Stage 2 result
- `"Calling API for batch of {N} questions..."` - LLM call
- `"✓ Generated answers for {N} questions"` - Batch complete
- `"✓ Factsheet saved to: {path}"` - Final output

## Error Handling

- **Missing Question Set:** Raises `FileNotFoundError` with path
- **Missing Chunks:** Raises `FileNotFoundError` with path
- **Missing API Key:** Raises `ValueError` with provider name
- **LLM API Error:** Logs error, returns "Error: {message}" for affected questions
- **Parse Error:** Falls back to sequential parsing
- **Empty Chunks:** Logs warning, uses all available chunks

## Dependencies

- `anthropic` - Claude API client
- `openai` - OpenAI API client
- `requests` - Ollama API calls
- `sentence_transformers` - Semantic embeddings
- `torch` - PyTorch backend for embeddings
- `rank_bm25` - BM25 implementation
- `numpy` - Numerical operations
- `json` - JSON I/O
- `re` - Regular expressions
- `pathlib` - Path handling

## Related Modules

- **Previous Steps:**
  - All previous modules (conversion → validation → extraction → chunking)
- **Next Step:**
  - `evaluation/` - RAGAS evaluation of factsheet quality
- **Inputs from:**
  - `question_set.md` - Question set
  - `outputs/{company}/{company}_chunks_semantic.json` - Chunks
- **Outputs to:**
  - `outputs/{company}/{company}_factsheet.md` - Factsheet
  - `outputs/{company}/{company}_evaluation.json` - Evaluation data

## Future Enhancements

- Cache embeddings and terminology across runs
- Process categories in parallel
- Adaptive Multi-HyDE (vary num_variants based on question complexity)
