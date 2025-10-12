# Evaluation Module

## Overview

Evaluates factsheet quality using the **RAGAS (Retrieval-Augmented Generation Assessment) framework**. Measures faithfulness, answer relevancy, context precision, and context recall to assess the quality of generated answers and the retrieval process. Provides aggregate scores and breakdown by question type (qualitative vs quantitative).

## Architecture

```
FactsheetEvaluator (Orchestrator)
├── QuestionRangeParser → Parse qualitative/quantitative question ranges
├── ModelInitializer → Initialize RAGAS LLM and embeddings
├── DataLoader → Load factsheet, chunks, and QA pairs
├── QAExtractor → Extract Q&A from factsheet
├── ContextRetriever → Format contexts from chunks
├── RAGASRunner → Run RAGAS evaluation
├── ScoreCalculator → Compute scores (individual/aggregate/breakdown)
└── EvaluationLogger → Log evaluation summary
```

## RAGAS Framework

### What is RAGAS?

**RAGAS** = Retrieval-Augmented Generation Assessment

A framework for evaluating RAG systems using LLM-based metrics:
- No ground truth required (except for recall)
- Uses LLM to judge answer quality
- Evaluates both generation and retrieval quality

### RAGAS Metrics

#### 1. **Faithfulness**
**Question:** Is the answer grounded in the provided context?

```
Measures: Hallucination detection
Range: 0.0 to 1.0 (1.0 = fully grounded)

Process:
1. LLM extracts claims from answer
2. LLM verifies each claim against context
3. Score = verified_claims / total_claims

Example:
Context: "Revenue for 2024 was $2,797M"
Answer: "Revenue for 2024 was $2,797M and growing rapidly"

Claims: ["Revenue for 2024 was $2,797M", "Revenue growing rapidly"]
Verified: [True, False]  # "growing rapidly" not in context
Score: 1/2 = 0.50  # 50% faithful (hallucinated growth claim)
```

#### 2. **Answer Relevancy**
**Question:** How relevant is the answer to the question?

```
Measures: Answer quality and directness
Range: 0.0 to 1.0 (1.0 = highly relevant)

Process:
1. LLM generates hypothetical questions from answer
2. Compute cosine similarity between original question and generated questions
3. Score = average similarity

Example:
Question: "What is the company's total revenue for 2024?"
Answer: "Revenue for 2024 was $2,797M"

Generated questions:
- "What was the 2024 revenue?"
- "How much revenue did the company generate in 2024?"

Similarity: 0.95 (highly similar)
Score: 0.95  # Relevant, direct answer
```

#### 3. **Context Precision**
**Question:** Are the relevant contexts ranked higher?

```
Measures: Retrieval ranking quality
Range: 0.0 to 1.0 (1.0 = perfect ranking)

Process:
1. LLM determines if each context is relevant to question
2. Calculate precision@k for each position
3. Score = average precision

Example:
Question: "What is total revenue?"
Retrieved contexts: [C1, C2, C3, C4, C5]
Relevance: [True, False, True, False, True]

Precision@1: 1/1 = 1.00  # C1 relevant
Precision@2: 1/2 = 0.50  # C2 not relevant
Precision@3: 2/3 = 0.67  # C3 relevant
Precision@4: 2/4 = 0.50  # C4 not relevant
Precision@5: 3/5 = 0.60  # C5 relevant

Context Precision = (1.00 + 0.67 + 0.60) / 3 = 0.76
# (average precision at relevant positions)
```

#### 4. **Context Recall**
**Question:** Was all necessary information retrieved?

```
Measures: Retrieval completeness
Range: 0.0 to 1.0 (1.0 = complete)

Process:
1. LLM extracts sentences from ground truth (or answer)
2. LLM checks if each sentence can be attributed to contexts
3. Score = attributed_sentences / total_sentences

Example:
Answer: "Revenue was $2,797M. Operating income was $348M."
Contexts: ["Revenue for 2024 was $2,797M"]

Sentences: ["Revenue was $2,797M", "Operating income was $348M"]
Attributed: [True, False]  # Operating income not in contexts
Score: 1/2 = 0.50  # Missed half the info
```

## Components

### 1. `ragas_evaluator.py`
**Main orchestrator** for RAGAS evaluation pipeline.

