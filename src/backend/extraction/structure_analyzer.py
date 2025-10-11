"""
Structure Analyzer
Analyzes markdown document structure and builds hierarchical paths
"""

import re
from typing import List, Dict


class StructureAnalyzer:
    """Analyzes markdown document structure"""

    def __init__(self):
        """Initialize structure analyzer"""
        pass

    def _create_header_dict(self, match) -> Dict:
        """Create header dictionary from regex match"""
        return {'level': len(match.group(1)), 'title': match.group(2).strip(),
                'start_pos': match.start(), 'end_pos': match.end()}

    def find_headers(self, markdown_text: str) -> List[Dict]:
        """Find all markdown headers in text"""
        header_pattern = r'^(#{1,6})\s+(.+)$'
        return [self._create_header_dict(m)
                for m in re.finditer(header_pattern, markdown_text, re.MULTILINE)]

    def _update_stack_for_header(self, stack, header):
        """Update stack by popping higher/equal level headers"""
        while stack and stack[-1]['level'] >= header['level']:
            stack.pop()
        stack.append({'level': header['level'], 'title': header['title']})

    def _build_parent_stack(self, headers_list: List[Dict], current_idx: int) -> List[Dict]:
        """Build stack of parent headers up to current position"""
        stack = []
        for i in range(current_idx + 1):
            self._update_stack_for_header(stack, headers_list[i])
        return stack

    def build_header_stack(self, headers_list: List[Dict], current_idx: int) -> str:
        """Build hierarchical header path from root to current position"""
        if not headers_list:
            return "Document"
        stack = self._build_parent_stack(headers_list, current_idx)
        return ' > '.join([h['title'] for h in stack])

    def get_section_content(self, markdown_text: str, headers: List[Dict], index: int) -> str:
        """Extract content for a section between headers"""
        header = headers[index]
        content_start = header['end_pos']
        content_end = headers[index + 1]['start_pos'] if index + 1 < len(headers) else len(markdown_text)
        return markdown_text[content_start:content_end].strip()
