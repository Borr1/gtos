# NOFILL Forward Offline Parser Projection Prototype Design 2026-05-09

Route: `NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_OFFLINE_PROJECTION_PROTOTYPE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Algorithm

1. Read only the accepted upstream source/control artifacts named in the context anchor.
2. Parse the 298 source-safe projection rows.
3. Add contract identity and future-gate metadata.
4. Preserve row family, duplicate flags, denominator flags, missing statuses, source hashes, redaction statuses, and closed route flags.
5. Emit `NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_2026-05-09.jsonl`.
6. Generate fixtures for accepted, source-control, source-impossible, reject, touch-not-observed, spread-present, redaction, same-tick ambiguity, missing/NA, duplicate, and forbidden-field examples.

## Explicit Non-Goals

No result/cost scoring, broker account/order/deal/history labels, validation, promotion, registry edit, live logger wiring, or live trading behavior is opened.
