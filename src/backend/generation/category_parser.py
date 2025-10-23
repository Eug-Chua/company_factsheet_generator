"""
Category Parser
Parses question set structure and extracts keywords dynamically
"""

from pathlib import Path
from typing import List, Dict, Optional


class CategoryParser:
    """Parses question set structure and builds category configuration"""

    def __init__(self, config, logger):
        """Initialize category parser"""
        self.config = config
        self.logger = logger
        self._category_structure = None

    def _read_question_file(self, question_path: Path):
        """Read question file lines"""
        with open(question_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def _is_part_marker(self, line: str):
        """Check if line is a PART marker"""
        return line.startswith('## PART')

    def _is_subsection_header(self, line: str):
        """Check if line is a subsection header"""
        return line.startswith('###') and line.isupper()

    def _is_question_line(self, line: str):
        """Check if line is a question"""
        if not line.startswith('###'):
            return False
        q_part = line.replace('###', '').strip().split('.')[0].strip()
        return q_part.isdigit()

    def _extract_question_number(self, line: str):
        """Extract question number from line"""
        q_num_str = line.replace('###', '').strip().split('.')[0].strip()
        try:
            return int(q_num_str)
        except ValueError:
            return None

    def _get_subsection_mapping(self):
        """Get subsection to category mapping"""
        return {'INCOME STATEMENT': 'Income Statement Data', 'CASH FLOW METRICS': 'Calculated Metrics - Cash Flow',
                'CASH FLOW DATA': 'Cash Flow Data', 'CASH FLOW': 'Cash Flow Data',
                'BALANCE SHEET - ASSETS': 'Balance Sheet - Assets', 'BALANCE SHEET - LIABILITIES': 'Balance Sheet - Liabilities',
                'DEBT DETAILS': 'Debt Details', 'PROFITABILITY METRICS': 'Calculated Metrics - Profitability',
                'GROWTH METRICS': 'Calculated Metrics - Growth', 'LEVERAGE RATIOS': 'Calculated Metrics - Leverage',
                'LIQUIDITY RATIOS': 'Calculated Metrics - Liquidity', 'EFFICIENCY RATIOS': 'Calculated Metrics - Efficiency'}

    def _map_subsection_to_category(self, subsection: str):
        """Map subsection name to category name"""
        mapping = self._get_subsection_mapping()
        for key, category in mapping.items():
            if key in subsection:
                return category
        return None

    def _parse_part_marker(self, line: str):
        """Parse PART marker to get section name"""
        if 'BUSINESS FUNDAMENTALS' in line:
            return 'PART 1', 'Business Fundamentals'
        elif 'FINANCIAL DATA EXTRACTION' in line:
            return 'PART 2', None
        elif 'CALCULATED METRICS' in line:
            return 'PART 3', None
        return None, None

    def _close_category(self, categories: Dict, current_category: str,
                       question_numbers: List[int], current_section: str):
        """Close current category and save"""
        if current_category and question_numbers:
            categories[current_category] = {
                'questions': sorted(question_numbers),
                'section': current_section
            }

    def _merge_balance_sheet_categories(self, categories: Dict, merged: Dict):
        """Merge Balance Sheet subsections"""
        balance_sheet_cats = ['Balance Sheet - Assets', 'Balance Sheet - Liabilities', 'Debt Details']
        if any(cat in categories for cat in balance_sheet_cats):
            if 'Balance Sheet Data' not in merged:
                merged['Balance Sheet Data'] = {'questions': [], 'section': 'PART 2'}
            for cat in balance_sheet_cats:
                if cat in categories:
                    merged['Balance Sheet Data']['questions'].extend(categories[cat]['questions'])

    def _merge_liquidity_efficiency_categories(self, categories: Dict, merged: Dict):
        """Merge Liquidity and Efficiency into single category"""
        liquidity_cats = ['Calculated Metrics - Liquidity', 'Calculated Metrics - Efficiency']
        if any(cat in categories for cat in liquidity_cats):
            if 'Calculated Metrics - Liquidity & Efficiency' not in merged:
                merged['Calculated Metrics - Liquidity & Efficiency'] = {'questions': [], 'section': 'PART 3'}
            for cat in liquidity_cats:
                if cat in categories:
                    merged['Calculated Metrics - Liquidity & Efficiency']['questions'].extend(categories[cat]['questions'])

    def _build_category_range(self, cat_info: Dict):
        """Build category with range from question numbers"""
        q_nums = sorted(cat_info['questions'])
        if q_nums:
            return {'range': range(min(q_nums), max(q_nums) + 1), 'section': cat_info['section']}
        return None

    def _convert_to_ranges(self, merged_categories: Dict):
        """Convert question lists to ranges"""
        final_categories = {}
        for cat_name, cat_info in merged_categories.items():
            cat_range = self._build_category_range(cat_info)
            if cat_range:
                final_categories[cat_name] = cat_range
        return final_categories

    def _process_part_marker(self, categories, current_category, question_numbers, current_section, line_stripped):
        """Process PART marker line"""
        self._close_category(categories, current_category, question_numbers, current_section)
        current_section, current_category = self._parse_part_marker(line_stripped)
        return current_section, current_category, []

    def _process_subsection(self, categories, current_category, question_numbers, current_section, line_stripped):
        """Process subsection header line"""
        self._close_category(categories, current_category, question_numbers, current_section)
        subsection = line_stripped.replace('###', '').strip()
        current_category = self._map_subsection_to_category(subsection)
        return current_category, []

    def _process_question_line(self, line_stripped, current_category, question_numbers):
        """Process question line"""
        q_num = self._extract_question_number(line_stripped)
        if q_num and current_category:
            question_numbers.append(q_num)

    def _handle_subsection_line(self, categories, current_category, question_numbers, current_section, line_stripped):
        """Handle subsection header line"""
        cat, qnums = self._process_subsection(categories, current_category, question_numbers, current_section, line_stripped)
        return current_section, cat, qnums

    def _process_single_line(self, line_stripped, categories, current_category, current_section, question_numbers):
        """Process a single line and update state"""
        if self._is_part_marker(line_stripped):
            return self._process_part_marker(categories, current_category, question_numbers, current_section, line_stripped)
        elif self._is_subsection_header(line_stripped):
            return self._handle_subsection_line(categories, current_category, question_numbers, current_section, line_stripped)
        elif self._is_question_line(line_stripped):
            self._process_question_line(line_stripped, current_category, question_numbers)
        return current_section, current_category, question_numbers

    def _parse_lines(self, lines):
        """Parse all lines to extract categories"""
        categories, current_category, current_section, question_numbers = {}, None, None, []
        for line in lines:
            current_section, current_category, question_numbers = self._process_single_line(
                line.strip(), categories, current_category, current_section, question_numbers)
        self._close_category(categories, current_category, question_numbers, current_section)
        return categories

    def _get_excluded_categories(self):
        """Get list of categories to exclude from final result"""
        return ['Balance Sheet - Assets', 'Balance Sheet - Liabilities', 'Debt Details',
               'Calculated Metrics - Liquidity', 'Calculated Metrics - Efficiency']

    def _add_non_excluded_categories(self, categories, merged_categories, excluded):
        """Add categories that are not in exclusion list"""
        for cat_name, cat_info in categories.items():
            if cat_name not in excluded:
                merged_categories[cat_name] = cat_info

    def _merge_all_categories(self, categories):
        """Merge related categories"""
        merged_categories = {}
        self._merge_balance_sheet_categories(categories, merged_categories)
        self._merge_liquidity_efficiency_categories(categories, merged_categories)
        excluded = self._get_excluded_categories()
        self._add_non_excluded_categories(categories, merged_categories, excluded)
        return merged_categories

    def parse_question_set_structure(self, question_path: Optional[Path] = None) -> Dict:
        """Dynamically parse question_set structure from markdown file"""
        lines = self._read_question_file(Path(question_path or self.config.question_set_path))
        categories = self._parse_lines(lines)
        merged_categories = self._merge_all_categories(categories)
        final_categories = self._convert_to_ranges(merged_categories)
        self.logger.info(f"✓ Dynamically parsed {len(final_categories)} categories from question set")
        self._category_structure = final_categories
        return final_categories

    def _get_financial_terms(self):
        """Get standard financial terms to look for"""
        return {'revenue', 'sales', 'turnover', 'income', 'profit', 'loss', 'EBIT', 'EBITDA',
                'gross profit', 'operating profit', 'net profit', 'cost', 'expense',
                'assets', 'liabilities', 'equity', 'capital', 'cash', 'receivables', 'inventory',
                'debt', 'borrowings', 'loans', 'bonds', 'cash flow', 'capex', 'FCF',
                'margin', 'ratio', 'ROE', 'ROA', 'growth', 'leverage', 'coverage'}

    def _format_found_term(self, term: str):
        """Format term with quotes if multi-word"""
        return f'"{term}"' if ' ' in term else term

    def _find_terms_in_question(self, q_text_lower: str, financial_terms: set, found_terms: set):
        """Find financial terms in question text"""
        for term in financial_terms:
            if term.lower() in q_text_lower:
                found_terms.add(self._format_found_term(term))

    def _extract_terms_from_questions(self, questions: List[Dict], q_range: range, financial_terms: set):
        """Extract financial terms that appear in questions"""
        category_questions = [q for q in questions if q['number'] in q_range]
        found_terms = set()
        for q in category_questions:
            self._find_terms_in_question(q['text'].lower(), financial_terms, found_terms)
        return found_terms

    def _add_income_statement_keywords(self, found_terms: set, keyword_set: set):
        """Add income statement keywords if relevant"""
        if any(term in found_terms for term in ['revenue', 'profit', 'income', 'EBIT', 'EBITDA']):
            keyword_set.update(['"income statement"', '"statement of profit or loss"'])

    def _add_balance_sheet_keywords(self, found_terms: set, keyword_set: set):
        """Add balance sheet keywords if relevant"""
        if any(term in found_terms for term in ['assets', 'liabilities', 'equity', 'debt']):
            keyword_set.update(['"balance sheet"', '"statement of financial position"'])

    def _add_cash_flow_keywords(self, found_terms: set, keyword_set: set):
        """Add cash flow keywords if relevant"""
        if any(term in found_terms for term in ['cash flow', 'capex', 'FCF']):
            keyword_set.add('"cash flow statement"')

    def _add_statement_keywords(self, found_terms: set, keyword_set: set):
        """Add standard financial statement names if relevant"""
        self._add_income_statement_keywords(found_terms, keyword_set)
        self._add_balance_sheet_keywords(found_terms, keyword_set)
        self._add_cash_flow_keywords(found_terms, keyword_set)

    def _get_business_fundamentals_keywords(self):
        """Get keywords specifically for Business Fundamentals section"""
        # Simple keyword to avoid query pollution
        return 'information on the company'

    def extract_keywords_from_questions(self, questions: List[Dict], q_range: range) -> str:
        """Extract financial keywords from question text automatically"""
        financial_terms = self._get_financial_terms()
        found_terms = self._extract_terms_from_questions(questions, q_range, financial_terms)
        keyword_set = set(found_terms)
        self._add_statement_keywords(found_terms, keyword_set)
        keywords_str = ' '.join(sorted(keyword_set))
        return keywords_str if keywords_str else 'financial data annual report'

    def _build_category_config_entry(self, cat_info: Dict, questions: List[Dict], category_name: str):
        """Build single category config entry"""
        q_range = cat_info['range']

        # Use category-specific keywords for Business Fundamentals
        if category_name == 'Business Fundamentals':
            keywords = self._get_business_fundamentals_keywords()
        else:
            keywords = self.extract_keywords_from_questions(questions, q_range)

        return {'range': q_range, 'keywords': keywords}

    def get_categories_config(self, questions: List[Dict]) -> Dict:
        """Get categories with ranges and dynamically extracted keywords"""
        if not self._category_structure:
            self._category_structure = self.parse_question_set_structure()
        categories_config = {cat_name: self._build_category_config_entry(cat_info, questions, cat_name)
                            for cat_name, cat_info in self._category_structure.items()}
        self.logger.info(f"✓ Built dynamic config for {len(categories_config)} categories")
        return categories_config

    def get_category_ranges(self) -> Dict:
        """Get question category ranges (dynamically parsed from question set)"""
        if not self._category_structure:
            self._category_structure = self.parse_question_set_structure()
        return {cat_name: cat_info['range']
                for cat_name, cat_info in self._category_structure.items()}
