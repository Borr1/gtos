# Pre-Replay Brief - V175 B7 Compact Cost-Surface Risk Release Repair

Generated UTC: 2026-07-08T09:07:40Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- Broker mutation, live broker authority, and final selection remain false.
- This is a focused XAUUSD runtime proof slice; it is not broad replay or live/final proof.

## Latest Completed Replay Baseline

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_V174_B7_ORDER_BLOCK_RELEASE_BRANCH_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Scope: XAUUSD, 2026-06-04..2026-06-05, `repaired_package_conversion_v3`.
- V174 remained behavior-identical to V171-V173:
  - Candidate / scorecard / order / trade rows: `1130 / 184 / 10 / 3`.
  - Order status split: `filled=3`, `pending_accepted=3`, `risk_rejected=3`, `terminal_lifecycle_position_state_mutation_deferred=1`.
  - Wins/losses/flats: `3/0/0`.
  - Net/gross/final R: `0.84449709 / 1.09529478 / 1.09529478`.
  - Cash PnL: `211.19447407`; risk cash / risk pct: `750.42443587 / 0.75`.
  - Executed broker-cost REFUSED/source-gap rows: `0 / 0`.
- V174 plus direct helper replay proved the release helper works on final ledger rows, but runtime compact packets can omit flat broker-cost fields. The helper only checked `packets`, not validated order/risk surfaces, so it failed closed before release.

## Same-Root Patch Batch

Files changed for this checkpoint:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness repair: `release_rederived_package_authority_risk_reject()` now builds a merged cost packet from original packets plus validated order-authority and risk-authority surfaces.
- Safety preserved: original normalized packet fields keep priority, so REFUSED/source-gap broker-cost packets still block execution; surface cost proof only fills missing compact fields.
- Test repair: focused test now proves release succeeds when compact packets omit cost but the risk surface carries `PASSED`, `broker_calibrated_replay_cost`, and `source_bound_cost_authority_present`.

Focused checks passed before replay:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority or order_materialization_preserves_router_refusal_fill_floor_false or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed or router_refusal_signed_namespace_uses_scheduler_decision_inputs or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases" -q --tb=short`
  - Result: `6 passed, 575 deselected, 1 warning`.

## V175 Target And Criteria

Replay target:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V175_B7_COMPACT_COST_SURFACE_RISK_RELEASE_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Window: `2026-06-04..2026-06-05`.
- Symbol: `XAUUSD`.
- Profile: `repaired_package_conversion_v3`.

Expected measurable effect:

- The three watched candidates should no longer remain `risk_rejected` for stale signed-missing package authority.
- They may fill or move to a later honest order/fill/lifecycle outcome.
- Trade count/net R may improve or worsen honestly.
- Executed broker-cost REFUSED/source-gap rows must remain `0`.

Failure criteria:

- The same three rows still reject as `source_bound_router_refusal_requires_signed_new_entry_authority`.
- Cost-refused/source-gap rows become executable.
