"""Global configuration settings for the Coordinate Converter."""

import os


VALID_ENVS = {"dev", "staging", "prod"}


def _get_str_env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    value = value.strip() if isinstance(value, str) else default
    return value or default


def _get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _normalize_env(value: str) -> str:
    normalized = (value or "dev").strip().lower()
    return normalized if normalized in VALID_ENVS else "dev"


APP_VERSION = _get_str_env("APP_VERSION", "1.0.0")
APP_TITLE = _get_str_env("APP_TITLE", "Coordinate Converter")
ENV = _normalize_env(os.getenv("APP_ENV", "dev"))
SHOW_DEBUG_INFO = ENV == "dev"

MAX_UPLOAD_SIZE_MB = _get_int_env("MAX_UPLOAD_SIZE_MB", 10)
DEFAULT_CACHE_TTL = _get_int_env("DEFAULT_CACHE_TTL", 3600)
GEOCODE_TIMEOUT_SECONDS = _get_int_env("GEOCODE_TIMEOUT_SECONDS", 10)
GEOCODE_MAX_RETRIES = _get_int_env("GEOCODE_MAX_RETRIES", 3)
GEOCODE_RETRY_BACKOFF_SECONDS = _get_float_env(
    "GEOCODE_RETRY_BACKOFF_SECONDS",
    0.5,
)
GPS_TIMEOUT_MS = _get_int_env("GPS_TIMEOUT_MS", 10000)
