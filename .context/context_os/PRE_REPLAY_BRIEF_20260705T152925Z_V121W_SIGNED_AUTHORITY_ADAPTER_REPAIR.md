# V121W Signed Authority Adapter Repair Pre-Replay Brief

Generated: `2026-07-05T15:29:25Z`

Broker/live/final remain closed. Local replay/package authority remains full 82-sleeve authority.

## Current Completed Replay

Latest completed replay is `BROAD_LIVE_AS_IF_REPLAY_V121V_SCHEDULER_REALLOCATION_VALUE_MODEL_REPAIR_20260514`, window `2026-05-14..2026-05-14`.

This is a bounded one-day hostile proof slice, not a full-reservoir transfer claim. It is behavior-neutral versus V121U: candidate `7968`, scorecard `96`, order `51`, trade `24`, missed `7942`, bucket `434`; net `+0.29253564R`, gross/final `+2.11053495R`, cash PnL `+24.60851082`, risk cash `2406.04506533`, W/L/F `9/15/0`, expected cost `1.81799931R`. All filled trades remain reduced/open-reduced risk.

Same-window transfer denominator: `1101` source axes, `848` candidate-generated axes, `299` scheduler-option-present axes, `25` scorecard-selected axes, `23` axis-attributed trades, `239087.650287501R` source-bound R inside this replay window, `0.0348003R` axis-attributed actual R.

## Active Process State

No broad replay, pytest, or git add/commit process is running. Beauvoir 2nd and Halley 2nd are closed and incorporated. Maxwell 2nd is still running and will be polled after the current non-overlapping patch batch.

## Baseline Comparison

V89D, V90, and V92 are hostile five-day comparators, not denominator-equivalent to V121V one-day:

| Run | Window | Trades | Net R | Gross/Final R | Cash PnL | W/L/F |
|---|---:|---:|---:|---:|---:|---:|
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V121V | 2026-05-14 | 24 | +0.29253564 | +2.11053495 | +24.60851082 | 9/15/0 |

## Dirty Files And Current Changes

The active route patch spans scheduler, timewarp, route verifier, and focused tests. There are also unrelated dirty Context OS/config/component files and deleted old large science JSONL ledgers in the worktree; they must not be reverted or staged with this checkpoint.

Active files for this batch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_timewarp_scheduler_materialization.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_denominator_to_deployment_verifier.py`

## Subagent Findings

Beauvoir 2nd, lane A: incorporated. Explicit prefixed/finalizer stop-hazard reasons must outrank stale generic `risk_basis_missing` without globally trusting stale stop-hazard fields.

Halley 2nd, lane C: incorporated into this V121W map. Current full timewarp signal at its disk snapshot was `21 failed, 500 passed`; the primary real code failure is downstream adapter demotion of valid signed package/selected authority by root config and stale scheduler-option surfaces.

Maxwell 2nd, lane B: still running. Its selector/materialization findings will be integrated when it returns, but it does not block the non-overlapping finalizer/materialization patch.

Earlier findings already incorporated or carried forward: raw/effective/materialized selector action split, release score diagnostic-only sort behavior, namespace refresh precedence, risk raw action precedence, terminal lifecycle R identity, verifier alias/breadth assertions.

## Mismatch Map

Source-bound -> candidate: partially fixed. V121U/V121V same-window generated `848/1101` source axes.

Candidate -> selector: partially fixed. Raw/effective/materialized action split exists; reason-only reduce-risk origin normalization still has a failing test.

Selector -> scheduler: partially fixed. Release score no longer acts as transfer value; selected scheduler aliases still need finalizer compatibility.

Scheduler -> risk: open. Valid signed package authority can be demoted by stale scheduler-option/root config gates.

Risk -> order: open. Fill-floor/current-config adapter blocks signed authority even when source-bound, broker-cost, and fillability proof exists.

Order -> lifecycle -> fill: open. Strict order-executable aliases are correct, but fixtures and lifecycle attribution must align with proof fields.

Fill -> exit: open after authority truth is green.

Ledger: partially fixed. Raw/effective selector and R identity propagation improved; verifier/test contracts still being aligned.

## Next Same-Root Patch Batch

Patch `signed authority adapter repair` across timewarp materialization and finalizer, with tests adjusted only where V121W intentionally changed raw/effective semantics or strict fillability proof requirements.

Patch type:

- Correctness: prefer valid signed candidate/packet authority over stale scheduler-option/root-config demotion in finalizer; map selected/package authority aliases into current-config order materialization; preserve exact decision-time backfill provenance; support finalizer extra-slot config aliases.
- Performance: restore valid package reduced/open-reduced candidates into risk/order transfer without globally opening unsafe gates.
- Diagnostic/ledger: preserve raw versus effective selector origin and lookup-source truth.

Expected before replay:

- Candidate -> scorecard: focused tests should prove signed authority rows reach scorecard/finalizer paths.
- Scorecard -> order: valid signed source-complete broker-cost-passed fillable rows should not fail with `fill_floor_open_reduced_risk_softening_disabled_by_config` unless explicit config false is authoritative.
- Order -> fill: unchanged until targeted replay.
- Missed positive R: should decrease in signed-authority/fill-floor buckets after targeted replay.
- Missed negative R: must remain scored, not suppressed.
- Trade count and R: unknown until replay; correctness may expose worse R.
- Cost-refused/source-gap execution: must remain zero executed refused/source-gap.
- Risk distribution: should become more diagnosable; broad full-risk promotion is not part of this adapter batch.

Focused proof succeeds if signed source-required lifecycle, canonical finalizer authority, reduce-risk authority, backfill identity, and extra-slot alias tests pass with py_compile green. It fails if valid signed authority is still blocked by stale root config or rejected without causal broker-cost/fillability/source-complete reason. If tests pass but targeted replay still leaks, the next root issue is lifecycle/fill/exit with correct authority provenance.
