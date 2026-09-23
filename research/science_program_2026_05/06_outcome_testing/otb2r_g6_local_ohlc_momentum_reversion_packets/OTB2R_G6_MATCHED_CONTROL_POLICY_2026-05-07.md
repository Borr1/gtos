# OTB2R G6 Matched Control Policy - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_family": "OTB2R_G6_MATCHED_CONTROL_POLICY",
  "ob_vs_generic_policy": {
    "applies_to_packet_id": "OTG0-PKT-060",
    "independent_generic_control_rows_allowed": false,
    "matched_group_field": "matched_control_group_id",
    "policy": "Do not create standalone generic-control records by copying OB setup rows. Each OB setup may carry one generic 80 percent retrace counterfactual level inside the same record and duplicate group. The countable denominator is the matched setup group, not OB rows plus generic rows.",
    "sample_floor_counting_unit": "unique matched_control_group_id"
  },
  "other_g6_packets": "Opening-drive, exhaustion/changepoint, no-retrace, and gold round-number packets use their own duplicate keys and must not be pooled into the OB-vs-generic denominator.",
  "outcome_review_opened": false,
  "policy_version": "otb2r_g6_matched_control_policy_v1",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}

```
