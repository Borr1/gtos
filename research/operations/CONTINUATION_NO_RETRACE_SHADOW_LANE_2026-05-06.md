# Continuation/No-Retrace Shadow Lane - 2026-05-06

## Objective

Preregister and build the continuation/no-retrace shadow lane after expanding
`m15_choch_exists` diagnostics. This phase is shadow-only and does not loosen
the L2 gate or change live prompts, risk, permissions, execution, order
placement, canary, or safety-gate behavior.

Promotion verdict: `NO_PROMOTION_VERDICT`

## Evidence Read

- Goal prompt: `.context/05_operations/NEXT_IMPROVEMENTS_AND_LTO031_032_GOAL_PROMPT_2026-05-06.md`
- Execution plan: `research/program_control/NEXT_IMPROVEMENTS_RIGHT_WAY_EXECUTION_PLAN_2026-05-06.md`
- Monitoring synthesis: `research/operations/GTOS_OWNER_DEEP_DIVE_MONITORING_SYNTHESIS_2026-05-06.md`
- M15 diagnostic audit:
  `research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.md`
- Candidate rows: `shadow_logs/strategy_follow_candidates.jsonl`
- Path rows: `shadow_logs/candidate_path_follow.jsonl`
- Opportunity rows: `shadow_logs/live_candidate_opportunity_clusters.jsonl`
- Trade-record proxy source: `knowledge_base/trade_records/`

## Preregistration

Artifact:

- `research/program_control/CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md`

Registered strategy:

- `strategy_id`: `CONTINUATION_NO_RETRACE_M15_FAIL_V1`
- `preregistration_version`: `continuation_no_retrace_prereg_v1`
- Primary entry model: `CNR_E0_DECISION_CLOSE_MARKET`
- Diagnostic proxy: `CNR_E1_DECISION_PRICE_PROXY`
- Stop model: original GTOS structural `stop_loss`
- Target model: original GTOS `take_profit_1`
- Aggregate count rule: count only
  `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`

No alternate target, no threshold, and no promotion rule was selected.

## Implementation

- Added `src/research_infra/continuation_no_retrace.py`.
  - Builds eligibility from decision-time candidate/verification fields.
  - Builds candidate rows without path/outcome fields.
  - Builds resolution rows from post-decision path/opportunity joins.
  - Keeps synthetic R source-blocked unless exact decision entry price and
    ordered post-entry path data exist.
- Added `scripts/backfill_continuation_no_retrace_shadow.py`.
  - Writes `shadow_logs/continuation_no_retrace_candidates.jsonl`.
  - Writes `shadow_logs/continuation_no_retrace_resolutions.jsonl`.
  - Writes audit JSON/MD under `research/program_control/`.
- Added `tests/test_continuation_no_retrace.py`.

## Backfill Result

Command:

```text
python scripts/backfill_continuation_no_retrace_shadow.py --decision-date-prefix 2026-05-05
```

Result:

- Status: `OK_SHADOW_ONLY_SOURCE_BLOCKED_FOR_R_SCORING`
- Eligible candidates: `22`
- Candidate rows appended: `22`
- Resolution rows: `22`
- Resolution rows appended: `22`
- Distance proxy available: `21`
- Later path outcomes:
  - `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`: `19`
  - `ENTRY_TOUCHED_UNRESOLVED`: `3`
- Aggregate counting:
  - `COUNTABLE_PRIMARY_ONLY`: `2`
  - `EXCLUDED_DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE`: `19`
  - `EXCLUDED_BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`: `1`

## Findings

- The lane is now auditably separated from the live retest strategy.
- May 5 contains a meaningful fast-continuation context, but most rows are
  duplicate active XAGUSD setup evidence and are not independently countable.
- The currently available trade-record price is only a proximity proxy; it is
  not an executable quote or exact candle close.
- Synthetic R remains intentionally uncomputed for all 22 rows because exact
  decision entry price and ordered post-entry path data are not captured.

## Verification

- `python -m py_compile src/research_infra/continuation_no_retrace.py scripts/backfill_continuation_no_retrace_shadow.py` passed.
- `python -m pytest tests/test_continuation_no_retrace.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase2_continuation_no_retrace` passed: `6 passed in 0.25s`.

## Ambiguity Status

- Is `continued_without_entry_touch_to_tp_area` tradable or hindsight
  directionality? `OPEN`.
- This phase answers only that a preregistered shadow lane exists and current
  rows can classify path context and duplicate-aware countability.
- Promotion-grade R scoring is source-blocked until exact decision-entry prices
  and ordered post-entry M1/tick paths are captured.

## Remaining Blockers

- Exact decision entry price is missing from current forward candidate rows.
- Ordered M1/tick path after continuation entry is missing.
- No spread/slippage execution model is approved for continuation entries.
- No broker actual-R evidence exists for rejected L2 shadow alternatives.

NO_PROMOTION_VERDICT
