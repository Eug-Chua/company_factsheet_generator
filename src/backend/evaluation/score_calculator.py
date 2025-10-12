"""
Score Calculator
Computes individual, aggregate, and breakdown scores from RAGAS results
"""

from typing import List, Dict
import numpy as np
import pandas as pd
import json
from pathlib import Path


class ScoreCalculator:
    """Calculates evaluation scores"""

    def __init__(self, question_range_parser, config, logger):
        """Initialize score calculator"""
        self.question_range_parser = question_range_parser
        self.config = config
        self.logger = logger

    def _extract_metrics_from_row(self, ragas_scores, index: int):
        """Extract RAGAS metrics from score row"""
        return {
            'faithfulness': ragas_scores.iloc[index]['faithfulness'],
            'answer_relevancy': ragas_scores.iloc[index]['answer_relevancy'],
            'context_precision': ragas_scores.iloc[index]['context_precision'],
            'context_recall': ragas_scores.iloc[index]['context_recall']
        }

    def _convert_metric_value(self, value):
        """Convert metric value, handling NaN"""
        return None if pd.isna(value) else float(value)

    def _build_result_dict(self, qa: Dict, metrics: Dict):
        """Build result dictionary with QA and metrics"""
        return {
            'question_number': qa['number'], 'question': qa['question'], 'answer': qa['answer'],
            'answer_length': len(qa['answer'].split()),
            'faithfulness': self._convert_metric_value(metrics['faithfulness']),
            'answer_relevancy': self._convert_metric_value(metrics['answer_relevancy']),
            'context_precision': self._convert_metric_value(metrics['context_precision']),
            'context_recall': self._convert_metric_value(metrics['context_recall']),
            'retrieved_chunks': []
        }

    def _add_chunk_metadata(self, result: Dict, qa: Dict):
        """Add retrieved chunks metadata to result"""
        for chunk in qa.get('retrieved_chunks', [])[:5]:
            result['retrieved_chunks'].append({
                'chunk_id': chunk.get('chunk_id', None),
                'section_header': chunk.get('section_header', ''),
                'content': chunk.get('content', '')
            })

    def extract_individual_scores(self, qa_pairs: List[Dict], ragas_scores) -> List[Dict]:
        """Extract individual scores for each question"""
        evaluation_results = []
        for i, qa in enumerate(qa_pairs):
            metrics = self._extract_metrics_from_row(ragas_scores, i)
            result = self._build_result_dict(qa, metrics)
            self._add_chunk_metadata(result, qa)
            evaluation_results.append(result)
        return evaluation_results

    def compute_aggregate_scores(self, ragas_scores) -> Dict:
        """Compute aggregate scores"""
        return {
            'faithfulness': ragas_scores['faithfulness'].mean(),
            'answer_relevancy': ragas_scores['answer_relevancy'].mean(),
            'context_precision': ragas_scores['context_precision'].mean(),
            'context_recall': ragas_scores['context_recall'].mean()
        }

    def _filter_questions_by_range(self, evaluation_results: List[Dict], question_range: range):
        """Filter questions by range"""
        return [q for q in evaluation_results if q['question_number'] in question_range]

    def _get_metric_values(self, questions: List[Dict], metric: str):
        """Get non-None metric values from questions"""
        return [q[metric] for q in questions if q[metric] is not None]

    def _compute_metric_scores(self, questions: List[Dict]):
        """Compute metric scores for questions"""
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        scores = {}
        for metric in metrics:
            values = self._get_metric_values(questions, metric)
            scores[metric] = np.mean(values) if values else None
        return scores

    def _compute_overall_average(self, scores: Dict):
        """Compute overall average from metric scores"""
        all_values = [v for v in scores.values() if v is not None]
        return np.mean(all_values) if all_values else None

    def _compute_avg_scores(self, questions: List[Dict]):
        """Compute average scores for list of questions"""
        if not questions:
            return None
        scores = self._compute_metric_scores(questions)
        scores['average'] = self._compute_overall_average(scores)
        return scores

    def _build_breakdown_dict(self, qual_questions: List[Dict], quant_questions: List[Dict]):
        """Build breakdown dictionary"""
        qualitative_range = self.question_range_parser.get_qualitative_range()
        quantitative_range = self.question_range_parser.get_quantitative_range()
        return {
            'qualitative': {
                'question_range': f'{qualitative_range.start}-{qualitative_range.stop - 1}',
                'num_questions': len(qual_questions),
                'scores': self._compute_avg_scores(qual_questions)
            },
            'quantitative': {
                'question_range': f'{quantitative_range.start}-{quantitative_range.stop - 1}',
                'num_questions': len(quant_questions),
                'scores': self._compute_avg_scores(quant_questions)
            }
        }

    def compute_breakdown_scores(self, evaluation_results: List[Dict]) -> Dict:
        """Compute qualitative vs quantitative breakdown using dynamically loaded ranges"""
        qualitative_range = self.question_range_parser.get_qualitative_range()
        quantitative_range = self.question_range_parser.get_quantitative_range()
        qual_questions = self._filter_questions_by_range(evaluation_results, qualitative_range)
        quant_questions = self._filter_questions_by_range(evaluation_results, quantitative_range)
        return self._build_breakdown_dict(qual_questions, quant_questions)

    def build_results(self, factsheet_path: Path, qa_pairs: List[Dict], chunks: List[Dict],
                     aggregate_scores: Dict, overall_score: float, evaluation_results: List[Dict],
                     breakdown_scores: Dict) -> Dict:
        """Build results dictionary"""
        return {
            'company': self.config.company_name,
            'factsheet_path': str(factsheet_path or self.config.factsheet_path),
            'num_questions': len(qa_pairs),
            'num_chunks': len(chunks),
            'evaluation_method': 'RAGAS',
            'aggregate_scores': {k: (None if pd.isna(v) else float(v)) for k, v in aggregate_scores.items()},
            'overall_quality_score': None if pd.isna(overall_score) else float(overall_score),
            'breakdown_by_question_type': breakdown_scores,
            'individual_scores': evaluation_results
        }

    def save_results(self, results: Dict, output_path: Path) -> Path:
        """Save evaluation results"""
        output_path = output_path or self.config.evaluation_path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        return output_path
