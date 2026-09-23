# No-Fill Entry Geometry Ambiguity/Split Packet

Generated UTC: `2026-05-16T02:29:48Z`

This packet preserves every repair/proxy branch and opens the next same-resource work layer without scoring outcomes.

## Counts

- `branch_status_rows`: `400`
- `bucket_rows`: `19`
- `candidate_rows`: `80`
- `challenger_denominator_rows`: `207`
- `invalid_geometry_split_rows`: `993`
- `m15_control_rows`: `264`
- `m1_stress_rows`: `9`
- `question_rows`: `3`
- `repair_branch_rows`: `400`
- `repair_candidate_rows`: `80`
- `source_manifest_rows`: `8`

## Proxy Projection Status Counts

- `NO_SCORE_PROXY_AVAILABLE_M15_ENVELOPE_ONLY_LTF_REQUIRED`: `66`
- `NO_SCORE_PROXY_READY_M1_RECOVERED_ORDER_AMBIGUOUS`: `3`
- `ROUTE_SPLIT_INVALID_TP1_GEOMETRY`: `331`

## Immediate Work

- Attempt tick/bid-ask replay for the M1 recovered ambiguity rows.
- Attempt owned/current/free lower-timeframe reconstruction for M15-only controls.
- Materialize target-retargeting grids for invalid-TP1 rows.
- Compare market-entry redesign target families on source-safe controls.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
