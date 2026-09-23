# G12 NOFILL Remaining Residual Source Closure Audit Goal Prompt - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`

## One-Line Starter

See `G12_NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_AUDIT_STARTER_MESSAGE_2026-05-09.txt`.

## Objective

Run `G12_NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_AUDIT` in this worktree as an independent red-team/source-control audit of:

`research/science_program_2026_05/06_outcome_testing/nofill_remaining_residual_source_closure/`

The goal is to decide whether the residual closure packet can be accepted as source/control evidence only:

- `NOFILL-CAT-ROW-0241` XAUUSD: proposed `SOURCE_CONTROL_CLEARED_INPUT_ONLY`.
- `NOFILL-CAT-ROW-0130`, `0143`, `0165`, `0178` USDJPY: proposed `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES`.

This is not a result lane. Do not score R, win rate, expectancy, validation, promotion, or live effect.

## Mandatory Preflight And Context

Before using any old summary:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. Read `.context/00_READING_ORDER.md`.

If a context file is stale, read the newer artifacts directly and state that you did.

## Required Controlling Inputs

Read the residual source-closure directory completely, including:

- `NOFILL_REMAINING_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_2026-05-09.json`
- `NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_2026-05-09.json`
- `NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_2026-05-09.json`
- `NOFILL_REMAINING_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER_2026-05-09.json`
- `NOFILL_REMAINING_SOURCE_HASH_MANIFEST_2026-05-09.json`
- `NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_2026-05-09.json`
- `NOFILL_REMAINING_NEXT_PROMPT_PACK_2026-05-09.md`
- `NOFILL_REMAINING_COMPLETION_AUDIT_2026-05-09.json`
- `build_nofill_remaining_residual_source_closure_2026_05_09.py`
- `verify_nofill_remaining_residual_source_closure_2026_05_09.py`
- `test_nofill_remaining_residual_source_closure_2026_05_09.py`
- raw MQL5 captures and the XAUUSD recovered tick parquet/capture JSON.

Also read the relevant upstream controls:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.md`

## Audit Questions

Answer these with evidence, not trust:

1. Are exactly five target rows audited and no others?
2. Were May 3 rows `0049/0050/0051` kept closed and not reopened?
3. Does XAUUSD `NOFILL-CAT-ROW-0241` have source-safe, read-only, side-aware quote/tick proof from true UTC `2026-05-06T00:00:00Z` through `2026-05-06T00:00:37.024315Z`?
4. Does the XAUUSD packet prove no short entry touch before cancel using bid/ask side-aware logic, without account/order/history labels?
5. Are the XAUUSD broker offset correction and recovered MT5 tick capture valid, hashed, and reproducible enough for source/control input-only evidence?
6. Do the four USDJPY rows truly reduce to single `MqlTick` quote-state rows where multiple predicates are true inside one source row?
7. Do official MQL5 docs support the claim that `MqlTick` has `time_msc` and flags but no sub-row event sequence?
8. Is array order meaningful only across rows/ticks, not inside one quote-state row?
9. Is the USDJPY impossibility claim too conservative, too aggressive, or exactly right under approved source routes?
10. Are any local heavy-data roots, prior worktrees, Sierra/proxy files, MT5 read-only exports, or source docs left unsearched that could resolve the USDJPY same-tick order without forbidden labels?
11. Are source hashes, raw captures, no-leak controls, duplicate/denominator controls, and label-family boundaries intact?
12. Did the residual verifier correctly avoid dirty-main false failures while still checking committed-scope forbidden live surfaces?
13. Is a future result/categorical rebuild now allowed, and if so exactly for which rows and evidence class?

## Hardening Standard

Use maximum practical reasoning. Apply curiosity, truthfulness, active creativity, anti-boxing, context-compaction discipline, proof-or-impossibility, and same-evidence-class continuation.

Do not stop at "audit says yes/no." If a decision is negative or impossible, explain why at row/source-contract level. If a decision is accepted, explain exactly what it proves and exactly what it does not prove. If a better source route exists inside the same source/control class, pursue it before finalizing. If it requires owner approval, name the exact source, path, access, fields, cost/API state, no-leak boundary, and expected decision impact.

Examples and file lists are starting points. Search absolute local heavy-data roots and prior worktrees if needed:

- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports`
- `C:\Users\MSI\Documents\ai-trading-agent\data\external`
- `C:\SierraChart\Data`
- `C:\tmp\gtos_otb`

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_remaining_residual_source_closure_audit/`

Write:

- context anchor;
- G12 decision ledger;
- XAUUSD source-control audit;
- USDJPY same-tick impossibility audit;
- source hash/raw capture audit;
- no-leak/duplicate/denominator/label-family audit;
- residual verifier audit;
- next prompt pack with exact next route;
- completion audit;
- verifier and focused tests where useful.

## Allowed Decisions

Use only these terminal decision classes unless you justify a stricter G12 class:

- `ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE`
- `ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY`
- `PARTIAL_ACCEPT_WITH_EXACT_BLOCKERS`
- `REJECT_INVALID_SOURCE_CLOSURE`
- `BLOCKED_WITH_EXACT_NEXT_SOURCE_OR_APPROVAL`

## Forbidden Surfaces

No live trading prompts, `src` trading logic, risk, execution, permissions, safety gates, selectors, canaries, MT5 order/account/history/deal/position calls, broker actual-R, hidden labels, paid/API/Databento without explicit approval, registry edits, promotion, validation-safe flips, outcome-review opening, remote pushes, credentials, or live order behavior.

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Verification

Run feasible checks before marking complete:

- JSON/JSONL parse;
- source hash recomputation;
- no-leak forbidden-key scan;
- exact five-row and May 3 exclusion checks;
- duplicate/denominator checks;
- label-family checks;
- `python -B -m py_compile` or syntax parse fallback;
- focused pytest with controlled temp directory if tests are added;
- committed-diff forbidden live-surface check.

## Stop Condition

The goal is complete only when G12 has a terminal decision for the residual closure packet, explains what is accepted/rejected/blocked at row and evidence-class level, preserves all safety flags, and writes durable artifacts plus next prompt guidance.
