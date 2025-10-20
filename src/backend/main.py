"""
Main Pipeline Orchestrator
Runs the complete credit analysis pipeline from PDF to evaluated factsheet
"""

import sys
from datetime import datetime
from typing import Dict, Optional
from config_loader import load_config
from conversion.markdown_converter import MarkdownConverter
from extraction.extractor import MarkdownExtractor
from post_conversion_validation.conversion_validator import PDFExtractionValidator
from table_extraction.table_extractor import NumericalExtractor
from chunking.merge_chunking.chunk_merger import ChunkMerger
from chunking.semantic_chunking.semantic_chunker import SemanticChunker
from generation.factsheet_generator import FactsheetGenerator
from evaluation.ragas_evaluator import FactsheetEvaluator


class CreditAnalysisPipeline:
    """Orchestrates the complete credit analysis pipeline"""

    def __init__(self, config=None):
        """
        Initialize pipeline with configuration

        Args:
            config: Config object. If None, loads default config.
        """
        self.config = config or load_config()
        self._setup_logging()

        # Initialize all components
        self.logger.info("Initializing pipeline components...")
        self.converter = MarkdownConverter(self.config)
        self.extractor = MarkdownExtractor(self.config)
        self.pdf_validator = PDFExtractionValidator(self.config)
        self.numerical_extractor = NumericalExtractor(self.config)
        self.chunk_merger = ChunkMerger(self.config)
        self.semantic_chunker = SemanticChunker(self.config)
        self.generator = FactsheetGenerator(self.config)
        self.evaluator = FactsheetEvaluator(self.config)

    def _setup_logging(self):
        """Setup main pipeline logging"""
        self.logger = self.config.setup_logger("main_pipeline", __name__)

    def _log_pipeline_start(self, company: str):
        """Log pipeline start"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"STARTING PIPELINE FOR: {company.upper()}")
        self.logger.info(f"{'='*80}\n")

    def _handle_pdf_conversion(self, skip_conversion: bool, results: Dict) -> object:
        """Handle PDF to Markdown conversion"""
        if skip_conversion and self.config.markdown_path.exists():
            self.logger.info("Step 1: Skipping PDF conversion (markdown exists)")
            return self.config.markdown_path

        self.logger.info("Step 1: Converting PDF to Markdown...")
        markdown_path = self.converter.convert_pdf_to_markdown()
        results['steps']['conversion'] = {'status': 'success', 'output': str(markdown_path)}
        self.logger.info(f"✓ Conversion complete: {markdown_path}")
        return markdown_path

    def run_single_company(self, company_name: Optional[str] = None,
                          skip_conversion: bool = False,
                          use_table_extraction: bool = True) -> Dict:
        """Run pipeline for a single company"""
        if company_name:
            self.config.set_company(company_name)

        company = self.config.company_name
        start_time = datetime.now()
        self._log_pipeline_start(company)

        results = {'company': company, 'status': 'started', 'steps': {}}

        try:
            markdown_path = self._handle_pdf_conversion(skip_conversion, results)
            self._validate_pdf_extraction(markdown_path, results)
            text_result = self._extract_and_chunk(markdown_path, results)

            # Extract tables and merge with text chunks if enabled
            if use_table_extraction:
                table_result = self._extract_table_chunks(results)
                merge_result = self._merge_chunks(text_result, table_result, results)
                semantic_result = self._apply_semantic_chunking_merged(merge_result, results)
            else:
                semantic_result = self._apply_semantic_chunking(text_result, results)

            factsheet_path = self._generate_factsheet(semantic_result, results)
            self._evaluate_factsheet(factsheet_path, semantic_result, results)
            results['status'] = 'completed'

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            results['status'] = 'failed'
            results['error'] = str(e)

        duration = (datetime.now() - start_time).total_seconds()
        results['duration_seconds'] = duration
        self._log_pipeline_summary(company, results, duration)

        return results

    def _run_pdf_validation(self, markdown_path):
        """Run PDF validation and return path"""
        self.logger.info("\nStep 2: Validating PDF extraction quality...")
        return self.pdf_validator.validate_extraction(
            pdf_path=self.config.pdf_path, markdown_path=markdown_path
        )

    def _load_validation_data(self, validation_path):
        """Load validation data from JSON"""
        import json
        with open(validation_path, 'r') as f:
            return json.load(f)

    def _build_validation_result(self, validation_data, validation_path):
        """Build validation result dictionary"""
        qual = validation_data['quality_assessment']
        return {
            'status': 'success',
            'quality': qual['quality'],
            'char_extraction_rate': qual['char_extraction_rate'],
            'keyword_coverage': qual['keyword_coverage_rate'],
            'output': str(validation_path)
        }

    def _log_validation_complete(self, validation_data):
        """Log validation completion"""
        qual = validation_data['quality_assessment']
        self.logger.info(f"✓ PDF validation complete: {qual['quality']} quality "
                        f"({qual['char_extraction_rate']:.1f}% extraction, "
                        f"{qual['keyword_coverage_rate']:.1f}% keywords)")

    def _validate_pdf_extraction(self, markdown_path, results: Dict):
        """Validate PDF extraction quality"""
        validation_path = self._run_pdf_validation(markdown_path)
        validation_data = self._load_validation_data(validation_path)
        results['steps']['pdf_validation'] = self._build_validation_result(validation_data, validation_path)
        self._log_validation_complete(validation_data)

    def _extract_and_chunk(self, markdown_path, results: Dict):
        """Extract and chunk markdown"""
        self.logger.info("\nStep 3: Extracting text chunks from markdown...")
        extraction_result = self.extractor.process_markdown_file(markdown_path)
        results['steps']['text_extraction'] = {
            'status': 'success',
            'num_chunks': extraction_result['num_chunks'],
            'avg_chunk_size': extraction_result['avg_chunk_size'],
            'output': str(extraction_result['chunks_path'])
        }
        self.logger.info(f"✓ Text extraction complete: {extraction_result['num_chunks']} chunks")
        return extraction_result

    def _extract_table_chunks(self, results: Dict):
        """Extract table chunks from tables JSON"""
        self.logger.info("\nStep 4: Extracting table chunks from tables...")
        try:
            table_result = self.numerical_extractor.run()
            results['steps']['table_extraction'] = {
                'status': 'success',
                'num_tables': table_result['num_tables'],
                'num_chunks': table_result['num_chunks'],
                'avg_chunk_size': table_result['avg_chunk_size'],
                'output': str(table_result['output_path'])
            }
            self.logger.info(f"✓ Table extraction complete: {table_result['num_chunks']} chunks from {table_result['num_tables']} tables")
            return table_result
        except FileNotFoundError:
            self.logger.warning("No tables JSON found, skipping table extraction")
            results['steps']['table_extraction'] = {
                'status': 'skipped',
                'reason': 'no_tables_file'
            }
            return {'num_chunks': 0, 'output_path': None}

    def _merge_chunks(self, text_result: Dict, table_result: Dict, results: Dict):
        """Merge text and table chunks"""
        if table_result['num_chunks'] == 0:
            self.logger.info("\nStep 5: Skipping chunk merge (no table chunks)")
            return text_result

        self.logger.info("\nStep 5: Merging text and table chunks...")
        merge_result = self.chunk_merger.run(
            text_chunks_path=text_result['chunks_path'],
            table_chunks_path=table_result['output_path']
        )
        results['steps']['chunk_merge'] = {
            'status': 'success',
            'text_chunks': merge_result['text_chunks'],
            'table_chunks': merge_result['table_chunks'],
            'total_chunks': merge_result['total_chunks'],
            'output': str(merge_result['output_path'])
        }
        self.logger.info(f"✓ Chunk merge complete: {merge_result['text_chunks']} text + {merge_result['table_chunks']} table = {merge_result['total_chunks']} total")
        return merge_result

    def _apply_semantic_chunking_merged(self, merge_result: Dict, results: Dict):
        """Apply semantic chunking to merged chunks"""
        self.logger.info("\nStep 6: Applying semantic chunking to merged chunks...")
        semantic_result = self.semantic_chunker.merge_chunks(chunks_path=merge_result['output_path'])
        results['steps']['semantic_chunking'] = self._build_semantic_result(semantic_result)
        self.logger.info(f"✓ Semantic chunking complete: {semantic_result['num_chunks']} chunks "
                        f"({semantic_result['reduction_pct']:.1f}% reduction)")
        return semantic_result

    def _build_semantic_result(self, semantic_result):
        """Build semantic chunking result dictionary"""
        return {
            'status': 'success',
            'num_chunks': semantic_result['num_chunks'],
            'original_chunks': semantic_result['original_chunks'],
            'reduction_pct': semantic_result['reduction_pct'],
            'output': str(semantic_result['output_path'])
        }

    def _apply_semantic_chunking(self, extraction_result: Dict, results: Dict):
        """Apply semantic chunking"""
        self.logger.info("\nStep 4: Applying semantic chunking...")
        semantic_result = self.semantic_chunker.merge_chunks(chunks_path=extraction_result['chunks_path'])
        results['steps']['semantic_chunking'] = self._build_semantic_result(semantic_result)
        self.logger.info(f"✓ Semantic chunking complete: {semantic_result['num_chunks']} chunks "
                        f"({semantic_result['reduction_pct']:.1f}% reduction)")
        return semantic_result

    def _generate_factsheet(self, semantic_result: Dict, results: Dict):
        """Generate factsheet"""
        self.logger.info("\nStep 5: Generating factsheet from semantic chunks...")
        factsheet_path = self.generator.generate_factsheet(chunks_path=semantic_result['output_path'])
        results['steps']['generation'] = {'status': 'success', 'output': str(factsheet_path)}
        self.logger.info(f"✓ Generation complete: {factsheet_path}")
        return factsheet_path

    def _run_evaluation(self, factsheet_path, semantic_result: Dict):
        """Run factsheet evaluation"""
        self.logger.info("\nStep 6: Evaluating factsheet quality...")
        return self.evaluator.evaluate_factsheet(
            factsheet_path=factsheet_path, chunks_path=semantic_result['output_path']
        )

    def _load_evaluation_data(self, evaluation_path):
        """Load evaluation data from JSON"""
        import json
        with open(evaluation_path, 'r') as f:
            return json.load(f)

    def _build_evaluation_result(self, eval_data, evaluation_path):
        """Build evaluation result dictionary"""
        return {
            'status': 'success',
            'overall_score': eval_data['overall_quality_score'],
            'scores': eval_data['aggregate_scores'],
            'output': str(evaluation_path)
        }

    def _evaluate_factsheet(self, factsheet_path, semantic_result: Dict, results: Dict):
        """Evaluate factsheet"""
        evaluation_path = self._run_evaluation(factsheet_path, semantic_result)
        eval_data = self._load_evaluation_data(evaluation_path)
        results['steps']['evaluation'] = self._build_evaluation_result(eval_data, evaluation_path)
        self.logger.info(f"✓ Evaluation complete: {evaluation_path}")

    def _log_summary_header(self, company: str, results: Dict, duration: float):
        """Log summary header"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"PIPELINE COMPLETE: {company.upper()}")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"  Status: {results['status']}")
        self.logger.info(f"  Duration: {duration:.1f} seconds")

    def _log_processing_stats(self, steps: Dict):
        """Log processing statistics"""
        # Handle both old and new key names for backwards compatibility
        text_chunks = steps.get('text_extraction', steps.get('extraction', {})).get('num_chunks', 0)

        self.logger.info(f"  Text Chunks: {text_chunks}")

        # Log table chunks if present
        if 'table_extraction' in steps and steps['table_extraction']['status'] == 'success':
            self.logger.info(f"  Table Chunks: {steps['table_extraction']['num_chunks']} "
                           f"from {steps['table_extraction']['num_tables']} tables")

        # Log merged chunks if present
        if 'chunk_merge' in steps:
            self.logger.info(f"  Merged Chunks: {steps['chunk_merge']['total_chunks']} "
                           f"({steps['chunk_merge']['text_chunks']} text + "
                           f"{steps['chunk_merge']['table_chunks']} table)")

        self.logger.info(f"  PDF Extraction Quality: {steps['pdf_validation']['quality']} "
                       f"({steps['pdf_validation']['char_extraction_rate']:.1f}% extraction, "
                       f"{steps['pdf_validation']['keyword_coverage']:.1f}% keywords)")
        self.logger.info(f"  Semantic Chunks: {steps['semantic_chunking']['num_chunks']} "
                       f"({steps['semantic_chunking']['reduction_pct']:.1f}% reduction)")
        self.logger.info(f"  Factsheet Quality Score: {steps['evaluation']['overall_score']:.3f}")

    def _log_output_paths(self, steps: Dict):
        """Log output file paths"""
        self.logger.info("  Outputs:")
        self.logger.info(f"    - Markdown: {self.config.markdown_path}")

        # Log text chunks
        text_output = steps.get('text_extraction', steps.get('extraction', {})).get('output')
        if text_output:
            self.logger.info(f"    - Text Chunks: {text_output}")

        # Log table chunks if present
        if 'table_extraction' in steps and steps['table_extraction']['status'] == 'success':
            self.logger.info(f"    - Table Chunks: {steps['table_extraction']['output']}")

        # Log merged chunks if present
        if 'chunk_merge' in steps:
            self.logger.info(f"    - Merged Chunks: {steps['chunk_merge']['output']}")

        self.logger.info(f"    - PDF Validation: {steps['pdf_validation']['output']}")
        self.logger.info(f"    - Semantic Chunks: {steps['semantic_chunking']['output']}")
        self.logger.info(f"    - Factsheet: {self.config.factsheet_path}")
        self.logger.info(f"    - Factsheet Eval: {self.config.evaluation_path}")

    def _log_pipeline_summary(self, company: str, results: Dict, duration: float):
        """Log pipeline completion summary"""
        self._log_summary_header(company, results, duration)
        if results['status'] == 'completed':
            steps = results['steps']
            self._log_processing_stats(steps)
            self._log_output_paths(steps)
        self.logger.info(f"{'='*80}\n")

    def _get_companies_list(self):
        """Get list of companies from config"""
        return list(self.config.config['pdf_files'].keys())

    def _log_batch_start(self, companies):
        """Log batch processing start"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"RUNNING PIPELINE FOR {len(companies)} COMPANIES")
        self.logger.info(f"Companies: {', '.join(companies)}")
        self.logger.info(f"{'='*80}\n")

    def _process_companies(self, companies, skip_conversion: bool, use_table_extraction: bool):
        """Process all companies and return results"""
        all_results = {}
        successful = 0
        for i, company in enumerate(companies, 1):
            self.logger.info(f"\n[{i}/{len(companies)}] Processing {company}...")
            result = self.run_single_company(company, skip_conversion, use_table_extraction)
            all_results[company] = result
            if result['status'] == 'completed':
                successful += 1
        return all_results, successful

    def _log_batch_summary_header(self, successful, total):
        """Log batch summary header"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"BATCH PIPELINE COMPLETE")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"  Successful: {successful}/{total}")

    def _log_company_result(self, company: str, result: Dict):
        """Log individual company result"""
        status = "✓" if result['status'] == 'completed' else "✗"
        if result['status'] == 'completed':
            score = result['steps']['evaluation']['overall_score']
            self.logger.info(f"  {status} {company}: Quality Score = {score:.3f}")
        else:
            self.logger.info(f"  {status} {company}: {result.get('error', 'Failed')}")

    def _log_batch_results(self, all_results: Dict):
        """Log all batch results"""
        for company, result in all_results.items():
            self._log_company_result(company, result)
        self.logger.info(f"{'='*80}\n")

    def run_all_companies(self, skip_conversion: bool = False, use_table_extraction: bool = True) -> Dict:
        """Run pipeline for all companies in config"""
        companies = self._get_companies_list()
        self._log_batch_start(companies)
        all_results, successful = self._process_companies(companies, skip_conversion, use_table_extraction)
        self._log_batch_summary_header(successful, len(companies))
        self._log_batch_results(all_results)
        return all_results


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run complete credit analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single company (from config)
  python main.py

  # Process specific company
  python main.py --company dbs

  # Process all companies
  python main.py --all

  # Skip PDF conversion (use existing markdown)
  python main.py --skip-conversion

  # Use custom config
  python main.py --config ../../configs/custom_config.yaml
        """
    )

    parser.add_argument(
        '--company',
        type=str,
        help='Company to process. If not specified, uses config default.'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all companies in config'
    )
    parser.add_argument(
        '--skip-conversion',
        action='store_true',
        help='Skip PDF to Markdown conversion if markdown file exists'
    )
    parser.add_argument(
        '--no-tables',
        action='store_true',
        help='Skip table extraction and use text chunks only'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config.yaml file (optional)'
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config) if args.config else load_config()

    # Initialize pipeline
    pipeline = CreditAnalysisPipeline(config)

    # Run pipeline
    use_tables = not args.no_tables  # Invert the flag

    if args.all:
        # Process all companies
        results = pipeline.run_all_companies(args.skip_conversion, use_tables)
    else:
        # Process single company
        if args.company:
            config.set_company(args.company)
        results = pipeline.run_single_company(
            company_name=args.company,
            skip_conversion=args.skip_conversion,
            use_table_extraction=use_tables
        )

    # Exit with appropriate code
    if args.all:
        # For batch processing, check if any failed
        failed = sum(1 for r in results.values() if r['status'] != 'completed')
        sys.exit(failed)
    else:
        # For single company, check status
        sys.exit(0 if results['status'] == 'completed' else 1)


if __name__ == "__main__":
    main()