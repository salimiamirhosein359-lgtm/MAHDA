"""Logging setup for AI Sentinel."""
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    # quiet noisy libs
    for name in ("httpx", "apscheduler", "sentence_transformers", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)
