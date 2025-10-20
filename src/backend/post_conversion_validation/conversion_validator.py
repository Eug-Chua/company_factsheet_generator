"""
PDF Extraction Validator
Validates PDF-to-markdown extraction quality by comparing metrics and keyword coverage
"""

import json
from pathlib import Path
from typing import Dict
from config_loader import load_config
from .pdf_analyzer import PDFAnalyzer
from .keyword_analyzer import KeywordAnalyzer


class PDFExtractionValidator:
    """Validates Docling extraction by comparing original PDF with generated markdown"""

    def __init__(self, config=None):
        """Initialize validator with PDF and keyword analyzers"""
        self.config = config or load_config()
        self.logger = self.config.setup_logger("pdf_validation", __name__)
        self.pdf_analyzer = PDFAnalyzer(self.logger, self.config)
        self.keyword_analyzer = KeywordAnalyzer()

    def validate_extraction(
        self, pdf_path: Path = None, markdown_path: Path = None
    ) -> Path:
        """
        Validate Docling extraction quality against original PDF.

        Performs a "smell test" to check if major information is missing:
        1. Character/word extraction rates
        2. Financial keyword coverage across categories

        Returns:
            Path to validation report JSON
        """
        # Resolve paths
        pdf_path = pdf_path or self.config.pdf_path
        markdown_path = markdown_path or self.config.markdown_path

        self.logger.info(f"Validating Docling extraction for: {self.config.company_name}")
        self.logger.info(f"  PDF: {pdf_path}")

        # Step 1: Extract PDF metadata and text
        self.logger.info("Step 1: Extracting PDF metadata and text...")
        pdf_metadata = self.pdf_analyzer.get_pdf_metadata(pdf_path)
        pdf_text = self.pdf_analyzer.extract_pdf_text(pdf_path)

        self.logger.info(
            f"  PDF: {pdf_metadata['page_count']} pages, "
            f"{pdf_metadata['pdf_char_count']:,} chars, "
            f"{pdf_metadata['pdf_word_count']:,} words"
        )

        # Step 2: Load markdown and tables
        self.logger.info("Step 2: Loading markdown and tables...")
        with open(markdown_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        # Include table text in validation
        table_text = self.pdf_analyzer.load_merged_chunks()
        extracted_text = f"{markdown_text}\n\n{table_text}" if table_text else markdown_text

        # Step 3: Calculate extraction metrics
        self.logger.info("Step 3: Calculating extraction metrics...")
        extraction_metrics = self._calculate_extraction_metrics(pdf_text, extracted_text)

        self.logger.info(
            f"  Docling: {extraction_metrics['markdown_char_count']:,} chars, "
            f"{extraction_metrics['markdown_word_count']:,} words"
        )
        self.logger.info(
            f"  Extraction rate: {extraction_metrics['char_extraction_rate']:.1f}% chars, "
            f"{extraction_metrics['word_extraction_rate']:.1f}% words"
        )

        # Step 4: Check keyword coverage
        self.logger.info("Step 4: Checking keyword coverage...")
        keyword_coverage = self.keyword_analyzer.check_keyword_presence(extracted_text)

        coverage_pct = keyword_coverage["overall"]["coverage"] * 100
        found = keyword_coverage["overall"]["total_found"]
        total = keyword_coverage["overall"]["total_keywords"]
        self.logger.info(
            f"  Overall keyword coverage: {coverage_pct:.1f}% ({found}/{total})"
        )

        # Step 5: Assess quality and save report
        quality_assessment = self._assess_quality(extraction_metrics, keyword_coverage)

        validation_report = {
            "company": self.config.company_name,
            "pdf_path": str(pdf_path),
            "markdown_path": str(markdown_path),
            "pdf_metadata": pdf_metadata,
            "extraction_metrics": extraction_metrics,
            "keyword_coverage": keyword_coverage,
            "quality_assessment": quality_assessment,
        }

        # Save report
        output_dir = self.config.outputs_folder / self.config.company_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.config.company_name}_extraction_validation.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(validation_report, f, indent=2)

        self.logger.info(f"✓ Validation complete: {output_path}")
        return output_path

    def _calculate_extraction_metrics(self, pdf_text: str, markdown_text: str) -> Dict:
        """
        Calculate extraction efficiency metrics.

        Returns:
            Dict with character/word counts and extraction rates
        """
        pdf_chars, md_chars = len(pdf_text), len(markdown_text)
        pdf_words, md_words = len(pdf_text.split()), len(markdown_text.split())

        return {
            "pdf_char_count": pdf_chars,
            "markdown_char_count": md_chars,
            "pdf_word_count": pdf_words,
            "markdown_word_count": md_words,
            "char_extraction_rate": (md_chars / pdf_chars * 100) if pdf_chars > 0 else 0,
            "word_extraction_rate": (md_words / pdf_words * 100) if pdf_words > 0 else 0,
        }

    def _assess_quality(self, extraction_metrics: Dict, keyword_coverage: Dict) -> Dict:
        """
        Smell test: Is major information missing?

        Not meant to be precise - keywords have synonyms, so 100% isn't expected.
        Just checks if extraction is "good enough" to proceed.

        Returns:
            Simple pass/warning status with any red flags
        """
        char_rate = extraction_metrics["char_extraction_rate"]
        keyword_rate = keyword_coverage["overall"]["coverage"]

        # Smell test: good enough to proceed?
        passes = char_rate >= 60 and keyword_rate >= 0.50

        # Note major red flags only
        red_flags = []
        if char_rate < 40:
            red_flags.append("Very low text extraction (<40%) - likely conversion failure")
        if keyword_rate < 0.3:
            red_flags.append("Very few keywords found (<30%) - major sections likely missing")

        # Check for completely missing categories (major red flag)
        for cat, data in keyword_coverage.items():
            if cat != "overall" and data["coverage"] == 0:
                red_flags.append(f"Entire category missing: {cat}")

        return {
            "status": "pass" if passes else "warning",
            "char_extraction_rate": char_rate,
            "keyword_coverage_rate": keyword_rate * 100,
            "red_flags": red_flags if red_flags else ["None"],
            "recommendation": "Extraction looks good - proceed" if passes else "Review extraction before proceeding"
        }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point for validation"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Docling PDF extraction quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate default company from config
  python conversion_validator.py

  # Validate specific company
  python conversion_validator.py --company dbs

  # Use custom config
  python conversion_validator.py --config /path/to/config.yaml
        """
    )

    parser.add_argument('--company', type=str,
                       help='Company to validate (optional, uses config default)')
    parser.add_argument('--config', type=str,
                       help='Path to config.yaml file (optional)')

    args = parser.parse_args()

    # Load config and set company
    config = load_config(args.config) if args.config else load_config()
    if args.company:
        config.set_company(args.company)

    # Run validation
    validator = PDFExtractionValidator(config)
    report_path = validator.validate_extraction()
    print(f"\n✓ Validation report saved to: {report_path}")


if __name__ == "__main__":
    main()
