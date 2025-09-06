# logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
import colorlog

# Directory for logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Define log colors for console
log_colors = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# Formatter for console with colors
console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors=log_colors,
)

# Formatter for file (no colors)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str = "AppLogger") -> logging.Logger:
    """Create and return a logger instance with both console + file handlers"""
    logger = logging.getLogger(name)

    if not logger.handlers:  # Avoid adding handlers multiple times
        logger.setLevel(logging.DEBUG)

        # Console handler (with colors)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)

        # File handler (rotating log file)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
