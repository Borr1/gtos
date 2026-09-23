# G12 NOFILL Forward Source Capture Duplicate Denominator Audit 2026-05-09

Route: `G12_NOFILL_FORWARD_SOURCE_CAPTURE_PROTOTYPE_ACCEPTANCE_AUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`


| Item | Value |
|---|---|
| Status | `PASS` |
| Frozen equation | `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject` |
| Prototype rows | `298` |
| Accepted row-level denominator | `225` |
| Primary duplicate-key denominator | `182` |
| Secondary duplicate-group denominator | `139` |
| Reject-overlap rows | `47` |
| Reject-overlap denominator effect | `{"duplicate_group_id_count_delta_from_rejects": 0, "nofill_duplicate_key_count_delta_from_rejects": 0, "reason": "The packet filters to accepted rows before counting or duplicate collapsing; reject rows remain exclusion proof only.", "row_level_count_delta_from_rejects": 0}` |
