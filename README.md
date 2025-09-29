 # Credit Analyst RAG System - Project Planning

  1. Project Scope & Requirements

  Input Sources:
  - Annual reports
  - Credit rating reports (Moody's, S&P, Fitch)
  - News articles & press releases
  - Industry reports

  Target Outputs:
  - 1-2 page factsheet with:
    - Business overview & segments
    - Geographic revenue breakdown
    - Credit ratings & outlook
    - Government support assessment
    - 3-year financial trends (revenue, EBITDA, debt)
    - Cash position & liquidity
    - Recent material developments
    - Risk assessment summary

  Success Metrics:
  - Accuracy on key financial metrics
  - Consistent formatting across factsheets

  2. System Architecture
    - Document Ingestion
        - PDF
        - APIs for company news
    - Processing Pipeline
        - Extract
        - Locate financial data
    - RAG System
        - Vector Store
        - Retrieval Query Router
    - Factsheet Generator
        - LLM Synthesis
        - LLM Eval

  3. Roadmap

  Foundation
  - Document processing pipeline
  - Financial data extraction & normalization
  - Basic RAG implementation
  - Simple factsheet template

  Intelligence
  - Financial ratio calculations
  - Time-series analysis ?
  - News sentiment integration ?

  Production
  - Automated workflows
  - Quality assurance
  - UI/UX

  4. Key Technologies

  Core Stack:
  - Document Processing: Docling
  - RAG: LangChain/LlamaIndex, ChromaDB/Pinecone
  - LLM: Claude/GPT-4 for synthesis
  - Financial Data: yfinance
  - News: NewsAPI, Bloomberg API ?

  Additional Tools:
  - FastAPI for backend
  - Streamlit/Gradio for UI
  - PostgreSQL for structured data
  - Redis for caching