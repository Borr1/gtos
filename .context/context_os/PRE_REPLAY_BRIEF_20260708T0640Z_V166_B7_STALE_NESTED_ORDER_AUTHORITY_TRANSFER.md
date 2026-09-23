# V166 B7 Stale Nested Order Authority Transfer Pre-Replay Brief

Generated: 2026-07-08T06:40Z

Scope: Fable B7 targeted runtime proof only. This is a bounded XAUUSD
2026-06-04..2026-06-05 proof slice, not a full-reservoir conversion claim.

## Current Batch

- Matrix status: B0/B1/B2/B5 done, B3/B4/B6 done-with-label, B7 partial,
  B8 open.
- Active same-root batch: scheduler/order/risk transfer for signed,
  cost-passed, source-bound package candidates.
- Broker/live/final: false. Local replay/package authority: full.

## Latest Completed Targeted Evidence

V150 local behavior baseline, five-symbol 2026-06-01..2026-06-05:
- candidates 6633; scorecards 480; order rows 13; trades 3; W/L/F 3/0/0;
  net/gross/final R 0.84449709/1.09529478/1.09529478; cash PnL 211.19447407.

V165 XAUUSD 2026-06-04..2026-06-05:
- candidates 1130; scorecards 184; order rows 1; trades 0; W/L/F 0/0/0;
  net/gross/final R 0/0/0.
- The three V150 XAUUSD winner candidate IDs were still missed:
  `broadorigin_62cb335107ef114d9725321c`,
  `broadorigin_e59c330b1467251e45c3fd09`,
  `broadorigin_a143179e468040fcc9bd5c71`.
- V165 blocker: candidate rows had current signed package/order authority, but
  scheduler scorecard/missed consumers carried stale nested false inputs:
  `package_fill_floor_quality_not_met:off_configured_session_requires_explicit_off_session_authority,fill_probability_below_execution_authority_floor`
  and `raw_reject_order_executable_promotion_contract_missing`.

## Current Patch

Files changed:
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Correctness repairs:
- Raw-reject promotion failure lists now preserve explicit current empty lists
  instead of falling through to stale nested failure lists.
- Package order-executable input priority now reads current candidate/package
  authority before nested decision inputs, and lower-priority false inputs do
  not override an earlier explicit current authority decision.

Focused proof before replay:
- `py_compile` passed for scheduler and scheduler tests.
- Scheduler focused tests passed: 4/4.
- Scheduler selected-bridge/order-executable focused tests passed: 5/5.
- Broad repair config focused tests passed: 2/2.
- Direct current-code probe on the three V165 watch rows:
  all are runtime-eligible, order-executable, approved at 0.25 risk, and have
  zero vetoes.

## Expected Replay Effect

Target prefix:
`BROAD_LIVE_AS_IF_REPLAY_V166_B7_STALE_NESTED_ORDER_AUTHORITY_TRANSFER_REPAIR_20260604_20260605_XAUUSD_TARGETED`

Expected if helped:
- The three watch candidates advance beyond scorecard/missed into order/fill, or
  expose a later lifecycle/fill/exit blocker with exact reason.
- Trade count should move from V165 0 toward V150 local 3.
- Net R should move from V165 0 toward V150 local +0.84449709 if the same rows
  fill and exit similarly.
- Cost-refused/source-gap execution remains 0.
- Improvement must be transfer/reallocation/order authority, not opportunity
  suppression.

Expected if failed:
- Watch rows still show stale nested order/fill-floor blockers or risk remains
  zero despite current authority.

Expected if next blocker exposed:
- Watch rows become order-authorized but fail at lifecycle, same-symbol,
  fillability, terminal binding, or exit with deterministic blocker fields.
