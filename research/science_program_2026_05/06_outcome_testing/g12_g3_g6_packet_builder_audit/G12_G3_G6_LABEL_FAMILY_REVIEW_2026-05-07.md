# G12 G3 G6 Label Family Review 2026-05-07 - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `False`
Outcome review opened: `False`

```json
{
  "artifact_family": "G12_G3_G6_LABEL_FAMILY_REVIEW",
  "outcome_review_opened": false,
  "packet_rows": [
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "EXP-G3-DC-OVERSHOOT-002",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "synthetic_path_r": 95
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-031",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "EXP-G3-DC-SWING-001",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "synthetic_path_r": 8
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-032",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "EXP-G3-TDA-007",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "synthetic_path_r": 96
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-036",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "input_only_features_no_labels": 80
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-060",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "lifecycle_no_fill",
      "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "input_only_features_no_labels": 51
      },
      "otg0_label_family": "lifecycle_no_fill",
      "packet_id": "OTG0-PKT-061",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "input_only_features_no_labels": 86
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-062",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "input_only_features_no_labels": 86
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-063",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    },
    {
      "broker_path_lifecycle_pooling_allowed": false,
      "declared_future_label_family": "synthetic_path_r",
      "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
      "label_values_absent": true,
      "materialized_record_label_family_counts": {
        "input_only_features_no_labels": 7
      },
      "otg0_label_family": "synthetic_path_r",
      "packet_id": "OTG0-PKT-066",
      "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators."
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "red_team_finding": "G3 declares synthetic_path_r for future use but writes no label values. G6 writes input_only_features_no_labels and declares the future family separately; OTG0-PKT-061 is lifecycle/no-fill, not synthetic path-R.",
  "validation_safe": false
}
```
