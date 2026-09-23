# vNext Moonshot Stage09 ML Dynamic Label Dataset Spec

Generated: `2026-05-26T06:43:59Z`

## Scope

- Dataset source: Stage06 as-of market-awareness feature rows joined to Stage04 corrected dynamic policy replay rows.
- ML role: research/shadow only until sealed validation and production-change approval.
- Paid API/vendor calls: `0`.
- Fixed 1.5R labels are retained only as comparator labels, not activation truth.

## Feature Columns

All feature columns are as-of market/context fields:

- `symbol`
- `transfer_group`
- `framework`
- `side`
- `session_bucket`
- `kill_zone_position`
- `session_subwindow`
- `weekday`
- `month`
- `quarter`
- `source_mode`
- `source_window_complete`
- `source_path_feature_status`
- `trend_state_20`
- `volatility_state_14_vs_50`
- `compression_expansion_state`
- `liquidity_sweep_proxy_state`
- `news_calendar_coverage_status`
- `news_high_impact_within_120m`
- `current_bar_direction`
- `asof_lookback_bars_available`
- `atr14_price`
- `atr50_price`
- `current_bar_displacement_atr14`
- `current_bar_speed_atr14`
- `entry_delay_bars`
- `lookback50_position`
- `return_1_bar`
- `return_4_bar`
- `return_16_bar`
- `trend_score_20_atr50`

## Label Families

- Dynamic R: `label_dynamic_r_live_current`, `label_dynamic_positive`.
- Stop-first risk: `label_stop_first_risk` from corrected live-current dynamic replay exit reason/R.
- No-fill risk: `label_no_fill_risk`, `label_no_fill_risk_binary` from pending lifecycle where matched, otherwise Stage06 fillability status.
- Candidate-origin family: `label_candidate_origin_family` from current framework origin.
- Prop-attempt success: `label_prop_attempt_success_proxy` from Stage07 best-stream branch membership; marked proxy, not row-terminal truth.
- Source-completeness: `label_source_completeness`, `label_source_complete_binary`.
- AI-call need: `label_ai_call_need`, `label_ai_call_need_binary` using Stage08 budget strata logic.
- Execution-policy recommendation: `label_execution_policy_recommendation` from highest corrected Stage04 policy final R.

## Splits

- Time: train `<=2024`, test `2025`, holdout `2026`.
- Symbol holdout: live-fleet symbols versus non-live-fleet symbols.
- Session holdout: NY broad session versus non-NY broad sessions.

## Leakage Guard

Outcome fields are label-only and are not present in `feature_columns`. See leakage audit ledger for field-level checks.

## Row Counts

- Feature ledger rows: `214536`
- Policy rows joined: `214536`
- No-fill rows matched: `214536`
