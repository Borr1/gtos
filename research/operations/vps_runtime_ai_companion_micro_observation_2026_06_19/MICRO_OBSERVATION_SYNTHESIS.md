# VPS Runtime AI Companion Micro Observation

Started: `2026-06-19T08:07:34.906339Z`
Ended: `2026-06-19T09:07:35.590166Z`
Samples: `61`
Runtime effect boundary: `read_only_log_pipeline_state_parse_no_broker_mutation_no_order_action_no_runtime_reload`
OK: `True`

## Latest Stability

- Packet rows in window: `220`; parse errors: `0`; validation issues: `0`.
- Launcher rows in window: `8`; placed count: `0`; skipped reasons: `{'already_placed_today': 2, 'cost_screen_spread_r:0.105>0.100 (spread 0.0001 vs asian_fade stop 0.0007)': 2, 'profile_missing_instrument_config': 29}`.
- Execution Manager rows in window: `0`; fatal reasons: `{}`.
- Trade records: `16` total, `3` nonclosed; joinability: `{'ticket_candidate_decision_policy_joinable': 13, 'ticket_policy_joinable': 3}`.
- Placement ledgers: `13` rows, incomplete ticket rows: `0`.

## Observed Intelligence Themes

- `AI-BROKER-SYMBOL-MAP-HYGIENE` observed in `53` samples.
- `AI-LEGACY-ATTRIBUTION-BOUNDARY` observed in `60` samples.
- `AI-NO-CANDIDATE-STATE-EXPLANATION` observed in `53` samples.
- `AI-RISK-GOVERNOR-AWARENESS` observed in `53` samples.

## AI Companion Recommendations

- `high` `AI_COMPANION_SELECTION_STATE_DIGEST`: Build a read-only companion digest that explains every cycle as no-candidate, candidate-rejected, cost-blocked, admitted, placed, managed, or closed, with the causal reason and evidence path.
- `high` `AI_COMPANION_COST_AND_SWAP_CONTEXT`: Have the companion review cost/swap/spread blocks as research signals and produce symbol/session thresholds for later replay, without overriding Execution Manager V4.
- `medium` `AI_COMPANION_RISK_GOVERNOR_CONTEXT`: Surface when selection is being shaped by drawdown-wall derisking so low activity is not misread as lack of market opportunity.
- `medium` `AI_COMPANION_BROKER_PROFILE_QUEUE`: Queue repeated unsupported-symbol or missing-profile candidates into a broker-profile/source-validation lane.
- `medium` `AI_COMPANION_BROKER_REAL_LEARNING_QUEUE`: Transform reconciled lifecycle/fill/cost packets into forward-learning tasks for entry quality, time-stop behavior, and opportunity cost.

## Residual Issues

- No high-severity read-only observation issues were classified.
