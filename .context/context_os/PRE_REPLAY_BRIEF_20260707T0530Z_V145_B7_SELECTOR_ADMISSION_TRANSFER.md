# Pre-Replay Brief - V145 B7 Selector Admission Transfer And Selected-Policy Quality

Generated UTC: 2026-07-07T05:30:00Z
Updated UTC: 2026-07-07T05:46:21Z

## Current Replay Baseline

- Latest targeted proof: `BROAD_LIVE_AS_IF_REPLAY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED`.
- V144 scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- V144 numbers: 6633 candidates, 480 scorecards, 15 orders, 3 fills, net R `+0.84449709`, gross/final R `+1.09529478/+1.09529478`, cash PnL `+84.46094125`, W/L/F `3/0/0`.
- V144 truth: executed REFUSED cost rows `0`, executed source-gap rows `0`, unsigned router-refusal executable authority predicate rows `0`.
- Latest full five-day reference remains V128, not this targeted proof: 55 fills, net R `+1.12099062`, gross/final R `+6.22739670/+6.22739670`, W/L/F `38/17/0`.

## Active Process State

- No broad replay was active before this brief.
- The only long-lived non-test processes observed were Context OS MCP sidecars and macOS `replayd`.
- Focused tests for the selector/timewarp consumer path completed before replay.

## Patch Batch

Selected Fable dependency batch: B7 transfer recovery, priority 20 selector admission calibration plus ledger consumer split, plus selected-policy stop-hazard quality gate consumer parity from Popper's returned audit.

Changed files:

- `src/components/selector_v4.py`: source-bound router-refusal package admission can materialize as open-reduced replay authority without the origin allowlist when broker-cost, source-bound, predecision quality, and final/live false gates pass.
- `tests/test_selector_v4.py`: regression for source-bound router-refusal materialization without origin allowlist.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `ledger_namespace_alias_fields()` now preserves scoreable `package_replay_candidate_use_allowed` for diagnostic source-bound package rows while keeping executable authority false until signed/materialized scheduler authority is present.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `selected_policy_executable_quality_gate_fields()` now treats suppressed score-triggered stop-hazard pressure as a causal predecision hazard; finalizer rank, soft-veto probing, finalizer selection, replay-exit, filled-trade, and missed-opportunity consumers use the same runtime thresholds.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: unsigned router-refusal executable leak scan no longer treats diagnostic `package_replay_candidate_use_allowed` as executable authority; true executable/order/replay-now aliases remain fatal.

Patch type:

- Selector change: behavior-changing correctness repair.
- Selected-policy quality change: behavior-changing correctness repair; it should demote uncapped/suppressed stop-pressure selected-policy replay authority rather than allow stop-loss-selected paths to look executable just because the direct pressure trigger was false.
- Ledger namespace split: diagnostic/proof-surface correctness repair, behavior-neutral for order execution.
- Verifier change: proof-surface correctness repair matching the diagnostic/executable split.

Subagent findings incorporated:

- Goodall: selector source-bound router-refusal materialization must use execution fillability, not entry-quality fill optimism; diagnostic candidate-use must not be treated as executable authority by the verifier. Incorporated in selector, verifier, and tests.
- Kepler: V144 priority 12/13 selected-package source/lifecycle materialization rows are diagnostic classification gaps in this slice, with zero candidate trace/source-bound/actual/missed R; no behavior patch to promote them into candidates/orders for V145.
- Popper: `selected_policy_replay:stop_loss` remained a major B7 losing bucket in V128, with 13 fills / `-14.31653698R` despite high calibrated expected net; suppressed/score-triggered stop-hazard pressure and runtime-threshold drift let fragile selected-policy rows remain executable. Incorporated in the selected-policy quality gate, finalizer rank/soft-veto/finalizer/replay-exit consumers, and focused tests. This is a causal predecision repair, not a date/symbol/session loss-bucket suppression.

Focused proof before replay:

