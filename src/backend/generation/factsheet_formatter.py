"""
Factsheet Formatter
Formats Q&A pairs into markdown factsheet
"""

from typing import List, Dict


class FactsheetFormatter:
    """Formats Q&A pairs into structured markdown"""

    def __init__(self, logger):
        """Initialize factsheet formatter"""
        self.logger = logger

    def _build_header(self, company_name: str):
        """Build factsheet header"""
        header = f"# {company_name.upper()} - Credit Analysis Factsheet\n\n"
        header += f"*Generated from annual report using RAG system*\n\n"
        header += "---\n\n"
        return header

    def _filter_qa_for_category(self, qa_pairs: List[Dict], q_range: range):
        """Filter Q&A pairs for specific category"""
        return [qa for qa in qa_pairs if qa['number'] in q_range]

    def _format_single_qa(self, qa: Dict):
        """Format a single Q&A pair"""
        formatted = f"### {qa['number']}. {qa['question']}\n\n"
        formatted += f"{qa['answer']}\n\n"
        return formatted

    def _format_category_section(self, category: str, q_range: range,
                                 qa_pairs: List[Dict]) -> str:
        """Format a single category section"""
        section = f"## {category}\n\n"
        category_qa = self._filter_qa_for_category(qa_pairs, q_range)
        for qa in category_qa:
            section += self._format_single_qa(qa)
        section += "---\n\n"
        return section

    def _sort_categories_by_question_order(self, categories: Dict):
        """Sort categories by their minimum question number"""
        return dict(sorted(categories.items(), key=lambda x: min(x[1])))

    def format_factsheet(self, qa_pairs: List[Dict], company_name: str,
                        categories: Dict) -> str:
        """Format Q&A pairs into a markdown factsheet"""
        markdown = self._build_header(company_name)
        sorted_categories = self._sort_categories_by_question_order(categories)
        for category, q_range in sorted_categories.items():
            markdown += self._format_category_section(category, q_range, qa_pairs)
        return markdown
