# G12 NOFILL Forward Decision Ledger 2026-05-09

- audit_lane_id: `G12_NOFILL_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT`
- audited_route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

Terminal G12 verdict: `ACCEPT_WITH_EXACT_CONTRACT_BLOCKERS`
Decision status: `PASS_ACCEPTED_WITH_BLOCKERS`

## Accepted Contract Claims

- The full NOFILL CAT V3 evidence chain and frozen count equation recompute cleanly from committed count/result-contract artifacts.
- The forward contract is correctly bounded as source/control only with NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, and live_effect=false.
- The schema has 80 fields across 12 families and covers source/as-of timestamps, hashes, parser/build provenance, event-order ambiguity, duplicate controls, and no-leak guards.
- The contract correctly rejects raw pending lifecycle/candidate/path logs as direct inputs when they contain account/order/result-shaped fields.
- The backlog keeps live wiring, paid/API/Databento, registry edits, result scoring, validation, and promotion outside this lane.

## Rejected Or Weakened Claims

- The contract is not implementation-ready until the exact addendum blockers are resolved or mapped to equivalent source-safe fields.
- Current raw source logs are not contract-safe and cannot be consumed without allowlist projection and forbidden-key scans.
- Local heavy data availability strengthens future source manifests but does not clear same-tick broker-native sequence blockers and does not create validation evidence.
- Cost/spread/slippage/execution observability is not sufficient for any later survival-adjusted expectancy test until explicit closed status fields and source hashes exist.

## Exact Contract Blockers

- `G12-FWD-BLOCKER-001` Capture-latency observability is only partial. The contract has source manifest and source coverage timestamps, but no explicit row capture/write latency fields. Exact fix: Add capture_observed_at_utc or equivalent., Add capture_write_completed_utc or equivalent., Add capture_latency_ms or explicit null/impossible reason., Add capture_clock_source_and_skew_policy or equivalent.
- `G12-FWD-BLOCKER-002` Source-safe pending-order observability is not explicit enough to consume current lifecycle logs without accidental order/account leakage. Exact fix: Add pending_order_mode_source_safe or map pending_order_mode with an allowlist., Add broker_pending_order_created_status as a categorical observability field, not a broker outcome label., Add native_pending_order_type_status with MT5 ticket redaction proof., Add mt5_order_ticket_redaction_status and fail closed when a ticket value would enter the contract row.
- `G12-FWD-BLOCKER-003` Cost/spread coverage is present only as spread_state and quote_side. Slippage and execution-quality observability need closed source-safe status fields before any later cost or survival test. Exact fix: Add decision_spread_source_safe and entry_touch_spread_source_safe or explicit unavailable statuses., Add slippage_label_status fixed to NOT_OPENED_FOR_SOURCE_CONTROL unless a later result lane is explicitly opened., Add execution_quality_label_status fixed to NOT_OPENED_FOR_SOURCE_CONTROL., Preserve source hashes for any spread/quote measurement.

## Next Route

After this G12 acceptance-with-blockers, run a contract-addendum/source-safe projection-builder lane that resolves G12-FWD-BLOCKER-001..003 without opening result scoring or live behavior.
