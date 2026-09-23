# V105 Predecision Source-Field + M1 Profit-Harvest Authority Pre-Replay Brief

Generated: 2026-07-03T18:13:42Z

## Current Process State

- No broad replay is running.
- Context OS catalog was rebuilt at 2026-07-03T17:49:37Z and a task pack was generated at 2026-07-03T17:50:22Z.
- Stale partial prefix `BROAD_LIVE_AS_IF_REPLAY_SOURCEFIELD_M1_PROFIT_HARVEST_V105_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID` is labeled `interrupted_partial_not_final_proof` and is superseded because a scheduler-row / allocator decision-input projection leak was found before proof completion.
- Broker/live/final remain false. Local replay/package authority remains full.

## Latest Completed Replay Evidence

- V104 19D non-May holdout tail prefix `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260619_INDEX_OMIT`: 112 trades, +14.66106256 net R, +23.29090562 gross/final R, cash +2266.04219515, W/L/F 51/61/0, 23 expired unfilled. Exact-window denominator: 535522.2063862989 source-bound R, 1101 package axes, 944 candidate-generated axes, 56 scorecard/order axes, 52 filled axes, 12.97951364 actual executable R.
- V104 5D hostile prefix `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260513_20260517`: 49 trades, +25.69434914 net R, W/L/F 28/21/0, 6 expired, zero cost-refused/source-gap executions, zero degraded passive distance-breach executions.
- V97 5D hostile comparator prefix `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, cash +4461.09800786, W/L/F 23/24/0, 51 expired. Candidate rows and scorecards matched V92 at 25006 and 288.
- V92 5D hostile baseline prefix `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, cash +6228.63096022, W/L/F 37/14/0, 62 expired.

## Baseline Comparison

- V97 vs V92: trades -4, net R -15.45942505, gross/final R -15.6932219, wins -14, losses +10, expired -11, scorecards unchanged, order rows -21, order events -43.
- V97 added 19 trades worth +0.99594545R and removed 23 V92 trades worth +13.53876156R. Added transfers are net positive but weak; removed transfers were much stronger. Added-minus-removed is -12.54281611R.
- V97 preserved candidate generation but weakened downstream scheduler/order/fill transfer and lost lifecycle/exit-rich V92 behavior.
- V104 hostile improved over V97 by +11.79807183R but still trails V92 by -3.66135322R.
- V104 19D is positive but weak versus its exact-window source-bound denominator; it is not a full-reservoir conversion claim.

## Dirty Files / Active Changes

- Dirty tree is broad and predates this V105 batch. Current tracked dirty code includes the broad replay harness, selected package bridge, verifier, selector, scheduler, reduced-risk action contract, timewarp loop, Context OS, and tests.
- This V105 batch will touch only `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, focused tests, and possibly scheduler tests if the source-field preservation needs scheduler-side assertion.
- Large deleted research JSONL files remain unrelated cleanup dirt and are not part of this patch proof.

## Subagent Findings

- Newton the 3rd: incorporated. V104 19D completed with 75911 candidates, 1056 scorecards, 138 order ids, 112 fills, +14.66106256R net, and zero refused/source-gap executions. Main leak is finalizer/order transfer plus large missed opportunity.
- Kierkegaard the 3rd: incorporated. Candidate generation is not the choke; finalizer selects only 138 order ids from 1056 scorecards and all terminal orders are open-reduced-risk. Do not loosen broker cost globally.
- Locke the 3rd: incorporated. Profit-harvest is present as diagnostics in V104 but not bound to headline because `m1_proxy_replay_headline_allowed` is hardcoded false despite runtime replay-only authority.
- Hume the 3rd: incorporated. V97 is worse than V92 because it displaces stronger V92 lifecycle/exit trades; candidate and scorecard counts are unchanged.
- Pasteur the 3rd: incorporated. Candidate enrichment and post-geometry preservation exist, but compact `source_fields`, M15 OHLC, and predecision current-price fields still had to be projected into `scheduler_row`, `scheduler_candidate_decision_inputs`, and allocator `score_components.candidate_decision_inputs`.
- Parfit the 3rd: incorporated. Use the existing V97/V92 comparator as bounded hostile evidence, then prove V105 first with a targeted 2026-06-01..2026-06-06 USOIL_cash/UKOIL_cash/XAUUSD smoke before broader non-May fullgrid replay.

## Known Mismatch Classes

- Source-bound -> candidate: not current choke. V92/V97 candidates are identical and V104 generates 944/1101 package axes in the exact window.
- Candidate -> selector: partially fixed. Expected-net/probability/source-completeness propagation exists, but missed rows remain dominated by selector-not-risk-bearing/cost-failed families.
- Selector -> scheduler -> risk finalizer: open major bottleneck. V104 transfers 944 candidate-generated axes to only 56 scorecard/order axes.
- Predecision source fields -> scheduler/order quality: patched pending targeted replay. Closed-M15 source fields now survive geometry and are transferred into scheduler rows, scheduler candidate decision inputs, candidate decision inputs, and allocator score components so immediate-marketable entry quality, scorecard, and pre-risk finalizer can consume the same source-safe payload.
- Risk -> order/fillability: partially fixed. Refused cost/source-gap executions and degraded passive distance-breach executions remain zero.
- Lifecycle/fill/exit: open material leak. Profit-harvest/protective-stop paths are diagnostic-only in V104 and V97 lost V92 profit-harvest trade value.
- Ledger/verifier: needs V105 update after code patch to prove source-field and profit-harvest authority truth.

## Highest-Leverage Same-Root Batch

Batch: `v105_predecision_sourcefield_and_m1_profit_harvest_authority_repair`.

Affected files/components:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: preserve enriched predecision fields across candidate geometry replacement; transfer compact predecision source fields into scheduler-facing decision inputs; replace hardcoded M1 proxy headline false with replay-only authority predicate.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: carry source-safe predecision payload from scheduler metadata into signed authority inputs and score components.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: focused tests for source-field preservation, scheduler decision-input transfer, and M1 replay-only authority.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: focused test for allocator score-component projection.

Patch types:

- Predecision field preservation: correctness repair.
- Scheduler/allocator decision-input projection: correctness repair.
- M1 profit-harvest replay-only binding: correctness and executable-value repair.
- Tests/brief/map: diagnostic/ledger repair supporting deterministic replay.

## Expected Measurable Effect Before Replay

- Candidate -> scorecard transfer: no intended broad candidate inflation.
- Scorecard -> order transfer: should improve for rows previously blocked by immediate-marketable entry-quality field loss.
- Order -> fill transfer: may improve via source-safe immediate-marketable limit routing.
- Missed positive R: should decrease if marketable/profit-harvest opportunities become executable.
- Missed negative R: may also decrease; this is not accepted as positive-by-suppression.
- Trade count: may increase or shift; not proof alone.
- Net/gross/final R and W/L/F: targeted rows should improve or expose the next deeper leak.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: no risk authority loosening in this batch.

## Replay Proof Rule

- Focused compile/tests passed: `py_compile` for timewarp/scheduler/harness; 7 selected timewarp tests; 1 selected scheduler projection test.
- Run targeted bucket/projection replay first for M1 profit-harvest diagnostics and immediate-marketable source-field failures.
- Run 5-day hostile and one non-May objective replay only after targeted proof passes or if the patch affects behavior too globally to isolate.
- This V105 smoke proves or disproves local repair behavior. It does not prove total 1.249M reservoir conversion.
