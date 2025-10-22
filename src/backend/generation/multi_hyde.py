"""
Multi-HyDE (Multiple Hypothetical Document Embeddings)
Implements multi-query expansion and hypothetical document generation for improved retrieval
"""

from typing import List, Dict
import numpy as np
from sentence_transformers import CrossEncoder


class MultiHyDE:
    """
    Multi-HyDE retrieval enhancement for financial RAG systems

    Process:
    1. Generate N diverse query variants from original question
    2. Generate hypothetical document for each variant
    3. Embed hypothetical documents (answers, not questions)
    4. Retrieve top-k chunks per hypothetical document
    5. Aggregate and deduplicate results
    6. Rerank using original question
    """

    def __init__(self, llm_client, embedder, logger, config, section_booster):
        """
        Initialize Multi-HyDE module

        Args:
            llm_client: LLM client for generating variants and hypothetical docs
            embedder: Embedder for encoding hypothetical documents
            logger: Logger instance
            config: Configuration object
            section_booster: SectionBooster for section-aware boosting
        """
        self.llm_client = llm_client
        self.embedder = embedder
        self.logger = logger
        self.config = config
        self.section_booster = section_booster
        self.use_cross_encoder = True

        # Multi-HyDE parameters
        self.num_variants = self.config.config.get('multi_hyde', {}).get('num_variants', 5)
        self.k_per_hypothetical = self.config.config.get('multi_hyde', {}).get('k_per_hypothetical', 10)

        try:
            cross_encoder_model = self.config.config.get('multi_hyde', {}).get(
                'cross_encoder_model', 'cross-encoder/ms-marco-MiniLM-L-6-v2'
            )
            self.logger.info(f"Loading cross-encoder model: {cross_encoder_model}")
            self.cross_encoder = CrossEncoder(cross_encoder_model)
            self.logger.info("✓ Cross-encoder loaded")
        except ImportError:
            self.logger.error("sentence-transformers not installed - Multi-HyDE requires cross-encoder!")
            raise RuntimeError("Multi-HyDE requires sentence-transformers. Install with: pip install sentence-transformers")

    def _generate_query_variants_prompt(self, question: str) -> str:
        """
        Build prompt for generating diverse query variants

        Strategy: Ask LLM to create non-equivalent queries that approach
        the question from different semantic angles
        """
        prompt = f"""You are a financial analyst helping to improve information retrieval from annual reports.

Given the following question about a company's annual report, generate {self.num_variants} diverse, non-equivalent query variants that approach the same question from different angles.

Each variant should:
- Ask the same fundamental question but with different wording
- Use different financial terminology or perspectives
- Focus on different aspects (e.g., one on numbers, one on qualitative, one on specific sections)
- Be distinct enough to retrieve different but relevant chunks

Original question: {question}

Generate {self.num_variants} query variants. Return ONLY the variants, one per line, numbered 1-{self.num_variants}.

Example format:
1. [First variant]
2. [Second variant]
3. [Third variant]
"""
        return prompt

    def _parse_query_variants(self, llm_response: str, question: str) -> List[str]:
        """
        Parse LLM response to extract query variants

        Args:
            llm_response: Raw LLM output with numbered variants

        Returns:
            List of query variant strings
        """
        variants = []
        lines = llm_response.strip().split('\n')

        for line in lines:
            line = line.strip()
            # Match patterns like "1.", "1)", "1:", or just numbered lines
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering prefix (e.g., "1. ", "1) ", "1: ", "- ")
                variant = line.split('.', 1)[-1].split(')', 1)[-1].split(':', 1)[-1].strip()
                if variant and variant.startswith('-'):
                    variant = variant[1:].strip()
                if variant:
                    variants.append(variant)

        # Fallback: if parsing failed, return original question duplicated
        if not variants:
            self.logger.warning("Failed to parse query variants, using original question")
            return [question] * self.num_variants

        return variants[:self.num_variants]  # Ensure we get exactly num_variants

    def generate_query_variants(self, question: str) -> List[str]:
        """
        Generate diverse query variants from original question

        Args:
            question: Original user question

        Returns:
            List of query variants
        """
        self.logger.debug(f"Generating {self.num_variants} query variants for: {question[:60]}...")

        prompt = self._generate_query_variants_prompt(question)
        llm_response = self.llm_client.call_llm(prompt, max_tokens=500)

        variants = self._parse_query_variants(llm_response, question)

        self.logger.debug("Generated variants:")
        for i, variant in enumerate(variants, 1):
            self.logger.debug(f"  {i}. {variant[:80]}...")

        return variants

    def _generate_hypothetical_document_prompt(self, query_variant: str) -> str:
        """
        Build prompt for generating hypothetical document snippet

        Strategy: Generate a passage that would likely answer the query,
        mimicking the style and content of annual report text
        """
        prompt = f"""You are a financial analyst writing content for an annual report.

Write a brief, realistic passage (2-3 sentences) that would directly answer this question:

Question: {query_variant}

Your passage should:
- Be written in the style of an annual report (formal, data-focused)
- Include specific financial terminology and metrics
- Sound like it came from a real company's financial disclosure
- Be detailed enough to be semantically rich for embedding

Write ONLY the passage, no preamble or explanation.
"""
        return prompt

    def generate_hypothetical_document(self, query_variant: str) -> str:
        """
        Generate hypothetical document for a single query variant

        Args:
            query_variant: A single query variant

        Returns:
            Hypothetical document text
        """
        prompt = self._generate_hypothetical_document_prompt(query_variant)
        hypothetical_doc = self.llm_client.call_llm(prompt, max_tokens=300)
        return hypothetical_doc.strip()

    def generate_all_hypothetical_documents(self, query_variants: List[str]) -> List[str]:
        """
        Generate hypothetical documents for all query variants

        Args:
            query_variants: List of query variants

        Returns:
            List of hypothetical documents
        """
        self.logger.debug(f"Generating hypothetical documents for {len(query_variants)} variants...")

        hypothetical_docs = []
        for i, variant in enumerate(query_variants, 1):
            hyp_doc = self.generate_hypothetical_document(variant)
            hypothetical_docs.append(hyp_doc)
            self.logger.debug(f"  HypDoc {i}: {hyp_doc[:60]}...")

        return hypothetical_docs

    def _retrieve_for_single_hypothetical(self, hypothetical_doc: str,
                                          chunks: List[Dict]) -> List[Dict]:
        """
        Retrieve top-k chunks for a single hypothetical document

        Args:
            hypothetical_doc: Hypothetical document text
            chunks: All available chunks

        Returns:
            Top-k relevant chunks
        """
        # Prepare chunk texts
        chunk_texts = self.embedder._prepare_chunk_texts(chunks)

        # Encode hypothetical document and chunks
        hyp_doc_emb, chunk_embs = self.embedder.encode_embeddings(hypothetical_doc, chunk_texts)

        # Calculate similarities
        similarities = self.embedder._calculate_similarities(hyp_doc_emb, chunk_embs)

        # Get top-k chunks
        return self.embedder.get_top_chunks(chunks, similarities, self.k_per_hypothetical)

    def retrieve_with_hypothetical_documents(self, hypothetical_docs: List[str],
                                            chunks: List[Dict]) -> List[Dict]:
        """
        Retrieve chunks using multiple hypothetical documents

        Args:
            hypothetical_docs: List of hypothetical documents
            chunks: All available chunks

        Returns:
            Aggregated list of chunks (with duplicates)
        """
        self.logger.debug(f"Retrieving top-{self.k_per_hypothetical} chunks per hypothetical document...")

        all_retrieved_chunks = []

        for i, hyp_doc in enumerate(hypothetical_docs, 1):
            chunks_i = self._retrieve_for_single_hypothetical(hyp_doc, chunks)
            all_retrieved_chunks.extend(chunks_i)
            self.logger.debug(f"  HypDoc {i}: Retrieved {len(chunks_i)} chunks")

        return all_retrieved_chunks

    def _deduplicate_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Deduplicate chunks by chunk ID, keeping highest similarity score

        Args:
            chunks: List of chunks (may contain duplicates)

        Returns:
            Deduplicated list of chunks
        """
        chunk_map = {}

        for chunk in chunks:
            chunk_id = chunk.get('chunk_id') or chunk.get('content')[:100]

            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = chunk
            else:
                # Keep chunk with higher similarity score
                existing_score = chunk_map[chunk_id].get('similarity_score', 0)
                new_score = chunk.get('similarity_score', 0)

                if new_score > existing_score:
                    chunk_map[chunk_id] = chunk

        return list(chunk_map.values())


    def _rerank_with_crossencoder(self, question: str, chunks: List[Dict],
                                  top_k: int) -> List[Dict]:
        """
        Rerank chunks using cross-encoder with section-aware boosting

        Args:
            question: Original user question
            chunks: Chunks to rerank
            top_k: Number of chunks to return

        Returns:
            Top-k reranked chunks
        """
        if not self.cross_encoder:
            self.logger.warning("Cross-encoder not initialized, cannot rerank")
            return chunks[:top_k]

        # Create question-chunk pairs
        pairs = [(question, chunk['content']) for chunk in chunks]

        # Score all pairs with cross-encoder
        scores = self.cross_encoder.predict(pairs)

        # Apply section-aware boost to cross-encoder scores
        self.logger.debug("Applying section-aware boost to cross-encoder scores...")
        patterns = self.section_booster.get_section_patterns_for_question(question)
        relevant_indices = self.section_booster.detect_relevant_sections(chunks, patterns)

        if relevant_indices:
            self.logger.debug(f"  Boosting {len(relevant_indices)} chunks from relevant sections")

        # Apply boost factor (same as baseline: 0.8 → 1.8× multiplier)
        boost_factor = 0.8
        for idx in relevant_indices:
            scores[idx] = scores[idx] * (1 + boost_factor)

        # Rank by boosted scores (descending)
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        # Build reranked chunks with final scores
        reranked_chunks = []
        for idx in ranked_indices:
            chunk = chunks[idx].copy()
            chunk['cross_encoder_score'] = float(scores[idx])
            reranked_chunks.append(chunk)

        return reranked_chunks

    def _rerank_with_original_question(self, question: str, chunks: List[Dict],
                                       top_k: int) -> List[Dict]:
        """
        Rerank deduplicated chunks using cross-encoder with section-aware boost

        Args:
            question: Original user question
            chunks: Deduplicated chunks from multi-retrieval
            top_k: Number of chunks to return

        Returns:
            Top-k reranked chunks
        """
        self.logger.debug(f"Reranking {len(chunks)} chunks with cross-encoder + section boost...")

        if not self.cross_encoder:
            self.logger.warning("Cross-encoder not initialized, returning chunks by original score")
            return sorted(chunks, key=lambda x: x.get('similarity_score', 0), reverse=True)[:top_k]

        # Cross-encoder reranking with section-aware boost
        final_chunks = self._rerank_with_crossencoder(question, chunks, top_k)
        self.logger.debug(f"✓ Reranking complete: {len(final_chunks)} final chunks")
        return final_chunks

    def retrieve_with_multi_hyde(self, question: str, chunks: List[Dict],
                                 top_k: int = 30) -> List[Dict]:
        """
        Complete Multi-HyDE retrieval pipeline

        Args:
            question: Original user question
            chunks: All available chunks
            top_k: Final number of chunks to return

        Returns:
            Top-k most relevant chunks using Multi-HyDE
        """
        self.logger.info(f"Multi-HyDE retrieval (variants={self.num_variants}, k_per_hyp={self.k_per_hypothetical})")

        # Step 1: Generate query variants
        query_variants = self.generate_query_variants(question)

        # Step 2: Generate hypothetical documents
        hypothetical_docs = self.generate_all_hypothetical_documents(query_variants)

        # Step 3: Retrieve with each hypothetical document
        all_chunks = self.retrieve_with_hypothetical_documents(hypothetical_docs, chunks)
        self.logger.info(f"  Retrieved {len(all_chunks)} chunks (across {len(hypothetical_docs)} hypotheticals)")

        # Step 4: Deduplicate
        unique_chunks = self._deduplicate_chunks(all_chunks)
        self.logger.info(f"  Deduplicated to {len(unique_chunks)} unique chunks")

        # Step 5: Rerank with original question
        final_chunks = self._rerank_with_original_question(question, unique_chunks, top_k)
        self.logger.info(f"✓ Multi-HyDE complete: {len(final_chunks)} final chunks")

        return final_chunks
