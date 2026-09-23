# OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION Prompt Pack - 2026-05-08

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`
Lane type: source-correction / contract-revision only

## One-Line Starter

`/goal Run OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION using C:\tmp\gtos_otb\NOFILLROUTER\research\science_program_2026_05\06_outcome_testing\nofill_blocked_family_source_correction_router\OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md as the controlling prompt; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; make categorical lifecycle labels possible only through source-correction or contract-revision evidence; do not compute R/performance or touch live trading surfaces.`

## Objective

Rebuild or revise the opening-drive source contract for 80 rows by source-hashing range_high, range_low, breakout_close_time, breakout_side, range bars, parser version, and decision-time as-of provenance. Use OTI4, OTX, G12/OTX artifacts, and local tick files. Decide patch-source-projection versus contract revision; do not assign labels in the prompt pack itself.

Rows in scope: `80`.
Blocker tuple(s): `['BLOCK_RESULT_MISSING_SOURCE']`.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. Read this prompt pack, `NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md`, `NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json`, and `NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json`.

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity. Treat examples, listed files, current timeframe, current worktree, current source modality, and first model framing as starting points, not boundaries. Search local heavy-data roots and prior artifacts before accepting any data blocker. Pursue every ambiguity until answered, proven impossible from approved inputs, reduced to an exact owner/access/source/capture requirement, or blocked by a hard forbidden boundary. Preserve context in committed artifacts so compaction cannot erase requirements.

## Scope Boundaries

- No R/performance scoring.
- No win-rate, expectancy, DSR/PBO, validation, promotion, or live-effect claims.
- No broker actual-R, account history, live order/deal/position labels, hidden labels, or blocked CNR061/six T3 scoring.
- No paid/API/Databento calls and no MT5 order/account/history calls.
- No live trading prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, remotes, registry promotion flags, validation flags, outcome-review flags, live-effect flags, or order behavior changes.

## Required Missing Fields Or Contract Terms

- `range_high`
- `range_low`
- `breakout_close_time`
- `breakout_side`
- `source_hashed_range_bars`
- `as_of_provenance`
- `parser_version`
- `decision_time_availability`

## Access State

No access request is currently needed for this family.

## Required Outputs For This Future Lane

- Context anchor and source-search ledger.
- Source/contract packet or exact impossibility ledger.
- Row-level route/eligibility decisions for every row in this family.
- Source-hash/no-leak/duplicate/as-of checks.
- Completion audit with exact blockers, no generic future-work language.

## Stop Condition

Stop only when every row in this family is source-corrected, contract-revised, blocked by exact source/as-of/no-leak/duplicate/label-family impossibility, or mapped to an exact owner/access/source/capture request.
