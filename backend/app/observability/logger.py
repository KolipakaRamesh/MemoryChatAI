import logging
import sys
from app.config import settings


def setup_logging():
    """Setup structured logging for the application."""
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Remove all existing handlers to ensure our configuration takes effect
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Ensure this takes effect even if already configured
    )
    
    # Set third-party loggers to INFO for debugging
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.INFO)
    logging.getLogger("chromadb").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
