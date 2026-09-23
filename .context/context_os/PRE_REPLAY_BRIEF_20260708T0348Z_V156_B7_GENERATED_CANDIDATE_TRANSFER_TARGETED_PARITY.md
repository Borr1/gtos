# Pre-Replay Brief - V156 B7 Generated-Candidate Transfer Targeted Parity

Generated UTC: 2026-07-08T03:48:14Z

## Current Latest Completed Replay

- Latest behavior prefix: `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`
- Window: 2026-06-01..2026-06-05 targeted B7 local proof slice.
- Candidate rows: `6633`
- Scorecard rows: `480`
- Order event rows: `13`
- Terminal order rows: `6`
- Filled orders / trade rows: `3`
- Expired unfilled orders: `3`
- Missed opportunity rows: `6627`
- W/L/F: `3/0/0`
- Net / gross / final R: `0.84449709 / 1.09529478 / 1.09529478`
- Cash PnL: `211.19447407`
- Risk cash / risk pct sum: `750.42443587 / 0.75`

This is bounded local behavior evidence only. It is not full-reservoir transfer evidence.

## Running Process State

No broad replay, verifier, pytest, or route builder process was active when this brief was written. A transient external git diff helper had completed before git fetch and route reads proceeded.

## Baselines

- V89D/V90/V92 remain historical hostile/comparator baselines from the Fable ladder and earlier matrices; they are not the denominator for this targeted V156 parity rebuild.
- V150 remains the latest same-window behavior baseline for the 2026-06-01..2026-06-05 targeted slice.
- V155 is the latest same-window source-bound parity baseline:
  - parity rows: `5461`
  - source member axes: `1101`
  - source axes with exact package candidate match: `65`
  - candidate-generated axes: `842`
  - candidate-not-generated axes: `259`
  - scheduler option present count: `553`
  - order present count: `0`
  - trade count: `0`
  - diagnostic reservoir source-bound R: `1249248.03066685`

## Dirty Files And Active Code Changes

Current scoped change before the targeted builder:

- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260708.md`: refreshed current disk/process state and next proof scope.
- `.context/context_os/PRE_REPLAY_BRIEF_20260708T0348Z_V156_B7_GENERATED_CANDIDATE_TRANSFER_TARGETED_PARITY.md`: this brief.

Pre-existing unrelated dirty files remain in Context OS/config/science-ledger cleanup surfaces and are not part of this checkpoint unless current evidence makes them route-owned.

## Subagent Findings

- Avicenna: INCORPORATED. V153 residual source audit; V154/V155 confirmed selected-package source materialization residuals must not be force-materialized.
- Lagrange: INCORPORATED. Pair-broadcast lifecycle context and missing row-bound label-to-axis evidence; diagnostic split is represented in V154/V155.
- Averroes: INCORPORATED. V155 residual source-evidence audit found zero honest residual hits across selected-package, pending-created, M15 expansion, M15 all-symbol, and ultimate replay-authority ledgers.
- Zeno: INCORPORATED. V155 producer audit identified member-axis alias producer/consumer contract leak; V155 repaired it.
- Halley: DEFERRED/NO EVIDENCE. Closed before returning a completed result.
- Earlier Goodall/Kepler/Popper B7 findings: INCORPORATED where reflected in V145-V150 patches and tests; superseded by current V154-V156 disk evidence for selecting the next batch.

## Known Mismatch Classes

- Source-bound -> candidate: residual `98` selected-package source materialization rows are now classified as non-generatable from current selected-package/pending/M15/ultimate evidence; V156 repaired boolean source-bound authority so exact signed identity is required for executable package source-bound truth.
- Candidate -> selector: generated axes still include selector reject/reduce-risk rows that may have insufficient selector/scheduler transfer attribution in V155.
- Selector -> scheduler: V155 open buckets include `64` generated-not-scheduler-selected axes, `7` generated reduce-risk-not-scheduler-selected axes, and `6` selector rejects.
- Scheduler -> risk: V156 should prevent boolean-only/source-gap/cost-refused rows from becoming executable while preserving scoreable missed opportunity rows.
- Risk -> order: no V156 runtime replay yet; order-present count remains from V150 behavior proof.
- Order -> lifecycle/fill/exit: no V156 runtime replay yet; unchanged until a runtime consumer changes.
- Ledger/verifier: V156 focused tests and verifier were green; parity artifacts still need regeneration under the V156 code contract.

## Status

- DONE: B0, B1, B2, B5.
- DONE WITH LABEL: B3, B4, B6.
- PARTIAL: B7.
- OPEN: B8.

## Highest-Leverage Same-Root Batch

Batch: `B7_generated_candidate_selector_scheduler_transfer_targeted_parity_rebuild`.

The first action is behavior-neutral parity materialization, not broad replay:

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py \
  --broad-prefix BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED \
  --artifact-tag V156_B7_PACKAGE_SOURCE_BOUND_AUTHORITY_CONTRACT_20260601_20260605_TARGETED
```

## Affected Files/Components

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/*V156_B7_PACKAGE_SOURCE_BOUND_AUTHORITY_CONTRACT_20260601_20260605_TARGETED*`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260708.md`
- Current V156 code consumers already committed in `src/components/ultimate_candidate_package.py`, `src/research/moonshot_scheduler_v4_best_trade_allocator.py`, and `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.

## Patch Type

- Matrix/brief update: diagnostic/control repair.
- Targeted parity rebuild: diagnostic/proof surface.
- No behavior-changing runtime patch should occur unless the V156 parity rebuild exposes a concrete producer/consumer defect.

## Expected Measurable Effect Before Runtime Replay

- Candidate -> scorecard transfer: no runtime behavior change expected.
- Scorecard -> order transfer: no runtime behavior change expected.
- Order -> fill transfer: no runtime behavior change expected.
- Missed positive/negative R: bucket attribution may change only where V156 authority truth changes row classification.
- Trade count, net/gross/final R, W/L/F: no change expected because no runtime replay is being run.
- Cost-refused/source-gap execution: must remain `0` executable.
- Risk-reduced/full-risk distribution: no runtime change expected.
- Generated-candidate buckets should either shrink due correct authority reclassification or gain more exact selector/scheduler deviation labels for the next code patch.

## Success / Failure Criteria

Helped:

- V156 parity artifacts materialize cleanly.
- Broker/live/final remain false.
- REFUSED/source-gap/unfillable/off-authority rows remain non-executable.
- Generated-candidate transfer buckets are measured with exact counts/R and the next code patch is selected from current V156 buckets.

Failed:

- Parity builder fails or emits schema/verifier regressions.
- V156 authority repair admits broker-cost REFUSED/source-gap rows as executable.
- Generated-candidate buckets lose attribution or are silently suppressed.

Next deeper flaw:

- If bucket counts remain unchanged and attribution is sufficient, the next code patch moves to selector/scheduler/risk transfer consumers rather than source materialization.
