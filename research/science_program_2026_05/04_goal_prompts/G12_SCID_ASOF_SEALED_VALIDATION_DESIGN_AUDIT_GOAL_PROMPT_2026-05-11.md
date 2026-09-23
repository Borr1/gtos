# G12 SCID As-Of Sealed Validation Design Audit Goal Prompt

Date: 2026-05-11
Owner lane: G12 audit of G0 SCID as-of sealed-validation design only
Evidence class: `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_ONLY`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit the G0 SCID as-of source-control synthesis and sealed-validation design packet. Decide whether the G0 design can be accepted as design-only control evidence for a future, separately gated sealed-validation execution lane.

This G12 audit must not execute validation, generate scored candidates, generate replay/path-label/result outcomes, calculate R/PnL/win-rate/expectancy/performance/cost/slippage, promote anything, call AI/API, use paid/vendor access, read broker account/order/history/deal/position evidence, commit raw market-data blobs, push remotes, alter prompts/config/risk/safety/execution/canary/selector behavior, restart live services, or change live trading behavior.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_READING_ORDER.md` enough to identify directly relevant context files.
8. Record current HEAD, dirty-state summary, controlling prompt path, and evidence-class boundary in the audit context anchor.

Do not rely on chat memory, previous assistant summaries, or compaction memory. Use disk artifacts and current git state.

## Mandatory Inputs

Read and reconcile these inputs directly:

- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_COMPLETION_AUDIT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_ACCEPTED_PACKET_RECONCILIATION_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_NOLEAK_FIELD_CONTRACT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_RULES_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_MULTIPLE_TESTING_DEBT_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_SCIENCE_HORIZON_ROUTE_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_FALSIFICATION_STOP_CONDITIONS_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_SATURATION_REDTEAM_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/`
- `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`

These inputs are starting points, not the full boundary. If the audit finds contradictions, search relevant builders, tests, manifests, source ledgers, current-state docs, and `git log` before reaching a terminal decision.

## Required Audit Facts

Recompute or independently verify from files:

- G0 evidence class: `G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_ONLY`.
- G12 packet decision being consumed: `ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY`.
- Source-control bars: exactly `7,567`.
- Candidate-generator input-only rows: exactly `3,014`.
- Row partition coverage: exactly `3,014` rows, every candidate input row exactly once.
- Partition counts: exactly `2,432` `SEALED_VALIDATION_CANDIDATE_DESIGN` rows and `582` `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` rows.
- Accepted bounded SCID segments: exactly `9`.
- Candidate denominator economic groups: exactly `7`.
- Discovery exclusions: exactly `365`.
- Adversarial baselines: exactly `4`.
- Both prior G12 warnings remain repaired:
  - `FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW`
  - `TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE`
- G0 verifier passed with `ok=true` and `can_mark_goal_complete=true`.
- G0 focused tests passed.
- Safe flags remain closed: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

If any required fact fails, do not accept the design. Route to exact repair with blocker IDs.

## Required Audit Questions

Answer these with machine-checkable audit ledgers:

1. Does the G0 design preserve source-control/input-only status and keep validation execution closed?
2. Does every one of the `3,014` candidate rows appear exactly once in the partition ledger with a valid partition status and duplicate/proxy denominator key?
3. Are the `2,432` sealed-design rows sufficiently separated from `582` stress-design rows, `365` discovery exclusions, and all contaminated/forbidden sources?
4. Do duplicate/proxy rules prevent GC/MGC and YM/MYM double counting while preserving source-context bars?
5. Does the no-leak field contract block hidden labels, post-outcome fields, broker-realized fields, path-labels, future-context fields, AI/API fields, result fields, cost/slippage fields, and live fields?
6. Does the science-horizon ledger avoid old-box narrowing and map the packet across path geometry, session/calendar, volatility/tail timing, SCID microstructure proxies, liquidity/stop-cascade hypotheses, regime/context, execution/cost realism, ML/meta-labeling, adversarial baselines, and current GTOS/OB comparator context?
7. Does the adversarial baseline and robustness plan freeze controls before future validation, including perturbation, holdouts, duplicate concentration, outlier removal, placebo, and cost/slippage stress design?
8. Does the multiple-testing debt ledger prevent discovery exposure from being rebranded as validation?
9. Do falsification/stop conditions prevent self-rescue, post-hoc thresholding, and promotion drift?
10. Does the next route, if accepted, correctly move to a separately gated sealed-validation execution packet and not execute validation inside this audit?
11. Does unrelated live/runtime dirt remain informational only, with no scoped forbidden live-surface or raw market-data changes?
12. What would a skeptical G12/G0 reviewer reject, and did this audit pursue that concern to proof, exact repair blocker, or proven impossibility?

