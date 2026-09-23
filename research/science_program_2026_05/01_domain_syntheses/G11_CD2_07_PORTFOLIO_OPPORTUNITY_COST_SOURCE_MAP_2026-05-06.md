# G11 CD2-07 Portfolio Opportunity-Cost Source Map - 2026-05-06

Lane: `G11` data sources and market expansion  
Assignment: `CD2-07` prop-firm stress calendar and portfolio opportunity cost  
Status: `G11_SECOND_PASS_SOURCE_MAP_ONLY`  
Frozen at UTC: `2026-05-06T09:32:18Z`  
Promotion verdict: `NO_PROMOTION_VERDICT`

## Scope Boundary

This artifact is a G11-owned second-pass handoff for CD2-07. It defines an observation-only source map and preregistered context boundary for explaining blocked opportunity cost around these seed rows:

- `G10-HYP-PROP-006`
- `G10-HYP-PORTFOLIO-007`
- `HYP-G7-CROSSASSET-STRESS-008`
- `HYP-G8-VVIX-TAIL-007`

It is not a master-registry edit, source-contract promotion, risk rule, correlation rule, order-routing rule, or validation result. It does not authorize live trading prompt changes, risk changes, execution changes, permissions changes, safety-gate changes, selector changes, MT5 calls, canary changes, paid data, credentials, remote pushes, or order behavior changes.

`Blocked opportunity cost` means a candidate or context row is observed as accepted, rejected, halved, dormant, skipped, source-blocked, or otherwise not converted into a full live position under the existing system. CD2-07 records the as-of context that explains that transition. It must not estimate missed R, broker actual-R, synthetic path-R, or financial opportunity value unless a later separate outcome-bearing prereg is frozen.

## Controlling Inputs Read

