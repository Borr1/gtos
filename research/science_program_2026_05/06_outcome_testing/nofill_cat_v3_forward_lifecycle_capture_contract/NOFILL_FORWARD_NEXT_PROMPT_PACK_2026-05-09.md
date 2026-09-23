# NOFILL Forward Next Prompt Pack 2026-05-09

- route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- schema_version: `nofill_cat_v3_forward_lifecycle_capture_contract_v1`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Prompt 1 - G12 Audit

Run `G12_NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT` against this folder. Audit the contract, schema, no-leak policy, duplicate/as-of controls, source/code audit, backlog, hostile review, tests, verifier, and completion audit. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, and do not open result scoring or live trading behavior.

## Prompt 2 - Source-Safe Projection Builder Plan

After G12 acceptance only, design an offline source-safe projection builder for already captured artifacts. It may read existing files and produce a manifest, but it must not edit live trading prompts/src logic, must not use MT5 account/order-history routes, and must fail closed on forbidden fields, missing hashes, unresolved event order, or generated duplicate keys.

## Prompt 3 - USDJPY Quote Event Sequence Source Access

Design a source-access route for `NOFILL-CAT-ROW-0130`, `NOFILL-CAT-ROW-0143`, `NOFILL-CAT-ROW-0165`, and `NOFILL-CAT-ROW-0178`. Required proof is bid/ask event ordering with sequence ID, sub-ms timestamp, or broker-native event sequence. Account/order labels and result scoring remain forbidden.
