"""Async repositories for immutable Feature Store metadata and feature-value history."""

from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.exceptions import FeatureSetVersionConflictError
from app.modules.feature_store.models import (
    FeatureDefinition,
    FeatureGenerationRun,
    FeatureLineage,
    FeatureSet,
    FeatureSetVersion,
    FeatureValidationRecord,
    FeatureValue,
)
from app.modules.feature_store.registry import FeatureSpec
from app.modules.feature_store.schemas import FeatureValueFilters, PaginationParams


class FeatureStoreRepository:
    """Persistence boundary; services never issue ad-hoc SQL against Feature Store tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_feature_set_version(
        self,
        *,
        code: str,
        name: str,
        description: str,
        owner: str,
        version: str,
        generator_version: str,
        definition_checksum: str,
        source_modules: list[str],
        specs: tuple[FeatureSpec, ...],
    ) -> tuple[FeatureSet, FeatureSetVersion, dict[str, FeatureDefinition]]:
        """Create a version once, or prove an existing version is equivalent."""
        feature_set = await self._session.scalar(select(FeatureSet).where(FeatureSet.code == code))
        if feature_set is None:
            feature_set = FeatureSet(code=code, name=name, description=description, owner=owner)
            self._session.add(feature_set)
            await self._session.flush()
        feature_set_version = await self._session.scalar(
            select(FeatureSetVersion).where(
                FeatureSetVersion.feature_set_id == feature_set.id,
                FeatureSetVersion.version == version,
            )
        )
        if feature_set_version is not None:
            if (
                feature_set_version.definition_checksum != definition_checksum
                or feature_set_version.generator_version != generator_version
            ):
                raise FeatureSetVersionConflictError(
                    f"Feature set '{code}' version '{version}' is immutable; use a new version."
                )
        else:
            feature_set_version = FeatureSetVersion(
                feature_set_id=feature_set.id,
                version=version,
                generator_version=generator_version,
                definition_checksum=definition_checksum,
                source_modules=source_modules,
            )
            self._session.add(feature_set_version)
            await self._session.flush()
            for spec in specs:
                definition = asdict(spec)
                definition["source_modules"] = list(spec.source_modules)
                definition["dependencies"] = list(spec.dependencies)
                self._session.add(
                    FeatureDefinition(
                        feature_set_version_id=feature_set_version.id,
                        **definition,
                    )
                )
            await self._session.flush()
        definitions = list(
            (
                await self._session.scalars(
                    select(FeatureDefinition).where(
                        FeatureDefinition.feature_set_version_id == feature_set_version.id
                    )
                )
            ).all()
        )
        return feature_set, feature_set_version, {item.feature_id: item for item in definitions}

    async def existing_run(self, idempotency_key: str) -> FeatureGenerationRun | None:
        """Find an earlier exact input snapshot before writing any duplicate feature values."""
        return await self._session.scalar(
            select(FeatureGenerationRun).where(
                FeatureGenerationRun.idempotency_key == idempotency_key
            )
        )

    async def create_run(self, run: FeatureGenerationRun) -> FeatureGenerationRun:
        """Persist and flush a pending run so its immutable child rows can reference it."""
        self._session.add(run)
        await self._session.flush()
        return run

    async def page_values(
        self, filters: FeatureValueFilters, pagination: PaginationParams
    ) -> tuple[list[FeatureValue], int]:
        """Retrieve immutable values through indexed canonical-subject and version filters."""
        statement = (
            select(FeatureValue)
            .join(FeatureDefinition, FeatureDefinition.id == FeatureValue.feature_definition_id)
            .join(
                FeatureSetVersion, FeatureSetVersion.id == FeatureDefinition.feature_set_version_id
            )
            .join(FeatureSet, FeatureSet.id == FeatureSetVersion.feature_set_id)
        )
        statement = self._apply_value_filters(statement, filters)
        total = await self._session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        rows = list(
            (
                await self._session.scalars(
                    statement.order_by(
                        FeatureValue.observed_at.desc(), FeatureValue.created_at.desc()
                    )
                    .offset(pagination.offset)
                    .limit(pagination.limit)
                )
            ).all()
        )
        return rows, total or 0

    async def feature_sets(self, pagination: PaginationParams) -> tuple[list[FeatureSet], int]:
        """List stable feature-set identities in deterministic code order."""
        statement = select(FeatureSet).order_by(FeatureSet.code)
        total = await self._session.scalar(select(func.count()).select_from(FeatureSet)) or 0
        rows = list(
            (
                await self._session.scalars(
                    statement.offset(pagination.offset).limit(pagination.limit)
                )
            ).all()
        )
        return rows, total

    async def versions(self, code: str) -> list[FeatureSetVersion]:
        """List immutable versions for one feature set, newest registry snapshot first."""
        return list(
            (
                await self._session.scalars(
                    select(FeatureSetVersion)
                    .join(FeatureSet, FeatureSet.id == FeatureSetVersion.feature_set_id)
                    .where(FeatureSet.code == code)
                    .order_by(FeatureSetVersion.created_at.desc())
                )
            ).all()
        )

    async def definitions(self, code: str, version: str) -> list[FeatureDefinition]:
        """List immutable definitions for a selected Feature Set version."""
        statement = (
            select(FeatureDefinition)
            .join(
                FeatureSetVersion,
                FeatureSetVersion.id == FeatureDefinition.feature_set_version_id,
            )
            .join(FeatureSet, FeatureSet.id == FeatureSetVersion.feature_set_id)
            .where(FeatureSet.code == code, FeatureSetVersion.version == version)
            .order_by(FeatureDefinition.feature_id)
        )
        return list((await self._session.scalars(statement)).all())

    async def lineage(self, feature_value_id: UUID) -> list[FeatureLineage]:
        """Return source evidence in stable chronological order for explainability consumers."""
        return list(
            (
                await self._session.scalars(
                    select(FeatureLineage)
                    .where(FeatureLineage.feature_value_id == feature_value_id)
                    .order_by(FeatureLineage.created_at, FeatureLineage.id)
                )
            ).all()
        )

    async def validation(self, feature_value_id: UUID) -> list[FeatureValidationRecord]:
        """Return persisted validation evidence for an immutable generated feature value."""
        return list(
            (
                await self._session.scalars(
                    select(FeatureValidationRecord)
                    .where(FeatureValidationRecord.feature_value_id == feature_value_id)
                    .order_by(FeatureValidationRecord.created_at, FeatureValidationRecord.id)
                )
            ).all()
        )

    @staticmethod
    def _apply_value_filters(
        statement: Select[tuple[FeatureValue]], filters: FeatureValueFilters
    ) -> Select[tuple[FeatureValue]]:
        if filters.fixture_id:
            statement = statement.where(FeatureValue.fixture_id == filters.fixture_id)
        if filters.team_id:
            statement = statement.where(FeatureValue.team_id == filters.team_id)
        if filters.player_id:
            statement = statement.where(FeatureValue.player_id == filters.player_id)
        if filters.competition_id:
            statement = statement.where(FeatureValue.competition_id == filters.competition_id)
        if filters.season_id:
            statement = statement.where(FeatureValue.season_id == filters.season_id)
        if filters.feature_set_code:
            statement = statement.where(FeatureSet.code == filters.feature_set_code)
        if filters.feature_set_version:
            statement = statement.where(FeatureSetVersion.version == filters.feature_set_version)
        if filters.feature_id:
            statement = statement.where(FeatureDefinition.feature_id == filters.feature_id)
        if filters.observed_after:
            statement = statement.where(FeatureValue.observed_at >= filters.observed_after)
        if filters.observed_before:
            statement = statement.where(FeatureValue.observed_at <= filters.observed_before)
        return statement
