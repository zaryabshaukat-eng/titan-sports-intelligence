"""Deterministic offline generation service for immutable canonical-data Feature Store values."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.enums import GenerationStatus, ValidationStatus
from app.modules.feature_store.exceptions import FeatureGenerationResolutionError
from app.modules.feature_store.generator import (
    CanonicalFeatureSourceReader,
    FeatureGenerationContext,
    SourceReference,
)
from app.modules.feature_store.lineage import build_lineage_rows
from app.modules.feature_store.metadata import feature_set_checksum, fingerprint
from app.modules.feature_store.models import (
    FeatureGenerationRun,
    FeatureValidationRecord,
    FeatureValue,
)
from app.modules.feature_store.registry import FeatureGeneratorRegistry
from app.modules.feature_store.repositories import FeatureStoreRepository
from app.modules.feature_store.schemas import FeatureGenerationRequest, FeatureGenerationResult
from app.modules.feature_store.validation import validate_feature

DEFAULT_FEATURE_SET_CODE = "core_fixture"
DEFAULT_FEATURE_SET_NAME = "Core Fixture Features"
DEFAULT_FEATURE_SET_DESCRIPTION = (
    "Deterministic fixture, team-temporal, market, and statistics features "
    "from canonical TITAN data."
)
DEFAULT_FEATURE_SET_OWNER = "sports-intelligence"
DEFAULT_GENERATOR_VERSION = "1.0.0"


class FeatureGenerationService:
    """Coordinates registry initialization, canonical reads, validation, lineage, and append-only writes."""  # noqa: E501

    def __init__(self, session: AsyncSession, registry: FeatureGeneratorRegistry) -> None:
        self._session = session
        self._registry = registry
        self._repository = FeatureStoreRepository(session)

    async def generate(self, request: FeatureGenerationRequest) -> FeatureGenerationResult:
        """Generate or reuse one Feature Set snapshot for a fixture at a historical cutoff."""
        specs = self._registry.specs
        definitions_metadata = [asdict(spec) for spec in specs]
        definition_checksum = feature_set_checksum(definitions_metadata)
        _, set_version, definitions = await self._repository.ensure_feature_set_version(
            code=request.feature_set_code,
            name=DEFAULT_FEATURE_SET_NAME,
            description=DEFAULT_FEATURE_SET_DESCRIPTION,
            owner=DEFAULT_FEATURE_SET_OWNER,
            version=request.feature_set_version,
            generator_version=DEFAULT_GENERATOR_VERSION,
            definition_checksum=definition_checksum,
            source_modules=sorted({source for spec in specs for source in spec.source_modules}),
            specs=specs,
        )
        source_reader = CanonicalFeatureSourceReader(self._session)
        fixture = await source_reader.fixture_context(request.fixture_id)
        if fixture is None:
            raise FeatureGenerationResolutionError(
                f"Canonical fixture '{request.fixture_id}' does not exist."
            )
        context = FeatureGenerationContext(
            fixture=fixture,
            as_of=request.as_of,
            source_reader=source_reader,
        )
        generated = [
            result
            for generator in self._registry.generators
            for result in await generator.generate(context)
        ]
        target_fixture_source = SourceReference(
            source_module="sports",
            source_entity_type="fixture",
            source_record_id=fixture.fixture_id,
            observed_at=fixture.scheduled_start_at,
            source_fingerprint=fingerprint(
                {
                    "id": fixture.fixture_id,
                    "scheduled_start_at": fixture.scheduled_start_at,
                }
            ),
        )
        generated = [
            replace(
                item,
                sources=(
                    item.sources
                    if any(
                        source.source_module == "sports"
                        and source.source_entity_type == "fixture"
                        and source.source_record_id == fixture.fixture_id
                        for source in item.sources
                    )
                    else (*item.sources, target_fixture_source)
                ),
            )
            for item in generated
        ]
        input_fingerprint = fingerprint(
            {
                "definition_checksum": definition_checksum,
                "fixture_id": request.fixture_id,
                "as_of": request.as_of,
                "sources": [
                    {
                        "feature_id": item.feature_id,
                        "value": item.value,
                        "sources": [
                            {
                                "module": source.source_module,
                                "type": source.source_entity_type,
                                "id": source.source_record_id,
                                "fingerprint": source.source_fingerprint,
                            }
                            for source in item.sources
                        ],
                    }
                    for item in generated
                ],
            }
        )
        idempotency_key = fingerprint(
            {
                "feature_set_version": set_version.id,
                "fixture_id": request.fixture_id,
                "as_of": request.as_of,
                "input_fingerprint": input_fingerprint,
            }
        )
        existing = await self._repository.existing_run(idempotency_key)
        if existing is not None:
            return FeatureGenerationResult(
                generation_run_id=existing.id,
                status=existing.status,
                generated_count=existing.generated_count,
                reused_existing_run=True,
            )
        run = await self._repository.create_run(
            FeatureGenerationRun(
                feature_set_version_id=set_version.id,
                fixture_id=request.fixture_id,
                as_of=request.as_of,
                generator_version=DEFAULT_GENERATOR_VERSION,
                input_fingerprint=input_fingerprint,
                idempotency_key=idempotency_key,
                status=GenerationStatus.RUNNING,
            )
        )
        invalid = False
        for result in generated:
            definition = definitions.get(result.feature_id)
            if definition is None:
                invalid = True
                continue
            spec = next(spec for spec in specs if spec.feature_id == result.feature_id)
            findings = validate_feature(
                spec=spec,
                feature=result,
                as_of=request.as_of,
                generator_version=DEFAULT_GENERATOR_VERSION,
            )
            if any(finding.status is ValidationStatus.FAILED for finding in findings):
                invalid = True
                for finding in findings:
                    self._session.add(
                        FeatureValidationRecord(
                            generation_run_id=run.id,
                            feature_definition_id=definition.id,
                            rule_name=finding.rule_name,
                            status=finding.status,
                            message=finding.message,
                        )
                    )
        if invalid:
            run.status = GenerationStatus.FAILED
            run.failure_reason = "feature validation failed"
            run.completed_at = request.as_of
            return FeatureGenerationResult(
                generation_run_id=run.id,
                status=run.status,
                generated_count=0,
            )

        for result in generated:
            definition = definitions[result.feature_id]
            spec = next(spec for spec in specs if spec.feature_id == result.feature_id)
            numeric_value = _numeric_value(result.value)
            feature_value = FeatureValue(
                generation_run_id=run.id,
                feature_definition_id=definition.id,
                fixture_id=result.fixture_id,
                team_id=result.team_id,
                player_id=result.player_id,
                competition_id=result.competition_id,
                season_id=result.season_id,
                value=_json_value(result.value),
                numeric_value=numeric_value,
                quality_score=result.quality_score,
                calculated_at=request.as_of,
                observed_at=request.as_of,
                valid_from=request.as_of,
                valid_until=(
                    request.as_of + timedelta(seconds=spec.validity_window_seconds)
                    if spec.validity_window_seconds is not None
                    else None
                ),
            )
            self._session.add(feature_value)
            await self._session.flush()
            self._session.add_all(
                build_lineage_rows(
                    feature_value_id=feature_value.id,
                    sources=result.sources,
                    calculation_logic=spec.calculation_logic,
                    generator_version=DEFAULT_GENERATOR_VERSION,
                )
            )
            for finding in validate_feature(
                spec=spec,
                feature=result,
                as_of=request.as_of,
                generator_version=DEFAULT_GENERATOR_VERSION,
            ):
                self._session.add(
                    FeatureValidationRecord(
                        generation_run_id=run.id,
                        feature_definition_id=definition.id,
                        feature_value_id=feature_value.id,
                        rule_name=finding.rule_name,
                        status=finding.status,
                        message=finding.message,
                    )
                )
        run.generated_count = len(generated)
        run.status = GenerationStatus.COMPLETED
        run.completed_at = request.as_of
        return FeatureGenerationResult(
            generation_run_id=run.id,
            status=run.status,
            generated_count=run.generated_count,
        )


def _numeric_value(value: object | None) -> Decimal | None:
    """Persist exact numeric values separately from JSON for efficient numeric consumers."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    return Decimal(str(value))


def _json_value(value: object | None) -> object | None:
    """Convert Decimal results into JSON-safe scalar values while retaining exact numeric_value."""
    return float(value) if isinstance(value, Decimal) else value
