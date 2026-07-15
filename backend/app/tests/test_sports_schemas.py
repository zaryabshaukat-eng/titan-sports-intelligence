"""Unit tests for Sports API query validation and pagination boundaries."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.sports.schemas import FixtureFilters, PaginationParams


def test_pagination_rejects_unbounded_limit() -> None:
    """List endpoints never permit an unbounded database page."""
    with pytest.raises(ValidationError):
        PaginationParams(limit=101)


def test_fixture_filter_rejects_inverted_time_window() -> None:
    """Fixture filtering refuses a time range that cannot yield valid results."""
    with pytest.raises(ValidationError, match="starts_after"):
        FixtureFilters(
            starts_after=datetime(2026, 7, 16, tzinfo=UTC),
            starts_before=datetime(2026, 7, 15, tzinfo=UTC),
        )


def test_fixture_filter_rejects_naive_time_bound() -> None:
    """Fixture filtering requires an explicit timezone rather than a server default."""
    with pytest.raises(ValidationError, match="timezone offset"):
        FixtureFilters(starts_after=datetime(2026, 7, 15))