- `python3 -m py_compile src/components/selector_v4.py src/research_infra/v4_timewarp_simulated_live_research_loop.py src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_selector_v4.py tests/test_timewarp_scheduler_materialization.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_selector_v4.py -k "source_bound_router_refusal_materializes_without_origin_allowlist or source_bound_router_refusal_respects_execution_fill_floor or package_router_refusal_softening_uses_signed_sleeve_origin" -q`: 3 passed.
- `python3 -m pytest tests/test_timewarp_scheduler_materialization.py -k "reduce_risk_numeric_open_reduced_disabled_stays_rankable_as_reduce_risk or package_positive_numeric_disagreement_reduce_risk_reaches_scheduler_with_cost_passed or nonpackage_reduce_risk_new_entry_does_not_reach_scheduler or package_positive_reduce_risk_keeps_refused_cost_blocked" -q`: 4 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "source_bound_router_refusal_materialization_uses_execution_fillability_floor or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_alias_keeps_raw_router_rejects_diagnostic_only or scheduler_backfill_refresh_restores_materialized_router_refusal_authority or package_router_refusal_authority_daily_loss_release_is_narrow_replay_path" -q`: 5 passed.
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "source_bound_router_refusal_passive_limit_queue_does_not_bypass_execution_authority_floor or package_executable_authority_accepts_strict_source_bound_aliases or selected_package_bridge_alias_alone_is_not_source_bound_authority" -q`: 3 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias or unsigned_router_refusal_diagnostic_candidate_use_is_not_executable_alias or order_transfer_scan_flags_unsigned_router_refusal_executable_alias" -q`: 3 passed.
- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "selected_policy_quality_gate or selected_execution_policy_replay_blocks_predecision_quality_failure_before_path or selected_execution_policy_replay_uses_runtime_quality_thresholds or finalizer_admission_rank_uses_runtime_selected_policy_pressure_floor or risk_finalizer_blocks_selected_policy_hazard_before_selection" -q`: 7 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "broad_selected_policy_replay_authority_flags_quality_gate_leaks" -q`: 1 passed.

## Expected Measurable Effect

- Candidate -> scorecard/order: should increase or remain stable for source-bound router-refusal rows that are broker-cost-passed, source-complete, and quality-passed.
- Scorecard/order -> fill: may increase only through signed/materialized replay authority and execution-fillability floor compliance; REFUSED/source-gap execution must remain zero.
- Selected-policy replay/exit: uncapped suppressed stop-pressure rows should become non-authoritative quality-gate blocks before path replay, reducing fragile stop-loss selected-policy fills if they appear in the targeted window; blocked rows must remain scoreable/missed with exact gate failures.
- Missed positive R: should fall if valid router-refusal source-bound opportunities transfer to order/fill, or remain visible as scheduler/lifecycle/order blockers.
- Missed negative R: must remain visible; no date/symbol/session loss-bucket suppression is allowed.
- Trade count/net R/W-L can move either way. A negative added transfer is acceptable only if it exposes the next deeper admission/exit flaw honestly.
- Full-risk/reduced-risk distribution must remain reported separately.

## V145 Success / Failure Criteria

Success:

- V145 keeps broker/live/final false and executed REFUSED/source-gap rows at zero.
- V145 preserves V144 router-refusal unsigned executable-authority zero count.
- V145 shows previously hard-rejected source-bound router-refusal candidates now become scorecard/order candidates or are classified with exact downstream blocker reasons.
- V145 either reduces selected-policy stop-hazard fills or labels them with `selected_policy_stop_hazard_pressure_suppressed_uncapped` / selected-policy quality-gate blockers in order/trade/missed surfaces, with no outcome-field use.
- Any added trades are attributed as conversion, not suppression.

Failure:

- Any REFUSED/source-gap/live/final row executes.
- Candidate scoreability disappears again through executable-authority demotion.
- Improvement comes only from trade collapse.
- Router-refusal rows remain hard-rejected with no selected scheduler/order transfer or exact downstream blocker.
- Selected-policy quality-gate blocked rows reach executable filled order/trade authority, or the selected-policy gate uses outcome fields.
