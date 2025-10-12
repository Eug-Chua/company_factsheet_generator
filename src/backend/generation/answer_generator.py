"""
Answer Generator
Generates answers using LLM for single and batch questions
"""

from typing import List, Dict


class AnswerGenerator:
    """Generates answers using LLM"""

    def __init__(self, llm_client, prompt_builder, logger):
        """Initialize answer generator"""
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder
        self.logger = logger

    def _log_chunks_sent(self, num_chunks: int):
        """Log number of chunks being sent to LLM"""
        self.logger.info(f"Sending {num_chunks} retrieved chunks to the LLM")

    def _build_error_answers(self, questions: List[Dict], error_message: str):
        """Build error answers for all questions"""
        return {q['number']: f"Error: Could not generate answer - {error_message}"
                for q in questions}

    def generate_batch_answers(self, questions: List[Dict], relevant_chunks: List[Dict],
                               category: str) -> Dict[int, str]:
        """Generate answers for a batch of questions in the same category"""
        self._log_chunks_sent(len(relevant_chunks))
        prompt = self.prompt_builder.build_batch_prompt(category, questions, relevant_chunks)
        try:
            response_text = self.llm_client.call_llm(prompt, max_tokens=4000)
            return self.prompt_builder.parse_batch_response(response_text, questions)
        except Exception as e:
            self.logger.error(f"Error generating batch answers for {category}: {e}")
            return self._build_error_answers(questions, str(e))

    def _prepare_single_context(self, relevant_chunks: List[Dict]):
        """Prepare context from chunks for single question"""
        context_texts = []
        for i, chunk in enumerate(relevant_chunks[:11], 1):
            context_texts.append(f"[Context {i} - {chunk['section_header']}]\n{chunk['content']}\n")
        return "\n---\n".join(context_texts)

    def generate_answer(self, question: str, question_num: int,
                       relevant_chunks: List[Dict]) -> str:
        """Generate answer using LLM with retrieved chunks as context"""
        context = self._prepare_single_context(relevant_chunks)
        prompt = self.prompt_builder.build_single_answer_prompt(question, question_num, context)
        try:
            return self.llm_client.call_llm(prompt, max_tokens=1000)
        except Exception as e:
            self.logger.error(f"Error generating answer for Q{question_num}: {e}")
            return f"Error: Could not generate answer - {str(e)}"
