import logging
from logging import Logger, StreamHandler, FileHandler
from logging.handlers import RotatingFileHandler

from typing import Optional

class OrchestratorLogger:
    """
    Centralized logger configuration for the orchestrator.
    Provides a structured logger with console and file handlers.

    Usage:
        logger = OrchestratorLogger.get_logger()
        logger.info("Message...")
    """
    _logger: Optional[Logger] = None

    @classmethod
    def get_logger(cls, name: str = "owl",
                   log_file: Optional[str] = None,
                   level: int = logging.INFO,
                   max_bytes: int = 10 * 1024 * 1024,
                   backup_count: int = 5) -> Logger:
        if cls._logger:
            return cls._logger

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # Basic structured formatter
        formatter = logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        ch = StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Rotating file handler if requested
        if log_file:
            fh = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        cls._logger = logger
        return logger
