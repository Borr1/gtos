# G12 NOFILL Source-State Gap Closure And Tick Export Manifest Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source-control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`.

Independently audit the completed `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE` as source-control acquisition/capture evidence only. Verify whether its blocker pursuit, market-data export requests, contamination exclusions, recovered-state negative evidence, 55-field closure, owner action manifest, no-leak posture, verifier/tests, and scoped commits are strong enough to become accepted control evidence for the next route.

This audit must be rigorous and adversarial, but not timid. Do not rubber-stamp the target route. Do not reject lazily. Pursue every same-evidence-class ambiguity inside this audit until accepted, repaired inside the audit write scope, reduced to an exact upstream repair/source request, or proven impossible from approved source-control routes. Conservatism applies to source/no-leak validity and live-safety boundaries, not to effort, search breadth, or audit depth.

Expected terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_GAP_CLOSURE_AND_EXPORT_MANIFEST`
- `ACCEPT_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS`
- `REJECT_IF_FORBIDDEN_EVIDENCE_CLASS_OPENED`

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Read `.context\00_core\research_current_state.md`.
9. Read this prompt and record current HEAD plus prompt path in a context anchor.

Do not rely on chat memory. If context compaction, restart, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read the target artifacts, and continue from disk.

Run the audit from the current merged main/worktree state, not from the old target branch summary. If the target artifacts or context docs were merged after the target route completed, the G12 audit must inspect the files as they exist in the current audit worktree and record the HEAD used.

## Target Route

Audit these target artifacts:

- `research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_COMPLETION_AUDIT_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_VERIFICATION_RESULT_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_PURSUIT_LADDER_LEDGER_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_CONTAMINATION_EMBARGO_HANDLING_LEDGER_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_MANIFEST_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_FORWARD_CAPTURE_REQUIREMENT_MATRIX_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_55_FIELD_CLOSURE_LEDGER_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_NON_GENERATABLE_TRUTH_PROOF_LEDGER_2026-05-10.json`
- `NOFILL_SOURCE_STATE_GAP_CLOSURE_NOLEAK_FORBIDDEN_ROUTE_AUDIT_2026-05-10.json`
- target builder, verifier, and focused tests.

Accepted upstream facts to preserve unless independently disproven:

- `2` admitted source-bound rows.
- `37` blockers.
- `9` rejects.
- Duplicate denominators `2/2/2`.
- Repaired packet hash `5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341`.
- Target reported `37/37` active-pursuit ladder rows.
- Target reported `31/31` tick/export-dependent blockers with market-data-only manifests.
- Target reported `17/17` contamination/embargo blockers as clean-denominator exclusions.
- Target reported recovered historical source-state count `0`.
- Target reported `55/55` forward-capture field closure.
- Target owner-action manifest should contain `22` grouped market-data export requests across `GBPJPY`, `GBPUSD`, `US30_cash`, `USDJPY`, and `XAUUSD`, plus one forward-capture approval request and one access/export umbrella request. Independently recompute the exact counts from the manifest rather than trusting this sentence.

## Required G12 Outputs

Create a new audit route under:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/`

Required artifacts:

1. Context anchor.
2. G12 decision ledger.
3. Target artifact inventory and source-hash audit.
4. Independent count reconciliation for `2/37/9`, duplicate denominators `2/2/2`, `31`, `17`, `0`, and `55`.
5. Active-pursuit ladder audit for all `37` blockers and allowed terminal vocabulary.
6. Tick/export manifest audit for all `31` market-data-dependent blockers.
7. Contamination/embargo exclusion audit for all `17` rows.
8. Recovered-source-state negative-evidence audit.
9. Non-generatable historical GTOS source-state proof audit.
10. Forward-capture `55`-field closure audit against accepted implementation/design artifacts and `src/research_infra/forward_capture.py`.
11. Owner action exactness audit.
12. No-leak/forbidden-route/live-surface audit.
13. Target verifier/test rerun ledger.
14. Owner/export request grouping audit, including exact grouped market-data request count and symbol/date/window coverage.
15. Next-route ranking ledger that decides among read-only tick recovery/export, forward-capture implementation/capture, reject/contamination fixture learning, or exact repair first.
16. Saturation/self-red-team audit.
17. Next route prompt pack with one-line starter. If the next route is known, create a full controlling prompt file under `research/science_program_2026_05/04_goal_prompts/`, not only a short markdown note.
18. Completion audit with `can_mark_goal_complete`.
19. G12 builder, verifier, and focused tests.

## Audit Requirements

