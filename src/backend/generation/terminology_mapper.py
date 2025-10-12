"""
Terminology Mapper
Auto-detects and substitutes company-specific financial terminology
"""

import re
from typing import List, Dict


class TerminologyMapper:
    """Detects and maps company-specific financial terms"""

    def __init__(self, config, logger):
        """Initialize terminology mapper"""
        self.config = config
        self.logger = logger
        self.terminology_map = None

    def _get_term_variants(self):
        """Define standard terms and their possible variants"""
        return {"EBITDA": ["EBITDA", "adjusted EBITDA", "EBIT", "operating income", "operating profit"],
                "debt": ["total debt", "borrowings", "total borrowings", "debt obligations", "long-term debt", "short-term debt"],
                "capex": ["capital expenditure", "capex", "purchase of property", "additions to property", "PP&E"],
                "receivables": ["trade receivables", "accounts receivable", "trade and other receivables"],
                "inventory": ["inventory", "inventories", "stock"],
                "cash": ["cash and cash equivalents", "cash", "cash and bank balances"]}

    def _count_variant_in_chunks(self, variant: str, chunks: List[Dict]):
        """Count occurrences of variant in chunks (weighted by table priority)"""
        table_count = sum(1 for c in chunks if variant.lower() in c['content'].lower() and c.get('is_table', False))
        text_count = sum(1 for c in chunks if variant.lower() in c['content'].lower() and not c.get('is_table', False))
        return (table_count * 3) + text_count

    def _get_top_variants(self, variant_counts: Dict):
        """Get top 2 most common variants"""
        sorted_variants = sorted(variant_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_variants[:2]]

    def _add_variant_if_found(self, variant: str, chunks: List[Dict], variant_counts: Dict):
        """Add variant to counts if found in chunks"""
        total_weighted = self._count_variant_in_chunks(variant, chunks)
        if total_weighted > 0:
            variant_counts[variant] = total_weighted

    def _build_variant_counts(self, variants: List[str], chunks: List[Dict]):
        """Build dictionary of variant counts"""
        variant_counts = {}
        for variant in variants:
            self._add_variant_if_found(variant, chunks, variant_counts)
        return variant_counts

    def _detect_variants_for_term(self, standard_term: str, variants: List[str], chunks: List[Dict]):
        """Detect which variants are used for a standard term"""
        variant_counts = self._build_variant_counts(variants, chunks)
        if variant_counts:
            return self._get_top_variants(variant_counts)
        return None

    def _add_detected_term(self, standard_term: str, found_variants: List[str], detected_terms: Dict):
        """Add detected term to dictionary and log"""
        detected_terms[standard_term] = found_variants
        self.logger.debug(f"  {standard_term} → {found_variants}")

    def _process_term_variants(self, term_variants: Dict, chunks: List[Dict]):
        """Process all term variants and return detected terms"""
        detected_terms = {}
        for standard_term, variants in term_variants.items():
            found_variants = self._detect_variants_for_term(standard_term, variants, chunks)
            if found_variants:
                self._add_detected_term(standard_term, found_variants, detected_terms)
        return detected_terms

    def detect_company_terminology(self, chunks: List[Dict]) -> Dict:
        """Auto-detect which terminology variants exist in company's chunks"""
        term_variants = self._get_term_variants()
        detected_terms = self._process_term_variants(term_variants, chunks)
        self.terminology_map = detected_terms
        self.logger.info(f"✓ Auto-detected terminology for {self.config.company_name}")
        return detected_terms

    def _format_company_term(self, term: str):
        """Format company term with quotes if multi-word"""
        return f'"{term}"' if ' ' in term else term

    def _build_substitution_string(self, company_terms: List[str]):
        """Build substitution string from company terms"""
        return " ".join([self._format_company_term(term) for term in company_terms])

    def _substitute_single_term(self, keywords: str, standard_term: str, company_terms: List[str]):
        """Substitute a single standard term with company-specific terms"""
        company_terms_str = self._build_substitution_string(company_terms)
        pattern = re.compile(re.escape(standard_term), re.IGNORECASE)
        return pattern.sub(f"{standard_term} {company_terms_str}", keywords)

    def _should_substitute_term(self, standard_term: str, keywords: str):
        """Check if standard term should be substituted"""
        return standard_term.lower() in keywords.lower()

    def _apply_term_substitutions(self, keywords: str):
        """Apply all term substitutions to keywords"""
        substituted = keywords
        for standard_term, company_terms in self.terminology_map.items():
            if self._should_substitute_term(standard_term, keywords):
                substituted = self._substitute_single_term(substituted, standard_term, company_terms)
        return substituted

    def substitute_terms(self, keywords: str) -> str:
        """Substitute standard terms with company-specific detected terms"""
        if not self.terminology_map:
            return keywords
        return self._apply_term_substitutions(keywords)
