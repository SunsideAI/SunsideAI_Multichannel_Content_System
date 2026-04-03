"""Sunside AI Content Autopilot — Google Autocomplete Client."""

import json
import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"

# Rate limiting: max 10 requests/minute
_last_request_times: list[float] = []
MAX_REQUESTS_PER_MINUTE = 10


def _throttle() -> None:
    """Enforce rate limit of 10 requests per minute."""
    now = time.time()
    # Remove timestamps older than 60 seconds
    while _last_request_times and _last_request_times[0] < now - 60:
        _last_request_times.pop(0)

    if len(_last_request_times) >= MAX_REQUESTS_PER_MINUTE:
        sleep_time = 60 - (now - _last_request_times[0]) + 0.5
        if sleep_time > 0:
            logger.debug(f"Autocomplete throttle: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

    _last_request_times.append(time.time())


def get_suggestions(keyword: str, language: str = "de") -> list[str]:
    """
    Get Google Autocomplete suggestions for a keyword.

    Args:
        keyword: The seed keyword
        language: Language code (default: 'de' for German)

    Returns:
        List of autocomplete suggestions
    """
    _throttle()

    try:
        resp = requests.get(
            AUTOCOMPLETE_URL,
            params={
                "client": "firefox",
                "hl": language,
                "q": keyword,
            },
            timeout=10,
        )
        resp.raise_for_status()

        data = json.loads(resp.text)
        suggestions = data[1] if len(data) > 1 else []
        return [s for s in suggestions if s.lower() != keyword.lower()]

    except Exception as e:
        logger.error(f"Autocomplete failed for '{keyword}': {e}")
        return []


def expand_keywords(
    seed_keywords: list[str],
    language: str = "de",
) -> dict[str, list[str]]:
    """
    Expand a list of seed keywords with autocomplete suggestions.

    Args:
        seed_keywords: List of keywords to expand
        language: Language code

    Returns:
        Dict mapping each seed keyword to its suggestions
    """
    results = {}
    for keyword in seed_keywords:
        suggestions = get_suggestions(keyword, language)
        if suggestions:
            results[keyword] = suggestions
            logger.debug(f"'{keyword}' → {len(suggestions)} suggestions")
    return results


# Default seed keywords for Sunside AI's domain
DEFAULT_SEEDS = [
    "immobilienmakler ki",
    "chatbot immobilien",
    "ki für makler",
    "immobilien automatisierung",
    "seo immobilienmakler",
    "telefonassistent immobilien",
    "immobilienmakler website",
    "immobilien leads generieren",
    "crm immobilienmakler",
    "immobilienmakler software",
]
