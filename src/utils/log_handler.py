"""
Custom Log Handler
"""

import logging
from pathlib import Path

def _count_lines(self, file_path: Path) -> int:
    """Count number of lines in file"""
    if not file_path.exists():
        return 0
    try:
        with open(file_path, 'r') as file:
            return sum(1 for _ in file)
    except Exception:
        return 0