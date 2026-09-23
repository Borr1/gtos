# NOFILL Historical Source Expansion Builder Local Tick Shadow Packet Goal Prompt

Date: 2026-05-10
Owner lane: G0 source expansion builder
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build the next source/control-only NOFILL historical source-expansion packet from local tick and shadow sources.

The parent G0 synthesis accepted that current committed CAT V3 NOFILL rows contain zero sealed-validation rows. This route must therefore create the next possible source-hashed candidate packet for future G12 source/control audit, or prove exactly why no eligible packet can be built from approved local routes.

This is not validation execution. It must not score outcomes, compute R, compute win rate, compute expectancy, open cost/slippage/execution-quality labels, read broker actual-R, read MT5 account/order/deal/position/history values, promote, edit registries, call paid/API routes, push remote, restart live processes, change prompts/config/risk/permissions/safety/selectors/canaries/MT5 behavior, touch credentials, or change live trading behavior.

Expected terminal decisions:

- `ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT`
- `ACCEPT_ZERO_PACKET_WITH_EXACT_SOURCE_EXPANSION_REQUIREMENTS`
- `BLOCKED_WITH_EXACT_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENT`
- `REJECT_INVALID_G0_OR_SOURCE_CHAIN`

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt and record exact HEAD and prompt path in a context anchor.

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read the parent route artifacts, and continue from disk.

## Controlling Inputs

Parent G0 synthesis route:

- `research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_partition_source_binding_synthesis_control_review/`
- `G0_NOFILL_HIST_SYNTHESIS_DECISION_LEDGER_2026-05-10.md`
- `G0_NOFILL_HIST_SYNTHESIS_NEXT_SOURCE_EXPANSION_ROUTE_RANKING_2026-05-10.json`
- `G0_NOFILL_HIST_SYNTHESIS_EXACT_SOURCE_EXPANSION_REQUIREMENTS_MATRIX_2026-05-10.json`
- `G0_NOFILL_HIST_SYNTHESIS_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json`
- `G0_NOFILL_HIST_SYNTHESIS_NOLEAK_DUPLICATE_PURGE_EMBARGO_SOURCE_HASH_RULES_2026-05-10.json`
- `G0_NOFILL_HIST_SYNTHESIS_LOCAL_HEAVY_PRIOR_ARTIFACT_SEARCH_PLAN_2026-05-10.json`
- `G0_NOFILL_HIST_SYNTHESIS_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENTS_LEDGER_2026-05-10.json`
- `G0_NOFILL_HIST_SYNTHESIS_VALIDATION_EXECUTION_CLOSED_GATE_LEDGER_2026-05-10.json`

Accepted G12 audit:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_sealed_validation_partition_source_binding_audit/`

Accepted target partition route:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/`

Upstream source-control chain:

- `nofill_cat_v3_source_control_rebuild/`
- `g12_nofill_cat_v3_source_control_audit/`
- `nofill_forward_source_safe_projection_builder/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_forward_source_capture_additive_logger_implementation/`
- `g12_nofill_forward_source_capture_additive_logger_implementation_audit/`
- `g0_nofill_forward_source_capture_implementation_synthesis_readiness_route/`

Approved local source roots for this route:

- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`
- current worktree committed source-control artifacts

Do not use stale worktree artifacts as admitted rows. Prior `C:\tmp\gtos_otb` worktrees may be used only as contradiction/control references if hashed and clearly separated from admitted source rows.

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, activity, and creativity, while staying in this source/control evidence class.

Do not stop at "no rows found" unless you have saturated the approved local roots, recorded searched paths, hashed/paraphrased relevant source files, and reduced the result to an exact source/capture/access requirement.

Do not box the search to one obvious file. Start from the parent G0 seed dates and source roots, then inspect the relevant shadow-log families and tick coverage needed to reconstruct source-safe NOFILL candidate rows. Treat parent route seed dates as starting points, not limits. If another source-safe route exists in the approved local evidence class, pursue it far enough to accept, reject, block, or prove impossible.

No `n too small` excuse is allowed for source expansion. If sample size is small, build the exact small packet and state that validation is not open. If sample size is zero, prove why and specify the exact source expansion requirement.

## Required Build Tasks

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`

Build artifacts must include, at minimum:

