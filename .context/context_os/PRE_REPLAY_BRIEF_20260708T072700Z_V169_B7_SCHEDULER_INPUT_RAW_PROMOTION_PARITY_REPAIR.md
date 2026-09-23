# Pre-Replay Brief - V169 B7 Scheduler Input Raw-Promotion Parity Repair

Generated UTC: 2026-07-08T07:27:00Z.

## Fable Matrix Position

- Active dependency batch: B7 full proof ladder, scheduler/order/risk-expression transfer.
- B0/B1/B2/B5 remain DONE; B3/B4/B6 remain DONE WITH LABEL.
- B8 remains OPEN and ineligible until B7 runtime proof passes.
- Broker mutation, live broker authority, and final selection remain false.

## Latest Completed Target

- V168 targeted XAUUSD 2026-06-04..2026-06-05 completed with candidates `1130`, scorecards `184`, order rows `1`, trades `0`, missed rows `1130`, and net/gross/final R `0`.
- V168 watched rows carried `package_replay_order_executable_candidate_use_allowed=true` in the candidate ledger, but scorecard option inputs recomputed raw-reject promotion as missing and missed rows ended at `risk_pct_basis_missing`.

## Patch Batch

Files changed for this checkpoint:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness repair: sync the existing coupled package-order authority contract into `scheduler_candidate_decision_inputs` before scheduler allocation.
- Consumer repair: ensure scorecard/backfill consumers see raw-reject order-executable promotion fields from the same nested decision-input surface they already consume.
- Behavior expectation: cost-passed/source-complete raw-reject package candidates can advance past the prior `raw_reject_order_executable_promotion_contract_missing` blocker; broker-cost REFUSED/source-gap rows remain non-executable.

Focused checks passed before replay:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "source_bound_router_refusal_reject_materializes_with_router_floors or raw_reject_promotion_fields_survive_compact_scheduler_trace or raw_reject_promotion_fields_survive_scheduler_backfill_and_execution_attribution" -q --tb=short`
  - Result: `3 passed, 576 deselected, 1 warning`.
- Prior scheduler focused checks for the soft-failure override passed: `7 passed, 256 deselected, 1 warning`.

## V169 Target And Criteria

Replay target:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V169_B7_SCHEDULER_INPUT_RAW_PROMOTION_PARITY_REPAIR_20260604_20260605_XAUUSD_TARGETED`
- Window: `2026-06-04..2026-06-05`
- Symbol: `XAUUSD`
- Profile: `repaired_package_conversion_v3`

Success criteria:

- Watched candidate scorecard inputs show raw-reject promotion contract present and allowed.
- `trusted_order_executable_soft_failure_override_allowed` is no longer blocked by `raw_reject_open_reduced_promotion_not_allowed`.
- If orders still do not fill, the remaining blocker must shift to the next downstream B7 reason with deterministic attribution.
- Executed REFUSED/source-gap counts remain `0`.

Failure criteria:

- REFUSED/source-gap rows become executable.
- Scorecard inputs still show `raw_reject_order_executable_promotion_contract_missing`.
- `risk_pct_basis_missing` remains the terminal reason for the watched cost-passed/source-complete raw-reject class.

This is a targeted B7 repair proof only; it does not claim full reservoir transfer.
