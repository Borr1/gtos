# G0 NOFILL CAT V2 Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

## Primary Next Route

`NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER`

Objective: Build a source-only pending lifecycle capture contract from the G0 synthesis/control outputs. Preserve the exact G0 boundaries: no result scoring, no validation, no promotion, no live trading behavior change, no registry edits, no broker/account/order labels, and no use of blocked or rejected rows as results.

Must read:

- `G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.md`
- `G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json`
- `G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json`
- `G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json`
- Upstream row ledger `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`

Required output:

- A source-contract spec for pending create, cancel/expiry, terminal touch, side-aware entry touch, no-touch proof, coverage status, duplicate key, and source hashes.
- A verifier that rejects missing duplicate denominator policy, true safety flags, generated duplicate keys, result fields, blocked/rejected denominator inclusion, and absent source coverage status.
- A capture backlog that can run prospectively without changing live trading behavior.

Stop condition: complete only when the source contract is machine-checkable and still carries `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Secondary Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

Objective: Target exactly the 8 residual blockers. Do not score accepted rows, rejected rows, or blocked rows. Clear a blocker only with read-only source proof that satisfies the exact unblocker in `G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json`.

Priority order:

1. OTI4 May 3 frozen opening-range source gaps.
2. Original OTI2 XAUUSD active-window side-aware source gap.
3. OTI3 same-tick ambiguities only if higher-resolution event-order source exists without account/order labels.

## Tertiary Route

`NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE`

Objective: Design a future result contract without opening outcomes. Freeze denominator, source fields, sample floor, duplicate policy, no-leak proof, G12 gate, owner approval requirement, and forbidden fields. Do not compute or inspect results.

## Closed Route

`NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE` remains closed until a separate frozen preregistration, sample floor, no-leak proof, G12 acceptance, and explicit owner approval exist.
