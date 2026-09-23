# Failure Anatomy Next Hypothesis Ledger

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "artifact_family": "failure_anatomy_next_hypothesis_ledger",
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
  "policy": "Negative or surprising path-behavior patterns become future preregistered hypotheses or source-control questions, not post-hoc validation claims.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "rows": [
    {
      "candidate_denominator": 1553202,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.02935034,
        "continuation_context_touch_rate": 0.52227205,
        "protective_boundary_context_touch_rate": 0.44837761
      },
      "failure_or_artifact_questions": [
        "continuation-context touches are more common than protective-boundary context touches in this discovery ledger"
      ],
      "family_id": "ob_retest",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 1532652,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.17178003,
        "continuation_context_touch_rate": 0.28277195,
        "protective_boundary_context_touch_rate": 0.54544802
      },
      "failure_or_artifact_questions": [
        "high ambiguity/unresolved burden; future source/control work should inspect same-bar and window limits",
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "fvg_fill",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 20269,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.03423948,
        "continuation_context_touch_rate": 0.46795599,
        "protective_boundary_context_touch_rate": 0.49780453
      },
      "failure_or_artifact_questions": [
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "breaker_re_entry",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 147780,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.04632562,
        "continuation_context_touch_rate": 0.0,
        "protective_boundary_context_touch_rate": 0.0
      },
      "failure_or_artifact_questions": [
        "uses midpoint/extension lifecycle labels, so do not compare label names directly to continuation/protective families"
      ],
      "family_id": "opening_drive_no_fill_lifecycle",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 141507,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.03457779,
        "continuation_context_touch_rate": 0.45409768,
        "protective_boundary_context_touch_rate": 0.51132453
      },
      "failure_or_artifact_questions": [
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "session_kz_sweep",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 3165357,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.01298558,
        "continuation_context_touch_rate": 0.44330166,
        "protective_boundary_context_touch_rate": 0.54371276
      },
      "failure_or_artifact_questions": [
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "liquidity_stop_run_context",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 159883,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.02564375,
        "continuation_context_touch_rate": 0.34707255,
        "protective_boundary_context_touch_rate": 0.6272837
      },
      "failure_or_artifact_questions": [
        "baseline/control family; use to test whether path-label prevalence is generic market behavior",
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "baseline_random_session_control",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 2543496,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.06565412,
        "continuation_context_touch_rate": 0.43074296,
        "protective_boundary_context_touch_rate": 0.50360292
      },
      "failure_or_artifact_questions": [
        "baseline/control family; use to test whether path-label prevalence is generic market behavior",
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "baseline_shifted_entry_control",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 1965307,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.01627176,
        "continuation_context_touch_rate": 0.3133139,
        "protective_boundary_context_touch_rate": 0.67041434
      },
      "failure_or_artifact_questions": [
        "baseline/control family; use to test whether path-label prevalence is generic market behavior",
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "baseline_momentum_continuation",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 1081043,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.09643372,
        "continuation_context_touch_rate": 0.18786302,
        "protective_boundary_context_touch_rate": 0.71570326
      },
      "failure_or_artifact_questions": [
        "baseline/control family; use to test whether path-label prevalence is generic market behavior",
        "protective-boundary context touches are more common than continuation-context touches in this discovery ledger"
      ],
      "family_id": "baseline_mean_reversion",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    },
    {
      "candidate_denominator": 542262,
      "discovery_path_behavior_summary": {
        "ambiguity_unresolved_rate": 0.0621729,
        "continuation_context_touch_rate": 0.73177173,
        "protective_boundary_context_touch_rate": 0.20605538
      },
      "failure_or_artifact_questions": [
        "continuation-context touches are more common than protective-boundary context touches in this discovery ledger"
      ],
      "family_id": "adjacent_range_compression_breakout",
      "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
      "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened."
    }
  ],
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "validation_safe": false
}
```
