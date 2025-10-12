"""
Model Initializer
Initializes RAGAS LLM, embeddings, and local embedder
"""

import os
from sentence_transformers import SentenceTransformer


class ModelInitializer:
    """Initializes models for RAGAS evaluation"""

    def __init__(self, config, logger):
        """Initialize model initializer"""
        self.config = config
        self.logger = logger
        self.ragas_llm = None
        self.ragas_embeddings = None
        self.embedder = None

    def _validate_openai_api_key(self):
        """Validate and set OpenAI API key"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found - required for RAGAS evaluation")
        os.environ['OPENAI_API_KEY'] = api_key

    def _init_ragas_llm(self):
        """Initialize RAGAS LLM with proper configuration"""
        from langchain_openai import ChatOpenAI
        self.ragas_llm = ChatOpenAI(model_name=self.config.openai_model, temperature=0.3, n=3, streaming=False)

    def _init_ragas_embeddings(self):
        """Initialize RAGAS embeddings"""
        from langchain_openai import OpenAIEmbeddings
        self.ragas_embeddings = OpenAIEmbeddings()

    def _init_local_embedder(self):
        """Initialize local embedding model for retrieval"""
        self.logger.info(f"Loading embedding model: {self.config.embedding_model}")
        self.embedder = SentenceTransformer(self.config.embedding_model)

    def _log_initialization(self):
        """Log initialization completion"""
        self.logger.info(f"RAGAS evaluation initialized with ChatOpenAI LLM (n={self.ragas_llm.n}, streaming={self.ragas_llm.streaming})")

    def initialize_models(self):
        """Initialize RAGAS and embedding model"""
        self._validate_openai_api_key()
        self._init_ragas_llm()
        self._init_ragas_embeddings()
        self._init_local_embedder()
        self._log_initialization()

    def get_ragas_llm(self):
        """Get RAGAS LLM"""
        return self.ragas_llm

    def get_ragas_embeddings(self):
        """Get RAGAS embeddings"""
        return self.ragas_embeddings

    def get_embedder(self):
        """Get local embedder"""
        return self.embedder
