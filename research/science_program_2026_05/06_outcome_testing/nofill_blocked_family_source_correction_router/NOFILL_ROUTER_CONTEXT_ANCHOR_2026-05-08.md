# NOFILL Router Context Anchor

Generated: 2026-05-08T14:13:17Z

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Route all 246 G12-blocked no-fill categorical rows to exact source-correction, contract-revision, access/source request, or impossibility decisions without opening result/performance/live lanes.

## Preflight Files Read

- `.context/LIVE_STATE.md`
- `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/local_heavy_data_inventory.md`
- `.context/00_READING_ORDER.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_GOAL_PROMPT_2026-05-08.md`

## Starting Counts

{
  "blocked_rows": 246,
  "blocker_code_counts": {
    "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
    "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
    "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
    "BLOCK_RESULT_MISSING_SOURCE": 80,
    "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 1,
    "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1
  },
  "blocker_tuple_counts": {
    "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
    "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
    "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
    "BLOCK_RESULT_MISSING_SOURCE": 80,
    "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED+BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1
  },
  "eligible_rows": 52,
  "g12_blocked_cnr061_rows_excluded": 94,
  "row_0127_terminal_first_touch": "2026-05-06T07:15:00.634000Z",
  "row_0127_tick_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
  "six_t3_rows_excluded": [
    "CNR-T3-CAND-0001",
    "CNR-T3-CAND-0002",
    "CNR-T3-CAND-0003",
    "CNR-T3-CAND-0004",
    "CNR-T3-CAND-0005",
    "CNR-T3-CAND-0006"
  ],
  "total_categorical_rows": 298
}

## Forbidden Boundaries

- No R/performance scoring.
- No win-rate, expectancy, DSR/PBO, validation, promotion, or live-effect claims.
- No broker actual-R, account history, live order/deal/position labels, hidden labels, or blocked CNR061/six T3 scoring.
- No paid/API/Databento calls and no MT5 order/account/history calls.
- No live trading prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, remotes, registry promotion flags, validation flags, outcome-review flags, live-effect flags, or order behavior changes.
