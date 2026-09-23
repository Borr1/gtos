# G12 SCID Future Capture Blocked15 Source-State Materialization Audit

Evidence class: `G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY`

Audit the target route:

`research/science_program_2026_05/06_outcome_testing/scid_future_capture_field_source_state_materialization_for_blocked15/`

Target prompt:

`research/science_program_2026_05/04_goal_prompts/G0NAPI_R3_FUTURE_CAPTURE_SOURCE_GOAL_PROMPT_2026-05-12.md`

## Mandatory Checks

1. Run mandatory GTOS preflight: `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
2. Recompute the blocked subset from `G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json` and verify exactly 15 cards route to `SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15`.
3. Verify every missing field maps to accepted SCID capture groups and all ten capture groups remain visible.
4. Independently validate every row in `SCID_FUTURE_CAPTURE_RECOVERED_SOURCE_STATE_ROWS_2026-05-12.jsonl` with `src.research_infra.forward_capture.validate_scid_forward_source_capture_row`.
5. Confirm recovered rows do not contain broker account/order/history/deal/position payloads, raw tickets, actual-R, synthetic-R, PnL, win-rate, expectancy, validation labels, or promotion claims.
6. Confirm recovered rows are treated as source-state examples and not as accepted 40-card result-denominator closure.
7. Confirm prospective contracts cover source logger, as-of clock, redaction, fail-closed status, parser/hash proof, owner/restart gate, tests, verifier, and G12 criteria.
8. Confirm the search ledger includes accepted artifacts, additive implementation evidence, code/tests/verifiers, shadow logs, absolute local roots, and prior worktrees.
9. Confirm no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid vendor/broker account-order-history-deal-position/raw-market-blob/live restart/live behavior/trading-risk-safety-prompt-decision changes were opened.

## Required Output

Emit a G12 audit route with a decision ledger, source-search audit, recovered-row schema/redaction audit, contract exactness audit, completion audit, verifier/focused tests, and the next G0 blocked-card unblocking synthesis prompt/starter if accepted.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
