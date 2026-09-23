# OTB1 Schema Validation Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

## Exact Primary Row Contract

| Field |
| --- |
| setup_id_or_candidate_id |
| decision_asof_utc |
| source_capture_utc |
| pending_created_utc_if_applicable |
| lifecycle_event_id |
| lifecycle_state |
| fill_or_no_fill_state |
| cancel_expiry_or_wrong_side_reason |
| duplicate_group_id |
| source_hash |
| source_symbol |
| packet_build_source_paths |
| label_family |
| forbidden_primary_fields_absent |

## Packet Validation

| Packet | Experiment | Decision | Valid | Rows | Issues |
| --- | --- | --- | --- | --- | --- |
| OTG0-PKT-011 | G10-EXP-PREFILL-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-016 | EXP-G11-FRICTION-GATE-007 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-017 | EXP-G11-OBSERVER-EXPANSION-006 | BLOCKED_WITH_OWNER_QUESTION | True | 0 | 0 |
| OTG0-PKT-025 | EXP-G2-GARCH-LIFECYCLE-002 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-029 | EXP-G2-SURVIVAL-PATH-006 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-045 | EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 2 | 0 |
| OTG0-PKT-055 | EXP-G5-NEWS-005 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-059 | EXP-G5-XG7-MACRO-ATTN-009 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-071 | EXP-G7-FOMC-ATTN-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 8 | 0 |
| OTG0-PKT-079 | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | True | 4 | 0 |

## Forbidden Primary Field Check

Forbidden fields checked: actual_r, broker_actual_r, future_return, outcome_r, post_entry_path, synthetic_path_r, trade_result, win_loss. Primary rows also reject keys containing result/R fragments used by OTB1.
