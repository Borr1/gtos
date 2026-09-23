# G12 SCID READY8 Discriminative Card Rowset Repair Audit

Date: 2026-05-13

## Evidence Class

`G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AUDIT_ONLY`

This is an independent G12 audit of the repaired READY8 discriminative card-rowset source-control package. It is not target scoring, not validation, not promotion, and not a live-trading change.

The target route is:

`research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`

Audit the package from disk. Do not rely on chat memory or the closeout message.

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/goal_session_research_discipline.md`
6. `.context/00_core/research_current_state.md`
7. Latest session handoff in `.context/02_session_handoffs/`

Then read the target route artifacts, the accepted upstream READY8 numerical-screen audit, and the accepted READY8 learning synthesis from disk.

## Audit Objective

Independently determine whether the repaired READY8 package can be accepted as source-control discriminative rowset/design evidence.

Verify, from disk and recomputation where feasible:

- target terminal decision is `REPAIRED_READY8_DISCRIMINATIVE_CARD_ROWSET_DESIGN_G12_ACCEPTANCE_REQUIRED`;
- exact source candidate universe remains `3,014`;
- exact repaired accounting rowset is `24,112` rows = `8` cards x `3,014` source candidates;
- rowset SHA256 matches manifest;
- all `8` READY8 cards are present exactly:
  - `ADV-001`
  - `ADV-003`
  - `BEH-001`
  - `HAZ-001`
  - `HAZ-005`
  - `MAC-001`
  - `MAC-004`
  - `UNC-004`
- all `8` cards have source-field maps, predicate IDs, descriptor contrast designs, source fields consumed, and derived fields;
- row-level denominator roles are explicit and conserved:
  - `per_card_pass_row`
  - `per_card_contrast_row`
  - `per_card_non_applicable_row`
  - `per_card_fail_closed_row`
- status vocabulary is internally consistent:
  - `PASS_DESCRIPTOR_CONTRAST_ELIGIBLE`
  - `PASS_CARD_PREDICATE`
  - `ELIGIBLE_CONTRAST_CONTROL`
  - `NON_APPLICABLE_SOURCE_CONTEXT`
  - `FAIL_CLOSED_MISSING_PRIOR_CANDIDATE`
  - `FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE`
- fail-closed rows are retained with exact source requirements and are not inferred, dropped, or counted as passes;
- non-applicable rows are retained and cannot enter pass denominators;
- duplicate policy uses `duplicate_proxy_denominator_key` and preserves `candidate_input_row_id`, canonical economic group, symbol/session/source-proxy grouping, and source segment hash controls;
- existing partition labels remain source-control only, not validation;
- target-opening prerequisites are closed and exact;
- safe flags remain closed:
  - `NO_PROMOTION_VERDICT`
  - `validation_safe=false`
  - `outcome_review_opened=false`
  - `live_effect=false`
- no target-result scoring, validation, performance/R/PnL/win-rate/expectancy claims, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commit, registry edit, remote push, prompt/config/risk/safety/execution/canary/selector change, live restart, or live trading behavior was opened.

## Audit Posture

Be strict, fair, and exact.

Do not invent blockers or perform conservative theater. A blocker must cite exact disk evidence: file, row id, field, count, hash, schema, source/as-of proof, no-leak rule, parser issue, verifier/test failure, dirty-scope issue, or manifest mismatch.

Do not reject the package because it is broad, non-OB, adversarial, descriptor-based, or not yet a performance result. The target package is a repaired source-control rowset/design artifact. The absence of result scoring is not a defect.

Do not accept weak proof either. If the rowset only renames the old repeated denominator without real predicate/descriptor separation, reject or repair with exact evidence. Pay particular attention to:

- `ADV-001` and `ADV-003`: these are adversarial/control cards and may legitimately keep full source-candidate coverage if their descriptor contrast cells are real, hashed, and verifier-covered. Do not mistake full coverage in control cards for edge-card redundancy, but do verify the descriptor contrasts are nontrivial.
- `BEH-001`, `HAZ-001`, `HAZ-005`, `MAC-001`, `MAC-004`, and `UNC-004`: these must have meaningful pass/control/non-applicable/fail-closed separation or exact reasons why a full-coverage descriptor-control design is appropriate.
- Any fail-closed or non-applicable row must be visible in the rowset and policy ledgers.
- Any "same_evidence_class remaining = 0" claim must be supported by saturation/self-red-team and blocker ledgers.

If an issue is repairable inside this same G12 audit evidence class, repair it before final decision. Same-G12 repairs may include manifest rebinding, EOL/hash normalization, verifier hardening, stale completion metadata repair, output manifest refresh, parse/shape checks, rowset hash verification, and exact no-leak scans. Do not stop with "needs another prompt" for same-G12 repairs.

Split only if the next action crosses evidence class boundaries, requires unavailable external/source access, opens forbidden live/broker/API/paid/raw surfaces, requires target-result scoring, or requires non-generatable historical source truth.

## Required Audit Questions

Answer all questions in artifacts:

1. Does the target route exist and parse?
2. Do all target artifacts listed in the output manifest exist and hash-match?
3. Does the rowset have exactly `24,112` valid JSONL rows?
4. Does each card have exactly `3,014` accounting rows?
5. Do the pass, contrast, non-applicable, and fail-closed role counts match the manifest and verifier?
6. Are the two adversarial control cards intentionally full-coverage descriptor-control designs, with multiple descriptor contrast keys?
7. Are the six non-control cards truly discriminative by row status and descriptor contrast?
8. Are fail-closed rows retained with exact source requirements?
9. Are non-applicable rows retained and excluded from pass denominators?
10. Are duplicate/concentration policies present and enforceable by future result-opening routes?
11. Are partition labels explicitly source-control only?
12. Are target-opening prerequisites closed and exact?
13. Are safe flags closed everywhere?
14. Are forbidden result/performance/broker/live/API/paid/raw/registry/remote surfaces absent?
15. Did the target verifier and focused tests pass from disk?
16. Are there exact same-G12 repairs to perform? If yes, perform them before terminal decision.
17. What terminal decision is justified by disk evidence?

## Required Output Directory

Create:

`research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_card_rowset_repair_audit/`

## Required Artifacts

Emit versioned artifacts with `2026-05-13` in the file name:

1. `G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_2026-05-13.json`
   - terminal decision,
   - target route commit/path,
   - exact count reconciliation,
   - accepted/repaired/rejected findings,
   - safe flags.

2. `G12_SCID_READY8_DISCRIMINATIVE_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json`
   - independent rowset count/status/role/card/hash recomputation,
   - descriptor contrast count checks,
   - fail-closed/non-applicable checks,
   - duplicate policy checks,
   - forbidden-field/no-leak checks.

3. `G12_SCID_READY8_DISCRIMINATIVE_AUDIT_REPAIR_LEDGER_2026-05-13.json`
   - every issue found,
   - same-G12 repairs performed,
   - exact unrepaired blocker only if not same-G12-repairable.

4. `G12_SCID_READY8_DISCRIMINATIVE_AUDIT_COMPLETION_AUDIT_2026-05-13.json`
   - checklist for every audit question,
   - instruction-coverage checklist,
   - `can_mark_goal_complete`,
   - proof that no invented/vague blockers remain.

5. `G12_SCID_READY8_DISCRIMINATIVE_AUDIT_VERIFICATION_RESULT_2026-05-13.json`
   - standalone audit verifier output.

6. Standalone audit builder, verifier, and focused tests.

7. If accepted, emit the next non-audit result-opening/materialization prompt only if the repaired package is ready for the next evidence-class gate. If the correct next step is a narrow G0 synthesis gate, emit that exact prompt instead and justify why.

8. If rejected or repair-blocked, emit an exact repair prompt only after same-G12 repair options are exhausted.

## Verification Requirements

Before marking complete:

1. Rerun the target route verifier from disk.
2. Rerun target focused tests if feasible.
3. Build the G12 audit artifacts.
4. Run the G12 standalone verifier.
5. Run G12 focused pytest.
6. Syntax-check new G12 Python files. If Windows pycache friction appears, use explicit cfile or AST/no-bytecode fallback and record it precisely.
7. Parse every emitted G12 JSON/JSONL artifact.
8. Confirm no normal-Git blob over the repository limit and no raw market-data blob was introduced.
9. Confirm no unrelated live/runtime/shadow dirt was staged.
10. Confirm safe flags remain closed.
11. Regenerate `.context/LIVE_STATE.md`.
12. Update `.context/00_core/research_current_state.md`.
13. Commit scoped audit/prompt/context changes only.

## Allowed Terminal Decisions

- `ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_CONTROL_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS`
- `REPAIR_BLOCKED_WITH_EXACT_READY8_DISCRIMINATIVE_REPAIR_REQUIREMENTS`
- `REJECT_WITH_EXACT_SOURCE_OR_VERIFICATION_FAILURES`

## Completion Standard

Complete only when every audit question is answered from disk, all same-G12 repairs have been pursued, no invented or vague blockers remain, verifier/focused tests pass, forbidden surfaces remain closed, and scoped commits are made.
