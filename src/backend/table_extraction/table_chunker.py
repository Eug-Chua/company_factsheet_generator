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

    def _create_table_chunk_dict(self, chunk_id: int, section_header: str, content: str,
                                 table_id: str, page, shape: Dict) -> Dict:
        """Create chunk dictionary for a table"""
        return {'chunk_id': chunk_id, 'section_header': section_header, 'header_level': 0,
                'content': content, 'content_type': 'table', 'table_id': table_id,
                'table_page': page, 'table_shape': shape}

    def _is_header_line(self, line: str, index: int) -> bool:
        """Check if line is part of table header"""
        return index < 2 or line.startswith('|---')

    def _separate_table_header_and_data(self, lines: List[str]) -> tuple[str, List[str]]:
        """Separate table header from data lines"""
        header_lines = [line for i, line in enumerate(lines) if self._is_header_line(line, i)]
        data_lines = [line for i, line in enumerate(lines) if not self._is_header_line(line, i)]
        return '\n'.join(header_lines), data_lines

    def _can_fit_in_chunk(self, current_chunk: str, line: str, max_chunk_size: int) -> bool:
        """Check if line can fit in current chunk"""
        return len(current_chunk) + len(line) + 1 <= max_chunk_size

    def _append_chunk_to_list(self, chunks: List[Dict], chunk_id_offset: int,
                              section_header: str, chunk_num: int, current_chunk: str,
                              table_id: str, page, shape: Dict):
        """Append a chunk to the chunks list"""
        chunks.append(self._create_table_chunk_dict(chunk_id_offset + len(chunks),
                     f"{section_header} (Part {chunk_num})", current_chunk, table_id, page, shape))

    def _create_multi_part_chunks(self, header_text: str, data_lines: List[str],
                                  section_header: str, table_id: str, page, shape: Dict,
                                  chunk_id_offset: int, chunks: List[Dict], max_chunk_size: int):
        """Create multiple chunks from large table"""
        current_chunk, chunk_num = header_text, 1
        for line in data_lines:
            if self._can_fit_in_chunk(current_chunk, line, max_chunk_size):
                current_chunk += '\n' + line
            else:
                self._append_chunk_to_list(chunks, chunk_id_offset, section_header, chunk_num,
                                          current_chunk, table_id, page, shape)
                current_chunk, chunk_num = header_text + '\n' + line, chunk_num + 1
        if current_chunk.strip():
            self._append_chunk_to_list(chunks, chunk_id_offset, section_header, chunk_num,
                                      current_chunk, table_id, page, shape)

    def _create_section_header(self, table_idx: int, page, shape: Dict) -> str:
        """Create section header for table"""
        return f"Table {table_idx + 1} (Page {page}): {shape['rows']}×{shape['columns']}"

    def _add_single_chunk(self, chunks: List[Dict], chunk_id_offset: int,
                         section_header: str, markdown_content: str,
                         table_id: str, page, shape: Dict):
        """Add a single chunk for small table"""
        chunks.append(self._create_table_chunk_dict(chunk_id_offset + len(chunks),
                     section_header, markdown_content, table_id, page, shape))

    def _process_large_table(self, markdown_content: str, section_header: str,
                            table_id: str, page, shape: Dict,
                            chunk_id_offset: int, chunks: List[Dict], max_chunk_size: int):
        """Process a large table into multiple chunks"""
        header_text, data_lines = self._separate_table_header_and_data(markdown_content.split('\n'))
        self._create_multi_part_chunks(header_text, data_lines, section_header,
                                      table_id, page, shape, chunk_id_offset, chunks, max_chunk_size)

    def _process_single_table_to_chunks(self, table_idx: int, table_id: str, table_info: Dict,
                                       chunk_id_offset: int, chunks: List[Dict], max_chunk_size: int):
        """Process a single table and add its chunks"""
        shape, page = table_info['shape'], table_info['location'].get('page', 'unknown')
        markdown_content = table_info['markdown']
        section_header = self._create_section_header(table_idx, page, shape)
        if len(markdown_content) <= max_chunk_size:
            self._add_single_chunk(chunks, chunk_id_offset, section_header, markdown_content, table_id, page, shape)
        else:
            self._process_large_table(markdown_content, section_header, table_id, page, shape,
                                     chunk_id_offset, chunks, max_chunk_size)

    def _validate_tables_data_loaded(self):
        """Validate that tables data is loaded"""
        if not self.table_loader.tables_data:
            raise ValueError("No tables loaded. Call load_tables() first.")

    def _process_all_tables_to_chunks(self, chunk_id_offset: int, chunks: List[Dict], max_chunk_size: int):
        """Process all tables and convert to chunks"""
        for table_idx, (table_id, table_info) in enumerate(self.table_loader.tables_data.items()):
            self._process_single_table_to_chunks(table_idx, table_id, table_info, chunk_id_offset, chunks, max_chunk_size)

    def create_table_chunks(self, max_chunk_size: int = 2000) -> List[Dict]:
        """Convert tables to chunks for RAG retrieval"""
        self._validate_tables_data_loaded()
        chunks, chunk_id_offset = [], 10000
        self.logger.info(f"Creating chunks from {len(self.table_loader.tables_data)} tables...")
        self._process_all_tables_to_chunks(chunk_id_offset, chunks, max_chunk_size)
        self.logger.info(f"✓ Created {len(chunks)} table chunks from {len(self.table_loader.tables_data)} tables")
        return chunks

    def _get_default_output_path(self) -> Path:
        """Get default output path for table chunks"""
        return self.config.output_dir / f"{self.config.company_name}_table_chunks.json"

    def _prepare_output_path(self, output_path: Optional[Path]) -> Path:
        """Prepare output path and create parent directories"""
        output_path = Path(output_path or self._get_default_output_path())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def _write_chunks_to_file(self, chunks: List[Dict], output_path: Path):
        """Write chunks to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

    def save_table_chunks(self, chunks: List[Dict], output_path: Optional[Path] = None) -> Path:
        """Save table chunks to JSON file"""
        output_path = self._prepare_output_path(output_path)
        self._write_chunks_to_file(chunks, output_path)
        self.logger.info(f"✓ Saved {len(chunks)} table chunks to: {output_path}")
        return output_path

    def _calculate_avg_chunk_size(self, chunks: List[Dict]) -> float:
        """Calculate average chunk size"""
        return sum(len(c['content']) for c in chunks) / len(chunks) if chunks else 0

    def _build_processing_result(self, chunks: List[Dict], output_path: Path) -> Dict:
        """Build processing result dictionary"""
        return {'num_tables': len(self.table_loader.tables_data), 'num_chunks': len(chunks),
                'avg_chunk_size': self._calculate_avg_chunk_size(chunks), 'output_path': output_path}

    def process_tables_to_chunks(self, tables_path: Optional[Path] = None,
                                 max_chunk_size: int = 2000) -> Dict:
        """Complete pipeline: load tables → create chunks → save"""
        self.table_loader.load_tables(tables_path)
        chunks = self.create_table_chunks(max_chunk_size)
        output_path = self.save_table_chunks(chunks)
        return self._build_processing_result(chunks, output_path)
