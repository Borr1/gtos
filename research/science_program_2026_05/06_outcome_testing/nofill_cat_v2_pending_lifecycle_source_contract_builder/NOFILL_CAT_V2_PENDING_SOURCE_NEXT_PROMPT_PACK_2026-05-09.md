# NOFILL CAT V2 Pending Source Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

## Primary Next Route

`G12_NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_AUDIT`

Objective: Red-team the pending lifecycle source contract, schema fields, duplicate denominator verifier control, no-leak audit, blocker taxonomy, capture backlog, and completion audit. This is an audit/control route only. It must not score outcomes, open validation, edit registries, use broker/account/order labels, or touch live trading behavior.

Required inputs:

- `NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json`
- `NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json`
- Upstream row ledger `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`

Audit questions:

1. Does the schema include every required pending lifecycle, source coverage, no-touch, quote-side, hash, duplicate, ambiguity, and no-leak field family?
2. Does duplicate verifier control reject missing row-level and unique-key denominators, missing group/canonical fields, missing noncanonical exclusion policy, and generated fallback keys?
3. Are 8 blockers and 65 rejects still outside labels, denominators, result use, validation use, and promotion use?
4. Does the next source-access lane have enough fields to clear exact blockers without account/order/history labels?

## Secondary Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

Target exactly the 8 residual blockers with read-only source proof. Use this pending source contract as the schema. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Priority:

1. OTI4 May 3 opening-range source gaps with read-only tick parquet or M1/lower OHLC for `2026-05-03 13:00-13:30 UTC`.
2. Original OTI2 XAUUSD active-window source gap with side-aware bid/ask coverage through cancel.
3. OTI3 same-tick ambiguity only if higher-resolution event-order source exists without account/order labels.

## Tertiary Routes

- `NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT`: build event-order categorical source contract from entry, protective, terminal, quote-side, and ambiguity fields.
- `NOFILL_CAT_V2_OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT`: freeze opening-range projection source fields and duplicate denominator before any label route.
- `NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE`: design a future no-fill result lane without opening outcomes.

## Closed Route

`NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE` remains closed until separate frozen preregistration, source fields, sample floor, no-leak proof, G12 gate, and owner approval exist.
