# Friday Microscope Final Report

Generated: 2026-05-31T11:01:22.408056+00:00
HEAD at generation: `1e745b447133b90a8abbabeaa4224ed7bdddb18d`
Route id: `vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31`

## Scope And Freeze

The clean primary freeze starts at `2026-05-28T23:45:00+00:00` and ends before `2026-05-29T21:00:00+00:00`. The boundary rule is: include non-crypto rows with timestamp_basis_utc >= first placed candidate candle and < 2026-05-29T21:00:00Z; exclude exactly-21:00 spread-close batch from primary denominator and preserve it as close-spread evidence.

Primary non-crypto rows: `328`. The exact `2026-05-29T21:00:00Z` close-spread batch is excluded from the primary denominator and preserved as close evidence: `32` rows, all `spread_too_wide`. BTCUSD/ETHUSD are excluded from the primary execution-era denominator because they had different market-hours behavior and no placed trades in this slice; appendix rows: `66` (`BTCUSD=30`, `ETHUSD=36`).

## Denominators

- Raw generated Friday candidates: `328`.
- Current full moonshot selected-or-bridge candidates: `328`.
- Selected-cell risk present: `9`.
- Broker geometry pass: `328`.
- Spread/cost pass: `325`.
- Prop exposure pass: `283`.
- Broker-placement ready: `9`.
- Actually placed: `8`.
- Broker truth rows reconciled through Friday close: `8`.
- Broad selected replay scanned for quality-selector context: `289600` selected rows.

The raw weekend tournament remains diagnostic only. The clean reconciliation status counts are `{"selected_current_no_trade_or_dynamic_refusal": 1, "selected_or_raw_bridge_missing_selected_cell_risk": 274, "selected_risk_broker_ready_placed": 8, "selected_risk_proof_present_prop_deferred": 45}`.

## What Happened Friday

Outcome counts were `{"DEFERRED_GTOS_VNEXT_PROP_RESET": 45, "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN": 8, "REJECTED_GATE3_CIRCUIT_BREAKER": 3, "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC": 272}`. Placement concentrated in XAUUSD and NAS100: `{"NAS100": 3, "XAUUSD": 5}`. Canonical row dispositions were `{"bridge_or_selected_risk_source_repair_required": 271, "correct_spread_or_circuit_no_trade_pending_replay": 3, "placed_trade_lifecycle_reconciled_or_open": 6, "placed_trade_with_logging_or_lifecycle_defect": 2, "prop_exposure_repair_required": 45, "selected_current_refusal_requires_replay_disposition": 1}`.

The placed lifecycle split was `{"filled_and_full_closed_before_friday_close": 4, "filled_open_at_friday_close": 2, "filled_partial_exit_residual_open_at_friday_close": 2}`. Broker truth status through Friday close was `{"filled_and_full_closed_before_friday_close": 4, "filled_open_at_friday_close": 2, "filled_partial_exit_residual_open_at_friday_close": 2}`. Net broker-R status was `{"blocked_missing_initial_risk_dollar_or_partial_broker_profit": 3, "source_fields_available_for_net_r_calculation": 5}`. Manual intervention scan found `{"no_manual_intervention_detected_in_local_slippage_or_weekend_autopsy": 8}`.

## Placed Trade Autopsy

