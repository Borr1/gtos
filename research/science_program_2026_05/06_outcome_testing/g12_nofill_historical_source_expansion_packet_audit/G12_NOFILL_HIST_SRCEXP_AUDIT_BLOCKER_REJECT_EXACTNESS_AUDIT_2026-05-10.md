# Blocker Reject Exactness Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "blocker_reject_exactness_audit",
  "audit_passed": true,
  "audited_rows": [
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "decision_time_utc": "2026-04-14T01:15:05.006410+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "decision_time_utc": "2026-04-14T15:30:05.012815+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "decision_time_utc": "2026-04-15T00:30:05.011237+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
      "decision_time_utc": "2026-04-15T13:15:57.164919+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "decision_time_utc": "2026-04-16T00:16:00.503237+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-16",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
      "decision_time_utc": "2026-04-22T08:00:05.028587+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-22",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
      "decision_time_utc": "2026-04-23T07:16:14.138817+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-23",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-23",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPJPY_2026-04-28T09:00:05.010558+00:00",
      "decision_time_utc": "2026-04-28T09:00:05.010558+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-28",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "GBPJPY_2026-05-04T03:00:00+00:00",
      "decision_time_utc": "2026-05-04T03:00:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-03",
        "2026-05-04",
        "2026-05-05"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-04",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "GBPJPY_2026-05-06T02:30:00+00:00",
      "decision_time_utc": "2026-05-06T02:30:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-05",
        "2026-05-06"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-06",
      "symbol": "GBPJPY",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
      "decision_time_utc": "2026-04-14T07:30:05.011677+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-14",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
      "decision_time_utc": "2026-04-14T14:00:57.743957+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-14",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
      "decision_time_utc": "2026-04-15T07:30:05.010905+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
      "decision_time_utc": "2026-04-15T13:16:01.327115+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "decision_time_utc": "2026-04-17T08:00:59.541491+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-17",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "decision_time_utc": "2026-04-17T14:15:05.012317+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-17",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "decision_time_utc": "2026-04-20T07:45:05.020140+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-20"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-20",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-20",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "decision_time_utc": "2026-04-20T15:31:14.730975+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-20"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-20",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-20",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "decision_time_utc": "2026-04-21T11:30:05.011826+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-20"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-21",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-21",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
      "decision_time_utc": "2026-04-22T07:16:12.155934+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-22",
      "symbol": "GBPUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "NAS100_2026-04-29T15:00:05.012307+00:00",
      "decision_time_utc": "2026-04-29T15:00:05.012307+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-30"
      ],
      "exact_source_requirement_reasons": [
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-29",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "NAS100_2026-05-01T08:15:00+00:00",
      "decision_time_utc": "2026-05-01T08:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-30",
        "2026-05-01"
      ],
      "exact_source_requirement_reasons": [
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-05-01",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "NAS100_2026-05-03T16:15:00+00:00",
      "decision_time_utc": "2026-05-03T16:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-03",
        "2026-05-04"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-03",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
      "decision_time_utc": "2026-05-04T07:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-03",
        "2026-05-04",
        "2026-05-05"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-04",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "NAS100_2026-05-05T07:15:00+00:00",
      "decision_time_utc": "2026-05-05T07:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-04",
        "2026-05-05",
        "2026-05-06"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-05",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "NAS100_2026-05-06T07:15:00+00:00",
      "decision_time_utc": "2026-05-06T07:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-05",
        "2026-05-06"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-06",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "NAS100_2026-05-07T07:15:00+00:00",
      "decision_time_utc": "2026-05-07T07:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-06"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-07",
      "symbol": "NAS100",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
      "decision_time_utc": "2026-04-14T08:16:00.983581+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=US30_cash/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-14",
      "symbol": "US30_cash",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
      "decision_time_utc": "2026-04-16T13:45:56.810509+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=US30_cash/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-16",
      "symbol": "US30_cash",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
      "decision_time_utc": "2026-04-15T02:45:05.009485+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
      "decision_time_utc": "2026-04-15T13:15:57.398922+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
      "decision_time_utc": "2026-04-16T15:00:05.011292+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-16",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
      "decision_time_utc": "2026-04-21T13:45:05.018194+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-20"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-21",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-21",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
      "decision_time_utc": "2026-04-22T00:30:05.018068+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-22",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
      "decision_time_utc": "2026-04-22T15:15:05.016051+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-22",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
      "decision_time_utc": "2026-04-23T08:45:05.012266+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-23",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-23",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
      "decision_time_utc": "2026-04-24T00:16:10.771453+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-24",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-24",
      "symbol": "USDJPY",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAGUSD_2026-05-01T08:30:00+00:00",
      "decision_time_utc": "2026-05-01T08:30:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-30",
        "2026-05-01"
      ],
      "exact_source_requirement_reasons": [
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-05-01",
      "symbol": "XAGUSD",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "decision_time_utc": "2026-04-15T14:15:05.007998+00:00",
      "embargo_or_contamination_hits": [],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-15",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "decision_time_utc": "2026-04-16T09:30:05.013547+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-16",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "decision_time_utc": "2026-04-16T13:16:01.126537+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-16",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
      "decision_time_utc": "2026-04-17T13:30:05.007149+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-17"
      ],
      "exact_source_requirement_reasons": [
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-04-17",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": false
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAUUSD_2026-05-01T08:15:00+00:00",
      "decision_time_utc": "2026-05-01T08:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-30",
        "2026-05-01"
      ],
      "exact_source_requirement_reasons": [
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-05-01",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "audit_status": "DEFENSIBLE_EXACT_SOURCE_REQUIREMENT",
      "candidate_id": "XAUUSD_2026-05-01T15:45:00+00:00",
      "decision_time_utc": "2026-05-01T15:45:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-04-30",
        "2026-05-01"
      ],
      "exact_source_requirement_reasons": [
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "issues": [],
      "source_date": "2026-05-01",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
      "decision_time_utc": "2026-05-04T07:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-03",
        "2026-05-04",
        "2026-05-05"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-04",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": null
    },
    {
      "admission_status": "REJECTED_ONE_DAY_EMBARGO_OVERLAP",
      "audit_status": "DEFENSIBLE_REJECT_CONTAMINATION_OR_EMBARGO",
      "candidate_id": "XAUUSD_2026-05-05T08:15:00+00:00",
      "decision_time_utc": "2026-05-05T08:15:00+00:00",
      "embargo_or_contamination_hits": [
        "2026-05-04",
        "2026-05-05",
        "2026-05-06"
      ],
      "exact_source_requirement_reasons": [],
      "issues": [],
      "source_date": "2026-05-05",
      "symbol": "XAUUSD",
      "tick_missing_claim_exists_now": null
    }
  ],
  "blocked_candidate_count": 37,
  "candidate_count_considered": 48,
  "changes_live_trading_behavior": false,
  "checks": {
    "all_blocker_reject_reasons_defensible": true,
    "audited_37_blocked_rows": true,
    "audited_9_rejected_rows": true,
    "candidate_count_considered_is_48": true,
    "no_blocked_or_rejected_rows_entered_packet": true,
    "route_level_impossibility_is_exact_source_absent": true,
    "status_counts_match_expected": true
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T05:28:55Z",
  "issues": [],
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
  "rejected_candidate_count": 9,
  "route_level_impossibilities": [
    {
      "exact_requirement": "Owner-approved forward source-capture logger run must create this file before the forward-capture route can admit rows from it.",
      "source_route": "shadow_logs/nofill_forward_source_capture.jsonl",
      "status": "SOURCE_ABSENT"
    }
  ],
  "status_counts": {
    "ADMITTED_SOURCE_PACKET_ROW": 2,
    "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT": 37,
    "REJECTED_ONE_DAY_EMBARGO_OVERLAP": 9
  },
  "validation_safe": false
}
```
