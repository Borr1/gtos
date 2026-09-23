# V121Y Stop-Hazard Pressure Fragility Repair Pre-Replay Brief

Generated: `2026-07-05T16:19:04Z`

Broker/live/final remain closed. Local replay/package authority remains full 82-sleeve authority.

## Current Completed Replay

Latest completed replay is `BROAD_LIVE_AS_IF_REPLAY_V121X_FINALIZER_FILLABILITY_TRANSFER_SCORE_REPAIR_20260514`, window `2026-05-14..2026-05-14`.

This is a bounded one-day hostile proof slice, not a full-reservoir transfer claim. V121X rows: candidate `7968`, scorecard `96`, order `54`, trade `25`, missed `7941`, bucket `433`, source universe `282`. Trade result: net `-0.78175217R`, gross/final `+1.11053495R`, expected cost `1.89228712R`, cash PnL `-83.4112076`, risk cash `2506.49700901`, W/L/F `9/16/0`.

V121X versus V121V: `24` common trades, `1` added, `0` removed. Added trade `broadorigin_54d9e14cae6740f8b91c8664@@2026-05-14T15:15:00+00:00` was GBPUSD LONG NY, rank `3`, open-reduced-risk, stop-hazard-capped, target_r `2.0`, net `-1.07428781R`.

## Active Process State

No broad replay, pytest, verifier, or git add/commit process is running.

## Baselines

| Run | Window | Trades | Net R | Gross/Final R | Cash PnL | W/L/F |
|---|---:|---:|---:|---:|---:|---:|
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V121V | 2026-05-14 | 24 | +0.29253564 | +2.11053495 | +24.60851082 | 9/15/0 |
| V121X | 2026-05-14 | 25 | -0.78175217 | +1.11053495 | -83.41120760 | 9/16/0 |

Five-day comparators are not denominator-equivalent to this one-day proof slice.

## Dirty Files / Active Changes

Current active patch files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- this root-cause map/pre-replay brief and active cursor files

The broader worktree remains dirty with unrelated route/context changes and old large-ledger deletions. Do not stage broadly.

## Subagents

- Meitner 2nd: partially incorporated/rejected. Correctly focused on risk/stop-hazard transfer, but the exact missing-TP geometry predicate is rejected for V121X because current trade rows have `take_profit_1` and `target_r=2.0`.
- Erdos 2nd: pending at brief write time.
- Tesla 2nd: pending at brief write time.
- Prior V121X findings: incorporated; finalizer fillability transfer-score alias repair was replay-proven and exposed the added rank-3 loser.

## Mismatch Map

Source-bound -> candidate: partially fixed, no V121Y candidate-generation change expected.

Candidate -> selector: partially fixed, raw/effective/materialized action split exists.

Selector -> scheduler: partially fixed, finalizer fillability aliases now affect transfer score.

Scheduler -> risk: V121Y patch. Stop-hazard pressure no longer becomes a cap unless base fragility exists. Pressure-only marketable/high-fill/high-target rows remain diagnostic.

Risk -> order: replay proof pending. Expected to change risk-expression distribution and possibly full-risk/reduced-risk split.

Order -> lifecycle -> fill: open.

Fill -> exit: open; may become next dominant issue if risk-expression release exposes larger stop-loss damage.

Ledger: patched to preserve `pressure_score_triggered`, `pressure_triggered`, `pressure_requires_base_fragility`, and `pressure_suppressed_reason`.

## Patch Batch

Highest-leverage same-root batch: stop-hazard pressure overbreadth in scheduler/risk expression.

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: config and hazard predicate.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: attribution propagation.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: corrected pressure/base-fragility contract.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: attribution preservation.

Patch classification:

- Correctness: pressure score is not sufficient for stop-hazard cap unless base fragile-stop condition is present.
- Performance: top signed candidates should not all be risk-capped to `0.10%` solely by marketable/high-fill/high-target pressure.
- Diagnostic/ledger: raw pressure and accepted pressure are separated.

## Expected Measurable Effect

- Candidate -> scorecard: same.
- Scorecard -> order: may change from risk/order finalizer consequences.
- Order -> fill: may change if released risk changes order/reallocation.
- Missed positive R: must not improve by hidden suppression.
- Missed negative R: may rise if more risk is honestly expressed.
- Trade count: likely same or modestly changed.
- Net/gross/final R: may improve or worsen; if worse, inspect exit/stop root next.
- W/L/F: report separately.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: expected to move away from blanket `open-reduced-risk` if no other gates block full risk.

## Proof Criteria

Helped: V121Y shows pressure-only rows with `pressure_score_triggered=true`, `pressure_triggered=false`, `pressure_suppressed_reason=stop_hazard_pressure_requires_base_fragility`; not every filled row is stop-hazard-capped reduced-risk from pressure alone; zero executed cost-refused/source-gap; added/removed trades attributed.

Failed: all rows remain capped with only pressure conditions and no base fragility, or downstream ledgers lose the new pressure fields.

Exposed next flaw: full-risk/risk-expression release worsens R via stop-loss or exit behavior. That is not a reason to revert the truth repair; it points to the next exit/stop/fill-realism batch.
