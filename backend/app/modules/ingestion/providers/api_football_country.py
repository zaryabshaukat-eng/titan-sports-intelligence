"""Explicit API-Football country-vocabulary normalization at the provider boundary."""

from __future__ import annotations


class ApiFootballCountryNormalizationError(ValueError):
    """Raised when a provider country identifier has no approved canonical mapping."""


_API_FOOTBALL_COUNTRY_ISO2: dict[str, str] = {
    "GB-ENG": "GB",
}


def normalize_api_football_country_code(provider_code: str) -> str:
    """Return the approved ISO-3166 alpha-2 code for one exact provider identifier.

    This is intentionally a finite lookup: provider codes are neither truncated nor
    syntactically transformed, and unknown values fail closed.
    """
    try:
        return _API_FOOTBALL_COUNTRY_ISO2[provider_code]
    except KeyError as exc:
        raise ApiFootballCountryNormalizationError(
            f"unsupported API-Football country code '{provider_code}'"
        ) from exc