1. Context anchor with prompt path, HEAD, source roots, parent route hashes, and forbidden-surface summary.
2. Decision ledger with terminal decision and no-promotion posture.
3. Source inventory and search ledger for local tick root, selected shadow logs, source-control artifacts, and any prior-artifact control references.
4. Source hash manifest for every consumed raw tick/shadow/source file and every parser/builder/verifier file.
5. Parser/as-of manifest explaining how each admitted field is available at decision/capture as-of or fail-closed.
6. Contamination purge ledger excluding CAT V3 contaminated packet row IDs, source row IDs, source inventory IDs, nofill duplicate keys, duplicate groups, source dates, and one-day same-symbol/source-lane embargo overlaps.
7. Candidate admission ledger explaining every admitted, blocked, rejected, or impossible source candidate.
8. Frozen source-bound NOFILL candidate packet JSONL. If zero rows, emit a zero-row packet manifest and exact source expansion requirement ledger.
9. 55-field binding checklist per admitted row, preserving the accepted categories: `17 SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED`, `20 FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE`, `11 SCHEMA_ONLY_CONTROL`, `7 FORBIDDEN_REDACTED_STATUS_ONLY`.
10. Future-20 extraction/fail-closed ledger for:
    - `capture_write_started_at_utc`
    - `capture_write_completed_at_utc`
    - `capture_latency_ms`
    - `capture_clock_source_status`
    - `capture_clock_skew_ms`
    - `capture_clock_skew_status`
    - `native_pending_order_type_source_safe`
    - `native_pending_order_type_status`
    - `decision_spread_status`
    - `decision_spread_value_source_safe`
    - `decision_spread_unit`
    - `entry_touch_spread_status`
    - `entry_touch_spread_value_source_safe`
    - `spread_source_hash`
    - `pending_horizon_start_utc`
    - `pending_horizon_end_utc`
    - `terminal_area_touch_status`
    - `terminal_area_first_touch_utc`
    - `protective_area_touch_status`
    - `protective_area_first_touch_utc`
11. Forbidden/redacted status-only audit for:
    - `cost_testing_gate_status`
    - `execution_quality_label_status`
    - `execution_quality_value_redaction_status`
    - `mt5_order_ticket_redaction_status`
    - `raw_ticket_field_present_status`
    - `slippage_label_status`
    - `slippage_value_redaction_status`
12. Duplicate denominator ledger with row-level count, primary `nofill_duplicate_key_sha256` or source-safe equivalent, and secondary `duplicate_group_id_sha256` or source-safe equivalent.
13. No-leak audit proving no result, cost, slippage, execution-quality, broker actual-R, account history, order, deal, position, hidden label, validation, or promotion fields entered admitted rows.
14. Exact blocker/impossibility ledger for every row or source route not admitted.
15. Saturation/self-red-team pass listing every plausible source route considered and why it was accepted, blocked, rejected, or impossible.
16. Next G12 source/control audit prompt pack.
17. Completion audit with `can_mark_goal_complete=true` only if the route has a terminal packet/zero-packet decision, exact ledgers, tests, scoped commits, and closeout verification.
18. Builder, verifier, and focused tests.

## Verification Requirements

Required verification:

- Generated JSON/JSONL/Markdown parse checks.
- Source hash recomputation.
- Parser/builder/verifier hash recomputation.
- Exact count reconciliation for packet rows, blocked rows, rejected rows, impossible rows, duplicate denominators, source files, and forbidden-field hits.
- No-leak/forbidden key scan across generated packet rows and artifacts.
- `python -m py_compile` for new Python files. If Windows `__pycache__` friction blocks bytecode writing, run AST syntax fallback and record it explicitly.
- Focused pytest for the route.
- Committed-diff scan proving no changes under `src/`, `prompts/`, `config/`, canaries, live execution/risk/permissions/safety/selector paths, MT5 order/account/history behavior, credentials, registry, remotes, or live trading behavior.
- Final `python scripts\generate_live_state.py` and freshness read.

## Completion Rules

Do not mark complete unless all are true:

- Route has one accepted terminal decision.
- A source-hashed candidate packet or exact zero-packet/source-requirement proof exists.
- Every consumed source/log/parser artifact is hashed.
- Contaminated CAT V3 rows and embargo overlaps are excluded.
- 55-field binding is complete per admitted row or fail-closed for zero packet.
- Duplicate denominator and no-leak audits pass.
- Next G12 audit prompt pack exists.
- Verifier and focused tests pass or failures are reduced to exact environmental friction with AST/alternate verification.
- Scoped commits include artifacts, builder, verifier, tests, and context refresh when research state changes.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.

If anything blocks, pursue it until cleared, proven impossible from approved local routes, or reduced to an exact owner/access/source/capture requirement. Do not call the goal complete on a vague blocker.
