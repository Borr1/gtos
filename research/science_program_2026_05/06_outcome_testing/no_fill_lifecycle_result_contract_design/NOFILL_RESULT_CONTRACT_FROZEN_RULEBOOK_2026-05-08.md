# NOFILL Result Contract Frozen Rulebook

Contract: `NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1`
Status: `FROZEN_DESIGN_ONLY_RESULT_LANE_NOT_OPEN`

## Locked Starting Evidence

- G12 decision: `ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE`
- Packet rows: `298`
- Source closed/source blocked exact: `298` / `0`
- Row 0127 OTR061 SHA256: `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`
- Row 0127 first terminal-area touch: `2026-05-06T07:15:00.634000Z`

## Contract Boundary

A future G12-accepted result lane may categorize lifecycle closure states from source-hashed evidence under these rules.

This lane opens no result rows and forbids R/performance, broker/account/live/order/hidden labels, validation, promotion, and live effect.

## Side-Aware Parser

- LONG entry: `ask <= entry_price`; terminal: `bid >= terminal_area_price`; protective: `bid <= protective_level_price`.
- SHORT entry: `bid >= entry_price`; terminal: `ask <= terminal_area_price`; protective: `ask >= protective_level_price`.
- Same-timestamp conflicts are ambiguous.