**Key Responsibilities:**
- Initialize all evaluation components
- Load QA pairs with retrieved chunks
- Run RAGAS evaluation
- Compute aggregate and breakdown scores
- Save evaluation results

**Key Methods:**
- `evaluate_factsheet()` - Complete evaluation pipeline
- `_run_evaluation_and_get_scores()` - Execute RAGAS
- `_compute_all_scores()` - Calculate all score types

**Usage:**
```python
from evaluation.ragas_evaluator import FactsheetEvaluator
from config_loader import load_config

config = load_config()
config.set_company('grab')

evaluator = FactsheetEvaluator(config)
output_path = evaluator.evaluate_factsheet()

print(f"Evaluation saved to: {output_path}")
```

### 2. `ragas_runner.py`
**Runs RAGAS evaluation with configured LLM and embeddings.**

**Key Responsibilities:**
- Prepare RAGAS dataset from QA pairs
- Execute RAGAS evaluation with metrics
- Configure parallel execution

**RAGAS Execution:**
```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

# Run evaluation with parallel workers
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    llm=ragas_llm,             # Claude 3.5 Sonnet
    embeddings=ragas_embeddings,  # OpenAI text-embedding-3-small
    run_config=RunConfig(max_workers=16)  # Parallel execution
)
```

**Key Methods:**
- `run_ragas_evaluation()` - Main evaluation runner
- `_prepare_ragas_data()` - Format data for RAGAS

### 3. `data_loader.py`
**Loads factsheet, chunks, and QA pairs with retrieved chunks.**

**Key Responsibilities:**
- Load factsheet markdown
- Load chunks JSON
- Load QA pairs with retrieved chunks from generation

**QA Pairs Structure:**
```json
[
  {
    "number": 1,
    "question": "What industries does the company operate in?",
    "answer": "- Delivery: Food delivery...",
    "retrieved_chunks": [
      {"chunk_id": 0, "section_header": "Business Overview", "content": "..."},
      {"chunk_id": 5, "section_header": "CEO Letter", "content": "..."}
    ],
    "category": "Business Fundamentals"
  }
]
```

**Key Feature:**
- Uses **same chunks that generated each answer** for faithful evaluation
- Ensures evaluation reflects actual generation context

### 4. `score_calculator.py`
**Computes individual, aggregate, and breakdown scores.**

**Score Types:**

**Individual Scores:**
```python
# Per-question scores
{
    'question_number': 1,
    'question': "What industries...",
    'answer': "- Delivery: Food...",
    'faithfulness': 0.85,
    'answer_relevancy': 0.92,
    'context_precision': 0.78,
    'context_recall': 0.88,
    'retrieved_chunks': [...]  # Top 5 chunks
}
```

**Aggregate Scores:**
```python
# Average across all questions
{
    'faithfulness': 0.87,
    'answer_relevancy': 0.91,
    'context_precision': 0.82,
    'context_recall': 0.89
}
```

**Breakdown Scores:**
```python
# By question type
{
    'qualitative': {  # Q1-Q9
        'question_range': '1-9',
        'num_questions': 9,
        'scores': {
            'faithfulness': 0.85,
            'answer_relevancy': 0.88,
            'context_precision': 0.75,
            'context_recall': 0.83,
            'average': 0.83
        }
    },
    'quantitative': {  # Q10-Q57
        'question_range': '10-57',
        'num_questions': 48,
        'scores': {
            'faithfulness': 0.92,
            'answer_relevancy': 0.94,
            'context_precision': 0.88,
            'context_recall': 0.91,
            'average': 0.91
        }
    }
}
```

**Key Methods:**
- `extract_individual_scores()` - Per-question scores
- `compute_aggregate_scores()` - Overall averages
- `compute_breakdown_scores()` - Qualitative vs quantitative

### 5. `model_initializer.py`
**Initializes RAGAS LLM and embedding models.**

**Models:**
```python
# LLM for evaluation (generates judgments)
ragas_llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0
)

# Embeddings for similarity calculations
ragas_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)
```

**Key Methods:**
- `initialize_models()` - Initialize all models
- `get_ragas_llm()` - Return RAGAS LLM
- `get_ragas_embeddings()` - Return RAGAS embeddings

