# LTO033 Orderflow Primitives - 2026-05-05

**Status:** `OK_PRIMITIVES_REGISTERED_WITH_SOURCE_BLOCKERS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

LTO-033 is now registered as measurable orderflow primitives instead of broad opinions. Current cached/local data supports trades-level delta/absorption, MBP-10 depth, NAS100 MBO diagnostics, and partial volume-profile context; stacked footprint imbalance and VAH/VAL remain source-not-captured; Databento live remains license-blocked.

## Primitive Registry

| Primitive | Lane | Family | Schemas | Status | Roles |
| --- | --- | --- | --- | --- | --- |
| X1_FOOTPRINT_DELTA_ABSORPTION_V1 | X-1 | footprint_delta_absorption | trades, sierra_scid | CACHED_TRADES_EXTRACTOR_READY_SIERRA_FOOTPRINT_PARTIAL | entry_timing, bad_condition_veto, stop_invalidation_efficiency |
| X1_STACKED_IMBALANCE_FOOTPRINT_V1 | X-1 | stacked_imbalance | sierra_scid, trades | SOURCE_NOT_CAPTURED_REGISTERED_PRIMITIVE | entry_timing, bad_condition_veto |
| X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1 | X-2 | depth_thinness_wall_concentration | mbp-10, sierra_depth | CACHED_MBP10_AND_SIERRA_DEPTH_AVAILABLE_WITH_PROXY_POLICIES | bad_condition_veto, entry_timing, stop_invalidation_efficiency |
| X2_LIQUIDITY_PULL_DEPLETION_V1 | X-2 | liquidity_pull_depletion | mbo, sierra_depth | NAS100_CACHED_MBO_DIAGNOSTIC_ONLY_LIVE_LICENSE_BLOCKED | bad_condition_veto, entry_timing |
| X3_META_ORDER_FLOW_QUEUE_BEHAVIOR_V1 | X-3 | meta_order_flow_queue_behavior | mbo | MBO_SOURCE_BLOCKED_FOR_LIVE_LICENSE_AND_COST_VALUE | bad_condition_veto, target_rr_expansion |
| VP_VOLUME_PROFILE_CONTEXT_V1 | X-1 | volume_profile_context | trades, sierra_scid | EXTRACTOR_PARTIAL_POC_HVN_LVN_READY_VAH_VAL_NOT_CAPTURED | target_rr_expansion, stop_invalidation_efficiency, entry_timing |

## Field Coverage

| Primitive | Coverage | Missing decision fields | Blockers |
| --- | --- | --- | --- |
| X1_FOOTPRINT_DELTA_ABSORPTION_V1 | 1 | - | SIERRA_SCID_FOOTPRINT_CONVERTER_NOT_FULLY_REGISTERED |
| X1_STACKED_IMBALANCE_FOOTPRINT_V1 | 0 | pre60_stacked_imbalance_run_count, event15_stacked_imbalance_run_count, event15_max_bid_ask_volume_ratio_by_price, event15_imbalance_price_level_count | FOOTPRINT_PRICE_LEVEL_BID_ASK_VOLUME_NOT_CAPTURED |
| X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1 | 1 | - | DATABENTO_LIVE_LICENSE_BLOCKED, SYMBOL_SPECIFIC_SIERRA_PARITY_REQUIRED |
| X2_LIQUIDITY_PULL_DEPLETION_V1 | 1 | - | DATABENTO_LIVE_LICENSE_BLOCKED, MBO_COST_AND_STORAGE_CAP_REQUIRED |
| X3_META_ORDER_FLOW_QUEUE_BEHAVIOR_V1 | 1 | - | DATABENTO_LIVE_LICENSE_BLOCKED, MBO_NOT_DEFAULT_COLLECTION_SCHEMA |
| VP_VOLUME_PROFILE_CONTEXT_V1 | 0.714286 | profile_vah_price, profile_val_price | VAH_VAL_NOT_CAPTURED, SESSION_PROFILE_DEFINITION_NOT_FROZEN |

## Role Matrix

| Role | Primitives |
| --- | --- |
| entry_timing | X1_FOOTPRINT_DELTA_ABSORPTION_V1, X1_STACKED_IMBALANCE_FOOTPRINT_V1, X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1, X2_LIQUIDITY_PULL_DEPLETION_V1, VP_VOLUME_PROFILE_CONTEXT_V1 |
| bad_condition_veto | X1_FOOTPRINT_DELTA_ABSORPTION_V1, X1_STACKED_IMBALANCE_FOOTPRINT_V1, X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1, X2_LIQUIDITY_PULL_DEPLETION_V1, X3_META_ORDER_FLOW_QUEUE_BEHAVIOR_V1 |
| stop_invalidation_efficiency | X1_FOOTPRINT_DELTA_ABSORPTION_V1, X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1, VP_VOLUME_PROFILE_CONTEXT_V1 |
| target_rr_expansion | X3_META_ORDER_FLOW_QUEUE_BEHAVIOR_V1, VP_VOLUME_PROFILE_CONTEXT_V1 |

## No-Lookahead And Cost Policy

- No-lookahead check: `PASS`.
- Decision fields checked: `40`.
- Post-event policy: post15/post60 fields are forensic-only and are not in primitive decision_feature_fields.
- Databento trigger cap: `$2.5`.
- Databento daily cap: `$25.0`.
- This audit paid-data calls: `0`.

## Cached Feature Stability

Cached feature stability supports forward field selection only. It does not validate a live filter because actual broker-R coverage is sparse and date concentration is high.

| Feed | Candidate | Context | Actual R | Top date share | Depth sign flips | Thin sign flips | Imbalance sign flips |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MBO_TOP20 | 12 | 47 | 1 | 0.75 | 1 | 0 | 0 |
| MBP10_TOP10 | 12 | 61 | 1 | 0.75 | 1 | 2 | 1 |

## Source Readiness

- Databento live status: `WAITING_FOR_DATABENTO_LIVE_LICENSE`.
- Databento live license blocker: `True`.
- Sierra depth status: `OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE`.
- Sierra 6B/SI policy status: `OK_WITH_6B_POLICY_AND_SI_BLOCKER`.

## Boundary

Primitive registration and cached feature design only. No live filter, signal, risk modifier, entry rule, target rule, or promotion claim is authorized.

## Next Actions

- Use these primitive IDs in future Sierra/Databento candidate-window rows.
- Keep post15/post60 fields forensic only and score only pre60/event15/profile decision fields.
- Prioritize Sierra .scid footprint conversion for stacked imbalance and VAH/VAL semantics.
- Use MBO only in surgical NAS100/NQ windows until live license/cost/value evidence is stronger.

## Non-Claims

- No orderflow primitive is promoted.
- No threshold is selected.
- No live filter, target, stop, risk, prompt, execution, or order behavior changed.
