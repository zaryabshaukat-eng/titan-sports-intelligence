"""Canonical controlled vocabularies for the sports domain."""

from enum import StrEnum


class CompetitionType(StrEnum):
    """The structural format of a competition."""

    LEAGUE = "league"
    CUP = "cup"
    TOURNAMENT = "tournament"
    PLAYOFF = "playoff"
    FRIENDLY = "friendly"
    OTHER = "other"


class SeasonStatus(StrEnum):
    """Lifecycle states for a competition season."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TeamType(StrEnum):
    """Canonical team classifications independent of data provider terminology."""

    CLUB = "club"
    NATIONAL = "national"
    REPRESENTATIVE = "representative"
    OTHER = "other"


class OfficialRole(StrEnum):
    """The role an official performs for a specific fixture."""

    REFEREE = "referee"
    ASSISTANT_REFEREE = "assistant_referee"
    FOURTH_OFFICIAL = "fourth_official"
    VIDEO_ASSISTANT = "video_assistant"
    OTHER = "other"
