# OTI7 CNR Accepted Quarantined Result Goal Prompt - 2026-05-08

Promotion posture: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## One-Line Starter

/goal Run OTI7 CNR accepted-row quarantined result audit from current worktree `C:\tmp\gtos_otb\OTI7CNRRESULT` using `research/science_program_2026_05/06_outcome_testing/oti7_cnr_accepted_quarantined_results/OTI7_CNR_ACCEPTED_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-08.md` as controlling prompt and using only the G12-accepted input rows from `research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json`, with `research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json` as mandatory exclusion/unblocker ledger and `research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_2026-05-08.json`, `research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json`, `research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-08.json`, `research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_PREREGISTRATION_2026-05-07.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/research_current_state.md` as required context; perform mandatory GTOS preflight by regenerating and reading `.context/LIVE_STATE.md`, reading latest handoff, quick reference, research doctrine/current state, local-heavy-data policy, G12 CNR audit outputs, CNR timing preregistration, and this prompt before scoring anything; owner approval is granted only for this quarantined result audit over the 102 accepted input-only rows, not for promotion, live changes, broker actual-R, account history, blocked rows, paid/API/Databento calls, or source-safe flips; score no row unless it is present in the ready shortlist, absent from blocker exclusion, source-hash verified, no-leak clean, duplicate-policy classified, geometry reconstructable from source packet plus accepted row, and eligible under pre-entry target-already-passed checks; audit only `CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1` and `CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1` because those are the only G12-accepted timing/target families; use source-hashed tick/quote paths and source packets, never hidden path labels, broker actual-R, account history, live result fields, blocked-packet outcomes, post-hoc target/stop choices, or the 6098 blocked rows; apply executable quote-side and target/stop geometry before R scoring, classify target-already-passed/no-entry/no-coverage/same-bar ambiguity/null-R states before any synthetic path-R, and never force a win/loss when geometry or ordering is impossible; treat this as unlimited-effort proof-or-impossibility inside the hard safety boundaries, maintain a context anchor and active question stack, re-read controlling context after compaction/resume/uncertainty, search absolute local heavy-data roots when needed, and pursue every ambiguity until it is answered, proven impossible from approved inputs, or converted into an exact source/capture/approval requirement; produce OTI7-owned artifacts only under `research/science_program_2026_05/06_outcome_testing/oti7_cnr_accepted_quarantined_results/`: row-level result ledger JSON/JSONL/MD, source-hash/path-coverage audit, geometry/eligibility audit, duplicate/effective-N audit, no-leak/label-family audit, timing-family comparison, target-already-passed/null-result forensics, negative-result learning ledger, methodology DSR/PBO/effective-N report, next-hypothesis/blocker ledger, context-continuity/instruction-coverage ledger, completion audit, builder/verifier/tests; run JSON parse, source-hash recomputation, forbidden-field scans, duplicate denominator checks, py_compile, focused pytest, NO_PROMOTION_VERDICT coverage, unsafe-flag scan, and forbidden live-surface diff; stop only when all 102 accepted rows are scored or explicitly classified unscoreable with exact file-grounded reasons, all blocked rows remain excluded, failure/success anatomy is explained, artifacts are committed, context is refreshed, and `NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false` remain preserved with no prompt/risk/execution/permissions/safety/selector/canary/credential/remote/paid/API/Databento/MT5-order/order-behavior changes.

## Objective

Run the first CNR quarantined result audit over the G12-accepted rows only. This lane can produce discovery evidence, null/impossibility evidence, and learning for future preregistration. It cannot produce validation, source promotion, or live trading changes.

## Allowed Rows

- Source of truth: `G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json`
- Accepted row count: `102`
- Countable denominator rows: `54`
- Noncountable duplicate-context rows: `48`
- Accepted timing/target families:
  - `CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1`: `51`
  - `CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1`: `51`
- Ready by packet:
  - `OTG0-PKT-060`: `26`
  - `OTG0-PKT-061`: `8`
  - `OTG0-PKT-062`: `32`
  - `OTG0-PKT-063`: `32`
  - `OTG0-PKT-066`: `4`

## Mandatory Exclusions

- Exclude all `6098` blocked rows from `G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json`.
- Exclude every CNR family not accepted by G12: `CNR_E2`, `CNR_E3`, `CNR_E4`, `CNR_T1`, `CNR_T2`, and `CNR_T3`.
- Exclude broker actual-R, account history, live trade results, blocked-packet outcomes, hidden path labels, post-hoc targets, post-hoc stops, and any row without source-hashed path coverage.

## Result Rules

- Apply the pre-entry target-already-passed geometry gate before any R scoring.
- Use side-aware executable quote logic from source-hashed ticks/quotes; do not infer from OHLC if ordered ticks are available.
- If source geometry, stop, target, quote side, or terminal ordering is missing, classify exactly rather than imputing.
- Count duplicate denominator rows separately from duplicate-context rows.
- Report DSR/PBO/effective-N honestly; if not computable, state the exact reason and expansion path.
- Negative/null results require forensics: what failed, how it failed, what decision/path states caused it, whether the issue is timing, target, source, market mechanism, duplicate denominator, or methodology.

## Required Outputs

- `OTI7_CNR_RESULT_LEDGER_2026-05-08.md/json/jsonl`
- `OTI7_CNR_SOURCE_HASH_PATH_COVERAGE_AUDIT_2026-05-08.md/json`
- `OTI7_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-08.md/json`
- `OTI7_CNR_DUPLICATE_EFFECTIVE_N_AUDIT_2026-05-08.md/json`
- `OTI7_CNR_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-08.md/json`
- `OTI7_CNR_TIMING_FAMILY_COMPARISON_2026-05-08.md/json`
- `OTI7_CNR_TARGET_ALREADY_PASSED_AND_NULL_FORENSICS_2026-05-08.md/json`
- `OTI7_CNR_NEGATIVE_RESULT_LEARNING_LEDGER_2026-05-08.md/json`
- `OTI7_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-08.md/json`
- `OTI7_CNR_NEXT_HYPOTHESIS_AND_BLOCKER_LEDGER_2026-05-08.md/json`
- `OTI7_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md/json`
- `OTI7_CNR_COMPLETION_AUDIT_2026-05-08.md/json`
- builder/verifier/test files sufficient to regenerate and check the lane.

## Forbidden

No live trading prompt, risk, execution, permission, safety, selector, canary, MT5 order, credential, remote, paid/API/Databento, or order-behavior changes. No source marked `validation_safe=true`. No prereg marked `outcome_review_opened=true`. No `live_effect=true`. No promotion language. No blocked row scoring. No broker actual-R/account-history/live-result inspection.
