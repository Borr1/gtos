# Tick M15 Target Movement Packet

Generated UTC: `2026-05-15T15:59:16Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: development neutral target-movement controls only. No validation, R/PnL, live-readiness, or promotion verdict.

## Counts

- Primitive event rows: `8977`
- Target event rows: `22229`
- Flag control rows: `420`
- Fail-closed rows: `4702`
- Flag universe rows: `140`
- Control rows with flagged_n >= 20: `92`

## Sample Status

- `DESCRIPTIVE_N_GE_20`: `92`
- `DESCRIPTIVE_SMALL_N_LT20`: `328`

## Boundary

- Current-day partial rows are excluded fail-closed.
- Future bars must be contiguous.
- Same-symbol/session/horizon controls are development denominators, not validation.
- No neighbor/placebo/shuffle ranking has been applied yet.
