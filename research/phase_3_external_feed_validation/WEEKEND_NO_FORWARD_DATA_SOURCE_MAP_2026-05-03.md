# Weekend No-Forward-Data Source Map

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question Registered Before Work

Which weekend tasks can be executed using only existing local data, cached Databento artifacts, existing raw-OHLC replay outputs, and research-only tooling, while explicitly skipping anything that requires live-market forward rows, active Sierra capture, broad paid data pulls, or live trading behavior changes?

## Preflight Evidence Read

- `.context/LIVE_STATE.md` regenerated at `2026-05-02 15:54:04 UTC`; HEAD at preflight was `8770cc7 docs: add weekend goal handoff`.
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
- `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`
- `research/phase_3_external_feed_validation/PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md`
- `research/phase_3_external_feed_validation/PHASE3_EXECUTION_UPDATE_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_15_2026-05-02.md`
- `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_NQM26_DEPTH_PROBE_2026-05-02.md`

## Current Local Data Inventory

### Raw-OHLC Path Scaling

Existing replay/report anchors:

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURE_CONFLUENCE_AUDIT_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURE_CONFLUENCE_AUDIT_2026-05-02.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_SELECTOR_FORENSICS_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_ARCHITECTURE_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_RISK_ACCOUNTING_2026-05-02.md`

Frozen event logs and replay outputs:

- `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260502T072836Z.jsonl`
- `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_20260502T072840Z.json`
- earlier V2 event-log snapshots under the same directory remain usable only if explicitly pinned.

Reusable scripts/tests already present:

- `scripts/analyze_raw_ohlc_path_scaling_v2_confluence.py`
- `scripts/analyze_raw_ohlc_path_scaling_v2_selector_forensics.py`
- `scripts/evaluate_raw_ohlc_path_scaling_v2b_prospective.py`
- `scripts/run_raw_ohlc_path_scaling_v2_levels.py`
- `tests/test_raw_ohlc_path_scaling_v2_confluence.py`
- `tests/test_raw_ohlc_path_scaling_v2_selector_forensics.py`
- `tests/test_raw_ohlc_path_scaling_v2b_prospective.py`
- `tests/test_raw_ohlc_path_scaling_v2_levels.py`

### Cached Orderflow And Proxy Mapping

Existing orderflow/report anchors:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_VALIDATION_SYNTHESIS_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_AGGRESSIVE_PROXY_EXPANDED_MBP10_FEATURES_2026-05-02.json`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_AGGRESSIVE_SURGICAL_TRADES_OUTCOME_JOIN_2026-05-02.json`
- `research/databento_orderflow_capture_2026-05-02/USDJPY_6J_INVERSE_RETURN_FOLLOWUP_VALIDATION_2026-05-02.json`
- `research/databento_orderflow_capture_2026-05-02/FUTURES_CFD_PROXY_EXPANSION_AUDIT_2026-05-02.json`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_15_2026-05-02.md`

Reusable scripts/tests already present:

- `scripts/analyze_orderflow_mbo_nas100_features.py`
- `scripts/analyze_orderflow_depth_mbp10_features.py`
- `scripts/analyze_orderflow_event_features.py`
- `scripts/audit_orderflow_proxy_mapping_priorities.py`
- `scripts/audit_futures_proxy_expansion_validation.py`
- `tests/test_orderflow_mbo_nas100_features.py`
- `tests/test_orderflow_depth_mbp10_features.py`
- `tests/test_orderflow_proxy_mapping_priorities.py`
- `tests/test_futures_proxy_expansion_audit.py`

### Sierra Chart Parser Proof

Existing Sierra anchors:

- `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_NQM26_DEPTH_PROBE_2026-05-02.md`
- `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_DEPTH_PARSER_SPEC_2026-05-02.md`
- `research/sierrachart_data_source_research_2026-05-02/tools/sierra_depth_probe.py`
- `research/sierrachart_data_source_research_2026-05-02/samples/NQM26-CME.2026-05-02_delayed.depth`
- `research/sierrachart_data_source_research_2026-05-02/samples/NQM26-CME.2026-05-01_delayed.depth`

