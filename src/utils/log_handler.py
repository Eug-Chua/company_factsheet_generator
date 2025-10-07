"""
Custom Log Handler
"""

import logging
from pathlib import Path

class LogHandler(logging.FileHandler):
    def __init__(self, file_name, max_lines=3000, mode='a', encoding=None, delay=False):
        self.base_filename = Path(file_name)
        self.max_lines = max_lines
        self.current_file_number = self._find_active_file()
        actual_filename = self._build_filename()
        super().__init__(actual_filename, mode, encoding, delay)

    def _count_lines(self, file_path: Path) -> int:
        """Count number of lines in file"""
        if not file_path.exists():
            return 0
        try:
            with open(file_path, 'r') as file:
                return sum(1 for _ in file)
        except Exception:
            return 0
        
    def _has_space(self, file_path: Path) -> bool:
        """Checks if file has space"""
        return self._count_lines(file_path) < self.max_lines

    def _extract_file_number(self, file_path: Path, base_name:str) ->int :
        """Extract log file's number"""
        name = file_path.stem
        if name == base_name:
            return 1
        num_str = file_path.stem.split('_')[-1]
        if num_str.isdigit():
            return int(num_str)
        return -1

    def _is_valid_log_file(self, file: Path, base_name: str) -> bool:
        """Check if log file is valid"""
        return self._extract_file_number(file, base_name) != -1

    def _build_filename(self) -> Path:
        """Build the file name to use"""
        if self.current_file_number == 1:
            return self.base_filename
        base_name = self.base_filename.stem
        base_ext = self.base_filename.suffix
        return self.base_filename.parent / f"{base_name}_{self.current_file_number}{base_ext}"

    def _find_active_file(self) -> int:
        """Find the current log file number to use"""
        base_dir = self.base_filename.parent
        base_name = self.base_filename.stem
        base_ext = self.base_filename.suffix

        if not base_dir.exists():
            return 1
        
        max_num = 0
        for file in sorted(base_dir.glob(f"{base_name}*{base_ext}")):
            if not self._is_valid_log_file(file, base_name):
                continue
            num = self._extract_file_number(file, base_name)
            max_num = max(max_num, num)
            if self._has_space(file):
                return num

        return max_num + 1 if max_num > 0 else 1

    def _rotate_file(self):
        """Rotate to next file"""
        self.close()
        self.current_file_number += 1
        self.baseFilename = str(self._build_filename())
        self.stream = self._open()

    def emit(self, record):
        """Outputs the record to the file"""
        current_lines = self._count_lines(Path(self.baseFilename))
        if current_lines >= self.max_lines:
            self._rotate_file()
        super().emit(record)