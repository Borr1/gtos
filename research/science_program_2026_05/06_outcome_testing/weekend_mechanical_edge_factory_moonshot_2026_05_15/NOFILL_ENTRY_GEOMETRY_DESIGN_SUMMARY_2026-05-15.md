# No-Fill Entry Geometry Design Packet

Generated UTC: `2026-05-15T15:12:52Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `DESCRIPTIVE_DIAGNOSTIC_AND_FUTURE_STRATEGY_PROJECTION_DESIGN_ONLY`

This packet does not score an entry-offset strategy. It turns no-fill-to-TP-area path behavior into frozen future branch specs and capture requirements.

## Counts

- `latest_candidate_path_rows`: `207`
- `nofill_tp_area_rows`: `80`
- `nofill_group_rows`: `8`
- `path_context_rows`: `27`
- `branch_spec_rows`: `40`
- `capture_requirement_rows`: `4`

## Primary Findings

- No-fill-to-TP-area is frequent enough in the latest candidate_path_follow denominator to justify a dedicated entry-geometry challenger design.
- Observed miss distance varies sharply by symbol/side/framework, so offset branches must be symbol/session/regime scoped rather than global.
- Sierra depth features are available for a subset of metals/index no-fill rows and should become context descriptors, not causal claims yet.
- Decision-time bid/ask and conservative path ordering are required before converting this design into a strategy projection.

## Required Before Scoring

- `NOFILL-GEOM-CAP-001` decision_time_price: bid, ask, mid, spread, source_timestamp_utc
- `NOFILL-GEOM-CAP-002` candidate_geometry: original_entry, stop_loss, take_profit_1, risk_distance, min_distance_constraint, order_type
- `NOFILL-GEOM-CAP-003` path_ordering: tick_or_m1_bid_ask_path, entry_touch_time, tp_touch_time, sl_touch_time, ambiguity_flag
- `NOFILL-GEOM-CAP-004` cost_and_execution: spread_model, slippage_model, commission, reject_or_min_distance_status
