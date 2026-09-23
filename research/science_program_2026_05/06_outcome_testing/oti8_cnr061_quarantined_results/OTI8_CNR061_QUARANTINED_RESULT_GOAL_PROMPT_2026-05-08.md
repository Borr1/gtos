# OTI8 CNR061 Quarantined Result Goal Prompt - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## One-Line Starter

`/goal Run OTI8_CNR061_QUARANTINED_RESULT_LANE using C:\tmp\gtos_otb\OTI8CNR061\research\science_program_2026_05\06_outcome_testing\oti8_cnr061_quarantined_results\OTI8_CNR061_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-08.md as the controlling prompt; complete mandatory GTOS preflight; read .context/LIVE_STATE.md, .context/00_core/quick_reference_card.md, .context/00_core/research_operating_doctrine.md, .context/00_core/research_current_state.md, .context/00_core/goal_session_research_discipline.md, .context/00_core/local_heavy_data_inventory.md, the latest handoff, G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_2026-05-08.json, G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json, G12_CNR061_NEXT_LANE_PROMPT_PACK_2026-05-08.md, and all upstream CNR061/CNR/OTX/OTR061 artifacts named in this prompt; operate at maximum practical reasoning depth with curiosity, truthfulness, active creativity, proof-or-impossibility, context-anchor and searched-root ledgers; score only the exact 8 G12-accepted sidecar_row_sha256 rows and exactly exclude the 94 blocked rows; freeze duplicate denominator and metric policy before label review; use only source-hashed input/quote/ordered-tick-path evidence; do not use broker actual-R/account history/live trade results/hidden path labels/blocked rows/post-hoc targets; no paid/API/Databento/MT5 order/account calls unless explicitly approved; write method-freeze, result ledger, source/no-leak/duplicate/label/methodology/failure-forensics/next-lane/completion artifacts plus verifier/tests; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; touch no live prompts/risk/execution/permissions/safety/selectors/canaries/MT5 order behavior/credentials/remotes/order behavior; stop only with a completed quarantined result package or exact source/no-leak/as-of/duplicate impossibility before scoring.`

## Objective

Run the OTI8 quarantined result lane for `OTG0-PKT-061` / CNR061 continuation/no-retrace using only the `8` rows that G12 accepted in `G12_CNR061_SIDECAR_REAUDIT`.

This is a discovery-only result audit, not validation and not promotion. The output should answer what happened on these eight accepted, source-hashed input-only rows, why it happened, and what this teaches for future CNR timing/target models. It must not rescue, tune, or promote the idea.

## Mandatory Preflight

Before using old memory or summaries:

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Record the current `HEAD`, branch, worktree path, runtime dirt, and exact controlling prompt path in a context anchor artifact before scoring.

If context is stale, regenerate/read the fresh files and continue from committed artifacts. Do not rely on chat memory.

## Controlling Inputs

Read and machine-parse where possible:

- `research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_SOURCE_HASH_JOIN_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_NEXT_LANE_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_JOIN_MAP_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROW_MATRIX_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_RECOVERY_COMPLETION_AUDIT_2026-05-07.json` if present; if absent, search the OTR061 directory and record the exact artifact names found.

Use these as starting points, not blind limits. If an accepted row references a local source path, search absolute local roots from `local_heavy_data_inventory.md` before declaring missing data. Still, the scoring cohort is fixed to the `8` G12-accepted sidecar rows only; source searches are for proof, hash, and as-of reconstruction, not cohort expansion.

## Hardening Standard

This lane must follow `.context/00_core/goal_session_research_discipline.md` in full:

- maximum practical reasoning depth;
- curiosity, truthfulness, active creativity;
- proof-or-impossibility;
- anti-boxing across timeframe, symbol, worktree, source modality, current edge, and first hypothesis wording;
- small `n` blocks validation/promotion only, not research or failure anatomy;
- negative/null results require row-level failure forensics and learning;
- maintain context anchor, active question stack, searched-root ledger, route-decision ledger, and instruction-coverage checklist;
- request access when needed rather than silently stopping.

Do not turn creativity into evidence. The market/source data decides.

## Frozen Scope

Score exactly and only the `8` rows whose `sidecar_row_sha256` values are accepted in the G12 CNR061 decision/readiness ledgers.

Exclude exactly the `94` blocked rows. Assert zero overlap by:

