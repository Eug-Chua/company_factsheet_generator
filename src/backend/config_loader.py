"""
Configuration Loader
Loads configuration from config.yaml and provides easy access to settings
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any

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
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML config file"""
        with open(self.config_path,'r') as f:
            return yaml.safe_load(f)
        
    