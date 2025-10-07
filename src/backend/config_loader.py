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
        
    def _resolve_folder_paths(self, project_root: Path):
        """Resolve folder paths"""
        self.data_folder = (project_root / self.config['data_folder']).resolve()
        self.markdown_folder = (project_root / self.config['markdown_folder']).resolve()
        self.outputs_folder = (project_root / self.config['outputs_folder']).resolve()
        self.logs_folder = (project_root / self.config['logs_folder']).resolve()
        self.question_set_path = (project_root / self.config['question_set_path']).resolve()

    def _create_directories(self):
        """Create the necessary directories"""
        self.markdown_folder.mkdir(parents=True, exist_ok=True)
        self.outputs_folder.mkdir(parents=True, exist_ok=True)
        self.logs_folder.mkdir(parents=True, exist_ok=True)

    def _resolve_paths(self):
        """Convert relative paths to absolute paths"""
        project_root = Path(__file__).parent.parent.parent
        self._resolve_folder_paths(project_root)
        self._create_directories()