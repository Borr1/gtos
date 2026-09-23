# Expanded OOS Frozen Candidate Registry

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Frozen before expanded outcome runs: `True`

## Trial Accounting

| Metric | Value |
| --- | --- |
| frozen_strategy_or_comparator_rows | 6 |
| path_management_candidates | 3 |
| orderflow_diagnostics | 1 |
| simulation_comparators | 1 |
| failed_or_parked_routes_excluded | 6 |
| opened_outcome_slices_at_registration | 0 |
| rule_tuning_allowed_after_outcome_open | False |

## Frozen Candidates

| ID | Rule | Class | Status | Variant/Hypothesis | Primary label requirements |
| --- | --- | --- | --- | --- | --- |
| CAND-001-J46-J49-LIVE-BASELINE | Current live/J46-J49 baseline stack | champion_baseline | FROZEN_FOR_COMPARISON |  | actual_broker_r when available; path_synthetic_r separated when replayed offline; fill_no_fill separated for pending-limit rows |
| CAND-002-V2-OB-BOUNDARY | V2 OB-boundary path candidate | path_management_candidate | FROZEN_DISCOVERY_CANDIDATE | STRUCT_OB_BOUNDARY_V2 | resolved OB-boundary/J46 pair; cost_key; lower_tf_available |
| CAND-003-V2-FVG-PATH | V2 FVG path candidate | path_management_candidate | FROZEN_DISCOVERY_CANDIDATE | STRUCT_FVG_MID_EDGE_V2 | resolved FVG/J46 pair; sequence/fired flags; cost_key |
| CAND-004-V3-FVG-ONLY-RESCUE | V3 FVG-only rescue risk-bank candidate | reentry_path_management_candidate | FROZEN_DISCOVERY_CANDIDATE | V3_FVG_ONLY_RESCUE_RISK_BANK | FVG fires; OB lock absent; FVG net R exceeds J46 and OB in source event; risk-bank invariant preserved; same-bar ambiguity bounded, not guessed |
| CAND-005-NAS100-DEPTH-THINNESS | NAS100 depth/thinness orderflow diagnostic | orderflow_diagnostic_not_filter | REGISTERED_DIAGNOSTIC_NOT_PROMOTABLE | OF-NAS100-DEPTH-ADVERSE-SELECTION-V1 | actual_broker_r when available; synthetic/path labels separately flagged; depth source and schema recorded; leave-one-date stability checked |
| CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR | Current full-stack/S79/side-aware risk baseline | simulation_comparator_only | FROZEN_FOR_SIMULATION_COMPARISON_ONLY |  | simulation row must identify risk model separately from signal candidate; no live risk replacement in this goal |

## Excluded Routes

| Route | Status | Reason |
| --- | --- | --- |
| Composite structural selector as broad policy | EXCLUDED_EXCEPT_NEGATIVE_CONTROL | prior confluence deep dive classifies broad Composite as overlock/global underperformer |
| K54 v3/v4 same-cohort architecture iteration | EXCLUDED | current cohort architecture iteration is closed without new source-balanced labels |
| Portfolio-wide vol scaling | EXCLUDED | already failed Lane 6 tail triage |
| V3 OB-lock and FVG-then-OB underperforming variants | EXCLUDED_EXCEPT_DIAGNOSTIC_CONTEXT | not first-line expanded OOS strategy candidates in current owner prompt |
| Component 3B debate | PARKED | owner parked due to extra AI/API cost |
| Prompt cascade rebuild, Reflexion/adaptive loop, live AI behavior changes | EXCLUDED_APPROVAL_REQUIRED | behavior/API-cost changes require explicit separate approval |

## Label Policy

- `actual_broker_r`: highest-priority outcome when present; never overwritten by synthetic replay
- `path_synthetic_r`: offline replay label only
- `fill_no_fill`: separate from R because unfilled/expired/cancelled pending intents are not losing broker trades by default
- `futures_proxy_transfer`: mechanism/orderflow evidence, not MT5 broker execution truth
- `cross_instrument_transfer`: expansion discovery, not validation of original instrument

## Candidate Artifact Anchors

### CAND-001-J46-J49-LIVE-BASELINE

- `research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md`
- `research/ml_program/audit/dsr_retroactive_sweep.md`
- `src/components/permissions.py`
- `src/components/orchestrator.py`

### CAND-002-V2-OB-BOUNDARY

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_OB_BOUNDARY_VALIDATION_SPEC_V1.json`
- `scripts/evaluate_raw_ohlc_path_scaling_v2b_prospective.py`
- `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/`

### CAND-003-V2-FVG-PATH

- `scripts/analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json`

### CAND-004-V3-FVG-ONLY-RESCUE

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_PRE_REGISTERED_VARIANTS_2026-05-03.json`
- `scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py`

### CAND-005-NAS100-DEPTH-THINNESS

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_HYPOTHESIS_CONTRACT_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json`
- `scripts/analyze_orderflow_nas100_cached_feature_forensics.py`

### CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR

- `research/ml_program/phase_2/position_mgmt/combined_mc_j46_s79_side_aware.md`
- `research/ml_program/audit/dsr_retroactive_sweep.md`
- `config/agent_config.yaml`
- `config/profiles/redacted_account.yaml`
