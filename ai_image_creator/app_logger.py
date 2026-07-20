"""Central logger. All modules log through `AppLogger`, never `print`.

Single off/level switch (Centralized-Logger rule): the whole app's logging is
configured here once and controlled by `Settings.log_level`.
"""

from __future__ import annotations

import logging

from ai_image_creator import constants


class AppLogger:
    _configured = False

    @classmethod
    def configure(cls, level: str = "INFO") -> None:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        )
        cls._configured = True

    @classmethod
    def get(cls) -> logging.Logger:
        if not cls._configured:
            cls.configure()
        return logging.getLogger(constants.LOGGER_NAME)
