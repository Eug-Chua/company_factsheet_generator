"""
Table Chunker
Handles creating chunks from tables for RAG retrieval
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class TableChunker:
    """Creates chunks from table data"""

    def __init__(self, logger, config, table_loader):
        """Initialize chunker with logger, config, and table loader"""
        self.logger = logger
        self.config = config
        self.table_loader = table_loader

    # ========== Helper: Chunk Creation ==========

    def _add_chunk(
        self, chunks: List[Dict], section_header: str, content: str
    ):
        """Create a chunk and append to chunks list"""
        chunk = {
            "chunk_id": len(chunks),
            "section_header": section_header,
            "header_level": 0,
            "content": content,
            "content_type": "table",
        }
        chunks.append(chunk)

    def _create_section_header(self, table_idx: int, page, shape: Dict) -> str:
        """Create descriptive section header: 'Table X (Page Y): RxC'"""
        return f"Table {table_idx + 1} (Page {page}): {shape['rows']}×{shape['columns']}"

    # ========== Helper: Table Header/Data Separation ==========

    def _split_header_from_data(self, markdown: str) -> tuple[str, List[str]]:
        """
        Split markdown table into header and data rows.

        Header = first 2 lines + separator line (|---|)
        Data = all remaining lines
        """
        lines = markdown.split("\n")

        # First 2 lines + separator are header
        header_lines = []
        data_lines = []

        for i, line in enumerate(lines):
            if i < 2 or line.startswith("|---"):
                header_lines.append(line)
            else:
                data_lines.append(line)

        return "\n".join(header_lines), data_lines

    # ========== Core: Process Single Table ==========

    def _split_large_table(
        self, markdown: str, section_header: str,
        chunks: List[Dict], max_chunk_size: int
    ):
        """
        Split large table into multiple chunks, preserving header in each chunk.

        Strategy:
        1. Extract header (first 2 lines + separator)
        2. Add data rows one by one to current chunk
        3. When chunk is full, save it and start new chunk with header
        """
        header_text, data_rows = self._split_header_from_data(markdown)

        current_chunk = header_text
        part_num = 1

        for row in data_rows:
            # Check if this row fits in current chunk
            if len(current_chunk) + len(row) + 1 <= max_chunk_size:
                current_chunk += "\n" + row
            else:
                # Chunk is full - save it and start new chunk with header
                self._add_chunk(
                    chunks, f"{section_header} (Part {part_num})",
                    current_chunk
                )
                current_chunk = header_text + "\n" + row
                part_num += 1

        # Save final chunk
        if current_chunk.strip():
            self._add_chunk(
                chunks, f"{section_header} (Part {part_num})",
                current_chunk
            )

    def _process_single_table_to_chunks(
        self, table_idx: int, table_info: Dict,
        chunks: List[Dict], max_chunk_size: int
    ):
        """
        Convert one table into one or more chunks.

        Flow:
        1. Extract metadata (shape, page for section header)
        2. Small table → single chunk
        3. Large table → split with preserved headers
        """
        # Extract metadata (only needed for section header)
        shape = table_info["shape"]
        page = table_info["location"].get("page", "unknown")
        markdown = table_info["markdown"]
        section_header = self._create_section_header(table_idx, page, shape)

        # Small table - fits in single chunk
        if len(markdown) <= max_chunk_size:
            self._add_chunk(chunks, section_header, markdown)
            return

        # Large table - split into multiple parts
        self._split_large_table(
            markdown, section_header, chunks, max_chunk_size
        )

    # ========== Core: Process All Tables ==========

    def create_table_chunks(self, max_chunk_size: int = 2000) -> List[Dict]:
        """
        Convert all loaded tables to chunks for RAG retrieval.

        Returns:
            List of chunk dictionaries with IDs starting at 0
        """
        if not self.table_loader.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")

        chunks = []
        num_tables = len(self.table_loader.tables_data)
        self.logger.info(f"Creating chunks from {num_tables} tables...")

        for table_idx, (_, table_info) in enumerate(self.table_loader.tables_data.items()):
            self._process_single_table_to_chunks(
                table_idx, table_info,
                chunks, max_chunk_size
            )

        self.logger.info(f"✓ Created {len(chunks)} table chunks from {num_tables} tables")
        return chunks

    # ========== Pipeline: Save & Complete Process ==========

    def save_table_chunks(
        self, chunks: List[Dict], output_path: Optional[Path] = None
    ) -> Path:
        """
        Save table chunks to JSON file.

        Args:
            chunks: List of chunk dictionaries
            output_path: Optional custom output path

        Returns:
            Path where chunks were saved
        """
        # Determine output path
        if output_path is None:
            output_path = self.config.output_dir / f"{self.config.company_name}_table_chunks.json"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        self.logger.info(f"✓ Saved {len(chunks)} table chunks to: {output_path}")
        return output_path

    def process_tables_to_chunks(
        self, tables_path: Optional[Path] = None, max_chunk_size: int = 2000
    ) -> Dict:
        """
        Complete pipeline: load tables → create chunks → save.

        Returns:
            Dict with processing statistics:
            - num_tables: Number of tables processed
            - num_chunks: Number of chunks created
            - avg_chunk_size: Average chunk size in characters
            - output_path: Path where chunks were saved
        """
        # Load tables
        self.table_loader.load_tables(tables_path)

        # Create chunks
        chunks = self.create_table_chunks(max_chunk_size)

        # Save chunks
        output_path = self.save_table_chunks(chunks)

        # Return statistics
        avg_size = sum(len(c["content"]) for c in chunks) / len(chunks) if chunks else 0
        return {
            "num_tables": len(self.table_loader.tables_data),
            "num_chunks": len(chunks),
            "avg_chunk_size": avg_size,
            "output_path": output_path,
        }
