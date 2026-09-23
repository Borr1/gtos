# Expansion Candidate Ledger

- **route_id:** `G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS`
- **evidence_class:** `G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_40_card_denominator_unchanged": true,
  "accepted_denominator_count": 40,
  "all_expansion_candidates_remain_outside_accepted_denominator": true,
  "artifact_family": "expansion_candidate_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY",
  "g0_discovered_additional_candidate_count": 4,
  "g0_discovered_additional_candidates": [
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE",
      "candidate_family": "sealed_partition_and_embargo_hygiene",
      "candidate_id": "G0-EXP-PARTITION-001",
      "future_acceptance_requirement": "Separate expansion acceptance route must prove source fields and denominator use before accepted-card inclusion.",
      "source_safe_hypothesis_or_field": "partition/embargo/frozen-rowset quality as a first-class source-control candidate before any result packet"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE",
      "candidate_family": "domain_x_source_availability_intersection_controls",
      "candidate_id": "G0-EXP-DOMAIN-MISSINGNESS-001",
      "future_acceptance_requirement": "Separate route must freeze source statuses before any denominator entry.",
      "source_safe_hypothesis_or_field": "science-domain by source-availability status as a control stratum, not an edge claim"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE",
      "candidate_family": "cross_domain_negative_control_bundle",
      "candidate_id": "G0-EXP-NEGCTRL-001",
      "future_acceptance_requirement": "Separate route must define controls without looking at result labels.",
      "source_safe_hypothesis_or_field": "bundle adversarial controls across calendar, duplicate, source-hash, and missingness fields before scoring"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE",
      "candidate_family": "rowset_materialization_failure_modes",
      "candidate_id": "G0-EXP-ROWSET-001",
      "future_acceptance_requirement": "Separate route must prove rowset failure modes are source/control fields only.",
      "source_safe_hypothesis_or_field": "rowset construction failure mode as a quarantined diagnostic candidate for later packet quality audits"
    }
  ],
  "generated_at_utc": "2026-05-12T14:25:41Z",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "preserved_target_expansion_candidate_count": 8,
  "preserved_target_expansion_candidates": [
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "duplicate_key_collision_and_drift_controls",
      "candidate_id": "EXP-DENOM-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "duplicate-key collision, drift, and group-membership stability as a denominator hygiene stratum"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "source_missingness_as_control_not_edge",
      "candidate_id": "EXP-MISS-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "fail-closed source availability/missingness status as an adversarial control for later result packets"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "poi_source_bar_cardinality_and_freshness",
      "candidate_id": "EXP-POI-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "POI source bar id count, source timeframe, and detection-rule version as preregistered context fields"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "ltf_availability_gap_topology",
      "candidate_id": "EXP-LTF-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "lower-timeframe availability pattern itself as a source-status control before any path values are used"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "orderflow_proxy_validity_state",
      "candidate_id": "EXP-PROXY-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "proxy availability, source family, mapping version, and publication/capture as-of as source-status controls"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "redacted_lifecycle_state_transition_source_status",
      "candidate_id": "EXP-LIFE-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "redacted lifecycle event type and source-event clock basis as packet-quality controls, not trade outcome labels"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "calendar_fix_dst_context_packet_fields",
      "candidate_id": "EXP-CAL-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "calendar/fix/DST context fields as pre-result source-control descriptors for session/cross-asset cards"
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "assigned_next_route": "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
      "candidate_family": "hash_integrity_placebo_controls",
      "candidate_id": "EXP-ADV-001",
      "future_acceptance_requirement": "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator.",
      "source_safe_hypothesis_or_field": "source-hash completeness and missing-hash strata as placebo/control families"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS",
  "schema_version": "g0_scid_noapi_prereg_synthesis_v1",
  "total_quarantined_expansion_candidate_count": 12,
  "validation_safe": false
}
```