| Trade | Ticket | Symbol/Side | Friday lifecycle | Gross close R observed | Broker profit observed | Current repaired code difference |
|---|---:|---|---|---:|---:|---|
| XAUUSD_2026-05-28_moonshot_h23_00_2345 | 241725208 | XAUUSD SHORT | filled_and_full_closed_before_friday_close | -1.0069 | -250.74 | yes_ticket_bound_or_logging_repair_needed |
| XAUUSD_2026-05-29_moonshot_h01_02_0115 | 241739921 | XAUUSD LONG | filled_open_at_friday_close | None | None | no_known_code_difference_from_current_local_evidence |
| XAUUSD_2026-05-29_moonshot_h01_02_0130 | 241742912 | XAUUSD SHORT | filled_and_full_closed_before_friday_close | -1.0018 | -232.26 | no_known_code_difference_from_current_local_evidence |
| NAS100_2026-05-29_moonshot_h06_07_0615 | 241779188 | NAS100 LONG | filled_partial_exit_residual_open_at_friday_close | 1.0312 | None | no_known_code_difference_from_current_local_evidence |
| NAS100_2026-05-29_ny_1345 | 241926200 | NAS100 LONG | filled_and_full_closed_before_friday_close | -1.0009 | -243.08 | no_known_code_difference_from_current_local_evidence |
| NAS100_2026-05-29_ny_1415 | 241948220 | NAS100 SHORT | filled_partial_exit_residual_open_at_friday_close | 1.0429 | None | yes_ticket_bound_or_logging_repair_needed |
| XAUUSD_2026-05-29_ny_1500 | 241972476 | XAUUSD LONG | filled_open_at_friday_close | None | None | no_known_code_difference_from_current_local_evidence |
| XAUUSD_2026-05-29_ny_1515 | 241989671 | XAUUSD LONG | filled_and_full_closed_before_friday_close | -1.0175 | -155.6 | no_known_code_difference_from_current_local_evidence |

Open/residual rows at Friday close: `4`. Residual statuses were `{"filled_open_at_friday_close": 2, "filled_partial_exit_residual_open_at_friday_close": 2}`. Later MT5 history would be required only if a route needs post-Friday terminal outcome; this route stops at the proven Friday boundary.

## Losing And Winning Mechanisms

Microscopic anatomy covers all `328` primary rows with tick bid/ask and D1/H4/H1/M15 context. Terminal path classes were `{"loss_sl_before_partial_trigger": 200, "winner_partial_then_be_return": 73, "winner_partial_then_dynamic_final": 36, "stuck_entry_no_sl_or_1r_before_friday_close": 12, "partial_trigger_then_open_at_friday_close": 5, "no_entry_touch_before_friday_close": 2}`.

Major losing mechanisms were stop-first adverse path, wrong direction/no continuation, sweep-continuation failure, spread-cost large versus stop, and stale selected-risk bridge domination. Major winning mechanisms were liquidity sweep reclaim, displacement follow-through, M1/tick continuation, structural-distance follow-through, and volatility-expansion follow-through.

## Refusals, Stale Blockers, And Repairs

The route separated correct no-trade rows from stale or repaired blockers. The important repaired defects were same-symbol vNext lifecycle fail-closed behavior, pending lifecycle stale terminal selection, broker net-R/cost logging, full selected denominator replay, microscopic price-action anatomy, quality selector evidence reanchor, and account-exposure prop-deferral reconstruction.

The `271` selected/risk bridge missing-or-zero rows remain classified as source-repair-required in the clean Friday live packet, not as proof that the whole selected vNext system failed. The Stage08/09 broad selected scan closes the earlier Stage04 selected-shard gap at the evidence-metadata level by scanning `289600` selected rows and reanchoring the active quality-selector evidence path away from weekend contamination.

## Market Coverage And Starvation

Why only XAUUSD/NAS100 placed: only those two symbols reached selected-cell risk and broker-ready state in the clean freeze. XAUUSD had `6` broker-ready rows and `5` placed; NAS100 had `3` broker-ready rows and `3` placed. The other non-crypto symbols were dominated by prop deferrals, selected-cell/risk bridge refusals, dynamic selector refusals, spread rejections, or no primary candidate rows.

