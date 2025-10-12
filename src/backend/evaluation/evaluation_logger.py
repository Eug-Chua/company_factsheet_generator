"""
Evaluation Logger
Logs evaluation summaries and results
"""

from pathlib import Path
from typing import Dict


class EvaluationLogger:
    """Logs evaluation summaries"""

    def __init__(self, config, logger):
        """Initialize evaluation logger"""
        self.config = config
        self.logger = logger

    def _log_summary_header(self):
        """Log evaluation summary header"""
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"RAGAS Evaluation Summary for {self.config.company_name}")
        self.logger.info(f"{'=' * 60}")

    def _log_aggregate_metrics(self, aggregate_scores: Dict, overall_score: float):
        """Log aggregate metrics"""
        self.logger.info(f"  Overall Quality Score: {overall_score:.3f}")
        self.logger.info(f"  Faithfulness: {aggregate_scores['faithfulness']:.3f}")
        self.logger.info(f"  Answer Relevancy: {aggregate_scores['answer_relevancy']:.3f}")
        self.logger.info(f"  Context Precision: {aggregate_scores['context_precision']:.3f}")
        self.logger.info(f"  Context Recall: {aggregate_scores['context_recall']:.3f}")

    def _log_question_type_scores(self, type_name: str, type_data: Dict):
        """Log scores for a question type"""
        scores = type_data['scores']
        if scores:
            self.logger.info(f"    {type_name} (Q{type_data['question_range']}): {scores['average']:.3f}")
            self.logger.info(f"      Faithfulness: {scores['faithfulness']:.3f}")
            self.logger.info(f"      Answer Relevancy: {scores['answer_relevancy']:.3f}")
            self.logger.info(f"      Context Precision: {scores['context_precision']:.3f}")
            self.logger.info(f"      Context Recall: {scores['context_recall']:.3f}")

    def _log_breakdown_scores(self, breakdown_scores: Dict):
        """Log breakdown scores by question type"""
        self.logger.info("")
        self.logger.info("  Breakdown by Question Type:")
        self._log_question_type_scores("Qualitative", breakdown_scores['qualitative'])
        self._log_question_type_scores("Quantitative", breakdown_scores['quantitative'])

    def _log_summary_footer(self, output_path: Path):
        """Log summary footer"""
        self.logger.info("")
        self.logger.info(f"  Results saved to: {output_path}")
        self.logger.info(f"{'=' * 60}\n")

    def log_evaluation_summary(self, aggregate_scores: Dict, overall_score: float,
                               breakdown_scores: Dict, output_path: Path):
        """Log evaluation summary"""
        self._log_summary_header()
        self._log_aggregate_metrics(aggregate_scores, overall_score)
        self._log_breakdown_scores(breakdown_scores)
        self._log_summary_footer(output_path)
