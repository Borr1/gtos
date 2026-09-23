# G12 NOFILL Forward Source-Capture Prototype Acceptance Audit Goal Prompt

Date: 2026-05-09
Owner lane: G12 independent red-team audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 acceptance audit of:

`research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/`

Decide whether the package can be accepted as source/control contract evidence only for a future owner-approved implementation-design lane, or whether it must be returned with exact repair blockers.

This is not live logger wiring, result/cost scoring, validation, promotion, registry editing, paid/API use, or live trading behavior. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Mandatory Preflight And Context

Before relying on memory:

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Re-read this prompt and record exact HEAD, prompt path, and audited package path in the audit context anchor.

Do not rely on chat memory. If context compaction happens, regenerate live state, reread this prompt and the audited package context anchor, and continue from disk artifacts.

## Controlling Inputs

Primary audited package:

- `nofill_forward_source_capture_contract_hardening_offline_projection_prototype/NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_2026-05-09.md/json`
- `NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json`
- `NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_2026-05-09.json`
- `NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_2026-05-09.jsonl`
- `NOFILL_FORWARD_FIXTURE_MANIFEST_2026-05-09.json` and `fixtures/`
- `NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_2026-05-09.json/md`
- `NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json`
- `NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_2026-05-09.json/md`
- `NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.json/md`
- `NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_2026-05-09.json/md`
- `NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_2026-05-09.json/md`
- builder, verifier, tests, and `NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json`

Also read the upstream chain as needed, especially:

- `g0_nofill_forward_projection_synthesis_control_route/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_forward_source_safe_projection_builder/`
- `nofill_forward_contract_addendum_projection_plan/`
- `g12_nofill_forward_lifecycle_capture_contract_audit/`
- `nofill_cat_v3_source_control_rebuild/`
- `g12_nofill_cat_v3_source_control_audit/`
- sealed-validation doctrine files referenced by `research_current_state.md`

## Hardening Standard

Operate at maximum practical reasoning depth. Take the time needed inside hard safety boundaries.

Enforce the owner's research virtues:

- Curiosity: search for contradictions, stale hashes, missing source fields, weak status vocabulary, redaction holes, duplicate traps, source/as-of mistakes, implementation traps, and better source-safe capture designs.
- Truthfulness: do not rescue weak evidence or relabel uncertainty. If a claim fails, say exactly why and what field/source/schema/control must change.
- Active creativity: do not be boxed by the first artifact, worktree, timeframe, source family, or known strategy framing. Explore alternative source-safe audit routes, then let evidence and no-leak controls decide.

Do not stop at shallow blocker taxonomy. Within this source/control audit class, pursue every ambiguity until accepted, rejected, repaired locally, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement.

Split only when the next route crosses an evidence-class gate: live logger wiring, result/cost scoring, sealed validation, promotion, registry edit, paid/API/live trading behavior, or remote push.

Use the third-party trading-system memo as hostile-review pressure, not as conservative law: verify source integrity, cost/execution separability, duplicate denominators, regime/session fields, perturbation-readiness, and whether later survival-adjusted expectancy can be measured without leakage.

## Audit Requirements

1. Reconstruct the evidence chain and frozen equation: `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`; accepted denominators `225/182/139`; reject-overlap rows zero-effect.
2. Independently audit the 55-field source-capture contract: field names, types, required/fail-closed status, as-of rules, source lineage, missing-status vocabulary, no-leak rules, owner/G12 gate status, and result/cost/live-wiring boundaries.
3. Recompute or independently verify the 298 offline prototype rows, fixture coverage, source/hash manifest, duplicate/denominator audit, no-leak/redaction audit, source/cost/execution separation, and hostile-review saturation.
4. Specifically attack raw-ticket/order/deal/position/account leakage, accidental hashing of sensitive values, hidden result labels, cost/slippage label creep, same-tick ambiguity fabrication, missing-status collapse, and accepted/reject denominator contamination.
5. Search local-heavy/context artifacts when needed; worktree absence is not data absence.
6. Decide exactly one terminal verdict:
   - `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY`
   - `ACCEPT_WITH_EXACT_REPAIR_BLOCKERS`
   - `RETURN_TO_SOURCE_CAPTURE_LANE_WITH_EXACT_FIXES`
   - `REJECT_INVALID_SOURCE_CONTROL_CONTRACT`

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_prototype_acceptance_audit/`

At minimum produce:

- decision ledger
- schema/field audit
- source/hash recomputation audit
- no-leak/redaction audit
- duplicate/denominator audit
- fixture/prototype-row audit
- hostile-review/saturation audit
- exact repair/blocker ledger if any
- next prompt pack
- completion audit
- builder/verifier/focused tests if useful

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

Before marking complete:

- Parse all generated JSON/JSONL.
- Run `python -B -m py_compile` or an equivalent bytecode-free syntax check if Windows pycache blocks writes, and record the reason.
- Run focused pytest with `-p no:cacheprovider` and a controlled `--basetemp`.
- Run the generated verifier.
- Recompute source/parser/fixture/generated hashes or record bounded mutable-context exceptions.
- Confirm no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`, no result/cost/live-wiring opening, and `NO_PROMOTION_VERDICT` is preserved.
- Check committed diff scope and ensure no live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors/canary/order behavior, MT5 order/account/history/deal/position behavior, credentials, paid/API/Databento route, registry promotion, or remote push was touched.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain any generated snapshot dirt.

## Completion Standard

The goal is complete only when the audited package has a terminal G12 decision, exact evidence for every acceptance/blocker claim, verification artifacts, scoped commits, and a next prompt pack. If accepted, it remains source/control evidence only; future live logger wiring still requires separate owner approval and a separate evidence-class lane.
