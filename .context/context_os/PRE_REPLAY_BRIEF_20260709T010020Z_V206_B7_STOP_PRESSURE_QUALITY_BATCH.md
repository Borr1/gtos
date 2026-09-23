# Pre-Replay Brief - V206 B7 Stop-Pressure / Quality-Provenance Batch

Generated UTC: 2026-07-09T01:00:20Z.

## Current Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V205_B7_2_HOSTILE_5D_VALUE_TRANSFER_PROOF_20260513_20260517_FULLGRID`
- Window: 2026-05-13..2026-05-17 hostile bucket.
- Headline trades: 72.
- Net/gross/final R: `-5.20239659 / 0.16828289 / 0.16828289`.
- Cash PnL: `-3907.50669036`.
- W/L/F: `41/31/0`.
- Missed rows: 24,914.
- Source-bound R available in this exact window: `425161.75241648`.
- Package axes/candidate axes/scorecard-order axes/filled axes: `1101 / 894 / 43 / 37`.

## Running Process State

No broad replay, pytest, py_compile, or route verifier is intentionally running before V206 targeted proof. Recurrent Codex UI `git diff --numstat` helpers were killed when they pinned CPU.

## Baseline Comparison

- V92 same-window net: `+29.3557R`; V205 delta `-34.5581R`, with V205 adding 69 trades worth `-5.4154R` and removing 47 trades worth `+26.2946R`.
- V97 same-window net: V205 delta `-19.0987R`, with V205 adding 66 trades worth `-4.8959R` and removing 40 trades worth `+9.3000R`.
- V198 same-window net: V205 delta `-1.3621R`.
- V201 same-window net: V205 delta `+1.3454R`, but V201 was targeted and not a full broad proof.

## Current Batch

B7 same-root repair for stop-pressure authority, hazard-adjusted scheduler admission, runtime full-risk demotion, and default-confidence provenance truth.

Changed components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- Focused tests under `tests/`.

Focused proof already passed:

- py_compile for touched modules.
- 9 focused pytest cases covering route config, scheduler authority provenance, stop-pressure gate semantics, runtime risk finalizer gate, and verifier default-confidence provenance.

## Expected Measurable Effect

- Candidate -> scorecard transfer: suppressed-pressure candidates may be demoted; clean route-resolved passive candidates should remain admissible.
- Scorecard -> order transfer: rows with uncapped selected-policy stop pressure should stop binding terminal selected-policy authority or lose full-risk promotion.
- Order -> fill transfer: fewer uncapped stop-pressure fills; cost-refused/source-gap executed count should remain zero.
- Missed positive R: must be inspected; improvement by suppressing winners is failure.
- Missed negative R: expected to rise for demoted stop-pressure losers.
- Trade count: likely below V205 if reallocation cannot find cleaner alternatives.
- Net/gross/final R: should improve versus V205 if the stop-pressure bucket was the dominant leak.
- W/L/F: loss count should fall more than win count.
- Full-risk vs reduced-risk: V205 negative 14-row full-risk bucket should shrink or be demoted.

## Proof Plan

Run the smallest targeted proof first:

`BROAD_LIVE_AS_IF_REPLAY_V206_B7_STOP_PRESSURE_QUALITY_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`

Window: 2026-05-13 only, repaired profile only, compact missed ledger, omit packet sidecar.

Success:

- Focused verifier remains green on regenerated V206 artifacts.
- Net R improves versus V204/V205 one-day baseline without simply suppressing all opportunity.
- Stop-pressure rows show `pressure_requires_base_fragility=false` in repaired profile and are capped/blocked or demoted from full risk.
- Default-confidence source, if present, is visibly flagged by warning/flag fields across candidate/order/trade/missed surfaces.

Failure:

- Net worsens because winners are removed more than losers.
- Trade count collapses without missed positive R explanation.
- Cost/source REFUSED/source-gap rows execute.
- Verifier reports hidden default-confidence provenance or missing compact missed provenance.

Next after targeted proof:

- If correctness passes but value is still weak, inspect added/removed trades and top remaining losing buckets before another patch.
- If targeted proof improves and verifier is green, run hostile five-day V206 and then a non-May objective regime bucket.
