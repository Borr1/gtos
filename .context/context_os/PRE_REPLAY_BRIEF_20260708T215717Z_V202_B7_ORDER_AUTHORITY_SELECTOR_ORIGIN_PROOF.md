# Pre-Replay Brief - V202 B7 Order Authority / Selector Origin Proof

Generated UTC: 2026-07-08T21:57:17Z.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V201_B7_EXECUTABLE_TRANSFER_RISK_AND_STOP_MATERIALIZATION_AUTHORITY_20260513_20260517_TARGETED`
- Window: 2026-05-13..2026-05-17 hostile bucket, repaired package conversion profile.
- Rows: 14384 candidates, 288 scorecards, 161 orders, 70 filled trades.
- W/L/F: 40/30/0.
- Net/gross/final R: -6.54784120 / -1.36541623 / -1.36541623.
- Cash PnL: -2186.20676163.
- Risk cash / risk pct sum: 30392.11105544 / 30.84253588.
- Broker/live/final: false / false / false.

## Current Verification State

V201 route artifacts were rebuilt without a broad replay:

- `SOURCE_BOUND_TO_EXECUTED_PARITY_V201_B7_EXECUTABLE_TRANSFER_RISK_AND_STOP_MATERIALIZATION_AUTHORITY_20260513_20260517_TARGETED_SUMMARY.json`
- `BIG_R_PROVENANCE_BREAKDOWN_V201_B7_EXECUTABLE_TRANSFER_RISK_AND_STOP_MATERIALIZATION_AUTHORITY_20260513_20260517_TARGETED.json`
- `EXECUTION_LEAKAGE_BUCKET_V201_B7_EXECUTABLE_TRANSFER_RISK_AND_STOP_MATERIALIZATION_AUTHORITY_20260513_20260517_TARGETED_LEDGER.jsonl`
- `EXECUTION_LEAKAGE_REPAIR_PLAN_V201_B7_EXECUTABLE_TRANSFER_RISK_AND_STOP_MATERIALIZATION_AUTHORITY_20260513_20260517_TARGETED.json`
- `OUTPUT_MANIFEST.json` now points `broad_quality_parity_prefix` to V201.

Verifier after producer/consumer patches:

- `issue_count`: 2.
- Remaining issue class 1: stale V201 order rows materialized while `package_replay_executable_candidate_use_allowed=false` for `source_bound_router_refusal_requires_signed_new_entry_authority`; 85 order rows.
- Remaining issue class 2: stale V201 scorecard/order/trade rows have selector materialization but lack `scheduler_materialization_original_selector_action`; 49 / 30 / 14 rows.
- Cleared issue classes: missing V201 parity artifacts, manifest V150 pointer, candidate-index `selected_cell_risk_pct` scan, same-side pending scale-in authority scan, scorecard not-order-executable false-positive scan.

Focused tests/compile before replay:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `python3 -m pytest` targeted set: 7 passed.

## Fable Batch Matrix

- B0: DONE. Instrumentation and current parity artifacts exist.
- B1: DONE/REPAIRED. Raw selector origin/effective action contract has producer and verifier coverage; V202 must prove fresh ledger projection.
- B2: DONE/CONDITIONAL. Fillability/reallocation contracts exist; current V202 does not retune thresholds.
- B3: DONE/CONDITIONAL. Risk ladder exists; this checkpoint preserves selected-cell risk proof and signed release authority.
- B4: DONE/CONDITIONAL. Fill realism remains enforced; no bypass.
- B5: DONE/PATCHED. Verifier precision repaired for selected-cell risk fallback, not-order-executable scorecards, and signed scale-in lifecycle.
- B6: PARTIAL. Cost calibration authority remains unchanged; no REFUSED/source-gap execution allowed.
- B7: PARTIAL/ACTIVE. Current same-root batch repairs unsigned router-refusal executable release, selector-origin projection, marketable contract-unmet terminal binding, risk proof compaction, and lifecycle scale-in proof.
- B8: OPEN. Broker/live/final remain closed.

## Patch Batch

Files changed for this B7 batch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_denominator_to_deployment_verifier.py`

Patch type:

- Correctness: signed source-bound-router-refusal rederived risk release must require exact signed namespace authority.
- Correctness: contract-unmet marketable route rows are final-blocked marketable-guard rows, not bound executable orders.
- Correctness/proof: selector origin is preserved before authority/final-blocker consumers.
- Diagnostic/proof: compact candidate index and verifier consume selected-cell risk through explicit risk-budget aliases.
- Verifier/proof: signed same-symbol scale-in authority is accepted; unsigned scale-in remains fatal.

## Next Replay

Run the smallest behavior-changing proof that can regenerate the affected producer fields:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V202_B7_ORDER_AUTHORITY_SELECTOR_ORIGIN_PROOF_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: 2026-05-13 only.
- Profile: `repaired_package_conversion_v3`.
- Full 24-symbol surface; no top-N cap; no broker/live/final authority.

Success criteria:

- `order:package_executable_false_materialized` becomes 0.
- `order:immediate_marketable_route_contract_unmet` becomes 0 or every such row is `final_blocked/marketable_guard` with no bound order/trade id.
- `selector_materialized_without_original_selector_action` becomes 0 across scorecard/order/trade.
- Candidate quality scan has no `selected_cell_risk_pct` missing counts.
- Executed REFUSED/source-gap rows remain 0.
- Report trade count, net/gross/final R, cash PnL, W/L/F, orders, expired/contract-unmet/final-blocked counts, and added/removed trade deltas against the same 2026-05-13 slice of V201.

Failure criteria:

- Any unsigned source-bound-router-refusal row still reaches pending/filled order materialization.
- Any materialized selector action lacks original selector action.
- Any improvement comes only from suppressing all opportunity rather than repaired authority transfer.
