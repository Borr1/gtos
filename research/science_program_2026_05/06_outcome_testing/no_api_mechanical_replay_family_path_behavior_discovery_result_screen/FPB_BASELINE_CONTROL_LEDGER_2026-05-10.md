# Baseline Control Ledger

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "all_four_baseline_controls_included": true,
  "artifact_family": "baseline_control_ledger",
  "baseline_control_families": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "baseline_rows": [
    {
      "candidate_denominator": 159883,
      "control_role": "adversarial time/session placebo comparator",
      "distribution": {
        "ambiguity_unresolved_count": 4100,
        "counts": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 55491,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 100292,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 3822,
          "UNRESOLVED_AT_SOURCE_END": 2,
          "UNRESOLVED_BY_WINDOW": 276
        },
        "proportions": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.34707255,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.6272837,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 0.02390498,
          "UNRESOLVED_AT_SOURCE_END": 1.251e-05,
          "UNRESOLVED_BY_WINDOW": 0.00172626
        }
      },
      "family_id": "baseline_random_session_control",
      "use_boundary": "Comparator for discovery path-behavior only; not a strategy result and not a promotion baseline."
    },
    {
      "candidate_denominator": 2543496,
      "control_role": "delayed-entry control for source-safe level/path timing",
      "distribution": {
        "ambiguity_unresolved_count": 166991,
        "counts": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1095593,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1280912,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 110965,
          "UNRESOLVED_AT_SOURCE_END": 140,
          "UNRESOLVED_BY_WINDOW": 55886
        },
        "proportions": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.43074296,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.50360292,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 0.04362696,
          "UNRESOLVED_AT_SOURCE_END": 5.504e-05,
          "UNRESOLVED_BY_WINDOW": 0.02197212
        }
      },
      "family_id": "baseline_shifted_entry_control",
      "use_boundary": "Comparator for discovery path-behavior only; not a strategy result and not a promotion baseline."
    },
    {
      "candidate_denominator": 1965307,
      "control_role": "simple continuation comparator",
      "distribution": {
        "ambiguity_unresolved_count": 31979,
        "counts": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 615758,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1317570,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 29975,
          "UNRESOLVED_AT_SOURCE_END": 64,
          "UNRESOLVED_BY_WINDOW": 1940
        },
        "proportions": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.3133139,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.67041434,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 0.01525207,
          "UNRESOLVED_AT_SOURCE_END": 3.256e-05,
          "UNRESOLVED_BY_WINDOW": 0.00098712
        }
      },
      "family_id": "baseline_momentum_continuation",
      "use_boundary": "Comparator for discovery path-behavior only; not a strategy result and not a promotion baseline."
    },
    {
      "candidate_denominator": 1081043,
      "control_role": "simple reversion comparator",
      "distribution": {
        "ambiguity_unresolved_count": 104249,
        "counts": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 203088,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 773706,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 103828,
          "UNRESOLVED_AT_SOURCE_END": 32,
          "UNRESOLVED_BY_WINDOW": 389
        },
        "proportions": {
          "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
          "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.18786302,
          "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
          "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.71570326,
          "SAME_BAR_CONTEXT_AMBIGUOUS": 0.09604428,
          "UNRESOLVED_AT_SOURCE_END": 2.96e-05,
          "UNRESOLVED_BY_WINDOW": 0.00035984
        }
      },
      "family_id": "baseline_mean_reversion",
      "use_boundary": "Comparator for discovery path-behavior only; not a strategy result and not a promotion baseline."
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "generated_at_utc": "2026-05-11T04:20:56+00:00",
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
  "policy": "Baselines are adversarial controls that can expose path-label prevalence artifacts. They are not throwaways and are not performance comparators.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "validation_safe": false
}
```
