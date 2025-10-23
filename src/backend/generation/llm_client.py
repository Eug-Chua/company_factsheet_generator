"""
LLM Client
Handles API calls to OpenAI, Anthropic, and Ollama
"""

import os
import requests
from openai import OpenAI
from anthropic import Anthropic


class LLMClient:
    """Unified LLM client for OpenAI, Anthropic, and Ollama"""

    def __init__(self, config, logger):
        """Initialize LLM client with configuration"""
        self.config = config
        self.logger = logger
        self.llm_provider = self._get_provider()
        self._initialize_client()

    def _get_provider(self):
        """Get LLM provider from config"""
        return self.config.config.get('llm_provider', 'openai')

    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.llm_provider == 'openai':
            self._init_openai()
        elif self.llm_provider == 'anthropic':
            self._init_anthropic()
        elif self.llm_provider == 'ollama':
            self._init_ollama()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}. Use 'openai', 'anthropic', or 'ollama'.")

    def _init_openai(self):
        """Initialize OpenAI API client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.openai = OpenAI(api_key=api_key)
        self.openai_model = self.config.config.get('openai_model', 'gpt-4o-mini')
        self.logger.info(f"Using OpenAI API with model: {self.openai_model}")

    def _init_anthropic(self):
        """Initialize Anthropic API client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.anthropic = Anthropic(api_key=api_key)
        self.anthropic_model = self.config.config.get('anthropic_model', 'claude-sonnet-4-5-20250929')
        self.logger.info(f"Using Anthropic API with model: {self.anthropic_model}")

    def _init_ollama(self):
        """Initialize Ollama local client"""
        self.ollama_url = self.config.config.get('ollama_url', 'http://localhost:11434')
        self.ollama_model = self.config.config.get('ollama_model', 'qwen2.5:32b')
        self.logger.info(f"Using Ollama with model: {self.ollama_model} at {self.ollama_url}")

    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Call OpenAI API"""
        response = self.openai.chat.completions.create(
            model=self.openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0
        )
        return response.choices[0].message.content.strip()

    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic API"""
        response = self.anthropic.messages.create(
            model=self.anthropic_model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

    def _build_ollama_request(self, prompt: str, max_tokens: int):
        """Build Ollama API request payload"""
        return {"model": self.ollama_model, "prompt": prompt, "stream": False,
                "options": {"temperature": 0, "num_predict": max_tokens}}

    def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """Call Ollama API"""
        response = requests.post(f"{self.ollama_url}/api/generate",
                                json=self._build_ollama_request(prompt, max_tokens))
        response.raise_for_status()
        return response.json()['response']

    def call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """Unified LLM caller - works with OpenAI, Anthropic, or Ollama"""
        if self.llm_provider == 'openai':
            return self._call_openai(prompt, max_tokens)
        elif self.llm_provider == 'anthropic':
            return self._call_anthropic(prompt, max_tokens)
        elif self.llm_provider == 'ollama':
            return self._call_ollama(prompt, max_tokens)
