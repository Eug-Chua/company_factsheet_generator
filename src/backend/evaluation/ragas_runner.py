"""
RAGAS Runner
Runs RAGAS evaluation with configured LLM and embeddings
"""

from typing import List, Dict
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)


class RAGASRunner:
    """Runs RAGAS evaluation"""

    def __init__(self, ragas_llm, ragas_embeddings, context_retriever, logger):
        """Initialize RAGAS runner"""
        self.ragas_llm = ragas_llm
        self.ragas_embeddings = ragas_embeddings
        self.context_retriever = context_retriever
        self.logger = logger

    def _prepare_ragas_data(self, qa_pairs: List[Dict]) -> Dict:
        """Prepare data for RAGAS evaluation using chunks from generation"""
        ragas_data = {'question': [], 'answer': [], 'contexts': [], 'ground_truth': []}
        for qa in qa_pairs:
            contexts = self.context_retriever.prepare_contexts_from_chunks(qa['retrieved_chunks'])
            ragas_data['question'].append(qa['question'])
            ragas_data['answer'].append(qa['answer'])
            ragas_data['contexts'].append(contexts)
            ragas_data['ground_truth'].append(qa['answer'])
        return ragas_data

    def run_ragas_evaluation(self, ragas_data: Dict):
        """Run RAGAS evaluation with configured LLM"""
        dataset = Dataset.from_dict(ragas_data)
        self.logger.info("Running RAGAS evaluation with parallel execution...")
        return evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=self.ragas_llm,
            embeddings=self.ragas_embeddings,
            run_config=RunConfig(max_workers=16)
        )
