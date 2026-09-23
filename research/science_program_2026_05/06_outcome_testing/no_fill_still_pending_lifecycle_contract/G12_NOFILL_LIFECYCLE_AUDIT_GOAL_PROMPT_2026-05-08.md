# G12 No-Fill Lifecycle Audit Goal Prompt - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Goal

Audit `SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1` under `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/` as G12 red-team / blocker-clearing review. Decide whether the no-fill lifecycle contract and 298-row input-only packet should be accepted, blocked, or rejected as research-control lifecycle evidence. Do not compute R, performance, win rate, expectancy, DSR, PBO, validation, promotion, or live-edge claims.

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
9. Write a G12 context anchor before decision artifacts. It must include HEAD, controlling prompt paths, artifact set read, active audit questions, searched roots, source/no-leak boundaries, and completion checklist.

## Controlling Inputs

Read directly from disk, not chat:

- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_G12_AUDIT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_GOAL_PROMPT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_CONTEXT_ANCHOR_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_INPUT_ONLY_PACKET_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/build_nofill_still_pending_lifecycle_contract_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/verify_nofill_still_pending_lifecycle_contract_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/test_nofill_still_pending_lifecycle_contract_2026_05_08.py`
- The upstream CNR T3 and G12 T3 artifacts that define the 298-row universe and exclusions.

## Owner Hardening

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside the hard safety boundaries.

Mandatory virtues:

- Curiosity: actively look for source-safe contradictions, hidden family mixups, missing fields, duplicated rows, stale-route problems, and better next routes. Do not audit lazily.
- Truthfulness: accept what is actually proven, block what is actually missing, and reject only with clear evidence. Do not over-conserve by rejecting valid input-only evidence, and do not over-accept weak or leaky rows.
- Active creativity: if the artifact framing boxes the review too narrowly, search adjacent ledgers, source hashes, prior packet builders, local heavy-data roots, and previous G12 audits. Propose stronger next contracts when the data points to them, but do not convert creative explanations into validation claims.

Treat examples, listed files, current worktree, current timeframe, current instrument, first label family, and first model wording as starting points, not limits. Worktree absence is not data absence.

Search absolute local roots as needed:

- `C:\Users\MSI\Documents\ai-trading-agent`
- `C:\Users\MSI\Documents\ai-trading-agent\research`
- `C:\Users\MSI\Documents\ai-trading-agent\data`
- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`
- `C:\Users\MSI\Documents\ai-trading-agent\pipeline_state`
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base`
- `C:\tmp\gtos_otb`

If source evidence is missing, search until local pursuit is exhausted, then write the exact missing file/field/schema/logger/parser/hash/as-of rule/approval. Request access when needed. Curl/webfetch/public web is allowed only for source-contract documentation; save raw captures and an index if used. Paid/API/Databento/MT5 account/order/history calls are forbidden without explicit owner approval and are not expected for this G12 audit.

## Audit Questions

Answer these with machine-checkable evidence:

1. Is the exact 298-row universe reconstructed from the G12 CNR T3 `not_packet_eligible` set?
2. Are the six accepted T3 `stop_after_original_horizon` rows excluded?
3. Are the 94 G12-blocked CNR061 rows excluded with zero overlap?
4. Was the no-fill lifecycle contract frozen before classification?
5. Do labels avoid reusing `CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1` and correctly split no-fill still-pending, wrong-side cancellation, no-entry touch, source-blocked, local-OHLC terminal-order-unclaimed, and no-entry-touch/no-R-scored families?
6. Are source hashes recomputable, or are missing files recorded exactly?
7. Does any packet row carry forbidden R/performance/broker/account/live/order/hidden-label/blocked-outcome fields?
8. Are duplicate denominator and sample-floor controls enough to block validation/promotion while preserving research-control usefulness?
9. Does the packet prove only lifecycle/source-control state, or does any artifact accidentally imply performance?
10. What exact future source/result lanes are justified by the accepted families, and what remains blocked?

## Decision Standard

Use three terminal decisions:

- `ACCEPT_AS_INPUT_ONLY_LIFECYCLE_SOURCE_EVIDENCE`: rows are source-safe input/control evidence for future audit lanes only.
- `BLOCK_WITH_EXACT_NEXT_QUESTIONS`: one or more source/no-leak/duplicate/label-family issues require exact correction before acceptance.
- `REJECT_INVALID_CLEARING`: the contract or packet contains leakage, false universe membership, duplicate inflation, forbidden labels, or invalid clearing that should not be carried forward.

Be rigorous, not timid. Do not reject valid input-only evidence merely because it cannot validate edge/performance. Do not accept anything that leaks or overclaims. If accepted, state what it proves and what it does not prove.

## Required Outputs

Write under:

`research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/`

Required artifacts:

- `G12_NOFILL_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `G12_NOFILL_DECISION_LEDGER_2026-05-08.md` and `.json`
- `G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.md` and `.json`
- `G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.md` and `.json`
- `G12_NOFILL_NEXT_PROMPT_PACK_2026-05-08.md`
- `G12_NOFILL_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/focused test scripts where useful.

## Verification

Before completion:

- parse generated JSON/JSONL;
- recompute 298-row exactness, six-row T3 exclusion, and 94-row CNR061 blocked exclusion;
- recompute or verify source hashes;
- run no-leak scan for forbidden fields and overclaim language;
- verify duplicate/sample-floor controls;
- run `py_compile` on builder/verifier/test scripts;
- run focused pytest if tests exist;
- verify committed diff touches no live prompts, risk, execution, permissions, safety, selectors, MT5 order/account surfaces, canaries, credentials, remote, paid/API/Databento, or order-behavior files.

## Stop Condition

The goal is complete only when every audit question has a decision with evidence; accepted/blocked/rejected rows or families are explicit; next routes are actionable; and completion audit reports `can_mark_goal_complete=true`.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` in every artifact.