- AUDJPY: raw=25, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- AUDUSD: raw=22, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- CHFJPY: raw=23, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- EURGBP: raw=25, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- EURJPY: raw=21, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- EURUSD: raw=22, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- GBPJPY: raw=9, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- GBPUSD: raw=17, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- GER40: raw=12, risk=0, ready=0, placed=0, reason=dynamic_selected_cell_or_selector_bridge_refusals_dominated
- JP225: raw=16, risk=0, ready=0, placed=0, reason=dynamic_selected_cell_or_selector_bridge_refusals_dominated
- NAS100: raw=16, risk=3, ready=3, placed=3, reason=symbol_reached_order_placement
- NZDUSD: raw=0, risk=0, ready=0, placed=0, reason=no_primary_candidate_rows_in_clean_friday_freeze
- SPX500: raw=0, risk=0, ready=0, placed=0, reason=no_primary_candidate_rows_in_clean_friday_freeze
- UK100: raw=0, risk=0, ready=0, placed=0, reason=no_primary_candidate_rows_in_clean_friday_freeze
- UKOIL_cash: raw=18, risk=0, ready=0, placed=0, reason=dynamic_selected_cell_or_selector_bridge_refusals_dominated
- US30_cash: raw=0, risk=0, ready=0, placed=0, reason=no_primary_candidate_rows_in_clean_friday_freeze
- USDCAD: raw=27, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- USDCHF: raw=15, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- USDJPY: raw=21, risk=0, ready=0, placed=0, reason=prop_deferrals_and_selected_risk_bridge_refusals_dominated
- USOIL_cash: raw=16, risk=0, ready=0, placed=0, reason=dynamic_selected_cell_or_selector_bridge_refusals_dominated
- XAGUSD: raw=0, risk=0, ready=0, placed=0, reason=no_primary_candidate_rows_in_clean_friday_freeze
- XAUUSD: raw=23, risk=6, ready=6, placed=5, reason=symbol_reached_order_placement

## Full-System And Execution Policy Metrics

Clean Friday current selected policy on the 328-row selected denominator: `{"breakeven": 2, "gross_r_avg": -0.273696, "gross_r_sum": -89.772197, "known_r_rows": 328, "losses": 210, "rows": 328, "win_rate": 0.353659, "wins": 116}`. Broker-ready current selected policy on the 9-row denominator: `{"breakeven": 0, "gross_r_avg": -0.317164, "gross_r_sum": -2.854477, "known_r_rows": 9, "losses": 5, "rows": 9, "win_rate": 0.444444, "wins": 4}`.

Momentum/partial/fixed/trailing comparators were tested on selected and broker-ready denominators, not only raw candidates. The policy decision is: `do_not_promote_new_policy_from_friday_raw_slice; preserve current momentum/partial router and use selected/broker-ready denominators for next stress pass`. No new policy is promoted from the Friday raw slice; current `momentum_exhaustion` primary plus `partial_be_runner` exception remains the supported runtime posture.

## Quality Selector Decision

Decision: `keep_execution_predicates_reanchor_evidence_metadata_no_rule_expansion`. The implementation keeps execution predicates unchanged and reanchors evidence metadata to `FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json`; no broker action or live restart occurred.

Clean Friday quality classifications: `{"insufficient_current_proof": 283, "no_trade_by_evidence": 2, "tradeable_now": 43}`. Clean Friday tradeable subset: `{"breakeven": 0, "gross_r_avg": 0.22093, "gross_r_sum": 9.5, "known_r_rows": 43, "losses": 19, "rows": 43, "win_rate": 0.55814, "wins": 24}`. Clean Friday London liquidity rule: `{"breakeven": 0, "gross_r_avg": 0.35, "gross_r_sum": 7.0, "known_r_rows": 20, "losses": 9, "rows": 20, "win_rate": 0.55, "wins": 11}`. Clean Friday London displacement rule: `{"breakeven": 0, "gross_r_avg": 0.14, "gross_r_sum": 3.5, "known_r_rows": 25, "losses": 11, "rows": 25, "win_rate": 0.56, "wins": 14}`.

Broad selected replay support: London liquidity sweep reclaim `{"breakeven": 5035, "gross_r_avg": 0.553188, "gross_r_sum": 8654.622638, "known_r_rows": 15645, "losses": 980, "rows": 15645, "win_rate": 0.615532, "wins": 9630}`; London displacement continuation `{"breakeven": 2725, "gross_r_avg": 0.392758, "gross_r_sum": 3065.086268, "known_r_rows": 7804, "losses": 1043, "rows": 7804, "win_rate": 0.517171, "wins": 4036}`.

