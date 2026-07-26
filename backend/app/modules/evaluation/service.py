from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.backtest import no_future_leakage
from app.modules.evaluation.enums import BacktestRunStatus, BacktestValidationStatus
from app.modules.evaluation.lineage import build, fingerprint
from app.modules.evaluation.metrics import calculate
from app.modules.evaluation.models import (
    BacktestMetric,
    BacktestResult,
    BacktestRun,
    BacktestValidationRecord,
)
from app.modules.evaluation.registry import ScenarioRegistry
from app.modules.evaluation.repositories import EvaluationRepository
from app.modules.evaluation.schemas import BacktestRunCreate
from app.modules.evaluation.validation import validate, validate_scenario_parameters


class BacktestService:
    def __init__(self, s: AsyncSession) -> None:
        self._session = s
        self._repository = EvaluationRepository(s)

    async def create(self, request: BacktestRunCreate) -> BacktestRun:
        validate_scenario_parameters(request.scenario, request.parameters)
        prob = await self._repository.probability(request.probability_run_id)
        con = await self._repository.consensus(request.consensus_run_id)
        risk = await self._repository.risk(request.risk_run_id)
        explain = await self._repository.explainability(request.explainability_run_id)
        if not all((prob, con, risk, explain)):
            raise ValueError("All pipeline artifacts are required.")
        checksum = fingerprint(
            {
                "prob": prob.input_checksum,
                "consensus": con.input_checksum,
                "risk": risk.input_checksum,
                "explain": explain.input_checksum,
                "scenario": request.scenario,
                "parameters": request.parameters,
                "seed": request.random_seed,
                "outcomes": request.outcomes,
            }
        )
        key = fingerprint({"code": request.run_code, "input": checksum})
        if old := await self._repository.existing(key):
            return old
        if await self._repository.by_code(request.run_code):
            raise ValueError("Backtest run code is immutable.")
        output_map = {
            item.id: item
            for item in await self._repository.outputs(
                [x.probability_output_id for x in request.outcomes]
            )
        }
        if len(output_map) != len(request.outcomes):
            raise ValueError("Every requested probability output must exist.")
        if any(item.probability_run_id != prob.id for item in output_map.values()):
            raise ValueError("Every replay output must belong to the requested probability run.")
        fixtures = await self._repository.fixtures(
            [item.fixture_id for item in output_map.values()]
        )
        replayed = []
        leakage = False
        for outcome in request.outcomes:
            output = output_map.get(outcome.probability_output_id)
            fixture = fixtures.get(output.fixture_id) if output else None
            if not fixture or not no_future_leakage(
                output.prediction_timestamp, fixture.scheduled_start_at
            ):
                leakage = True
                continue
            replayed.append((output, outcome.observed_outcome, fixture.scheduled_start_at))
        findings = validate(
            prob,
            con,
            risk,
            explain,
            request.research_experiment_id,
            leakage,
        )
        valid = all(x.status is BacktestValidationStatus.PASSED for x in findings) and bool(
            replayed
        )
        run = await self._repository.create(
            BacktestRun(
                run_code=request.run_code,
                dataset_snapshot_id=prob.dataset_snapshot_id,
                feature_set_version_id=prob.feature_set_version_id,
                research_experiment_id=request.research_experiment_id,
                probability_run_id=prob.id,
                consensus_run_id=con.id,
                risk_run_id=risk.id,
                explainability_run_id=explain.id,
                scenario=request.scenario,
                parameters=request.parameters,
                random_seed=request.random_seed,
                status=BacktestRunStatus.COMPLETED
                if valid
                else BacktestRunStatus.VALIDATION_FAILED,
                input_checksum=checksum,
                idempotency_key=key,
            )
        )
        self._session.add_all(
            [
                BacktestValidationRecord(
                    backtest_run_id=run.id,
                    rule_name=x.rule_name,
                    status=x.status,
                    message=x.message,
                )
                for x in findings
            ]
        )
        self._session.add(build(run, prob))
        if not valid:
            return run
        ordered = sorted(replayed, key=lambda x: x[2])
        selected = (
            ScenarioRegistry().resolve(request.scenario.value).select(ordered, request.parameters)
        )
        if not selected:
            raise ValueError("Scenario selection produced no historical observations.")
        results = [
            BacktestResult(
                backtest_run_id=run.id,
                probability_output_id=o.id,
                fixture_id=o.fixture_id,
                market_type=o.market_type,
                outcome=o.outcome,
                predicted_probability=o.estimated_probability,
                observed_outcome=actual,
                prediction_timestamp=o.prediction_timestamp,
                fixture_start_at=start,
            )
            for o, actual, start in selected
        ]
        self._session.add_all(results)
        metrics, reliability = calculate(results)
        self._session.add(
            BacktestMetric(
                backtest_run_id=run.id,
                sample_count=len(results),
                metrics=metrics,
                reliability=reliability,
            )
        )
        return run
