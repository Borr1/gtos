# G12 NOFILL Forward Source-Capture Text-Gate Repair Reaudit Goal Prompt

Date: 2026-05-10
Owner lane: G12 independent repair reaudit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 reaudit of the text-gated hash fallback repair after commit `d2bd8cac research: text-gate nofill source capture hash fallback`.

The prior G12 repair reaudit accepted the general repair direction but kept `G12-SRC-CAP-REPAIR-001` open because LF-normalized fallback was not gated to text artifacts. The exact narrowed blocker was:

> A strict `.bin` non-text artifact can be accepted when raw SHA changes but LF-normalized hash matches.

Audit whether `d2bd8cac` closes that exact blocker without weakening content-hash integrity, mutable-context separation, source/control-only boundaries, no-leak controls, duplicate/denominator controls, or future live-wiring gates.

If the repair is accepted, the terminal decision should be `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_TEXT_GATE_REPAIR`. If not, return exact remaining repair blockers.

This is not live logger wiring, result/cost scoring, validation, promotion, registry editing, paid/API use, remote push, or live trading behavior.

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
- `test_nofill_forward_capture_contract_2026_05_09.py`
- `NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json`
- the full `nofill_forward_source_capture_contract_hardening_offline_projection_prototype/` package

Prior G12 repair reaudit:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_repair_reaudit/`

Prior G12 acceptance audit:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_prototype_acceptance_audit/`

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity.

Do not accept the repair because the package verifier passes in the current checkout. Prove or disprove it using adversarial hash-policy cases. Within this repair-reaudit evidence class, pursue every ambiguity until accepted, rejected, repaired locally if within audit scope, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement.

Split only when crossing into live logger wiring, result/cost scoring, sealed validation, promotion, registry edits, paid/API/live trading behavior, or remote push.

## Required Reaudit Questions

1. Did commit `d2bd8cac` add an explicit text-artifact gate before LF-normalized fallback acceptance?
2. Does the repaired verifier still accept strict text CRLF/LF portability only through bounded `sha256_lf_normalized` evidence?
3. Does it still reject true text content mutation where LF-normalized SHA changes?
4. Does it now reject strict binary/non-text raw SHA mismatch even if a synthetic LF-normalized hash matches?
5. Do mutable-context `strict_hash_recompute=false` entries remain warning-only and unable to mask strict-source failures?
6. Does the regenerated source-hash manifest remain internally consistent and free of true strict failures?
7. Did the repair leave `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`, denominators `225/182/139`, redaction/no-leak controls, same-tick ambiguity preservation, source/cost/execution separation, and future live logger gating unchanged?

## Required Adversarial Proof

Build or record adversarial proof covering:

- strict text artifact whose raw SHA changes under CRLF/LF normalization while LF-normalized SHA matches and is accepted only through the bounded text fallback;
- strict text artifact with true content mutation where LF-normalized SHA changes and is rejected;
- strict `.bin` or non-text artifact where raw SHA changes and LF-normalized hash is synthetically set to match; this must now be rejected;
- mutable-context entry with raw drift and `strict_hash_recompute=false`; this remains warning-only and cannot mask any strict-source failure;
- cleanup/no-mutation proof for all temporary adversarial fixtures.

If tests or verifier fixtures are modified, commit only scoped audit artifacts plus context refresh. Do not mutate source artifacts except through the audited package verifier result if the prompt explicitly requires rerun.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_text_gate_repair_reaudit/`

At minimum produce:

- decision ledger
- text-gate repair verification audit
- adversarial hash-policy proof
- source/hash recomputation audit
- no-leak/control regression audit
- blocker closure ledger
- next prompt pack
- completion audit
- builder/verifier/focused tests if useful

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

- Parse all generated JSON/JSONL.
- Run syntax checks without relying on writable `__pycache__` if Windows blocks bytecode writes.
- Run focused pytest with `-p no:cacheprovider` and a controlled existing `--basetemp`.
- Run generated verifier.
- Run or cite the repaired package verifier and package focused tests.
- Confirm no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`, no result/cost/live-wiring opening, and `NO_PROMOTION_VERDICT` is preserved.
- Check committed diff scope; no live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors/canary/order behavior, MT5 order/account/history/deal/position behavior, credentials, paid/API/Databento route, registry promotion, or remote push.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when `G12-SRC-CAP-REPAIR-001` is independently accepted as closed after the text gate, or a remaining exact blocker is recorded. Acceptance remains source/control evidence only. Future live logger wiring still requires separate owner approval and a separate evidence-class lane.
