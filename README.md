# Company Fact Sheet Generator

RAG-powered tool that generates 1-2 page credit memos from corporate annual reports for preliminary credit assessment.

## Problem Statement

Credit analysts face a critical bottleneck: before committing significant time to deep credit analysis, they must present a concise 1-2 page credit memo to their Chief Risk Officers (CROs) for an initial "smell test." This preliminary assessment determines whether a potential borrower is worth further investigation.

**The Challenge:**
- Annual reports are 200-400 pages of dense financial and operational information
- Analysts need to quickly extract and synthesize 35+ key credit metrics
- Manual extraction is time-consuming and inconsistent
- Time spent on poor prospects could be better allocated to viable opportunities

**The Solution:**
AR-RAG-Snapshot automates the extraction and synthesis of critical credit information from annual reports, producing structured credit memos that enable rapid preliminary assessment. This allows credit teams to quickly identify promising opportunities and filter out unsuitable candidates before investing significant analytical resources.

## Overview

This project serves two primary purposes:

1. **Practical Application**: Automated generation of standardized credit memos for preliminary borrower assessment
2. **Technical Demonstration**: Implementation and evaluation of RAG (Retrieval-Augmented Generation) systems using the RAGAS evaluation framework

The system ingests corporate annual reports (PDFs) and produces comprehensive factsheets covering business fundamentals, income statement analysis, cash flow metrics, balance sheet data, and key financial ratios - all formatted for executive review.

## Key Features

- **End-to-end RAG Pipeline**: PDF ingestion → Chunking → Retrieval → Generation → Evaluation
- **RAGAS Evaluation**: Comprehensive quality assessment using faithfulness, relevance, and precision metrics
- **Multiple LLM Support**: OpenAI GPT, Anthropic Claude, and Ollama (local models)
- **Semantic Chunking**: Intelligent document segmentation using embedding-based similarity
- **Quality Validation**: Built-in PDF extraction quality checks and factsheet evaluation
- **Configurable**: Easy customization of models, chunking parameters, and question sets

## Folder Structure

```
company_factsheet_generator/
├── configs/
│   ├── config.yaml
│   └── prompt_config.yaml
│
├── data/
│   ├── dbs-annual-report-2024.pdf
│   ├── Capitaland 2024.pdf
│   ├── Grab 2024.pdf
│   └── SQ 2024.pdf
│
├── markdown_files/
│   ├── dbs-annual-report-2024.md
│   ├── Capitaland 2024.md
│   ├── Grab 2024.md
│   └── SQ 2024.md
│
├── src/
│   ├── backend/
│   │   ├── config_loader.py
│   │   ├── markdown_convertor.py
│   │   ├── conversion_validator.py
│   │   ├── extract.py
│   │   ├── chunker.py
│   │   ├── generate_factsheet.py
│   │   ├── llm_evaluation.py
│   │   └── main.py
│   │
│   └── frontend/
│       └── app.py
│
├── outputs/
│   ├── dbs/
│   │   ├── dbs_chunks.json
│   │   ├── dbs_chunks_inspection.txt
│   │   └── dbs_factsheet.md
│   │
│   ├── capitaland/
│   │   ├── capitaland_chunks.json
│   │   ├── capitaland_chunks_inspection.txt
│   │   └── capitaland_factsheet.md
│   │
│   ├── grab/
│   │   ├── grab_chunks.json
│   │   ├── grab_chunks_inspection.txt
│   │   └── grab_factsheet.md
│   │
│   └── sq/
│       ├── sq_chunks.json
│       ├── sq_chunks_inspection.txt
│       └── sq_factsheet.md
│
├── logs/
├── tests/
├── question_set.md                         
├── requirements.txt
├── .gitignore
└── README.md                         
```

## Workflow
```
  The Pipeline Flow

  1. PDF File
     ↓
  2. markdown_converter.py → Markdown File (one big document)
     ↓
  3. extract.py → Chunks JSON (many small searchable pieces)
     ↓
  4. semantic_chunker.py → Merged Chunks (semantically combined)
     ↓
  5. generate_factsheet.py → Uses chunks for RAG
     ↓
  6. llm_evaluation.py
```