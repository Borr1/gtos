# G12 OTI5 OTR061 Duplicate Label Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Confirms OTI5 duplicate denominator policy and OTR061 input-only label-family boundary.
- Future OTR061 scoring must reuse the prior OTX duplicate group before any result denominator is opened.

```json
{
  "artifact_family": "G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT",
  "audit_verdict": "PASS_DUPLICATE_AND_LABEL_CONTROLS",
  "generated_at_utc": "2026-05-07T09:59:44Z",
  "label_family_separation_verdict": "PASS_SYNTHETIC_PATH_R_AND_INPUT_ONLY_PACKET_SEPARATED",
  "live_effect": false,
  "oti5_duplicate_denominator": {
    "denominator_policy_verdict": "PASS_DUPLICATE_DENOMINATOR_FROZEN_BEFORE_SCORING",
    "duplicate_group_rows": [
      {
        "duplicate_group_id": "G6_EXHAUSTION|GBPJPY|2026-05-04|tokyo|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|GBPJPY_2026-05-04T02:15:00+00:00",
        "record_count": 3,
        "record_ids": [
          "OTG0-PKT-063|GBPJPY_2026-05-04T02:15:00+00:00",
          "OTG0-PKT-063|GBPJPY_2026-05-04T02:30:00+00:00",
          "OTG0-PKT-063|GBPJPY_2026-05-04T03:00:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|GBPJPY|2026-05-06|london|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|GBPJPY_2026-05-06T07:30:00+00:00",
        "record_count": 2,
        "record_ids": [
          "OTG0-PKT-063|GBPJPY_2026-05-06T07:30:00+00:00",
          "OTG0-PKT-063|GBPJPY_2026-05-06T07:45:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|GBPJPY|2026-05-06|tokyo|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|GBPJPY_2026-05-06T02:30:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|GBPJPY_2026-05-06T02:30:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|NAS100|2026-05-04|london|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|NAS100_2026-05-04T07:15:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-04T07:15:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|NAS100|2026-05-04|london|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|NAS100_2026-05-04T10:30:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-04T10:30:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|NAS100|2026-05-04|ny|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|NAS100_2026-05-04T13:15:00+00:00",
        "record_count": 12,
        "record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-04T13:15:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T13:30:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T14:00:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T14:15:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T14:30:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T15:15:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T15:45:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T16:00:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T16:15:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T16:30:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T16:45:00+00:00",
          "OTG0-PKT-063|NAS100_2026-05-04T17:00:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|NAS100|2026-05-05|london|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|NAS100_2026-05-05T07:15:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-05T07:15:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|NAS100|2026-05-06|london|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|NAS100_2026-05-06T07:15:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-06T07:15:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|US30_cash|2026-05-06|london|LONG|LONG",
        "primary_record_id": "OTG0-PKT-063|US30_cash_2026-05-06T09:15:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|US30_cash_2026-05-06T09:15:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|USDJPY|2026-05-05|tokyo|SHORT|SHORT",
        "primary_record_id": "OTG0-PKT-063|USDJPY_2026-05-05T00:45:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|USDJPY_2026-05-05T00:45:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-04|london|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAGUSD_2026-05-04T07:15:00+00:00",
        "record_count": 14,
        "record_ids": [
          "OTG0-PKT-063|XAGUSD_2026-05-04T07:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T07:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T07:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T08:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T08:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T08:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T08:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T09:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T09:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T09:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T09:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T10:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T10:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T10:30:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-04|ny|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAGUSD_2026-05-04T13:15:00+00:00",
        "record_count": 16,
        "record_ids": [
          "OTG0-PKT-063|XAGUSD_2026-05-04T13:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T13:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T13:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T14:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T14:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T14:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T14:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T15:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T15:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T15:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T15:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T16:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T16:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T16:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T16:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-04T17:00:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-05|london|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAGUSD_2026-05-05T07:30:00+00:00",
        "record_count": 11,
        "record_ids": [
          "OTG0-PKT-063|XAGUSD_2026-05-05T07:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T08:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T08:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T08:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T09:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T09:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T09:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T09:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T10:00:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T10:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T10:30:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-05|ny|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAGUSD_2026-05-05T14:15:00+00:00",
        "record_count": 10,
        "record_ids": [
          "OTG0-PKT-063|XAGUSD_2026-05-05T14:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T14:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T14:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T15:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T15:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T15:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T16:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T16:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T16:45:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-05T17:00:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-06|london|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T07:15:00+00:00",
        "record_count": 3,
        "record_ids": [
          "OTG0-PKT-063|XAGUSD_2026-05-06T07:15:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-06T07:30:00+00:00",
          "OTG0-PKT-063|XAGUSD_2026-05-06T08:45:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAUUSD|2026-05-04|london|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAUUSD_2026-05-04T07:15:00+00:00",
        "record_count": 1,
        "record_ids": [
          "OTG0-PKT-063|XAUUSD_2026-05-04T07:15:00+00:00"
        ]
      },
      {
        "duplicate_group_id": "G6_EXHAUSTION|XAUUSD|2026-05-05|london|SHORT|LONG",
        "primary_record_id": "OTG0-PKT-063|XAUUSD_2026-05-05T08:00:00+00:00",
        "record_count": 2,
        "record_ids": [
          "OTG0-PKT-063|XAUUSD_2026-05-05T08:00:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-05T08:15:00+00:00"
        ]
      }
    ],
    "duplicate_primary_selection_rule": "Sort by decision_asof_utc, then record_id; keep rank 1 as countable primary.",
    "nonprimary_duplicate_rows": 64,
    "primary_rows_observed": 17,
    "raw_source_ready_rows": 81,
    "raw_total_packet_rows": 86,
    "unique_duplicate_group_count": 17
  },
  "oti5_label_family": {
    "allowed_result_key_policy": "synthetic_r appears only in OTI5 quarantined result rows after gates pass and is not validation evidence.",
    "blocked_packet_outcomes_opened": false,
    "broker_actual_r_opened": false,
    "input_label_family_counts": {
      "original_packet": {
        "input_only_features_no_labels": 86
      },
      "proposal_rows": {
        "input_only_features_no_labels": 86
      }
    },
    "result_label_family": "synthetic_path_r_quarantined_discovery_only"
  },
  "otr061_duplicate_and_label": {
    "future_result_lane_duplicate_requirement": "Use prior_otx_input_record_for_traceability.duplicate_group_id before scoring; do not infer a denominator from the recovered tick file alone.",
    "label_family": "input_only_features_no_labels",
    "no_result_fields_assertion": true,
    "prior_otx_duplicate_group_id": "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52",
    "record_count": 1,
    "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
  },
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
