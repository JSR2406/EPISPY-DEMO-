"""Logging configuration for the epidemic AI system."""
import logging
import logging.handlers
import os
from typing import Optional
from .config import settings

def setup_logger(
    name: str, 
    log_file: Optional[str] = None, 
    level: str = None
) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or settings.log_level))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file or settings.log_file:
        log_path = log_file or settings.log_file
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=10485760, backupCount=5  # 10MB files, keep 5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Global logger instances
main_logger = setup_logger("epidemic_ai")
api_logger = setup_logger("epidemic_ai.api")
agent_logger = setup_logger("epidemic_ai.agent")
model_logger = setup_logger("epidemic_ai.models")
data_logger = setup_logger("epidemic_ai.data")
