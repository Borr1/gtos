# V182 B7 Pre-Replay Brief - Derived Router-Refusal Marketable Authority Release

Generated UTC: 2026-07-08T10:32:11Z

## Control State

- Fable dependency batch: B7, after B0-B6 matrix gates marked done/done-with-label.
- Latest completed replay baseline: `BROAD_LIVE_AS_IF_REPLAY_V181_B7_SOURCE_BOUND_ROUTER_REFUSAL_FLOOR_PARITY_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Active process state before patch: no broad replay process active.
- Broker/live/final: closed. This patch does not set live broker authority, broker mutation, or final selection true.
- Scope: targeted 2026-06-04..2026-06-05 XAUUSD proof slice only. It is not full reservoir conversion proof.

## V181 Evidence

- Candidate/scorecard/order/trade/missed/bucket rows: `1130 / 184 / 15 / 6 / 1122 / 30`.
- W/L/F: `5 / 1 / 0`.
- Net/gross/final R: `1.43436072 / 1.98898776 / 1.98898776`.
- Expected cost R: `0.55462704`.
- Executed broker-cost REFUSED/source-gap rows: `0 / 0`.
- V181 fixed stale source-bound router-refusal floor provenance but did not add trades/orders.

## Root Mismatch

V181 still leaves `10` scoreable, broker-cost-passed, source-complete, signed-order-authority rows blocked by `package_marketable_limit_entry_guard_blocked`.

Those rows have:
- missed package order executable authority true;
- source-bound candidate use allowed true;
- signed package new-entry authority valid;
- predecision limit marked marketable;
- broker pretrade cost passed;
- immediate-marketability quality and entry-quality floors passing on the strongest rows.

The remaining blocker is profile authority drift: the scheduler/timewarp code already has a strict derived immediate-marketable authority path, but the repaired replay profile still sets `scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled = False`, forcing valid signed source-bound router-refusal rows to remain diagnostic.

## Patch Batch

Files changed:
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `tests/test_broad_replay_repair_config.py`

Patch type:
- Behavior-changing config repair in local replay only.
- The existing scheduler route remains strict: source-bound router-refusal immediate-marketable route requires signed predecision package authority, broker-cost pass, source completeness, configured session or explicit off-session authority, immediate-entry quality, and cost ceiling.

Focused proof already run:
- `python3 -m py_compile research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py tests/test_broad_replay_repair_config.py src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'marketable_guard_router_refusal_source_bound_signature_requires_derived_immediate_flag or marketable_guard_uses_measured_tick_floor_cost_ceiling_for_liquid_symbol or marketable_guard_does_not_apply_structure_quality_to_unscoped_family or source_bound_router_refusal_marketable_guard_blocks_scheduler_runtime_slot' -q --tb=short`
- `python3 -m pytest tests/test_broad_replay_repair_config.py::test_repaired_profile_routes_marketable_package_entries_only_in_no_broker_replay tests/test_broad_replay_repair_config.py::test_repaired_profile_forwards_window_headroom_policy_to_scheduler -q --tb=short`

## Expected Replay Effect

Expected improvement class:
- better order/fillability conversion, not blocking trades;
- marketable guard diagnostic rows should route to immediate-marketable replay order policy only if strict signed/predecision gates pass.

Expected measurable movement:
- candidate -> scorecard transfer: neutral.
- scorecard -> order transfer: should increase for eligible V181 marketable-guard rows.
- order -> fill transfer: should increase only where immediate-marketable fill has source-safe predecision price.
- missed positive R: should fall for the `package_marketable_limit_entry_guard_blocked` rows that become executable.
- missed negative R: may also fall because the release is causal and not outcome-fitted; V181 bucket net is `+1.82271865R` with positive `+5.12135038R` and negative `-3.29863173R`.
- trade count: may increase.
- net/gross/final R: unknown until replay. A worse result is acceptable if it exposes honest execution behavior under this causal authority.
- cost-refused/source-gap executions: must remain `0 / 0`.
- risk-reduced/full-risk distribution: report separately.

## Pass / Fail Criteria

Helped:
- eligible signed marketable-guard rows move from missed diagnostic to order/trade ledgers;
- no broker-cost REFUSED/source-gap rows execute;
- live broker authority, broker mutation, and final selection remain false;
- added trades and missed reductions are fully attributable by candidate instance.

Failed:
- no transfer change despite profile authority enabled, meaning the consumer path still drops authority;
- REFUSED/source-gap/unfillable rows execute;
- improvement comes only from suppressing opportunity;
- the new rows expose a deeper negative executable policy, in which case keep the truth and patch the next B7 leak rather than reverting blindly.

