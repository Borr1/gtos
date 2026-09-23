# G0 FPB Evidence Chain Reconciliation Ledger

- Route: `G0_NO_API_MECHANICAL_REPLAY_FPB_DISCOVERY_SYNTHESIS_CONTROL_ROUTE`
- Evidence class: `NO_API_G0_DISCOVERY_SYNTHESIS_CONTROL_ONLY`
- Generated: `2026-05-11T07:57:49+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Count Checks

| Check | Expected | Matrix | Denominator/G12 | Status |
|---|---:|---:|---:|---|
| `raw_candidate_attempts` | 13540033 | 13540033 | 13540033 | PASS |
| `duplicate_candidate_keys` | 687275 | 687275 | 687275 | PASS |
| `unique_denominator_path_label_rows` | 12852758 | 12852758 | 12852758 | PASS |
| `opened_family_count` | 11 | 11 | 11 | PASS |
| `baseline_control_family_count` | 4 | 4 | 4 | PASS |
## Boundary

This artifact is discovery/control-only. It does not validate an edge, promote a family, score R/PnL/win-rate/expectancy/performance, call AI/API, use broker account/order/history/deal/position evidence, or change live trading behavior.
