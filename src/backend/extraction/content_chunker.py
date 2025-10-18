"""
Content Chunker
Handles content splitting, table detection, and chunk creation
"""

from typing import List, Dict, Optional


class ContentChunker:
    """Creates and manages content chunks"""

    def __init__(self, logger, min_chunk_size: int, max_chunk_size: int):
        """Initialize chunker with size constraints"""
        self.logger = logger
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def _is_chunk_too_small(self, content: str, section_header: str) -> bool:
        """Check if chunk is below minimum size"""
        if len(content.strip()) < self.min_chunk_size:
            self.logger.debug(
                f"Skipping small chunk ({len(content)} chars): {section_header[:50]}"
            )
            return True
        return False

    def create_chunk(
        self, chunk_id: int, section_header: str, header_level: int, content: str
    ) -> Optional[Dict]:
        """Create a chunk dictionary with validation"""
        if self._is_chunk_too_small(content, section_header):
            return None
        return {
            "chunk_id": chunk_id,
            "section_header": section_header,
            "header_level": header_level,
            "content": content,
        }

    def create_chunks_from_content(
        self,
        content_chunks: List[str],
        section_header: str,
        level: int,
        start_id: int = 0,
    ) -> List[Dict]:
        """Create chunks from split content"""
        chunks, chunk_id = [], start_id
        for chunk_content in content_chunks:
            chunk = self.create_chunk(chunk_id, section_header, level, chunk_content)
            if chunk:
                chunks.append(chunk)
                chunk_id += 1
        return chunks

    def _is_table_row(self, line: str) -> bool:
        """Check if a line is part of a markdown table"""
        return line.strip().startswith("|")

    def _collect_table_lines(
        self, lines: List[str], start_idx: int
    ) -> tuple[List[str], int]:
        """Collect all consecutive table lines"""
        table_lines, idx = [], start_idx
        while idx < len(lines) and self._is_table_row(lines[idx]):
            table_lines.append(lines[idx])
            idx += 1
        return table_lines, idx

    def _extract_table(self, lines: List[str], start_idx: int) -> tuple[str, int]:
        """Extract a complete markdown table starting from start_idx"""
        table_lines, end_idx = self._collect_table_lines(lines, start_idx)
        return "\n".join(table_lines), end_idx

    def _append_to_chunk(self, current_chunk: str, text: str) -> str:
        """Append text to current chunk with newline if needed"""
        if current_chunk:
            return current_chunk + "\n" + text
        return text

    def _should_split_chunk(self, current_chunk: str, line: str) -> bool:
        """Check if we should split chunk at this line"""
        if not current_chunk:
            return False
        if len(current_chunk) + len(line) + 1 <= self.max_chunk_size:
            return False
        return not line.strip()  # Split on empty lines (paragraph boundaries)

    def _process_table(
        self, lines: List[str], i: int, current_chunk: str, chunks: List[str]
    ) -> tuple[str, int]:
        """Process a table and update chunks"""
        table_text, end_idx = self._extract_table(lines, i)
        if (
            current_chunk
            and len(current_chunk) + len(table_text) + 1 > self.max_chunk_size
        ):
            chunks.append(current_chunk.strip())
            return table_text, end_idx
        return self._append_to_chunk(current_chunk, table_text), end_idx

    def _process_line(self, line: str, current_chunk: str, chunks: List[str]) -> str:
        """Process a regular line and update chunks"""
        if self._should_split_chunk(current_chunk, line):
            chunks.append(current_chunk.strip())
            return ""
        return self._append_to_chunk(current_chunk, line)

    def _finalize_chunks(self, chunks: List[str], current_chunk: str):
        """Finalize chunks list by adding remaining content"""
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

    def _process_lines_to_chunks(self, lines: List[str]) -> List[str]:
        """Process lines into chunks"""
        chunks, current_chunk, i = [], "", 0
        while i < len(lines):
            if self._is_table_row(lines[i]):
                current_chunk, i = self._process_table(lines, i, current_chunk, chunks)
            else:
                current_chunk = self._process_line(lines[i], current_chunk, chunks)
                i += 1
        self._finalize_chunks(chunks, current_chunk)
        return chunks

    def split_content(self, content: str) -> List[str]:
        """Split content into chunks respecting max size, paragraph boundaries, and tables"""
        if len(content) <= self.max_chunk_size:
            return [content]
        return self._process_lines_to_chunks(content.split("\n"))
