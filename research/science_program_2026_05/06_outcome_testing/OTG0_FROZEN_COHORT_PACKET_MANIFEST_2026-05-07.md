# OTG0 Frozen Cohort Packet Manifest - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Manifest status:** `FROZEN_PACKET_CONTROL_ONLY_OUTCOMES_CLOSED`  
**Outcome review opened:** `false`  
**Validation safe:** `false`

## Rule

These are frozen packet definitions, not outcome packets with results. OTG0 lists source paths from source contracts and required fields from preregs/hypotheses, but it does not inspect source data rows or outcome rows.

## Universal Packet Fields

- `experiment_id`
- `hypothesis_id`
- `frozen_at_utc`
- `outcome_review_opened=false`
- `promotion_verdict=NO_PROMOTION_VERDICT`
- `metric`
- `null`
- `alternative`
- `sample_floor`
- `duplicate_policy`
- `label_separation_policy`
- `source_contract_or_blocker_refs`
- `result_quarantine_path`

## Class Field Profiles

```json
{
  "broker_actual_r_blocked": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "position_id_or_order_ticket",
    "candidate_or_setup_id_link",
    "account_history_exported_utc",
    "entry_fill_utc",
    "close_fill_utc",
    "commission_swap_spread_slippage_fields",
    "intended_entry_sl_tp_fields",
    "manual_trade_exclusion_or_tag",
    "duplicate_group_id",
    "label_family=broker_actual_r",
    "synthetic_path_r_separate_comparator_only"
  ],
  "control_only": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "audit_unit_id",
    "asof_or_control_timestamp",
    "source_or_manifest_id",
    "status_or_blocker_code",
    "duplicate_group_id_if_repeated_status",
    "label_family=context_only_or_observation_only",
    "r_outcome_columns_absent=true"
  ],
  "forward_shadow_prospective": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "capture_start_not_before_frozen_at_utc",
    "decision_asof_utc",
    "source_capture_utc",
    "schema_version",
    "duplicate_group_id",
    "label_family_declared_before_followup",
    "outcome_review_opened=false_until_packet_allows"
  ],
  "lifecycle_no_fill_existing_data_audit": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "setup_id_or_candidate_id",
    "symbol",
    "session",
    "side",
    "decision_asof_utc",
    "source_capture_utc",
    "pending_created_utc_if_applicable",
    "lifecycle_event_id",
    "lifecycle_state",
    "fill_or_no_fill_state",
    "cancel_expiry_or_wrong_side_reason",
    "duplicate_group_id",
    "label_family=lifecycle_no_fill",
    "forbidden_primary_fields_absent=broker_actual_r,synthetic_path_r,win_loss,outcome_r"
  ],
  "source_asof_cleanup_first": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "source_id",
    "url_or_vendor",
    "cache_path",
    "source_fetch_or_file_asof_utc",
    "source_hash",
    "parser_version",
    "publication_asof_timestamp_rule",
    "vintage_or_revision_rule_if_applicable",
    "license_or_access_state",
    "no_lookahead_fixture_status",
    "outcome_columns_absent=true"
  ],
  "synthetic_replay_existing_data_audit": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "setup_id",
    "symbol",
    "session",
    "side",
    "decision_asof_utc",
    "ordered_path_source_id",
    "path_start_utc",
    "path_end_utc",
    "entry_sl_tp_or_level_packet",
    "same_bar_ambiguity_policy",
    "cost_model_version",
    "duplicate_group_id",
    "label_family=synthetic_path_r",
    "broker_actual_r_absent_from_primary_metric=true"
  ]
}
```

## Packet Index

