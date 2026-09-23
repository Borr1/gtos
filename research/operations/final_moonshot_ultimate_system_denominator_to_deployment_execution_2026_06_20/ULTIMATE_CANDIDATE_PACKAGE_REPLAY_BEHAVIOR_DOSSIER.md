# Ultimate Candidate Package Replay Behavior Dossier

Status: proxy package selected for local replay and implementation drafting; broker-live activation closed.

## Verdict

- Simulated executed trade ledger: `0` filled replay rows, net `0` R, final `0` R, gross `0` R, simulated cash PnL `0`, risk cash `0`, wins/losses/flats by net R `{'win_rows': 0, 'loss_rows': 0, 'flat_rows': 0, 'missing_rows': 0}`.
- Package scorecard layer: `1213` decision-window rows, `0` package R rows, package result `0.0` R, paired package-vs-baseline delta `0` R, missed-fill opportunity cost `0.0` R.
- Reconstructed proxy layer: `6374` proxy rows, `3710` scoreable, raw proxy result `-731.800345701` R, guarded proxy result `864.499654299` R, raw negative rows `94`, guarded negative rows `0`.

The actual simulated fill ledger is nonnegative after replay loss-bucket repair. The raw reconstructed proxy denominator remains separate from the guarded proxy surface, and the guarded policy makes the proxy surface nonnegative by skip/reduce/delay behavior. This is replay/proxy evidence, not broker-real expectancy.

## Executed Replay Trades

- Trade rows: `0`
- Date range: `None` to `None` across `0` trade days
- Trades per trade day: `0.0`
- Net R / final R / gross R: `0` / `0` / `0`
- Net proxy R: `0`
- Simulated cash PnL / risk cash / risk percent sum: `0` / `0` / `0`
- Average risk percent: `None`
- Expected cost R sum: `0`
- Net R outcomes: `{'win_rows': 0, 'loss_rows': 0, 'flat_rows': 0, 'missing_rows': 0}`
- Final R outcomes: `{'win_rows': 0, 'loss_rows': 0, 'flat_rows': 0, 'missing_rows': 0}`

Every executed simulated fill is normalized in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_REPLAY_BEHAVIOR_TRADE_LEDGER.jsonl`. Aggregates by symbol, day, side, session, source, order type, action, terminal outcome, and close reason are in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_REPLAY_BEHAVIOR_BUCKET_LEDGER.jsonl`.

## Selection And Action Behavior

- Candidate rows: `59074`
- Selected candidate rows: `0`
- Order-policy rows: `1213`
- Simulated order-decision rows / decisions: `626` / `626`
- Delayed/queued scorecard rows: `626`
- Skipped scorecard rows: `580`
- Held scorecard rows: `7`
- Scorecard action counts: `{"replay_delay_queue_limit_first": 626, "replay_hold_source_required": 7, "replay_skip_or_reject": 580}`
- Scorecard order-type counts: `{"limit_first_delay_queue": 626, "skip": 587}`

## Order-Policy Materialization

- Decision ledger rows: `1213`
- Intended order rows: `626`
- Policy skip rows: `587`
- Source candidate joined / missing: `626` / `0`
- Broker-cost refused or not passed rows: `276`
- Broker-cost passed rows: `350`
- Materialization status counts: `{"broker_cost_authority_refused_or_not_passed": 276, "policy_skip_no_order_attempt": 587, "source_joined_cost_passed_pending_live_as_if_order_materialization": 350}`
- Cost status counts: `{"PASSED": 350, "REFUSED": 276, "__missing__": 587}`
- Order and oracle rows: `626` / `626`
- Decision ledger: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_REPLAY_BEHAVIOR_DECISION_LEDGER.jsonl`
- Order ledger: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_REPLAY_BEHAVIOR_ORDER_LEDGER.jsonl`
- Ordered-path oracle ledger: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_REPLAY_BEHAVIOR_ORDERED_PATH_ORACLE_LEDGER.jsonl`

These rows are local replay classifications only. They do not place broker orders and keep final/live authority closed.

## Missing Or Reconstructed R

- Exact historical denominator joins: `0` / `877`
- Exact historical denominator missing rows: `877`
- Scorecard package-result missing rows: `1213`
- Scorecard baseline-result missing rows: `1213`
- Scorecard package-vs-baseline delta missing rows: `1213`
- Reconstructed proxy unscoreable rows: `2664`
- Broker actual-R joined rows / close-cost joined rows / remaining close-history rows: `1` / `1` / `8`
- Cash PnL boundary: `pnl_cash and risk_cash are simulated account replay fields, not broker-real realized cash`

## Raw Vs Guarded Robustness

- Replay-authority stress raw negative rows / guarded negative rows: `94` / `0`
- Replay-authority min raw stressed delta / guarded min stressed delta: `-62.6` / `0.0`
- Replay-authority MC raw positive pass rate / guarded nonnegative pass rate: `None` / `None`
- Reconstructed proxy stress raw negative rows / guarded negative rows: `7` / `0`
- Reconstructed proxy stress raw sum / guarded sum: `-5679.102419907` / `3276.048617196`
- Reconstructed proxy MC raw positive trials / raw negative trials / guarded negative trials: `256` / `0` / `0`
- Guarded policy interpretation: `guarded_policy_makes_proxy_surface_non_negative_by_skipping_reducing_or_delaying_negative_paths`

## Authority Boundary

	- Final package selected under proxy authority: `false`
- Live trading enabled: `false`
- Live execution activation allowed: `false`
- Broker mutation allowed: `false`
- Order calls: `0`
