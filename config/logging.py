import logging
import os


DEFAULT_LOG_LEVEL = "INFO"


def configure_logging(level: str | None = None) -> None:
    resolved_level = (level or os.getenv("APP_LOG_LEVEL", DEFAULT_LOG_LEVEL)).upper()
    logging.basicConfig(
        level=getattr(logging, resolved_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
