# OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT Prompt Pack - 2026-05-08

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`
Lane type: source-correction / contract-revision only

## One-Line Starter

`/goal Run OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT using C:\tmp\gtos_otb\NOFILLROUTER\research\science_program_2026_05\06_outcome_testing\nofill_blocked_family_source_correction_router\OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md as the controlling prompt; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; make categorical lifecycle labels possible only through source-correction or contract-revision evidence; do not compute R/performance or touch live trading surfaces.`

## Objective

Determine whether the 69 USDJPY price-only rows can become categorical lifecycle evidence under a conservative quote/tick contract. Use source-hashed USDJPY CFD M1 only as context; quote/tick proof is required for labels. Route rows with missing tick dates to the exact access/source request.

Rows in scope: `69`.
Blocker tuple(s): `['BLOCK_RESULT_LTF_PRICE_ONLY']`.

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

- `bid_ask_quote_or_tick_source`
- `entry_touch_time_utc`
- `terminal_area_touch_time_utc`
- `protective_level_touch_time_utc`
- `ordered_source_events`
- `same_timestamp_ambiguity`
- `parser_contract`

## Access State

Rows needing exact access/source request:
- NOFILL-CLOSE-ROW-0129 USDJPY 2026-04-17T00:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-17; no MT5 order/account/history calls.
- NOFILL-CLOSE-ROW-0130 USDJPY 2026-04-20T00:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-20; no MT5 order/account/history calls.
- NOFILL-CLOSE-ROW-0131 USDJPY 2026-04-20T02:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-20; no MT5 order/account/history calls.
- NOFILL-CLOSE-ROW-0163 USDJPY 2026-04-17T00:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-17; no MT5 order/account/history calls.
- NOFILL-CLOSE-ROW-0164 USDJPY 2026-04-17T00:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-17; no MT5 order/account/history calls.
- NOFILL-CLOSE-ROW-0165 USDJPY 2026-04-20T00:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-20; no MT5 order/account/history calls.
- NOFILL-CLOSE-ROW-0166 USDJPY 2026-04-20T02:15:00Z: Locate or extract read-only USDJPY bid/ask tick parquet for 2026-04-20; no MT5 order/account/history calls.

## Required Outputs For This Future Lane

- Context anchor and source-search ledger.
- Source/contract packet or exact impossibility ledger.
- Row-level route/eligibility decisions for every row in this family.
- Source-hash/no-leak/duplicate/as-of checks.
- Completion audit with exact blockers, no generic future-work language.

## Stop Condition

Stop only when every row in this family is source-corrected, contract-revised, blocked by exact source/as-of/no-leak/duplicate/label-family impossibility, or mapped to an exact owner/access/source/capture request.
