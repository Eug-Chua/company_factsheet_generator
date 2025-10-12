"""
RAGAS Evaluator
Main orchestrator for evaluating factsheet quality using RAGAS framework
"""

from pathlib import Path
from typing import Optional
import numpy as np
from dotenv import load_dotenv
from config_loader import load_config
from .question_range_parser import QuestionRangeParser
from .model_initializer import ModelInitializer
from .data_loader import DataLoader
from .qa_extractor import QAExtractor
from .context_retriever import ContextRetriever
from .ragas_runner import RAGASRunner
from .score_calculator import ScoreCalculator
from .evaluation_logger import EvaluationLogger

load_dotenv()


class FactsheetEvaluator:
    """Evaluates factsheet quality using RAGAS framework"""

    def __init__(self, config=None):
        """Initialize evaluator with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging for evaluation process"""
        self.logger = self.config.setup_logger("evaluation", __name__)

    def _init_question_range_parser(self):
        """Initialize question range parser"""
        self.question_range_parser = QuestionRangeParser(self.config, self.logger)
        self.question_range_parser.load_question_ranges()

    def _init_models(self):
        """Initialize models"""
        self.model_initializer = ModelInitializer(self.config, self.logger)
        self.model_initializer.initialize_models()

    def _init_data_components(self):
        """Initialize data components"""
        self.data_loader = DataLoader(self.config, self.logger)
        self.qa_extractor = QAExtractor(self.logger)

    def _init_evaluation_components(self):
        """Initialize evaluation components"""
        embedder = self.model_initializer.get_embedder()
        self.context_retriever = ContextRetriever(embedder)
        ragas_llm = self.model_initializer.get_ragas_llm()
        ragas_embeddings = self.model_initializer.get_ragas_embeddings()
        self.ragas_runner = RAGASRunner(ragas_llm, ragas_embeddings, self.context_retriever, self.logger)

    def _init_score_and_logging_components(self):
        """Initialize score and logging components"""
        self.score_calculator = ScoreCalculator(self.question_range_parser, self.config, self.logger)
        self.evaluation_logger = EvaluationLogger(self.config, self.logger)

    def _initialize_components(self):
        """Initialize all components"""
        self._init_question_range_parser()
        self._init_models()
        self._init_data_components()
        self._init_evaluation_components()
        self._init_score_and_logging_components()

    def _load_and_log_qa_pairs(self):
        """Load QA pairs and log evaluation start"""
        qa_pairs = self.data_loader.load_qa_pairs_with_chunks()
        self.logger.info(f"\nEvaluating {len(qa_pairs)} Q&A pairs with RAGAS...")
        self.logger.info("Using the SAME chunks that generated each answer for faithful evaluation")
        return qa_pairs

    def _run_evaluation_and_get_scores(self, qa_pairs):
        """Run RAGAS evaluation and get scores dataframe"""
        ragas_data = self.ragas_runner._prepare_ragas_data(qa_pairs)
        ragas_result = self.ragas_runner.run_ragas_evaluation(ragas_data)
        return ragas_result.to_pandas()

    def _compute_all_scores(self, qa_pairs, ragas_scores):
        """Compute all evaluation scores"""
        evaluation_results = self.score_calculator.extract_individual_scores(qa_pairs, ragas_scores)
        aggregate_scores = self.score_calculator.compute_aggregate_scores(ragas_scores)
        breakdown_scores = self.score_calculator.compute_breakdown_scores(evaluation_results)
        overall_score = np.mean(list(aggregate_scores.values()))
        return evaluation_results, aggregate_scores, breakdown_scores, overall_score

    def _build_and_save_results(self, factsheet_path, qa_pairs, chunks_path, aggregate_scores,
                                overall_score, evaluation_results, breakdown_scores, output_path):
        """Build results dict, save to file, and log summary"""
        chunks = self.data_loader.load_chunks(chunks_path)
        results = self.score_calculator.build_results(factsheet_path, qa_pairs, chunks, aggregate_scores,
                                                      overall_score, evaluation_results, breakdown_scores)
        output_path = self.score_calculator.save_results(results, output_path)
        self.evaluation_logger.log_evaluation_summary(aggregate_scores, overall_score, breakdown_scores, output_path)
        return output_path

    def evaluate_factsheet(self, factsheet_path: Optional[Path] = None,
                          chunks_path: Optional[Path] = None,
                          output_path: Optional[Path] = None) -> Path:
        """Complete evaluation pipeline using RAGAS with generation chunks"""
        qa_pairs = self._load_and_log_qa_pairs()
        ragas_scores = self._run_evaluation_and_get_scores(qa_pairs)
        evaluation_results, aggregate_scores, breakdown_scores, overall_score = self._compute_all_scores(qa_pairs, ragas_scores)
        return self._build_and_save_results(factsheet_path, qa_pairs, chunks_path, aggregate_scores,
                                           overall_score, evaluation_results, breakdown_scores, output_path)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate factsheet quality with LLM")
    parser.add_argument('--company', type=str, help='Company to evaluate. If not specified, uses config default.')
    parser.add_argument('--factsheet', type=str, help='Path to factsheet markdown file (optional)')
    parser.add_argument('--chunks', type=str, help='Path to chunks JSON file (optional)')
    parser.add_argument('--output', type=str, help='Path for output evaluation (optional)')
    parser.add_argument('--config', type=str, help='Path to config.yaml file (optional)')

    args = parser.parse_args()

    config = load_config(args.config) if args.config else load_config()

    if args.company:
        config.set_company(args.company)

    evaluator = FactsheetEvaluator(config)

    factsheet_path = Path(args.factsheet) if args.factsheet else None
    chunks_path = Path(args.chunks) if args.chunks else None
    output_path = Path(args.output) if args.output else None

    evaluator.evaluate_factsheet(factsheet_path, chunks_path, output_path)

    evaluator.logger.info(f"✓ Evaluation complete for {config.company_name}")


if __name__ == "__main__":
    main()
