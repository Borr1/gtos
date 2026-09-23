# G12 CNR061 Sidecar Reaudit Decision Ledger - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- `decision`: `ACCEPT_AS_INPUT_ONLY_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT`
- `accepted_sidecar_row_count`: `8`
- `blocked_rows_excluded`: `94`

```json
{
  "accepted_sidecar_row_count": 8,
  "accepted_unique_duplicate_group_count": 2,
  "accepted_unique_record_id_count": 4,
  "artifact_family": "G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER",
  "blocked_rows_excluded": 94,
  "decision": "ACCEPT_AS_INPUT_ONLY_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
  "decision_scope": "G12 input-only packet-readiness audit; not a result lane and not validation-safe",
  "generated_at_utc": "2026-05-08T04:41:16Z",
  "live_effect": false,
  "no_outcome_scoring_or_post_hoc_rescue": true,
  "non_promotion_boundary": "This acceptance means only that the 8 rows are eligible input packets for a future quarantined result lane. It does not validate CNR061, does not score outcomes, and has no live effect.",
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "row_decisions": [
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "sidecar_row_sha256": "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "sidecar_row_sha256": "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "sidecar_row_sha256": "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "sidecar_row_sha256": "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "sidecar_row_sha256": "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "sidecar_row_sha256": "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "sidecar_row_sha256": "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "future_constraints": [
        "future quarantined result lane only",
        "freeze duplicate denominator policy before outcome review",
        "do not treat duplicate group as sufficient row join",
        "preserve NO_PROMOTION_VERDICT and validation_safe=false"
      ],
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "sidecar_row_sha256": "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "target_model_family": "CNR_T0_ORIGINAL_TP1",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    }
  ],
  "schema_version": "g12_cnr061_sidecar_reaudit_v1",
  "validation_safe": false
}
```
