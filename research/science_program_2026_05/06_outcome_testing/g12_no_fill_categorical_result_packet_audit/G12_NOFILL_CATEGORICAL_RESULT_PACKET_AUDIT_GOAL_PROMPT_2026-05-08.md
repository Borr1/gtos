# G12 NOFILL Categorical Result Packet Audit Goal Prompt

Date: 2026-05-08
Lane: G12_NOFILL_CATEGORICAL_RESULT_PACKET_AUDIT_V1
Worktree: C:\tmp\gtos_otb\G12NOFILLCAT
Promotion posture: NO_PROMOTION_VERDICT

## One-Line Starter

`/goal Run G12_NOFILL_CATEGORICAL_RESULT_PACKET_AUDIT_V1 using C:\tmp\gtos_otb\G12NOFILLCAT\research\science_program_2026_05\06_outcome_testing\g12_no_fill_categorical_result_packet_audit\G12_NOFILL_CATEGORICAL_RESULT_PACKET_AUDIT_GOAL_PROMPT_2026-05-08.md as the controlling prompt; complete mandatory GTOS preflight, independently audit NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1, decide accept/block/reject as categorical lifecycle-only evidence, pursue every ambiguity to proof-or-impossibility, preserve context in committed artifacts, request access if needed, and do not touch live trading prompts, risk, execution, permissions, safety gates, selectors, MT5 order/account paths, canaries, paid/API/Databento calls, credentials, remotes, registry promotion flags, validation flags, outcome-review flags, or order behavior.`

## Objective

Independently red-team audit `NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1` and decide whether it is accepted, blocked, or rejected as categorical lifecycle-only evidence.

This is an audit lane, not a new result lane. Do not compute or reinterpret R, performance, expectancy, win rate, broker actual-R, account history, live order/deal/position labels, hidden labels, validation, promotion, or live effect.

The goal is complete only when G12 writes machine-checkable accept/block/reject decision artifacts, verifies the packet from source artifacts, and records exact next-lane guidance for every accepted or blocked family.

## Mandatory Preflight

Before any audit work:

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this controlling prompt again after preflight.
10. Create a G12 context anchor before auditing rows. It must record current HEAD, controlling inputs, prompt path, active question stack, source roots searched, hard boundaries, route decisions, and instruction coverage.

If there is a resume, conversation compaction, context uncertainty, or long interruption, regenerate `LIVE_STATE`, reread this prompt and core context docs, reread the latest lane artifacts, and continue from committed state.

## Controlling Inputs

Read these directly from disk:

- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_NEXT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_COMPLETION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_PACKET_MANIFEST_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_FAILURE_LEARNING_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/build_nofill_lifecycle_categorical_result_packet_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/verify_nofill_lifecycle_categorical_result_packet_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/test_nofill_lifecycle_categorical_result_packet_2026_05_08.py`
- Upstream contract/source artifacts from `no_fill_lifecycle_result_contract_design`, `no_fill_lifecycle_closure_source_packet`, `no_fill_lifecycle_closure_source_correction`, `g12_no_fill_correction_reaudit`, and `otr061_xau_tick_recovery`.

If an input appears missing in this worktree, search `C:\Users\MSI\Documents\ai-trading-agent`, `C:\tmp\gtos_otb`, and relevant prior worktrees before accepting absence.

## Starting Facts To Preserve

- Source universe is exactly `298` G12-accepted source-closed no-fill rows.
- Eligible categorical rows: `52`.
- Blocked-before-label rows: `246`.
- Row-level category counts: `{"nofill_terminal_before_entry": 52}`.
- Row `NOFILL-CLOSE-ROW-0127` OTR061 SHA256 remains `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff` with first terminal-area touch `2026-05-06T07:15:00.634000Z`, but it remains result-blocked by missing prereg opening-drive fields.
- Six T3 rows and all 94 G12-blocked CNR061 rows remain excluded.
- All outputs preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## G12 Audit Questions

Answer these with files, not chat:

- Does the packet truly cover exactly the accepted 298 source-closed rows?
- Are the 52 labels assigned only after row-level eligibility decisions?
- Are all 52 labels defensible as categorical lifecycle-only `nofill_terminal_before_entry` evidence?
- Are all 246 blockers exact, non-lazy, and source/contract-valid?
- Do any blocked rows actually have source-safe evidence that should have been found through local-heavy-data search?
- Are duplicate conflicts handled correctly, including the 42 otherwise-labelable rows across 3 conflicted `nofill_duplicate_key` groups?
- Is row 0127 correctly blocked before label despite OTR061 tick evidence because it lacks the required prereg opening-drive fields?
- Are M1/M5 OHLC rows kept as price-compatible context only rather than quote-valid categorical evidence?
- Are the six T3 rows and 94 G12-blocked CNR061 rows strictly excluded?
- Do packet rows contain any forbidden R/performance/account/live/order/hidden/result fields?
- Does the verifier prove the right thing on main despite unrelated live-monitoring runtime dirt?
- What exact next lane should run after this: accept categorical evidence, run a source-correction lane, run contract revision, split blockers by family, or stop?

## Hardening Standard

Operate at maximum practical reasoning depth and take as much time and as many internal steps as needed inside the hard boundaries.

Enforce:

- Curiosity: search beyond the obvious packet summary and actively look for hidden source/context issues, duplicated denominators, stale artifacts, alternate local-heavy-data evidence, and better next hypotheses.
- Truthfulness: do not rescue weak labels, hide blockers, or turn categorical evidence into performance. If a label or blocker is wrong, say exactly why.
- Active creativity: think beyond the first framing and propose source-safe next routes, but keep all claims bound to data and prereg contracts.

Anti-boxing rule: listed files and examples are starting points, not limits. Search builders, tests, JSON/JSONL, source projections, manifests, raw/cached folders, git history, neighboring lane outputs, `C:\Users\MSI\Documents\ai-trading-agent\data`, `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`, `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`, and `C:\tmp` if needed before accepting a data-missing blocker.

Small-N rule: small n blocks validation and promotion, not research. If categories are too small, freeze the denominator, explain exact sample-floor posture, and write an expansion or blocker path.

Negative and blocked rows are first-class evidence. Audit why each family is blocked and what this teaches about future no-fill/fill/no-entry hypotheses. Do not write lazy "future work"; write exact source, field, parser, or contract requirements.

Request access when needed. Use `curl`/webfetch only for lane-authorized public/source-contract evidence and save raw capture/source index. Do not use paid/API/Databento or MT5 order/account calls here.

## Allowed Work

- Read and audit all no-fill categorical packet artifacts.
- Re-run packet verifier and focused pytest.
- Recompute or independently check source hashes where feasible.
- Write G12 decision, source/no-leak, duplicate/sample-floor, blocker, learning, next-prompt, and completion artifacts.
- Add a G12 builder/verifier/test if useful.
- Update `.context\00_core\research_current_state.md` if the research map materially changes.

## Forbidden Work

Do not:

- compute R, synthetic path-R, broker actual-R, expectancy, win rate, validation lift, promotion value, DSR/PBO, or live effect;
- read account history, broker actual-R, live trade outcome labels, live order/deal/position labels, hidden labels, blocked-packet outcomes, or post-outcome fields;
- score or relabel the six T3 rows or 94 blocked CNR061 rows;
- edit master registries, source validation flags, promotion flags, selectors, live prompts, risk, execution, permissions, safety gates, MT5 order/account code, canaries, credentials, remotes, or order behavior;
- run paid/API/Databento calls or MT5 order/account/history calls;
- mark any source `validation_safe=true`, set `outcome_review_opened=true`, set `live_effect=true`, or remove `NO_PROMOTION_VERDICT`.

## Required Output Directory

Write scoped artifacts only under:

`research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/`

Expected artifacts:

- `G12_NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_DECISION_LEDGER_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_SOURCE_HASH_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_BLOCKER_REVIEW_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_LEARNING_LEDGER_2026-05-08.md` and `.json`
- `G12_NOFILL_CAT_NEXT_PROMPT_PACK_2026-05-08.md`
- `G12_NOFILL_CAT_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/test files if useful.

## Verification Requirements

Before marking complete:

- Parse all generated JSON and upstream packet JSON/JSONL.
- Verify exact `298 = 52 eligible + 246 blocked`.
- Verify all assigned labels equal `nofill_terminal_before_entry`.
- Verify row-level eligibility/blocker decisions precede labels.
- Verify source hashes and source/as-of references.
- Verify no overlap with six T3 rows or 94 G12-blocked CNR061 rows.
- Verify no forbidden R/performance/account/live/order/hidden/result fields.
- Verify duplicate conflicts and sample-floor posture.
- Verify `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Run `py_compile` for new Python files.
- Run focused pytest if tests are written.
- Run forbidden live-surface diff against committed lane scope and record unrelated runtime dirt separately.

## Stop Condition

Do not finish until G12 has:

1. accepted, blocked, or rejected the packet as categorical lifecycle-only evidence;
2. identified exact blockers or correction routes for the 246 blocked rows;
3. stated what the 52 labels prove and do not prove;
4. written the next prompt pack;
5. passed verification; and
6. committed scoped artifacts.