### 6. `question_range_parser.py`
**Parses qualitative/quantitative question ranges from config.**

**Question Types:**
```python
# Qualitative questions (Business fundamentals)
qualitative_range = range(1, 10)  # Q1-Q9

# Quantitative questions (Financial data + calculations)
quantitative_range = range(10, 58)  # Q10-Q57
```

**Key Methods:**
- `load_question_ranges()` - Load ranges from config
- `get_qualitative_range()` - Return qualitative range
- `get_quantitative_range()` - Return quantitative range

### 7. `evaluation_logger.py`
**Logs evaluation summary to console and logs.**

**Log Output:**
```
============================================================
Evaluation Summary
============================================================

Aggregate Scores (across all 57 questions):
  Faithfulness:       0.87
  Answer Relevancy:   0.91
  Context Precision:  0.82
  Context Recall:     0.89
  Overall Quality:    0.87

Breakdown by Question Type:
  Qualitative (Q1-Q9):
    Faithfulness:       0.85
    Answer Relevancy:   0.88
    Context Precision:  0.75
    Context Recall:     0.83
    Average:            0.83

  Quantitative (Q10-Q57):
    Faithfulness:       0.92
    Answer Relevancy:   0.94
    Context Precision:  0.88
    Context Recall:     0.91
    Average:            0.91

✓ Evaluation results saved to: outputs/grab/grab_evaluation_scores.json
============================================================
```

## Data Flow

```
QA Pairs JSON (from generation/)
    ├→ Contains: questions, answers, retrieved_chunks
    └→ Uses SAME chunks that generated each answer
    ↓
[Data Loader]
    ├→ Load QA pairs with chunks
    ├→ Load factsheet
    └→ Load all chunks
    ↓
[RAGAS Runner]
    ├→ Prepare RAGAS dataset
    │   ├→ Questions
    │   ├→ Answers
    │   ├→ Contexts (from retrieved_chunks)
    │   └→ Ground truth (uses answers)
    ├→ Run RAGAS evaluation (parallel)
    │   ├→ Faithfulness (LLM judges claims)
    │   ├→ Answer Relevancy (similarity)
    │   ├→ Context Precision (ranking quality)
    │   └→ Context Recall (completeness)
    └→ Return scores dataframe
    ↓
[Score Calculator]
    ├→ Extract individual scores (per question)
    ├→ Compute aggregate scores (overall)
    └→ Compute breakdown scores (qual vs quant)
    ↓
[Evaluation Logger]
    ├→ Log summary to console
    └→ Log details to logs/
    ↓
[Output]
    └→ {company}_evaluation_scores.json
```

## Usage

### CLI Usage
```bash
# Evaluate factsheet for specific company
python -m evaluation.ragas_evaluator --company grab

# With custom paths
python -m evaluation.ragas_evaluator \
    --company grab \
    --factsheet outputs/grab/grab_factsheet.md \
    --chunks outputs/grab/grab_chunks_semantic.json \
    --output outputs/grab/grab_evaluation_custom.json
```

### Programmatic Usage
```python
from evaluation.ragas_evaluator import FactsheetEvaluator
from config_loader import load_config

config = load_config()
config.set_company('grab')

evaluator = FactsheetEvaluator(config)
output_path = evaluator.evaluate_factsheet()

print(f"Evaluation completed: {output_path}")
```

### Pipeline Integration
```python
# Called in main pipeline Step 7 (after generation)
evaluation_result = evaluator.evaluate_factsheet()
# Returns: Path to evaluation_scores.json
```

## Output Format

