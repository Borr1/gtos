# Pre-Replay Brief - V172 B7 Risk/Order Scheduler-Input Authority Repair

Generated UTC: 2026-07-08T08:19:30Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- B0/B1/B2/B5 are DONE; B3/B4/B6 are DONE WITH LABEL; B8 remains OPEN.
- Broker mutation, live broker authority, and final selection remain false.
- This is a focused XAUUSD runtime proof slice; it is not broad replay or live/final proof.

## Latest Completed Replay Baseline

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_V171_B7_SCHEDULER_COMPACT_SIGNED_SELF_LOCK_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Scope: XAUUSD, 2026-06-04..2026-06-05, `repaired_package_conversion_v3`.
- Candidate / scorecard / order / trade rows: `1130 / 184 / 10 / 3`.
- Order status split: `filled=3`, `pending_accepted=3`, `risk_rejected=3`, `terminal_lifecycle_position_state_mutation_deferred=1`.
- Wins/losses/flats: `3/0/0`.
- Net/gross/final R: `0.84449709 / 1.09529478 / 1.09529478`.
- Cash PnL: `211.19447407`; risk cash / risk pct: `750.42443587 / 0.75`.
- The three remaining risk rejects are:
  - `broadorigin_bf1a01f81a62731eb07810e1` at `2026-06-04T07:30:00+00:00`;
  - `broadorigin_4198e4ca590f2fc63e022d51` at `2026-06-04T08:45:00+00:00`;
  - `broadorigin_b8a223d65d654f26188d842f` at `2026-06-04T14:30:00+00:00`.
- Those rows still rejected as `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`, while their missed rows preserved `risk_finalizer_package_replay_executable_candidate_use_allowed=true` with reason `derived_predecision_quality_source_and_broker_cost_authority`.

## Same-Root Patch Batch

Files changed for this checkpoint:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness repair: `order_materialization_authority_candidate_surface()` now consumes `scheduler_candidate_decision_inputs` from the selected option, candidate, or packets as a first-class authority surface.
- Correctness repair: package new-entry authority attribution, lifecycle aliases, replay executable flags, and order executable flags can be resolved from scheduler decision inputs when the top-level candidate row still carries re-derivable stale false authority.
- Safety preserved: hard non-rederivable false reasons such as unresolved fill-floor/router-floor order vetoes remain terminal; broker-cost REFUSED/source-gap enforcement is unchanged.

Focused checks passed before replay:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority or order_materialization_preserves_router_refusal_fill_floor_false or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed or router_refusal_signed_namespace_uses_scheduler_decision_inputs or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases" -q --tb=short`
  - Result: `6 passed, 575 deselected, 1 warning`.

## V172 Target And Criteria

Replay target:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V172_B7_RISK_ORDER_SCHEDULER_INPUT_AUTHORITY_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Window: `2026-06-04..2026-06-05`.
- Symbol: `XAUUSD`.
- Profile: `repaired_package_conversion_v3`.

Expected measurable effect:

- The three watched V171 rows must no longer reject as `source_bound_router_refusal_requires_signed_new_entry_authority`.
- If they remain unfilled, their order/missed rows must carry a new downstream reason such as lifecycle/fillability/risk-budget/order-policy, not stale signed-authority loss.
- Order rows may increase or the same rows may change status; trade rows/net R may improve or worsen depending on honest downstream execution.
- Candidate and scorecard counts should remain near V171 unless the changed consumer causes additional selected-order rows.
- Executed broker-cost REFUSED rows and source-gap cost rows must remain `0`.

Success criteria:

- Valid signed `scheduler_candidate_decision_inputs` authority reaches risk/order materialization.
- No order/trade executes with broker-cost REFUSED or source-gap cost authority.
- Hard fill-floor/order veto tests remain green.

Failure criteria:

- The same three rows still reject as missing signed router-refusal authority.
- REFUSED/source-gap rows become executable.
- The repair only changes ledger labels while leaving risk/order consumers unchanged.
