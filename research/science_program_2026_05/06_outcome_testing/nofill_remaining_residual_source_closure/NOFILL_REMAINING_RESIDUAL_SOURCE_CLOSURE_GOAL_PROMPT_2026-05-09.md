# NOFILL Remaining Residual Source Closure Goal Prompt - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`

## One-Line Starter

See `NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_STARTER_MESSAGE_2026-05-09.txt`.

## Objective

Run `NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_V1` in this worktree as a source/control lane only. The goal is to pursue the residual no-fill source blockers that remain after the accepted G12 May 3 source proof:

- `NOFILL-CAT-ROW-0241` XAUUSD original OTI2 active-window/cancel gap.
- `NOFILL-CAT-ROW-0130` USDJPY same-tick event-order ambiguity.
- `NOFILL-CAT-ROW-0143` USDJPY same-tick event-order ambiguity.
- `NOFILL-CAT-ROW-0165` USDJPY same-tick event-order ambiguity.
- `NOFILL-CAT-ROW-0178` USDJPY same-tick event-order ambiguity.

Do not re-open the three May 3 rows except as closed context. They are already accepted by G12 as source/control market-session-empty evidence only.

This lane must not stop at blocker-family classification. It must pursue every allowed source-safe route inside this same evidence class until each of the five rows is either:

- cleared as source/control input-only evidence,
- proven impossible from approved source routes with exact saturation evidence, or
- reduced to an exact owner/access/source/capture requirement that cannot be satisfied inside the run.

No result scoring, R/performance, win rate, expectancy, validation, promotion, registry edit, selector change, or live behavior is allowed.

## Mandatory Preflight And Context

Before doing any work:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. Read `.context/00_READING_ORDER.md`.

If `LIVE_STATE` says research context is stale, read the newer research artifacts directly before relying on summaries.

## Controlling Artifacts To Read

Read these as controlling inputs, then follow the evidence even if another relevant artifact is discovered:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/G12_NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_BLOCKER_AND_FAILURE_LEARNING_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/oti1_pending_intent_closure_source_packet/OTI1_PENDING_INTENT_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.md`

## Hardening Standard

Use maximum practical reasoning. Be curious, truthful, active, and creative. Examples and paths in this prompt are starting points, not boundaries. Check whether the session is accidentally boxed by:

- this worktree's sparse checkout,
- a single timeframe,
- a single data modality,
- only Git-tracked files,
- only the first row ledger,
- only MT5 ticks,
- only CFD data,
- only prior prompt wording,
- only the first source gap explanation.

Worktree absence is not data absence. Search absolute local-heavy-data roots and prior worktrees before accepting missing data:

- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports`
- `C:\Users\MSI\Documents\ai-trading-agent\data\external`
- `C:\SierraChart\Data`
- `C:\tmp\gtos_otb`
- any source roots named in `.context/00_core/local_heavy_data_inventory.md`

If a route needs access, request it. If a route needs public source proof, use official/public webfetch or curl only when source-contract evidence is relevant, save raw captures, and record a source index. If a route needs Databento or another paid/API source, do not spend silently; write a pre-call manifest with symbol, venue, schema, window, expected cost/free-credit status, fields, no-leak boundary, and ask for approval unless an explicit local approval artifact already covers that exact call.

## Row-Specific Source Routes

### XAUUSD `NOFILL-CAT-ROW-0241`

Target question: can side-aware XAUUSD bid/ask quote/tick coverage prove the active pending window through `2026-05-06T00:00:37.024315Z`?

Pursue:

- existing XAUUSD tick parquet and any raw tick source around `2026-05-06T00:00:00Z` to `2026-05-06T00:00:37.024315Z`;
- adjacent day files and concatenation boundary defects around `2026-05-05T23:59:59.998Z`;
- MT5 read-only `copy_ticks_range` only if needed and only for quote/tick data; do not call account, order, deal, position, or history APIs;
- any Sierra or broker export that contains side-aware bid/ask quote evidence for that exact gap;
- parser/hash proof that the row is either no-touch-through-cancel, entry-touch-before-cancel, still source-missing, or impossible from approved routes.

Do not use M1-only context as side-aware proof. Do not use broker account/order/history labels.

### USDJPY `NOFILL-CAT-ROW-0130`, `0143`, `0165`, `0178`

Target question: can a source-safe event-order contract resolve same source-timestamp quote rows that satisfy multiple touch predicates?

Pursue:

- exact local USDJPY tick files and schemas for timestamp granularity, `time_msc`, flags, spread, bid/ask state, row order, and any sequence-like field;
- whether source-file row order is a valid event-order source under a frozen parser contract, or whether it is unsafe because one row is a state snapshot rather than ordered events;
- existing MT5 read-only tick exports from prior worktrees and whether they contain sequence/flags/sub-ms fields sufficient for event ordering;
- read-only MT5 `copy_ticks_range` only if needed and only for quote/tick data; do not call account, order, deal, position, or history APIs;
- Sierra/6J or other proxy data only as proxy/source-contract evidence, never as direct CFD event order unless a valid proxy contract is proven;
- official/vendor docs or local parser code that proves what the tick row represents, if needed;
- exact impossibility proof if the current source row is inherently a quote-state snapshot that cannot order entry/protective/terminal predicates within the same tick row.

If same-tick ordering is impossible from approved source classes, write the exact reason and the exact higher-resolution source that would be required, not just "same timestamp ambiguous."

## Required Outputs

Create a new directory:

`research/science_program_2026_05/06_outcome_testing/nofill_remaining_residual_source_closure/`

Write at minimum:

- context anchor with current HEAD, controlling prompt, active question stack, and searched roots;
- source search ledger for XAUUSD and USDJPY;
- XAUUSD active-window proof packet;
- USDJPY same-tick event-order source-contract/proof packet;
- row decision ledger covering exactly the five rows;
- blocker/clearance/impossibility ledger;
- source hash manifest for every consumed source file or raw capture;
- no-leak, duplicate, denominator, and label-family audit;
- next prompt pack, including whether G12 audit is now needed and exactly what it should audit;
- completion audit with instruction-coverage checklist;
- verifier and focused tests where useful.

Every output must preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Verification

Before completion, run all feasible checks:

- JSON/JSONL parse checks;
- source hash recomputation;
- no-leak forbidden-key scan;
- duplicate/denominator exclusion checks;
- label-family separation checks;
- `python -B -m py_compile` or syntax-parse fallback if Windows bytecode writes fail;
- focused pytest with a controlled temp directory if tests are added;
- committed-diff forbidden live-surface check.

If Windows temp/pycache permissions fail, distinguish environment friction from verifier failure and record it.

## Forbidden Surfaces

Do not touch or commit changes to live trading prompts, `src` trading logic, risk, execution, permissions, safety gates, selectors, canaries, MT5 order/account/history code, credentials, remotes, registry edits, promotion files, paid/API calls without explicit approval, or live order behavior.

Do not inspect broker actual-R, account history, order history, live order results, hidden labels, blocked-packet outcomes, R/performance, win rate, expectancy, validation, promotion, or live-effect routes.

## Stop Condition

This goal completes only when all five target rows have terminal source/control statuses backed by artifacts and verification:

- source/control cleared input-only,
- impossible from approved source routes with exact proof,
- or still blocked with exact external owner/access/source/capture requirement.

Generic blocker taxonomy is not enough. The completion audit must prove the allowed pursuit path was saturated.
