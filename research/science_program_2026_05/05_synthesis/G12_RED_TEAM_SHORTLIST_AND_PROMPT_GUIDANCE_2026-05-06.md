# G12 Red-Team Shortlist And Prompt Guidance - 2026-05-06

**Lane:** `G0`
**Target lane:** `G12`
**Status:** `G12_READY_AFTER_G0_CD2_RECONCILIATION`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Generated at UTC:** `2026-05-06T11:29:13Z`
**G12 controlling prompt:** `research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md`

## Final Launch Instructions

- Run in C:\tmp\gtosg\G12 using the G12 controlling prompt.
- Start from G0_CD2_RECONCILIATION_2026-05-06.md/json, then inspect master registries and each CD2 artifact.
- Treat the two CD2 preregs in the master preregistry as research-only rows, not validated or promotion-safe rows.
- Decide whether blocked proposal rows need schema cleanup, rejection, or a future owner question.
- Preserve validation_safe=false unless explicit blocker-clearing source evidence exists.
- Return red-team findings as files only; do not touch live trading surfaces.

## Required First Reads

- `research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.json`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json`
- `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json`

## CD2 Red-Team Addendum

| Topic | Rows or artifacts | Review question |
| --- | --- | --- |
| `G12-CD2-RT-01` Registered CD2 prereg safety | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001, EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001 | Do the two master-registered CD2 preregs remain schema-safe, outcome-closed, label-separated, and blocked from promotion? |
| `G12-CD2-RT-02` Proposal-only rows blocked from master | CD2-01, CD2-05, CD2-07, CD2-08 | Should any proposal be rejected or converted into a future machine-readable schema row, and what blocker evidence is required first? |
| `G12-CD2-RT-03` K55/orderflow provenance boundary | CD2-04, HYP-G9G4-K55-SOURCE-006, HYP-G4-OFI-DEPTH-001 | Can K55 consume only source-status/provenance flags while raw orderflow/depth values and validation-safe claims remain quarantined? |
| `G12-CD2-RT-04` Execution/path label separation | CD2-06, G10-HYP-PREFILL-003, G6-HYP-002, HYP-G4-FILL-QUALITY-009 | Are lifecycle/no-fill, synthetic path-R, same-bar ambiguity, and broker actual-R boundaries explicit enough to prevent mixed labels? |
| `G12-CD2-RT-05` Global source validation boundary after CD2 | all source_contract_v2 rows, CD2-01, CD2-04, CD2-07, CD2-08 | Do any CD2 reports imply source validation safety despite all source_contract_v2 rows remaining validation_safe=false? |

## Standing Wave-2 Shortlist

G12 must also retain the prior wave-2 shortlist: G11 no-leak semantic inversion, unregistered source placeholders, broker actual-R scarcity, macro/vol publication leakage, execution/path label separation, old G6 normalization residue, and global `validation_safe=false` source boundary.

## Forbidden

- No live trading prompt changes.
- No risk, execution, permissions, selector, safety-gate, MT5, canary, paid-data, credential, remote, or order-behavior changes.
- No source marked `validation_safe=true` without explicit blocker-clearing evidence.
- No promotion claim.

## NO_PROMOTION_VERDICT

G12 is a red-team lane only. It may recommend blocker cleanup or rejection; it may not promote CD2 rows.
