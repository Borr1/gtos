# LTO031 / LTO032 Source Unblocking And Replay Plan - 2026-05-05

**Status:** `GOAL_EXTENSION_READY_RESEARCH_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Schema:** `lto031_lto032_source_unblocking_and_replay_plan_v1`

## Purpose

The approved LTO goal is complete with LTO-031/LTO-032 documented as source-blocked. This extension converts those blockers into a source-unblocking and replay implementation program.

This is part of the completed limitations-to-opportunities goal as a follow-on source-unblocking program. It is not a live-trading promotion and does not change prompts, execution, risk, safety gates, or order behavior.

## Current Blocker Summary

| Lane | Status | Source count | Status counts |
| --- | --- | --- | --- |
| LTO-031 | SOURCE_BLOCKED_READINESS_REGISTERED | 7 | {"BLOCKED": 5, "BLOCKED_SOURCE_MAPPING_REQUIRED": 1, "BLOCKED_SOURCE_UNSPECIFIED": 1} |
| LTO-032 | PARTIAL_FORWARD_CONTEXT_WITH_SOURCE_BLOCKERS_REGISTERED | 4 | {"BLOCKED": 2, "BLOCKED_CONSTRUCTION_REQUIRED": 1, "READY_FORWARD_CONTEXT_ONLY": 1} |
| Orderflow | SIERRA_ACTIVE_DATABENTO_HISTORICAL_REPLAY_DATABENTO_LIVE_LICENSE_BLOCKED | - | - |

## Source Contracts

| Source | LTO | Priority | Free/existing | Databento use | Sierra use | Decision use |
| --- | --- | --- | --- | --- | --- | --- |
| fx_cot | LTO-031 | P1_FREE_PUBLIC | FREE_PUBLIC_EXPECTED | NOT_APPLICABLE | NOT_APPLICABLE | K55_FEATURE_AND_REGIME_CONTEXT_SHADOW_ONLY |
| bis_macro | LTO-031 | P1_FREE_PUBLIC | FREE_PUBLIC_EXPECTED | NOT_APPLICABLE | NOT_APPLICABLE | REGIME_AND_MACRO_CONTEXT_SHADOW_ONLY |
| fed_fred_research | LTO-031 | P1_FREE_PUBLIC | PARTIALLY_EXISTING_FREE_PUBLIC | NOT_APPLICABLE | NOT_APPLICABLE | MACRO_CONTEXT_AND_K55_FEATURE_SHADOW_ONLY |
| kmw_fx_fix | LTO-031 | P2_SOURCE_SPEC_THEN_PUBLIC_OR_PROXY | FREE_PROXY_POSSIBLE_OFFICIAL_SOURCE_REQUIRED | CAN_REPLAY_FUTURES_VOLUME_AROUND_FIX_WINDOWS_FOR_FX_PROXIES | CAN_SANITY_CHECK_INTRADAY_VOLUME_SHAPE_AFTER_FLAGS_EXIST | SESSION_CONTEXT_SHADOW_ONLY |
| hkm_intermediary_capital | LTO-031 | P3_SOURCE_DISCOVERY | SOURCE_SEARCH_REQUIRED | NOT_APPLICABLE | NOT_APPLICABLE | SLOW_REGIME_CONTEXT_SHADOW_ONLY |
| pre_2024_tick_lob | LTO-031 | P2_DATABENTO_CREDIT_REPLAY | EXISTING_DATABENTO_HISTORICAL_CREDITS_FIRST | PRIMARY_HISTORICAL_COUNTERFACTUAL_REPLAY_SOURCE | LOCAL_RECENT_DEPTH_ONLY_NOT_PRE_2024_UNLESS_FILES_EXIST | HISTORICAL_COUNTERFACTUAL_REPLAY_AND_K55_FEATURE_DESIGN |
| pre_2022_ohlcv | LTO-031 | P3_LOCAL_THEN_PROVIDER | LOCAL_FIRST_PROVIDER_LATER | POSSIBLE_OHLCV_HISTORY_SOURCE_IF_CREDIT_COST_IS_REASONABLE | SCID_EXPORT_IF_FILES_EXIST_OR_OPERATOR_DOWNLOAD_AVAILABLE | REPLAY_INPUT_ONLY |
| flashalpha_basic_gex_forward_proxy | LTO-032 | P1_KEEP_RUNNING | EXISTING_FORWARD_CONTEXT | NOT_APPLICABLE | NOT_APPLICABLE | FORWARD_CONTEXT_ONLY |
| vix_vix9d_gvz_vvix_vix1d | LTO-032 | P1_FREE_PUBLIC_PARTIAL | FREE_PUBLIC_PARTIAL | NOT_PRIMARY_SOURCE_FOR_CBOE_VOL_INDEX_HISTORY | NOT_APPLICABLE | VOLATILITY_REGIME_CONTEXT_SHADOW_ONLY |
| official_or_historical_aggregate_gex | LTO-032 | P4_PAID_SOURCE_DECISION_AFTER_FREE_EVIDENCE | PAID_OR_QUOTE_DEPENDENT | ONLY_IF_OPTIONS_DATASET_AND_GAMMA_CONSTRUCTION_ARE_LICENSED | NOT_APPLICABLE | SOURCE_EVALUATION_THEN_SHADOW_FEATURE_ONLY |
| vrp_delta | LTO-032 | P3_FORMULA_AND_TESTS | FREE_PROXY_POSSIBLE_PAID_FOR_FULL_OPTIONS | REALIZED_VOL_OR_OPTIONS_SOURCE_IF_LICENSED | REALIZED_VOL_FROM_LOCAL_BARS_ONLY_IF_ASOF | VOL_REGIME_CONTEXT_SHADOW_ONLY |

## Implementation Phases

### P0_SOURCE_CONTRACT_REGISTRY

- Status: `READY_TO_IMPLEMENT_RESEARCH_ONLY`
- Objective: Convert LTO-031/LTO-032 blockers into concrete source contracts before any ingest.
- Promotion boundary: No data fetched; no validation claim.
- Outputs:
  - source registry JSON with url/vendor, legal/access status, cache schema, publication timestamp rule, feature safety
  - tests proving blocked sources cannot be marked validation-safe without source contract evidence
- Tests:
  - unit tests for source-counts, status transitions, no-promotion boundary, no-action counters

### P1_FREE_PUBLIC_AND_EXISTING_FEEDS

- Status: `NEXT`
- Objective: Unblock the free/high-ROI parts first: FX COT, BIS, FRED/Fed extensions, public Cboe vol indices, FlashAlpha forward snapshots.
- Promotion boundary: Feature/context rows only; no live rule.
- Outputs:
  - raw source snapshots plus source index
  - normalized point-in-time caches with release/publication timestamps
  - candidate join snapshots keyed by candidate_id and decision_time_utc
- Tests:
  - parser fixtures
  - publication timestamp/no-lookahead fixtures
  - candidate join fixtures with missing-source and stale-source states

### P2_DATABENTO_HISTORICAL_CREDIT_REPLAY

- Status: `APPROVED_TO_PLAN_ESTIMATE_FIRST`
- Objective: Use existing Databento historical credits for counterfactual candidate-window replay instead of letting credits sit unused.
- Promotion boundary: Historical replay can justify live subscription value; it is not the same as live operational validation.
- Outputs:
  - predeclared Databento request manifests
  - cost estimates before fetch
  - raw/cache paths and source index after fetch
  - decision-time-capped trades/MBP-10/MBO features
  - outcome joins separated by broker actual-R, synthetic path-R, and lifecycle labels
- Tests:
  - manifest schema tests
  - cost-cap rejection tests
  - window cutoff tests proving features do not use post-decision rows
  - outcome-label separation tests

### P3_SIERRA_FULL_UTILIZATION

- Status: `ACTIVE_LOCAL_SOURCE`
- Objective: Use Sierra .depth and .scid for every possible local market-awareness feature before buying more data.
- Promotion boundary: Sierra features remain shadow/context until validated against outcome labels.
- Outputs:
  - guarded .depth enrichment backlog
  - .scid footprint/delta/volume-profile extractor design and tests
  - source parity status per symbol
  - feature rows joined to candidates with source freshness
- Tests:
  - SCID parser fixtures
  - depth file-size guard tests
  - bid/ask volume and profile bin tests
  - source parity status tests

### P4_OPTIONS_GAMMA_AND_VRP

- Status: `PARTIAL_SOURCE_BLOCKED`
- Objective: Turn options/gamma/VRP into source-safe features, using public/proxy data first and paid official GEX only after evidence supports it.
- Promotion boundary: No historical gamma validation before legal timestamped GEX source exists.
- Outputs:
  - FlashAlpha forward-context join
  - Cboe vol-index cache where legal/public
  - VRP formula preregistration
  - paid historical GEX source-decision dossier if still needed
- Tests:
  - proxy mapping tests
  - VRP realized-vol no-lookahead tests
  - daily vol-index availability tests
  - paid-source blocked state tests

### P5_K55_AND_SHADOW_JOIN

- Status: `REQUIRED_INTEGRATION_LAYER`
- Objective: Make every valid source improve K55/ML shadow quality through as-of features, provenance, freshness, and label-quality flags.
- Promotion boundary: ML remains shadow-only until separate promotion dossier.
- Outputs:
  - external_context feature bundle
  - feature provenance and source freshness fields
  - sample eligibility fields
  - blocked/missing-source flags kept out of decision-time numeric leakage
- Tests:
  - feature-safe key whitelist tests
  - post-decision label exclusion tests
  - source dependency signature tests

### P6_VALIDATION_DOSSIER_GATES

- Status: `FUTURE_AFTER_ROWS`
- Objective: Review evidence by event-count gates, not by waiting a calendar month.
- Promotion boundary: Any live filter/risk/entry/execution promotion needs separate owner approval.
- Outputs:
  - rolling source value dossier
  - actual-R vs synthetic-R separated results
  - concentration/effective-N/DSR/PBO where computable
  - promotion dossier template only when sample floors are met
- Tests:
  - claim-ledger schema tests
  - sample-floor tests
  - concentration cap tests
  - not-computable reason tests

## Databento Credits And Sierra

Databento historical credits should be used for cost-capped counterfactual replay windows. The first replay priority is NAS100/NQ, then US30/YM, XAUUSD/GC, XAGUSD/SI, USDJPY/6J, and GBPUSD/6B. Every replay window must be predeclared, estimated before fetch, capped at `decision_time_utc`, cached, and joined to outcome labels without leakage.

Sierra should continue as the immediate local orderflow source: `.depth` for ladder/depth context and `.scid` for footprint-style bid/ask volume, delta, and volume-profile context. Sierra does not replace Databento MBO or macro/options sources.

## Budget Policy

- Posture: `ZERO_NEW_EXTERNAL_CASH_FOR_NOW_FREE_PUBLIC_AND_EXISTING_CREDITS_ONLY`
- Current external cash spend cap: `$0`.
- First public-source pass estimate: `$0` to `$0` because the current phase allows no new external cash spend.
- Initial Databento historical credit cap: `$25.0` existing credits total, `$8.0` existing credits daily, `$1.0` existing credits per request.
- Paid-source revisit trigger: Open a separate spend decision only after free/public + existing-credit evidence identifies a concrete source family with measurable candidate-outcome value.

## Validation Gates

| Gate | Requirement | Evidence |
| --- | --- | --- |
| G0_NO_ACTION_BOUNDARY | planner/builders make zero AI, canary, MT5 order, execution, prompt, risk, or live-decision changes | no-action counters and focused tests |
| G1_SOURCE_CONTRACT | each source has URL/vendor, legal/access path, cache schema, timestamp convention, cost policy, and feature-safety classification | source registry tests and source index |
| G2_NO_LOOKAHEAD | every feature joins by decision_time_utc/asof_cutoff_utc and source publication timestamp | fixture tests with report date vs publication date, intraday cutoffs, and missing-source states |
| G3_LABEL_SEPARATION | broker actual-R, synthetic path-R, lifecycle truth, and proxy/context labels remain separate | outcome join tests and claim-ledger fields |
| G4_COST_AND_COVERAGE | Databento requests estimate cost before fetch; every paid/credit usage logs manifest and budget ledger row | manifest/cost-cap tests and source index |
| G5_SOURCE_VALUE_REVIEW | feature value is reviewed against broker actual-R where available, synthetic path-R separately, fill/no-fill, cost/slippage, symbol/session/regime concentration | rolling source value dossier |
| G6_PROMOTION_DOSSIER_ONLY | no live signal/filter/risk/entry/execution changes until a separate promotion dossier passes sample, concentration, cost, no-leak, and owner-approval gates | promotion checklist and explicit NO_PROMOTION_VERDICT |

## Required Tests

- `python -m pytest tests/test_lto031_lto032_source_unblocking_plan.py -q`
- `python -m pytest tests/test_lto_blocked_lane_readiness.py tests/test_orderflow_shadow_data_acceleration_plan.py -q`
- `python -m py_compile scripts/build_lto031_lto032_source_unblocking_plan.py`

## NO_PROMOTION_VERDICT

This plan is research/tooling only. It does not validate, promote, wire, or alter live trading behavior.
