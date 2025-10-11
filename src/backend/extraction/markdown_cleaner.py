"""
Markdown Cleaner
Handles text preprocessing and artifact removal
"""

import re


class MarkdownCleaner:
    """Cleans and preprocesses markdown text"""

    def __init__(self, logger):
        """Initialize cleaner with logger"""
        self.logger = logger

    def _remove_html_comments(self, text: str) -> str:
        """Remove HTML comments from text"""
        return re.sub(r"<!--.*?-->", "", text)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive newlines and strip whitespace"""
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def clean_markdown_artifacts(self, markdown_text: str) -> str:
        """Remove artifacts like '<!-- image -->' and normalize whitespace"""
        self.logger.info("Cleaning markdown artifacts...")
        cleaned_text = self._remove_html_comments(markdown_text)
        cleaned_text = self._normalize_whitespace(cleaned_text)
        self.logger.info(f"Cleaned {len(markdown_text) - len(cleaned_text)} characters")
        return cleaned_text
