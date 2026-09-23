# Selection Bias Multiple Testing Ledger

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "abandoned_or_excluded_branches": [
    {
      "branch": "native_depth_order_book_absorption",
      "reason": "requires Sierra depth parser/source contract before joining replay denominators",
      "status": "excluded_from_result_screen"
    },
    {
      "branch": "mt5_bid_ask_tick_spread_sensitive_entries",
      "reason": "requires MT5 bid/ask/flags quote source packet; spread/cost scoring is forbidden here",
      "status": "excluded_from_result_screen"
    },
    {
      "branch": "production_ai_intent_replay",
      "reason": "requires source-logged prompt/input/output/gate/lifecycle truth and would cross evidence class",
      "status": "excluded_from_result_screen"
    }
  ],
  "artifact_family": "selection_bias_multiple_testing_ledger",
  "baseline_controls_frozen_before_result_screen": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "changes_live_trading_behavior": false,
  "compact_cap_policy": "Compact sample rows are not decisive ranking evidence; full aggregate matrix is decisive for this route's inspection-priority ledger.",
  "credentials_touched": false,
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "family_choices_frozen_before_result_screen": [
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "opening_drive_no_fill_lifecycle",
    "session_kz_sweep",
    "liquidity_stop_run_context",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
    "adjacent_range_compression_breakout"
  ],
  "g0_rank_1_route": "research/science_program_2026_05/04_goal_prompts/NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN_GOAL_PROMPT_2026-05-10.md",
  "g0_ranking_criteria_inherited": [
    "source safety",
    "denominator quality",
    "ambiguity burden",
    "baseline-control usefulness",
    "science-horizon value",
    "downstream readiness",
    "selection-bias risk",
    "compact-cap limitations",
    "mandatory follow-on audit gates"
  ],
  "generated_at_utc": "2026-05-11T04:20:56+00:00",
  "live_effect": false,
  "multiple_testing_debt": {
    "label_count": 7,
    "opened_family_count": 11,
    "post_hoc_thresholds_created": false,
    "promotion_permitted": false,
    "selection_not_validation": true,
    "slice_dimensions_reported": [
      "source_family",
      "symbol",
      "timeframe",
      "session_or_kill_zone",
      "regime_phase",
      "side"
    ]
  },
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
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "route_priority_not_performance": [
    {
      "ambiguity_unresolved_rate": 0.0621729,
      "baseline_distribution_js_divergence": 0.15904391,
      "candidate_denominator": 542262,
      "family_id": "adjacent_range_compression_breakout",
      "inspection_priority_score_not_performance": 23.060193,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 1
    },
    {
      "ambiguity_unresolved_rate": 0.01298558,
      "baseline_distribution_js_divergence": 0.0161661,
      "candidate_denominator": 3165357,
      "family_id": "liquidity_stop_run_context",
      "inspection_priority_score_not_performance": 21.999089,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 2
    },
    {
      "ambiguity_unresolved_rate": 0.02935034,
      "baseline_distribution_js_divergence": 0.02837154,
      "candidate_denominator": 1553202,
      "family_id": "ob_retest",
      "inspection_priority_score_not_performance": 21.612181,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 3
    },
    {
      "ambiguity_unresolved_rate": 0.09643372,
      "baseline_distribution_js_divergence": 0.03148052,
      "candidate_denominator": 1081043,
      "family_id": "baseline_mean_reversion",
      "inspection_priority_score_not_performance": 21.530428,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 4
    },
    {
      "ambiguity_unresolved_rate": 0.04632562,
      "baseline_distribution_js_divergence": 0.9550197,
      "candidate_denominator": 147780,
      "family_id": "opening_drive_no_fill_lifecycle",
      "inspection_priority_score_not_performance": 21.458852,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 5
    },
    {
      "ambiguity_unresolved_rate": 0.17178003,
      "baseline_distribution_js_divergence": 0.03075115,
      "candidate_denominator": 1532652,
      "family_id": "fvg_fill",
      "inspection_priority_score_not_performance": 20.622446,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 6
    },
    {
      "ambiguity_unresolved_rate": 0.06565412,
      "baseline_distribution_js_divergence": 0.00851365,
      "candidate_denominator": 2543496,
      "family_id": "baseline_shifted_entry_control",
      "inspection_priority_score_not_performance": 20.02036,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 7
    },
    {
      "ambiguity_unresolved_rate": 0.01627176,
      "baseline_distribution_js_divergence": 0.00992963,
      "candidate_denominator": 1965307,
      "family_id": "baseline_momentum_continuation",
      "inspection_priority_score_not_performance": 19.832679,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 8
    },
    {
      "ambiguity_unresolved_rate": 0.03457779,
      "baseline_distribution_js_divergence": 0.01681024,
      "candidate_denominator": 141507,
      "family_id": "session_kz_sweep",
      "inspection_priority_score_not_performance": 14.897141,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 9
    },
    {
      "ambiguity_unresolved_rate": 0.02564375,
      "baseline_distribution_js_divergence": 0.00460732,
      "candidate_denominator": 159883,
      "family_id": "baseline_random_session_control",
      "inspection_priority_score_not_performance": 13.664295,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 10
    },
    {
      "ambiguity_unresolved_rate": 0.03423948,
      "baseline_distribution_js_divergence": 0.01351858,
      "candidate_denominator": 20269,
      "family_id": "breaker_re_entry",
      "inspection_priority_score_not_performance": 13.073167,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 11
    }
  ],
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "this_route_ranking_criteria": [
    "full-population path-behavior distribution contrast versus combined baseline controls",
    "full-population denominator coverage",
    "full-population ambiguity/unresolved burden",
    "source/symbol/timeframe/session/regime concentration diagnostics"
  ],
  "validation_safe": false
}
```
