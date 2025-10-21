"""
Factsheet Generator
Main orchestrator for generating credit analysis factsheets
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from config_loader import load_config
from .llm_client import LLMClient
from .data_loader import DataLoader
from .terminology_mapper import TerminologyMapper
from .embedder import Embedder
from .section_booster import SectionBooster
from .bm25_retriever import BM25Retriever
from .prompt_builder import PromptBuilder
from .answer_generator import AnswerGenerator
from .category_parser import CategoryParser
from .factsheet_formatter import FactsheetFormatter
from .multi_hyde import MultiHyDE

load_dotenv()


class FactsheetGenerator:
    """Generates Q&A factsheets using adaptive retrieval strategies"""

    def __init__(self, config=None):
        """Initialize generator with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging for generation process"""
        self.logger = self.config.setup_logger("generation", __name__)

    def _init_core_components(self):
        """Initialize core components"""
        self.llm_client = LLMClient(self.config, self.logger)
        self.data_loader = DataLoader(self.config, self.logger)
        self.terminology_mapper = TerminologyMapper(self.config, self.logger)
        self.embedder = Embedder(self.config, self.logger)

    def _init_retrieval_components(self):
        """Initialize retrieval components"""
        self.section_booster = SectionBooster(self.logger)
        self.bm25_retriever = BM25Retriever(self.logger)
        self.multi_hyde = MultiHyDE(self.llm_client, self.embedder, self.logger, self.config)

    def _init_generation_components(self):
        """Initialize generation components"""
        self.prompt_builder = PromptBuilder(self.logger)
        self.answer_generator = AnswerGenerator(self.llm_client, self.prompt_builder, self.logger)
        self.category_parser = CategoryParser(self.config, self.logger)
        self.factsheet_formatter = FactsheetFormatter(self.logger)

    def _initialize_components(self):
        """Initialize all components"""
        self._init_core_components()
        self._init_retrieval_components()
        self._init_generation_components()

    def load_questions(self, question_path: Optional[Path] = None) -> List[Dict]:
        """Load questions from question_set.md"""
        return self.data_loader.load_questions(question_path)

    def load_chunks(self, chunks_path: Optional[Path] = None) -> List[Dict]:
        """Load chunks from JSON files (both text and table chunks)"""
        chunks = self.data_loader.load_chunks(chunks_path)
        self.terminology_mapper.detect_company_terminology(chunks)
        self.logger.info(f"✓ Auto-detected terminology for {self.config.company_name}")
        return chunks

    def _apply_section_boost(self, chunks: List[Dict], similarities, question: str):
        """Apply section-aware boost to similarities"""
        return self.section_booster.boost_by_section_relevance(chunks, similarities, question)

    def _apply_structure_boost(self, chunks: List[Dict], similarities):
        """Apply document structure boost to similarities"""
        return self.section_booster.apply_document_structure_boost(chunks, similarities)

    def _compute_similarities(self, question: str, chunks: List[Dict]):
        """Compute similarity scores between question and chunks"""
        chunk_texts = self.embedder._prepare_chunk_texts(chunks)
        question_emb, chunk_embs = self.embedder.encode_embeddings(question, chunk_texts)
        return self.embedder._calculate_similarities(question_emb, chunk_embs)

    def _apply_boosts(self, chunks: List[Dict], similarities, question: str,
                     apply_structure_boost: bool, section_aware: bool):
        """Apply section or structure boosts to similarities"""
        if section_aware:
            return self._apply_section_boost(chunks, similarities, question)
        elif apply_structure_boost:
            return self._apply_structure_boost(chunks, similarities)
        return similarities

    def retrieve_relevant_chunks(self, question: str, chunks: List[Dict], top_k: int = 10,
                                 apply_structure_boost: bool = False,
                                 section_aware: bool = False) -> List[Dict]:
        """Retrieve most relevant chunks for a question using embeddings"""
        similarities = self._compute_similarities(question, chunks)
        similarities = self._apply_boosts(chunks, similarities, question, apply_structure_boost, section_aware)
        return self.embedder.get_top_chunks(chunks, similarities, top_k)

    def retrieve_hybrid(self, question: str, chunks: List[Dict], top_k: int = 10,
                       semantic_top_k: int = 20, bm25_top_k: int = 20) -> List[Dict]:
        """Hybrid retrieval combining semantic search and BM25 keyword search using RRF"""
        self.logger.debug(f"Hybrid retrieval: semantic_top_k={semantic_top_k}, bm25_top_k={bm25_top_k}")
        semantic_results = self.retrieve_relevant_chunks(question, chunks, top_k=semantic_top_k)
        return self.bm25_retriever.retrieve_hybrid(semantic_results, chunks, question, top_k, bm25_top_k)

    def _log_category_processing(self, category_name: str, category_questions: List[Dict],
                                 q_range: range, keywords: str):
        """Log category processing info"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Processing Category: {category_name}")
        self.logger.info(f"Questions: {len(category_questions)} ({min(q_range)}-{max(q_range)})")
        self.logger.info(f"Target keywords: {keywords}")
        self.logger.info(f"{'='*60}")

    def _retrieve_semantic_only(self, question: str, chunks: List[Dict], top_k: int):
        """Retrieve using pure semantic search with section-aware boost"""
        # Check if Multi-HyDE is enabled in config
        use_multi_hyde = self.config.config.get('multi_hyde', {}).get('enabled', False)

        if use_multi_hyde:
            self.logger.info("Using Multi-HyDE retrieval...")
            relevant_chunks = self.multi_hyde.retrieve_with_multi_hyde(question, chunks, top_k=top_k)
            self.logger.info(f"Retrieved {len(relevant_chunks)} chunks (Multi-HyDE)")
        else:
            self.logger.info("Using SEMANTIC-ONLY retrieval with section-aware boost...")
            relevant_chunks = self.retrieve_relevant_chunks(question, chunks, top_k=top_k, section_aware=True)
            self.logger.info(f"Retrieved {len(relevant_chunks)} chunks (semantic + section-aware)")

        return relevant_chunks

    def _apply_terminology_substitution(self, keywords: str):
        """Apply company-specific terminology substitution"""
        substituted_keywords = self.terminology_mapper.substitute_terms(keywords)
        if substituted_keywords != keywords:
            self.logger.info(f"✓ Applied company-specific terminology")
        return substituted_keywords

    def _retrieve_hybrid(self, keywords: str, question: str, chunks: List[Dict],
                        top_k: int, semantic_top_k: int, bm25_top_k: int):
        """Retrieve using hybrid search with terminology substitution"""
        substituted_keywords = self._apply_terminology_substitution(keywords)
        targeted_query = f"{substituted_keywords} {question}"
        self.logger.info(f"Using HYBRID retrieval (semantic + BM25) for financial data...")
        relevant_chunks = self.retrieve_hybrid(targeted_query, chunks, top_k, semantic_top_k, bm25_top_k)
        self.logger.info(f"Retrieved {len(relevant_chunks)} chunks (RRF merged)")
        return relevant_chunks

    def _build_qa_pair(self, q_dict: Dict, answer: str, category_name: str,
                      relevant_chunks: List[Dict]):
        """Build a single Q&A pair dictionary"""
        return {'number': q_dict['number'], 'question': q_dict['text'], 'answer': answer,
                'category': category_name, 'retrieved_chunks': relevant_chunks}

    def _get_category_questions(self, questions: List[Dict], q_range: range):
        """Get questions for a specific category"""
        return [q for q in questions if q['number'] in q_range]

    def _rerank_chunks_for_precision(self, retrieved_chunks: List[Dict],
                                     category_questions: List[Dict], final_k: int = 30) -> List[Dict]:
        """Stage 2: Re-rank retrieved chunks using all category questions for better precision"""
        if len(retrieved_chunks) <= final_k:
            return retrieved_chunks

        self.logger.info(f"Re-ranking {len(retrieved_chunks)} chunks to top {final_k} for better precision...")

        # Combine all questions in category for better relevance scoring
        combined_query = " ".join([q['text'] for q in category_questions])

        # Re-score chunks against the combined question set
        similarities = self._compute_similarities(combined_query, retrieved_chunks)

        # Convert to numpy array if it's a tensor (handles MPS/CUDA devices)
        if hasattr(similarities, 'cpu'):
            similarities = similarities.cpu().numpy()
        elif not isinstance(similarities, np.ndarray):
            similarities = np.array(similarities)

        # Get top-k based on new scores
        top_indices = np.argsort(similarities)[-final_k:][::-1]
        reranked_chunks = [retrieved_chunks[i] for i in top_indices]

        self.logger.info(f"✓ Re-ranked to {len(reranked_chunks)} most relevant chunks")
        return reranked_chunks

    def _retrieve_for_category(self, category_name: str, first_question: str,
                               keywords: str, chunks: List[Dict]):
        """Retrieve chunks based on category type"""
        if category_name == "Business Fundamentals":
            return self._retrieve_semantic_only(first_question, chunks, top_k=50)
        return self._retrieve_hybrid(keywords, first_question, chunks, top_k=50, semantic_top_k=60, bm25_top_k=60)

    def _build_qa_pairs_from_answers(self, category_questions: List[Dict], batch_answers: Dict,
                                     category_name: str, relevant_chunks: List[Dict]):
        """Build Q&A pairs from batch answers"""
        qa_pairs = []
        for q_dict in category_questions:
            q_num = q_dict['number']
            answer = batch_answers.get(q_num, "Error: Answer not found in batch response")
            qa_pairs.append(self._build_qa_pair(q_dict, answer, category_name, relevant_chunks))
            self.logger.info(f"  ✓ Q{q_num}: {q_dict['text'][:60]}...")
        return qa_pairs

    def _process_category(self, category_name: str, category_info: Dict,
                         questions: List[Dict], chunks: List[Dict]) -> List[Dict]:
        """Process a single category with adaptive retrieval strategy"""
        q_range, keywords = category_info["range"], category_info["keywords"]
        category_questions = self._get_category_questions(questions, q_range)
        if not category_questions:
            return []
        self._log_category_processing(category_name, category_questions, q_range, keywords)

        # Stage 1: Broad retrieval (50-60 chunks)
        retrieved_chunks = self._retrieve_for_category(category_name, category_questions[0]['text'], keywords, chunks)

        # Stage 2: Re-rank for precision (reduce to 30 most relevant)
        relevant_chunks = self._rerank_chunks_for_precision(retrieved_chunks, category_questions, final_k=30)

        self.logger.info(f"Calling API for batch of {len(category_questions)} questions...")
        batch_answers = self.answer_generator.generate_batch_answers(category_questions, relevant_chunks, category_name)
        return self._build_qa_pairs_from_answers(category_questions, batch_answers, category_name, relevant_chunks)

    def _save_factsheet(self, factsheet_content: str, output_path: Path):
        """Save factsheet to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(factsheet_content)

    def _save_qa_json(self, qa_pairs: List[Dict], output_path: Path):
        """Save Q&A pairs to JSON"""
        qa_json_path = output_path.parent / f"{self.config.company_name}_qa_pairs.json"
        with open(qa_json_path, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, indent=2)

    def _save_outputs(self, factsheet_content: str, qa_pairs: List[Dict],
                     output_path: Path) -> Path:
        """Save factsheet and QA pairs"""
        output_path = output_path or self.config.factsheet_path
        output_path = Path(output_path)
        self._save_factsheet(factsheet_content, output_path)
        self._save_qa_json(qa_pairs, output_path)
        return output_path

    def _build_completion_message(self, output_path: Path, qa_pairs: List[Dict], num_categories: int):
        """Build completion message lines"""
        qa_json_path = output_path.parent / f"{self.config.company_name}_qa_pairs.json"
        return [f"\n{'=' * 60}", "Factsheet Generation Complete (BATCH MODE)", f"{'=' * 60}",
                f"  Company: {self.config.company_name}", f"  Questions answered: {len(qa_pairs)}",
                f"  Categories processed: {num_categories}", f"  Factsheet: {output_path}",
                f"  Q&A JSON: {qa_json_path}", f"{'=' * 60}\n"]

    def _log_completion(self, output_path: Path, qa_pairs: List[Dict], num_categories: int):
        """Log completion summary"""
        for line in self._build_completion_message(output_path, qa_pairs, num_categories):
            self.logger.info(line)

    def _sort_categories_by_question_order(self, categories: Dict):
        """Sort categories by their minimum question number"""
        return dict(sorted(categories.items(), key=lambda x: min(x[1]['range'])))

    def _process_all_categories(self, categories: Dict, questions: List[Dict], chunks: List[Dict]):
        """Process all categories and return Q&A pairs"""
        qa_pairs = []
        sorted_categories = self._sort_categories_by_question_order(categories)
        for category_name, category_info in sorted_categories.items():
            category_qa = self._process_category(category_name, category_info, questions, chunks)
            qa_pairs.extend(category_qa)
        return qa_pairs

    def _generate_and_save_factsheet(self, qa_pairs: List[Dict], output_path: Optional[Path]):
        """Generate factsheet markdown and save outputs"""
        category_ranges = self.category_parser.get_category_ranges()
        factsheet_content = self.factsheet_formatter.format_factsheet(qa_pairs, self.config.company_name, category_ranges)
        return self._save_outputs(factsheet_content, qa_pairs, output_path)

    def generate_factsheet_batch(self, chunks_path: Optional[Path] = None,
                                 questions_path: Optional[Path] = None,
                                 output_path: Optional[Path] = None) -> Path:
        """Generate factsheet using batch processing by category"""
        chunks = self.load_chunks(chunks_path)
        questions = self.load_questions(questions_path)
        categories = self.category_parser.get_categories_config(questions)
        self.logger.info(f"\nGenerating answers for {len(questions)} questions using BATCH processing...")
        qa_pairs = self._process_all_categories(categories, questions, chunks)
        output_path = self._generate_and_save_factsheet(qa_pairs, output_path)
        self._log_completion(output_path, qa_pairs, len(categories))
        return output_path

    def generate_factsheet(self, chunks_path: Optional[Path] = None,
                          questions_path: Optional[Path] = None,
                          output_path: Optional[Path] = None) -> Path:
        """Complete pipeline to generate factsheet from chunks using BATCH processing"""
        return self.generate_factsheet_batch(chunks_path, questions_path, output_path)


def main():
    """CLI entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Generate credit analysis factsheet from chunks")
    parser.add_argument('--company', type=str, help='Company to process')
    parser.add_argument('--chunks', type=str, help='Path to chunks JSON file')
    parser.add_argument('--questions', type=str, help='Path to questions file')
    parser.add_argument('--output', type=str, help='Path for output factsheet')
    parser.add_argument('--config', type=str, help='Path to config.yaml file')
    args = parser.parse_args()
    config = load_config(args.config) if args.config else load_config()
    if args.company:
        config.set_company(args.company)
    generator = FactsheetGenerator(config)
    chunks_path = Path(args.chunks) if args.chunks else None
    questions_path = Path(args.questions) if args.questions else None
    output_path = Path(args.output) if args.output else None
    generator.logger.info("Using BATCH processing mode (default)")
    result = generator.generate_factsheet(chunks_path, questions_path, output_path)
    generator.logger.info(f"✓ Factsheet generation complete for {config.company_name}")


if __name__ == "__main__":
    main()
