# V121AF Pre-Replay Brief

Generated: 2026-07-05T19:58:23Z

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121AE_TERMINAL_BINDING_TICK_PROVENANCE_DAILY_LOSS_DOMINANCE_SOURCE_CACHE_20260513_20260517`
- Window: 2026-05-13..2026-05-17 hostile bucket.
- Trades: 46; headline net R: 19.20145378; gross/final R: 22.480769; expected cost R: 3.27931522; cash PnL: 10438.7343719.
- W/L/F: 26/20/0. Full/reduced risk trades: 16/30.
- Stop-first: 11 trades, -11.79025217R.
- Cost-refused/source-gap executed: 0/0.

## Same-Window Transfer

V121AE parity was rebuilt after the reconciliation patch.

- Parity rows: 18,606; leakage buckets: 1,101.
- Source-bound R inside replay window: 388,818.616849148.
- Candidate-generated axes: 886.
- Scorecard/order axes: 32.
- Filled axes: 27.
- Headline replay net R: 19.20145378.
- Unique actual executable R: 21.59967027.
- Axis-attributed actual executable R: 25.59240843.
- Reconciliation status: `headline_unique_axis_r_surfaces_differ_explicit`.

This proves local hostile-window transfer accounting only. It does not prove full-reservoir conversion.

## Baselines

- V121AE vs V121AB: trades -10, net +3.8641694R; added 6/+2.35198513R; removed 16/-1.51218427R.
- V121AE vs V92: trades -5, net -10.15424858R; added 41/+16.82341422R; removed 46/+27.34036921R.

Interpretation: V121AE is a truthful stricter-replay improvement over V121AB, but it still loses to V92 headline because it removed more V92 winner R than it added. V92 optimistic fills should not be blindly restored; the transfer path needs dominance/fillability correctness.

## Subagent Findings Incorporated

- Hooke: stop-first leak is concentrated in open-reduced/router-refusal immediate fills; stop-hazard cap was risk sizing only. Incorporated via stop-hazard materialization dominance preflight and replacement-quality propagation.
- Godel: V121AE candidate generation matches V92 at 886 axes, but scheduler/materialization/fill-realism displaces V92 winners. Partially incorporated by making signed reduced-risk rows visible to dominance; allocator-level hard dominance remains open.
- Euclid: headline/unique/axis R were not explicitly reconciled. Incorporated in builder and verifier.

## Patch Batch

Correctness repairs:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: fragile stop-hazard reduced-risk immediate marketable limit routes now require reallocation dominance before order materialization.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `risk_admitted_scheduler_reallocation_*` aliases now propagate through replacement-quality ledger projection.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: signed `open-reduced-risk` / `reduce-risk` candidates with cost/source/fill/signature authority stay visible to scheduler dominance audits.

Proof repairs:

- `build_source_bound_execution_parity.py`: exact-window transfer writes headline-vs-unique-vs-axis R reconciliation.
- `verify_denominator_to_deployment_execution.py`: verifier requires reconciliation status and delta consistency.

Focused tests passed:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'stop_hazard_materialization or signed_reduced_risk_veto_visible or best_admitted_dominance'`
- `python3 -m py_compile research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py tests/test_build_source_bound_execution_parity.py tests/test_denominator_to_deployment_verifier.py`
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k exact_replay_window_transfer_contract`
- `python3 -m pytest tests/test_build_source_bound_execution_parity.py -k exact_replay_window_denominator`

## Expected Replay Effects

- Candidate -> scorecard/order transfer: should not decrease solely from signed reduced-risk dominance invisibility; stronger dominance diagnostics should expose displaced candidates.
- Scorecard/order -> fill transfer: fragile stop-hazard immediate reduced-risk fills should decline unless reallocation quality passes.
- Missed positive R: may increase if weak stop-hazard fills are correctly demoted to missed/counterfactual rows; this is acceptable if blocked rows were weak/non-dominant.
- Missed negative R: should capture newly blocked fragile stop-first candidates.
- Trade count: likely lower than V121AE if the stop-hazard gate catches immediate capped reduced-risk rows.
- Net/gross/final R: helped if stop-first losses drop more than any newly blocked winners.
- W/L/F: loss count should fall if the gate is hitting the intended stop-first leak.
- Cost-refused/source-gap execution: must remain 0.
- Risk distribution: reduced-risk immediate stop-hazard rows should split into dominance-passed fills vs blocked/missed rows.

## Prove/Fail Criteria

The next targeted hostile-5d proof helps if stop-first loss R improves, no broker-cost/source-gap row executes, and opportunity accounting shows blocked rows as scored missed opportunities rather than disappearing.

The batch fails if improvement comes only from suppressing all opportunity, if dominant valid signed candidates are blocked, or if V92-like winners still disappear without scorecard/order/missed accounting.

If it fails, the next root issue is allocator-level hard replacement dominance in `src/research/moonshot_scheduler_v4_best_trade_allocator.py` plus missing-materialization rows for the six removed V92 instances.
