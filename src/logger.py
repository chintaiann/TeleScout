"""Logging configuration for TeleScout."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_to_file: bool = True) -> None:
    """Set up logging configuration for TeleScout."""
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    # Configure log format
    log_format = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"telescout_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        logging.info(f"Logging to file: {log_file}")
    
    # Reduce noise from telethon
    logging.getLogger('telethon').setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")