# OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT Prompt Pack - 2026-05-08

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`
Lane type: source-correction / contract-revision only

## One-Line Starter

`/goal Run OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT using C:\tmp\gtos_otb\NOFILLROUTER\research\science_program_2026_05\06_outcome_testing\nofill_blocked_family_source_correction_router\OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md as the controlling prompt; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; make categorical lifecycle labels possible only through source-correction or contract-revision evidence; do not compute R/performance or touch live trading surfaces.`

## Objective

Design the separate fill/path categorical contract for the single entry-touched row. Separate entry-touch/fill/path terminal order without R/performance, broker/account/live/order labels, or hidden labels.

Rows in scope: `1`.
Blocker tuple(s): `['BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED+BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS']`.

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

- `entry_touch_source`
- `post_entry_terminal_touch_time_utc`
- `post_entry_protective_touch_time_utc`
- `ordered_source_events`
- `same_timestamp_ambiguity`
- `separate_fill_path_label_family`

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
