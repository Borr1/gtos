# NOFILL Closure Source Correction Goal Prompt - 2026-05-08

## Starter Message

Use the one-line starter message from the owner, but treat this file as the controlling prompt.

## Goal

Run `NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1` as a source-only correction lane after G12 audited the NOFILL close packet.

The goal is to make the upstream `NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1` artifacts internally consistent with G12's corrected audit state:

- upstream reported state: `298` rows, `297 source_closed`, `1 source_blocked_exact`;
- G12 corrected state: `298` rows, `298 source_closed`, `0 source_blocked_exact`;
- corrected row: `NOFILL-CLOSE-ROW-0127`;
- clearing source: `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet`;
- SHA256: `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`;
- source coverage: `2026-05-06T07:10:01.820Z` through `2026-05-06T11:15:59.763Z`;
- source-only event: terminal-area side-aware touch first observed at `2026-05-06T07:15:00.634000Z`.

This lane must not score R/performance or open a result lane. It must update or rebuild source/control artifacts only.

## Mandatory GTOS Preflight

Before using memory:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered file in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. If context is stale, read the newer artifacts directly and record the stale-context condition in the context anchor.

## Controlling Inputs

G12 audit and next-lane guidance:

- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_NEXT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/build_g12_nofill_close_audit_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/verify_g12_nofill_close_audit_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/test_g12_nofill_close_audit_2026_05_08.py`

Upstream NOFILL close packet to correct:

- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_PACKET_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/build_nofill_lifecycle_closure_source_packet_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/verify_nofill_lifecycle_closure_source_packet_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/test_nofill_lifecycle_closure_source_packet_2026_05_08.py`

Clearing source:

- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/`

## Owner Hardening Standard

This is a maximum-effort source correction task, not a quick patch.

The three required research virtues apply:

- Curiosity: actively ask what other stale blocker, source-boxing, local-heavy-data miss, count mismatch, no-leak bug, or verifier weakness this correction reveals.
- Truthfulness: do not overstate the correction. It clears source closure only; it does not create R/performance evidence.
- Active creativity: search non-obvious but approved local paths, prior lane outputs, hash ledgers, code history, and source manifests before calling anything missing.

Rules:

- Go to proof-or-impossibility. If row `0127` or any related file cannot be corrected cleanly, write the exact blocker and why.
- Treat worktree-local absence as insufficient. Search absolute local heavy-data roots and prior output lanes before declaring missing data.
- Preserve a context anchor, active question stack, searched-root ledger, route-decision ledger, and instruction-coverage checklist.
- After resume or compaction, regenerate `LIVE_STATE`, re-read this prompt and the core context docs, re-read latest lane artifacts, and continue from committed state.
- Small sample size is not a correction blocker; this is not a validation lane.
- Negative findings and non-promotable status must still produce learning.

## Required Work

1. Reconstruct G12's correction from source:
   - locate and hash the OTR061 XAUUSD tick recovery parquet;
   - verify it covers the row `0127` source window enough for source-only terminal-sequence closure;
   - verify the first relevant terminal-area side-aware touch timestamp used by G12;
   - prove this uses no broker/account/live/order/hidden result labels and no R/performance scoring.

2. Correct upstream NOFILL close artifacts:
   - update row `NOFILL-CLOSE-ROW-0127` from `source_blocked_exact` to source-closed input-only terminal-sequence source evidence;
   - remove or supersede the stale `BLOCKED_NO_TICKS_IN_WINDOW` blocker for that row;
   - remove or mark the old read-only extraction manifest as superseded by existing local source evidence;
   - update source-search/source-hash/no-leak ledgers to include the OTR061 source file and hash;
   - update row counts to `298 source_closed`, `0 source_blocked_exact`;
   - keep all fields source-only and no-leak safe;
   - update completion audit and companion markdown.

3. Harden upstream builder/verifier/test logic:
   - before emitting `BLOCKED_NO_TICKS_IN_WINDOW`, search prior tick recovery lanes and absolute local heavy-data roots;
   - make this search path auditable, deterministic, and source-hashed;
   - add/adjust tests so row `0127` must be source-closed from the OTR061 parquet;
   - verify six T3 rows and 94 G12-blocked CNR061 rows remain excluded;
   - keep duplicate/sample-floor validation-blocked.

4. Write correction-lane artifacts under:

`research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/`

Required correction artifacts:

- `NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_CORR_PATCH_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md` and `.json`
- `NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.md` and `.json`
- `NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md`
- `NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/test for the correction lane if useful.

## Verification Requirements

Before marking complete:

- JSON/JSONL parse for all updated and new machine-readable artifacts.
- Recompute strict SHA256 for OTR061 parquet and every source file cited by the corrected packet.
- Verify packet counts: `298` total, `298 source_closed`, `0 source_blocked_exact`.
- Verify row `NOFILL-CLOSE-ROW-0127` is source-closed and no stale extraction request remains active.
- Verify six T3 rows and 94 G12-blocked CNR061 rows remain excluded.
- Run no-leak scan for forbidden R/performance/account/live/order/hidden/result fields.
- Verify `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Run `python -B -m py_compile` on changed/new scripts.
- Run focused pytest for upstream NOFILL close and the correction lane.
- Run G12 NOFILL close verifier if relevant after correction.
- Run forbidden live-surface diff over `src`, `prompts`, `config`, canaries, execution, risk, permissions, safety, selectors, MT5 order/account, paid/API/Databento, credentials, remotes, and order-behavior paths.
- Regenerate `LIVE_STATE` at closeout and record freshness.

## Allowed Write Scope

Allowed:

- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/`
- `.context/00_core/research_current_state.md`
- `.context/LIVE_STATE.md`

Do not edit master registries unless the correction prompt explicitly creates a proposed patch artifact. Do not touch live trading surfaces.

## Hard Boundaries

Do not:

- score R/performance, win rate, expectancy, DSR/PBO, validation, promotion, or live effect;
- inspect broker actual-R, account history, live trade results, live orders, or hidden labels;
- score blocked CNR061 rows;
- execute MT5 order/account calls;
- use paid/API/Databento calls;
- change live prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, credentials, remotes, or order behavior;
- mark any source `validation_safe=true`;
- set `outcome_review_opened=true`;
- claim promotion or validation.

## Stop Condition

This goal is complete only when the corrected upstream source packet and correction audit prove `298 source_closed + 0 source_blocked_exact`, all source hashes and no-leak checks pass, row `0127` is source-closed from existing local OTR061 evidence, stale blocker/extraction request state is resolved, verifiers/tests pass, and next G12 reaudit guidance is written. Chat-only conclusions are not complete.