| Packet | Experiment | Class | Sources | Blockers |
|---|---|---|---|---|
| `OTG0-PKT-001` | `SCI-G1-EXP-001` | `broker_actual_r_blocked` | 0 | 2 |
| `OTG0-PKT-002` | `SCI-G1-EXP-002` | `forward_shadow_prospective` | 0 | 1 |
| `OTG0-PKT-003` | `SCI-G1-EXP-003` | `forward_shadow_prospective` | 0 | 1 |
| `OTG0-PKT-004` | `SCI-G1-EXP-004` | `control_only` | 0 | 2 |
| `OTG0-PKT-005` | `SCI-G1-EXP-005` | `control_only` | 0 | 2 |
| `OTG0-PKT-006` | `SCI-G1-EXP-006` | `broker_actual_r_blocked` | 0 | 2 |
| `OTG0-PKT-007` | `G10-EXP-COST-002` | `broker_actual_r_blocked` | 2 | 1 |
| `OTG0-PKT-008` | `G10-EXP-J46J49-004` | `broker_actual_r_blocked` | 2 | 1 |
| `OTG0-PKT-009` | `G10-EXP-PENDING-001` | `forward_shadow_prospective` | 3 | 0 |
| `OTG0-PKT-010` | `G10-EXP-PORTFOLIO-007` | `control_only` | 3 | 1 |
| `OTG0-PKT-011` | `G10-EXP-PREFILL-003` | `lifecycle_no_fill_existing_data_audit` | 2 | 1 |
| `OTG0-PKT-012` | `G10-EXP-PROP-006` | `control_only` | 3 | 1 |
| `OTG0-PKT-013` | `G10-EXP-RISKBANK-005` | `synthetic_replay_existing_data_audit` | 2 | 1 |
| `OTG0-PKT-014` | `G10-EXP-XDOMAIN-008` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-015` | `EXP-G11-COVERAGE-GATE-002` | `source_asof_cleanup_first` | 0 | 3 |
| `OTG0-PKT-016` | `EXP-G11-FRICTION-GATE-007` | `lifecycle_no_fill_existing_data_audit` | 0 | 3 |
| `OTG0-PKT-017` | `EXP-G11-OBSERVER-EXPANSION-006` | `lifecycle_no_fill_existing_data_audit` | 0 | 3 |
| `OTG0-PKT-018` | `EXP-G11-OPTIONS-VOL-005` | `source_asof_cleanup_first` | 0 | 3 |
| `OTG0-PKT-019` | `EXP-G11-PROVENANCE-GATE-001` | `control_only` | 0 | 3 |
| `OTG0-PKT-020` | `EXP-G11-PUBLIC-LAG-004` | `control_only` | 0 | 3 |
| `OTG0-PKT-021` | `EXP-G11-SOURCE-TRANSFER-003` | `control_only` | 0 | 3 |
| `OTG0-PKT-022` | `EXP-G11G4-SOURCE-GATED-ORDERFLOW-008` | `control_only` | 0 | 3 |
| `OTG0-PKT-023` | `EXP-G2-AR-DECAY-001` | `control_only` | 0 | 2 |
| `OTG0-PKT-024` | `EXP-G2-EVT-TAILDEP-005` | `control_only` | 0 | 2 |
| `OTG0-PKT-025` | `EXP-G2-GARCH-LIFECYCLE-002` | `lifecycle_no_fill_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-026` | `EXP-G2-HMM-DWELL-003` | `control_only` | 0 | 2 |
| `OTG0-PKT-027` | `EXP-G2-JUMP-HAWKES-007` | `control_only` | 0 | 2 |
| `OTG0-PKT-028` | `EXP-G2-ROUGH-PATH-004` | `control_only` | 0 | 2 |
| `OTG0-PKT-029` | `EXP-G2-SURVIVAL-PATH-006` | `lifecycle_no_fill_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-030` | `EXP-G3-COH-004` | `control_only` | 3 | 1 |
| `OTG0-PKT-031` | `EXP-G3-DC-OVERSHOOT-002` | `synthetic_replay_existing_data_audit` | 3 | 1 |
| `OTG0-PKT-032` | `EXP-G3-DC-SWING-001` | `synthetic_replay_existing_data_audit` | 3 | 1 |
| `OTG0-PKT-033` | `EXP-G3-HURST-005` | `control_only` | 3 | 1 |
| `OTG0-PKT-034` | `EXP-G3-MFD-006` | `control_only` | 3 | 1 |
| `OTG0-PKT-035` | `EXP-G3-SIG-008` | `broker_actual_r_blocked` | 2 | 1 |
| `OTG0-PKT-036` | `EXP-G3-TDA-007` | `synthetic_replay_existing_data_audit` | 2 | 1 |
| `OTG0-PKT-037` | `EXP-G3-WAV-HAR-003` | `broker_actual_r_blocked` | 3 | 1 |
| `OTG0-PKT-038` | `EXP-G4-AUCTION-CONTEXT-005` | `control_only` | 0 | 2 |
| `OTG0-PKT-039` | `EXP-G4-FILL-QUALITY-008` | `source_asof_cleanup_first` | 0 | 2 |
| `OTG0-PKT-040` | `EXP-G4-NAS100-DEPTH-ADVERSE-002` | `broker_actual_r_blocked` | 0 | 2 |
| `OTG0-PKT-041` | `EXP-G4-OFI-DEPTH-001` | `source_asof_cleanup_first` | 0 | 2 |
| `OTG0-PKT-042` | `EXP-G4-PROFILE-VWAP-004` | `source_asof_cleanup_first` | 0 | 2 |
| `OTG0-PKT-043` | `EXP-G4-PROXY-LEADLAG-007` | `control_only` | 0 | 2 |
| `OTG0-PKT-044` | `EXP-G4-STOP-CASCADE-MOMENTUM-006` | `synthetic_replay_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-045` | `EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003` | `lifecycle_no_fill_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-046` | `EXP-G4G3-AUCTION-PATH-013` | `control_only` | 0 | 2 |
| `OTG0-PKT-047` | `EXP-G4G3-DC-DEPTH-012` | `source_asof_cleanup_first` | 0 | 2 |
| `OTG0-PKT-048` | `EXP-G4G6-AUCTION-EXHAUSTION-011` | `control_only` | 0 | 2 |
| `OTG0-PKT-049` | `EXP-G4G6-CASCADE-GENERIC-010` | `synthetic_replay_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-050` | `EXP-G4G6-DEPTH-CONTINUATION-009` | `source_asof_cleanup_first` | 0 | 2 |
| `OTG0-PKT-051` | `EXP-G5-AINARR-006` | `source_asof_cleanup_first` | 2 | 3 |
| `OTG0-PKT-052` | `EXP-G5-AMH-004` | `synthetic_replay_existing_data_audit` | 1 | 3 |
| `OTG0-PKT-053` | `EXP-G5-CROWD-001` | `synthetic_replay_existing_data_audit` | 2 | 3 |
| `OTG0-PKT-054` | `EXP-G5-HERD-002` | `control_only` | 2 | 3 |
| `OTG0-PKT-055` | `EXP-G5-NEWS-005` | `lifecycle_no_fill_existing_data_audit` | 1 | 3 |
| `OTG0-PKT-056` | `EXP-G5-PRED-003` | `synthetic_replay_existing_data_audit` | 0 | 4 |
| `OTG0-PKT-057` | `EXP-G5-XG4-PRED-007` | `source_asof_cleanup_first` | 0 | 4 |
| `OTG0-PKT-058` | `EXP-G5-XG6-CROWD-DECAY-008` | `forward_shadow_prospective` | 2 | 2 |
| `OTG0-PKT-059` | `EXP-G5-XG7-MACRO-ATTN-009` | `lifecycle_no_fill_existing_data_audit` | 1 | 3 |
| `OTG0-PKT-060` | `G6-EXP-001-OB-VS-GENERIC-RETRACE` | `synthetic_replay_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-061` | `G6-EXP-002-CONTINUATION-NO-RETRACE` | `forward_shadow_prospective` | 0 | 1 |
| `OTG0-PKT-062` | `G6-EXP-003-OPENING-DRIVE-CONTINUATION` | `synthetic_replay_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-063` | `G6-EXP-004-EXHAUSTION-CHANGEPOINT` | `synthetic_replay_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-064` | `G6-EXP-005-TREND-REVERSION-STATE` | `control_only` | 0 | 2 |
| `OTG0-PKT-065` | `G6-EXP-006-RESIDUAL-REVERSION-ANALOG` | `control_only` | 0 | 2 |
| `OTG0-PKT-066` | `G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE` | `synthetic_replay_existing_data_audit` | 0 | 2 |
| `OTG0-PKT-067` | `EXP-G7-BIS-CARRY-007` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-068` | `EXP-G7-COT-GOLD-KILLED-005` | `control_only` | 2 | 1 |
| `OTG0-PKT-069` | `EXP-G7-CROSSASSET-STRESS-008` | `synthetic_replay_existing_data_audit` | 3 | 1 |
| `OTG0-PKT-070` | `EXP-G7-DXY-SOFT-002` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-071` | `EXP-G7-FOMC-ATTN-003` | `lifecycle_no_fill_existing_data_audit` | 3 | 1 |
| `OTG0-PKT-072` | `EXP-G7-FX-COT-MAPPING-006` | `control_only` | 2 | 1 |
| `OTG0-PKT-073` | `EXP-G7-GOLD-FLOW-009` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-074` | `EXP-G7-LBMA-FIX-004` | `synthetic_replay_existing_data_audit` | 2 | 1 |
| `OTG0-PKT-075` | `EXP-G7-USD-REALRATE-001` | `synthetic_replay_existing_data_audit` | 3 | 1 |
| `OTG0-PKT-076` | `EXP-G7-XG11-SOURCE-FRESH-012` | `control_only` | 3 | 3 |
| `OTG0-PKT-077` | `EXP-G7-XG5-MACRO-ATTN-010` | `source_asof_cleanup_first` | 3 | 3 |
| `OTG0-PKT-078` | `EXP-G7-XG8-VOL-MACRO-011` | `source_asof_cleanup_first` | 3 | 3 |
| `OTG0-PKT-079` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | `lifecycle_no_fill_existing_data_audit` | 2 | 1 |
| `OTG0-PKT-080` | `EXP-G8-GEX-FEEDBACK-001` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-081` | `EXP-G8-GVZ-METALS-003` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-082` | `EXP-G8-OPEX-005` | `control_only` | 3 | 1 |
| `OTG0-PKT-083` | `EXP-G8-PROXYMAP-006` | `source_asof_cleanup_first` | 2 | 1 |
| `OTG0-PKT-084` | `EXP-G8-VIX1D9D-STRESS-002` | `source_asof_cleanup_first` | 2 | 1 |
| `OTG0-PKT-085` | `EXP-G8-VRP-004` | `source_asof_cleanup_first` | 3 | 1 |
| `OTG0-PKT-086` | `EXP-G8-VVIX-TAIL-007` | `source_asof_cleanup_first` | 2 | 1 |
| `OTG0-PKT-087` | `EXP-G9-AIML-COMPARATOR-003` | `broker_actual_r_blocked` | 0 | 2 |
| `OTG0-PKT-088` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | `forward_shadow_prospective` | 0 | 1 |
| `OTG0-PKT-089` | `EXP-G9-DEBATE-007` | `broker_actual_r_blocked` | 0 | 2 |
| `OTG0-PKT-090` | `EXP-G9-K55-ARTIFACT-001` | `broker_actual_r_blocked` | 0 | 2 |
| `OTG0-PKT-091` | `EXP-G9-K55-NOLEAK-002` | `control_only` | 0 | 2 |
| `OTG0-PKT-092` | `EXP-G9-K55-SOURCE-006` | `control_only` | 0 | 2 |
| `OTG0-PKT-093` | `EXP-G9-LLM-SELFAUDIT-010` | `control_only` | 0 | 2 |
| `OTG0-PKT-094` | `EXP-G9-OFFLINE-RL-009` | `forward_shadow_prospective` | 0 | 1 |
| `OTG0-PKT-095` | `EXP-G9-REFLEXION-008` | `control_only` | 0 | 2 |
| `OTG0-PKT-096` | `EXP-G9-TOOL-NUMERIC-004` | `control_only` | 0 | 2 |
| `OTG0-PKT-097` | `EXP-G9-TOOL-ORDERFLOW-005` | `control_only` | 0 | 2 |

## Full Machine Manifest

See `OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json` for all `97` packet definitions, source contracts, no-leak fields, nulls, metrics, duplicate policy, and blockers.

## NO_PROMOTION_VERDICT

Packet readiness is not test readiness. OTL1/OTL2/OTL3 must audit packet fields and source/as-of boundaries before any test implementation can read outcomes.
