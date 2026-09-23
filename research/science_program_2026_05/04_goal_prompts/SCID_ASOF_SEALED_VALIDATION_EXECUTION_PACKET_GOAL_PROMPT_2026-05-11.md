# SCID As-Of Sealed Validation Execution Packet Goal Prompt

Date: 2026-05-11
Owner lane: separately gated SCID as-of sealed-validation execution packet
Evidence class: `SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_ONLY`
Promotion posture: `NO_PROMOTION_VERDICT`
Live authority: none

## Activation Prerequisite

Do not run this prompt unless all of the following are true from disk:

- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json` exists.
- Its terminal decision is exactly `ACCEPT_AS_G12_SEALED_VALIDATION_DESIGN_CONTROL_EVIDENCE_ONLY`.
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_VERIFICATION_RESULT_2026-05-11.json` exists and reports `ok=true` and `can_mark_goal_complete=true`.

If any prerequisite fails, do not open validation outputs. Emit an exact prerequisite-blocker ledger and stop.

## Goal

Use the accepted G12 design-control evidence to build the quarantined SCID as-of sealed-validation execution packet. This lane may open sealed-validation/result evidence only within the accepted design boundaries. It has no promotion authority, no live authority, no prompt/config/risk/safety/execution/canary/selector edit authority, no remote-push authority, no AI/API authority, no paid/vendor authority, no raw market-data blob authority, and no broker account/order/history/deal/position evidence authority.

The primary objective is not to make a profitable-looking report. It is to execute the accepted sealed rowset honestly, with frozen rowsets, frozen variants, frozen denominators, explicit no-leak controls, adversarial baselines, stress separation, concentration diagnostics, failure anatomy, and a next independent G12 post-execution audit prompt.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_READING_ORDER.md` enough to identify directly relevant context files.
8. Read and record current HEAD, dirty-state scope, controlling prompt path, and evidence-class boundary in the route context anchor.

Do not rely on chat memory, prior assistant summaries, or compaction memory. Use disk artifacts and current git state.

## Hard Boundaries

- Preserve `NO_PROMOTION_VERDICT` in every report.
- Preserve `live_effect=false` in every report.
- Use `validation_safe=false` unless a subsequent independent G12 post-execution audit changes it. This lane can execute quarantined validation, but it cannot declare the result safe for promotion or live use.
- Preserve `outcome_review_opened=false` in every report. Quarantined validation/result artifacts are not an owner outcome-review opening, promotion review, or live-readiness review.
- Do not hide outcome opening. If result/outcome rows are generated, label them `QUARANTINED_SEALED_VALIDATION_RESULT_EVIDENCE_ONLY`.
- Do not touch live trading prompts, config, risk, safety, execution, canary, selector, credentials, remotes, MT5 order/account/history/deal/position evidence, or live services.
- Do not call AI/API, paid/vendor access, or broad web/source routes.
- Do not commit raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or other raw market-data blobs.
- Do not reassign row partitions after opening validation outputs.
- Do not tune thresholds, horizons, variants, or filters on sealed rows and call them validation.
- Do not combine sealed-validation rows with stress rows, discovery exclusions, contaminated rows, secondary proxy denominator rows, or live/shadow rows.
- Do not use broker-realized outcomes, account PnL, order/deal/position history, slippage, or execution-cost truth in this lane.
- Do not claim edge, promote, recommend live changes, or update registries.
- Do not allow generated large artifacts to become a GitHub push blocker. If any generated file approaches GitHub raw-blob limits, use a source-safe LFS pointer or deterministic split/manifest policy and prove no raw Git blob over 100 MB is staged or committed.

## Mandatory Inputs

Read and reconcile these inputs directly:

- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_VERIFICATION_RESULT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_NOLEAK_FIELD_CONTRACT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_RULES_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_MULTIPLE_TESTING_DEBT_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_FALSIFICATION_STOP_CONDITIONS_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_SCIENCE_HORIZON_ROUTE_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_ROWS_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_MANIFEST_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json`
- `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`

These inputs are starting points, not the full boundary. If a same-evidence-class blocker appears, search relevant builders, tests, manifests, ledgers, current-state docs, and `git log` before accepting the blocker.

## Pre-Outcome Freeze Requirement

Before reading, deriving, or writing any validation outcome/result row, emit and hash a pre-outcome freeze packet containing:

- prerequisite acceptance proof;
- source artifact list and hashes;
- frozen candidate input manifest hash;
- frozen row partition ledger hash;
- primary sealed rowset: exactly `2,432` rows with `SEALED_VALIDATION_CANDIDATE_DESIGN`;
- stress rowset: exactly `582` rows with `STRESS_ROBUSTNESS_CANDIDATE_DESIGN`;
- excluded discovery-source rows: exactly `365`;
- candidate denominator groups: exactly `7`;
- primary denominator key: `duplicate_proxy_denominator_key`;
- forbidden secondary denominator sources: `XAUUSD_MGC` and `US30_MYM`;
- exact variant/family registry to execute;
- exact baseline/control registry to execute;
- exact outcome target definitions and horizons;
- exact metrics to compute;
- exact stop/falsification rules.
- full-population execution/checkpoint plan proving the route will not substitute compact-only or sampled outputs for the `2,432` sealed rows or `582` stress rows.
- large-artifact storage policy for result rows, aggregate ledgers, and compact/checkpoint files.

