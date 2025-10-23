"""
Question Range Parser
Parses question set to extract qualitative and quantitative ranges
"""

from pathlib import Path
from typing import Dict, List


class QuestionRangeParser:
    """Parses question set to determine qualitative vs quantitative ranges"""

    def __init__(self, config, logger):
        """Initialize question range parser"""
        self.config = config
        self.logger = logger
        self.qualitative_range = None
        self.quantitative_range = None

    def _set_default_ranges(self):
        """Set default question ranges"""
        self.qualitative_range = range(1, 10)
        self.quantitative_range = range(10, 61)

    def _detect_part_type(self, line: str):
        """Detect question part type from line"""
        if line.startswith('## PART 1:') and 'Qualitative' in line:
            return 'qualitative'
        elif line.startswith('## PART 2:') and 'Quantitative' in line:
            return 'quantitative'
        elif line.startswith('## PART 3:') and 'CALCULATED' in line:
            return 'quantitative'
        return None

    def _extract_question_number_from_line(self, line: str):
        """Extract question number from markdown line"""
        header = line.replace('###', '').strip()
        parts = header.split('. ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            return int(parts[0])
        return None

    def _process_question_line(self, line: str, current_part: str, part_questions: Dict):
        """Process a question line and add to part_questions"""
        if current_part and line.startswith('### ') and '. ' in line:
            question_num = self._extract_question_number_from_line(line)
            if question_num:
                part_questions[current_part].append(question_num)

    def _parse_question_content(self, content: str):
        """Parse file content to extract question numbers by part"""
        lines = content.split('\n')
        current_part = None
        part_questions = {'qualitative': [], 'quantitative': []}
        for line in lines:
            part_type = self._detect_part_type(line)
            if part_type:
                current_part = part_type
            self._process_question_line(line, current_part, part_questions)
        return part_questions

    def _build_range_from_questions(self, questions: List[int], default_range: range):
        """Build range from question list or return default"""
        if questions:
            return range(min(questions), max(questions) + 1)
        return default_range

    def _set_ranges_from_parsed(self, part_questions: Dict):
        """Set qualitative and quantitative ranges from parsed questions"""
        self.qualitative_range = self._build_range_from_questions(part_questions['qualitative'], range(1, 10))
        self.quantitative_range = self._build_range_from_questions(part_questions['quantitative'], range(10, 61))

    def _log_loaded_ranges(self, question_set_path: Path):
        """Log loaded question ranges"""
        self.logger.info(f"Loaded question ranges from {question_set_path.name}:")
        self.logger.info(f"  Qualitative: Q{self.qualitative_range.start}-Q{self.qualitative_range.stop - 1}")
        self.logger.info(f"  Quantitative: Q{self.quantitative_range.start}-Q{self.quantitative_range.stop - 1}")

    def load_question_ranges(self):
        """Parse question set file to extract qualitative and quantitative ranges dynamically"""
        question_set_path = self.config.question_set_path
        if not question_set_path.exists():
            self.logger.warning(f"Question set file not found: {question_set_path}. Using default ranges.")
            self._set_default_ranges()
            return
        with open(question_set_path, 'r', encoding='utf-8') as f:
            content = f.read()
        part_questions = self._parse_question_content(content)
        self._set_ranges_from_parsed(part_questions)
        self._log_loaded_ranges(question_set_path)

    def get_qualitative_range(self):
        """Get qualitative range"""
        return self.qualitative_range

    def get_quantitative_range(self):
        """Get quantitative range"""
        return self.quantitative_range