## Risk, Exposure, And Concurrency

All `45` Friday prop deferrals are explained by the GTOS internal daily overlay budget: `{"no_budget_after_existing_and_buffers": 44, "positive_budget_below_min_reduced_risk": 1}`. Binding budget counts: `{"gtos_internal_daily_overlay": 45}`. Allowed new-trade risk percent range was `{"max": 0.204174, "min": -0.414157}` with open-position risk amount range `{"max": 4044.7716, "min": 4022.8736}`.

Count/concurrency refusal rows: `0`. Current interpretation: `{"legacy_count_cap": "legacy/non-vNext only; selected-cell-governed vNext rows bypass old filled-position count cap", "open_position_risk_source": "ticket-bound pending lifecycle selected-cell risk; missing lifecycle does not default to base risk", "pre_dynamic_prop_projection": "budget actions before dynamic selected-cell risk are projection-only unless hard boundary reasons apply", "same_symbol_vnext_gate": "same-symbol stacking remains fail-closed until multi-ticket lifecycle support is explicit", "terminal_prop_gate": "reruns after selected-cell risk and executable geometry"}`. Repair decision: `no_additional_code_change_required_for_friday_stage10; existing current code repairs stale pre-dynamic prop terminal block and stale count defaults`.

## Code, Config, Test, And Context Changes

Code/config/test repairs and route artifacts in this route include:

- `config/agent_config.yaml` quality-selector evidence metadata reanchor.
- `src/research/moonshot_default_off_policy_router.py` selector evidence-path/rule metadata repair.
- same-symbol selected-cell lifecycle fail-closed behavior in `src/components/permissions.py`.
- pending lifecycle terminal ordering repair in `src/research_infra/pending_limit_lifecycle_audit.py`.
- broker net-R/cost telemetry and audit fields in close-side logging/audit helpers.
- builders and verifiers for Friday freeze, canonical event replay, micro anatomy, policy/quality replay, and account exposure repair.

Focused code-repair verification is `{"checks": ["same_symbol_vnext_position_source_error_fails_closed", "pending_lifecycle_fill_event_wins_over_stale_checked_candle", "close_slippage_net_broker_r_fields", "broker_actual_r_audit_net_fields"], "issue_count": 0, "ok": true}`.

Stage13/14 closeout artifacts added: `FRIDAY_TO_BROAD_REPLAY_CHANGE_DOSSIER.jsonl`, `FRIDAY_PRODUCTION_CHANGE_EVIDENCE_MATRIX.json`, `FRIDAY_IMPLEMENT_KILL_REDESIGN_DECISION_LEDGER.jsonl`, `FRIDAY_CONTEXT_STALENESS_REPAIR_LEDGER.jsonl`, this final report, and refreshed route state/audit/manifest.

## Remaining Unsolved Source Requirements

- Post-Friday terminal outcomes for open/residual tickets require MT5/account history after the Friday close boundary if a later route asks that question.
- Some net broker-R rows remain blocked where initial dollar risk or partial broker profit source fields are incomplete.
- Historical selected-cell bridge missing/zero rows remain source-repair requirements; they are not converted into performance claims.
- Multi-ticket same-symbol lifecycle support remains intentionally fail-closed until explicit lifecycle source support exists.
- Production-change readiness for any new selector/router expansion requires a separate dossier; this route repaired evidence, logging, replay, and metadata but did not authorize live behavior expansion.

## Next Moonshot Directions

- Build a broader meta-selector from the preserved mechanism expansion ledger, with source identity, cost/stress, and selected denominator guards.
- Continue broad selected-system stress by symbol/session/origin, especially for London liquidity sweep reclaim and London displacement continuation.
- Convert residual selected-cell bridge missingness into source-capture contracts so future live rows are not ambiguous.
- Extend broker truth joins for partial/residual lifecycle rows to capture net R consistently through full close.
- Keep market-starvation monitoring by symbol so silent or underrepresented symbols get explicit candidate/risk/spec/source reasons instead of being invisible.