### Evaluation Scores JSON
```json
{
  "company": "grab",
  "factsheet_path": "outputs/grab/grab_factsheet.md",
  "num_questions": 57,
  "num_chunks": 612,
  "evaluation_method": "RAGAS",

  "aggregate_scores": {
    "faithfulness": 0.87,
    "answer_relevancy": 0.91,
    "context_precision": 0.82,
    "context_recall": 0.89
  },

  "overall_quality_score": 0.87,

  "breakdown_by_question_type": {
    "qualitative": {
      "question_range": "1-9",
      "num_questions": 9,
      "scores": {
        "faithfulness": 0.85,
        "answer_relevancy": 0.88,
        "context_precision": 0.75,
        "context_recall": 0.83,
        "average": 0.83
      }
    },
    "quantitative": {
      "question_range": "10-57",
      "num_questions": 48,
      "scores": {
        "faithfulness": 0.92,
        "answer_relevancy": 0.94,
        "context_precision": 0.88,
        "context_recall": 0.91,
        "average": 0.91
      }
    }
  },

  "individual_scores": [
    {
      "question_number": 1,
      "question": "What industries does the company operate in?",
      "answer": "- Delivery: Food delivery...",
      "answer_length": 45,
      "faithfulness": 0.85,
      "answer_relevancy": 0.92,
      "context_precision": 0.78,
      "context_recall": 0.88,
      "retrieved_chunks": [
        {
          "chunk_id": 0,
          "section_header": "Business Overview",
          "content": "The company operates in three segments..."
        }
      ]
    }
  ]
}
```

## Configuration

### config.yaml
```yaml
# Evaluation settings
evaluation:
  qualitative_range: [1, 9]   # Q1-Q9
  quantitative_range: [10, 57] # Q10-Q57

# RAGAS models
ragas_llm_model: claude-3-5-sonnet-20241022
ragas_embedding_model: text-embedding-3-small
```

### Environment Variables
```bash
# Required for Claude (RAGAS LLM)
ANTHROPIC_API_KEY=sk-ant-...

# Required for OpenAI (RAGAS embeddings)
OPENAI_API_KEY=sk-...
```

## Output Locations

```
outputs/
├── grab/
│   ├── grab_factsheet.md                  # Generated factsheet
│   ├── grab_qa_pairs.json                 # QA with chunks (from generation)
│   └── grab_evaluation_scores.json        # ✓ RAGAS evaluation results
├── sq/
│   └── ...
└── ...
```

## Design Decisions

### Why RAGAS Framework?

**Advantages:**
1. **No Ground Truth Required:** Uses LLM to judge quality
2. **Multi-Dimensional:** Measures generation AND retrieval
3. **Interpretable:** Clear metrics (faithfulness, relevancy, etc.)
4. **Industry Standard:** Widely used for RAG evaluation

**Alternatives Considered:**
- Manual evaluation: Too slow, not scalable
- BLEU/ROUGE: Poor for semantic similarity
- Perplexity: Doesn't measure factuality

### Why Use Generation Chunks for Evaluation?

**Design Choice:** Evaluate using **same chunks that generated each answer**.

**Rationale:**
```
Option 1: Re-retrieve chunks for evaluation
→ May retrieve different chunks
→ Evaluates retrieval, not generation quality
→ Unfair to penalize answer for different context

Option 2: Use generation chunks (chosen)
→ Same chunks that generated answer
→ Faithful evaluation of generation quality
→ Measures: "Given these chunks, was answer good?"
```

**Benefits:**
- **Fairness:** Answer judged on actual context used
- **Debugging:** Can trace low scores to specific chunks
- **Consistency:** Evaluation matches generation

### Why Qualitative vs Quantitative Breakdown?

**Observation:** Different question types have different characteristics.

**Qualitative (Q1-Q9):**
- Subjective, narrative answers
- Multiple valid answer styles
- Harder to judge (typically lower scores)
- Context precision often lower (info scattered)

**Quantitative (Q10-Q57):**
- Objective, data-driven answers
- Exact numbers required
- Easier to judge (typically higher scores)
- Context precision often higher (specific tables)

**Benefit:** Breakdown reveals if issues are systemic or question-type-specific.

### Why Parallel Execution?

**Problem:** RAGAS evaluation involves many LLM calls (4 metrics × 57 questions = 228 calls).

**Solution:** Parallel execution with 16 workers.
```python
run_config=RunConfig(max_workers=16)
```

**Results:**
- Sequential: ~10 minutes
- Parallel (16 workers): ~2 minutes
- **5x speedup**

## Performance

### Evaluation Time

| Company | Questions | Evaluation Time | LLM Calls | Cost    |
|---------|-----------|-----------------|-----------|---------|
| Grab    | 57        | ~2 min          | ~228      | $1.50   |
| SQ      | 57        | ~2 min          | ~228      | $1.50   |
| SEA     | 57        | ~2 min          | ~228      | $1.50   |

