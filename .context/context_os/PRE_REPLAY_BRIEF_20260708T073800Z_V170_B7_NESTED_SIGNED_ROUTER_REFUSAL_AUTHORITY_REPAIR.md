# Pre-Replay Brief - V170 B7 Nested Signed Router-Refusal Authority Repair

Generated UTC: 2026-07-08T07:38:00Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- Broker mutation, live broker authority, and final selection remain false.
- This is a targeted replay proof, not a broad replay or live/final claim.

## V169 Result That Selected This Patch

- V169 completed on XAUUSD 2026-06-04..2026-06-05.
- Candidate rows remained `1130`; scorecard rows remained `184`.
- Order rows increased from V168 `1` to V169 `3`; trade rows remained `0`.
- All three V169 order rows were cost-passed, raw-promotion allowed, and package order-executable, but ended `risk_rejected` with:
  `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`.
- The same rows carried valid signed package new-entry authority inside `scheduler_candidate_decision_inputs`.

## Patch Batch

Files changed for this checkpoint:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness repair: make source-bound router-refusal signed namespace validation traverse direct rows, nested scheduler decision inputs, score components, and nested package authority surfaces.
- Boundary repair: preserve unsigned source-bound/router-refusal rows as scoreable diagnostic evidence while keeping executable aliases false until signed authority exists.

Focused checks passed before replay:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "router_refusal_signed_namespace_uses_scheduler_decision_inputs or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or source_bound_router_refusal_reject_materializes_with_router_floors or raw_reject_promotion_fields_survive_scheduler_backfill_and_execution_attribution" -q --tb=short`
  - Result: `5 passed, 575 deselected, 1 warning`.

## V170 Target And Criteria

Replay target:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V170_B7_NESTED_SIGNED_ROUTER_REFUSAL_AUTHORITY_REPAIR_20260604_20260605_XAUUSD_TARGETED`
- Window: `2026-06-04..2026-06-05`
- Symbol: `XAUUSD`
- Profile: `repaired_package_conversion_v3`

Success criteria:

- The three V169 order rows no longer reject with `source_bound_router_refusal_requires_signed_new_entry_authority`.
- If they still reject, the reason must shift to a downstream executable blocker with exact attribution.
- Executed REFUSED/source-gap rows remain `0`.
- Unsigned router-refusal rows remain scoreable/missed but non-executable.

Failure criteria:

- Broker-cost REFUSED or source-gap rows become executable.
- Signed rows still reject as unsigned.
- Source-bound diagnostic aliases disappear for unsigned rows.
