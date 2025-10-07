"""
Configuration Loader
Loads configuration from config.yaml and provides easy access to settings
"""

import yaml
import logging
from pathlib import Path

from utils.log_handler import LogHandler

class ConfigLoader:
    """Config manager for the credit analysis RAG system"""

    def _get_default_config_path(self):
        """Get default config path"""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "configs" / "config.yaml"

    def __init__(self, config_path: str):
        if config_path is None:
            config_path = self._get_default_config_path()
        self.config_path = Path(config_path)
        self.config = None