### Cost Breakdown (Claude 3.5 Sonnet)

| Metric             | Calls | Tokens/Call | Total Tokens | Cost    |
|--------------------|-------|-------------|--------------|---------|
| Faithfulness       | 57    | ~1500       | 85K          | $0.65   |
| Answer Relevancy   | 57    | ~800        | 46K          | $0.35   |
| Context Precision  | 57    | ~1200       | 68K          | $0.50   |
| Context Recall     | 57    | ~1000       | 57K          | $0.43   |
| **Total**          | 228   | —           | 256K         | **$1.93** |

### Bottleneck

**LLM API calls:** 95% of evaluation time
- Faithfulness: Most expensive (extracts claims, verifies each)
- Context Precision: Second most expensive (checks each context)

## Typical Score Ranges

### Overall Scores (Observed)

| Metric             | Typical Range | Good Score | Excellent Score |
|--------------------|---------------|------------|-----------------|
| Faithfulness       | 0.75 - 0.95   | > 0.85     | > 0.92          |
| Answer Relevancy   | 0.85 - 0.98   | > 0.90     | > 0.95          |
| Context Precision  | 0.65 - 0.90   | > 0.75     | > 0.85          |
| Context Recall     | 0.80 - 0.95   | > 0.85     | > 0.90          |
| Overall Quality    | 0.75 - 0.92   | > 0.82     | > 0.88          |

### By Question Type

**Qualitative (Q1-Q9):**
- Typical: 0.75 - 0.88
- Lower context precision (info scattered)
- Lower faithfulness (more interpretive)

**Quantitative (Q10-Q57):**
- Typical: 0.88 - 0.95
- Higher context precision (specific data)
- Higher faithfulness (exact numbers)

## Logging

Evaluation operations logged to `logs/logs_{timestamp}.log` with prefix `evaluation`.

**Key Log Messages:**
- `"Loaded X QA pairs with retrieved chunks"` - Data loading
- `"Evaluating X Q&A pairs with RAGAS..."` - Evaluation start
- `"Using the SAME chunks that generated each answer"` - Context source
- `"Running RAGAS evaluation with parallel execution..."` - RAGAS start
- `"Aggregate Scores:"` - Summary header
- `"  Faithfulness: X.XX"` - Metric scores
- `"✓ Evaluation results saved to: {path}"` - Completion

## Error Handling

- **Missing QA Pairs:** Raises `FileNotFoundError` with path
- **Missing Chunks:** Raises `FileNotFoundError` with path
- **Missing API Key:** Raises `ValueError` with provider name
- **RAGAS API Error:** Logs error, continues with remaining metrics
- **NaN Scores:** Converts to None, logs warning

## Dependencies

- `ragas` - RAGAS framework
- `datasets` - HuggingFace datasets (required by RAGAS)
- `anthropic` - Claude API (RAGAS LLM)
- `openai` - OpenAI API (RAGAS embeddings)
- `langchain_anthropic` - LangChain wrapper for Claude
- `langchain_openai` - LangChain wrapper for OpenAI
- `pandas` - Score calculations
- `numpy` - Numerical operations
- `json` - JSON I/O
- `pathlib` - Path handling

## Related Modules

- **Previous Step:**
  - `generation/` - Generates factsheet and QA pairs with chunks
- **Inputs from:**
  - `outputs/{company}/{company}_qa_pairs.json` - QA with chunks
  - `outputs/{company}/{company}_factsheet.md` - Factsheet
  - `outputs/{company}/{company}_chunks_semantic.json` - Chunks
- **Outputs to:**
  - `outputs/{company}/{company}_evaluation_scores.json`

## Future Enhancements

- **Ground Truth Annotation:** Manual ground truth for higher-quality recall
- **Custom Metrics:** Domain-specific financial answer quality metrics
- **Error Analysis:** Automatic identification of low-score patterns
- **Comparative Evaluation:** Compare multiple factsheet versions
- **Fine-Tuned Evaluator:** Train custom evaluation model
- **Real-Time Monitoring:** Track evaluation scores over time
- **Human-in-the-Loop:** Allow human feedback on scores
