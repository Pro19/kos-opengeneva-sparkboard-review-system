# logging_utils.py
import logging
import os
import sys
from typing import Optional
from config import LOGGING_CONFIG

def setup_logger(
    name: str = "hackathon_review",
    log_level: Optional[int] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up and configure a logger."""
    # Get settings from config
    if log_level is None:
        log_level_str = LOGGING_CONFIG.get("default_level", "INFO")
        log_level = getattr(logging, log_level_str)
    
    if log_file is None:
        log_file = LOGGING_CONFIG.get("log_file")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create a default logger
logger = setup_logger()