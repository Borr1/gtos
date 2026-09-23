# V121X Finalizer Fillability Transfer-Score Repair Pre-Replay Brief

Generated: `2026-07-05T15:48:05Z`

Broker/live/final remain closed. Local replay/package authority remains full 82-sleeve authority.

## Current Completed Replay

Latest completed replay is `BROAD_LIVE_AS_IF_REPLAY_V121V_SCHEDULER_REALLOCATION_VALUE_MODEL_REPAIR_20260514`, window `2026-05-14..2026-05-14`.

This is a bounded one-day hostile proof slice, not a full-reservoir transfer claim. It is behavior-neutral versus V121U: candidate `7968`, scorecard `96`, order `51`, trade `24`, missed `7942`, bucket `434`; net `+0.29253564R`, gross/final `+2.11053495R`, cash PnL `+24.60851082`, risk cash `2406.04506533`, W/L/F `9/15/0`, expected cost `1.81799931R`. All filled trades remain reduced/open-reduced risk.

Same-window transfer denominator: `1101` source axes, `848` candidate-generated axes, `299` scheduler-option-present axes, `25` scorecard-selected axes, `23` axis-attributed trades, `239087.650287501R` source-bound R inside this replay window, `0.0348003R` axis-attributed actual R.

## Active Process State

No broad replay, pytest, verifier, or git add/commit process is running.

## Current Patch

Root issue: finalizer admission ranking read finalizer expected R, probability, source completeness, and risk fields, but did not read the matching finalizer-materialized execution fillability alias. Valid candidates therefore carried `causal_finalizer_candidate_fill_probability` on probe rows while `finalizer_admission_expected_transfer_score` stayed `0.0`, causing extra-slot/finalizer rows to fail as `expected_transfer_score_below_floor`.

Production repair: `source_bound_execution_fill_probability_with_source()` now accepts `risk_finalizer_execution_fill_probability` and `causal_finalizer_candidate_fill_probability` only when source/authority metadata proves they are source-bound execution fillability. Generic candidate fill probability remains non-authoritative.

Direct contract check: the sample row with expected net `0.95`, probability `0.82`, fillability `0.88`, source completeness `1.0`, and risk `0.35` now returns `finalizer_admission_expected_transfer_score=0.239932` instead of `0.0`.

## Verification

- `python3 -m py_compile` on scheduler, timewarp, and denominator verifier: passed.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: `521 passed`.
- `tests/test_timewarp_scheduler_materialization.py`: `78 passed`.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: `241 passed`.
- `tests/test_denominator_to_deployment_verifier.py`: `110 passed`.
- Focused finalizer tests: `3 passed`.
- Scoped `git diff --check`: passed for touched scheduler/timewarp/verifier/test files.
- Full route verifier: not completed here. A `--help` attempt entered the full verifier and was interrupted while parsing a large denominator bridge ledger, so it is not counted as proof.

## Baseline Comparison

V89D, V90, and V92 are hostile five-day comparators, not denominator-equivalent to V121V one-day:

| Run | Window | Trades | Net R | Gross/Final R | Cash PnL | W/L/F |
|---|---:|---:|---:|---:|---:|---:|
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V121V | 2026-05-14 | 24 | +0.29253564 | +2.11053495 | +24.60851082 | 9/15/0 |

## Subagent Findings

Beauvoir 2nd: incorporated. Explicit prefixed/finalizer stop-hazard reasons outrank stale generic `risk_basis_missing` without globally trusting stale stop-hazard fields.

Halley 2nd: incorporated. Scheduler strict admission is not the defect; downstream timewarp materialization/finalizer demotes valid signed authority through stale/root-config surfaces.

Maxwell 2nd: incorporated. Raw/effective selector split is correct; strict fillability/order executable fixtures are now aligned.

## Mismatch Map

Source-bound -> candidate: partially fixed. V121V generated `848/1101` source axes.

Candidate -> selector: partially fixed. Raw/effective/materialized action split exists.

Selector -> scheduler: partially fixed. Release score no longer acts as transfer value.

Scheduler -> risk: partially fixed by signed authority adapter tests; replay proof pending.

Risk -> order: partially fixed; cost REFUSED/source-gap rows remain non-executable in tests.

Order -> lifecycle -> fill: open. No V121X replay yet.

Fill -> exit: open after authority transfer is replay-verified.

Ledger: partially fixed. Finalizer transfer-score/extra-slot fields now share the same execution fillability contract.

## Next Proof

Run a targeted V121X replay against the same one-day V121V window before any five-day or broad historical run. This smoke proves only the local repair, not total reservoir conversion.

Expected before replay:

- Candidate -> scorecard: same or slightly higher; no top-N narrowing.
- Scorecard -> order: valid signed extra-slot/finalizer rows should no longer be blocked solely by zeroed `expected_transfer_score`.
- Order -> fill: unknown until replay.
- Missed positive R: should decrease for true fillability-alias `expected_transfer_score_below_floor` buckets.
- Missed negative R: must remain scored; no suppression-only improvement accepted.
- Trade count and R: may rise or fall; pass/fail is causal transfer and attribution.
- Cost-refused/source-gap execution: must remain zero.
- Risk distribution: report full-risk vs reduced-risk; no global full-risk promotion in this patch.

Replay helps if V121X shows nonzero finalizer transfer score for valid extra-slot/finalizer candidates, fewer alias-caused `expected_transfer_score_below_floor` misses, zero executed cost-refused/source-gap rows, and causally explained added/removed trades versus V121V.

Replay fails if valid rows still show `finalizer_admission_expected_transfer_score=0.0` or extra-slot `expected_transfer_score_below_floor` despite source-bound fillability metadata.

If transfer score is repaired but R still leaks, the next root issue is lifecycle/fill/exit behavior under correct authority provenance.
