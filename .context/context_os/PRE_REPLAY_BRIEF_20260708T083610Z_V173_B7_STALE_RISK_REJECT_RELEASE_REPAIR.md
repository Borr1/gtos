# Pre-Replay Brief - V173 B7 Stale Risk Reject Release Repair

Generated UTC: 2026-07-08T08:36:10Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- B0/B1/B2/B5 are DONE; B3/B4/B6 are DONE WITH LABEL; B8 remains OPEN.
- Broker mutation, live broker authority, and final selection remain false.
- This is a focused XAUUSD runtime proof slice; it is not broad replay or live/final proof.

## Latest Completed Replay Baseline

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_V172_B7_RISK_ORDER_SCHEDULER_INPUT_AUTHORITY_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Scope: XAUUSD, 2026-06-04..2026-06-05, `repaired_package_conversion_v3`.
- V172 was behavior-identical to V171:
  - Candidate / scorecard / order / trade rows: `1130 / 184 / 10 / 3`.
  - Order status split: `filled=3`, `pending_accepted=3`, `risk_rejected=3`, `terminal_lifecycle_position_state_mutation_deferred=1`.
  - Wins/losses/flats: `3/0/0`.
  - Net/gross/final R: `0.84449709 / 1.09529478 / 1.09529478`.
  - Cash PnL: `211.19447407`; risk cash / risk pct: `750.42443587 / 0.75`.
  - Executed broker-cost REFUSED rows: `0`; executed source-gap cost rows: `0`.
- V172 row inspection proved the remaining leak is not missing order authority:
  - order rows for the three watched candidates carried nested `risk_authority.package_replay_executable_candidate_use_allowed=true`;
  - nested `risk_authority.package_replay_order_executable_candidate_use_allowed=true`;
  - nested `risk_authority.package_new_entry_authority_valid=true`;
  - but top-level `risk_decision` stayed `reject` with stale reason `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`.

## Same-Root Patch Batch

Files changed for this checkpoint:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness repair: adds `release_rederived_package_authority_risk_reject()` and consumes it inside `simulate_order()` after order authority validation and before stop/lifecycle guards.
- Correctness repair: the release only applies when the old reject reason is package-authority diagnostic, the reason is not a hard order veto, broker-cost/source-gap authority is not blocked, unresolved fill-floor failures are absent, signed new-entry authority is valid, package executable is true, order executable is true, and an approved/runtime risk pct is positive.
- Ledger/proof repair: released rows carry `risk_finalizer_rederived_package_authority_released_stale_reject=true`, the stale reason, release source, and release risk pct.
- Safety preserved: hard router/fill vetoes, broker-cost REFUSED, source-gap, and unresolved fill-floor paths remain non-executable.

Focused checks passed before replay:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority or order_materialization_preserves_router_refusal_fill_floor_false or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed or router_refusal_signed_namespace_uses_scheduler_decision_inputs or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases" -q --tb=short`
  - Result: `6 passed, 575 deselected, 1 warning`.

## V173 Target And Criteria

Replay target:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V173_B7_STALE_RISK_REJECT_RELEASE_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Window: `2026-06-04..2026-06-05`.
- Symbol: `XAUUSD`.
- Profile: `repaired_package_conversion_v3`.

Expected measurable effect:

- The three watched V172 rows should no longer have `risk_decision=reject` from stale signed-missing authority.
- They may fill, become pending/expired, be blocked by a later lifecycle/fillability/order-policy reason, or be rejected by a different hard gate.
- Candidate and scorecard counts should remain near V172 unless downstream materialization adds rows from the same windows.
- Trade count/net R may improve or worsen depending on honest downstream fill/exit behavior; this is a correctness repair, not suppression.
- Executed broker-cost REFUSED rows and source-gap cost rows must remain `0`.

Success criteria:

- Valid signed order authority releases stale package-authority risk rejects.
- New rows carry release provenance and downstream reason if still unfilled.
- No broker-cost REFUSED/source-gap/unresolved fill-floor row becomes executable.

Failure criteria:

- The same three rows still reject as missing signed router-refusal authority.
- REFUSED/source-gap rows become executable.
- Risk is released without positive approved risk pct or without signed order authority.
