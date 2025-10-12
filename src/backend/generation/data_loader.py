"""
Data Loader
Loads questions and chunks from files
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class DataLoader:
    """Loads questions and chunks for factsheet generation"""

    def __init__(self, config, logger):
        """Initialize data loader"""
        self.config = config
        self.logger = logger

    def _clean_question_line(self, line: str):
        """Clean and strip question line"""
        line = line.strip()
        if line.startswith('###'):
            line = line.replace('###', '').strip()
        return line

    def _extract_question_parts(self, line: str):
        """Extract question number and text"""
        parts = line.split('. ', 1)
        if len(parts) == 2:
            return {'number': int(parts[0]), 'text': parts[1]}
        return None

    def _parse_question_line(self, line: str) -> Optional[Dict]:
        """Parse a single question line"""
        line = self._clean_question_line(line)
        if line and line[0].isdigit() and '. ' in line:
            return self._extract_question_parts(line)
        return None

    def _read_question_file(self, question_path: Path):
        """Read question file content"""
        with open(question_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_questions_from_content(self, content: str):
        """Parse questions from file content"""
        questions = []
        for line in content.split('\n'):
            q = self._parse_question_line(line)
            if q:
                questions.append(q)
        return questions

    def _validate_question_path(self, question_path: Path):
        """Validate question path exists"""
        if not question_path.exists():
            raise FileNotFoundError(f"Question set not found: {question_path}")

    def load_questions(self, question_path: Optional[Path] = None) -> List[Dict]:
        """Load questions from question_set.md"""
        question_path = Path(question_path or self.config.question_set_path)
        self._validate_question_path(question_path)
        content = self._read_question_file(question_path)
        questions = self._parse_questions_from_content(content)
        self.logger.info(f"Loaded {len(questions)} questions")
        return questions

    def _read_chunks_file(self, chunks_path: Path):
        """Read chunks from JSON file"""
        with open(chunks_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_table_chunks_path(self, chunks_path: Path):
        """Get path to table chunks file"""
        return chunks_path.parent / f"{chunks_path.stem}_table_chunks.json"

    def _load_table_chunks(self, table_chunks_path: Path):
        """Load table chunks if file exists"""
        if table_chunks_path.exists():
            with open(table_chunks_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _log_chunks_loaded(self, text_chunks, table_chunks):
        """Log chunks loading summary"""
        self.logger.info(f"Loaded {len(text_chunks)} text chunks")
        if table_chunks:
            self.logger.info(f"Loaded {len(table_chunks)} table chunks")
        else:
            self.logger.warning("No table chunks file found")

    def _validate_chunks_path(self, chunks_path: Path):
        """Validate chunks path exists"""
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    def _is_merged_or_semantic_chunks(self, chunks_path: Path):
        """Check if chunks file is already merged (contains both text and tables)"""
        filename = chunks_path.stem.lower()
        return 'merged' in filename or 'semantic' in filename

    def _load_text_and_table_chunks(self, chunks_path: Path):
        """Load both text and table chunks"""
        text_chunks = self._read_chunks_file(chunks_path)

        # If this is a merged/semantic file, chunks already contain both text and tables
        if self._is_merged_or_semantic_chunks(chunks_path):
            self.logger.info(f"Loaded {len(text_chunks)} chunks (already merged - text + tables)")
            return text_chunks, []

        # Otherwise, try to load separate table chunks
        table_chunks_path = self._get_table_chunks_path(chunks_path)
        table_chunks = self._load_table_chunks(table_chunks_path)
        return text_chunks, table_chunks

    def _combine_and_log_chunks(self, text_chunks: List[Dict], table_chunks: List[Dict]):
        """Combine chunks and log total"""
        all_chunks = text_chunks + table_chunks
        if table_chunks:
            self.logger.info(f"✓ Total chunks: {len(all_chunks)} ({len(text_chunks)} text + {len(table_chunks)} tables)")
        else:
            self.logger.info(f"✓ Total chunks: {len(all_chunks)}")
        return all_chunks

    def load_chunks(self, chunks_path: Optional[Path] = None) -> List[Dict]:
        """Load chunks from JSON files (both text and table chunks)"""
        chunks_path = Path(chunks_path or self.config.chunks_path)
        self._validate_chunks_path(chunks_path)
        text_chunks, table_chunks = self._load_text_and_table_chunks(chunks_path)
        if table_chunks:
            self._log_chunks_loaded(text_chunks, table_chunks)
        return self._combine_and_log_chunks(text_chunks, table_chunks)
