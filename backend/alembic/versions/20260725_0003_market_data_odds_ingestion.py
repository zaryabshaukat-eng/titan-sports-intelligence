"""Create immutable Market Data and Odds Ingestion bounded-context tables.

Revision ID: 20260725_0003
Revises: 20260715_0002
Create Date: 2026-07-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260725_0003"
down_revision: str | None = "20260715_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMP = sa.DateTime(timezone=True)
JSONB = postgresql.JSONB()

odds_ingestion_run_status = postgresql.ENUM(
    "running",
    "completed",
    "completed_with_errors",
    "failed",
    name="market_data_odds_ingestion_run_status",
    create_type=False,
)
raw_odds_payload_status = postgresql.ENUM(
    "received",
    "valid",
    "invalid",
    "applied",
    name="market_data_raw_odds_payload_status",
    create_type=False,
)
odds_audit_outcome = postgresql.ENUM(
    "processed",
    "unchanged",
    "validation_failed",
    name="market_data_odds_audit_outcome",
    create_type=False,
)
provider_entity_type = postgresql.ENUM(
    "fixture",
    "bookmaker",
    "market",
    "selection",
    name="market_data_provider_entity_type",
    create_type=False,
)
odds_movement_type = postgresql.ENUM(
    "opening",
    "closing",
    "price_increased",
    "price_decreased",
    "market_suspended",
    "market_reopened",
    "selection_added",
    "selection_removed",
    name="market_data_odds_movement_type",
    create_type=False,
)
market_data_event_type = postgresql.ENUM(
    "OddsSnapshotCreated",
    "OddsChanged",
    "MarketSuspended",
    "MarketReopened",
    "OddsValidationFailed",
    name="market_data_event_type",
    create_type=False,
)


def audit_columns() -> list[sa.Column[object]]:
    """Return the common UUID identity and audit timestamp columns."""
    return [
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "created_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    ]


def upgrade() -> None:
    """Create canonical market entities, immutable odds history, and market-data provenance."""
    bind = op.get_bind()
    odds_ingestion_run_status.create(bind, checkfirst=True)
    raw_odds_payload_status.create(bind, checkfirst=True)
    odds_audit_outcome.create(bind, checkfirst=True)
    provider_entity_type.create(bind, checkfirst=True)
    odds_movement_type.create(bind, checkfirst=True)
    market_data_event_type.create(bind, checkfirst=True)

    op.create_table(
        "market_data_bookmakers",
        *audit_columns(),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("website_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("deleted_at", TIMESTAMP, nullable=True),
        sa.UniqueConstraint("name", name="uq_market_data_bookmakers_name"),
        sa.UniqueConstraint("code", name="uq_market_data_bookmakers_code"),
    )
    op.create_index("ix_market_data_bookmakers_name", "market_data_bookmakers", ["name"])
    op.create_index(
        "ix_market_data_bookmakers_deleted_at", "market_data_bookmakers", ["deleted_at"]
    )

    op.create_table(
        "market_data_market_types",
        *audit_columns(),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameter_schema", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.UniqueConstraint("code", name="uq_market_data_market_types_code"),
    )

    op.create_table(
        "market_data_market_statuses",
        *audit_columns(),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_terminal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("sort_order >= 0", name="ck_market_data_market_statuses_sort_order"),
        sa.UniqueConstraint("code", name="uq_market_data_market_statuses_code"),
    )

    market_type_table = sa.table(
        "market_data_market_types",
        sa.column("id", UUID),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        market_type_table,
        [
            {
                "id": "10000000-0000-0000-0000-000000000001",
                "code": "match_winner",
                "name": "Match Winner",
                "description": "Outcome market with home, draw, and away selections.",
                "is_active": True,
            },
            {
                "id": "10000000-0000-0000-0000-000000000002",
                "code": "double_chance",
                "name": "Double Chance",
                "description": "Two-outcome coverage of match winner selections.",
                "is_active": True,
            },
            {
                "id": "10000000-0000-0000-0000-000000000003",
                "code": "draw_no_bet",
                "name": "Draw No Bet",
                "description": "Winner market with draw stakes returned.",
                "is_active": True,
            },
            {
                "id": "10000000-0000-0000-0000-000000000004",
                "code": "asian_handicap",
                "name": "Asian Handicap",
                "description": "Handicap market using the line_value market parameter.",
                "is_active": True,
            },
            {
                "id": "10000000-0000-0000-0000-000000000005",
                "code": "handicap",
                "name": "Handicap",
                "description": "Generic handicap market using the line_value market parameter.",
                "is_active": True,
            },
            {
                "id": "10000000-0000-0000-0000-000000000006",
                "code": "over_under",
                "name": "Over/Under",
                "description": "Total market using the line_value market parameter.",
                "is_active": True,
            },
            {
                "id": "10000000-0000-0000-0000-000000000007",
                "code": "both_teams_to_score",
                "name": "Both Teams To Score",
                "description": "Yes/no market for both teams scoring.",
                "is_active": True,
            },
        ],
    )
    op.execute(
        "UPDATE market_data_market_types "
        'SET parameter_schema = \'{"line_value": "decimal"}\'::jsonb '
        "WHERE code IN ('asian_handicap', 'handicap', 'over_under')"
    )

    market_status_table = sa.table(
        "market_data_market_statuses",
        sa.column("id", UUID),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_terminal", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    op.bulk_insert(
        market_status_table,
        [
            {
                "id": "20000000-0000-0000-0000-000000000001",
                "code": "open",
                "name": "Open",
                "description": "Market is accepting or displaying active prices.",
                "is_terminal": False,
                "sort_order": 0,
            },
            {
                "id": "20000000-0000-0000-0000-000000000002",
                "code": "suspended",
                "name": "Suspended",
                "description": "Market is temporarily unavailable.",
                "is_terminal": False,
                "sort_order": 10,
            },
            {
                "id": "20000000-0000-0000-0000-000000000003",
                "code": "closed",
                "name": "Closed",
                "description": "Market is closed and its latest prices are closing odds.",
                "is_terminal": True,
                "sort_order": 20,
            },
            {
                "id": "20000000-0000-0000-0000-000000000004",
                "code": "settled",
                "name": "Settled",
                "description": "Market is settled after the fixture outcome is known.",
                "is_terminal": True,
                "sort_order": 30,
            },
        ],
    )

    op.create_table(
        "market_data_odds_ingestion_runs",
        *audit_columns(),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("status", odds_ingestion_run_status, nullable=False),
        sa.Column(
            "started_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("completed_at", TIMESTAMP, nullable=True),
        sa.Column("received_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("snapshots_created_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("snapshots_ignored_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("movements_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.CheckConstraint("received_count >= 0", name="ck_market_data_odds_runs_received_count"),
        sa.CheckConstraint(
            "snapshots_created_count >= 0", name="ck_market_data_odds_runs_created_count"
        ),
        sa.CheckConstraint(
            "snapshots_ignored_count >= 0", name="ck_market_data_odds_runs_ignored_count"
        ),
        sa.CheckConstraint("movements_count >= 0", name="ck_market_data_odds_runs_movements_count"),
        sa.CheckConstraint("failed_count >= 0", name="ck_market_data_odds_runs_failed_count"),
    )
    op.create_index(
        "ix_market_data_odds_ingestion_runs_provider_name",
        "market_data_odds_ingestion_runs",
        ["provider_name"],
    )
    op.create_index(
        "ix_market_data_odds_ingestion_runs_status",
        "market_data_odds_ingestion_runs",
        ["status"],
    )
    op.create_index(
        "ix_market_data_odds_runs_provider_started",
        "market_data_odds_ingestion_runs",
        ["provider_name", "started_at"],
    )

    op.create_table(
        "market_data_raw_odds_payloads",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("fixture_provider_name", sa.String(length=64), nullable=True),
        sa.Column("provider_fixture_id", sa.String(length=128), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("validation_status", raw_odds_payload_status, nullable=False),
        sa.Column("validation_errors", JSONB, nullable=True),
        sa.Column(
            "ingested_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("processed_at", TIMESTAMP, nullable=True),
        sa.Column("canonical_fixture_id", UUID, nullable=True),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["market_data_odds_ingestion_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["canonical_fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "provider_name",
            "idempotency_key",
            name="uq_market_data_raw_odds_payloads_provider_key",
        ),
    )
    op.create_index(
        "ix_market_data_raw_odds_payloads_ingestion_run_id",
        "market_data_raw_odds_payloads",
        ["ingestion_run_id"],
    )
    op.create_index(
        "ix_market_data_raw_odds_payloads_provider_name",
        "market_data_raw_odds_payloads",
        ["provider_name"],
    )
    op.create_index(
        "ix_market_data_raw_odds_payloads_validation_status",
        "market_data_raw_odds_payloads",
        ["validation_status"],
    )
    op.create_index(
        "ix_market_data_raw_odds_payloads_canonical_fixture_id",
        "market_data_raw_odds_payloads",
        ["canonical_fixture_id"],
    )
    op.create_index(
        "ix_market_data_raw_odds_payloads_provider_fixture",
        "market_data_raw_odds_payloads",
        ["provider_name", "provider_fixture_id"],
    )
    op.create_index(
        "ix_market_data_raw_odds_payloads_checksum",
        "market_data_raw_odds_payloads",
        ["checksum"],
    )

    op.create_table(
        "market_data_provider_mappings",
        *audit_columns(),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("entity_type", provider_entity_type, nullable=False),
        sa.Column("provider_entity_id", sa.String(length=128), nullable=False),
        sa.Column("canonical_entity_id", UUID, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("removed_at", TIMESTAMP, nullable=True),
        sa.Column(
            "first_seen_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "last_seen_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.UniqueConstraint(
            "provider_name",
            "entity_type",
            "provider_entity_id",
            name="uq_market_data_provider_mappings_provider_entity",
        ),
    )
    op.create_index(
        "ix_market_data_provider_mappings_canonical",
        "market_data_provider_mappings",
        ["entity_type", "canonical_entity_id"],
    )

    op.create_table(
        "market_data_markets",
        *audit_columns(),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_type_id", UUID, nullable=False),
        sa.Column("market_status_id", UUID, nullable=False),
        sa.Column("period_code", sa.String(length=32), server_default="full_time", nullable=False),
        sa.Column("line_value", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("line_key", sa.String(length=32), server_default="none", nullable=False),
        sa.Column("attributes", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "status_observed_at",
            TIMESTAMP,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(period_code) >= 1", name="ck_market_data_markets_period_code"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["market_type_id"], ["market_data_market_types.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["market_status_id"], ["market_data_market_statuses.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "market_type_id",
            "period_code",
            "line_key",
            name="uq_market_data_markets_fixture_type_period_line",
        ),
    )
    op.create_index("ix_market_data_markets_fixture_id", "market_data_markets", ["fixture_id"])
    op.create_index(
        "ix_market_data_markets_market_type_id", "market_data_markets", ["market_type_id"]
    )
    op.create_index(
        "ix_market_data_markets_market_status_id", "market_data_markets", ["market_status_id"]
    )
    op.create_index(
        "ix_market_data_markets_status_observed_at", "market_data_markets", ["status_observed_at"]
    )
    op.create_index(
        "ix_market_data_markets_fixture_status",
        "market_data_markets",
        ["fixture_id", "market_status_id"],
    )

    op.create_table(
        "market_data_selections",
        *audit_columns(),
        sa.Column("market_id", UUID, nullable=False),
        sa.Column("selection_key", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("removed_at", TIMESTAMP, nullable=True),
        sa.Column("attributes", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["market_data_markets.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "market_id", "selection_key", name="uq_market_data_selections_market_key"
        ),
    )
    op.create_index("ix_market_data_selections_market_id", "market_data_selections", ["market_id"])
    op.create_index(
        "ix_market_data_selections_market_active",
        "market_data_selections",
        ["market_id", "is_active"],
    )

    op.create_table(
        "market_data_odds_snapshots",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("bookmaker_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_id", UUID, nullable=False),
        sa.Column("selection_id", UUID, nullable=False),
        sa.Column("decimal_odds", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("implied_probability", sa.Numeric(precision=12, scale=8), nullable=False),
        sa.Column("observed_at", TIMESTAMP, nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.CheckConstraint("decimal_odds > 1", name="ck_market_data_odds_snapshots_decimal_odds"),
        sa.CheckConstraint(
            "implied_probability > 0 AND implied_probability < 1",
            name="ck_market_data_odds_snapshots_implied_probability",
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["market_data_odds_ingestion_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["market_data_raw_odds_payloads.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["bookmaker_id"], ["market_data_bookmakers.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["market_id"], ["market_data_markets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["market_data_selections.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "provider_name",
            "bookmaker_id",
            "selection_id",
            "observed_at",
            "checksum",
            name="uq_market_data_odds_snapshots_observation",
        ),
    )
    for index_name, columns in (
        ("ix_market_data_odds_snapshots_ingestion_run_id", ["ingestion_run_id"]),
        ("ix_market_data_odds_snapshots_raw_payload_id", ["raw_payload_id"]),
        ("ix_market_data_odds_snapshots_provider_name", ["provider_name"]),
        ("ix_market_data_odds_snapshots_bookmaker_id", ["bookmaker_id"]),
        ("ix_market_data_odds_snapshots_fixture_id", ["fixture_id"]),
        ("ix_market_data_odds_snapshots_market_id", ["market_id"]),
        ("ix_market_data_odds_snapshots_selection_id", ["selection_id"]),
        ("ix_market_data_odds_snapshots_observed_at", ["observed_at"]),
        (
            "ix_market_data_odds_snapshots_selection_observed",
            ["selection_id", "observed_at"],
        ),
        (
            "ix_market_data_odds_snapshots_fixture_market_observed",
            ["fixture_id", "market_id", "observed_at"],
        ),
    ):
        op.create_index(index_name, "market_data_odds_snapshots", columns)

    op.create_table(
        "market_data_odds_movements",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("bookmaker_id", UUID, nullable=False),
        sa.Column("market_id", UUID, nullable=False),
        sa.Column("selection_id", UUID, nullable=True),
        sa.Column("previous_snapshot_id", UUID, nullable=True),
        sa.Column("current_snapshot_id", UUID, nullable=True),
        sa.Column("movement_type", odds_movement_type, nullable=False),
        sa.Column("previous_decimal_odds", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("current_decimal_odds", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("delta_decimal_odds", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("observed_at", TIMESTAMP, nullable=False),
        sa.Column("details", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["market_data_odds_ingestion_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["market_data_raw_odds_payloads.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["bookmaker_id"], ["market_data_bookmakers.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["market_id"], ["market_data_markets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["selection_id"], ["market_data_selections.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["previous_snapshot_id"], ["market_data_odds_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["current_snapshot_id"], ["market_data_odds_snapshots.id"], ondelete="RESTRICT"
        ),
    )
    for index_name, columns in (
        ("ix_market_data_odds_movements_ingestion_run_id", ["ingestion_run_id"]),
        ("ix_market_data_odds_movements_raw_payload_id", ["raw_payload_id"]),
        ("ix_market_data_odds_movements_bookmaker_id", ["bookmaker_id"]),
        ("ix_market_data_odds_movements_market_id", ["market_id"]),
        ("ix_market_data_odds_movements_selection_id", ["selection_id"]),
        ("ix_market_data_odds_movements_movement_type", ["movement_type"]),
        ("ix_market_data_odds_movements_observed_at", ["observed_at"]),
        ("ix_market_data_odds_movements_market_observed", ["market_id", "observed_at"]),
        ("ix_market_data_odds_movements_selection_observed", ["selection_id", "observed_at"]),
    ):
        op.create_index(index_name, "market_data_odds_movements", columns)

    op.create_table(
        "market_data_odds_audit",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=True),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_fixture_id", sa.String(length=128), nullable=True),
        sa.Column("outcome", odds_audit_outcome, nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("changes", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("snapshots_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("snapshots_ignored", sa.Integer(), server_default="0", nullable=False),
        sa.Column("movements_detected", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "occurred_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["market_data_odds_ingestion_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["market_data_raw_odds_payloads.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
    )
    for index_name, columns in (
        ("ix_market_data_odds_audit_ingestion_run_id", ["ingestion_run_id"]),
        ("ix_market_data_odds_audit_raw_payload_id", ["raw_payload_id"]),
        ("ix_market_data_odds_audit_fixture_id", ["fixture_id"]),
        ("ix_market_data_odds_audit_provider_name", ["provider_name"]),
        ("ix_market_data_odds_audit_outcome", ["outcome"]),
        ("ix_market_data_odds_audit_provider_occurred", ["provider_name", "occurred_at"]),
        ("ix_market_data_odds_audit_fixture_occurred", ["fixture_id", "occurred_at"]),
    ):
        op.create_index(index_name, "market_data_odds_audit", columns)

    op.create_table(
        "market_data_outbox_events",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("event_type", market_data_event_type, nullable=False),
        sa.Column("event_key", sa.String(length=160), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column(
            "occurred_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("published_at", TIMESTAMP, nullable=True),
        sa.Column("delivery_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["market_data_odds_ingestion_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["market_data_raw_odds_payloads.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("event_key", name="uq_market_data_outbox_events_event_key"),
    )
    for index_name, columns in (
        ("ix_market_data_outbox_events_ingestion_run_id", ["ingestion_run_id"]),
        ("ix_market_data_outbox_events_raw_payload_id", ["raw_payload_id"]),
        ("ix_market_data_outbox_events_event_type", ["event_type"]),
        ("ix_market_data_outbox_events_unpublished", ["published_at", "occurred_at"]),
    ):
        op.create_index(index_name, "market_data_outbox_events", columns)


def downgrade() -> None:
    """Remove Market Data tables before dropping their PostgreSQL controlled-vocabulary types."""
    op.drop_table("market_data_outbox_events")
    op.drop_table("market_data_odds_audit")
    op.drop_table("market_data_odds_movements")
    op.drop_table("market_data_odds_snapshots")
    op.drop_table("market_data_selections")
    op.drop_table("market_data_markets")
    op.drop_table("market_data_provider_mappings")
    op.drop_table("market_data_raw_odds_payloads")
    op.drop_table("market_data_odds_ingestion_runs")
    op.drop_table("market_data_market_statuses")
    op.drop_table("market_data_market_types")
    op.drop_table("market_data_bookmakers")

    bind = op.get_bind()
    market_data_event_type.drop(bind, checkfirst=True)
    odds_movement_type.drop(bind, checkfirst=True)
    provider_entity_type.drop(bind, checkfirst=True)
    odds_audit_outcome.drop(bind, checkfirst=True)
    raw_odds_payload_status.drop(bind, checkfirst=True)
    odds_ingestion_run_status.drop(bind, checkfirst=True)