The current Sierra sample proves parser readability only. It does not support active-session market claims, Databento parity, or lead-lag research.

## Tasks That Can Run Now

| Priority | Task | Weekend status | Main local basis |
|---:|---|---|---|
| P0 | Source map and run plan | runnable now | docs and frozen artifacts listed above |
| P1-A | V2 confluence/disagreement deep dive | runnable now | V2 event log plus existing confluence script/tests |
| P1-B | Pre-fill delivery-path capture harness | runnable now as coverage/tooling | existing raw-OHLC replay inputs and historical M1/M5/M15 availability; scoring remains forbidden |
| P1-C | V3 full exploratory replay/risk-bank forensics | runnable under the handoff override | V3 must remain discovery-only, pre-registered, label-separated, and non-promotional |
| P1-D | V2b rolling status/evaluator hardening | runnable now | existing V2b evaluator and blocked-state artifacts |
| P1-E | Cached NAS100 orderflow feature forensics | runnable cached-only | existing MBO/MBP/trades feature diagnostics |
| P1-F | Proxy mapping weak-window forensics | runnable cached-only | USDJPY/6J follow-up and proxy expansion artifacts |
| P2-G | Phase 3 methodology diagnostics harness | runnable now | current claim ledger and methodology scripts |
| P2-H | D-11 old-data bias check | runnable if source files are present | structure detector backfills and ML audit inputs |
| P2-I | Shadow telemetry specs / isolated logger tests | runnable as spec or isolated test only | existing pending-limit telemetry spec and slippage logger tests |
| P2-J | Small backlog ops docs | runnable now | operations/backlog docs and code references |

## Explicit Weekend Skips

| Skip | Reason |
|---|---|
| Active Sierra capture | Weekend/market-closed sample is insufficient; needs active CME session and owner-side Sierra capture. |
| Sierra/Databento active parity | Requires a longer active Sierra `.depth` sample and aligned intraday export/window. |
| V2b validation verdict | Current state has `110` wanted post-cutoff rows but `0` resolved post-cutoff OB-boundary/J46 pairs. |
| Broad new Databento pulls | Goal is cached/local/no-new-forward-data; broad paid pulls are forbidden. |
| K54 v5/v6 architecture iteration | Deferred by current research state; same-cohort K54 primary iteration is stale. |
| Q2 sequence models | Deferred until cohort n `>=5000`. |
| Prompt/live decision-logic/risk/execution changes | Forbidden by weekend goal and project approval rules. |
| Production promotion dossier | All outputs in this weekend goal remain `NO_PROMOTION_VERDICT`. |

## Initial Run Plan

1. Finish P0 with this source map and commit only this research artifact.
2. Run P1-A next because it directly extends existing V2 event-log tooling and can produce a full-corpus confluence report without forward data.
3. Use P1-B after P1-A to build the missing pre-fill delivery-path coverage layer without scoring a strategy.
4. Treat P1-C V3 as allowed only after risk-bank tests and pre-registration are in place; every selected lift remains `DISCOVERY_ONLY_NOT_REGISTERED`.
5. Continue down the queue while preserving scoped commits and leaving known runtime dirt unstaged.

## Ambiguity Ledger

- Some same-date reports disagree about supported manifest counts because mutable shadow logs moved after earlier manifests; pinned report artifacts must be cited instead of live shadow-log counts.
- V3 outcome research conflicts with older `research_current_state.md` language that says outcome mining is blocked; the session-54 handoff explicitly opens V3 exploratory replay under stricter discovery-only rules. This source map treats the handoff as the task-specific override while preserving `NO_PROMOTION_VERDICT`.
- Pre-fill delivery-path reconstruction may be limited by missing original pending-limit lifecycle fields; P1-B should report coverage and missing fields rather than inventing fill states.
- Orderflow actual broker-R remains sparse, so cached orderflow work must separate synthetic/path labels from actual broker R and fill/no-fill state.