## Required Output Route

Create audit artifacts under:

`research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/`

Emit at minimum:

- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_CONTEXT_ANCHOR_2026-05-11.md`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_COMPLETION_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_PACKET_RECONCILIATION_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_ROW_PARTITION_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_NOLEAK_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_DUPLICATE_PROXY_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_BASELINE_ROBUSTNESS_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_MULTIPLE_TESTING_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_SCIENCE_HORIZON_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_FALSIFICATION_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_SATURATION_REDTEAM_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_REPAIR_BLOCKER_LEDGER_2026-05-11.json`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_NEXT_PROMPT_PACK_2026-05-11.md`
- `verify_g12_scid_asof_sealed_validation_design_audit_2026_05_11.py`
- `test_g12_scid_asof_sealed_validation_design_audit_2026_05_11.py`
- `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_VERIFICATION_RESULT_2026-05-11.json`

If accepted, emit the next prompt as a validation-execution packet prompt only, still with no live/promotion authority:

`research/science_program_2026_05/04_goal_prompts/SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_GOAL_PROMPT_2026-05-11.md`

If not accepted, emit a repair prompt instead and do not emit an execution prompt.

## Allowed Terminal Decisions

Use exactly one:

- `ACCEPT_AS_G12_SEALED_VALIDATION_DESIGN_CONTROL_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_REPAIR_BLOCKERS`
- `REJECT_ROUTE_TO_SOURCE_CONTROL_OR_DESIGN_REPAIR`

Acceptance means the design is accepted only as design-control evidence. It does not itself execute validation, score candidates, prove edge, open promotion, or alter live behavior.

## Verification Requirements

Run or create:

- JSON/JSONL parse checks for target and audit artifacts.
- Exact count checks for `7,567`, `3,014`, `2,432`, `582`, `9`, `7`, `365`, and `4`.
- Row-partition uniqueness and coverage check for all `3,014` candidate input rows.
- No-leak/forbidden-field/value scan on design and audit artifacts.
- Duplicate/proxy denominator audit.
- Science-horizon and anti-boxing coverage audit.
- Robustness/baseline/falsification/multiple-testing audit.
- Safe-flag scan for `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
- Dirty-state scoped-diff check that records unrelated runtime/live dirt but fails on scoped forbidden live-surface or raw-market-data changes.
- `python -m py_compile` or explicit syntax-parse fallback if Windows pycache friction occurs.
- Focused pytest for target route if useful and for this G12 audit route.
- Standalone G12 verifier that emits `ok=true` and `can_mark_goal_complete=true` only if the audit completion standard passes.

## Saturation And Self-Red-Team

Before completion, write a saturation red-team audit that asks what would make the G0 design unsafe. At minimum, test:

- input-only rows being treated as validation rows;
- stress-design rows leaking into sealed-design rows;
- discovery-exposed rows leaking into sealed validation;
- duplicate/proxy inflation;
- hidden labels or future-context fields surviving no-leak checks;
- planned metrics being mistaken for computed metrics;
- old-box hypothesis narrowing;
- under-specified falsification/stop rules;
- missing G12 gate before validation execution;
- dirty live/runtime files confusing scoped audit evidence.

If the red-team exposes an allowed same-evidence-class gap, pursue it inside this audit before completion. Do not mark complete with vague future work when a same-class repair can be performed.

## Commit And Context Requirements

- Commit only scoped G12 audit artifacts, the emitted next prompt, and required context refresh files.
- Never stage unrelated live/runtime/shadow dirt.
- Update `.context/00_core/research_current_state.md` with the G12 design-audit result after completion.
- Regenerate `.context/LIVE_STATE.md` at closeout and record freshness.
- Do not push remote.

## Completion Standard

Mark complete only when:

- all mandatory inputs were read or exact missing-input blockers were recorded;
- the G0 design packet was independently reconciled with exact counts and row coverage;
- no validation execution, result scoring, path-label/result generation, AI/API, broker evidence, raw market-data commit, promotion, or live behavior was opened;
- the audit emits one allowed terminal decision with exact blocker ledger if not fully accepted;
- if accepted, the next prompt is a separate sealed-validation execution packet prompt and remains gated by this acceptance;
- verifier and focused tests pass or exact environment friction is recorded with syntax-safe fallback;
- completion audit reports `can_mark_goal_complete=true`;
- safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
