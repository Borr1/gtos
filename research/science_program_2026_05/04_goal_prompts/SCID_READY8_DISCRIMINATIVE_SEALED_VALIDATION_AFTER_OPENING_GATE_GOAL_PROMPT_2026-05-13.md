# SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_AFTER_OPENING_GATE

Date: 2026-05-13

## Evidence Class

`SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_EXECUTION_ONLY`

This is the separate sealed-validation execution route opened by `G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_NUMERICAL_SCREEN_G12_AUDIT`. It may score the frozen sealed historical validation partition only. It is not promotion, live-readiness, strategy deployment, or a live trading behavior change.

This route is validation execution, not another gate or summary. "No promotion" is not "no numerical validation." Compute and report every source-bound sealed/stress target metric allowed by the frozen contract, while keeping trade-performance/live-deployment claims closed.

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/goal_session_research_discipline.md`
5. `.context/00_core/research_operating_doctrine.md`
6. `.context/00_core/research_current_state.md`
7. `.context/00_core/local_heavy_data_inventory.md`
8. `.context/00_core/ai_in_loop_cost_control_research_plan.md`
9. The latest session handoff in `.context/02_session_handoffs/`
10. `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_sealed_validation_opening_gate_after_numerical_screen_g12_audit/`

Treat the gate artifacts as the execution contract. Do not rely on chat memory. Treat `.context/00_core/goal_session_research_discipline.md` as active instruction: no arbitrary top-N, no conservative brake, pursue every data-opened validation question, and explain why working slices work and failed/inverse slices fail from the frozen evidence.

The frozen READY8 contract is a boundary against leakage, not a box against analysis. Within the frozen files, inspect every lawful branch, interaction, descriptor, partition, symbol/economic group, source segment, horizon, target family, pass/control role, duplicate bucket, and fail-closed family the data exposes. Do not restrict yourself to the obvious card-level summaries or the seed questions in this prompt.

## Frozen Inputs

- Repaired discriminative rowset path: `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl`
- Repaired rowset SHA256: `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`
- Target-result packet directory: `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/`
- Opening-gate prerequisite ledger: `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_sealed_validation_opening_gate_after_numerical_screen_g12_audit/G0_SCID_READY8_DISC_SEALED_GATE_FROZEN_PREREQUISITE_LEDGER_2026-05-13.json`

## Frozen Counts

- `8` READY8 cards: `ADV-001, ADV-003, BEH-001, HAZ-001, HAZ-005, MAC-001, MAC-004, UNC-004`
- `3,014` source candidates.
- `24,112` repaired discriminative rowset rows.
- `192,896` target-result rows.
- `162,336` computable rows.
- `30,560` fail-closed rows.
- Horizons: `1/4/16/32`.
- Target families: `neutral_close_to_close_return_m15_horizons_v1` and `neutral_high_low_excursion_m15_horizons_v1`.
- G0 screen ledger counts: aggregate `4,561`, contrast `3,400`, candidate `24,112`, partition `192`, failure `2,161`, explanation `8,689`, ambiguity `8,691`, data-backing `17,380`.

## Objective

Execute sealed validation on the frozen sealed historical partition without changing the rules. Use only `SEALED_VALIDATION_CANDIDATE_DESIGN` rows with `COMPUTABLE` target status for primary sealed scoring. Evaluate `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` rows only after the sealed pool and report them separately as stress evidence.

Compute pass-vs-control and descriptor-contrast comparisons for every READY8 card, horizon, target family, symbol/economic group, partition, denominator role, and source segment allowed by the gate policy. For each eligible branch, compute sealed/stress counts, unique duplicate denominator counts, effective-N/concentration flags, signed movement mean/median/distribution summaries, positive/negative/zero target-movement rates, pass-control deltas, inversion flags, underpowered flags, fail-closed attrition, and data-backed explanations. Preserve positive, negative/inverse, neutral, non-applicable, fail-closed, duplicate/concentration, horizon, target-family, partition, symbol/economic-group, descriptor, outlier, and ambiguity findings in full ledgers. Rankings may summarize only after the complete ledgers exist.

Do not stop at obvious questions or a top-N slice. Generate a validation question stack from the data itself and pursue every same-evidence-class ambiguity to conclusion: why did a branch pass, fail, invert, tie, become underpowered, concentrate, or fail-closed; what strengthens it; what destroys it; and what exact downstream audit or repair owns anything that cannot be answered from the frozen files.

Speed is not a constraint. If exhaustive branch computation is large, stream, chunk, checkpoint, or build compact indexes over complete ledgers. Do not substitute samples, representative rows, top-N slices, or "good enough" summaries for the full frozen population.

Do not tune thresholds, change card predicates, change target definitions, change partitions, drop fail-closed rows silently, merge stress into sealed evidence, or treat ADV-001/ADV-003 as edge-card performance claims.

## Required Policy

- Use `duplicate_proxy_denominator_key` as the primary duplicate denominator key.
- Report effective-N and concentration using `duplicate_proxy_denominator_key`, `source_segment_sha256`, `canonical_economic_group`, `symbol`, and `session`.
- Primary branches require at least `30` unique duplicate denominator keys to avoid underpowered interpretation; below-floor slices remain in ledgers as underpowered.
- Warn when one canonical economic group or one source segment exceeds `50%` of a primary branch.
- Fail-closed rows remain visible in attrition/source-repair ledgers and are excluded from target effect numerators and denominators unless a separate source-control repair supplies predecision evidence.
- Non-applicable rows stay non-applicable and cannot enter pass denominators.
- No R/PnL, trade win-rate, expectancy, live-readiness, strategy deployment, or promotion claim is allowed. This prohibition does not block sealed target-movement statistics, pass/control deltas, sign rates, effect-size summaries, attrition rates, concentration/effective-N diagnostics, or stress/sealed comparisons when clearly labeled as sealed validation metrics over neutral target families rather than trade performance.
- The route may use strong research language such as promising, weak, inverse, fragile, underpowered, concentrated, stress-sensitive, or killed when those labels are backed by sealed/stress target metrics. Do not soften or hide real validation results merely because promotion remains closed.
- If a branch appears strong, explain what supports it and what could invalidate it. If a branch appears weak, inverse, or null, explain the failure anatomy and whether it becomes a filter, exclusion, repair route, or killed hypothesis.

## Required Outputs

Create a versioned output directory under `research/science_program_2026_05/06_outcome_testing/` and emit:

- sealed-validation execution decision ledger,
- frozen-input/hash check ledger,
- sealed primary result ledger,
- stress robustness ledger,
- pass/control/contrast ledger,
- all-branches sealed/stress metric ledger,
- data-generated validation question ledger,
- winner/loser/inversion/neutral/failure explanation ledger,
- full branch-universe coverage ledger proving no allowed branch family was skipped,
- fail-closed attrition/source-repair ledger,
- duplicate/concentration/effective-N ledger,
- partition/symbol/economic-group/source-segment ledgers,
- full data-generated question and ambiguity ledger,
- saturation/self-red-team ledger,
- completion audit,
- concise synthesis,
- builder/verifier/focused-test scripts,
- next G12 sealed-validation result audit prompt and starter.

## Verification

Before closeout:

- Rerun or losslessly verify this opening gate verifier.
- Parse every emitted JSON/JSONL artifact.
- Run focused tests.
- Check no forbidden surfaces were touched.
- Regenerate `.context/LIVE_STATE.md`.
- Update `.context/00_core/research_current_state.md` if the research map changes.
- Commit only scoped route/prompt/context files with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.

## Safe Boundaries

Preserve `NO_PROMOTION_VERDICT`. Do not open promotion, live-readiness, live trading behavior, AI/API calls, paid/vendor access, broker account/order/history/deal/position evidence, raw-market-blob commits, prompt/config/risk/safety/execution/canary/selector changes, registry edits, or remote pushes.

## Completion Standard

Complete only when sealed and stress ledgers are computed from the frozen files, every allowed branch and data-opened validation question is scored/explained/bounded without arbitrary top-N substitution, verifier/focused tests pass, forbidden surfaces remain closed, and the next G12 audit prompt/starter is emitted.
