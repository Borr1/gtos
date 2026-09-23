# V102 Pre-Replay Brief - Stop-Hazard Block Repair

Generated: 2026-07-03T12:15Z

## Current Completed Replay And Numbers

- V101 non-May `BROAD_LIVE_AS_IF_REPLAY_STOP_HAZARD_CAP_RANK_REPAIR_V101_20260601_20260605`: behavior-identical to V100. 67 trades, +3.79682093 net R, +8.60745638 gross/final R, W/L/F 30/37/0, 26 expired unfilled.
- V101 versus V100: 0 added trades, 0 removed trades, +0.0 net R delta.
- V101 confirmed the score-penalty patch was applied: all-threshold stop-hazard selected rows carried `predecision_stop_hazard_guard_score_penalty=1.25` and lower scheduler scores, but still ranked high enough to fill.
- This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

## Process State

- No broad replay, parity builder, comparator, pytest, or compile process is running.
- Broker/live/final remain false.

## Baseline Comparison

- V97 non-May: 62 trades, +2.21033496 net R, +7.10115419 gross/final R, W/L/F 28/34/0, 68 expired unfilled.
- V98 non-May: 48 trades, +4.65521903 net R, +8.38946808 gross/final R, W/L/F 23/25/0, 8 expired unfilled.
- V100/V101 non-May: 67 trades, +3.79682093 net R, +8.60745638 gross/final R, W/L/F 30/37/0, 26 expired unfilled.
- V100/V101 versus V98: +19 trades, -0.85839810 net R, +0.21798830 final R, W/L +7/+12/0, expired +18. Added trades +1.08080190R, removed trades +1.93920000R.

## Root Evidence For This Batch

- V100/V101 non-May stop closes: 30 rows, -32.14113976R, 0/30 winners.
- All-threshold stop-hazard class in V100/V101 non-May: 7 rows, -7.35366167R, 0/7 winners.
- All-threshold stop-hazard class in V100 hostile: 1 row, -1.09623503R, 0/1 winners.
- Two-condition stop-hazard rows are not safe to block globally because non-May had 12 two-condition targets for +25.58704815R. V102 blocks only the existing all-threshold class.

## Patch Batch

- `run_broad_live_as_if_replay_harness.py`: repaired profile now sets `scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_action = "block"`.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: retained V101 correctness repair so capped hazards apply score penalty when a profile chooses `cap`.
- `tests/test_broad_replay_repair_config.py`: repaired profile asserts block action and 1.25 score penalty.
- Existing scheduler tests continue to prove cap semantics when explicitly configured.

Classification: correctness/performance repair. It is causal and predecision-only: unit-risk ATR, distance-to-limit risk, limit-fill probability, and action intent. It is not a symbol/date/session loss bucket.

## Expected Measurable Effect

- Candidate and scorecard rows should remain stable around 35191 and 480.
- All-threshold stop-hazard filled rows should fall from 7 to 0 on the non-May window unless reintroduced through a different action path.
- Trade count may fall by up to 7 or reallocate to next-best candidates.
- Net R should improve over V100/V101 if those all-threshold hazards were not replaced by worse rows.
- Added/removed transfer versus V100 should explain whether improvement came from blocking losers or from reallocation.
- Missed negative R should capture the blocked all-threshold hazards; missed positive R must be monitored so this is not positive-by-suppression.
- Cost REFUSED/source-gap execution must remain zero.

## Success And Failure Criteria

- Helped: V102 improves over V100/V101 and V98 non-May, all-threshold hazard fills go to zero, and added/reallocated rows are not worse than the blocked stops.
- Failed: V102 merely removes trades while net R does not improve, or reallocation introduces equal/worse losses.
- Exposes next flaw: if V102 improves but still underperforms because two-condition stops dominate, the next step is a richer predecision hazard model rather than broad threshold blocking.
