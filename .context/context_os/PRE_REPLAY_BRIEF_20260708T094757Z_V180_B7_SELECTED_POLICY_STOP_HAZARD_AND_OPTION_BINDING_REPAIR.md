# V180 B7 Pre-Replay Brief - Selected Policy Stop-Hazard And Option Binding Repair

Generated UTC: 2026-07-08T09:47:57Z

## Control State

- Fable ladder active batch: B7 package replay conversion and scheduler/order/risk transfer.
- Broker/live/final: closed. Local replay/package authority: full.
- This is a targeted proof slice only: XAUUSD, 2026-06-04..2026-06-05, `repaired_package_conversion_v3`.
- No broad replay, focused test, or compile process is active before this run.

## Latest Completed Local Replay

V179 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V179_B7_SIGNED_DAILY_LOSS_LEDGER_PROJECTION_REPAIR_20260604_20260605_XAUUSD_TARGETED`

V179 local metrics:
- candidates/scorecards/orders/trades/missed/buckets: 1130 / 184 / 12 / 5 / 1124 / 28
- net/gross/final R: +0.86245094 / +1.32715957 / +1.32715957
- W/L/F: 4 / 1 / 0
- cost-refused/source-gap executed: 0 / 0
- missed positive/negative R: +61.63597461 / -184.91760067

## Incorporated Subagent Findings

- Poincare: incorporated as a safety boundary. The 219 `package_replay_order_executable_authority_missing` rows are mixed and negative in aggregate, so this patch does not broadly release them. The two scoreable raw-reject contract-passed rows at 20:30/21:00 are the target class.
- Darwin: incorporated. Exact scheduler option binding must resolve time aliases nested in `score_components.candidate_decision_inputs`, and raw-reject order-executable aliases must be recomputed after signed authority stamping.

## Patch Batch

Same-root B7 chain:
- scheduler option identity and exact instance lookup;
- selected-policy executable quality gate semantics;
- raw-reject signed order-executable alias materialization;
- order-materialization direct authority to package-new-entry alias truth.

Files:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Correctness repairs:
- Added shared exact scheduler-option time resolver and used it in selected-option lookup, ranked-option identity, scheduler option indexing, and candidate option resolution.
- Recomputed package-new-entry authority aliases after raw-reject open-reduced order-executable promotion.
- Re-synced package-new-entry order-executable aliases after final direct authority corrections so fill-floor/source/cost hard false wins over stale allowed aliases.
- Changed selected-policy stop-hazard quality gate so base-fragility-suppressed pressure is not treated as active uncapped stop hazard, while raw or non-benign pressure remains blocked.

Focused proof before replay:
- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'selected_scheduler_replacement_ids_require_exact_candidate_instance or source_bound_router_refusal_materializes_order_executable_contract or selected_policy_quality_gate_blocks_predecision_stop_hazard or selected_policy_quality_gate_allows_base_fragility_suppressed_stop_pressure or selected_policy_quality_gate_blocks_nonbenign_suppressed_stop_pressure or risk_finalizer_blocks_selected_policy_hazard_before_selection or order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority or order_materialization_surface_blocks_unresolved_fill_floor_stale_allowed or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed or risk_finalizer_promotes_exact_bound_soft_probe_runtime_and_risk_intent or risk_finalizer_keeps_non_executable_bound_all_candidate_probe_diagnostic_only' -q --tb=short`
- Result: compile passed; 9 focused tests passed, 573 deselected, 1 warning.

## Expected Measurable Effect

- Candidate -> scorecard: neutral unless exact option binding exposes a previously stale exact-instance consumer.
- Scorecard -> order: expected increase if `broadorigin_de06e049904b34e7157320bc@@2026-06-05T20:30:00+00:00` no longer fails `selected_policy_stop_hazard_pressure_suppressed_uncapped`.
- Order -> fill: expected +1 possible fill for 20:30 if downstream order/lifecycle/fillability remains valid.
- Missed positive R: expected decrease by up to +0.57190978R if 20:30 transfers.
- Missed negative R: should remain protected from the 219 broad missing-authority rows; passive-limit-too-close rows should stay blocked.
- Trade count: expected 5 -> 6 if 20:30 fills.
- Net R: expected improvement by up to +0.57190978R versus V179 if the same missed-opportunity value transfers.
- W/L/F: expected +1 winner if 20:30 fills.
- Cost-refused/source-gap execution: must remain 0 / 0.
- Risk distribution: 20:30 finalizer probe already showed `risk_decision=trade`, `final_approved_risk_pct=1.0`; filled trade should preserve provenance if it transfers.

## Success / Failure Criteria

Helped:
- 20:30 raw-reject contract-passed row no longer ends as selected-policy stop-hazard pressure suppressed uncapped.
- Any added trade/order is broker-cost passed, source-complete, fillable, and signed-authority backed.
- Cost-refused/source-gap/unresolved-fill-floor executions remain zero.

Failed:
- 20:30 remains blocked by benign suppressed stop pressure.
- Raw-reject signed aliases remain absent or stale on scorecard/order/missed rows.
- Any terminal hard blocker executes.

Exposed next blocker:
- 20:30 advances from selected-policy gate to a later order, lifecycle, fillability, or exit reason. That exact downstream reason becomes the next B7 patch target.

Not acceptable:
- Positive-by-suppression.
- Broad release of the mixed 219 missing-authority rows.
- Loosening passive-limit-too-close or broker-cost REFUSED/source-gap hard blocks.
