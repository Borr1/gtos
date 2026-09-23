# OTB2 Ambiguity Ledger - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

| ID | Topic | Status | Remaining question |
| --- | --- | --- | --- |
| OTB2-AMB-001 | Default V2/V3 ordered path source | RESOLVED_FOR_READY_G10_WITH_LOCAL_SHADOW_PATH_ROWS | Should historical V2/V3 result-bearing event logs be regenerated into input-only rows, or remain rejected as packet sources? |
| OTB2-AMB-002 | Result-bearing event logs | CONTROLLED_BY_REJECTION_LEDGER | None for OTB2; later lanes need an input-only replay export if they want historical rows. |
| OTB2-AMB-003 | Same-bar ambiguity | ROW_LEVEL_POLICY_FIELD_EMITTED_FOR_READY_PACKET | Blocked packets need their own source-specific same-bar policy before G12 can accept them. |
| OTB2-AMB-004 | Source contracts for G3/G4/G5/G6/G7 feature packets | MOSTLY_BLOCKED_WITH_OWNER_QUESTIONS | Owner/G12 must choose or approve source-specific packet builders for those feature families. |
| OTB2-AMB-005 | Same-dataset contamination | CONTROLLED_PACKET_INPUT_ONLY | Any future result lane must use quarantine and G12 post-test audit before interpretation. |
