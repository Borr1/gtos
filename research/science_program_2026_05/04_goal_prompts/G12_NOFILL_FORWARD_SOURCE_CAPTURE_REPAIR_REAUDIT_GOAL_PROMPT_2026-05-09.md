# G12 NOFILL Forward Source-Capture Repair Reaudit Goal Prompt

Date: 2026-05-09
Owner lane: G12 independent repair reaudit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 repair reaudit for `G12-SRC-CAP-REPAIR-001` after commit `59e41bd8 research: close nofill source capture hash verifier blocker`.

Audit whether the source-capture prototype package verifier now correctly accepts LF-normalized hashes for strict text artifacts when the manifest `sha256_lf_normalized` matches, without weakening content-hash integrity, no-leak controls, duplicate/denominator controls, or source/control-only boundaries.

If the repair is accepted, the terminal decision should be `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_REPAIR`. If not, return with exact remaining repair blockers.

This is not live logger wiring, result/cost scoring, validation, promotion, registry editing, paid/API use, or live trading behavior.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Re-read this prompt and record exact HEAD and prompt path in the audit context anchor.

Do not rely on chat memory. If context compaction occurs, regenerate live state, reread this prompt and the audited package context anchor, and continue from disk artifacts.

## Controlling Inputs

Primary repair target:

- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/verify_nofill_forward_capture_contract_2026_05_09.py`
- `NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json`
- the full `nofill_forward_source_capture_contract_hardening_offline_projection_prototype/` package

Prior G12 audit:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_prototype_acceptance_audit/`

Upstream chain as needed:

- `g0_nofill_forward_projection_synthesis_control_route/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_forward_source_safe_projection_builder/`
- `g12_nofill_forward_lifecycle_capture_contract_audit/`
- `nofill_cat_v3_source_control_rebuild/`
- sealed-validation doctrine files referenced by `research_current_state.md`

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity.

Do not stop at shallow blocker taxonomy. Within this repair-reaudit evidence class, pursue every ambiguity until accepted, rejected, repaired locally if within audit scope, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement.

Split only when crossing into live logger wiring, result/cost scoring, sealed validation, promotion, registry edits, paid/API/live trading behavior, or remote push.

## Audit Requirements

1. Reconstruct the prior decision: `ACCEPT_WITH_EXACT_REPAIR_BLOCKERS`, blocker `G12-SRC-CAP-REPAIR-001`.
2. Independently inspect the repaired package verifier and confirm it:
   - still recomputes raw SHA for all manifest entries;
   - still fails true content hash mismatches;
   - still allows mutable-context entries only when `strict_hash_recompute=false`;
   - accepts strict text artifacts only when actual LF-normalized SHA equals manifest `sha256_lf_normalized`;
   - records the LF-normalized fallback as bounded warning/evidence, not silent pass.
3. Do not accept the repair just because the current checkout passes. Build or record an adversarial hash-policy proof that covers:
   - at least one strict text artifact whose raw SHA changes under CRLF/LF normalization while the LF-normalized SHA still matches the manifest and is accepted only through the bounded text fallback;
   - at least one strict text artifact with a true content mutation that changes the LF-normalized SHA and is rejected;
   - at least one binary or non-text strict artifact that still requires exact raw SHA and cannot use text normalization;
   - at least one mutable-context entry showing it remains non-strict and cannot mask strict-source failures;
   - restoration/no-mutation of committed source artifacts after any temporary adversarial fixtures.
4. Rerun the package verifier and confirm it returns `ok=true`, `can_mark_goal_complete=true`, zero failures, source/control-only flags closed, and no live-wiring/result/cost route opened.
5. Recompute the core package invariants: `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`; accepted denominators `225/182/139`; future live logger wiring still gated.
6. Re-audit no-leak, redaction, source/cost/execution separation, fixtures, same-tick ambiguity preservation, and duplicate/denominator controls only as needed to ensure the repair did not weaken them.
7. Decide exactly one terminal verdict:
   - `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_REPAIR`
   - `ACCEPT_WITH_REMAINING_EXACT_REPAIR_BLOCKERS`
   - `RETURN_TO_SOURCE_CAPTURE_LANE_WITH_EXACT_FIXES`
   - `REJECT_INVALID_REPAIR`

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_repair_reaudit/`

At minimum produce:

- decision ledger
- repair verification audit
- source/hash recomputation audit
- no-leak/control regression audit
- blocker closure ledger
- next prompt pack
- completion audit
- builder/verifier/focused tests if useful

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

- Parse all generated JSON/JSONL.
- Run `python -B -m py_compile` or equivalent syntax check if Windows pycache blocks writes.
- Run focused pytest with `-p no:cacheprovider` and controlled `--basetemp`.
- Run generated verifier.
- Require the generated verifier or focused tests to include the adversarial hash-policy cases above. If the session chooses not to write fixtures/tests, it must produce an equivalent documented proof with exact temp paths, hashes before/after, and cleanup verification.
- Confirm no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`, no result/cost/live-wiring opening, and `NO_PROMOTION_VERDICT` is preserved.
- Check committed diff scope; no live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors/canary/order behavior, MT5 order/account/history/deal/position behavior, credentials, paid/API/Databento route, registry promotion, or remote push.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when `G12-SRC-CAP-REPAIR-001` is independently accepted as closed or a remaining exact blocker is recorded. Acceptance remains source/control evidence only. Future live logger wiring still requires separate owner approval and a separate evidence-class lane.
