# NOFILL Lifecycle Closure Source Packet Goal Prompt - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Goal

Build `NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1` as a separate frozen source-only lane for the accepted no-fill/still-pending/wrong-side/no-entry/terminal-order-unclaimed/source-blocked families from G12_NOFILL. This is a source closure packet lane, not a result lane. Do not compute R, performance, win rate, expectancy, DSR, PBO, validation, promotion, or live-edge claims.

The purpose is to pursue every source-safe closure question raised by G12:

- pending lifecycle closure: pending-created, entry-touched, filled, cancelled, expired, frozen observation horizon, and quote/source hash;
- no-entry path order: decision as-of, entry price/bounds, entry touch proof, terminal-area touch proof, lower-timeframe or tick source coverage hash;
- terminal-order proof: post-entry tick/lower-timeframe order, target/stop touch times, same-bar ambiguity policy, parser/scale contract;
- source-blocked rows: price-compatible M1/tick path or exact parser/scale/source impossibility proof;
- OTI1 metadata: top-level symbol/session/side projection before any future result denominator.

## Mandatory Preflight

Before making decisions:

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Skim `.context/00_READING_ORDER.md`.
9. Write a context anchor before contract/classification artifacts, recording HEAD, this prompt path, controlling inputs read, active question stack, searched roots, source boundaries, forbidden fields, and stop-condition checklist.

## Controlling Inputs

Read directly from disk:

- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_NEXT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_INPUT_ONLY_PACKET_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json`
- Relevant upstream packet/result/control artifacts referenced by G12_NOFILL and the NOFILL source ledger, including OTI1/2/3/4/5, CNR T3, G12 T3, and OTB rebuild ledgers.

## Owner Hardening

Operate at maximum practical reasoning depth and take as much time and as many internal steps as needed inside hard safety boundaries.

Mandatory virtues:

- Curiosity: actively hunt every source-safe path to close lifecycle state. Do not stop at "missing" before searching local roots, prior worktrees, builders, hashes, shadow logs, pipeline state, knowledge base, and raw/cached data.
- Truthfulness: never fake closure. If a row cannot be source-closed, record exactly what was searched and what file/field/schema/logger/parser/as-of rule is missing.
- Active creativity: do not stay boxed by the current row family, timeframe, data modality, worktree files, instrument, or first framing. Use local heavy data and prior artifacts creatively, then keep evidence claims strict.

Small `n` is not a reason to stop. Small `n` blocks validation/promotion only. Build the source closure packet or exact expansion/capture requirements.

Negative and blocked evidence are first-class: for every family that cannot close, write failure anatomy and exact next capture requirements.

## Anti-Boxing Search Rules

Worktree absence is not data absence. Search current worktree and absolute roots as needed:

- `C:\Users\MSI\Documents\ai-trading-agent`
- `C:\Users\MSI\Documents\ai-trading-agent\research`
- `C:\Users\MSI\Documents\ai-trading-agent\data`
- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\data\external`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`
- `C:\Users\MSI\Documents\ai-trading-agent\pipeline_state`
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base`
- `C:\tmp\gtos_otb`

Use structured parsers for JSON/JSONL/CSV/parquet when available. Recompute source hashes. Record every searched root and consumed file. If read-only MT5 tick/rates extraction would materially close a source gap, write the exact requested extraction manifest and request access before doing it. Do not call MT5 account/order/history, broker actual-R, paid/API/Databento, credentials, or remotes.

## Required Contract

Freeze `NOFILL_LIFECYCLE_CLOSURE_SOURCE_CONTRACT_V1` before scanning/classifying rows. It must define:

- allowed source inputs;
- allowed closure labels;
- exact as-of/frozen observation rules;
- quote/tick/lower-timeframe coverage rules;
- parser/scale and same-bar ambiguity policy;
- source hash requirements;
- forbidden fields;
- duplicate denominator policy;
- validation/promotion blockers.

Possible closure labels may include, but are not limited to:

- `pending_still_open_at_frozen_horizon_source_confirmed`;
- `pending_cancelled_before_entry_touch_source_confirmed`;
- `pending_expired_before_entry_touch_source_confirmed`;
- `entry_touched_no_fill_source_confirmed`;
- `entry_not_touched_before_terminal_area_source_confirmed`;
- `terminal_order_unclaimed_due_same_bar_or_ltf_gap`;
- `source_blocked_missing_price_compatible_path`;
- `source_blocked_missing_pending_lifecycle_fields`;
- `source_blocked_missing_top_level_symbol_session_side`;
- `not_closure_contract_eligible`.

If better labels are justified, define them before use. Do not use labels that imply R/performance or live results.

## Required Outputs

Write under:

`research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/`

Required artifacts:

- `NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_ROW_PACKET_2026-05-08.json` plus `NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl` if any rows clear
- `NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.md` and `.json`
- `NOFILL_CLOSE_G12_AUDIT_PROMPT_PACK_2026-05-08.md`
- `NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/focused test scripts where useful.

## Verification

Before completion:

- parse all generated JSON/JSONL;
- verify row universe is anchored to G12_NOFILL accepted input rows;
- verify six T3 rows and 94 blocked CNR061 rows remain excluded;
- recompute source hashes for consumed files;
- no-leak scan for forbidden fields and overclaim language;
- duplicate/sample-floor checks;
- prove contract was written before row scan/classification;
- run `py_compile` on builder/verifier/test scripts;
- run focused pytest if tests exist;
- run forbidden live-surface diff over `src`, `prompts`, `config`, canaries, risk, execution, permissions, safety, selectors, MT5 order/account surfaces, paid/API/Databento, credentials, remote, and order-behavior paths.

## Stop Condition

Complete only when every accepted G12_NOFILL family has either source-closed packet rows or exact actionable blockers; every source gap names exact missing field/file/schema/logger/parser/as-of rule/access; next G12 prompt pack exists; verification passes; and completion audit can mark goal complete.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` in every artifact.
