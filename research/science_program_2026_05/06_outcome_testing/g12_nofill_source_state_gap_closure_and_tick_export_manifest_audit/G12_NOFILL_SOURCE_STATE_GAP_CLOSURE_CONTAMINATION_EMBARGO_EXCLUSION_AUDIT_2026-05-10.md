# G12 Nofill Source State Gap Closure Contamination Embargo Exclusion Audit 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`
- contamination_embargo_blocker_count: `17`

```json
{
  "artifact_family": "contamination_embargo_exclusion_audit",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "clean_denominator_policy": "excluded_from_clean_denominators_result_labels_validation_and_promotion",
  "contamination_candidate_ids_subset_of_blockers": true,
  "contamination_embargo_blocker_count": 17,
  "credentials_touched": false,
  "failures": [],
  "g0_reject_row_count": 9,
  "g0_reject_rows": [
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
  "generated_at_utc": "2026-05-10T09:13:22Z",
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
  "reject_policy": "nine_rejects_barred_from_clean_denominators_unless_separate_future_source_control_proof",
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "rows": [
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-16",
      "symbol": "GBPJPY"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-17",
      "symbol": "GBPUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-17",
      "symbol": "GBPUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-20",
      "symbol": "GBPUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-20",
      "symbol": "GBPUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-21",
      "symbol": "GBPUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "NAS100_2026-04-29T15:00:05.012307+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-29",
      "symbol": "NAS100"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "NAS100_2026-05-01T08:15:00+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-05-01",
      "symbol": "NAS100"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-16",
      "symbol": "US30_cash"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-16",
      "symbol": "USDJPY"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-21",
      "symbol": "USDJPY"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAGUSD_2026-05-01T08:30:00+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-05-01",
      "symbol": "XAGUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-16",
      "symbol": "XAUUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-16",
      "symbol": "XAUUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-04-17",
      "symbol": "XAUUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-05-01T08:15:00+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-05-01",
      "symbol": "XAUUSD"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-05-01T15:45:00+00:00",
      "checks": {
        "clean_denominator_excluded": true,
        "future_clean_requires_separate_proof": true,
        "handling_status_excluded": true,
        "reusable_only_non_validation": true
      },
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "source_date": "2026-05-01",
      "symbol": "XAUUSD"
    }
  ],
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "validation_safe": false
}
```
