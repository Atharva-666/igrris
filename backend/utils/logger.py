"""
logger.py — Centralized logging utility for Igrris AI.

Features:
  - Automatically creates the logs/ directory if it doesn't exist
  - Configures RotatingFileHandler to write logs to logs/igrris.log
  - Limits file size to 5MB with 3 backup files (rotates automatically)
  - Also outputs logs to stdout/console
  - Provides get_recent_logs() to read logs for UI display
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from backend.config import LOG_DIR, LOG_FILE

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level=logging.INFO) -> None:
    """
    Initialize logging handlers for stdout and logs/igrris.log.
    Called on application startup.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if setup_logging is called multiple times
    if root_logger.handlers:
        return

    # Console handler — force UTF-8 so emoji in email subjects never crash logging
    # on Windows (default cp1252 console). errors='backslashreplace' is a safety net.
    try:
        stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='backslashreplace', closefd=False)
    except Exception:
        stream = sys.stdout
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # Rotating file handler (5 MB per file, max 3 backup files)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(file_handler)


def get_recent_logs(max_lines: int = 100) -> str:
    """
    Read and return the last `max_lines` from logs/igrris.log.
    Returns a helpful message if the log file doesn't exist yet.
    """
    if not os.path.exists(LOG_FILE):
        return "[SYSTEM LOG] No log file created yet. Initiate a scan or action to generate logs."

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as e:
        return f"[SYSTEM LOG] Could not read log file: {e}"
