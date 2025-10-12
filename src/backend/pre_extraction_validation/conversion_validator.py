"""
PDF Extraction Validator
Orchestrates validation of PDF extraction quality
"""

import json
from pathlib import Path
from typing import Dict, List
from config_loader import load_config
from .pdf_analyzer import PDFAnalyzer
from .keyword_analyzer import KeywordAnalyzer


class PDFExtractionValidator:
    """Validates Docling extraction by comparing with original PDF"""

    def __init__(self, config=None):
        """Initialize validator with configuration"""
        self.config = config or load_config()
        self._setup_logging()
        self._initialize_analyzers()

    def _setup_logging(self):
        """Setup logging for PDF validation"""
        self.logger = self.config.setup_logger("pdf_validation", __name__)

    def _initialize_analyzers(self):
        """Initialize PDF and keyword analyzers"""
        self.pdf_analyzer = PDFAnalyzer(self.logger, self.config)
        self.keyword_analyzer = KeywordAnalyzer()

    def calculate_extraction_metrics(self, pdf_text: str, markdown_text: str) -> Dict:
        """Calculate extraction efficiency metrics"""
        pdf_chars, md_chars = len(pdf_text), len(markdown_text)
        pdf_words, md_words = len(pdf_text.split()), len(markdown_text.split())
        return {
            "pdf_char_count": pdf_chars,
            "markdown_char_count": md_chars,
            "pdf_word_count": pdf_words,
            "markdown_word_count": md_words,
            "char_extraction_rate": (md_chars / pdf_chars * 100)
            if pdf_chars > 0
            else 0,
            "word_extraction_rate": (md_words / pdf_words * 100)
            if pdf_words > 0
            else 0,
        }

    def _log_pdf_info(self, pdf_metadata: Dict):
        """Log PDF information"""
        self.logger.info(
            f"  PDF: {pdf_metadata['page_count']} pages, "
            f"{pdf_metadata['pdf_char_count']:,} chars, "
            f"{pdf_metadata['pdf_word_count']:,} words"
        )

    def _log_extraction_info(self, extraction_metrics: Dict):
        """Log extraction metrics"""
        self.logger.info(
            f"  Docling: {extraction_metrics['markdown_char_count']:,} chars, "
            f"{extraction_metrics['markdown_word_count']:,} words"
        )
        self.logger.info(
            f"  Extraction rate: {extraction_metrics['char_extraction_rate']:.1f}% chars, "
            f"{extraction_metrics['word_extraction_rate']:.1f}% words"
        )

    def _log_keyword_info(self, markdown_keywords: Dict):
        """Log keyword coverage info"""
        coverage = markdown_keywords["overall"]["coverage"] * 100
        found = markdown_keywords["overall"]["total_found"]
        total = markdown_keywords["overall"]["total_keywords"]
        self.logger.info(
            f"  Overall keyword coverage: {coverage:.1f}% ({found}/{total})"
        )

    def _build_validation_report(
        self,
        pdf_path: Path,
        markdown_path: Path,
        pdf_metadata: Dict,
        extraction_metrics: Dict,
        markdown_keywords: Dict,
    ) -> Dict:
        """Build validation report dictionary"""
        return {
            "company": self.config.company_name,
            "pdf_path": str(pdf_path),
            "markdown_path": str(markdown_path),
            "pdf_metadata": pdf_metadata,
            "extraction_metrics": extraction_metrics,
            "keyword_coverage": markdown_keywords,
            "quality_assessment": self._assess_quality(
                extraction_metrics, markdown_keywords
            ),
        }

    def _save_validation_report(self, validation_report: Dict) -> Path:
        """Save validation report to JSON"""
        output_dir = self.config.outputs_folder / self.config.company_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = (
            output_dir / f"{self.config.company_name}_extraction_validation.json"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(validation_report, f, indent=2)
        return output_path

    def _resolve_validation_paths(self, pdf_path, markdown_path):
        """Resolve PDF and markdown paths"""
        return (
            pdf_path or self.config.pdf_path,
            markdown_path or self.config.markdown_path,
        )

    def _log_validation_start(self, pdf_path):
        """Log validation start information"""
        self.logger.info(
            f"Validating Docling extraction for: {self.config.company_name}"
        )
        self.logger.info(f"  PDF: {pdf_path}")

    def _extract_pdf_text_and_metadata(self, pdf_path):
        """Extract PDF metadata and text (Step 1)"""
        self.logger.info("Step 1: Extracting PDF metadata and text...")
        pdf_metadata = self.pdf_analyzer.get_pdf_metadata(pdf_path)
        pdf_text = self.pdf_analyzer.extract_pdf_text(pdf_path)
        self._log_pdf_info(pdf_metadata)
        return pdf_metadata, pdf_text

    def _load_markdown_text(self, markdown_path):
        """Load markdown file text"""
        with open(markdown_path, "r", encoding="utf-8") as f:
            return f.read()

    def _combine_markdown_and_tables(self, markdown_text: str, table_text: str):
        """Combine markdown and table text"""
        if table_text:
            return f"{markdown_text}\n\n{table_text}"
        return markdown_text

    def _get_extracted_text(self, markdown_path):
        """Get extracted text from markdown and tables (Step 2)"""
        self.logger.info("Step 2: Loading markdown and tables...")
        markdown_text = self._load_markdown_text(markdown_path)
        table_text = self.pdf_analyzer.load_merged_chunks()
        return self._combine_markdown_and_tables(markdown_text, table_text)

    def _calculate_and_log_metrics(self, pdf_text, extracted_text):
        """Calculate extraction metrics (Step 3)"""
        self.logger.info("Step 3: Calculating extraction metrics...")
        extraction_metrics = self.calculate_extraction_metrics(pdf_text, extracted_text)
        self._log_extraction_info(extraction_metrics)
        return extraction_metrics

    def _check_and_log_keywords(self, extracted_text):
        """Check keyword coverage (Step 4)"""
        self.logger.info("Step 4: Checking keyword coverage...")
        keywords_coverage = self.keyword_analyzer.check_keyword_presence(extracted_text)
        self._log_keyword_info(keywords_coverage)
        return keywords_coverage

    def _build_and_save_report(
        self,
        pdf_path,
        markdown_path,
        pdf_metadata,
        extraction_metrics,
        keywords_coverage,
    ):
        """Build and save validation report (Step 5)"""
        validation_report = self._build_validation_report(
            pdf_path, markdown_path, pdf_metadata, extraction_metrics, keywords_coverage
        )
        return self._save_validation_report(validation_report)

    def validate_extraction(
        self, pdf_path: Path = None, markdown_path: Path = None
    ) -> Path:
        """Validate Docling extraction quality against original PDF"""
        pdf_path, markdown_path = self._resolve_validation_paths(
            pdf_path, markdown_path
        )
        self._log_validation_start(pdf_path)
        pdf_metadata, pdf_text = self._extract_pdf_text_and_metadata(pdf_path)
        extracted_text = self._get_extracted_text(markdown_path)
        extraction_metrics = self._calculate_and_log_metrics(pdf_text, extracted_text)
        keywords_coverage = self._check_and_log_keywords(extracted_text)
        output_path = self._build_and_save_report(
            pdf_path, markdown_path, pdf_metadata, extraction_metrics, keywords_coverage
        )
        self.logger.info(f"✓ Validation complete: {output_path}")
        return output_path

    def _determine_quality_level(
        self, char_rate: float, keyword_rate: float
    ) -> tuple[str, str]:
        """Determine quality level and status"""
        MIN_EXTRACTION_RATE, GOOD_KEYWORD_COVERAGE, FAIR_KEYWORD_COVERAGE = (
            70,
            0.85,
            0.60,
        )
        if char_rate >= MIN_EXTRACTION_RATE and keyword_rate >= GOOD_KEYWORD_COVERAGE:
            return "Excellent", "pass"
        elif char_rate >= MIN_EXTRACTION_RATE and keyword_rate >= FAIR_KEYWORD_COVERAGE:
            return "Good", "pass"
        elif char_rate >= 50 and keyword_rate >= 0.50:
            return "Fair", "warning"
        return "Poor", "fail"

    def _add_extraction_rate_issue(self, issues, char_rate, MIN_EXTRACTION_RATE):
        """Add extraction rate issue if below threshold"""
        if char_rate < MIN_EXTRACTION_RATE:
            issues.append(
                f"Low extraction rate: {char_rate:.1f}% (expected >{MIN_EXTRACTION_RATE}%)"
            )

    def _add_keyword_coverage_issue(self, issues, keyword_rate, FAIR_KEYWORD_COVERAGE):
        """Add keyword coverage issue if below threshold"""
        if keyword_rate < FAIR_KEYWORD_COVERAGE:
            issues.append(
                f"Low keyword coverage: {keyword_rate * 100:.1f}% (expected >{FAIR_KEYWORD_COVERAGE * 100}%)"
            )

    def _add_category_coverage_issues(self, issues, keyword_coverage):
        """Add category-specific coverage issues"""
        for category, data in keyword_coverage.items():
            if category != "overall" and data["coverage"] < 0.5:
                issues.append(
                    f"Poor coverage in {category}: {data['coverage'] * 100:.1f}%)"
                )

    def _identify_issues(
        self, char_rate: float, keyword_rate: float, keyword_coverage: Dict
    ) -> List[str]:
        """Identify extraction issues"""
        MIN_EXTRACTION_RATE, FAIR_KEYWORD_COVERAGE = 70, 0.60
        issues = []
        self._add_extraction_rate_issue(issues, char_rate, MIN_EXTRACTION_RATE)
        self._add_keyword_coverage_issue(issues, keyword_rate, FAIR_KEYWORD_COVERAGE)
        self._add_category_coverage_issues(issues, keyword_coverage)
        return issues if issues else ["None - extraction quality is good"]

    def _extract_rates(self, extraction_metrics, keyword_coverage):
        """Extract char and keyword rates"""
        char_rate = extraction_metrics["char_extraction_rate"]
        keyword_rate = keyword_coverage["overall"]["coverage"]
        return char_rate, keyword_rate

    def _build_quality_assessment_dict(
        self, quality, status, char_rate, keyword_rate, issues
    ):
        """Build quality assessment dictionary"""
        return {
            "quality": quality,
            "status": status,
            "char_extraction_rate": char_rate,
            "keyword_coverage_rate": keyword_rate * 100,
            "issues": issues,
            "recommendation": self._get_recommendation(quality, issues),
        }

    def _assess_quality(self, extraction_metrics: Dict, keyword_coverage: Dict) -> Dict:
        """Assess overall extraction quality"""
        char_rate, keyword_rate = self._extract_rates(
            extraction_metrics, keyword_coverage
        )
        quality, status = self._determine_quality_level(char_rate, keyword_rate)
        issues = self._identify_issues(char_rate, keyword_rate, keyword_coverage)
        return self._build_quality_assessment_dict(
            quality, status, char_rate, keyword_rate, issues
        )

    def _get_recommendation(self, quality: str, issues: List[str]) -> str:
        """Get recommendation based on quality assessment"""
        recommendations = {
            "Excellent": "Extraction quality is excellent. Proceed with semantic chunking.",
            "Good": "Extraction quality is good. Proceed with semantic chunking.",
            "Fair": "Extraction quality is fair. Review missing keywords before proceeding. Consider adjusting Docling parameters.",
            "Poor": "Extraction quality is poor. Review PDF conversion settings or consider alternative extraction method.",
        }
        return recommendations.get(quality, "Unknown quality level")


# CLI Functions


def _create_cli_parser():
    """Create argument parser for CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Docling PDF extraction")
    parser.add_argument(
        "--company",
        type=str,
        help="Company to validate (optional, uses config default)",
    )
    parser.add_argument(
        "--config", type=str, help="Path to config.yaml file (optional)"
    )
    return parser


def _load_and_configure_config(args):
    """Load config and set company if specified"""
    config = load_config(args.config) if args.config else load_config()
    if args.company:
        config.set_company(args.company)
    return config


def _run_validation_and_print(config):
    """Run validation and print result"""
    validator = PDFExtractionValidator(config)
    report_path = validator.validate_extraction()
    print(f"\n✓ Validation report saved to: {report_path}")


def main():
    """CLI entry point for testing"""
    parser = _create_cli_parser()
    args = parser.parse_args()
    config = _load_and_configure_config(args)
    _run_validation_and_print(config)


if __name__ == "__main__":
    main()
