# G0 NOFILL CAT V2 Source Contract And Capture Backlog

Promotion posture: `NO_PROMOTION_VERDICT`.

## Capture Backlog Summary

- Prospective pending lifecycle fields must be captured as-of, source-hashed, and separate from results.
- Fill/path event ordering must store same-tick ambiguity rather than guess order.
- Opening-drive projection fields must freeze range and breakout inputs before labels.
- Duplicate source identity must be part of every future packet.
- Residual blockers need exact source-access manifests and must not become outcome rows.

## Source Contracts

### `PENDING_LIFECYCLE_HYGIENE_SOURCE_CONTRACT_V1` (P1)

- Purpose: Prospectively capture pending order lifecycle states before any result use.
- Source learning: Terminal-before-entry and no-entry-through-horizon categories require explicit pending create/cancel/expiry and side-aware touch proof.
- Required fields: `source_inventory_id, source_packet_id, symbol, session, side, decision_asof_utc, pending_create_utc, pending_cancel_or_expiry_utc, cancel_or_expiry_reason, entry_price, side_aware_entry_touch_utc_or_null, terminal_area_touch_utc_or_null, protective_level_touch_utc_or_null, source_coverage_start_utc, source_coverage_end_utc, source_coverage_status, source_hashes, nofill_duplicate_key`
- Forbidden fields: `forbidden_result_metric_fields, forbidden_external_result_fields, forbidden_order_result_fields`
- Owner: `SOURCE_BUILDER`

### `FILL_PATH_EVENT_ORDER_CATEGORICAL_CONTRACT_V1` (P2)

- Purpose: Freeze event-order categories and ambiguity states before any future result lane.
- Source learning: OTI2 labels prove event order can be categorized, while same-tick rows prove ambiguity must be explicit.
- Required fields: `entry_event_utc, protective_event_utc, terminal_event_utc, same_tick_or_same_bar_flag, quote_side_used, source_granularity, source_window_start_utc, source_window_end_utc, source_window_end_reason`
- Forbidden fields: `guessed_sequence, post_outcome_sequence_inference`
- Owner: `SOURCE_BUILDER`

### `OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT_V1` (P3)

- Purpose: Turn opening-drive projection readiness into frozen source fields without label or result inflation.
- Source learning: Opening-drive projection rows are useful inventory but duplicate clustered.
- Required fields: `opening_range_start_utc, opening_range_end_utc, range_high, range_low, range_complete_asof, breakout_side, breakout_close_time, candidate_side_match_status, range_source_hashes, duplicate_projection_key`
- Forbidden fields: `opening_drive_result_label, performance_metric_fields`
- Owner: `SOURCE_BUILDER`

### `DUPLICATE_DENOMINATOR_CONTROL_CONTRACT_V1` (P0_MANDATORY_FOR_ALL_FUTURE_PACKETS)

- Purpose: Prevent row-level projections from becoming inflated denominators.
- Source learning: 225 accepted row-level inputs reduce to 182 unique duplicate keys; 39 noncanonical projections are rejected.
- Required fields: `nofill_duplicate_key, duplicate_group_id, canonical_counting_row_id, is_canonical_counting_row, noncanonical_projection_count, denominator_scope, canonical_selection_reason`
- Forbidden fields: `generated_unstable_duplicate_key, noncanonical_denominator_inclusion`
- Owner: `G0_CONTROL`

### `RESIDUAL_BLOCKER_SOURCE_ACCESS_MANIFEST_V1` (P2)

- Purpose: Clear only exact source/order blockers without opening outcomes.
- Source learning: The 8 blockers have exact source/access requirements and must stay outside labels until cleared by source proof.
- Required fields: `packet_row_id, blocker_family, symbol, requested_window_start_utc, requested_window_end_utc, allowed_source_types, source_path, source_sha256, source_coverage_status, clear_or_remain_blocked_decision`
- Forbidden fields: `accepted_row_scoring, rejected_row_scoring, forbidden_external_result_fields`
- Owner: `SOURCE_ACCESS_LANE`


## Source Hash Inputs

| path | exists | sha256 |
| --- | --- | --- |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route/NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE_GOAL_PROMPT_2026-05-09.md | True | a4cb4f9c7318a55459139ab64b84e5b18bb0700176822f9fd1516945c1b33ef1 |
| .context/LIVE_STATE.md | True | 7b2588f2b8087d6537c769f279e75580f068a93799cb3cba4a269b95ba2fa684 |
| .context/00_core/quick_reference_card.md | True | e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd |
| .context/00_core/research_operating_doctrine.md | True | 27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe |
| .context/00_core/research_current_state.md | True | b99dbb48ad3e2741cb4213a3fd6e5daee052d5c44d09ba8078c5f19f9fdda3e7 |
| .context/00_core/goal_session_research_discipline.md | True | d8637b6e9809801cb8e28d0c2b633bfac9b22f74196d9b3c43c55856fe9ca994 |
| .context/00_core/local_heavy_data_inventory.md | True | fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0 |
| .context/00_READING_ORDER.md | True | 2ec3964df18b42c89059de7cac803d96d9c30e9d330439000695cd444e0fecfc |
| .context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md | True | 0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_2026-05-09.md | True | 99a407122ad8a34c5408dfa79b55cebbbcd63267b65840f0e0239aec03c769e1 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_2026-05-09.md | True | 5438bcbd96a4fa2bc8062a7345b8944ac96429c6c27b64c017e07e33d46101e4 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NEXT_PROMPT_PACK_2026-05-09.md | True | 9fa87589b97f3b16ac2e9c7de861431e914e1ee75bef8c63e9d1159bc32b47d8 |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.md | True | 2ff4ca8ed197195d08dc0de2ef50d91df01c73696e225c1bb455c4153c74ffa8 |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json | True | 3ae8bbd698eefe44d11fd831889c456b1512b1a313f184da7977751f4094d3dd |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.md | True | 69298392099839ea47a7565cd5c5a9ac449a9fd609989dc5598f623709335808 |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.json | True | 9ac6a5166058aa9f2ea19161177fbcc1ee5dd3534d70b22681ec4587cab44bd5 |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.md | True | d94b40190fd9ce96f6db3b189009662eacba8cd55d8bbf7c1898d19321c95cd5 |
| research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json | True | f8ebf01d035f4b199ce49ebe0851de0700b18fda32d44bcb0828fb605dce9fcf |
| research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl | True | 88ed66d0488ef98e302a01897f9717b1cec368964fdccaca737c9cf90150eec4 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json | True | 07c25d2a26785361deee363d33509515057615f6f03ee8d4d5b59fadcb6a05ba |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_2026-05-09.json | True | 728086c4252b86cd2143a747a9869d5d3e6e8ba1070e21794ad61c026b4387f9 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_2026-05-09.json | True | e6c9b13305c6f615de2e6705298601ffba00a778d13eeb73ef04c7a38ed0f019 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_2026-05-09.json | True | bb10a774ee62d3d7c85f43e240c9b45c1a560b6c59ba1440d5621e6eb1de9a52 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_2026-05-09.json | True | f421b2f597c6de5d8480c3748e4bd069dbb90d4469550b2f814de079cb1f54c2 |
| research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_2026-05-09.json | True | e926295d9aff04fbd4cf9e2fb524ef14a6a99cee22534ccd556b5b8f03a5d081 |
