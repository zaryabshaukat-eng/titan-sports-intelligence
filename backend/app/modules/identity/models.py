"""Identity roles, permissions, and authenticated-principal contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Permission(StrEnum):
    """Stable backend permission vocabulary independent of identity-provider claims."""

    DATA_READ = "data:read"
    FIXTURE_INGEST = "fixtures:ingest"
    MARKET_DATA_INGEST = "market_data:ingest"
    STATISTICS_INGEST = "statistics:ingest"
    OUTBOX_OPERATE = "outbox:operate"


class Role(StrEnum):
    """Initial TITAN internal roles; future providers map their claims to these roles."""

    ADMIN = "titan_admin"
    DATA_INGESTOR = "data_ingestor"
    ANALYST = "analyst"
    OPERATOR = "operator"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.DATA_INGESTOR: frozenset(
        {
            Permission.DATA_READ,
            Permission.FIXTURE_INGEST,
            Permission.MARKET_DATA_INGEST,
            Permission.STATISTICS_INGEST,
        }
    ),
    Role.ANALYST: frozenset({Permission.DATA_READ}),
    Role.OPERATOR: frozenset({Permission.DATA_READ, Permission.OUTBOX_OPERATE}),
}


@dataclass(frozen=True, slots=True)
class Principal:
    """Provider-neutral verified identity used by authorization dependencies."""

    subject: str
    organization_id: str | None
    roles: frozenset[Role]

    @property
    def permissions(self) -> frozenset[Permission]:
        """Derive effective permissions from stable TITAN roles."""
        return frozenset().union(*(ROLE_PERMISSIONS[role] for role in self.roles))

    def permits(self, *required: Permission) -> bool:
        """Return whether all required permissions are granted to this principal."""
        return set(required).issubset(self.permissions)