If exact outcome target definitions and horizons cannot be frozen from accepted source-control/design artifacts without arbitrary post-hoc choices, do not improvise. Emit `EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC`, a repair prompt, and no result rows.

## Rowset Rules

- Primary sealed-validation results may use only the `2,432` rows assigned `SEALED_VALIDATION_CANDIDATE_DESIGN`.
- Stress/robustness results may use only the `582` rows assigned `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` and must remain in separate artifacts.
- The `365` discovery-source exclusions must remain outside sealed validation, outside stress denominators unless explicitly used as contaminated/context controls, and outside result interpretation.
- Candidate rows with source symbol `XAUUSD_MGC` or `US30_MYM` may provide source context only if present in bar context; they cannot create extra denominator rows.
- Every result row must carry the source `candidate_input_row_id`, partition assignment, denominator key, symbol, canonical economic group, decision as-of, source packet row hash, and provenance hashes.

## Variant And Family Rules

Execute only variants/families that are frozen before outcome opening. At minimum, the pre-outcome registry must address these known discovery/control families and state either `EXECUTE`, `CONTROL_ONLY`, or `NOT_EXECUTABLE_FROM_PACKET_SOURCE_FIELDS`:

- `adjacent_range_compression_breakout`
- `ob_retest`
- `opening_drive_no_fill_lifecycle`
- `fvg_fill`
- `liquidity_stop_run_context`
- `session_kz_sweep`
- `breaker_re_entry`
- `baseline_random_session_control`
- `baseline_shifted_entry_control`
- `baseline_momentum_continuation`
- `baseline_mean_reversion`

If a family requires fields not present in the accepted source-control packet, mark it `NOT_EXECUTABLE_FROM_PACKET_SOURCE_FIELDS` with exact missing fields. Do not infer GTOS intent, OB/FVG/breaker state, pending orders, side, broker fills, or live decisions from neutral source-control rows unless those fields exist in the accepted packet.

New science-horizon families may be included only as `DESIGN_ONLY_NOT_EXECUTED` unless their exact source fields, target definitions, horizons, and no-leak rules are frozen before outcome opening. Any new family added after outcome opening is `POST_HOC_DISCOVERY_ONLY` and cannot be compared as validation.

## Outcome And Metric Rules

Allowed in this lane only after the pre-outcome freeze packet exists:

- sealed result rows for frozen executable families;
- separate stress/robustness rows;
- separate adversarial baseline/control rows;
- aggregate metrics by frozen family, symbol, canonical economic group, session/time bucket if defined pre-outcome, and partition;
- concentration diagnostics;
- duplicate denominator diagnostics;
- DSR/PBO/effective-N diagnostics where computable;
- `not_computable` diagnostics with exact reasons.

Forbidden:

- broker actual-R or account PnL;
- live trade outcomes;
- AI/API responses;
- paid/vendor evidence;
- cost/slippage claims beyond design/stress assumptions already frozen;
- post-hoc filter tuning;
- changing the validation rowset after seeing results;
- promoting or recommending live changes.

All metric artifacts must state `QUARANTINED_SEALED_VALIDATION_RESULT_EVIDENCE_ONLY`, `NO_PROMOTION_VERDICT`, `validation_safe=false`, and `live_effect=false`.

