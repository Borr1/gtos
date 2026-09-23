# OTI4 Opening-Drive Context Anchor

- Generated at UTC: `2026-05-08T14:58:23Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`
- Live effect: `false`

- Preserves the controlling prompt, active question stack, and stop-condition status.

```json
{
  "active_question_stack": [
    "Can the 80 OTI4 missing-source rows be source-corrected from OTX and local tick files?",
    "Which rows require contract revision because the frozen range was unavailable as of decision?",
    "Which rows remain exact local source gaps after local-heavy search?"
  ],
  "artifact_family": "OTI4_OPENING_DRIVE_CONTEXT_ANCHOR",
  "artifact_outputs": [
    "OTI4_OPENING_DRIVE_CONTEXT_ANCHOR_2026-05-08.json",
    "OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "OTI4_OPENING_DRIVE_SOURCE_CONTRACT_PACKET_2026-05-08.json",
    "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_2026-05-08.json",
    "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_2026-05-08.jsonl",
    "OTI4_OPENING_DRIVE_SOURCE_HASH_ASOF_DUPLICATE_AUDIT_2026-05-08.json",
    "OTI4_OPENING_DRIVE_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json",
    "OTI4_OPENING_DRIVE_COMPLETION_AUDIT_2026-05-08.json"
  ],
  "controlling_prompt": "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
  "current_head_expected_at_start": "9cad99c8 docs: refresh research state after no-fill router merge",
  "generated_at_utc": "2026-05-08T14:58:23Z",
  "lane_id": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
  "live_effect": false,
  "outcome_review_opened": false,
  "parser_version": "oti4_opening_drive_tick_mid_m1_source_contract_v1_2026_05_08",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "source_contract_id": "OTI4_OPENING_DRIVE_TICK_RANGE_BREAKOUT_SOURCE_CONTRACT_V1",
  "stop_condition_status": "SATISFIED_BY_SOURCE_CORRECTION_OR_EXACT_BLOCKERS",
  "validation_safe": false
}
```
