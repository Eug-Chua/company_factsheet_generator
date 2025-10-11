"""
Keyword Analyzer
Handles financial keyword detection and coverage analysis
"""

from typing import Dict, List


class KeywordAnalyzer:
    """Analyzes financial keywords in extracted text"""

    def __init__(self):
        """Initialize keyword analyzer"""
        pass

    def _get_keyword_categories(self) -> Dict:
        """Get financial keyword categories"""
        return {
            "Income Statement": [
                "revenue", "gross profit", "operating profit", "EBIT", "EBITDA",
                "net income", "net profit", "earnings per share", "EPS",
                "cost of sales", "operating expenses", "income statement"
            ],
            "Balance Sheet": [
                "total assets", "current assets", "non-current assets",
                "total liabilities", "current liabilities", "shareholders equity",
                "share capital", "retained earnings", "balance sheet"
            ],
            "Cash Flow": [
                "cash flow", "operating cash flow", "investing cash flow",
                "financing cash flow", "free cash flow", "FCF",
                "cash and cash equivalents", "cash flow statement"
            ],
            "Debt & Leverage": [
                "total debt", "long-term debt", "short-term debt",
                "net debt", "debt to equity", "interest coverage",
                "borrowings", "financial liabilities"
            ],
            "Profitability Ratios": [
                "ROE", "ROA", "ROCE", "return on equity", "return on assets",
                "profit margin", "operating margin", "net margin"
            ],
            "Corporate Governance": [
                "board of directors", "independent directors", "audit committee",
                "remuneration", "corporate governance", "shareholders",
                "related party transactions"
            ]
        }

    def _get_keyword_variants(self, keyword: str) -> List[str]:
        """Get common variations of financial keywords"""
        variants_map = {
            "cash flow statement": ["cash flow statement", "statement of cash flows", "consolidated statement of cash flows", "consolidated cash flow"],
            "operating cash flow": ["operating cash flow", "cash from operating", "cash from operations", "cash flows from operating activities"],
            "investing cash flow": ["investing cash flow", "cash from investing", "cash flows from investing activities"],
            "financing cash flow": ["financing cash flow", "cash from financing", "cash flows from financing activities"],
            "free cash flow": ["free cash flow", "fcf"],
            "income statement": ["income statement", "statement of profit or loss", "consolidated income statement", "statement of comprehensive income"],
            "balance sheet": ["balance sheet", "statement of financial position", "consolidated balance sheet"],
            "total debt": ["total debt", "total borrowings", "total financial liabilities"],
            "long-term debt": ["long-term debt", "non-current borrowings", "non-current financial liabilities"],
            "short-term debt": ["short-term debt", "current borrowings", "current portion"],
            "shareholders equity": ["shareholders equity", "total equity", "equity attributable"],
        }
        return variants_map.get(keyword.lower(), [keyword])

    def _keyword_matches(self, text_lower: str, keyword: str) -> bool:
        """Check if keyword or its variants are present in text"""
        variants = self._get_keyword_variants(keyword)
        return any(variant.lower() in text_lower for variant in variants)

    def _check_category_keywords(self, text_lower: str, keywords: List[str]) -> Dict:
        """Check keyword presence for a category with variant support"""
        found = [kw for kw in keywords if self._keyword_matches(text_lower, kw)]
        missing = [kw for kw in keywords if not self._keyword_matches(text_lower, kw)]
        return {
            'found': found,
            'missing': missing,
            'coverage': len(found) / len(keywords) if keywords else 0
        }

    def _calculate_overall_coverage(self, results: Dict, keyword_categories: Dict) -> Dict:
        """Calculate overall keyword coverage"""
        total_found = sum(len(cat['found']) for cat in results.values())
        total_keywords = sum(len(keywords) for keywords in keyword_categories.values())
        return {
            'total_found': total_found,
            'total_keywords': total_keywords,
            'coverage': total_found / total_keywords if total_keywords else 0
        }

    def check_keyword_presence(self, text: str) -> Dict:
        """Check for presence of critical financial keywords"""
        keyword_categories = self._get_keyword_categories()
        text_lower = text.lower()
        results = {}
        for category, keywords in keyword_categories.items():
            results[category] = self._check_category_keywords(text_lower, keywords)
        results['overall'] = self._calculate_overall_coverage(results, keyword_categories)
        return results
