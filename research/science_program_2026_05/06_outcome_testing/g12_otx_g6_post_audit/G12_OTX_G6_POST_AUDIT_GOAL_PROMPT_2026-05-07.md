# G12 OTX G6 Post-Audit Goal Prompt

Date: 2026-05-07
Owner lane: G12 red team / methodology audit
Scope: research/outcome-testing control only
Promotion posture: NO_PROMOTION_VERDICT

## Objective

Run the G12 post-audit of the OTX G6 tick-aware end-to-end resolution. Do not produce a chat-only summary. Produce committed G12-owned audit artifacts that decide, with proof-or-impossibility discipline, what is actually accepted, blocked, rejected, or ready for a future quarantined result lane.

This goal must not stop at "needs G12 review" because this session is the G12 review. It must inspect the OTX source chain deeply enough to either accept the OTX decisions, overturn them with evidence, or record exact impossibility and exact next unblockers.

This is a saturation audit. A blocker is not acceptable until the session has pursued every approved local path that could clear it, including absolute main-repo ignored/untracked data paths, committed builders, packet JSON/JSONL, source ledgers, shadow-log provenance, git history, and prior lane artifacts. The correct terminal state is proof, rejection with evidence, or impossibility with an exact unblocker.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Record HEAD and freshness in the completion audit.

If Git reports dubious ownership or path permissions, request access. Do not silently skip preflight.

## Context Freshness Contract

The session must treat context freshness as part of the objective.

- If `.context/LIVE_STATE.md` reports stale or unknown research context, do not continue from memory. Read `git log --oneline -20`, identify the newest research/outcome-testing commits, read the newer artifacts directly, and record the freshness repair in the completion audit.
- Read this prompt file from disk after preflight and treat it as the controlling instruction if any older handoff or context file conflicts.
- Read `.context/00_core/goal_session_research_discipline.md` and enforce the owner instruction: proof-or-impossibility, no lazy summaries, no vague blockers, request access when needed, and produce committed files.
- If context files are stale but the exact artifact evidence is sufficient, the goal may proceed, but the completion audit must name the stale file, the commits/artifacts read to compensate, and whether `.context/00_core/research_current_state.md` was updated.

## Controlling Inputs

Primary OTX directory:

- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/`

Required OTX files to read directly:

- `OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md/json`
- `OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-07.md/json`
- `OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md/json`
- `OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.md/json`
- `OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md/json`
- `OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.md/json`
- `OTX_G6_OTI4B_QUARANTINED_RESULT_ROWS_2026-05-07.jsonl`
- `OTX_G6_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md/json`
- `OTX_G6_ADVERSARIAL_SELF_REVIEW_2026-05-07.md/json`
- `build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py`
- `test_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py`

Prior context to read directly:

- `research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/`
- `research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results/`
- `research/science_program_2026_05/06_outcome_testing/otb6_g6_blocker_clearing_proof_pack/`
- `research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/`
- `research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`

Absolute data-source rule:

- Before accepting any "missing tick data" or "worktree missing data" blocker, inspect the absolute main-repo data path `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`.
- If a worktree lacks ignored/untracked data, that is not proof of absence. Use the absolute main path, hash any source file you use, and record the exact source path/hash in the audit.
- Do not use broker actual-R, account history, MT5 calls, live order state, or blocked-packet outcome sources.

Local saturation search must include, where relevant:

- `data/ticks/` in both the worktree and `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`;
- `shadow_logs/` only for source/provenance discovery unless the lane explicitly allows a non-result field; do not consume result-bearing or broker actual-R fields;
- packet/projection/cache folders under `research/science_program_2026_05/06_outcome_testing/`;
- builders/tests for OTB2R, G6PACKETS, OTB6, OTX, OTI4, G12 packet audit, and G12 OTB rebuild audit;
- `git log`, `git show --name-only`, and targeted `rg` searches for packet IDs, experiment IDs, source hashes, and missing row timestamps.

## Packet Decisions Required

Audit all five OTX target packets. Each packet must end with exactly one terminal G12 decision and a reason:

- `OTG0-PKT-060`: accept or overturn OTX's "blocked with exact impossibility from approved local ticks". To overturn, find a valid as-of mechanical OB bounds/source-row artifact with row hash, H1 OB id, bounds, creation UTC, impulse BOS UTC, mitigation state, and touch sequence. If not found after local saturation, write exact future instrumentation requirements.
- `OTG0-PKT-061`: accept or overturn OTX's "blocked with exact partial tick coverage". Search the absolute main tick path for the missing `XAUUSD 2026-05-06 07:15 UTC` quote/path evidence before accepting the blocker. If still missing, name the exact missing file/window/source.
- `OTG0-PKT-062`: audit OTX's quarantined OTI4B discovery result. Decide whether it is accepted as quarantined discovery evidence only, rejected, or blocked. Verify row exclusions, duplicate denominator, synthetic-vs-actual label separation, same-bar policy, DSR/PBO/effective-N status, sample floor, and source hashes. Do not promote.
- `OTG0-PKT-063`: audit the CUSUM/changepoint rebuilt packet proposal. Decide whether it is accepted for a future quarantined outcome audit, blocked with exact row/source questions, or rejected for leakage/methodology/source invalidity. If accepted, freeze the allowed subset/exclusion policy and write the next result-lane prompt in the prompt pack.
- `OTG0-PKT-066`: audit the sweep/round-number rebuilt packet proposal. Decide whether it is accepted for a future quarantined outcome audit, blocked with exact row/source questions, or rejected for leakage/methodology/source invalidity. If accepted, freeze the allowed subset/exclusion policy and write the next result-lane prompt in the prompt pack.

## Depth Requirements

This is a maximum-effort red-team audit, not a shallow review.

- Recompute or independently verify source hashes where practical.
- Re-run the OTX focused test and `py_compile`.
- Inspect OTX builders and tests for hardcoded conclusions, hidden outcome fields, same-bar assumptions, duplicate denominator errors, parser shortcuts, or path labels leaking into input packets.
- Read the relevant JSON/JSONL rows, not only Markdown summaries.
- Search local artifacts, git history, source projections, manifests, shadow logs, and data folders before declaring any blocker.
- If a new ambiguity appears, pursue it locally until resolved or impossible. Write the searched paths/patterns, row IDs, timestamps, commands/patterns used, positive evidence, negative evidence, and the exact reason it cannot be resolved from current approved inputs.
- If the audit can clear a row or packet without opening prohibited outcomes, it must clear it before writing a blocker.
- If the audit rejects an OTX conclusion, it must show the exact contradiction and produce the corrected packet/status artifact.
- Do not use `BLOCKED` as a safe default. Valid terminal states are: accepted as quarantined discovery only, accepted for future quarantined outcome audit with frozen subset/exclusions, blocked with exact impossibility/next unblocker, or rejected invalid clearing with evidence.
- Request access when needed. Use curl/webfetch only if official/public source-contract evidence is required and local cache is insufficient; save raw captures and a source index. No paid/API/Databento calls in this G12 audit unless a pre-call manifest and explicit owner approval are written first.

## Required Outputs

Write only under:

- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/`

