"""Simple logging utility"""

import logging
import sys
from typing import Literal


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_type: Literal["text", "json"] = "text"
) -> logging.Logger:
    """Setup a simple logger

    Args:
        name: Logger name
        level: Logging level
        format_type: "text" for human-readable or "json" for structured logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    if format_type == "json":
        formatter = logging.Formatter(
            '{"time":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", "message":"%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
