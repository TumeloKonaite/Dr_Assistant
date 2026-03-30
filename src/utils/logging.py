from __future__ import annotations

import logging


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
