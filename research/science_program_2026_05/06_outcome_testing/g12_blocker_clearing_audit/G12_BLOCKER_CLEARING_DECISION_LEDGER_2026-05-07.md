# G12 Blocker-Clearing Decision Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Scope:** packet/source/no-leak artifacts only; no outcomes.

## Decision Counts

| Decision | Count |
| --- | --- |
| ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT | 1 |
| BLOCKED_WITH_NEXT_EXACT_QUESTION | 16 |
| REJECT_INVALID_CLEARING | 10 |

## Packet And Artifact Decisions

| Family | Packet | Experiment | Incoming decision | G12 decision | Rows | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| OTB1 | OTG0-PKT-011 | G10-EXP-PREFILL-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-016 | EXP-G11-FRICTION-GATE-007 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-017 | EXP-G11-OBSERVER-EXPANSION-006 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Original packet remains blocked; no primary lifecycle rows exist. |
| OTB1 | OTG0-PKT-025 | EXP-G2-GARCH-LIFECYCLE-002 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-029 | EXP-G2-SURVIVAL-PATH-006 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-045 | EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 2 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-055 | EXP-G5-NEWS-005 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-059 | EXP-G5-XG7-MACRO-ATTN-009 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-071 | EXP-G7-FOMC-ATTN-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 8 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB1 | OTG0-PKT-079 | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 4 | Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty path labels and OTB1 source_hash computation does not exclude that key. |
| OTB2 | OTG0-PKT-013 | G10-EXP-RISKBANK-005 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | REJECT_INVALID_CLEARING | 86 | ordered_path_source_id points to raw path-order source rows with result-bearing keys; local OHLC coverage metadata ends before packet path_end_utc. |
| OTB2 | OTG0-PKT-031 | EXP-G3-DC-OVERSHOOT-002 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-032 | EXP-G3-DC-SWING-001 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-036 | EXP-G3-TDA-007 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-044 | EXP-G4-STOP-CASCADE-MOMENTUM-006 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-049 | EXP-G4G6-CASCADE-GENERIC-010 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-052 | EXP-G5-AMH-004 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-053 | EXP-G5-CROWD-001 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-056 | EXP-G5-PRED-003 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-060 | G6-EXP-001-OB-VS-GENERIC-RETRACE | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-062 | G6-EXP-003-OPENING-DRIVE-CONTINUATION | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-063 | G6-EXP-004-EXHAUSTION-CHANGEPOINT | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-066 | G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-069 | EXP-G7-CROSSASSET-STRESS-008 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-074 | EXP-G7-LBMA-FIX-004 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB2 | OTG0-PKT-075 | EXP-G7-USD-REALRATE-001 | BLOCKED_WITH_OWNER_QUESTION | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | Blocked packet has no primary records and carries an owner question. |
| OTB3 | OTB3_PROPOSED_PATCHSET | SOURCE_NOLEAK_CLEANUP_SIDECAR | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT | n/a | Accepted as context-only sidecar guidance for future packet builders; not accepted as a direct master-registry patch or validation-safe source flip. |
