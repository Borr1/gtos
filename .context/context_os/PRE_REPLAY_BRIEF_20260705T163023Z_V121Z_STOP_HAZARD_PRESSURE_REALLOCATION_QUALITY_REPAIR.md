# V121Z Stop-Hazard Pressure + Reallocation-Quality Pre-Replay Brief

Generated: `2026-07-05T16:30:23Z`

Broker/live/final remain closed. Local replay/package authority remains full 82-sleeve authority.

## Current Completed Replay

Latest completed replay is `BROAD_LIVE_AS_IF_REPLAY_V121X_FINALIZER_FILLABILITY_TRANSFER_SCORE_REPAIR_20260514`, window `2026-05-14..2026-05-14`.

This is a bounded one-day hostile proof slice, not a full-reservoir transfer claim. V121X rows: candidate `7968`, scorecard `96`, order `54`, trade `25`, missed `7941`, bucket `433`, source universe `282`. Trade result: net `-0.78175217R`, gross/final `+1.11053495R`, expected cost `1.89228712R`, cash PnL `-83.41120760`, risk cash `2506.49700901`, W/L/F `9/16/0`.

V121X versus V121V: `24` common trades, `1` added, `0` removed. Added trade `broadorigin_54d9e14cae6740f8b91c8664@@2026-05-14T15:15:00+00:00` was GBPUSD LONG NY, rank `3`, open-reduced-risk, stop-hazard-capped, target_r `2.0`, net `-1.07428781R`.

## Active Process State

No broad replay, pytest, verifier, or git add/commit process is running. Three stale app `git diff --numstat` helpers were terminated before this patch batch.

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

- Erdos 2nd: incorporated/deferred. V121X added exactly one loser versus V121V; that row was missed negative in V121V, not a positive missed opportunity. Not-top stop-hazard-capped reduced-risk subset is losing. Close-and-reverse/lifecycle attribution remains open after this patch.
- Meitner 2nd: partially incorporated/rejected. Correctly focused on risk/stop-hazard transfer, but the exact no-TP predicate is rejected because V121X rows have `take_profit_1` and `target_r=2.0`.
- Tesla 2nd: incorporated. Negative reallocation quality was still marked eligible downstream; scheduler and timewarp finalizer now block that path and preserve hard failures.

## Mismatch Map

Source-bound -> candidate: partially fixed, no V121Z candidate-generation change expected.

Candidate -> selector: partially fixed, raw/effective/materialized action split exists.

Selector -> scheduler: partially fixed, finalizer fillability aliases now affect transfer score.

Scheduler -> risk: V121Z patch. Stop-hazard pressure no longer becomes a cap unless base fragility exists, and negative reallocation quality is non-promotable.

Risk -> order: replay proof pending. Expected to change risk-expression distribution and block invalid finalizer reallocation.

Order -> lifecycle -> fill: open; close-and-reverse/lifecycle remains a likely next root.

Fill -> exit: open; may become dominant if risk-expression release exposes larger stop-loss damage.

Ledger: patched to preserve raw/accepted pressure fields and reallocation eligibility/hard failures.

## Patch Batch

Highest-leverage same-root batch: risk-expression and finalizer reallocation authority parity.

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: stop-hazard pressure predicate and reallocation-quality diagnostic.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: attribution propagation and finalizer quality gates.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: pressure/base-fragility and negative reallocation diagnostics.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: pressure attribution, reallocation candidate block, and zero-trade score-handoff block.

Patch classification:

- Correctness: pressure score is not sufficient for stop-hazard cap unless base fragile-stop condition is present; negative/ineligible reallocation quality cannot be promoted or converted downstream.
- Performance: top signed candidates are no longer automatically reduced solely because they are marketable/high-fill/high-target; weak fallback/reallocation rows should not displace stronger executable candidates.
- Diagnostic/ledger: raw pressure and accepted pressure are separated; reallocation eligibility and hard failures are preserved.

## Expected Measurable Effect

- Candidate -> scorecard: same.
- Scorecard -> order: may change because finalizer should stop negative-quality reallocation while pressure-only cap loosens.
- Order -> fill: may change if risk/order finalizer reallocates differently.
- Missed positive R: must not improve by hidden suppression.
- Missed negative R: should include refused/ineligible negative reallocation rows as missed diagnostics.
- Trade count: likely same or modestly changed.
- Net/gross/final R: may improve or worsen; if worse, inspect exit/stop/fill/lifecycle next.
- W/L/F: report separately.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: should separate legitimate reduced-risk rows from full-risk signed rows if no other gate caps them.

## Proof Criteria

Helped: V121Z shows pressure-only rows with `pressure_score_triggered=true`, `pressure_triggered=false`, `pressure_suppressed_reason=stop_hazard_pressure_requires_base_fragility`; negative/ineligible reallocation-quality rows are not selected; zero executed cost-refused/source-gap; added/removed trades attributed.

Failed: all rows remain capped with only pressure conditions and no base fragility, or negative/ineligible reallocation-quality rows still execute.

Exposed next flaw: risk expression is truthful but R worsens through stop-loss, exit, fill, lifecycle, or close-and-reverse behavior. That is not a reason to revert this truth repair; it points to the next targeted batch.
