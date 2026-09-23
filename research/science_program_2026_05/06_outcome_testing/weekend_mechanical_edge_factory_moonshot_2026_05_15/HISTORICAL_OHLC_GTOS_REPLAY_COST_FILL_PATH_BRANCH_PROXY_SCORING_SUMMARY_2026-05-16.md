# Historical OHLC GTOS Replay Cost/Fill/Path Branch Proxy Scoring

Generated UTC: 2026-05-16T05:51:49Z

## Boundary

Historical OHLC GTOS replay cost/fill/path branch proxy scoring only. Rows mechanically score same-resource fillability, spread/path sensitivity, source confidence, ambiguity, duplicate/effective-N, and implementation implications for all 386 branch-queue rows; no validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior change is claimed.

## Counts

- Branch score rows: 386
- Action score rows: 1499
- Concentration rows: 196
- Duplicate/effective-N rows: 386
- Implementation implication rows: 3190
- Bucket rows: 18
- Question rows: 8
- Repair-entry-only rows: 2

## Bucket Distributions

### path_scope_bucket
- M15_PATH_CONTROL_JOINED: 384
- REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT: 2

### fillability_bucket
- FAR_OR_WITHIN_RANGE_NOFILL_REDESIGN_AVAILABLE: 128
- MIXED_OR_DESCRIPTOR_ONLY_FILLABILITY: 128
- NEAR_MISS_ENTRY_CHALLENGER_AVAILABLE: 48
- PATH_PROXY_FAVORABLE_EVIDENCE_DOMINANT: 80
- REPAIR_ONLY_FILLABILITY_SCOPE: 2

### cost_robustness_bucket
- COST_DESCRIPTOR_INVARIANT_OR_ABSENT: 2
- EXACT_SPREAD_SOURCE_STRESS: 181
- EXACT_SPREAD_SUPRA_STATIC_STRESS: 17
- SPREAD_PROXY_GRADIENT_SENSITIVE: 9
- ZERO_TO_SPREAD_DESCRIPTOR_SHIFT: 177

### source_confidence_bucket
- EXACT_SOURCE_SUPPORTED: 16
- SOURCE_CONTEXT_ABSENT: 194
- SOURCE_STRESS_OR_PROXY_DOMINANT: 176

### ambiguity_bucket
- HIGH_SAME_M15_OR_ORDERING_AMBIGUITY: 43
- NO_RECORDED_PATH_ORDERING_AMBIGUITY: 45
- SOME_SAME_M15_OR_ORDERING_AMBIGUITY: 298

## Active Next Questions

The question ledger preserves all generated question rows with affected branch IDs. It is an execution queue, not a completion packet.
