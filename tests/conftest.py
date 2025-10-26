"""
Pytest configuration and shared fixtures
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock
import pandas as pd
import numpy as np


# ============================================================================
# Directory Fixtures
# ============================================================================

@pytest.fixture
def tests_dir():
    """Return path to tests directory"""
    return Path(__file__).parent


@pytest.fixture
def fixtures_dir(tests_dir):
    """Return path to fixtures directory"""
    return tests_dir / "fixtures"


@pytest.fixture
def src_dir(tests_dir):
    """Return path to src/backend directory"""
    return tests_dir.parent / "src" / "backend"


# ============================================================================
# Data Fixtures - Load from Files
# ============================================================================

@pytest.fixture
def sample_markdown(fixtures_dir):
    """Load sample markdown file"""
    with open(fixtures_dir / "sample_markdown.md") as f:
        return f.read()


@pytest.fixture
def sample_tables(fixtures_dir):
    """Load sample tables JSON"""
    with open(fixtures_dir / "sample_tables.json") as f:
        return json.load(f)


@pytest.fixture
def sample_chunks(fixtures_dir):
    """Load sample chunks JSON"""
    with open(fixtures_dir / "sample_chunks.json") as f:
        return json.load(f)


@pytest.fixture
def sample_questions(fixtures_dir):
    """Load sample questions markdown"""
    with open(fixtures_dir / "sample_questions.md") as f:
        return f.read()


# ============================================================================
# Mock Object Fixtures
# ============================================================================

@pytest.fixture
def mock_logger():
    """Return a mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_config():
    """Return a mock configuration object"""
    config = Mock()
    config.config = {
        'llm_provider': 'openai',
        'openai_model': 'gpt-4o-mini',
        'anthropic_model': 'claude-sonnet-4-5-20250929',
        'embedding_model': 'text-embedding-3-small'
    }
    config.chunking_config = {
        'min_chunk_size': 200,
        'max_chunk_size': 2000
    }
    config.setup_logger = Mock(return_value=Mock())
    return config


# ============================================================================
# Data Structure Fixtures - In-Memory
# ============================================================================

@pytest.fixture
def simple_dataframe():
    """Return a simple pandas DataFrame"""
    return pd.DataFrame({
        'Property, plant and equipment': ['US$50,000', 'US$220,000'],
        'Intangible assets': ['US$100,000', 'US$500,000'],
        'Investment properties': ['US$200,000', 'US$600,000']
    })


@pytest.fixture
def duplicate_columns_dataframe():
    """Return a DataFrame with duplicate column names"""
    return pd.DataFrame(
        [['US$100,000', 'US$500,000', 'US$100,000']],
        columns=['Intangible assets', 'Intangible assets', 'Intangible assets']
    )


@pytest.fixture
def sample_text_chunks():
    """Return sample text chunks for testing"""
    return [
        {
            "id": 0,
            "content": "The company's revenue grew by 15% in 2024.",
            "section_header": "Financial Performance",
            "is_table": False
        },
        {
            "id": 1,
            "content": "Net income increased to $780 million.",
            "section_header": "Financial Performance",
            "is_table": False
        },
        {
            "id": 2,
            "content": "The company operates in three segments.",
            "section_header": "Business Overview",
            "is_table": False
        }
    ]


@pytest.fixture
def sample_table_chunks():
    """Return sample table chunks for testing"""
    return [
        {
            "id": 0,
            "content": "| Year | Revenue |\n|------|--------|\n| 2024 | $5.2B |",
            "section_header": "Financial Data",
            "is_table": True
        }
    ]


# ============================================================================
# Embedding Fixtures
# ============================================================================

@pytest.fixture
def sample_embeddings():
    """Return sample embeddings (normalized vectors)"""
    return [
        np.array([1.0, 0.0, 0.0]),     # Vector 1
        np.array([0.9, 0.1, 0.0]),     # Similar to Vector 1
        np.array([0.0, 1.0, 0.0]),     # Orthogonal to Vector 1
        np.array([0.0, 0.0, 1.0])      # Another orthogonal vector
    ]


@pytest.fixture
def identical_embeddings():
    """Return identical embeddings for testing similarity"""
    vec = np.array([0.5, 0.5, 0.5])
    return [vec, vec.copy()]


@pytest.fixture
def orthogonal_embeddings():
    """Return orthogonal embeddings (similarity = 0)"""
    return [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0])
    ]


# ============================================================================
# Mock API Response Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_embedding_response():
    """Return a mock OpenAI embedding API response"""
    mock_response = Mock()
    mock_response.data = [
        Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5]),
        Mock(embedding=[0.6, 0.7, 0.8, 0.9, 1.0])
    ]
    return mock_response


@pytest.fixture
def mock_openai_chat_response():
    """Return a mock OpenAI chat completion response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is a test response from the LLM."
    return mock_response


@pytest.fixture
def mock_anthropic_response():
    """Return a mock Anthropic messages API response"""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "This is a test response from Claude."
    return mock_response


# ============================================================================
# Docling Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_docling_table():
    """Return a mock Docling table object"""
    mock_table = Mock()

    # Mock DataFrame export
    df = pd.DataFrame({
        'Column A': ['Value 1', 'Value 2'],
        'Column B': ['Value 3', 'Value 4']
    })
    mock_table.export_to_dataframe.return_value = df

    # Mock provenance
    mock_prov = Mock()
    mock_prov.page = 10
    mock_table.prov = [mock_prov]

    return mock_table


@pytest.fixture
def mock_docling_result(mock_docling_table):
    """Return a mock Docling conversion result"""
    mock_result = Mock()

    # Mock markdown export
    mock_result.document.export_to_markdown.return_value = "# Test Document\n\nThis is test content."

    # Mock tables
    mock_result.document.tables = [mock_docling_table]

    return mock_result


# ============================================================================
# RAGAS Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_ragas_dataset():
    """Return a mock RAGAS dataset"""
    return {
        "question": [
            "What was the revenue in 2024?",
            "What is the EBITDA margin?"
        ],
        "answer": [
            "Revenue in 2024 was $5.2 billion.",
            "EBITDA margin was 22%."
        ],
        "contexts": [
            ["Total revenue for 2024 reached $5.2 billion."],
            ["EBITDA margin expanded to 22%."]
        ],
        "ground_truth": [None, None]
    }


@pytest.fixture
def mock_ragas_scores():
    """Return mock RAGAS evaluation scores"""
    return {
        "faithfulness": [0.95, 0.88],
        "answer_relevancy": [0.92, 0.85],
        "context_precision": [0.80, 0.75],
        "context_recall": [0.90, 0.87]
    }


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Pure unit tests (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with mocked APIs"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (end-to-end, manual validation)"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require real API keys"
    )
