# V121E Order-Fillability Execution Authority Split Pre-Replay Brief

Broker/live/final remain closed. Local replay/package authority remains full. This is a bounded one-day truth repair proof; it does not prove or disprove full reservoir transfer.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121C_SELECTOR_SCHEDULER_RISK_TRUTH_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-15..2026-05-15`
- Candidate ledger: omitted
- Scorecards / order events / unique orders / trades / missed: `96 / 26 / 13 / 4 / 8161`
- Expired unfilled: `9`
- Net R: `-3.80274600`
- Gross/final R: `-3.36900465`
- Cash PnL / risk cash / risk pct: `-947.38489674 / 995.84992526 / 1.0`
- W/L/F: `0/4/0`
- Executed REFUSED/source-gap rows: `0`

V121C did not change behavior from V120F on this one-day slice. The current patch is expected to change truth surfaces and may change behavior by removing candidate-fill optimism.

## Active Process State

No broad replay, pytest, or py_compile process is running. Stale git helper processes were killed: `git add --`, `git merge-base HEAD origin/main`, `git add -A`, and `git rev-list --count HEAD --not --remotes=origin`. The cached index had `0` staged files before this brief.

## Baseline Comparison

Do not compare this one-day proof slice directly to the global million-R reservoir. V89D/V90/V92 are hostile five-day comparators; V120F/V121C are same-day local baselines.

| Run | Window | Trades | Net R | Gross/Final R | Cash | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V120F | 2026-05-15 | 4 | -3.80274600 | -3.36900465 | -947.38489674 | 0/4/0 |
| V121C | 2026-05-15 | 4 | -3.80274600 | -3.36900465 | -947.38489674 | 0/4/0 |

## Dirty Files And Active Code Changes

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: guarded fallback now requires order-fillability authority, off-configured fallback defaults closed, M1 elapsed fallback is diagnostic-only without tick/queue proof, and pending missed attribution no longer falls back to candidate fill.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: pending exposure and execution-fill helpers no longer use candidate fill as order-fillability; package identity materialization is tightened.
- `src/components/selector_v4.py`: router-refusal origin aliases preserve raw origin families for admission parity.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`: repaired profile sets explicit order-fillability floors for fallback.
- Focused test fixtures were updated to provide `predecision_limit_fillability` only when replay authority is intended.

## Subagent Findings

- Fable audit: incorporated for this batch. The saved plan identifies fillability/reallocation truth and fill realism as core conversion roots, not paperwork.
- Banach: incorporated. The concrete bug was candidate/thesis fill acting as order-fill authority in fallback, pending exposure, and scheduler execution-fill paths.
- Prior risk/selector findings remain partially fixed and must be rechecked after V121E artifacts: raw/effective selector split, selected bridge parity, and risk ladder distribution.

## Mismatch Classes

1. Source-bound -> candidate: source-bound edge exists, but exact order-fillability proof may not materialize per row.
2. Candidate -> selector: candidate entry-quality fill and order-fillability must remain separate.
3. Selector -> scheduler: raw selector action and effective/materialized action must remain separate.
4. Scheduler -> risk: signed identity and risk authority must carry into selected-cell/risk packets.
5. Risk -> order: cost-refused/source-gap rows stay scoreable missed, never executable.
6. Order -> lifecycle: guarded fallback requires predecision order-fill proof or tick/queue proof, not candidate fill.
7. Lifecycle -> fill: M1 elapsed fallback without tick/queue confirmation is diagnostic-only.
8. Fill -> exit: replay R remains bounded proof and must be split by fill-realism authority.
9. Ledger: missed rows should expose missing order-fillability instead of flattering fills.

## Fixed / Partial / Open

Fixed in this batch:

- Candidate fill no longer bypasses guarded fallback wait ceilings.
- Missing order-fillability now emits explicit missing-source-bound reasons.
- Off-configured guarded fallback is closed by default.
- M1 fallback without tick/queue proof is diagnostic-only.
- Pending exposure no longer derives executable fillability from candidate fill.
- Scheduler execution-fill helpers return `execution_fillability_missing_source_bound_input` when order-fill proof is absent.

Partially fixed:

- Selected-package bridge identity parity and raw/effective selector provenance have focused tests but need replay artifact proof.
- Risk-expression provenance remains visible but needs full/reduced behavior counts from the run.

Still open:

- If V121E exposes mass `pending_order_fillability_missing`, the next same-root repair is source-bound order-fillability materialization, not another selector threshold tweak.
- Reallocation/fallback expiry, passive queue realism, and risk ladder proof remain Fable-plan follow-on batches.

## Highest-Leverage Same-Root Batch

Patch batch: `V121E_ORDER_FILLABILITY_EXECUTION_AUTHORITY_SPLIT`.

Affected components:

- Selector admission origin aliasing.
- Scheduler pending exposure and execution-fill authority.
- Timewarp guarded fallback, fill realism class, pending missed attribution.
- Harness repaired-profile fillability floor config.
- Focused scheduler/timewarp/selector/harness tests.

Patch type:

- Correctness repair: separates candidate entry-quality fill from executable order-fillability.
- Diagnostic/ledger repair: exposes missing order-fillability and M1 diagnostic fallback instead of letting them act as executable fills.
- Performance effect: unknown before replay; worse headline R is acceptable if it removes false fill authority.

## Expected Measurable Effect

- Candidate -> scorecard transfer: should remain comparable, but truth fields may expose missing candidate ledger materialization.
- Scorecard -> order transfer: may drop if previous orders depended on candidate-fill fallback.
- Order -> fill transfer: may drop for M1/candidate-fill-only fallback paths.
- Missed positive R: may increase under `pending_order_fillability_missing` or `execution_fillability_missing_source_bound_input`.
- Missed negative R: may also increase; compare positive and negative separately.
- Trade count: may decrease or shift.
- Net/gross/final R: may improve or worsen; correctness is the first proof target.
- Cost-refused/source-gap execution: must stay zero.
- Risk-reduced/full-risk distribution: report separately after replay.

## Replay Proof Criteria

Helped if:

- `candidate_fill_probability_fallback` disappears as order/pending execution authority.
- Missing order-fillability appears as explicit missed/diagnostic reasons.
- M1 guarded fallback without tick/queue proof is diagnostic-only.
- Explicit off-configured fallback remains closed.
- REFUSED/source-gap executions remain zero.

Failed if:

- Candidate fill still authorizes fallback fills.
- M1 fallback still produces executable fills without tick/queue proof.
- The run becomes positive only by suppressing opportunity without missed accounting.
- Cost-refused/source-gap rows execute.

Exposes next flaw if:

- Trade count falls and missed positive R moves into source-bound order-fillability gaps. In that case the next repair is source-bound order-fillability materialization and queue/fillability proof propagation.

## Next Run

Targeted proof prefix:

`BROAD_LIVE_AS_IF_REPLAY_V121E_ORDER_FILLABILITY_EXECUTION_AUTHORITY_SPLIT_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

Window:

`2026-05-15..2026-05-15`

This run is a local truth proof. It is not full-reservoir proof and must be normalized to this one-day window.
