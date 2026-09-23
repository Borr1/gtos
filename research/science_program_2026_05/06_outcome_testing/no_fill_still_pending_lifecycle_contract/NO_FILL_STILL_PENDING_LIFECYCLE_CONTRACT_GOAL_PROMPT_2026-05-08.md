# No-Fill / Still-Pending Lifecycle Contract Goal Prompt - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Goal

Build `SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1` for the 298 `CNR_T3` `not_packet_eligible` rows as a new source-safe lifecycle/no-fill/no-entry/still-pending/source-blocked/terminal-order-unclaimed contract. This is a research-control and input-packet lane only. It must not compute R, performance, win rate, expectancy, DSR, PBO, validation, promotion, or live-edge claims.

## Mandatory Preflight

Before making decisions or writing output:

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Skim `.context/00_READING_ORDER.md`.
9. Write a context anchor before downstream decision artifacts. The anchor must record current HEAD, this prompt path, controlling inputs read, active question stack, searched roots, source boundaries, forbidden fields, and stop-condition checklist.

## Controlling Inputs

Read these directly from disk. Do not rely on chat summaries:

- `research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/G12_CNR_T3_NEXT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/G12_CNR_T3_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json`
- Relevant upstream row sources named by the T3 inventory and blocker ledger, including OTI1, OTI2, OTI3, OTI4, OTI5, OTI8, G12 OTI audits, OTB packet builders, and source/no-leak ledgers.

## Owner Hardening

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside the hard safety boundaries. This is not a quick summary task.

Mandatory virtues:

- Curiosity: actively search for ways lifecycle/no-fill/no-entry/still-pending evidence could improve GTOS understanding. Do not stay boxed by the first lane framing, current timeframe, current instrument, worktree-local files, known GTOS edge, default labels, or common trading-strategy vocabulary.
- Truthfulness: do not fake, rescue, soften, or relabel failures. If a row cannot be classified from source-safe inputs, say exactly what is missing and what was searched.
- Active creativity: explore non-obvious source-safe routes, parsers, ledgers, worktree artifacts, local heavy-data paths, source contracts, and previous research outputs. Creative hypotheses are welcome; evidence claims must remain source-bound and preregistered.

Do not stop because `n` is small. Small `n` can block validation and promotion only. If sample size is small, define the denominator, search for source-safe expansion rows, and either build the expansion inventory or prove exactly why expansion is impossible from approved inputs.

Negative and blocked evidence are first-class. For each blocked family, produce failure anatomy: what input/source state exists, what is missing, whether the blocker is source/data/methodology/label-family/sample-floor/forbidden-field based, and what exact capture or contract would close it.

## Anti-Boxing Search Rules

Worktree absence is not data absence. Search both the current worktree and absolute local roots, including where relevant:

- `C:\Users\MSI\Documents\ai-trading-agent`
- `C:\Users\MSI\Documents\ai-trading-agent\data`
- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\data\external`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`
- `C:\Users\MSI\Documents\ai-trading-agent\pipeline_state`
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base`
- `C:\Users\MSI\Documents\ai-trading-agent\research`
- `C:\tmp\gtos_otb`

Use `rg`, `git log`, `git show`, JSON/JSONL parsing, source hashes, and focused scripts as needed. If a source appears absent in the worktree, check the absolute main root before declaring a blocker. Record every searched root and the exact files consumed or missing.

Curl/webfetch/public web evidence is allowed only if the lane needs source-contract or public documentation evidence and local cached artifacts are insufficient. Save raw captures and a source index. Paid/API/Databento/MT5 account/order/history calls require an explicit manifest and owner approval before use. Read-only local file inspection is allowed. Request access when needed instead of silently stopping.

## Scope And Classification Task

Reconstruct the 298 exact `not_packet_eligible` rows from the G12 T3 audit and upstream T3 source packet. Preserve the exclusion of:

- the six accepted T3 `stop_after_original_horizon` rows,
- the 94 G12-blocked CNR061 rows,
- any row requiring broker actual-R, account history, live trade result, live order state, hidden path labels, or blocked-packet outcome inspection.

Create a new frozen contract before classification or source scanning. Do not reuse `CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1` labels. The new contract should split, at minimum, these families if source-safe evidence exists:

- no-fill or pending order never became executable/touched,
- no-entry or setup never armed before the observation horizon,
- still-pending at the frozen observation horizon,
- source-blocked because required as-of fields are missing,
- terminal-order-unclaimed because same-bar or lower-timeframe order cannot be proven,
- not contract-eligible under this separate lifecycle contract.

If different or better labels are justified by the data, define them in the frozen contract before use. Do not create labels after seeing outcome/performance.

For every row, produce one of:

- an input-only source-hashed lifecycle/no-fill row under the new contract,
- an exact blocker with the missing source/file/field/as-of/hash/parser/logger/approval named,
- a proof that the row belongs to another future route, not this contract.

## No-Leak Boundaries

Forbidden as decision or packet fields:

- `synthetic_r`, `broker_actual_r`, account-history results, live trade results, live order state,
- hidden path labels, blocked-packet outcomes, post-outcome terminal ordering,
- win rate, expectancy, DSR/PBO, validation, promotion, live-effect claims.

You may read prior outcome-testing artifacts only to reconstruct row identity, family, source-contract status, and already quarantined audit boundaries. If an upstream artifact contains R or performance fields, do not carry those fields into the new contract packet and record that they were excluded.

## Required Outputs

Write artifacts under:

`research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/`

Required artifacts:

- `NOFILL_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.md` and `.json`
- `NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.md` and `.json`
- `NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_INPUT_ONLY_PACKET_2026-05-08.json` plus `NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl` if any rows clear the contract
- `NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_FORENSICS_AND_LEARNING_2026-05-08.md` and `.json`
- `NOFILL_G12_AUDIT_PROMPT_PACK_2026-05-08.md`
- `NOFILL_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/focused test scripts where useful.

## Verification

Before completion:

- parse all generated JSON/JSONL;
- verify the 298-row universe is exact and the six T3 rows and 94 blocked CNR061 rows are excluded;
- recompute source hashes for every consumed source file;
- run a no-leak scan for forbidden keys and forbidden value claims;
- run duplicate/sample-floor checks;
- prove the frozen contract was written before classification/source scanning;
- run `py_compile` on builder/verifier/test scripts;
- run focused pytest if a test exists;
- run forbidden live-surface diff checks over `src`, `prompts`, `config`, `scripts/canary`, MT5 order/account surfaces, risk, execution, permissions, safety, selectors, credentials, remote, paid/API/Databento, and order-behavior paths.

## Stop Condition

The goal is complete only when it has produced the source contract, family split inventory, source search/hash ledger, input-only packet or proof of no clearable packet rows, no-leak/duplicate/sample-floor audit, exact blocker/impossibility ledger, forensics/learning ledger, G12 audit prompt pack, verification evidence, and completion audit.

Every blocker must be actionable. "Needs more data" is insufficient unless it names the exact data, source, field, schema, logger, parser, legal/access proof, owner approval, or capture requirement.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` in every artifact. Do not touch live trading prompts, risk, execution, permissions, safety gates, selectors, MT5 order/account paths, canaries, paid data, credentials, remote pushes, or order behavior.