Required artifacts:

- `G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md/json`
- `G12_OTX_G6_LEAKAGE_NOLEAK_AUDIT_2026-05-07.md/json`
- `G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.md/json`
- `G12_OTX_G6_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.md/json`
- `G12_OTX_G6_METHOD_STATS_AUDIT_2026-05-07.md/json`
- `G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07.md/json`
- `G12_OTX_G6_BLOCKER_ACTION_MAP_2026-05-07.md/json`
- `G12_OTX_G6_NEXT_LANE_PROMPT_PACK_2026-05-07.md`
- `G12_OTX_G6_COMPLETION_AUDIT_2026-05-07.md/json`
- A small builder/verifier script and focused tests if needed to make the audit machine-checkable.

The next-lane prompt pack must include one-line `/goal` starter prompts, worktree/data-path instructions, controlling input files, and stop conditions for every accepted follow-up lane. If no future result lane is justified, the prompt pack must say so explicitly and identify the next exact data/instrumentation task instead.

## Verification

Before marking complete:

- JSON parse every generated JSON/JSONL artifact.
- Run `python -B -m py_compile` on any generated Python scripts.
- Run focused pytest for generated tests and the OTX test.
- Scan G12 artifacts for `NO_PROMOTION_VERDICT`.
- Confirm no generated JSON has `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Confirm no forbidden live-surface diff under `src`, `prompts`, `config`, `scripts/canary`, MT5, execution, permissions, safety gates, selectors, credentials, remote pushes, or order behavior.
- Regenerate `.context/LIVE_STATE.md` at closeout and update `.context/00_core/research_current_state.md` only if this G12 audit changes the durable research map.
- Confirm the completion audit contains a per-packet saturation ledger with paths searched, evidence found, negative evidence, and final terminal decision.

## Forbidden

Do not edit live trading prompts, risk, execution, permissions, safety gates, selectors, MT5 integration, canaries, credentials, remote state, order behavior, or master registries. Do not open broker actual-R or live trade outcome sources. Do not set `validation_safe=true`, `outcome_review_opened=true`, or any promotion verdict. Do not call paid/API/Databento sources in this lane without an explicit pre-call budget/approval artifact.

## Stop Condition

The goal is complete only when all five packets have terminal G12 decisions, every accepted/blocked/rejected decision has machine-checkable evidence, next actions are exact enough for the owner to run without another interpretation pass, and all verification checks pass.
