"""Explicit football-data.org country vocabulary normalization."""

from __future__ import annotations


class FootballDataCountryNormalizationError(ValueError):
    """Raised when a provider country code has no approved canonical mapping."""


_COUNTRY_ISO2_MAP: dict[str, str] = {
    "ENG": "GB",
}


def normalize_football_data_country_code(provider_code: str) -> str:
    """Map only explicitly approved provider country codes to canonical ISO-2 values."""
    normalized = provider_code.strip().upper()
    try:
        return _COUNTRY_ISO2_MAP[normalized]
    except KeyError as exc:
        raise FootballDataCountryNormalizationError(
            f"unsupported football-data.org country code '{provider_code}'"
        ) from exc
