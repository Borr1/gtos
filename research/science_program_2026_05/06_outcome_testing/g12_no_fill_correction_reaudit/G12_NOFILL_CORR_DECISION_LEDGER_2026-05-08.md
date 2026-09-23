# G12 NOFILL Correction Decision Ledger - 2026-05-08

Decision: `ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE`
Status: `PASS_ACCEPTED`

## Reasons
- Packet count is 298 rows with 298 source_closed and 0 source_blocked_exact.
- NOFILL-CLOSE-ROW-0127 is source-closed from OTR061 XAUUSD tick parquet with matching SHA256 and recomputed terminal-area first touch.
- Old BLOCKED_NO_TICKS_IN_WINDOW request is inactive/superseded.
- Prior tick-recovery and absolute local-heavy-data root search is now represented in builder/verifier/tests and row-level source search.
- Six T3 rows and 94 G12-blocked CNR061 rows remain excluded.
- No-leak, as-of, duplicate/sample-floor, source-hash, and label-family controls remain source-only.

## Non-Claims
- No R/performance scoring.
- No broker/account/live/order/hidden labels inspected.
- No blocked CNR061 rows scored or rescued.
- No validation, promotion, or live effect.

Next lane: `RESULT_CONTRACT_DESIGN_BEFORE_ANY_RESULT_SCORING`
