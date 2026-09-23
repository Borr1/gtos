# G12 Otx G6 Duplicate Denominator Audit

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "accepted_future_subset_policy": {
    "OTG0-PKT-063": {
      "excluded_record_ids": [
        "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00"
      ],
      "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
      "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
      "required_status": "PREREGISTERED_TICK_CUSUM_FEATURE_READY",
      "source_ready_rows": 81
    },
    "OTG0-PKT-066": {
      "accepted_record_ids": [
        "OTG0-PKT-066|XAUUSD_2026-05-04T07:15:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-05T08:00:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-05T08:15:00+00:00"
      ],
      "excluded_record_ids": [
        "OTG0-PKT-066|XAUUSD_2026-05-03T16:15:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-03T16:30:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-06T07:15:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-06T08:00:00+00:00"
      ],
      "required_feature_asof_lte_decision": true,
      "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
      "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
      "required_sweep_status": "STRUCTURED_SWEEP_FIELDS_READY",
      "sample_floor": 150,
      "source_ready_rows": 3
    }
  },
  "artifact_family": "G12_OTX_G6_DUPLICATE_DENOMINATOR_AUDIT",
  "denominator_policy_verdict": "PASS_NO_RAW_RECORD_DENOMINATOR_ACCEPTED_AS_VALIDATION",
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "live_effect": false,
  "oti4b_countable_discovery_rows": 9,
  "oti4b_countable_duplicate_keys": [
    "G6_OPENING_DRIVE_TICK|GBPJPY|london|2026-05-06T07:00:00Z|2026-05-06T07:30:00Z|UP",
    "G6_OPENING_DRIVE_TICK|GBPJPY|tokyo|2026-05-04T00:00:00Z|2026-05-04T00:30:00Z|UP",
    "G6_OPENING_DRIVE_TICK|GBPJPY|tokyo|2026-05-06T00:00:00Z|2026-05-06T00:30:00Z|UP",
    "G6_OPENING_DRIVE_TICK|NAS100|london|2026-05-04T07:00:00Z|2026-05-04T07:30:00Z|DOWN",
    "G6_OPENING_DRIVE_TICK|NAS100|ny|2026-05-04T13:00:00Z|2026-05-04T13:30:00Z|UP",
    "G6_OPENING_DRIVE_TICK|US30_cash|london|2026-05-06T07:00:00Z|2026-05-06T07:30:00Z|UP",
    "G6_OPENING_DRIVE_TICK|XAGUSD|london|2026-05-04T07:00:00Z|2026-05-04T07:30:00Z|DOWN",
    "G6_OPENING_DRIVE_TICK|XAGUSD|ny|2026-05-04T13:00:00Z|2026-05-04T13:30:00Z|DOWN",
    "G6_OPENING_DRIVE_TICK|XAGUSD|ny|2026-05-05T13:00:00Z|2026-05-05T13:30:00Z|DOWN"
  ],
  "oti4b_result_duplicate_status_counts": {
    "COUNTABLE_PRIMARY_UNIQUE_BREAKOUT": 31,
    "DUPLICATE_BREAKOUT_GROUP_NOT_COUNTABLE": 55
  },
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proposal_duplicate_summary_by_packet": {
    "OTG0-PKT-060": {
      "max_records_per_duplicate_group": 16,
      "raw_over_unique_ratio": 4.0,
      "record_count": 80,
      "unique_duplicate_group_count": 20
    },
    "OTG0-PKT-061": {
      "max_records_per_duplicate_group": 16,
      "raw_over_unique_ratio": 6.375,
      "record_count": 51,
      "unique_duplicate_group_count": 8
    },
    "OTG0-PKT-062": {
      "max_records_per_duplicate_group": 16,
      "raw_over_unique_ratio": 4.526316,
      "record_count": 86,
      "unique_duplicate_group_count": 19
    },
    "OTG0-PKT-063": {
      "max_records_per_duplicate_group": 16,
      "raw_over_unique_ratio": 4.095238,
      "record_count": 86,
      "unique_duplicate_group_count": 21
    },
    "OTG0-PKT-066": {
      "max_records_per_duplicate_group": 2,
      "raw_over_unique_ratio": 1.166667,
      "record_count": 7,
      "unique_duplicate_group_count": 6
    }
  },
  "validation_safe": false
}
```
