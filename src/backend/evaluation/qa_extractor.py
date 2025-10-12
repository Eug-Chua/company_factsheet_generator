"""
QA Extractor
Extracts Q&A pairs from factsheet markdown
"""

from typing import List, Dict, Optional


class QAExtractor:
    """Extracts Q&A pairs from markdown factsheet"""

    def __init__(self, logger):
        """Initialize QA extractor"""
        self.logger = logger

    def _save_qa_pair(self, qa_pairs: List[Dict], current_number: int, current_question: str, current_answer: List[str]):
        """Save a Q&A pair to the list"""
        if current_question and current_answer:
            qa_pairs.append({
                'number': current_number,
                'question': current_question,
                'answer': '\n'.join(current_answer).strip()
            })

    def _parse_question_header(self, line: str) -> tuple[Optional[int], Optional[str]]:
        """Parse question header line"""
        header = line.replace('###', '').strip()
        parts = header.split('. ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            return int(parts[0]), parts[1]
        return None, None

    def extract_qa_pairs(self, factsheet_content: str) -> List[Dict]:
        """Extract Q&A pairs from factsheet markdown"""
        qa_pairs = []
        lines = factsheet_content.split('\n')
        current_question = None
        current_answer = []
        current_number = None
        for line in lines:
            if line.startswith('### ') and '. ' in line:
                self._save_qa_pair(qa_pairs, current_number, current_question, current_answer)
                current_number, current_question = self._parse_question_header(line)
                current_answer = []
            elif current_question and line.strip() and not line.startswith('#'):
                current_answer.append(line)
        self._save_qa_pair(qa_pairs, current_number, current_question, current_answer)
        self.logger.info(f"Extracted {len(qa_pairs)} Q&A pairs")
        return qa_pairs
