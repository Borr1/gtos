# OTG0 Prereg Classification Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Outcome review opened:** `false`  
**Validation safe:** `false`  
**Generated at UTC:** `2026-05-06T17:26:41Z`  
**Git HEAD at generation:** `ef439f37`

## Scope

This ledger classifies all `97` owner-review preregs from `research/science_program_2026_05/05_synthesis/G0_G12_OWNER_FULL_RESEARCH_REVIEW_2026-05-06.md` into OTG0 testing/control lanes. It is routing metadata only. It is not an outcome test, validation result, source-safety flip, or promotion artifact.

## Counts

| OTG0 lane | Count |
|---|---|
| `broker_actual_r_blocked` | 10 |
| `control_only` | 33 |
| `forward_shadow_prospective` | 7 |
| `lifecycle_no_fill_existing_data_audit` | 10 |
| `source_asof_cleanup_first` | 21 |
| `synthetic_replay_existing_data_audit` | 16 |

## Owner Class Mapping

| Owner class | OTG0 lane | Count | Next lane |
|---|---|---|---|
| `EXISTING_DATA_LIFECYCLE_OR_NO_FILL_CANDIDATE` | `lifecycle_no_fill_existing_data_audit` | 10 | `OTL1` |
| `EXISTING_DATA_SYNTHETIC_REPLAY_CANDIDATE` | `synthetic_replay_existing_data_audit` | 16 | `OTL2` |
| `SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST` | `source_asof_cleanup_first` | 21 | `OTL3` |
| `FORWARD_SHADOW_OR_PROSPECTIVE` | `forward_shadow_prospective` | 7 | `OTL-FORWARD` |
| `BROKER_ACTUAL_R_SEPARATE_OR_BLOCKED` | `broker_actual_r_blocked` | 10 | `OTL-BROKER-R` |
| `CONTROL_OR_OBSERVATION_ONLY` | `control_only` | 33 | `OTL-CONTROL` |

## Immediate Packet-Audit Queue

| Packet | Experiment | Lane | OTG0 lane | Status |
|---|---|---|---|---|
| `OTG0-PKT-011` | `G10-EXP-PREFILL-003` | `G10` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-013` | `G10-EXP-RISKBANK-005` | `G10` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-014` | `G10-EXP-XDOMAIN-008` | `G10` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-015` | `EXP-G11-COVERAGE-GATE-002` | `G11` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-016` | `EXP-G11-FRICTION-GATE-007` | `G11` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-017` | `EXP-G11-OBSERVER-EXPANSION-006` | `G11` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-018` | `EXP-G11-OPTIONS-VOL-005` | `G11` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-025` | `EXP-G2-GARCH-LIFECYCLE-002` | `G2` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-029` | `EXP-G2-SURVIVAL-PATH-006` | `G2` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-031` | `EXP-G3-DC-OVERSHOOT-002` | `G3` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-032` | `EXP-G3-DC-SWING-001` | `G3` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-036` | `EXP-G3-TDA-007` | `G3` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-039` | `EXP-G4-FILL-QUALITY-008` | `G4` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-041` | `EXP-G4-OFI-DEPTH-001` | `G4` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-042` | `EXP-G4-PROFILE-VWAP-004` | `G4` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-044` | `EXP-G4-STOP-CASCADE-MOMENTUM-006` | `G4` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-045` | `EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003` | `G4` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-047` | `EXP-G4G3-DC-DEPTH-012` | `G4` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-049` | `EXP-G4G6-CASCADE-GENERIC-010` | `G4` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-050` | `EXP-G4G6-DEPTH-CONTINUATION-009` | `G4` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-051` | `EXP-G5-AINARR-006` | `G5` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-052` | `EXP-G5-AMH-004` | `G5` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-053` | `EXP-G5-CROWD-001` | `G5` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-055` | `EXP-G5-NEWS-005` | `G5` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-056` | `EXP-G5-PRED-003` | `G5` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-057` | `EXP-G5-XG4-PRED-007` | `G5` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-059` | `EXP-G5-XG7-MACRO-ATTN-009` | `G5` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-060` | `G6-EXP-001-OB-VS-GENERIC-RETRACE` | `G6` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-062` | `G6-EXP-003-OPENING-DRIVE-CONTINUATION` | `G6` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-063` | `G6-EXP-004-EXHAUSTION-CHANGEPOINT` | `G6` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-066` | `G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE` | `G6` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-067` | `EXP-G7-BIS-CARRY-007` | `G7` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-069` | `EXP-G7-CROSSASSET-STRESS-008` | `G7` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-070` | `EXP-G7-DXY-SOFT-002` | `G7` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-071` | `EXP-G7-FOMC-ATTN-003` | `G7` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-073` | `EXP-G7-GOLD-FLOW-009` | `G7` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-074` | `EXP-G7-LBMA-FIX-004` | `G7` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-075` | `EXP-G7-USD-REALRATE-001` | `G7` | `synthetic_replay_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY` |
| `OTG0-PKT-077` | `EXP-G7-XG5-MACRO-ATTN-010` | `G7` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-078` | `EXP-G7-XG8-VOL-MACRO-011` | `G7` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-079` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | `G8` | `lifecycle_no_fill_existing_data_audit` | `PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW` |
| `OTG0-PKT-080` | `EXP-G8-GEX-FEEDBACK-001` | `G8` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-081` | `EXP-G8-GVZ-METALS-003` | `G8` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-083` | `EXP-G8-PROXYMAP-006` | `G8` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-084` | `EXP-G8-VIX1D9D-STRESS-002` | `G8` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-085` | `EXP-G8-VRP-004` | `G8` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |
| `OTG0-PKT-086` | `EXP-G8-VVIX-TAIL-007` | `G8` | `source_asof_cleanup_first` | `SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST` |

## Duplicate Hypothesis Families

Two master hypothesis IDs have both an original and CD2 experiment row. They must share a duplicate/parent-child policy before any test implementation:

```json
{
  "HYP-G8-VIX1D9D-STRESS-002": [
    "EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001",
    "EXP-G8-VIX1D9D-STRESS-002"
  ],
  "HYP-G9-OFFLINE-RL-POLICY-009": [
    "EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001",
    "EXP-G9-OFFLINE-RL-009"
  ]
}
```

## NO_PROMOTION_VERDICT

All rows remain research-control only. Every packet keeps `outcome_review_opened=false` and every source contract keeps `validation_safe=false`.
