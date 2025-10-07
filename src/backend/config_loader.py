"""
Configuration Loader
Loads configuration from config.yaml and provides easy access to settings
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any

from utils.log_handler import LogHandler

class Config:
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
        self._resolve_paths()

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

    @property
    def company_name(self) -> str:
        """Get company name"""
        return self.config['company_name']
    
    @property
    def pdf_path(self) -> Path:
        """Get PDF file path for current company"""
        pdf_filename = self.config['pdf_files'][self.company_name]
        return self.data_folder / pdf_filename
    
    @property
    def markdown_path(self) -> Path:
        """Get markdown file path for current company"""
        pdf_filename = self.config["pdf_files"][self.company_name]
        markdown_filename = Path(pdf_filename).stem + ".md"
        return self.markdown_folder / markdown_filename

    @property
    def output_dir(self) -> Path:
        """Get output directory for current company"""
        output_dir = self.outputs_folder / self.company_name
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @property
    def chunks_path(self) -> Path:
        """Get chunks JSON path for current company"""
        return self.output_dir / f"{self.company_name}_chunks.json"

    @property
    def factsheet_path(self) -> Path:
        """Get factsheet markdown path for current company"""
        return self.output_dir / f"{self.company_name}_factsheet.md"

    @property
    def evaluation_path(self) -> Path:
        """Get evaluation JSON path for current company"""
        return self.output_dir / f"{self.company_name}_evaluation.json"

    @property
    def embedding_model(self) -> str:
        """Get embedding model name"""
        return self.config["embedding_model"]    
    
    @property
    def chunking_config(self) -> Dict[str, int]:
        """Get chunking configuration"""
        return self.config.get("chunking", {})
    
    def get_log_path(self) -> Path:
        """Get path for log file"""
        return self.logs_folder / "logs.log"
    
    def _create_file_handler(self, log_path: Path, max_lines: int):
        """Create and configure file handler"""
        file_handler = LogHandler(log_path, max_lines=max_lines, mode="a")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        return file_handler

    def _create_console_handler(self):
        """Create and configure console handler"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        return console_handler

    def _setup_base_logger(self, logger_name: str):
        """Setup base logger with cleared handlers"""
        logger = logging.getLogger(logger_name or __name__)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        return logger

    def setup_logger(
        self, log_name: str, logger_name: str = None, max_lines: int = 3000):
        """Setup logger with rotating file handler and console handler"""
        log_path = self.get_log_path(log_name)
        logger = self._setup_base_logger(logger_name)
        file_handler = self._create_file_handler(log_path, max_lines)
        console_handler = self._create_console_handler()
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    def __repr__(self):
        return (
            f"Config(company={self.company_name}, "
            f"pdf={self.pdf_path.name}, "
            f"output_dir={self.output_dir})"
        )

def load_config(config_path: str = None) -> Config:
    """Load configuration from YAML file"""
    return Config(config_path)

if __name__ == "__main__":
    config = load_config()
    logger = config.setup_logger("config_test", __name__)

    logger.info("Configuration loaded successfully!")
    logger.info(f"Company: {config.company_name}")
    logger.info(f"PDF Path: {config.pdf_path}")
    logger.info(f"Markdown Path: {config.markdown_path}")
    logger.info(f"Output Dir: {config.output_dir}")
    logger.info(f"Chunks Path: {config.chunks_path}")
    logger.info(f"Factsheet Path: {config.factsheet_path}")
    logger.info(f"Embedding Model: {config.embedding_model}")
    logger.info(f"Claude Model: {config.claude_model}")
