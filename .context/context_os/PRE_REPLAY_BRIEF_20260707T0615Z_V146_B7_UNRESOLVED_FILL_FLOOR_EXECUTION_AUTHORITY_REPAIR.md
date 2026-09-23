# Pre-Replay Brief - V146 B7 Unresolved Fill-Floor Execution Authority Repair

Generated UTC: 2026-07-07T06:15:00Z

## Current Replay Baseline

- Latest targeted proof: `BROAD_LIVE_AS_IF_REPLAY_V145_B7_SELECTOR_ADMISSION_TRANSFER_AND_SELECTED_POLICY_QUALITY_20260601_20260605_TARGETED`.
- V145 scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- V145 numbers: 6633 candidates, 480 scorecards, 7 finalizer terminal orders, 14 summary order rows, 3 fills, net R `+0.18335355`, gross/final R `+0.48352934/+0.48352934`, cost R `+0.30017579`, W/L/F `2/1/0`.
- V145 versus V144: net R delta `-0.66114354`, gross R delta `-0.61176544`, cost R delta `+0.04937810`, trade count delta `0`, added trades `2`, removed trades `2`, common trades `1`.
- V145 truth boundary: executed REFUSED cost rows `0`, executed source-gap rows `0`, broker/live/final rows `0`, final package selection false.
- V145 leak exposed: 8 order/trade rows across 3 unique keys carried unresolved fill-floor failures into order/trade surfaces: `fill_probability_below_execution_authority_floor` and `numeric_disagreement_fill_probability`.
- Latest full five-day reference remains V128, not this targeted proof: 55 fills, net R `+1.12099062`, gross/final R `+6.22739670/+6.22739670`, W/L/F `38/17/0`.

This V146 replay is a bounded same-window repair proof. It does not prove full million-R reservoir conversion.

## Active Process State

- No broad replay, harness, route builder, route verifier, pytest, or py_compile process was active before this brief.
- The V146 patch has focused compile/test proof before replay.

## Patch Batch

Selected Fable dependency batch: B7 transfer recovery, unresolved fill-floor execution authority repair after V145 exposed a selected-package transfer truth leak.

Changed files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: unresolved signed package fill-floor execution failures now invalidate signed reduce-risk replay authority for all signed entry intents, not only `new_position`, and explicit reduce-risk authority cannot bypass unresolved execution fill-floor failures.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: unresolved fill-floor failure keys propagate through order-materialization authority override/coupled fields.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `order_materialization_authority_candidate_surface()` keeps package rows scoreable but sets order-executable authority false when unresolved fill-floor failures are present, even if selected/risk surfaces have stale allowed aliases.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `replay_order_materialization_authority_block_reason()` returns `package_fill_floor_unresolved_executable_authority:<failures>` before stale order authority can be rederived.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `package_order_executable_final_blocker_fields()` refuses order/trade binding when unresolved fill-floor failures remain.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: unresolved fill-floor failures are extracted by a shared helper and are fatal in broad order-executable transfer and selected-package executed order/trade authority scans.
- `tests/test_timewarp_scheduler_materialization.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`, and `tests/test_denominator_to_deployment_verifier.py`: focused regression coverage for scheduler fail-closed behavior, timewarp order surface/blocker consumers, and route verifier scans.

Patch type:

- Behavior-changing correctness repair.
- It should prevent unresolved fill-floor rows from executing; that can reduce trade count or force reallocation.
- It is not a suppression proof. If V146 becomes less positive or more negative, that is acceptable if unresolved order/trade authority is truthfully closed and the next transfer/reallocation blocker is exposed.

## Focused Proof Before Replay

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py tests/test_timewarp_scheduler_materialization.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_denominator_to_deployment_verifier.py`: passed.
- `python3 -m pytest tests/test_timewarp_scheduler_materialization.py -k "signed_reduce_risk_package_authority_requires_resolved_fill_floor or package_positive_numeric_disagreement_reduce_risk_reaches_scheduler_with_cost_passed or package_positive_reduce_risk_keeps_refused_cost_blocked" -q`: 3 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "package_order_executable_final_blocker_blocks_unresolved_fill_floor_binding or order_materialization_surface_blocks_unresolved_fill_floor_stale_allowed or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed or risk_finalizer_blocks_unresolved_fill_floor_probe_execution or risk_finalizer_primary_probe_alias_prefers_selected_policy_blocked_probe or selected_policy_quality_gate or selected_execution_policy_replay_uses_runtime_quality_thresholds" -q`: 9 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "broad_order_executable_transfer_scan_flags_unresolved_package_fill_floor_execution or selected_package_executed_authority_scan_flags_unresolved_package_fill_floor_order_trade or broad_emitted_scheduler_status_authority_scan_flags_ranked_package_leak or replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias or unsigned_router_refusal_diagnostic_candidate_use_is_not_executable_alias or order_transfer_scan_flags_unsigned_router_refusal_executable_alias or broad_selected_policy_replay_authority_flags_quality_gate_leaks" -q`: 7 passed.

## Expected Measurable Effect

- Candidate -> scorecard/order: should remain stable unless unresolved fill-floor rows were incorrectly promoted into order surfaces.
- Scorecard/order -> fill: unresolved fill-floor order/trade rows should fall from V145's 8 rows / 3 unique keys to 0.
- Trade count: may fall if V145's added unresolved transfers were not reallocated; if it falls, classify the missed opportunities instead of calling it improvement by suppression.
- Added/removed trades: V145's added keys `bf1a...07:30` and `b8a...14:30` should not fill unless the route proves the fill-floor failures resolved. Removed V144 winners should be tracked for reallocation.
- Missed positive/negative R: positive missed R should remain visible if unresolved rows are demoted; negative missed R must remain visible.
- Net/gross/final R and W/L/F: can move either way; interpret through added/removed/common trade keys and unresolved-fill-floor counts.
- Full-risk/reduced-risk distribution must remain reported separately.
- Executed REFUSED/source-gap/live/final counts must remain zero.

## V146 Success / Failure Criteria

Success:

- Broker mutation, live broker authority, and final selection remain false.
- Executed REFUSED cost rows, source-gap rows, live rows, and final rows are all zero.
- Order/trade rows with unresolved fill-floor failures are zero.
- V144 unsigned router-refusal executable-authority zero count remains closed.
- Candidate/scorecard/order/fill counts, added/removed trades, missed R, selected-policy gate rows, and risk distribution are reported versus V145 and V144.
- Any lower R is explained as truth repair or next exposed transfer/reallocation blocker, not hidden as improvement.

Failure:

- Any unresolved fill-floor failure row reaches filled order/trade authority.
- Any REFUSED/source-gap/live/final row executes.
- Candidate scoreability collapses without exact blocker classification.
- The result improves only by suppressing all opportunity.
- V145 leak keys disappear without missed-opportunity attribution.

## Next Step After V146

Parse V146 immediately against V145 and V144. If unresolved fill-floor order/trade authority is closed, rank the remaining top B7 leakage bucket and patch the next same-root chain: scheduler reallocation, lifecycle/same-symbol replacement, order/fillability, or exit/stop geometry depending on the V146 ledgers.
