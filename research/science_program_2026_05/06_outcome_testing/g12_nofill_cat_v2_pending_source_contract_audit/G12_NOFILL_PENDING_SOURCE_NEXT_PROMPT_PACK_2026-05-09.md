# G12 NOFILL Pending Source Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

## Primary Next Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

Objective: Use the G12-accepted pending source contract to attempt source/control clearance for exactly the 8 residual blockers. This route must remain source/control only and must not score accepted, blocked, or rejected rows.

Required inputs:

- `G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json`
- `G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json`
- `G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json`
- `G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json`
- `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`

Allowed work:

1. For the 3 OTI4 May 3 source gaps, search read-only tick parquet or M1/lower OHLC covering `2026-05-03 13:00-13:30 UTC`.
2. For the 1 original OTI2 source gap, search side-aware bid/ask coverage through active pending window and cancel.
3. For the 4 OTI3 same-tick rows, keep blocked unless higher-resolution event-order source exists without account/order labels.
4. Hash consumed source files and record source coverage status, quote side, parser version, source paths, duplicate identity, and ambiguity status.

Forbidden work:

- No result scoring, validation, promotion, registry edit, broker actual-R, account history, order history, hidden labels, MT5 order/account/history calls, paid/API/Databento calls, or live trading behavior.
- Do not move any of the 8 blockers into accepted labels or denominators unless exact source-control clearance is proven from approved source fields.
- Keep the 65 rejects outside all labels and denominators.

## Secondary Route

`NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT`

Objective: Build a categorical source contract for entry/protective/terminal event ordering using the accepted source schema families. Same-tick/same-bar ambiguity must stay explicit. No path-R, actual-R, validation, promotion, or selector use is allowed.

## Tertiary Route

`NOFILL_CAT_V2_PENDING_LIFECYCLE_PROSPECTIVE_CAPTURE_SPEC`

Objective: Convert the source contract into an implementation ticket for future shadow capture. This must be a spec or isolated logger-test lane unless the owner separately approves live wiring. It cannot change order behavior, cancellation decisions, risk, execution, prompts, permissions, safety gates, or selectors.

## Closed Routes

`NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE`, validation, promotion, registry edits, broker/account/order label use, and live behavior changes remain closed until a separate frozen preregistration, sample floor, no-leak proof, G12 acceptance, and owner approval exist.
