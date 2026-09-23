# OTI4 Opening-Drive Completion Audit

- Generated at UTC: `2026-05-08T14:58:23Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`
- Live effect: `false`

- Maps prompt requirements to concrete artifacts and evidence.

```json
{
  "artifact_family": "OTI4_OPENING_DRIVE_COMPLETION_AUDIT",
  "can_mark_goal_complete": true,
  "exact_blocker_counts": {
    "BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE": 12,
    "BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE": 6,
    "BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION": 8,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3
  },
  "generated_at_utc": "2026-05-08T14:58:23Z",
  "lane_id": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
  "live_effect": false,
  "objective_restatement": "Source-correct or contract-revise the 80 OTI4 opening-drive missing-source rows without opening outcomes, so each row has source-hashed range/breakout/as-of proof or an exact blocker.",
  "outcome_review_opened": false,
  "parser_version": "oti4_opening_drive_tick_mid_m1_source_contract_v1_2026_05_08",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": [
        ".context/LIVE_STATE.md",
        ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/research_current_state.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/local_heavy_data_inventory.md",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json"
      ],
      "requirement": "Mandatory GTOS preflight and controlling prompt read",
      "status": "covered"
    },
    {
      "evidence": {
        "row_count": 80,
        "source_corrected_or_exact_blocked_rows": 80
      },
      "requirement": "80 OTI4 rows covered",
      "status": "covered"
    },
    {
      "evidence": {
        "exact_blocker_counts": {
          "BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE": 12,
          "BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE": 6,
          "BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION": 8,
          "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3
        },
        "proof_status_counts": {
          "EXACT_IMPOSSIBILITY_OR_SOURCE_BLOCKER": 11,
          "SOURCE_HASHED_RANGE_BREAKOUT_ASOF_PROOF": 69
        }
      },
      "requirement": "Every row has source-hashed range/breakout/as-of proof or exact impossibility/access blocker",
      "status": "covered"
    },
    {
      "evidence": {
        "live_effect": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
      "status": "covered"
    },
    {
      "evidence": {
        "forbidden_sources_read": [],
        "result_labels_assigned": 0
      },
      "requirement": "No R/performance or live trading surfaces",
      "status": "covered"
    },
    {
      "evidence": {
        "asof_failure_count_for_source_corrected_rows": 0,
        "source_corrected_contract_key_count": 16,
        "source_hash_mismatch_count": 0
      },
      "requirement": "Source-hash/no-leak/duplicate/as-of checks",
      "status": "covered"
    }
  ],
  "proof_status_counts": {
    "EXACT_IMPOSSIBILITY_OR_SOURCE_BLOCKER": 11,
    "SOURCE_HASHED_RANGE_BREAKOUT_ASOF_PROOF": 69
  },
  "remaining_unresolved_generic_future_work": [],
  "result_labels_assigned": 0,
  "row_count": 80,
  "row_route_decision_counts": {
    "CONTRACT_REVISED_EXCLUDE_BREAKOUT_SIDE_MISMATCH": 12,
    "CONTRACT_REVISED_EXCLUDE_DECISION_BEFORE_FROZEN_RANGE_CLOSE": 8,
    "CONTRACT_REVISED_EXCLUDE_NO_BREAKOUT_ASOF": 6,
    "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT": 51,
    "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY": 3
  },
  "source_contract_id": "OTI4_OPENING_DRIVE_TICK_RANGE_BREAKOUT_SOURCE_CONTRACT_V1",
  "source_hash_mismatch_count": 0,
  "validation_safe": false
}
```
