"""Batch logs: account ids and exception codes only — never amounts or names."""

from __future__ import annotations

import logging
from pathlib import Path

from banking_pipeline.paths import work_dir

_LOGGER_NAME = "andean.batch"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s  %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    return logger


def attach_batch_file(batch_id: str) -> Path:
    log_dir = work_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{batch_id}.log"
    logger = get_logger()
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s  %(message)s", "%Y-%m-%d %H:%M:%S"))
    handler.name = f"batch-{batch_id}"
    logger.addHandler(handler)
    return path


def detach_batch_file(batch_id: str) -> None:
    logger = get_logger()
    name = f"batch-{batch_id}"
    for handler in list(logger.handlers):
        if getattr(handler, "name", "") == name:
            handler.close()
            logger.removeHandler(handler)
