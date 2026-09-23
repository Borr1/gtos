# G0 FPB Concentration Duplicate Risk Ledger

- Route: `G0_NO_API_MECHANICAL_REPLAY_FPB_DISCOVERY_SYNTHESIS_CONTROL_ROUTE`
- Evidence class: `NO_API_G0_DISCOVERY_SYNTHESIS_CONTROL_ONLY`
- Generated: `2026-05-11T07:57:49+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Summary

- `raw_candidate_attempts`: `13540033`
- `duplicate_candidate_keys`: `687275`
- `duplicate_share_of_raw_attempts`: `0.05075874`
- `unique_denominator`: `12852758`
- `duplicate_key_policy`: `candidate duplicate key is symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256 per accepted substrate; duplicates are excluded from family/path-label denominators.`
- `path_label_duplicate_policy`: `one discovery path label is closed for each unique nonduplicate candidate; duplicate path keys remain zero under the accepted scanner contract.`
- `risk_decision`: `HIGH_ENOUGH_TO_REQUIRE_SEALED_HOLDOUT_AND_CONCENTRATION_CAPS_BEFORE_VALIDATION`

## Boundary

This artifact is discovery/control-only. It does not validate an edge, promote a family, score R/PnL/win-rate/expectancy/performance, call AI/API, use broker account/order/history/deal/position evidence, or change live trading behavior.
