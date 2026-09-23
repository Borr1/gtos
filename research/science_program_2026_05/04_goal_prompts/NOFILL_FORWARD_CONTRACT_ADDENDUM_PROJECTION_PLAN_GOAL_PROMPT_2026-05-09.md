# NOFILL Forward Contract Addendum And Source-Safe Projection Plan Goal Prompt

Date: 2026-05-09
Owner lane: forward source/control addendum
Worktree: `C:\tmp\gtos_otb\NOFILLFWDADDENDUM`
Branch: `nofill-forward-contract-addendum-projection-plan`
Starting HEAD: `5eecc6f4 docs: refresh g12 no-fill audit merge state`

## Goal

Resolve `G12-FWD-BLOCKER-001..003` from the accepted-with-blockers G12 NOFILL forward lifecycle capture contract audit. Build a source/control-only contract addendum and offline source-safe projection-builder plan that closes or precisely rejects each blocker.

This lane must not wire live loggers, score results, validate an edge, promote a source, edit registries, change live trading behavior, or open any broker/account/order/history/deal/position labels. It must preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Mandatory Preflight And Context

Before relying on memory:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.

Do not rely on chat memory. Maintain a context anchor in the output folder. If compaction or uncertainty occurs, regenerate live state, reread this prompt and the context anchor, then continue from disk.

## Controlling Inputs

Read and cite:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_lifecycle_capture_contract_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_usdjpy_sequence_source_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_quarantined_categorical_count_packet_audit/`
- `src/research_infra/forward_capture.py`
- `src/research_infra/live_shadow_gap_closure.py`
- `src/research_infra/live_mechanical_shadow.py`
- `scripts/audit_live_shadow_data_health.py`
- `scripts/verify_shadow_log_integrity.py`
- relevant shadow logs named by the forward audit.

## Required Blocker Closure

Close or exactly preserve the three G12 blockers:

1. `G12-FWD-BLOCKER-001`: add explicit capture-latency/write/clock-skew fields.
2. `G12-FWD-BLOCKER-002`: add source-safe pending-order observability with MT5 ticket redaction proof.
3. `G12-FWD-BLOCKER-003`: add closed source-safe spread/slippage/execution-quality status fields before cost or survival-adjusted expectancy testing.

For each blocker, produce:

- exact field names;
- schema family;
- source/as-of rule;
- allowed source roots/logs;
- forbidden fields/values;
- hash/provenance requirements;
- null/missing status vocabulary;
- duplicate/denominator effect;
- implementation readiness status;
- verifier assertions;
- remaining owner/access/source requirement if not closable.

## Hardening Standard

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside hard safety boundaries.

Enforce curiosity, truthfulness, and active creativity:

- Curiosity: search for every source-safe way to close the blockers, including existing logs, code, pending-intent state, MT5-safe metadata, runtime timing fields, and local-heavy-data manifests.
- Truthfulness: do not claim readiness if a field would leak result labels, live order labels, account/history labels, MT5 tickets, or post-decision outcomes. Preserve blockers if they are real.
- Active creativity: design source-safe, no-leak observability that can support future testing better than the first obvious fields, but do not cross into live wiring or result use.

Same-evidence-class continuation applies: do not stop at restating the blockers. Within this source/control lane, pursue every allowed blocker-closure route until each is closed, proven impossible under source-safe rules, or reduced to an exact owner/access/source requirement.

Small-N is not an excuse. If future testing needs more rows or better fields, define the exact capture expansion and verifier route. Do not claim validation.

Apply hostile trading-system review: the addendum must make future cost, spread, slippage, latency, session, regime, duplicate, and execution-quality testing measurable without leakage or hidden broker/account labels.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/`

Produce at minimum:

- `NOFILL_FORWARD_ADDENDUM_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.md`
- `NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.json`
- `NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json`
- `NOFILL_FORWARD_PENDING_ORDER_REDACTION_PROOF_2026-05-09.md`
- `NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC_2026-05-09.json`
- `NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC_2026-05-09.json`
- `NOFILL_FORWARD_OFFLINE_PROJECTION_BUILDER_PLAN_2026-05-09.md`
- `NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json`
- `NOFILL_FORWARD_BLOCKER_CLOSURE_DECISION_LEDGER_2026-05-09.md`
- `NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md`
- `NOFILL_FORWARD_ADDENDUM_COMPLETION_AUDIT_2026-05-09.md`
- builder/verifier/focused pytest if useful for reproducibility.

If it is source-safe and does not wire live behavior, you may build an offline dry-run projection verifier over existing committed logs to prove the schema catches forbidden fields and required missing statuses. Do not produce result labels or performance claims.

Update `.context/00_core/research_current_state.md` after the artifact commit.

## Verification Required

Before marking complete:

- JSON parse all generated JSON.
- Run `python -m py_compile` on generated Python.
- Run focused pytest.
- Verify all outputs preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Verify no result/R/win-rate/expectancy/DSR/PBO scoring.
- Verify no MT5 order/account/history/deal/position labels, no raw ticket leakage, no account PnL labels, no paid/API/Databento calls, no credential/remote changes.
- Verify no live trading prompt, `src` trading logic, config/risk/execution/permissions/safety/selectors/canary/order behavior changes.
- Verify committed diff scope; ignore unrelated generated runtime dirt only if explicitly recorded.
- Regenerate `LIVE_STATE.md` at closeout and make research context fresh.

Commit scoped artifacts with a research commit and a context refresh commit. Do not push remote.
