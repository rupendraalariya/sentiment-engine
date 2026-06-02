"""Shared logging helpers for the NLP Sentiment Analysis Engine.

Provides a single :func:`get_logger` factory so every module logs in a
consistent format and at a level controlled by configuration.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def _configure_root(level: str = "INFO") -> None:
    """Configure the root logger exactly once.

    Parameters
    ----------
    level:
        Logging level name (e.g. ``"INFO"``, ``"DEBUG"``).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    _CONFIGURED = True


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """Return a configured logger.

    Parameters
    ----------
    name:
        Logger name, typically ``__name__`` of the calling module.
    level:
        Optional explicit level. If ``None`` the configured root level is used.

    Returns
    -------
    logging.Logger
        A ready-to-use logger instance.
    """
    _configure_root(level or "INFO")
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
