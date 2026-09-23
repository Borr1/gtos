# OTB1 Lifecycle/No-Fill Packet Build Ledger - 2026-05-07

**Generated at UTC:** `2026-05-06T19:49:05+00:00`
**Branch/head:** `otb1-lifecycle-packets` / `56a84f3d`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**Outcome tests run:** `false`
**R/result values read:** `false`

## Decision Counts

| Decision | Count |
| --- | --- |
| BLOCKED_WITH_OWNER_QUESTION | 1 |
| PACKET_READY_FOR_G12_BLOCKER_AUDIT | 9 |

## Per-Experiment Packets

| Packet | Experiment | Decision | Rows | Packet hash prefix | Artifact |
| --- | --- | --- | --- | --- | --- |
| OTG0-PKT-011 | G10-EXP-PREFILL-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | 760b65e1b1874811 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-011_G10-EXP-PREFILL-003_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-016 | EXP-G11-FRICTION-GATE-007 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | 4e8d7b52e921c782 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-016_EXP-G11-FRICTION-GATE-007_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-017 | EXP-G11-OBSERVER-EXPANSION-006 | BLOCKED_WITH_OWNER_QUESTION | 0 | 247913fe52e098e1 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-017_EXP-G11-OBSERVER-EXPANSION-006_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-025 | EXP-G2-GARCH-LIFECYCLE-002 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | 9828ad8c50827ee7 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-025_EXP-G2-GARCH-LIFECYCLE-002_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-029 | EXP-G2-SURVIVAL-PATH-006 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | 515687046a683413 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-029_EXP-G2-SURVIVAL-PATH-006_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-045 | EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 2 | 34365d19b2a3fd46 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-045_EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-055 | EXP-G5-NEWS-005 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | 927e646d05435208 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-055_EXP-G5-NEWS-005_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-059 | EXP-G5-XG7-MACRO-ATTN-009 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | edbf3d26f6131e1d | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-059_EXP-G5-XG7-MACRO-ATTN-009_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-071 | EXP-G7-FOMC-ATTN-003 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 8 | 42327634388c33d2 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-071_EXP-G7-FOMC-ATTN-003_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |
| OTG0-PKT-079 | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001 | PACKET_READY_FOR_G12_BLOCKER_AUDIT | 4 | b1be3387242b7653 | research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/packets/OTG0-PKT-079_EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001_LIFECYCLE_NO_FILL_PACKET_2026-05-07.json |

## Base Lifecycle Evidence

| Metric | Value |
| --- | --- |
| raw_pending_limit_lifecycle_rows | 174 |
| raw_pending_lifecycle_groups | 8 |
| pending_limit_lifecycle_audit_rows | 49 |
| opportunity_lifecycle_audit_rows | 1360 |
| base_packet_rows | 8 |
| base_lifecycle_state_counts | {'still_pending': 5, 'wrong_side': 3} |

## Guardrails

- Primary lifecycle rows contain only the exact OTB1 field contract.
- Source hashes are computed from sanitized lifecycle/audit source rows after forbidden R/result fields are dropped.
- OTB3 no-leak and source sidecars are used as packet-building context only; no master registry rows were edited.
- No quarantine/result files were created.