## Required Output Route

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_execution_packet/`

Emit at minimum:

- `SCID_ASOF_SEALED_VALIDATION_CONTEXT_ANCHOR_2026-05-11.md`
- `SCID_ASOF_SEALED_VALIDATION_PREREQUISITE_ACCEPTANCE_AUDIT_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_PREOUTCOME_FREEZE_PACKET_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_FROZEN_ROWSET_MANIFEST_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_VARIANT_FAMILY_REGISTRY_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_SEALED_RESULT_ROWS_2026-05-11.jsonl`
- `SCID_ASOF_SEALED_VALIDATION_SEALED_AGGREGATE_METRICS_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_STRESS_RESULT_ROWS_2026-05-11.jsonl`
- `SCID_ASOF_SEALED_VALIDATION_STRESS_ROBUSTNESS_SUMMARY_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_ADVERSARIAL_BASELINE_RESULTS_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_DUPLICATE_PROXY_DENOMINATOR_AUDIT_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_MULTIPLE_TESTING_DSR_PBO_EFFECTIVE_N_LEDGER_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_CONCENTRATION_REGIME_SESSION_SYMBOL_LEDGER_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_FAILURE_ANATOMY_LEDGER_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_FALSIFICATION_STOP_LEDGER_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_SATURATION_REDTEAM_LEDGER_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_INTERPRETATION_LIMITS_2026-05-11.md`
- `SCID_ASOF_SEALED_VALIDATION_LARGE_ARTIFACT_STORAGE_AUDIT_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_COMPLETION_AUDIT_2026-05-11.json`
- `SCID_ASOF_SEALED_VALIDATION_COMPLETION_AUDIT_2026-05-11.md`
- `build_scid_asof_sealed_validation_execution_packet_2026_05_11.py`
- `verify_scid_asof_sealed_validation_execution_packet_2026_05_11.py`
- `test_scid_asof_sealed_validation_execution_packet_2026_05_11.py`
- `SCID_ASOF_SEALED_VALIDATION_VERIFICATION_RESULT_2026-05-11.json`

Emit the next independent audit prompt:

`research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-11.md`

If blocked before outcomes, emit a repair prompt instead and no result-row artifacts.

## Required Verification

Run or create:

- JSON/JSONL parse checks for generated artifacts.
- Exact prerequisite acceptance checks.
- Exact rowset checks for `3,014`, `2,432`, `582`, `365`, `7`, and denominator uniqueness.
- Pre-outcome freeze packet existence and hash checks before result artifacts are accepted.
- Result-row provenance checks against frozen rowset.
- Full-population/no-sampling checks proving every eligible sealed/stress row is represented by execution output or exact row-level block reason.
- No-leak/forbidden-field/value scan.
- Duplicate/proxy denominator audit.
- Sealed-vs-stress separation audit.
- Discovery-exclusion audit.
- Variant/family registry audit.
- Multiple-testing, effective-N, DSR/PBO where computable, or exact `not_computable` reasons.
- Concentration diagnostics by symbol, economic group, source file, session/time bucket if defined, and family.
- Failure-anatomy diagnostics by family, symbol, economic group, duplicate cluster, and target/horizon where results are negative, ambiguous, blocked, or baseline-explained.
- Falsification/stop-condition audit.
- Large-artifact storage audit proving no raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or raw Git blob over 100 MB is staged or committed; if Git LFS is used, verify pointer/materialization status.
- Dirty-state scoped-diff audit that records unrelated runtime/live dirt but fails on scoped forbidden live-surface or raw-market-data changes.
- `python -m py_compile` or syntax-parse fallback if Windows pycache friction occurs.
- Focused pytest for this route.
- Standalone verifier that emits `ok=true` and `can_mark_goal_complete=true` only when all completion checks pass.
- Post-commit no-write verifier rerun, `git status --short`, and committed-diff/raw-blob audit before marking complete.

## Saturation And Self-Red-Team

Before completion, write a saturation red-team ledger that asks what would make the result fake or unusable. At minimum:

- Did any stress row leak into sealed results?
- Did any discovery-exposed row leak into sealed results?
- Did any secondary proxy row inflate denominators?
- Did any family execute without frozen source fields and target definitions?
- Did any target/horizon/filter get selected after seeing results?
- Did any hidden label, future-context field, broker-realized field, path label, AI/API output, or live field enter results?
- Are results concentrated in one symbol, group, time window, source file, or duplicate cluster?
- Do baselines explain the result?
- Do perturbations or stress rows break the result?
- Is any metric not computable, and is the reason exact?
- If a result is negative, ambiguous, or baseline-explained, what row-level failure anatomy explains it without inventing a rescue rule?
- Are all large result artifacts stored in a push-safe, reproducible form without hiding data loss?
- What would a skeptical G12 post-execution audit reject?

If a same-evidence-class gap can be closed, close it inside this goal. Do not mark complete with vague future work.

## Terminal Decisions

Use exactly one:

- `BUILT_QUARANTINED_SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET`
- `EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC`
- `EXECUTION_BLOCKED_SOURCE_OR_ROWSET_REPAIR_REQUIRED`
- `EXECUTION_REJECTED_NO_SOURCE_SAFE_VALIDATION_ROUTE`

No terminal decision may claim promotion, live readiness, or an edge. A positive validation result is still only quarantined validation evidence pending G12 post-execution audit and subsequent G0 synthesis.

## Commit And Context Requirements

- Commit only scoped execution-packet artifacts, the next G12 audit prompt or repair prompt, and required context refresh files.
- Never stage unrelated live/runtime/shadow dirt.
- Update `.context/00_core/research_current_state.md` after completion.
- Regenerate `.context/LIVE_STATE.md` at closeout and record freshness.
- Do not push remote.

## Completion Standard

Mark complete only when:

- activation prerequisite is proven from disk;
- pre-outcome freeze packet exists before result artifacts;
- all `2,432` sealed-design rows and all `582` stress-design rows are either executed under frozen rules or blocked with exact reason;
- no discovery exclusions, secondary proxy denominator rows, live/shadow rows, or broker/account/order evidence leak into sealed results;
- result rows and aggregate metrics are quarantined, source-provenanced, and no-leak clean;
- stress and adversarial baseline outputs are separate from primary sealed validation;
- multiple-testing/concentration/falsification diagnostics are emitted;
- failure-anatomy and large-artifact storage audits are emitted;
- verifier and focused tests pass or exact environment friction is recorded with syntax-safe fallback;
- post-commit no-write verifier and committed-diff/raw-blob audit pass;
- next prompt is a G12 post-execution audit prompt if built, or a repair prompt if blocked;
- completion audit reports `can_mark_goal_complete=true`;
- every artifact preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
