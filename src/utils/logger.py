import logging
import sys
import os

def setup_logger(name: str, level=logging.INFO):
    """Configure logger with standard formatting"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Check for env var override
        env_level = os.getenv("LOG_LEVEL", "").upper()
        if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            level = getattr(logging, env_level)
            
        logger.setLevel(level)
        
    return logger