Independently verify:

- all target JSON/JSONL artifacts parse,
- all required artifacts exist,
- target row/count facts are recomputed from row-level ledgers, not copied from completion audit summaries,
- target artifact hashes are computed from current files in the audit worktree and any mutable context drift is separated from strict source-artifact drift,
- target verifier passes or any failure is reduced to an exact repair blocker,
- target focused tests pass or any failure is reduced to an exact repair blocker,
- all `37` blocker pursuit records use allowed terminal statuses and contain row identity, source-state gap, catalog/search evidence, and terminal action,
- terminal status counts are independently recomputed and any deviation from the expected split is explained or blocked,
- all `31` tick/export rows are market-data-only and exclude account/order/history/deal/position, broker actual-R, result/cost, and hidden labels,
- all grouped owner/export requests are exact enough to execute without guessing and reconcile to all `31` market-data-dependent blocker rows without duplicate or missing row coverage,
- all `17` contamination rows remain excluded from clean denominators, result labels, validation, and promotion,
- all `9` rejects and all `17` contamination blockers remain barred from clean denominators unless a separately named future source-control proof is required,
- recovered-source-state count `0` is supported by source-safe negative evidence, not weak assumption,
- non-generatable claims distinguish recoverable market data from historical GTOS intent/lifecycle/order-observability/write-clock/ticket-redaction truth,
- `55/55` fields are mapped to source-bound, future extraction/logger, schema-only control, or forbidden/redacted status-only categories,
- owner/export/capture requests are exact enough for a future route to run without guessing,
- optional parallel prompt packs have disjoint write scopes and do not cross into scoring/validation/live behavior,
- the next route recommendation is not passive: if accepted, rank the exact next route and produce a starter that can be run immediately; if blocked, produce exact repair/source prompt text,
- no current or generated artifact opens validation, result/cost/R/win-rate/expectancy scoring, broker actual-R, MT5 account/order/history/deal/position values, hidden labels, promotion, registry edits, paid/API/Databento routes, remote push, live restart, prompts, production trading logic, config/risk/permissions/safety/selectors/canaries, credentials, or live trading behavior.

## Hardening Requirements

Do not stop at a surface pass. If an audit concern is repairable inside the G12 audit write scope, repair it and record the repair. If it belongs to the target route, reduce it to an exact repair prompt with file paths, failed checks, expected counts, and no-leak boundaries. If the target is accepted, produce the next exact route starter, not a vague recommendation.

Do not be overly conservative by rejecting source-control evidence merely because it cannot validate an edge. This audit is not a validation/result lane. Accept source-control evidence if it is exact, source-safe, hashable, no-leak, and has correct next-route boundaries.

Do not perform the owner/export actions inside this G12 audit unless they are already source-safe local verification steps required to audit an existing claim. This G12 route can verify and harden manifests, source hashes, request exactness, and next-route prompt readiness; it must not silently become the tick-recovery/export route or forward-capture implementation route.

Apply curiosity, truthfulness, and active creativity:

- Curiosity: actively look for hidden denominator leakage, stale context, missing source hashes, incomplete owner actions, weak negative evidence, and source-state/market-data confusion.
- Truthfulness: do not rescue weak artifacts with optimistic interpretation; record exact failures.
- Activity/creativity: turn every failure into an actionable repair/source/capture route if possible.

## Forbidden In This Audit

- validation execution,
- result/cost/R/win-rate/expectancy scoring,
- broker actual-R,
- MT5 account/order/history/deal/position values,
- hidden result labels,
- promotion,
- registry edits,
- paid/API/Databento routes,
- remote push,
- live restart,
- live trading prompts,
- production trading logic,
- config/risk/permissions/safety/selectors/canaries,
- credentials,
- live trading behavior changes.

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Completion Standard

You may mark the goal complete only if:

- all required G12 artifacts exist,
- target route counts and ledgers are independently reconciled,
- target row-level ledgers, not only summary audits, are the basis of all count claims,
- target verifier/tests and G12 verifier/tests pass or exact repair blockers are frozen,
- owner/export request exactness and grouped request coverage are verified,
- next-route ranking plus full next controlling prompt file exist when the next route is known,
- all source hashes/no-leak/forbidden-surface checks are ledgered,
- next route prompt pack and one-line starter exist,
- JSON/JSONL artifacts parse,
- research context is refreshed,
- commits are scoped to this G12 route and required context refresh only,
- completion audit says `can_mark_goal_complete=true`,
- and no unsafe flags or live/validation/scoring surfaces are opened.
