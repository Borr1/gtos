# G12 G3 G6 Same Bar Timing Review 2026-05-07 - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `False`
Outcome review opened: `False`

```json
{
  "artifact_family": "G12_G3_G6_SAME_BAR_TIMING_REVIEW",
  "outcome_review_opened": false,
  "packet_rows": [
    {
      "packet_id": "OTG0-PKT-031",
      "policy_counts": {
        "G3_INPUT_ONLY_CLOSED_CANDLE_POLICY_V1": 95
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "NOT_APPLICABLE_INPUT_ONLY_NO_TERMINAL_ORDER_CLAIM": 95
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-032",
      "policy_counts": {
        "G3_INPUT_ONLY_CLOSED_CANDLE_POLICY_V1": 8
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "NOT_APPLICABLE_INPUT_ONLY_NO_TERMINAL_ORDER_CLAIM": 8
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-036",
      "policy_counts": {
        "G3_INPUT_ONLY_CLOSED_CANDLE_POLICY_V1": 96
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "NOT_APPLICABLE_INPUT_ONLY_NO_TERMINAL_ORDER_CLAIM": 96
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-060",
      "policy_counts": {
        "LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED": 74,
        "M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED": 6
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "same_m1_ambiguity_flagged": 4,
        "terminal_order_unclaimed": 76
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-061",
      "policy_counts": {
        "not_applicable_or_missing": 51
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "not_applicable_or_missing": 51
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-062",
      "policy_counts": {
        "LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED": 77,
        "M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED": 9
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "same_m1_ambiguity_flagged": 6,
        "terminal_order_unclaimed": 80
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-063",
      "policy_counts": {
        "LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED": 77,
        "M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED": 9
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "same_m1_ambiguity_flagged": 6,
        "terminal_order_unclaimed": 80
      },
      "terminal_order_claim_allowed": false
    },
    {
      "packet_id": "OTG0-PKT-066",
      "policy_counts": {
        "LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED": 5,
        "M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED": 2
      },
      "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
      "state_counts": {
        "same_m1_ambiguity_flagged": 1,
        "terminal_order_unclaimed": 6
      },
      "terminal_order_claim_allowed": false
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "red_team_finding": "Packets may carry path windows but cannot claim entry/SL/TP/continuation/reversal terminal order. Same-minute ambiguity remains bounded or unclaimed.",
  "source_policy_refs": [
    "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_SAME_BAR_POLICY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_SAME_BAR_TIMING_POLICY_2026-05-07.json"
  ],
  "validation_safe": false
}
```
