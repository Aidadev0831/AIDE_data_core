"""Configuration loader for AIDE Pipeline"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv


def load_config(config_file: str | Path = "config/schedule.yaml") -> Dict[str, Any]:
    """Load pipeline configuration from YAML file

    Args:
        config_file: Path to schedule.yaml configuration file

    Returns:
        Dict containing pipeline configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    # Load environment variables
    load_dotenv()

    # Convert to Path object
    config_path = Path(config_file)
    if not config_path.is_absolute():
        # Resolve relative to project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load YAML
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Inject environment variables
    config["env"] = {
        "database_url": os.getenv("DATABASE_URL"),
        "claude_api_key": os.getenv("CLAUDE_API_KEY"),
        "naver_client_id": os.getenv("NAVER_CLIENT_ID"),
        "naver_client_secret": os.getenv("NAVER_CLIENT_SECRET"),
        "notion_api_key": os.getenv("NOTION_API_KEY"),
        "logging_level": os.getenv("LOGGING_LEVEL", "INFO"),
        "pipeline_mode": os.getenv("PIPELINE_MODE", "development"),
    }

    return config


def get_job_config(config: Dict[str, Any], job_name: str) -> Dict[str, Any]:
    """Get configuration for specific job

    Args:
        config: Full pipeline configuration
        job_name: Name of the job (e.g., 'naver_news')

    Returns:
        Dict containing job-specific configuration

    Raises:
        KeyError: If job not found in config
    """
    if job_name not in config.get("jobs", {}):
        available_jobs = list(config.get("jobs", {}).keys())
        raise KeyError(
            f"Job '{job_name}' not found. Available jobs: {', '.join(available_jobs)}"
        )

    return config["jobs"][job_name]
