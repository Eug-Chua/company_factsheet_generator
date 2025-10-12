"""
Data Loader
Loads factsheets, chunks, and QA pairs for evaluation
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class DataLoader:
    """Loads data files for evaluation"""

    def __init__(self, config, logger):
        """Initialize data loader"""
        self.config = config
        self.logger = logger

    def load_factsheet(self, factsheet_path: Optional[Path] = None) -> str:
        """Load factsheet markdown file"""
        factsheet_path = factsheet_path or self.config.factsheet_path
        factsheet_path = Path(factsheet_path)
        if not factsheet_path.exists():
            raise FileNotFoundError(f"Factsheet not found: {factsheet_path}")
        with open(factsheet_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.logger.info(f"Loaded factsheet: {factsheet_path}")
        return content

    def load_chunks(self, chunks_path: Optional[Path] = None) -> List[Dict]:
        """Load chunks from JSON file"""
        chunks_path = chunks_path or self.config.chunks_path
        chunks_path = Path(chunks_path)
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        self.logger.info(f"Loaded {len(chunks)} chunks")
        return chunks

    def load_qa_pairs_with_chunks(self) -> List[Dict]:
        """Load QA pairs with their retrieved chunks from generation"""
        qa_path = self.config.output_dir / f"{self.config.company_name}_qa_pairs.json"
        if not qa_path.exists():
            raise FileNotFoundError(f"QA pairs file not found: {qa_path}")
        with open(qa_path, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        self.logger.info(f"Loaded {len(qa_pairs)} QA pairs with retrieved chunks")
        return qa_pairs
