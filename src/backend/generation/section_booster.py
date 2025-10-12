"""
Section Booster
Applies section-aware and position-based boosting to similarity scores
"""

import math
from typing import List, Dict, Set


class SectionBooster:
    """Boosts retrieval scores based on document structure"""

    def __init__(self, logger):
        """Initialize section booster"""
        self.logger = logger

    def _get_industry_patterns(self):
        """Get section patterns for industry/sector questions"""
        return ['chairman', 'ceo', 'message', 'letter', 'shareholders', 'strategic',
                'business review', 'overview', 'operations', 'about us', 'who we are',
                'business model', 'our business', 'what we do']

    def _get_geographic_patterns(self):
        """Get section patterns for geographic questions"""
        return ['chairman', 'strategic', 'geographic', 'market', 'operations',
                'business review', 'segments', 'our network', 'where we operate']

    def _get_government_patterns(self):
        """Get section patterns for government ownership questions"""
        return ['ownership', 'shareholders', 'shareholder', 'capital structure',
                'share capital', 'major shareholders', 'substantial shareholders']

    def _get_business_model_patterns(self):
        """Get section patterns for business model questions"""
        return ['business model', 'operations', 'strategic', 'segments',
                'what we do', 'our business', 'revenue', 'business review']

    def _get_risk_patterns(self):
        """Get section patterns for risk questions"""
        return ['risk', 'principal risk', 'risk factor', 'risk management',
                'managing risk', 'key risks']

    def _get_legal_patterns(self):
        """Get section patterns for legal/regulatory questions"""
        return ['legal', 'litigation', 'contingent', 'commitments',
                'regulatory', 'compliance', 'environmental']

    def _get_default_patterns(self):
        """Get default section patterns"""
        return ['chairman', 'ceo', 'message', 'letter', 'strategic',
                'business review', 'overview']

    def get_section_patterns_for_question(self, question: str) -> List[str]:
        """Get relevant section header patterns based on question content"""
        question_lower = question.lower()
        if any(t in question_lower for t in ['industry', 'sector', 'operate in']):
            return self._get_industry_patterns()
        elif any(t in question_lower for t in ['geographic', 'markets', 'countries', 'regions']):
            return self._get_geographic_patterns()
        elif any(t in question_lower for t in ['government', 'ownership', 'sovereign', 'state-owned']):
            return self._get_government_patterns()
        elif any(t in question_lower for t in ['business model', 'revenue stream', 'primary revenue']):
            return self._get_business_model_patterns()
        elif any(t in question_lower for t in ['risk', 'principal risk']):
            return self._get_risk_patterns()
        elif any(t in question_lower for t in ['legal', 'regulatory', 'environmental', 'litigation']):
            return self._get_legal_patterns()
        else:
            return self._get_default_patterns()

    def _section_matches_pattern(self, section_header: str, patterns: List[str]):
        """Check if section header matches any pattern"""
        header_lower = section_header.lower()
        return any(pattern in header_lower for pattern in patterns)

    def detect_relevant_sections(self, chunks: List[Dict], patterns: List[str]) -> Set:
        """Find chunks whose section headers match the given patterns"""
        relevant_indices = set()
        for i, chunk in enumerate(chunks):
            if self._section_matches_pattern(chunk['section_header'], patterns):
                relevant_indices.add(i)
        return relevant_indices

    def _log_boosted_sections(self, relevant_indices: Set, chunks: List[Dict]):
        """Log sample of boosted sections"""
        if relevant_indices:
            sample_headers = [chunks[i]['section_header'] for i in list(relevant_indices)[:3]]
            self.logger.debug(f"  Boosting {len(relevant_indices)} chunks from relevant sections")
            self.logger.debug(f"  Sample sections: {sample_headers}")

    def boost_by_section_relevance(self, chunks: List[Dict], similarities,
                                   question: str, boost_factor: float = 0.8):
        """Apply section-aware boost to similarity scores"""
        patterns = self.get_section_patterns_for_question(question)
        relevant_indices = self.detect_relevant_sections(chunks, patterns)
        self._log_boosted_sections(relevant_indices, chunks)
        boosted_similarities = similarities.clone()
        for idx in relevant_indices:
            boosted_similarities[idx] = similarities[idx] * (1 + boost_factor)
        return boosted_similarities

    def _calculate_max_chunk_id(self, chunks: List[Dict]):
        """Get maximum chunk_id for normalization"""
        return max(chunk['chunk_id'] for chunk in chunks)

    def _calculate_boost_factor(self, chunk_id: int, max_chunk_id: int,
                                base_boost: float, decay_rate: float):
        """Calculate exponential decay boost factor"""
        normalized_position = chunk_id / max_chunk_id if max_chunk_id > 0 else 0.0
        return base_boost * math.exp(-decay_rate * normalized_position)

    def apply_document_structure_boost(self, chunks: List[Dict], similarities,
                                      base_boost: float = 0.3, decay_rate: float = 3.0):
        """Apply position-based boost to similarity scores"""
        max_chunk_id = self._calculate_max_chunk_id(chunks)
        boosted_similarities = similarities.clone()
        for i, chunk in enumerate(chunks):
            boost_factor = self._calculate_boost_factor(chunk['chunk_id'], max_chunk_id,
                                                        base_boost, decay_rate)
            boosted_similarities[i] = similarities[i] * (1 + boost_factor)
        return boosted_similarities
