"""
utils.py — Shared utilities: logging setup and output folder cleanup.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent / "logs"
OUTPUT_DIR = Path(__file__).parent / "output"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger to write to both console and a daily log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_filename = LOGS_DIR / f"{datetime.utcnow().strftime('%Y-%m-%d')}.log"

    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(log_filename, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        handlers=handlers,
    )


def cleanup_output() -> None:
    """Remove all files in /output to free up disk space after upload."""
    if not OUTPUT_DIR.exists():
        return

    removed = 0
    for item in OUTPUT_DIR.iterdir():
        if item.is_file():
            item.unlink()
            removed += 1
        elif item.is_dir():
            shutil.rmtree(item)
            removed += 1

    logging.getLogger(__name__).info("Cleaned up %d item(s) from output/", removed)
