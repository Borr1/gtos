# NOFILL Forward Capture Backlog And Implementation Route 2026-05-09

- route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- schema_version: `nofill_cat_v3_forward_lifecycle_capture_contract_v1`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Backlog

1. `source_safe_projection_builder` (P0) - offline research builder over already captured artifacts. Done when: emits only the contract schema fields and fails closed on forbidden fields or missing hashes. Approval needed: `false`.
2. `tick_and_ltf_coverage_hasher` (P0) - read-only manifest over existing tick parquet, M1/LTF sources, and parser code hashes. Done when: source_file_hashes, coverage windows, missing intervals, and parser_code_hash populated. Approval needed: `false`.
3. `event_order_resolution_verifier` (P1) - source-only event ordering with explicit ambiguity or impossibility codes. Done when: same-tick/same-bar cases marked unresolved unless source sequence proves order. Approval needed: `false`.
4. `future_live_shadow_logger_projection` (P1) - proposal only; any live logger edit touches src and needs CEO approval before implementation. Done when: approval gate documented; no live code changed by this route. Approval needed: `true`.
5. `usdjpy_broker_native_quote_event_sequence_source_access` (P1) - source access route for NOFILL-CAT-ROW-0130/0143/0165/0178. Done when: bid/ask event sequence with sequence ID or sub-row timestamp, no account/order labels. Approval needed: `false`.
6. `may3_opening_drive_source_projection_contract` (P2) - market-session empty/tick-gap source projection for May 3 opening-drive rows. Done when: source-control rows remain input-only and unscored. Approval needed: `false`.
7. `fill_path_vocabulary_contract_alignment` (P2) - align future categorical vocabulary to source proofs, not result scoring. Done when: no entry/terminal/protective-area labels mapped to source-only proofs. Approval needed: `false`.

## Forbidden Implementation Routes

No live trading prompts, no `src` trading behavior change, no risk/execution/permissions/safety gate edits, no canary edits, no MT5 account/order-history pull, no paid/API/Databento use, no credentials, no registry edits, no remote push, and no order behavior change are opened by this contract.
