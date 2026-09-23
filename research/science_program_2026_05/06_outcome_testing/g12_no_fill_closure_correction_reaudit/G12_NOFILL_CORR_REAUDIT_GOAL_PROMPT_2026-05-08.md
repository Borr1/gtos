# G12 NOFILL Correction Reaudit Goal Prompt - 2026-05-08

## Goal

Run `G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_REAUDIT_V1` as the G12 red-team/audit owner for the corrected `NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1` and `NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1`.

The question is narrow and important: verify whether the upstream packet is now correctly source-closed at `298 source_closed / 0 source_blocked_exact`, whether `NOFILL-CLOSE-ROW-0127` is legitimately cleared from existing OTR061 XAUUSD tick recovery evidence, and whether the upstream builder/verifier now prevents local-heavy-data source boxing before emitting missing-tick blockers.

This is still source/control evidence only. Do not score R/performance or open a result lane.

## Mandatory GTOS Preflight

Before relying on memory:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered file in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. If context is stale, read the newer artifacts directly and record the stale-context condition.

## Controlling Inputs

Correction lane:

- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_PATCH_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_PATCH_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/build_nofill_closure_source_correction_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/verify_nofill_closure_source_correction_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/test_nofill_closure_source_correction_2026_05_08.py`

Corrected upstream packet:

- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_PACKET_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json`
- corrected upstream builder/verifier/tests in the same directory.

Prior G12 audit:

- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/`

Source evidence:

- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet`
- SHA256 expected: `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`
- expected coverage: `2026-05-06T07:10:01.820000Z` through `2026-05-06T11:15:59.763000Z`
- expected row `0127` source event: terminal-area side-aware touch at `2026-05-06T07:15:00.634000Z`

## Owner Hardening Standard

This is a maximum-effort reaudit, not a rubber stamp.

Apply curiosity, truthfulness, and active creativity:

- Curiosity: check whether the correction introduced any hidden source/as-of, row-count, duplicate, stale-blocker, or verifier weakness.
- Truthfulness: accept only what source evidence proves. Do not convert source closure into performance evidence.
- Active creativity: search prior artifacts, source ledgers, code history, and absolute local-heavy-data roots if anything looks inconsistent.

Rules:

- Go to proof-or-impossibility.
- Treat listed files as starting points, not boundaries.
- Search absolute local heavy-data roots and prior recovery lanes before accepting any source-missing blocker.
- Preserve context anchors and instruction-coverage artifacts so compaction cannot erase requirements.
- Small `n` blocks validation/promotion only, not source audit completion.
- Negative or narrow findings still require learning notes.

## Required Audit Questions

1. Does the corrected upstream packet report exactly `298` rows, `298 source_closed`, and `0 source_blocked_exact`?
2. Is `NOFILL-CLOSE-ROW-0127` source-closed only from source-safe OTR061 tick evidence, with the expected SHA256 and coverage?
3. Is the first side-aware source event for row `0127` terminal-area touch at `2026-05-06T07:15:00.634000Z`?
4. Is the old `BLOCKED_NO_TICKS_IN_WINDOW` request inactive/superseded and not active blocker state?
5. Does the corrected builder/verifier search prior tick-recovery lanes and absolute local-heavy-data roots before emitting missing-tick blockers?
6. Are six T3 rows and 94 G12-blocked CNR061 rows still excluded?
7. Are no-leak/as-of, duplicate/sample-floor, label-family, and source-hash controls still valid?
8. Are all flags still `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`?
9. What next lane is justified after this correction: result-contract design, another source audit, or a blocker?

## Required Outputs

Write outputs under:

`research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit/`

Required artifacts:

- `G12_NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.md` and `.json`
- `G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md`
- `G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/test if useful.

Decision options:

- `ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE`
- `ACCEPT_WITH_EXACT_REMAINING_BLOCKER`
- `BLOCKED_WITH_NEXT_EXACT_QUESTION`
- `REJECT_INVALID_CORRECTION`

## Verification Requirements

Before completion:

- JSON/JSONL parse all new machine-readable artifacts.
- Recompute OTR061 parquet SHA256.
- Verify exact corrected packet counts.
- Verify stale extraction request is inactive/superseded.
- Verify six T3 and 94 blocked CNR061 exclusions.
- Run no-leak scan for R/performance/account/live/order/hidden/result fields.
- Verify flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
- Run `py_compile` for new scripts.
- Run focused pytest if scripts/tests exist.
- Run corrected upstream NOFILL close verifier and correction verifier unless a specific historical-verifier incompatibility is documented.
- Run forbidden live-surface diff over `src`, `prompts`, `config`, canaries, execution, risk, permissions, safety, selectors, MT5 order/account, paid/API/Databento, credentials, remotes, and order-behavior paths.
- Regenerate `LIVE_STATE` at closeout.

## Hard Boundaries

Do not score R/performance, inspect broker/account/live/order/hidden labels, score blocked CNR061 rows, use paid/API/Databento or MT5 order/account calls, edit registries, touch live trading surfaces, credentials, remotes, or order behavior. Do not set `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`. Do not claim validation, promotion, or live effect.

## Stop Condition

The goal is complete only when G12 has accepted, blocked, or rejected the corrected source packet with machine-checkable evidence, exact counts, source-hash proof, no-leak controls, next-lane guidance, and preserved research-only safety flags.
