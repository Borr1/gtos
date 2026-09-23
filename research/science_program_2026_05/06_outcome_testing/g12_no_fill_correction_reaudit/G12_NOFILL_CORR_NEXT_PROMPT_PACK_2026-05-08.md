Run the next source-safe lane only after accepting G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_REAUDIT_V1.

Recommended lane: NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_DESIGN_V1.

Objective: design, but do not score, the result contract required before any no-fill lifecycle closure outcome lane can open. Complete mandatory GTOS preflight; read the G12 correction reaudit artifacts under research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit/ plus the corrected packet and correction lane. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.

The contract must freeze entry/fill/cancel/expiry semantics, quote/tick/lower-timeframe path evidence requirements, pending-intent closure fields, side-aware touch parser, duplicate policy, sample floor, source-hash rules, no-leak/as-of schema, and label-family separation before any result rows are opened.

Hard boundaries: do not score R/performance; do not inspect broker/account/live/order/hidden labels; do not score blocked CNR061 rows; do not use paid/API/Databento or MT5 order/account calls; do not edit registries, remotes, credentials, or live trading surfaces; do not claim validation, promotion, or live effect.

Required starting evidence from this reaudit:
- Decision: ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE
- Packet counts: 298 source_closed / 0 source_blocked_exact.
- Row 0127 OTR061 SHA256: 6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff.
- Row 0127 first terminal-area touch: 2026-05-06T07:15:00.634000Z.
- Six T3 rows and 94 G12-blocked CNR061 rows remain excluded.

Stop condition: produce a machine-checkable result-contract design, exact blockers for any missing source fields, and next-lane prompt guidance. Do not open outcomes.
