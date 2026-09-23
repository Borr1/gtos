# Live Shadow Opportunity Dedupe Context - 2026-05-04

Status: active monitoring doctrine
Scope: shadow/follow-data reporting only
Promotion posture: NO_PROMOTION_VERDICT

## Purpose

The live-shadow system must preserve every raw candidate/path/mechanical row,
but interpretation must not count consecutive duplicate detections of the same
active setup as separate trades. Raw candidate rows are evidence. Countable
opportunity rows are the unit for trade-opportunity comparison.

This was added after the owner flagged that the 2026-05-04 XAGUSD sequence was
being over-counted as many successful candidates even though it represented
repeated detections of the same active setup with only small level drift.

## Implemented Rule

Use `shadow_logs/live_candidate_opportunity_clusters.jsonl` and count only rows
whose latest `opportunity_counting_status` is:

`COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`

Do not count rows marked:

- `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE`
- `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`

Raw rows remain append-only and should still be inspected for evidence quality,
path sequencing, source gaps, and anomaly forensics.

## Assignment Logic

Algorithm version: `active_setup_lifecycle_tolerance_v1`

Consecutive detections are grouped as one active opportunity when they share:

- same symbol family,
- same side,
- same framework,
- materially similar entry/SL/TP1 geometry.

Similarity tolerance is recorded in each row under `opportunity_similarity`.
The default floor is two pips in the instrument convention, with a small
risk-relative allowance for prompt/buffer jitter. Exact raw levels are still
preserved.

A later detection can start a new countable opportunity only when there is
lower-timeframe reset evidence that the prior opportunity had an entry touch
followed by TP/SL before the later decision. A no-entry TP-area move is not a
reset because no trade happened.

If a new opportunity overlaps an already-open same-symbol shadow trade, it is
preserved but marked `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP` rather than
counted as a separate trade.

## Reporting Rule

Use `scripts/summarize_live_shadow_opportunities.py` for comparison summaries.
That script:

- reports raw candidate count separately from countable opportunities,
- collapses duplicate active setup detections,
- excludes active same-symbol overlaps from trade counts,
- computes proxy R only for rows with `score_status=COMPUTED_FROM_CANDIDATE_PATH`,
- keeps context-only, diagnostic, not-applicable, and not-scored rows out of R.

## Current 2026-05-04 Snapshot

As of the `11:15 UTC` summary:

- Raw candidates with latest cluster rows: `17`
- Unique opportunity IDs: `5`
- Countable primary opportunities: `5`
- Not countable: `12` duplicate active setup detections
- Countable path labels:
  - `entry_touched_then_reached_tp1`: `1`
  - `continued_without_entry_touch_to_tp_area`: `3`
  - `went_through_entry_and_continued_to_sl`: `1`

Entry-model proxy R after clean counting:

- `LIVE_AI_J46_J49_BASELINE_COMPARATOR`: `+0.5R`
- `PENDING_LIMIT_LIFECYCLE`: `+0.5R`
- `V2_STRUCT_OB_BOUNDARY`: `+1.5R` over `4` R-counted rows
- `V2B_OB_BOUNDARY_PROSPECTIVE`: `+1.5R` over `4` R-counted rows

Context-only rows such as `J46_J49_PORTFOLIO_POLICY`,
`S79_UNIFORM_FN_RISK_POLICY`, and `NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC` retain
outcome labels but do not contribute proxy R.

## Validation

Targeted tests:

`python -m pytest tests\test_live_opportunity_dedupe.py tests\test_live_shadow_gap_closure.py tests\test_live_mechanical_shadow.py tests\test_live_shadow_opportunity_summary.py --basetemp C:\tmp\pytest_live_opportunity_dedupe`

Result: `17 passed`.

Integrity:

`python scripts\verify_shadow_log_integrity.py`

Result after verifier spec correction: `OK_WITH_DOCUMENTED_WAITING_LANES`,
`issues={}`.

## Monitoring Requirement

Every future live-shadow comparison must state whether it is using:

- raw candidate rows, or
- countable opportunity rows.

For performance/strategy comparison, use countable opportunities. Raw candidate
rows can support forensic review but must not be summed as trades.
