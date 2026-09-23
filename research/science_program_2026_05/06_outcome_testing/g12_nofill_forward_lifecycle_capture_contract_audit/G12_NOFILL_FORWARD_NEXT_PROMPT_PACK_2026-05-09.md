# G12 NOFILL Forward Next Prompt Pack 2026-05-09

- audit_lane_id: `G12_NOFILL_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT`
- audited_route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Prompt 1 - Contract Addendum And Source-Safe Projection Builder

`/goal Resolve G12-FWD-BLOCKER-001..003 for the accepted-with-blockers NOFILL forward lifecycle capture contract. Build a source-control-only contract addendum and offline source-safe projection builder plan. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not open result scoring, validation, promotion, broker actual-R/account/order/deal history labels, live trading prompts, src trading logic, risk, execution, permissions, safety gates, selectors, canaries, paid/API/Databento, registry edits, credentials, remote pushes, or order behavior.`

## Prompt 2 - Offline Projection Verifier

After the addendum is accepted, build a verifier that consumes only hashed source-safe projections from current logs and local heavy manifests. It must fail closed on forbidden fields, generated duplicate keys, missing hashes, unresolved same-tick ordering, missing capture latency, and unsafe flags.

## Prompt 3 - USDJPY Quote-Event Access

The four USDJPY source-impossible rows still require broker-native bid/ask quote-event sequence, sub-millisecond timestamp, or monotonic event ID for the exact target timestamps. Proxy futures or M15/M1 OHLC cannot clear those rows.
