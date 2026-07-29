import type { IsoDateTime, JsonObject, ResourceId } from "./api";

export interface AuditedRecord {
  id: ResourceId;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
}

export interface League extends AuditedRecord {
  name: string;
  short_name: string | null;
  sport: string;
  country_id: ResourceId | null;
  deleted_at: IsoDateTime | null;
}

export interface Match extends AuditedRecord {
  season_id: ResourceId;
  home_team_id: ResourceId;
  away_team_id: ResourceId;
  fixture_status_id: ResourceId;
  venue_id: ResourceId | null;
  timezone_id: ResourceId | null;
  scheduled_start_at: IsoDateTime;
  scheduled_end_at: IsoDateTime | null;
  round_name: string | null;
  stage_name: string | null;
}

export interface Market extends AuditedRecord {
  fixture_id: ResourceId;
  market_type_id: ResourceId;
  market_status_id: ResourceId;
  period_code: string;
  line_value: number | null;
  line_key: string;
  attributes: JsonObject;
}

export interface OddsSnapshot extends AuditedRecord {
  ingestion_run_id: ResourceId;
  raw_payload_id: ResourceId;
  provider_name: string;
  bookmaker_id: ResourceId;
  fixture_id: ResourceId;
  market_id: ResourceId;
  selection_id: ResourceId;
  decimal_odds: number;
  implied_probability: number;
  observed_at: IsoDateTime;
  checksum: string;
}

export interface DashboardSnapshot {
  generated_at: IsoDateTime;
  metrics: JsonObject;
}

export interface DatasetSnapshot {
  id: ResourceId;
  dataset_code: string;
  version: string;
  name: string;
  description: string;
  owner: string;
  feature_set_version_id: ResourceId;
  selection: JsonObject;
  generator_versions: Record<string, string>;
  source_value_count: number;
  checksum: string;
  created_at: IsoDateTime;
}

export interface Experiment {
  id: ResourceId;
  experiment_code: string;
  name: string;
  description: string;
  owner: string;
  feature_set_version_id: ResourceId;
  dataset_snapshot_id: ResourceId;
  generator_versions: Record<string, string>;
  parameters: JsonObject;
  random_seed: number;
  status: string;
  input_checksum: string;
  created_at: IsoDateTime;
}

export interface Hypothesis {
  id: ResourceId;
  hypothesis_code: string;
  statement: string;
  description: string | null;
  owner: string;
  created_at: IsoDateTime;
}

export interface ProbabilityModel {
  model_identifier: string;
  version: string;
  algorithm: string;
  description: string;
  parameter_schema: JsonObject;
}

export interface ProbabilityRun {
  id: ResourceId;
  run_code: string;
  dataset_snapshot_id: ResourceId;
  feature_set_version_id: ResourceId;
  research_experiment_id: ResourceId;
  model_identifier: string;
  model_version: string;
  calibration_version_id: ResourceId | null;
  market_type: string;
  outcome: string;
  parameters: JsonObject;
  random_seed: number;
  prediction_timestamp: IsoDateTime;
  status: string;
  input_checksum: string;
  created_at: IsoDateTime;
}

export interface ProbabilityOutput {
  id: ResourceId;
  probability_run_id: ResourceId;
  fixture_id: ResourceId;
  market_type: string;
  outcome: string;
  estimated_probability: number;
  confidence_interval_low: number;
  confidence_interval_high: number;
  calibration_version: string | null;
  prediction_timestamp: IsoDateTime;
  support_count: number;
  created_at: IsoDateTime;
}

export interface ConsensusStrategy {
  identifier: string;
  description: string;
  parameter_schema: JsonObject;
}

export interface ConsensusRun {
  id: ResourceId;
  run_code: string;
  feature_set_version_id: ResourceId;
  dataset_snapshot_id: ResourceId;
  strategy: string;
  parameters: JsonObject;
  random_seed: number;
  status: string;
  input_checksum: string;
  created_at: IsoDateTime;
}

export interface ConsensusOutput {
  id: ResourceId;
  consensus_run_id: ResourceId;
  fixture_id: ResourceId;
  market_type: string;
  outcome: string;
  consensus_probability: number;
  confidence_score: number;
  disagreement_score: number;
  agreement_level: string;
  confidence_metrics: JsonObject;
  disagreement_metrics: JsonObject;
  contributor_count: number;
  expected_count: number;
  created_at: IsoDateTime;
}

export interface RiskAnalyzer {
  identifier: string;
  description: string;
}

export interface RiskOutput {
  id: ResourceId;
  risk_run_id: ResourceId;
  fixture_id: ResourceId;
  market_type: string;
  outcome: string;
  overall_risk_score: number;
  uncertainty_score: number;
  stability_score: number;
  calibration_risk: number;
  agreement_risk: number;
  data_quality_risk: number;
  completeness_score: number;
  components: JsonObject;
  created_at: IsoDateTime;
}

export interface Explainer {
  identifier: string;
  description: string;
}

export interface Explanation {
  id: ResourceId;
  explainability_run_id: ResourceId;
  fixture_id: ResourceId;
  market_type: string;
  outcome: string;
  explanation_summary: string;
  confidence: number;
  evidence_completeness: number;
  traceability_score: number;
  coverage_score: number;
  created_at: IsoDateTime;
}

export interface EvaluationScenario {
  identifier: string;
  description: string;
}

export interface BacktestRun {
  id: ResourceId;
  run_code: string;
  dataset_snapshot_id: ResourceId;
  feature_set_version_id: ResourceId;
  research_experiment_id: ResourceId;
  probability_run_id: ResourceId;
  consensus_run_id: ResourceId;
  risk_run_id: ResourceId;
  explainability_run_id: ResourceId;
  scenario: string;
  parameters: JsonObject;
  random_seed: number;
  status: string;
  input_checksum: string;
  created_at: IsoDateTime;
}
