# G0 NOFILL Historical Source Expansion 9 Reject Learning Ledger

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Summary

All nine rejects remain excluded from clean denominators and are reusable only in non-validation learning roles.

## Machine Payload

```json
{
  "artifact_family": "nine_reject_learning_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T07:53:15Z",
  "learning": [
    "Embargo and contamination rules are active enough to exclude nearby candidate rows even when geometry fields exist.",
    "Rejected rows teach future source expansion to avoid parent-contaminated dates and one-day same-symbol/source-lane overlaps.",
    "Rejects can harden source-contract fixtures and stress controls, but cannot increase clean sample size."
  ],
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rejected_row_count": 9,
  "route_id": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW",
  "rows": [
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-04",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-03"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "GBPJPY_2026-05-04T03:00:00+00:00",
      "decision_time_utc": "2026-05-04T03:00:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-04",
      "symbol": "GBPJPY",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-06",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-05"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "GBPJPY_2026-05-06T02:30:00+00:00",
      "decision_time_utc": "2026-05-06T02:30:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-06",
      "symbol": "GBPJPY",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-03",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-03"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "NAS100_2026-05-03T16:15:00+00:00",
      "decision_time_utc": "2026-05-03T16:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-03",
      "symbol": "NAS100",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-04",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-03"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
      "decision_time_utc": "2026-05-04T07:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-04",
      "symbol": "NAS100",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-05",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-04"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "NAS100_2026-05-05T07:15:00+00:00",
      "decision_time_utc": "2026-05-05T07:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-05",
      "symbol": "NAS100",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-06",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-05"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "NAS100_2026-05-06T07:15:00+00:00",
      "decision_time_utc": "2026-05-06T07:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-06",
      "symbol": "NAS100",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "one_day_embargo_overlap_with_contaminated_date=2026-05-06"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "NAS100_2026-05-07T07:15:00+00:00",
      "decision_time_utc": "2026-05-07T07:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-07",
      "symbol": "NAS100",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-04",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-03"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
      "decision_time_utc": "2026-05-04T07:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-04",
      "symbol": "XAUUSD",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    },
    {
      "admission_reasons": [
        "source_date_contaminated_by_parent_g12=2026-05-05",
        "one_day_embargo_overlap_with_contaminated_date=2026-05-04"
      ],
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "candidate_id": "XAUUSD_2026-05-05T08:15:00+00:00",
      "decision_time_utc": "2026-05-05T08:15:00+00:00",
      "exact_next_action": "Do not add to clean denominators. Reuse only as exclusion proof, forensics, stress controls, or source-contract fixtures unless a separate future G12 audit proves an independent uncontaminated source lane.",
      "reusable_only_as": [
        "forensics_learning",
        "stress_control",
        "source_contract_fixture"
      ],
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "source_date": "2026-05-05",
      "symbol": "XAUUSD",
      "terminal_route_class": "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO",
      "validation_safe": false
    }
  ],
  "schema_version": "g0_nofill_historical_source_expansion_packet_synthesis_control_review_v1",
  "summary": "All nine rejects remain excluded from clean denominators and are reusable only in non-validation learning roles.",
  "terminal_route_class_counts": {
    "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO": 9
  },
  "validation_safe": false
}
```
