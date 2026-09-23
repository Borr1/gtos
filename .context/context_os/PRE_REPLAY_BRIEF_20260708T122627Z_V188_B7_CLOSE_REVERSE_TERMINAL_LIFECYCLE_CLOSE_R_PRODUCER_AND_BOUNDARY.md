# V188 B7 Pre-Replay Brief - Close/Reverse Terminal Lifecycle Close-R Producer + Boundary

Generated UTC: 2026-07-08T12:26:27Z

## Current Completed Replay

Latest completed targeted behavior proof:
`BROAD_LIVE_AS_IF_REPLAY_V187_B7_SIGNED_EXECUTABLE_MIXED_COOLDOWN_DAILY_LOSS_RELEASE_20260604_20260605_XAUUSD_TARGETED`

V187 bounded XAUUSD 2026-06-04..2026-06-05:

- candidate rows: 1130
- scorecard rows: 184
- order rows: 28
- trade rows: 12
- missed rows: 1116
- bucket rows: 34
- W/L/F: 9/3/0
- net/gross/final R: 2.38236699 / 3.28997321 / 3.28997321
- cash PnL: 1486.8897995
- risk cash: 7374.85152098
- risk pct: 7.375
- expected cost R: 0.90760621
- executed broker-cost REFUSED rows: 0
- executed source-gap-cost rows: 0

V187 added four winners versus V186 and removed no V186 trades, but exposed a
terminal lifecycle truth gap: close/reverse entry legs became headline filled
trades even though the required close-side open-exposure mutation did not
commit because terminal lifecycle close R was missing.

## Active Process State

No broad live-as-if replay or pytest repair run is active in this repo at
pre-brief time. Do not start a duplicate replay; V188 is the next allowed
targeted proof after focused tests.

## Baseline Comparison Anchors

- V184: `1130/184/17/8/1121/31`, net/gross/final R
  `0.50779951/1.12248313/1.12248313`; added one broker-cost-passed
  source-complete SHORT winner and removed no V183 trades.
- V185: behavior-neutral versus V184, but moved the 17:45 close/reverse row to
  scheduler materialized rank 1.
- V186: behavior-neutral versus V185, but exposed runtime risk cooldown and
  daily-loss conflict handling.
- V187: `1130/184/28/12/1116/34`, net/gross/final R
  `2.38236699/3.28997321/3.28997321`; added four winners and removed no V186
  trades, while exposing the close/reverse terminal lifecycle close-R truth gap.

## Subagent Findings

- Erdos: INCORPORATED. V187 has 6 suspect order rows and 3 lifecycle-related
  suspect trade rows. `trade:000007` and `trade:000008` contribute
  `0.84363023R` final R while close/reverse mutation is not committed due to
  `not_committed_scheduler_close_and_reverse_close_r_missing`.
- Laplace: INCORPORATED. The root producer gap is that the mutator already
  requires `terminal_lifecycle_close_*` fields, but no runtime code stamps
  those fields from as-of source truth onto the open exposure before
  close/reverse mutation.
- Rawls: PENDING. Not required to block V188 because Erdos/Laplace/local disk
  evidence already identifies and tests the current same-root B7 batch.

## Root Mismatch Class

Pipeline stage:
source-bound replay rows -> open exposure terminal close mark -> scheduler
terminal lifecycle mutation -> reverse-entry materialization -> order/fill ->
trade ledger.

Mismatch:
close/reverse new-entry materialization had a consumer-side mutation contract,
but the close-side producer was absent. That allowed two bad outcomes:

- when source truth existed, the old leg could fail to close because close R was
  never stamped onto the open exposure;
- when source truth did not exist, the reverse entry could still become a
  headline fill even though required close-side lifecycle mutation was deferred.

## Code Changes Under Test

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
  - Adds `materialize_terminal_lifecycle_close_r_from_source(...)`.
  - Calls the producer immediately before close/reverse open-exposure mutation.
  - Stamps close gross R, close expected cost R, close net proxy R, close mark
    time/price/source, path authority, source path/hash, and lookup metadata.
  - Prefers ordered tick truth, then labelled M1/M15 replay source/proxy
    authority.
  - Keeps source-missing close/reverse entries non-executable and scoreable as
    `terminal_lifecycle_deferred_source_gap`.
  - Prefers close-specific expected cost fields before generic lifecycle cost.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
  - Adds source-present producer-to-mutator test.
  - Retains source-missing simulate-order fail-closed test.

## Focused Proof Already Run

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Focused pytest selection:
  `terminal_lifecycle_close_r_materializes_from_ordered_tick_source`,
  `simulate_order_blocks_close_reverse_entry_when_close_side_r_missing`,
  scheduler terminal close/reverse regressions:
  `5 passed, 583 deselected, 1 warning`.

## Expected Replay Effect

Behavior-changing correctness repair.

Expected measurable effect:

- Candidate -> scorecard transfer: neutral.
- Scorecard -> order transfer: neutral unless source-missing close/reverse rows
  are demoted before pending/fill.
- Order -> fill transfer: invalid close/reverse fills without close-side
  source R should drop out of headline fills.
- Filled trades: close/reverse old-leg terminal close rows should appear when
  source-bound close R is materializable.
- Missed positive/negative R: source-missing reverse entries remain scoreable
  as missed/diagnostic, not silently removed.
- Trade count/net R/W-L can move up or down. Improvement is not defined as
  positive R alone; it is defined as committed close-side lifecycle truth and
  no headline reverse entry when required close-side mutation cannot commit.
- Cost REFUSED/source-gap execution must remain zero.

## Success / Failure Criteria

V188 helped if:

- `not_committed_scheduler_close_and_reverse_close_r_missing` decreases or is
  converted into either committed close-side trade rows with source-bound close
  R or explicit `terminal_lifecycle_deferred_source_gap` non-executions;
- no close/reverse entry is counted as a headline fill when its required
  close-side lifecycle mutation is deferred;
- source-present close/reverse old legs carry `terminal_lifecycle_close_r_*`
  provenance and realized PnL;
- executed broker-cost REFUSED/source-gap rows remain zero.

V188 failed if:

- close/reverse entry fills still appear with uncommitted close-side mutation;
- source-present old legs remain source-gapped despite available tick/M1/M15
  rows in the same replay window;
- the patch suppresses all close/reverse rows without scoreable missed
  attribution.

Next deeper flaw if exposed:

- source coverage path has no rows inside the open-leg entry-to-close window;
- open positions lack entry/stop geometry needed for close R;
- close/reverse source truth exists but is not in the same `path_sources` map
  used by runtime order simulation.

