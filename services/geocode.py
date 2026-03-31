import logging
import time
from typing import Tuple

import requests

from config.settings import (
    GEOCODE_MAX_RETRIES,
    GEOCODE_RETRY_BACKOFF_SECONDS,
    GEOCODE_TIMEOUT_SECONDS,
)


logger = logging.getLogger(__name__)


def geocode_address(address: str) -> Tuple[float | None, float | None]:
    """Resolve a free-form address via Nominatim with retry + logging."""
    normalized_address = (address or "").strip()
    if not normalized_address:
        logger.warning("Geocode skipped: empty address input.")
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": normalized_address, "format": "json", "limit": 1}
    headers = {"User-Agent": "CoordinateConverter_App"}

    for attempt in range(1, GEOCODE_MAX_RETRIES + 1):
        try:
            logger.info(
                "Geocode request started for address=%r attempt=%s/%s",
                normalized_address,
                attempt,
                GEOCODE_MAX_RETRIES,
            )
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=GEOCODE_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(
                    "Geocode returned no result for address=%r",
                    normalized_address,
                )
                return None, None

            lon = float(data[0]["lon"])
            lat = float(data[0]["lat"])
            logger.info(
                "Geocode request succeeded for address=%r lon=%s lat=%s",
                normalized_address,
                lon,
                lat,
            )
            return lon, lat
        except requests.Timeout:
            logger.warning(
                "Geocode timeout for address=%r attempt=%s/%s timeout=%ss",
                normalized_address,
                attempt,
                GEOCODE_MAX_RETRIES,
                GEOCODE_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logger.warning(
                "Geocode HTTP error for address=%r attempt=%s/%s error=%s",
                normalized_address,
                attempt,
                GEOCODE_MAX_RETRIES,
                exc,
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.error(
                "Geocode response parse failed for address=%r error=%s",
                normalized_address,
                exc,
            )
            return None, None

        if attempt < GEOCODE_MAX_RETRIES:
            backoff_seconds = GEOCODE_RETRY_BACKOFF_SECONDS * attempt
            logger.info(
                "Geocode retry scheduled for address=%r in %.1fs",
                normalized_address,
                backoff_seconds,
            )
            time.sleep(backoff_seconds)

    logger.error(
        "Geocode failed after retries for address=%r attempts=%s",
        normalized_address,
        GEOCODE_MAX_RETRIES,
    )
    return None, None
