# Pre-Replay Brief - V171 B7 Scheduler Compact Signed Self-Lock Repair

Generated UTC: 2026-07-08T07:54:31Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- B0/B1/B2/B5 are DONE; B3/B4/B6 are DONE WITH LABEL; B8 remains OPEN.
- Broker mutation, live broker authority, and final selection remain false.
- This is a targeted runtime proof slice, not broad replay or live/final proof.

## Current Completed Replay Baseline

- Latest relevant targeted proof: `BROAD_LIVE_AS_IF_REPLAY_V170_B7_NESTED_SIGNED_ROUTER_REFUSAL_AUTHORITY_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Window/scope: XAUUSD, 2026-06-04..2026-06-05, repaired_package_conversion_v3.
- Candidate rows: `1130`.
- Scorecard rows: `184`.
- Order rows: `10`.
- Trade rows: `3`.
- Wins/losses/flats: `3/0/0`.
- Net/gross/final R: `0.84449709 / 1.09529478 / 1.09529478`.
- Cash PnL: `211.19447407`.
- Missed opportunity rows: `1127`.
- V170 still had three earlier cost-passed, signed, router-refusal rows rejected by risk as:
  `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`.

## Same-Root Patch Batch

Files changed for this checkpoint:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Patch type:

- Correctness repair: scheduler self-lock revalidation now traverses compact direct/nested package authority surfaces, including `scheduler_candidate_decision_inputs`, `score_components.candidate_decision_inputs`, and nested authority maps.
- Correctness repair: compact signed `package_new_entry_authority_*` aliases are accepted only inside source-bound router-refusal self-lock revalidation, not by the global signed-authority validator.
- Diagnostic repair: router-refusal floor override reason remains explicit when override is configured but positive-predecision floors block restamp.
- Test repair: zero-risk release status assertion now matches the current specific bounded status.

Focused checks passed before replay:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "source_bound_router_refusal_self_lock or replay_executable_package_authority_does_not_override_router_floor_failure_for_new_entry or source_bound_router_refusal_open_reduced_releases_zero_risk_with_authority_floors or source_bound_router_refusal_marketable_guard_blocks_scheduler_runtime_slot" -q --tb=short`
  - Result: `8 passed, 256 deselected, 1 warning`.
- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "router_refusal_signed_namespace_uses_scheduler_decision_inputs or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or source_bound_router_refusal_reject_materializes_with_router_floors or raw_reject_promotion_fields_survive_scheduler_backfill_and_execution_attribution" -q --tb=short`
  - Result: `5 passed, 575 deselected, 1 warning`.

## V171 Target And Criteria

Replay target:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V171_B7_SCHEDULER_COMPACT_SIGNED_SELF_LOCK_REPAIR_20260604_20260605_XAUUSD_TARGETED`
- Window: `2026-06-04..2026-06-05`
- Symbol: `XAUUSD`
- Profile: `repaired_package_conversion_v3`

Expected measurable effect:

- The three V170 signed router-refusal risk rejections should no longer reject as unsigned self-lock.
- If they remain unfilled, the reason must shift to a downstream executable blocker with exact attribution.
- Candidate/scorecard counts should remain near V170 (`1130` / `184`) unless the scheduler consumer now emits additional scorecard rows from the same candidate window.
- Order rows may increase if the three rows advance past risk.
- Trade rows/net R may improve or worsen depending on honest fill/lifecycle outcome; this patch is correctness-first and may add a loser.
- REFUSED/source-gap executed count must remain `0`.

Success criteria:

- No order/trade row executes with broker-cost REFUSED or source-gap cost authority.
- The three watched candidates no longer have risk reason:
  `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`.
- Risk/order ledgers preserve signed-authority provenance and downstream rejection/fill reason.

Failure criteria:

- Signed compact rows still reject as unsigned.
- Broker-cost REFUSED/source-gap rows become executable.
- Router-floor guard tests or V171 artifacts show package authority bypassed positive-predecision floors.