| Input | CD2-07 use |
|---|---|
| `research/science_program_2026_05/04_goal_prompts/G11_G11_DATA_SOURCES_EXPANSION_GOAL_PROMPT_2026-05-06.md` | G11 scope, source-governance role, forbidden surfaces, `NO_PROMOTION_VERDICT`, access and done standards. |
| `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md` | CD2-07 objective, seed rows, required blocker checks, and stop output. |
| `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md` | Confirms all G7-G11 rows remain research-only, all source contracts remain `validation_safe=false`, and cross-domain second-pass rows are lane handoffs only. |
| `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md` | Confirms reconciled master counts and survivor backlog `0`; no row is promotion-safe. |
| `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | Confirms `86` source contracts and `0` validation-safe rows. |
| `research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md` | Confirms `$0` new external cash spend and no approved paid source. |
| `research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.md` | Provides `experiment_prereg_v1` and `source_contract_v2` field standards for the sidecar prereg. |
| `research/science_program_2026_05/01_domain_syntheses/G10_EXECUTION_RISK_DOMAIN_SYNTHESIS_2026-05-06.md` | Defines prop-rule distance and portfolio cluster exposure as context, not alpha. |
| `research/science_program_2026_05/01_domain_syntheses/G7_MACRO_CROSS_ASSET_DOMAIN_SYNTHESIS_2026-05-06.md` | Defines cross-asset stress as source-governed context only; live correlation/risk gates remain untouched. |
| `research/science_program_2026_05/01_domain_syntheses/G8_OPTIONS_VOL_DOMAIN_SYNTHESIS_2026-05-06.md` | Defines VVIX/vol-of-vol context with Cboe source blockers and label separation. |
| `research/science_program_2026_05/01_domain_syntheses/G11_DATA_SOURCES_EXPANSION_SYNTHESIS_2026-05-06.md` | Defines G11 source provenance, public lag, options-vol, and observer/source-transfer gates. |

## Seed Row Interpretation

| Seed row | Original lane role | CD2-07 interpretation | Boundary |
|---|---|---|---|
| `G10-HYP-PROP-006` | `context_only` prop-firm rule-distance context | Map official prop rules, account phase, rule cache, equity snapshot, and internal risk-state distance at candidate decision time. | No financial advice, no parameter change, no operational prop-rule automation. |
| `G10-HYP-PORTFOLIO-007` | `observation_only` portfolio transition context | Map candidate-to-position transition state by concurrent count, open-position snapshot, correlation state, and existing risk-check outcome. | No correlation-group, max-concurrent, risk-sizing, or order behavior edits. |
| `HYP-G7-CROSSASSET-STRESS-008` | `synthetic_path_r` stress-context seed with live-gate edit explicitly forbidden | Use only predecision stress labels as explanatory context for clustered adverse conditions and co-movement. | Do not replay or alter live correlation/risk gates; do not score path outcomes in this sidecar. |
| `HYP-G8-VVIX-TAIL-007` | `context_only` vol-of-vol and short-tenor stress seed | Use Cboe vol-index source status as an optional index-stress context, blocked until as-of publication rules and parser tests exist. | No same-day intraday join until publication time is verified; no live selector/risk use. |

## Source Map

| Source contract or artifact | Local evidence | Candidate CD2-07 fields | As-of rule | Readiness | Blocker |
|---|---|---|---|---|---|
| `G10-SRC-PROP-FTMO-OFFICIAL` | Raw cache `raw/G10_execution_risk_sources_2026-05-06/ftmo_trading_objectives.html`; source index notes cache UTC `2026-05-06T08:04:57Z`. | `prop_vendor`, `program_type`, `account_phase`, `daily_loss_rule`, `max_loss_rule`, `min_trading_day_rule`, `rule_source_cached_at_utc`. | Re-fetch and parse before operational use; source cache time must be before candidate decision context. | `PARTIAL_SOURCE_CONTEXT_ONLY` | Program-type, phase, reset-time, and rule-update monitoring not complete. |
| `G10-SRC-PROP-redacted_account-OFFICIAL` | Raw cache `redacted_account_daily_loss_limit.html`; source index notes cache UTC `2026-05-06T08:04:58Z` and page `dateModified=2026-04-08T03:13:46Z`. | `prop_vendor`, `daily_loss_rule`, `account_type`, `server_day_rule`, `source_modified_at_utc`, `rule_source_cached_at_utc`. | Use official article modified/cache timestamp only after parser extracts article body and account-type mapping. | `BLOCKED_PARSER_INCOMPLETE` | Article body is embedded in minified Intercom payload; daily-loss article alone is not full program coverage. |
| `G10-SRC-LOCAL-EXECUTION-CODE` | G10 context ledger cites `src/components/permissions.py`, `concurrent_tracker.py`, `portfolio_risk.py`, and `cross_instrument_correlation_gate.py` as read-only behavior evidence. | `risk_check_asof_utc`, `risk_check_result`, `rejection_or_halving_reason`, `open_position_count`, `configured_concurrent_cap_observed`, `correlation_gate_context_observed`. | Use file evidence at current HEAD only as implementation context; rerun live state before future line-evidence claims. | `LOCAL_CONTEXT_ONLY` | Code is not market validation and cannot be modified by CD2-07. |
| `G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE` | `shadow_logs/` and research health audits list candidate/opportunity/lifecycle logs, including `live_candidate_opportunity_clusters.jsonl` and `missed_opportunity_shadow.jsonl`. | `candidate_transition_state`, `candidate_status_reason`, `lifecycle_state_before_outcome`, `source_capture_utc`, optional coverage flags. | Row timestamps must be before outcome review; source signature must be frozen. | `PARTIAL_OBSERVATION_CONTEXT` | Exact `risk_check_asof_utc`, open-position snapshot, and correlation matrix fields are not proven complete for every candidate. |
| `SRC-G7-FRED-RATES-001` | G7 source rows record FRED/rates as fetch-failed in that pass with no validation-ready cache. | Optional future `rates_stress_state`, `real_yield_state`, `rates_source_cache_time_utc`. | Daily close/availability time must precede candidate decision; observation date alone is not enough. | `BLOCKED_NO_CACHE` | Official refresh failed; parser/cache/no-lookahead tests missing. |
| `SRC-G7-ICE-DXY-001` | G7 source index records ICE DXY page cached as DXY-adjacent source discovery. | Optional future `dollar_state`, `dxy_source_timestamp_utc`, `dxy_cache_time_utc`. | Bar timestamp, close/publication time, retrieval time, and parser hash must be stored before use. | `BLOCKED_CONTEXT_ONLY` | No validation-safe DXY parser/cache; local DXY evidence is soft context only. |
| `SRC-G7-LOCAL-GTOS-MACRO-001` | G7 context/source index and local GTOS research docs. | `local_stress_context_source_ref`, killed-route and stale-context flags. | Local docs are not market data; future rows must reference source-specific publication timestamps. | `LOCAL_CONTEXT_ONLY` | Cannot validate stress labels or replace source contracts. |
| `SRC-G8-CBOE-VOL-CSV-001` | G8 source contracts record Cboe public daily CSVs for VIX, VIX1D, VIX9D, VIX3M, GVZ, and VVIX. | Optional future `vvix_vix_ratio_asof`, `vix_vix3m_slope_asof`, `vix1d_vix9d_spread_asof`, `vol_source_cache_time_utc`. | Treat same-day daily rows as unavailable for intraday decisions until publication timestamp proves otherwise. | `BLOCKED_ASOF_UNKNOWN` | License review, parser tests, source registry entry, and no-lookahead joins missing. |
| `SRC-G11-PUBLIC-CFTC-FRED-BIS` | G11 source contracts record release-aware public macro source family. | Source-governance flags for release lag, vintage, and observation-date leakage. | CFTC release timestamp, FRED release/vintage timestamp, and BIS release calendar timestamp are required. | `SOURCE_GOVERNANCE_CONTEXT_ONLY` | Release-aware joins not implemented; macro cadence too slow for direct M15/H1 role. |
| `SRC-G11-CBOE-OPTIONS-VOL` | G11 source contracts record options/gamma/vol source state and paid/licensed blockers. | Source-governance flags for options-vol completeness, license state, and historical coverage. | Vendor timestamp, index publication timestamp, and license method must be frozen before use. | `SOURCE_GOVERNANCE_CONTEXT_ONLY` | Historical aggregate GEX blocked; VIX1D/VIX9D/VVIX/VRP incomplete. |

## Observation Row Contract

CD2-07 should only create or evaluate rows that can be populated before outcome review. The minimum row contract is:

| Field group | Required fields | Notes |
|---|---|---|
| Identity | `cd2_07_row_id`, `setup_id`, `symbol`, `side`, `session`, `candidate_decision_asof_utc` | `setup_id` is the independent setup key when available. |
| Prop-rule context | `prop_vendor`, `program_type`, `account_phase`, `rule_snapshot_id`, `rule_source_cached_at_utc`, `rule_snapshot_effective_at_utc`, `server_day_rule` | Required only when the prop source parser is complete for the vendor/program. |
| Internal account/risk state | `equity_snapshot_asof_utc`, `daily_loss_distance_internal_pct`, `max_loss_distance_internal_pct`, `internal_daily_loss_stop_state` | Observation-only; no financial recommendation. |
| Portfolio transition | `risk_check_asof_utc`, `candidate_transition_state`, `rejection_or_halving_reason`, `open_positions_snapshot_utc`, `open_position_count`, `configured_concurrent_cap_observed` | Do not recompute after outcome. |
| Correlation context | `correlation_matrix_asof`, `correlation_group`, `correlation_gate_context_observed`, `same_direction_cluster_count` | Read-only explanation of existing gates; no group/rule edits. |
| Stress context | `stress_state_timestamp_utc`, `stress_source_cache_time_utc`, `stress_source_family`, `stress_bucket_predecision` | Only if source as-of timestamps pass; otherwise record `source_blocked`. |
| Vol-of-vol context | `vvix_source_timestamp_utc`, `vix_source_timestamp_utc`, `vix3m_source_timestamp_utc`, `vvix_vix_ratio_asof`, `vix_vix3m_slope_asof` | Block same-day intraday joins until Cboe publication timing is verified. |
| Label guard | `outcome_review_opened`, `label_family_allowed`, `forbidden_label_join_attempted` | Must keep `outcome_review_opened=false` in the sidecar phase. |

Forbidden in this source map: `actual_r`, `broker_actual_r`, `synthetic_path_r`, `future_return`, `tp_hit`, `sl_hit`, post-entry path fields, manual financial decision labels, and any field produced by changing risk/correlation/order behavior.

## Required Blocker Checks

| G0 required blocker check | CD2-07 status | Evidence |
|---|---|---|
| Prop rule parser completeness | `BLOCKED_PARTIAL` | FTMO official page is cached; redacted_account daily-loss page is cached but parser incomplete and daily-loss article alone is not full rule coverage. |
| Correlation/opportunity lifecycle labels | `PARTIAL_SOURCE_CONTEXT_ONLY` | G10 has portfolio-transition hypothesis/prereg rows and local shadow opportunity logs exist, but complete `risk_check_asof`, open-position snapshot, and correlation matrix fields are not proven across the row population. |
| Stress context as-of timestamps | `BLOCKED_PARTIAL` | G7 FRED/rates cache failed; ICE DXY is page-discovery only; G8 Cboe vol CSV publication timing is unknown. |
| No risk config edits | `PASS_FOR_THIS_ARTIFACT` | This artifact is markdown plus a sidecar prereg JSON only. It does not edit `config`, `src`, prompts, permissions, execution, safety gates, selectors, MT5, canaries, or order behavior. |

## Stop Output Link

Observation-only prereg sidecar:

`research/science_program_2026_05/03_experiment_specs/G11_CD2_07_PORTFOLIO_OPPORTUNITY_COST_PREREG_2026-05-06.json`

Final verdict: `NO_PROMOTION_VERDICT`.
