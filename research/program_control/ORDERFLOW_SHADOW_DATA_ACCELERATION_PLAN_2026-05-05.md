# Orderflow Shadow Data Acceleration Plan - 2026-05-05

**Status:** `SIERRA_ACTIVE_DATABENTO_HISTORICAL_REPLAY_DATABENTO_LIVE_LICENSE_BLOCKED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

This plan accelerates shadow-data capture and validation only. It does not alter live entries, filters, risk, execution, prompts, or safety gates.

## Current State

| Source | Metric | Value |
| --- | --- | --- |
| Databento | lto011_status | WAITING_FOR_DATABENTO_LIVE_LICENSE |
| Databento | live_license_blocker | true |
| Databento | broker_actual_r_rows_nas100_unique | 1 |
| Databento | cached_mbp10_candidate_rows | 12 |
| Databento | live_mbp10_candidate_rows | 0 |
| Databento | declared_nas100_nq_requests | 5 |
| Databento | historical_replay_policy | Use Databento historical as post-event replay with features capped at decision_time_utc. Do not treat historical availability as same as live feed availability. |
| Sierra | lto012_status | OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE |
| Sierra | lto013_status | OK_WITH_BLOCKED_PROXY_ROWS |
| Sierra | candidate_rows | 48 |
| Sierra | depth_features_extracted | 23 |
| Sierra | background_queue_candidates | 22 |
| Sierra | usable_depth_context_rows | 14 |
| Sierra | blocked_or_no_proxy_rows | 33 |

## Execution Lanes

| Lane | Status | Command | Value |
| --- | --- | --- | --- |
| SIERRA_REGISTRY_FIRST | OK_WITH_BLOCKED_PROXY_ROWS | python scripts/audit_sierra_proxy_registry.py | Prevents false confidence by forcing every candidate into validated, caution, blocked, no-proxy, or control-only use. |
| SIERRA_GUARDED_DEPTH_ENRICHMENT | OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE | python scripts/enrich_sierra_live_candidate_depth_features.py --max-hours 24 --max-file-size-mb 128 --max-per-symbol 2 --limit 6 | Turns local .depth capture into pre-decision shadow features without letting large files stall candidate capture. |
| SIERRA_FOOTPRINT_AND_VOLUME_PROFILE_DESIGN | NEXT_AFTER_DEPTH_REGISTRY | python scripts/convert_sierra_scid_to_ohlcv.py | Use Sierra .scid as the source for footprint-style bid/ask volume, delta, and volume-profile context around GTOS POIs. |
| SIERRA_OFF_KZ_BACKGROUND_QUEUE | READY_FOR_OPERATOR_WINDOW | python scripts/enrich_sierra_live_candidate_depth_features.py --max-hours 72 --max-file-size-mb 1024 --max-per-symbol 10 --limit 40 | Backfills guarded large-file rows outside active trading windows when runtime is acceptable. |
| DATABENTO_HISTORICAL_COUNTERFACTUAL_REPLAY | ESTIMATE_FIRST_EXECUTE_ONLY_UNDER_COST_CAP | python scripts/fetch_databento_manifest.py --schema mbp-10 --max-group-cost-usd 1 --max-total-cost-usd 8 | Measures what a live Databento collector would have seen, using decision-time cutoffs and no lookahead. |
| DATABENTO_LIVE_COLLECTOR | WAITING_FOR_DATABENTO_LIVE_LICENSE | python scripts/databento_live_shadow_collector.py | Runs only when the live license/env/cooldown/budget trigger policy allows it. |
| ACCOUNT_HISTORY_OUTCOME_JOIN | JOIN_ROWS_AS_ACCOUNT_HISTORY_REALIZED_ONLY | python scripts/audit_nas100_orderflow_adverse_selection.py | Orderflow only matters after candidate features join to broker actual-R, costs, and lifecycle truth. |

## What Each Source Adds

### Databento Unique

- Clean API with stable schemas, cost estimation, and reproducible historical/live request records.
- MBO order-level events for add, pull, and queue-flow diagnostics that Sierra MBP snapshots do not fully reconstruct.
- Canonical programmatic source for cross-session research and replay once licensed for live.

### Sierra Unique

- Local live capture and visual heatmap/replay evidence available before a Databento live subscription.
- .scid bid/ask-volume and local platform state that can support operator-visible source sanity checks.
- Redundant local source for registered futures depth when Databento live is license-blocked.

## ICT To Orderflow Translation

Orderflow should not replace GTOS structure first. It should explain the quality of a structural setup at the decision point, then test whether it improves timing, stop efficiency, target expansion, or bad-condition vetoes.

| Family | Source | Role To Test |
| --- | --- | --- |
| footprint_delta_absorption | Sierra footprint/.scid bid-ask volume first; Databento trades and MBO later | entry_timing_or_veto_shadow_only |
| volume_profile_context | Sierra .scid-derived session profile and operator chart profile | target_selection_and_rr_expansion_shadow_only |
| ladder_depth_liquidity | Sierra .depth now; Databento MBP-10/MBO for canonical replay/live once licensed | market_condition_awareness_and_adverse_selection_shadow_only |

## Promotion Gates

- No promotion from source presence, historical replay alone, synthetic labels, or a single proxy-transfer report.
- Review after event-count gates, not after a fixed month: each new block of broker actual-R rows should update the dossier.
- LTO-011 floors remain the first NAS100 orderflow minimum: 20 broker actual-R rows and 30 MBP10 candidate rows before filter claims.
- Any live-filter, signal, risk-modifier, entry-timing, or execution change still requires a separate CEO approval and source/prompt/src diff.

## Acceleration Policy

- Sierra is used now for every captured candidate with registry and depth enrichment lanes.
- Databento historical is used aggressively for counterfactual replay under cost caps instead of sitting idle.
- Databento live is blocked only by the live data license gate, not by a no-API posture.
- Promotion timing is evidence-count driven and can accelerate as soon as forward broker-R rows support it.
