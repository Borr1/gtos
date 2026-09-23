# XAGUSD Fresh-OB Late-NY Tracking - 2026-05-06

## Objective

Track the May 5 XAGUSD late-NY newer-OB shift separately from the older
duplicate active OB cluster. This is shadow-only bookkeeping; it does not
change live prompts, risk, permissions, execution, order placement, canary, or
safety-gate behavior.

Promotion verdict: `NO_PROMOTION_VERDICT`

## Evidence Read

- Goal prompt: `.context/05_operations/NEXT_IMPROVEMENTS_AND_LTO031_032_GOAL_PROMPT_2026-05-06.md`
- Monitoring synthesis:
  `research/operations/GTOS_OWNER_DEEP_DIVE_MONITORING_SYNTHESIS_2026-05-06.md`
- Candidate rows: `shadow_logs/strategy_follow_candidates.jsonl`
- Candidate path rows: `shadow_logs/candidate_path_follow.jsonl`
- Opportunity cluster rows: `shadow_logs/live_candidate_opportunity_clusters.jsonl`
- Opportunity lifecycle code: `src/research_infra/live_opportunity_dedupe.py`

## Implementation

- Added `src/research_infra/xagusd_fresh_ob_late_ny.py`.
  - Parses H1 OB zone from `h1_poi_exists` verification detail.
  - Builds a signature from `symbol|side|framework|entry|zone`.
  - Finds first-seen signature time across all XAGUSD OB candidates.
  - Labels late-NY rows as old carryover, fresh new signature, or fresh
    duplicate signature.
  - Preserves near-close unresolved rows as unresolved and unscored.
- Added `scripts/backfill_xagusd_fresh_ob_late_ny.py`.
  - Writes `shadow_logs/xagusd_fresh_ob_late_ny.jsonl`.
  - Writes status JSON/MD under `research/program_control/`.
- Added `tests/test_xagusd_fresh_ob_late_ny.py`.

## Backfill Result

Command:

```text
python scripts/backfill_xagusd_fresh_ob_late_ny.py --decision-date-prefix 2026-05-05
```

Result:

- Status: `OK_FRESH_OB_LATE_NY_TRACKED_NO_OUTCOME_CLAIM`
- Rows built: `4`
- Rows appended: `4`
- Fresh-OB status:
  - `OLD_OB_DUPLICATE_CARRYOVER`: `1`
  - `FRESH_OB_LATE_NY_NEW_SIGNATURE`: `1`
  - `FRESH_OB_LATE_NY_DUPLICATE_SIGNATURE`: `2`
- Path outcomes:
  - `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`: `1`
  - `ENTRY_TOUCHED_UNRESOLVED`: `3`
- Near-close resolution:
  - `NO_RETRACE_CONTINUATION_CONTEXT_NOT_FRESH_OB_SCORE`: `1`
  - `NEAR_CLOSE_ENTRY_TOUCHED_UNRESOLVED_DO_NOT_SCORE`: `3`
- Opportunity counting:
  - `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`: `1`
  - `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE`: `2`
  - `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`: `1`

## Findings

- `XAGUSD_2026-05-05T16:15:00+00:00` is the old `75.471` OB duplicate
  carryover.
- `XAGUSD_2026-05-05T16:30:00+00:00` is the fresh `73.222` entry /
  `73.22-73.97` OB signature and is countable as a new late-NY opportunity.
- `XAGUSD_2026-05-05T16:45:00+00:00` is the same fresh signature but blocked
  by active same-symbol overlap.
- `XAGUSD_2026-05-05T17:00:00+00:00` is the same fresh signature and not
  countable as a duplicate active setup.
- All three fresh-signature rows are `entry_touched_unresolved` by the close;
  none are wins, losses, or promotion evidence.

## Verification

- `python -m py_compile src/research_infra/xagusd_fresh_ob_late_ny.py scripts/backfill_xagusd_fresh_ob_late_ny.py` passed.
- `python -m pytest tests/test_xagusd_fresh_ob_late_ny.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase2_xagusd_fresh_ob` passed: `4 passed in 0.23s`.

## Ambiguity Status

- Does XAGUSD late-NY fresh-OB behavior repeat as a distinct lane? `OPEN`.
- This phase makes the lane trackable and prevents accidental merger with the
  older `75.471` duplicate cluster.
- The May 5 fresh-OB row is unresolved, so it cannot be scored.

NO_PROMOTION_VERDICT