- `sidecar_row_sha256`;
- source row hash;
- record id;
- duplicate denominator key;
- duplicate group id.

If any blocked row is needed to compute a result, stop before scoring and write an exact blocker.

## Metric Freeze Before Label Review

Before reading terminal path labels or computing any R:

1. Write a method-freeze artifact that names the accepted row hashes, duplicate denominator policy, terminal ordering policy, target/stop fields, quote side policy, path horizon, and exclusion gates.
2. Freeze side-aware terminal scoring:
   - use the row's source-hashed executable quote and ordered tick path;
   - for LONG and SHORT, use the correct bid/ask side according to the source row's execution/terminal policy;
   - do not infer same-bar order from OHLC if ordered ticks are absent;
   - do not use hidden `target_first`, `stop_first`, `result`, `path_label`, broker actual-R, account history, or live result fields.
3. Freeze R scoring:
   - `target_first` uses the source-frozen residual target R from executable quote to `CNR_T0_ORIGINAL_TP1`;
   - `stop_first` uses `-1.0R` only if stop geometry is valid at the executable quote;
   - `target_already_passed`, `invalid_stop_geometry`, missing geometry, missing quote, missing ordered path, or path horizon absence must be null/excluded with exact reason, not imputed;
   - no post-hoc target, stop, timebox, entry timing, or threshold may be invented.
4. Freeze duplicate aggregation:
   - report row-level all-eight results;
   - report countable results under the G12/CNR061 duplicate denominator policy;
   - report timing-family splits `CNR_E0` vs `CNR_E1`;
   - do not let duplicate group alone identify a row.

If the controlling artifacts disagree on any metric or duplicate policy, stop before scoring and write the exact contradiction.

## Required Output Artifacts

Create a new scoped directory:

`research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/`

Write versioned artifacts, including:

- `OTI8_CNR061_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `OTI8_CNR061_METHOD_FREEZE_2026-05-08.md` and `.json`
- `OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json`
- `OTI8_CNR061_RESULT_LEDGER_2026-05-08.md`, `.json`, and row-level `.jsonl`
- `OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT_2026-05-08.md` and `.json`
- `OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.md` and `.json`
- `OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-08.md` and `.json`
- `OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER_2026-05-08.md` and `.json`
- `OTI8_CNR061_BLOCKER_AND_NEXT_ACTION_LEDGER_2026-05-08.md` and `.json`
- `OTI8_CNR061_G12_POST_RESULT_PROMPT_PACK_2026-05-08.md`
- `OTI8_CNR061_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder, verifier, and focused test files if useful.

## Verification Requirements

Run and record:

- JSON/JSONL parse checks for every generated machine-readable artifact;
- source-hash recomputation for every accepted row source file used;
- exact 8 accepted / 94 blocked exclusion check;
- no-leak forbidden-key scan over packet/result rows;
- duplicate denominator audit;
- label-family separation audit;
- `py_compile` for any builder/verifier/test files;
- focused pytest if test files are created;
- forbidden live-surface diff/status check over `src`, `prompts`, `config`, `scripts/canary*`, `MT5` order paths, execution/risk/permissions/safety/selectors, credentials, remotes, and order behavior.

## Forbidden

- No live trading prompts, risk, execution, permissions, safety gates, selectors, canaries, MT5 order behavior, credentials, remote pushes, or order behavior changes.
- No broker actual-R, account-history, live trade result, live order state, hidden path labels, or blocked-row outcome inspection.
- No paid/API/Databento calls without explicit owner approval and a pre-call manifest/cost cap.
- No master registry edits.
- No validation-safe flip, outcome-review flip, live-effect flag, or promotion language.

## Stop Condition

Complete only when either:

1. the quarantined result package is built, verified, committed, and marked `NO_PROMOTION_VERDICT`; or
2. scoring is proven impossible before outcome review because a source hash, as-of, no-leak, duplicate denominator, or metric-freeze requirement fails, with exact searched roots and next unblocker recorded.

If the result is negative, null, or tiny-n, do not stop at the label. Explain the failure anatomy: which decision inputs led to the terminal outcome, whether target residual was too small, whether timing was late, whether geometry was invalid, whether path/horizon source was insufficient, whether duplicate concentration dominates, and what future preregistered timing/target/source capture would be needed to learn more.
