# SCID Forward Capture Additive Implementation Context Anchor - 2026-05-12

## Route

- Route id: `SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_FROM_ACCEPTED_PARALLEL_G12_WAVE`
- Controlling prompt: `research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_FROM_ACCEPTED_PARALLEL_G12_WAVE_GOAL_PROMPT_2026-05-12.md`
- Accepted upstream decision ledger: `research/science_program_2026_05/06_outcome_testing/g0_scid_parallel_g12_integration_orchestration/G0_SCID_PARALLEL_G12_INTEGRATION_DECISION_LEDGER_2026-05-12.md`
- Accepted decision: `ACCEPT_AS_G0_PARALLEL_G12_INTEGRATION_FOR_ADDITIVE_IMPLEMENTATION_SEQUENCE`

## Mandatory Preflight Completed Before Source Edits

- Regenerated `.context/LIVE_STATE.md` with `python scripts/generate_live_state.py`.
- Read `.context/LIVE_STATE.md`.
- Read latest handoff: `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`.
- Read `.context/00_core/quick_reference_card.md`.
- Read `.context/00_core/research_operating_doctrine.md`.
- Read `.context/00_core/research_current_state.md`.
- Read `.context/00_READING_ORDER.md`.
- Read `.context/00_core/goal_session_research_discipline.md`.
- Read `.context/00_core/local_heavy_data_inventory.md`.
- Read `.context/00_core/ai_in_loop_cost_control_research_plan.md`.

## Implementation Boundary

This route is an additive evidence-capture implementation only. It must not:

- promote, score, validate, or claim an edge;
- open outcome review;
- read or alter live trading decisions;
- change prompts, risk, execution, selector, canary, or safety behavior;
- call paid APIs, broker order/deal/history endpoints, vendor APIs, or remote services;
- commit raw market blobs or account/order/deal/position identifiers.

All SCID rows must carry:

- `promotion_verdict: NO_PROMOTION_VERDICT`
- `validation_safe: false`
- `outcome_review_opened: false`
- `live_effect: false`

## Accepted Capture Surface

The accepted schema package requires ten capture groups under schema version `scid_forward_source_capture_v1`:

1. `baseline_control_fields`
2. `framework_setup_family`
3. `future_orderflow_depth_proxy_requirements`
4. `intended_entry_reference`
5. `intended_side_direction`
6. `intended_stop_reference`
7. `intended_target_reference`
8. `lifecycle_fill_cancel_expiry_source_status`
9. `lower_timeframe_asof_path_availability`
10. `poi_type_bounds_source`

Expected candidate boundary from the accepted G12 package: 3,014 prospective candidates. This implementation captures source-safe fields for future denominators only; it does not evaluate those candidates.

