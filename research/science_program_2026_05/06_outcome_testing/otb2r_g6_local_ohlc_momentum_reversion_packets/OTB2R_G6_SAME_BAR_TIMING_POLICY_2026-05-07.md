# OTB2R G6 Same-Bar Timing Policy - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_family": "OTB2R_G6_SAME_BAR_TIMING_POLICY",
  "outcome_review_opened": false,
  "policy": "Input packets may define path_start_utc/path_end_utc label windows, but they do not claim whether entry, stop, target, continuation, or reversal happened first. M1/OHLC timing metadata is source context only until a separate outcome lane opens.",
  "policy_version": "otb2r_g6_same_bar_timing_policy_v1",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "same_bar_policy_counts": {
    "LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED": 233,
    "M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED": 26,
    "not_applicable_forward_packet": 51
  },
  "same_bar_state_counts": {
    "not_applicable_forward_packet": 51,
    "same_m1_ambiguity_flagged": 17,
    "terminal_order_unclaimed": 242
  },
  "terminal_order_claim_allowed": false,
  "validation_safe": false
}

```
