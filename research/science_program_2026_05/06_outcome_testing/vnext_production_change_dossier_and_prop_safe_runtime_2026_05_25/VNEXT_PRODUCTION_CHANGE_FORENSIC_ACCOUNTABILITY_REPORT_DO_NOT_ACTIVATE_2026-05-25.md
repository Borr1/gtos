# vNext Production Change Forensic Accountability Report

Date: 2026-05-25

Route: `vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25`

Status: DO NOT ACTIVATE AS-IS

This file preserves the forensic accountability findings from the post-closeout review. It is intended as a durable reference for a follow-up session. It is not an implementation patch, not a new route, and not an activation dossier.

## Blunt Diagnosis

The user was not seeing it wrong. The committed route went from a baseline/current-shadow result of `35,983` selected trades and `+4008.3317R` to a new production-mechanical replay result of `10` selected trades and `-4.999959R`.

That is a production candidate failure, not a successful production-change outcome.

The failure is a combination of:

- Production candidate collapse in Stage09.
- Prop-selector replay modeling bug/artifact: one continuous account path across the entire 2022-2026 candidate stream, with no challenge/account-window reset.
- Overblocking from vNext AVOID pressure.
- Route semantics bug in Stage09: new mechanical did not require route `FOLLOW`, so `LEGACY` and `MIXED` generated rows could pass through until prop budget blocked them.
- AI no-paid-call scenario was a diagnostic zero-trade path, not a viable production selector.
- Stage09 and Stage10 verifier weakness: catastrophic/no-trade or near-no-trade output was allowed to pass.
- Completion audit logic bug: audit wrote `complete=true` while embedded Stage10 status was still `in_progress`.

The committed runtime changes are unsafe to activate as-is. Keep activation flags off. Preserve the work as a diagnostic base unless the owner chooses a clean revert for history hygiene.

## Primary Artifacts Inspected

Route directory:

`research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/`

Inspected artifacts:

- `VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json`
- `VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_LEDGER_2026-05-25.jsonl`
- `stage09_shards/*/replay_comparison.jsonl.gz`
- `VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_DOSSIER_2026-05-25.md`
- `VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json`
- `VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json`
- `build_vnext_production_change_stage09_forward_replay_2026_05_25.py`
- `verify_vnext_production_change_stage09_forward_replay_2026_05_25.py`
- `test_vnext_production_change_stage09_forward_replay_2026_05_25.py`
- `build_vnext_production_change_stage10_completion_audit_2026_05_25.py`
- `verify_vnext_production_change_stage10_completion_audit_2026_05_25.py`
- `test_vnext_production_change_stage10_completion_audit_2026_05_25.py`
- `config/agent_config.yaml`
- `src/components/gtos_vnext_runtime.py`
- `src/components/orchestrator.py`
- `src/components/execution.py`
- `src/components/ai_supervisor.py`
- `src/components/primary_analyzer.py`

Upstream full replay artifacts inspected:

- `vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_2026-05-24.json`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_DOMINANCE_AND_POLLUTION_LEDGER_2026-05-24.jsonl`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/stage05_shards/*/dominance_and_pollution.jsonl.gz`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_M15_VS_LTF_DISAGREEMENT_LEDGER_2026-05-24.jsonl`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/stage04_shards/*/m15_vs_ltf_disagreement.jsonl.gz`
- `vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl`

## Accountability Timeline

Observed git history:

```text
75a85d244 (HEAD -> main) research: complete vnext production change route
3db3fc58c research: add vnext stage09 replay comparison
cd9101dc0 runtime: add bounded ai supervisor
1f8e806be (origin/main, origin/HEAD) runtime: add vnext mechanical ai policy
37f5cc8c0 research: checkpoint stage06 route state
```

Stage09 summary:

- File: `VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json`
- Created: `2026-05-25T11:04:04.676227Z`
- Git head recorded inside summary: `cd9101dc03eac35df2c1d39e17da0ff41b2afb92`

Stage09 verification result:

- File: `VNEXT_PRODUCTION_CHANGE_STAGE09_VERIFICATION_RESULT_2026-05-25.json`
- Created: `2026-05-25T11:04:15.004445Z`
- `ok=true`
- `candidate_rows=253234`
- `written_replay_rows=253234`

Stage10 completion audit:

- File: `VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json`
- Created: `2026-05-25T11:10:34.353653Z`
- `complete=true`
- Git head recorded inside audit: `3db3fc58c02e9b388754acb146c23437604431aa`
- Embedded `stage_status_table.STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER` remained `in_progress`

Final route state:

- File: `VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json`
- Updated: `2026-05-25T11:10:34.387984Z`
- `first_incomplete_invariant=NONE`
- Stage10 state later became `complete`

Conclusion: Stage09 knew the catastrophic metrics at `11:04Z`. Stage10 then converted those metrics into a completed route at `11:10Z`. The correct action should have been to classify the production candidate as failed and open repair/failure-anatomy work, not complete the route.

## Stage09 Headline Metrics

| Scenario | Selected | Performance Rows | Total R | Expectancy R | WR | PF | Missed Winners | Avoided Losers | Blocked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_current_shadow` | 35,983 | 33,845 | +4008.331701 | +0.118432 | 44.7658% | 1.214657 | 89,291 | 116,614 | n/a |
| `previous_hypothetical_activated` | 35,983 | 33,845 | +4008.331701 | +0.118432 | 44.7658% | 1.214657 | 89,291 | 116,614 | n/a |
| `new_production_change_mechanical` | 10 | 10 | -4.999959 | -0.499996 | 20.0% | 0.375005 | 104,440 | 135,300 | 216,161 |
| `new_production_change_external_budget_only` | 10 | 10 | -4.999959 | -0.499996 | 20.0% | 0.375005 | n/a | n/a | 216,171 |
| `new_ai_policy_no_paid_call` | 0 | 0 | 0.0 | null | null | null | n/a | n/a | all blocked/avoided |

Baseline final equity was `1.4385016190435467e+41`, which is meaningless compounding distortion from a multi-year continuous replay. New mechanical final equity was about `$90,092.35`, near the static overall max-loss floor.

## Complete Nonzero Bottleneck Table

### Baseline Current Shadow

| Skip reason | Count | Code path |
|---|---:|---|
| `route_legacy_not_follow` | 166,779 | Stage09 `selected_from_previous`, lines 325-337 |
| `pre_ai_skip_avoid_only` | 43,724 | Stage09 `selected_from_previous`, lines 331-332 |
| `route_mixed_not_follow` | 4,198 | Stage09 `selected_from_previous`, lines 333-334 |
| `route_avoid_not_follow` | 1,309 | Stage09 `selected_from_previous`, lines 333-334 |
| `risk_zero` | 1,241 | Stage09 `selected_from_previous`, lines 335-336 |

`previous_hypothetical_activated` was identical to baseline:

| Transition | Count |
|---|---:|
| baseline false, hypothetical false | 217,251 |
| baseline true, hypothetical true | 35,983 |

No row differed.

### New Production Mechanical

| Skip reason | Count | Code path / config |
|---|---:|---|
| `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget` | 208,176 | Stage09 lines 847-909; selector `evaluate_vnext_prop_safe_selector`, lines 14706-15110 |
| `vnext_decision_avoid` | 37,047 | `vnext_execution_block_reason`, lines 15140-15176; config `avoid_blocks_execution:true` |
| `pre_ai_skip_avoid_only` | 7,986 | Stage09 lines 891-903 |
| `prop_safe_selector_defer_until_reset_gtos_internal_daily_overlay_budget` | 15 | selector internal overlay, lines 14925-14957 |

### External Budget Only

| Skip reason | Count |
|---|---:|
| `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget` | 208,177 |
| `vnext_decision_avoid` | 37,047 |
| `pre_ai_skip_avoid_only` | 7,986 |
| `prop_safe_selector_block_redacted_account_external_daily_5pct_budget` | 9 |
| `prop_safe_selector_defer_until_reset_redacted_account_external_daily_5pct_budget` | 5 |

### AI No-Paid-Call

| Skip reason | Count |
|---|---:|
| `no_paid_ai_block_legacy_broad_fallback` | 170,187 |
| `no_paid_ai_call_ai_narrowed_route` | 39,323 |
| `no_paid_ai_skip_ai_mechanical_avoid` | 43,724 |

## Baseline To New Transition

| Baseline selected | New selected | Count |
|---|---:|---:|
| false | false | 217,247 |
| false | true | 4 |
| true | false | 35,977 |
| true | true | 6 |

Every one of the `35,977` baseline-selected rows that new dropped was dropped by:

`prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget`

Those dropped baseline-selected rows contained:

- Baseline winners blocked: `15,150`
- Baseline losers blocked: `18,689`
- Net baseline-selected R blocked: `+4011.831701R`

This proves the collapse was not a good filter. It discarded a positive baseline set because the replay account-path budget had already been poisoned.

## New Selected 10 Trades

All 10 new-selected trades were:

- Symbol: `XAGUSD`
- Month: `2022-01`
- Source mode: `OHLC_M1_CSV`

| Candidate | Time UTC | Session | Side | Framework | Outcome | R | Baseline selected | Prop action |
|---|---|---|---|---|---|---:|---|---|
| `cand_9c376be242e851c60b173d49` | 2022-01-03T10:00 | london | LONG | breaker_re_entry | stop_first | -1.0 | true | ALLOW |
| `cand_a14d9bf4261106d01e5b0b84` | 2022-01-03T11:30 | london | LONG | fvg_fill | stop_first | -1.0 | true | REDUCE_RISK internal 4% |
| `cand_30ae8cb2567e83b3df6ca4f6` | 2022-01-04T02:00 | tokyo | LONG | ob_retest | stop_first | -1.0 | false | ALLOW |
| `cand_b26fdd7e6cc2ba4bb7ef266e` | 2022-01-04T06:30 | off_kz | LONG | ob_retest | target_first | +1.500040803 | false | ALLOW |
| `cand_c9ae3f81c827b423349b0f73` | 2022-01-04T08:45 | london | LONG | fvg_fill | stop_first | -1.0 | true | ALLOW |
| `cand_7eb02ca78af9520ab4cff081` | 2022-01-04T09:45 | london | LONG | breaker_re_entry | target_first | +1.500000000 | true | ALLOW |
| `cand_4a1778758fb33fc6b1c18241` | 2022-01-04T10:00 | london | LONG | ob_retest | stop_first | -1.0 | true | ALLOW |
| `cand_3385813009afec97fcd5e43d` | 2022-01-04T13:00 | ny | SHORT | ob_retest | stop_first | -1.0 | false | ALLOW |
| `cand_7f7b7490d8eef0438d22525b` | 2022-01-04T13:15 | ny | SHORT | ob_retest | stop_first | -1.0 | false | ALLOW |
| `cand_66ad6a6a03cbbd5257e9d0a3` | 2022-01-05T08:45 | london | LONG | breaker_re_entry | stop_first | -1.0 | true | REDUCE_RISK overall |

These 10 are not representative. They are residue before the continuous replay account hit the max-loss floor.

## Row Examples

### Selected Winner

`cand_b26fdd7e6cc2ba4bb7ef266e`

- Time: `2022-01-04T06:30:00+00:00`
- Symbol/session/side/framework: `XAGUSD`, `off_kz`, `LONG`, `ob_retest`
- Outcome/R: `target_first`, `+1.500040803`
- Baseline selected: false
- Route decision: `LEGACY`
- Prop action: `ALLOW`

This row should not be interpreted as proof the new selector worked. It is an off-KZ generated row that survived because Stage09 new mechanical did not require route `FOLLOW`.

### Selected Loser

`cand_9c376be242e851c60b173d49`

- Time: `2022-01-03T10:00:00+00:00`
- Symbol/session/side/framework: `XAGUSD`, `london`, `LONG`, `breaker_re_entry`
- Outcome/R: `stop_first`, `-1.0`
- Baseline selected: true
- Route decision: `FOLLOW`
- Prop action: `ALLOW`

### Missed Winner

`cand_e364d2a758634caa75e4ce10`

- Time: `2022-01-03T07:30:00+00:00`
- Symbol/session/side/framework: `XAGUSD`, `london`, `SHORT`, `ob_retest`
- Outcome/R: `target_first`, `+1.499984523`
- Baseline reason: `pre_ai_skip_avoid_only`
- New reason: `vnext_decision_avoid`

### Avoided Loser

`cand_a83695ecc5112d6633e1920b`

- Time: `2022-01-03T10:30:00+00:00`
- Symbol/session/side/framework: `XAGUSD`, `london`, `SHORT`, `fvg_fill`
- Outcome/R: `stop_first`, `-1.0`
- New reason: `vnext_decision_avoid`

### Prop-Blocked Winner

`cand_0d0c767d3389c56cd92aa09d`

- Time: `2022-01-05T11:00:00+00:00`
- Symbol/session/side/framework: `XAGUSD`, `london`, `LONG`, `breaker_re_entry`
- Outcome/R: `target_first`, `+1.499982569`
- Baseline selected: true
- New reason: `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget`
- Remaining overall cushion before projected risk: `$92.35`
- Projected overall cushion after full risk: `-$2250.05`

## Prop-Safe Selector Findings

The redacted_account math formula in `src/components/gtos_vnext_runtime.py` was coded as requested:

- External daily floor: `day_start_baseline - initial_balance * 5%`, lines 14897-14914.
- Static overall floor: `initial_balance * 90%`, lines 14899-14922.
- No trailing drawdown modeled, line 14922.
- Internal 4% overlay kept separate, lines 14925-14957.
- Open, pending, new trade, spread/slippage/commission, correlation, concentration, and simultaneous candidate risk included, lines 14821-14883.

The failure is the Stage09 replay application/model:

- `ScenarioMetrics.equity` is a single account over the full sorted historical stream, lines 395-447 and 514-516.
- Daily reset rolls at GMT+3 using `reset_window_start_utc`, lines 125-128 and 442-447.
- There is no challenge/account-window reset.
- Stage09 `account_state_for_selector()` passes the same persistent `metrics.equity` into every later row, lines 652-684.
- Stage09 sets open position risk, pending order risk, and correlated exposure risk to zero in replay, lines 671-675.
- Off-KZ generated rows are still processed by the budget stream.

First overall block:

`cand_169057a8ef14afb1140860f1`

- Time: `2022-01-05T09:45:00+00:00`
- Symbol/session/side/framework: `XAGUSD`, `london`, `LONG`, `fvg_fill`
- R: `-1.0`
- Baseline selected: true
- Remaining daily cushion: `$2740.27`
- Remaining overall cushion: `$92.35`
- Projected daily cushion after full risk: `$397.87`
- Projected overall cushion after full risk: `-$2250.05`
- New reason: `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget`

Internal 4% overlay did not dominate:

- Mechanical vs external-only differed on only two rows.
- External overall 10% block was the dominant suppressor.
- External-budget-only still blocked `216,171` rows because the single continuous account path exhausted the static overall budget.

## Off-KZ Impact

Candidate universe by session:

| Session | Candidate rows |
|---|---:|
| london | 58,842 |
| ny | 56,920 |
| tokyo | 25,710 |
| off_kz | 111,762 |

Prop overall block by session:

| Session | Rows blocked by external overall |
|---|---:|
| off_kz | 111,755 |
| ny | 44,115 |
| london | 40,053 |
| tokyo | 20,238 |

Baseline selected zero off-KZ rows. New selected included one off-KZ row. Off-KZ generated rows materially distorted prop budget and blocker counts.

## Candidate Universe

Stage02 candidate generation summary:

- Method: `market_bar_asof_incremental_ob_fvg_breaker_generator`
- Denominator rows: `903,163`
- Candidate rows: `253,234`
- Candidate source origin: `market_bar_enumeration`

The `253,234` rows are route-local generated market-bar candidates, not true broker-live trade candidates.

Candidate universe by symbol:

| Symbol | Rows |
|---|---:|
| AUDJPY | 1,261 |
| AUDUSD | 1,252 |
| BTCUSD | 4,003 |
| CHFJPY | 1,254 |
| ETHUSD | 3,318 |
| EURGBP | 1,173 |
| EURJPY | 1,230 |
| EURUSD | 3,999 |
| GBPJPY | 34,838 |
| GBPUSD | 33,592 |
| GER40 | 4,667 |
| JP225 | 2,811 |
| NAS100 | 25,659 |
| NZDUSD | 2,505 |
| SPX500 | 2,020 |
| UK100 | 4,405 |
| UKOIL_cash | 1,142 |
| US30_cash | 27,854 |
| USDCAD | 1,044 |
| USDCHF | 1,262 |
| USDJPY | 35,716 |
| USOIL_cash | 1,013 |
| XAGUSD | 27,242 |
| XAUUSD | 29,974 |

Candidate universe by source mode in Stage09 scoring:

| Source mode | Rows |
|---|---:|
| OHLC_M1_CSV | 215,610 |
| SIERRA_SCID_CONVERTED_M1_PROXY | 17,838 |
| MISSING_SOURCE | 11,631 |
| OHLC_M15_CSV | 6,183 |
| LOCAL_TICK_PARQUET | 1,650 |
| OHLC_M5_CSV | 322 |

Candidate universe by terminal outcome:

| Terminal outcome | Rows |
|---|---:|
| stop_first | 132,851 |
| target_first | 101,477 |
| missing_source_denominator_excluded | 11,631 |
| timeout | 5,424 |
| no_fill | 1,817 |
| same_bar_ambiguous_unresolved | 34 |

Stage09 replay candidate IDs were unique: duplicate candidate IDs count was zero.

## Baseline Selected Breakdown

Baseline selected rows: `35,983`

By symbol:

| Symbol | Selected |
|---|---:|
| GBPJPY | 10,099 |
| GBPUSD | 7,099 |
| US30_cash | 5,961 |
| XAUUSD | 3,465 |
| XAGUSD | 3,223 |
| USDJPY | 2,778 |
| NAS100 | 2,745 |
| EURUSD | 613 |

By session:

| Session | Selected |
|---|---:|
| london | 17,188 |
| ny | 16,580 |
| tokyo | 2,215 |

By side:

| Side | Selected |
|---|---:|
| LONG | 32,182 |
| SHORT | 3,801 |

By framework:

| Framework | Selected |
|---|---:|
| fvg_fill | 16,431 |
| breaker_re_entry | 11,046 |
| ob_retest | 8,506 |

By source mode:

| Source mode | Selected |
|---|---:|
| OHLC_M1_CSV | 31,024 |
| SIERRA_SCID_CONVERTED_M1_PROXY | 2,478 |
| MISSING_SOURCE | 1,894 |
| OHLC_M15_CSV | 305 |
| LOCAL_TICK_PARQUET | 230 |
| OHLC_M5_CSV | 52 |

By terminal outcome:

| Terminal outcome | Selected |
|---|---:|
| stop_first | 18,662 |
| target_first | 15,108 |
| missing_source_denominator_excluded | 1,894 |
| no_fill | 241 |
| timeout | 75 |
| same_bar_ambiguous_unresolved | 3 |

## New Selected Breakdown

New selected rows: `10`

By symbol:

| Symbol | Selected |
|---|---:|
| XAGUSD | 10 |

By session:

| Session | Selected |
|---|---:|
| london | 6 |
| ny | 2 |
| tokyo | 1 |
| off_kz | 1 |

By side:

| Side | Selected |
|---|---:|
| LONG | 8 |
| SHORT | 2 |

By framework:

| Framework | Selected |
|---|---:|
| ob_retest | 5 |
| breaker_re_entry | 3 |
| fvg_fill | 2 |

By source mode:

| Source mode | Selected |
|---|---:|
| OHLC_M1_CSV | 10 |

By terminal outcome:

| Terminal outcome | Selected |
|---|---:|
| stop_first | 8 |
| target_first | 2 |

## vNext AVOID Pressure

`vnext_decision_avoid` blocked `37,047` rows.

Outcome classes:

| Class | Count |
|---|---:|
| loser | 19,741 |
| winner | 15,507 |
| R null | 1,799 |

Net R sum if taken: `+3502.764949R`. That means the AVOID block was net harmful in this replay.

Dominant evidence family/component aggregation from Stage05 dominance join:

| Evidence family/component | Count | Losers saved | Winners blocked | Null | R sum if taken |
|---|---:|---:|---:|---:|---:|
| `__NULL__` | 9,855 | 5,401 | 4,056 | 398 | +680.486827 |
| `l2_entry_in_ob_rejection_value` | 1,043 | 606 | 416 | 21 | +18.000001 |
| `l2_h1_poi_rejection_value` | 1,109 | 591 | 480 | 38 | +129.000552 |
| `l2_m15_choch_rejection_value` | 1,256 | 761 | 471 | 24 | -52.890009 |
| `rejected_candidate_blocked_limit_value` | 6,408 | 3,169 | 2,834 | 405 | +1081.045633 |
| `rejected_candidate_c1_failed_value` | 2,433 | 1,245 | 1,058 | 130 | +339.820526 |
| `rejected_candidate_c3_direction_mismatch_value` | 3,187 | 1,827 | 1,270 | 90 | +76.059685 |
| `rejected_candidate_ob_proximity_value` | 4,037 | 2,145 | 1,703 | 189 | +402.171086 |
| `rejected_candidate_other_unknown_value` | 3,111 | 1,596 | 1,295 | 220 | +344.496689 |
| `rejected_candidate_prescreen_no_direction_value` | 4,608 | 2,400 | 1,924 | 284 | +484.573959 |

Only `l2_m15_choch_rejection_value` was net useful. Most AVOID components blocked more R than they saved.

Broad/stale pollution did not explain these AVOID rows:

- `broad_unanchored_rows`: 0
- `stale_legacy_rows`: 0
- `current_source_bound_rows`: present for all `37,047`

## Pre-AI And AI Policy

Stage09 policy counts:

| Pre-AI action | Count |
|---|---:|
| `ALLOW_AI` | 170,187 |
| `NARROW_AI_TO_SIDE` | 39,323 |
| `SKIP_AI_AVOID_ONLY` | 43,724 |

Route decisions:

| Route decision | Count |
|---|---:|
| LEGACY | 166,779 |
| FOLLOW | 41,774 |
| AVOID | 37,047 |
| MIXED | 7,634 |

AI policy action counts:

| AI policy action | Count |
|---|---:|
| `BLOCK_LEGACY_BROAD_FALLBACK` | 170,187 |
| `CALL_AI_NARROWED_ROUTE` | 39,323 |
| `SKIP_AI_MECHANICAL_AVOID` | 43,724 |

AI no-paid-call selected zero because there was no `FOLLOW_WITHOUT_AI` path:

- Config `ai_policy_follow_no_ai_enabled: false`, `config/agent_config.yaml` lines 641-648.
- `CALL_AI_NARROWED_ROUTE` rows require AI calls.
- `BLOCK_LEGACY_BROAD_FALLBACK` rows are blocked.
- `SKIP_AI_MECHANICAL_AVOID` rows are avoided.

AI supervisor did not suppress candidates in Stage09:

- All `253,234` rows: `HEALTHY`, `disable_ai_narrowing=false`.
- Runtime supervisor cannot directly block trades, change direction, or change trade parameters; `src/components/ai_supervisor.py` lines 321-338.

## LTF / M1 / No-Fill

Stage09 LTF/pending did not affect selection:

- `ltf_action=PLACE_LIMIT` for all `253,234`.
- `pending_action=PLACE_LIMIT` for all `253,234`.
- No `SKIP_LTF_NOFILL_AVOID`.
- No pending/no-fill skip reason in Stage09 bottlenecks.

Stage04 M15-vs-LTF disagreement:

- Disagreement rows: `405,729`
- Unique candidate IDs: `216,331`
- Joined to Stage09: `405,729`

Disagreement rows by LTF mode:

| LTF mode | Rows |
|---|---:|
| m1_path_aware | 211,410 |
| m5_path_aware | 148,893 |
| tick_or_sierra_path_aware | 45,426 |

Change flags:

| Change flag | Rows |
|---|---:|
| entry_timing_changed | 393,221 |
| simulated_r_changed | 131,795 |
| terminal_outcome_changed | 128,918 |

Stage09 reason for disagreement rows:

| Stage09 reason | Rows |
|---|---:|
| prop overall block | 331,438 |
| vnext_decision_avoid | 60,979 |
| pre_ai_skip_avoid_only | 13,266 |
| internal overlay defer | 28 |
| selected | 18 |

Missed winners that were M1 path-aware with M15/LTF disagreement: `90,461`.

Conclusion: LTF path awareness existed in scoring, but Stage09 final selection behaved blind to it because execution action remained `PLACE_LIMIT` everywhere.

## Scoring And Leakage

Stage09 uses as-of decision inputs and post-decision scoring joins:

- Decision inputs include runtime fields and config, not future path labels.
- `future_outcome_inputs_used=false`.
- Scoring path/R/no-fill attached after decision in `post_decision_scoring`.
- Stage09 builder lines 985-1004 and 1136-1148 record the leakage guard.

No evidence was found that Stage09 decision logic consumed `simulated_r` directly for decisions.

However, scoring validity remains limited:

- Many R rows are OHLC reconstruction or proxy, not uniform live broker fills.
- Spread/slippage/commission is used in prop budget buffer, not consistently in path R.
- `MISSING_SOURCE` rows affect selected counts but do not contribute R.
- Same-bar ambiguous unresolved rows exist.
- Pass/fail proxy is not meaningful on a 253k-candidate continuous multi-year compounding path.

Stage09 selected source evidence:

| Evidence type | Rows |
|---|---:|
| local_m1_ohlc_reconstruction | 215,610 |
| sierra_scid_converted_m1_proxy_path_reconstruction | 17,838 |
| local_tick_or_sierra_scid_path_reconstruction | 11,631 |
| local_m15_ohlc_reconstruction | 6,183 |
| local_tick_quote_path_reconstruction | 1,650 |
| local_m5_ohlc_reconstruction | 322 |

## Completion And Verifier Failures

Stage09 verifier allowed catastrophic output:

- `verify_summary()` checks row count, written rows, chunk sums, scenario names, leakage flags, 5%/10% redacted_account math, and presence of metric keys.
- It does not assert positive expectancy, PF > 1, minimum selected count, trade frequency, market coverage, improvement vs baseline, prop pass improvement, missed-winner reduction, or non-collapse.
- File/function: `build_vnext_production_change_stage09_forward_replay_2026_05_25.py::verify_summary`, lines 1231-1268.

Smoking-gun Stage09 test:

- File/function: `test_vnext_production_change_stage09_forward_replay_2026_05_25.py::test_verify_summary_requires_all_scenarios_and_redacted_account_math`, lines 126-160.
- It builds a summary with every scenario `selected_count=0`, `total_r=0`, `expectancy_r=None`, and asserts `verify_summary(...) == []`.
- Missing assertion: production viability/non-collapse.

Stage10 converted bad Stage09 output into completion:

- `build_completion_audit()` sets instruction coverage from artifact existence and row counts, not result quality, lines 129-154.
- `remaining_executable_actions_before_owner_activation` becomes `[] if complete`, lines 166-168.
- `write_activation_dossier()` prints the bad metrics but does not classify failure, lines 270-277.
- `verify_audit()` checks instruction coverage, candidate row count, forbidden actions, and artifact existence, lines 346-358.

Stage10 inconsistency:

- Audit file says `complete=true`.
- Embedded `stage_status_table.STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER` says `in_progress`.
- Cause: `build_completion_audit()` writes audit and activation dossier before calling `update_state(audit, complete=complete)`, lines 237-239.
- Stage10 test explicitly allows Stage10 in-progress, `test_all_stage_statuses_complete_allows_stage10_in_progress`, lines 18-27.

## Controlling Prompt Interpretation

The controlling prompt did require system improvement, not merely measurement:

- It states the goal is "direct system improvement" including candidate selection, risk, pending/no-fill, LTF path awareness, prop-firm throttling, AI role control, and replay impact.
- It says: "Do not solve prop risk by blocking everything. Measure trade count, R, expectancy, drawdown, pass probability proxy, missed winners, avoided losers, and market coverage after each candidate selector. If a selector collapses the system into trivial no-trade, redesign it."
- It requires Stage10 completion only when replay comparison artifacts exist and are inspected, and activation dossier states what is ready and what remains gated.

The closeout treated "measured bad result" as "route complete." That was incorrect under the controlling prompt.

## Runtime Activation State

Current config remains default-off for broker-facing effect:

- `gtos_vnext_runtime.apply_to_execution: false`, `config/agent_config.yaml` lines 547-550.
- `ai_policy_apply_to_ai_call: false`, lines 638-648.
- `ltf_path_execution_apply_to_execution: false`, lines 2257-2258.
- `prop_safe_selector_apply_to_execution: false`, lines 2269-2270.

Stage09 replay forcibly enabled activation flags inside `activated_replay_config()`:

- `apply_to_execution=True`
- `pre_ai_apply_to_ai_call=True`
- `ai_policy_apply_to_ai_call=True`
- `prop_safe_selector_apply_to_execution=True`
- `ltf_path_execution_apply_to_execution=True`

Code path: Stage09 builder lines 190-206.

Therefore live/current config is not broker-mutating by default, but flipping activation flags would be unsafe without repair.

## Required Repair Route

Do not activate this runtime.

Next route should be a failure-anatomy/repair route continuing from current Stage09 artifacts, not restarting Stage00-04.

Required repair steps:

1. Add Stage09 and Stage10 failure gates:
   - minimum selected count;
   - minimum trade frequency;
   - selected-only market/session/symbol coverage;
   - positive expectancy;
   - PF threshold;
   - non-collapse vs baseline;
   - missed-winner ceiling;
   - prop overblock sanity;
   - explicit `production_candidate_failed` state.
2. Segment prop replay by challenge/account windows:
   - no one-account 2022-2026 continuous replay;
   - independent phase/account windows;
   - no off-KZ generated rows consuming budget unless executable.
3. Apply prop budget only to executable candidate streams:
   - baseline executable stream;
   - new executable stream;
   - no `LEGACY`/`MIXED` generated variants consuming budget unless they are actually executable.
4. Fix Stage09 route semantics:
   - new mechanical must not select `LEGACY` or `MIXED` simply because they are not actively blocked.
   - Preserve baseline/current behavior unless a specific production-change surface proves otherwise.
5. Separate scenario ablations:
   - baseline only;
   - vNext AVOID only;
   - prop on baseline executable stream;
   - prop on new executable stream;
   - AI no-paid-call diagnostic only;
   - LTF execution effect only.
6. Make coverage metrics selected-only in the dossier:
   - universe coverage separately;
   - selected coverage separately.
7. Re-evaluate AVOID components:
   - kill or redesign net-harmful AVOID families;
   - only preserve net-useful, source-bound blockers.
8. Re-evaluate LTF path as execution behavior:
   - Stage09 must show actual changed entry/no-fill behavior if the feature is considered implemented.
9. Stage10 must fail if Stage09 records production candidate failure.

## Assertions That Must Be Added

Stage09 verifier/test assertions:

- `new.selected_count >= configured_min_selected_count`
- `new.performance_count >= configured_min_performance_count`
- `new.expectancy_r > 0`
- `new.profit_factor > 1`
- `new.selected_count` must not collapse below a configured fraction of baseline unless explicitly marked failed.
- `new.missed_winners <= baseline.missed_winners` or route marks failed.
- `new.total_r >= baseline.total_r - allowed_tradeoff` for production candidate, or route marks failed.
- selected coverage must include expected markets/sessions/symbols unless intentionally scoped.
- prop block ratio must be bounded on executable stream.
- off-KZ generated rows must not consume prop budget unless explicitly executable.
- challenge/account-window segmentation required for prop pass proxy.
- no `complete=true` if `production_candidate_failed=true`.

Stage10 verifier/test assertions:

- audit cannot be `complete=true` if embedded `stage_status_table` has Stage10 `in_progress`.
- audit must compare embedded state to final state.
- audit must fail on negative expectancy, near-zero trade count, or catastrophic missed-winner count unless explicitly classified as failed candidate.
- activation dossier must state "unsafe to activate" when replay metrics fail viability.
- `remaining_executable_actions_before_owner_activation` cannot be empty if Stage09 says candidate failed.

## Final Recommendation

Do not activate `75a85d244`.

Preserve the committed disabled runtime changes as diagnostic scaffolding only. The activation/completion conclusion is invalid. The correct next action is a forensic repair route that uses this report and the Stage09 shards as the starting point, with no Stage00-04 restart unless an input hash mismatch is found.

## Appendix A - Direct Answers To The Accountability Questions

This appendix is intentionally explicit so the next session can use this file without reconstructing chat context.

### Core accountability

Did Stage09 know the bad production-mechanical result?

Yes. Stage09 had the production-mechanical scenario in its metrics and wrote the following aggregate result:

- selected: `10 / 253234`
- performance count: `10`
- total R: `-4.999959196997`
- expectancy: `-0.4999959197`
- win rate: `0.2`
- profit factor: `0.375005100375`
- missed winners: `104440`
- avoided losers: `135300`
- blocked trades: `216161`
- risk reductions: `2`
- deferred trades: `16`
- max drawdown pct: `9.907647919809`
- max loss streak: `4`
- min daily cushion: `1097.5`
- min overall cushion: `92.35208`

Where did the numbers first appear on disk?

- Row-level data first appeared in `stage09_shards/*/replay_comparison.jsonl.gz`.
- Aggregate scenario metrics appeared in `VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json`.
- The same aggregate result was carried into `VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_DOSSIER_2026-05-25.md`.
- Stage10 later embedded/computed completion state in `VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json`.

At what exact point was it accepted as complete?

The disk transition to "complete" happened in Stage10, not because Stage09 proved production viability. Stage10's builder wrote the completion audit before updating Stage10's own status table. The audit reported `complete=true` while the embedded `stage_status_table` still had Stage10 as `in_progress`. The Stage10 verifier/test suite allowed that inconsistency.

Did this treat "measured bad result" as "route complete" instead of "production candidate failed"?

Yes. The result was treated as artifact completion. The correct interpretation was: the production candidate failed, or at minimum entered a failure-anatomy/repair gate. The route did not encode that gate.

Did the controlling prompt require only measurement, or also repair when the measured system collapsed?

It required repair. The controlling instructions included a collapse guard: if the selector collapsed the system into trivial no-trade while budget remained available, it had to be redesigned before moving forward. Stage09/Stage10 did not enforce this.

Did any verifier require positive expectancy, minimum selected count, minimum trade frequency, improved prop outcome, reduced missed winners, or non-collapse versus baseline?

No. The verifiers checked artifact presence, row counts, scenario presence, leakage/math conditions, and instruction coverage. They did not require production viability.

Which verifier/test allowed catastrophic output to pass?

- `research/.../test_vnext_production_change_stage09_forward_replay_2026_05_25.py::test_verify_summary_requires_all_scenarios_and_redacted_account_math`
  - The test fixture allowed every scenario to have `selected_count=0`, `total_r=0`, and `expectancy=None`, then asserted no verifier failure.
  - Missing assertion: nonzero/minimum production selection, positive expectancy, PF above 1, non-collapse versus baseline, missed-winner ceiling, and explicit failure state.
- Stage09 builder function `verify_summary`
  - Missing assertion: viability of the production candidate.
- Stage10 builder function `verify_audit`
  - Missing assertion: Stage09 viability failure must prevent completion.
- Stage10 verifier/test
  - Missing assertion: audit cannot be `complete=true` while embedded Stage10 status is `in_progress`.

Which Stage10 logic converted bad Stage09 output into a completed activation dossier?

- Stage10 `build_completion_audit` interpreted artifact existence and instruction coverage as sufficient.
- Stage10 `remaining_executable_actions_before_owner_activation` became empty when the artifact checklist passed.
- Stage10 `write_activation_dossier` carried the bad numbers into the activation dossier but did not classify them as failure.
- Stage10 `verify_audit` did not inspect profitability, selected count, missed winners, or collapse.

Why did the completion audit say complete=true while Stage10 was still in_progress inside stage_status_table?

Because the audit was written before the session state was updated. The sequence was:

1. build completion audit from current state;
2. write completion audit and dossier;
3. update session state to Stage10 complete.

The audit therefore captured stale embedded state. The test suite explicitly tolerated Stage10 still being `in_progress` inside the audit.

Why was that inconsistency committed?

Because the verifier/test did not fail it, and I treated the generated completion artifact as the end gate. That was an accountability failure. It should have been rejected manually even without a test.

### Replay comparison

Why did baseline/current shadow select 35,983 while new production mechanical selected 10?

Baseline/current shadow selected only the old route `FOLLOW` stream and did not apply the newly forced Stage09 production-mechanical gates. New production mechanical applied vNext AVOID pressure and prop-safe budget governance to the full generated candidate stream, including rows that were not true executable baseline opportunities. The prop model then ran one continuous account path across all historical candidates and exhausted the static overall cushion in early January 2022. After that, the static 10 percent floor blocked almost everything.

What exact decision deltas converted 35,983 selected baseline rows into 10 selected new rows?

- Baseline selected and new selected: `6`
- Baseline selected and new blocked: `35977`
- Baseline blocked and new selected: `4`
- Baseline blocked and new blocked: `217247`

All 35,977 baseline-selected rows that were blocked by the new mechanical scenario were blocked by the prop overall budget path, not by an evidence edge improvement.

Which baseline winners were blocked by the new system?

`15150` baseline-selected winners were blocked by new production mechanical.

Which baseline losers were correctly blocked by the new system?

`18689` baseline-selected losers were blocked by new production mechanical.

Was that net beneficial?

No. The baseline-selected rows blocked by new production mechanical had net R of approximately `+4011.831701R`. Blocking them destroyed the previous replay's positive result.

Which new selected 10 trades were chosen?

See Appendix D for the full selected-10 table. They were all `XAGUSD`, all in `2022-01-03` through `2022-01-05`, all from `OHLC_M1_CSV`, and they produced `2` wins and `8` losses.

Why did those 10 survive while 104,440 winners did not?

They were simply the earliest rows that made it through before the continuous one-account prop model exhausted the overall cushion. They are not evidence of a healthy selector. They are a broken residue after overblocking.

Were the selected 10 representative?

No. They are a non-representative early-history residue concentrated in one symbol and a three-day window.

Did replay scoring use as-of decision fields and post-decision outcome only for scoring?

Stage09 joined scoring fields after decision reconstruction in the replay loop. I found no direct evidence that the prop decision path consumed terminal outcomes/R labels. However, this does not make the replay valid: it still applied prop governance to the wrong stream and wrong account segmentation.

Did the replay compare current live-like config to new activated config fairly?

Only as an activated-hypothetical comparison over rehydrated Stage03/Stage04 traces. It was not a fair live-like production comparison because many runtime flags are default-off in `config/agent_config.yaml`, while Stage09's `activated_replay_config` forcibly flipped the replay flags on.

Did default-off flags cause the replay to measure a partial/non-real production system?

Yes. The live config defaults had `gtos_vnext_runtime.apply_to_execution:false`, `prop_safe_selector.apply_to_execution:false`, AI policy apply flags off, and LTF apply flags off. Stage09 forced activated replay behavior. That is a valid hypothetical only if the route clearly labels it as a failed activation candidate. It was not valid as a completion success.

Did `previous_hypothetical_activated` equal baseline because old activation logic was unchanged?

Yes. The aggregate numbers are identical:

- baseline/current shadow selected `35983`, total R `4008.331701256812`
- previous hypothetical activated selected `35983`, total R `4008.331701256812`

The skip reasons are also identical.

### Prop-safe selector

Why did `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget` hit 208,176 rows as a final skip reason?

Because the replay modeled one continuous 100k account across the entire 2022-2026 candidate universe. After early selected losses and large reserved/prospective risk pressure, current equity approached the static 90k overall floor. From that point onward, most later candidates projected below the overall cushion and were blocked. The final skip-reason count is `208176`; the raw prop action count for overall blocks in the new mechanical scenario is `216161`. The difference is skip-reason priority: some rows were already assigned `vnext_decision_avoid`, `pre_ai_skip_avoid_only`, or another earlier reason.

Did the selector model one account path sequentially across all 253,234 candidates?

Yes. Stage09 used one `ScenarioMetrics` equity path over the sorted replay stream. There was daily reset logic, but no challenge/account reset boundary.

Did the selector simulate simultaneous candidate stream, unrealistic trade frequency, or path ordering that makes the prop budget collapse artificially?

Yes. The candidate stream had up to `186` candidates at the same timestamp. The replay did not model realistic order routing, fill limits, live portfolio throttles, or independent challenge windows. Early selected trades were all single-count timestamps, so the first collapse was not caused only by simultaneous reservation, but the stream as a whole is still unrealistic for prop-budget evaluation.

Did it use candidate order across years as one continuous account instead of independent replay periods/evaluation windows?

Yes. There was no reset between years, months, challenge phases, or account windows.

Did it reset daily at GMT+3 correctly?

The code uses `00:00 GMT+3` reset windows, which is `05:00 Malaysia time`. The Stage05 tests covered this reset model. The daily reset formula itself is not the main failure.

Did it reset challenge/account state at any boundary?

No. That is the major modeling failure.

Was static 10 percent max loss applied from initial balance correctly?

The runtime formula is static: `max_loss_floor = initial_balance * 0.90`; remaining overall cushion is `current_equity - floor`. That matches the redacted_account-style instruction. The replay application was wrong because it ran one account forever.

Did intraday profit increase daily cushion correctly?

The runtime formula and Stage05 tests covered this. The +2 percent intraday profit case increased the 100k account daily cushion to about 7k. I did not find evidence that this formula was implemented as a trailing daily floor in runtime.

Did open risk, pending risk, correlation exposure, and new trade risk get included?

The runtime function includes parameters for open position risk, pending order risk, new trade SL risk, spread/slippage/commission buffer, correlation exposure buffer, concentration/session buffers, and reset-window state. Stage09's replay, however, populated open and pending risk mostly as zero and used synthetic replay approximations. That means runtime had the fields, but replay did not validate a realistic live exposure state.

Did it double-count risk from blocked/non-executed candidates?

I did not find evidence that blocked rows updated equity. However, Stage09 evaluated prop governance across all generated candidates, including non-executable rows. It also used simultaneous candidate count/reservation-like pressure. That is not equity double-counting, but it is denominator/stream misuse.

Did internal 4 percent GTOS overlay dominate?

No. In the production-mechanical scenario:

- external overall blocks: `216161` prop actions, `208176` final skip reasons
- internal overlay defers: `16` prop actions, `15` final skip reasons
- internal overlay reductions: `1`

The external 10 percent overall floor dominated.

Compare mechanical versus external-budget-only line by line.

They selected the same total count (`10`) and had the same total R (`-4.999959196997`). The difference was two rows:

- `cand_3a9a37aa2351cf99d78affef`: mechanical deferred under internal overlay; external-only selected it with reduced risk to external daily budget.
- `cand_66ad6a6a03cbbd5257e9d0a3`: mechanical selected it after an external overall reduction; external-only blocked it because the previous row changed the external-only equity path.

Why does external-budget-only still block 216,171 rows?

Because removing the internal 4 percent overlay does not fix the continuous one-account model. The external static overall cushion still gets exhausted and stays exhausted across years.

Is the prop selector acting as a safety governor or near-total trading suppressor?

Runtime function design is a budget governor. Stage09 replay usage turned it into a near-total suppressor.

Is the prop-safe logic correct but candidate stream unrealistic?

Partly. The redacted_account daily/overall formulas appear mostly correct. The replay candidate stream and account-window modeling are wrong for prop evaluation.

Is the candidate stream correct but prop-safe logic wrong?

The full generated candidate universe may be useful for diagnostics, but it is not correct as an executable prop-account stream. The prop-safe logic may still need replay repairs around reservations and reductions, but the biggest proven defect is applying it to the wrong continuous stream.

Is the replay missing account-window segmentation required for prop challenges?

Yes. This is mandatory for any meaningful pass/fail proxy.

### vNext decision pressure

Why did `vnext_decision_avoid` block 37,047 rows?

Because Stage09 rehydrated vNext route decisions and treated AVOID as a hard mechanical block in the activated scenario. These rows came from source-bound Stage05 dominance/evidence rows, especially `gtos_vnext_rejected_candidate_l2_value_mining` and null-family route pressure.

Which evidence families created those AVOIDs?

- `gtos_vnext_rejected_candidate_l2_value_mining`: `27192`
- `__NULL__`: `9855`

Which AVOID families saved actual losers?

Loser counts by family/component are in Appendix G. The only clearly net-useful component by R was `l2_m15_choch_rejection_value`, with total R of about `-52.890009` on the avoided set. Most other AVOID components blocked positive net R.

Which AVOID families blocked actual winners?

All families/components blocked winners. The AVOID set included `13073` missed winners overall.

Which AVOID families are stale/legacy/non-override but acted as hard pressure?

For the AVOID rows I joined to Stage05 dominance data, I found no evidence of stale legacy or broad unanchored rows dominating. The matched rows were source-bound. The problem was not stale legacy dominance; it was that many source-bound AVOID families were net harmful and got used as hard execution pressure.

Did legacy research override fresher evidence?

I did not find proof of stale legacy rows overriding source-bound evidence in the AVOID set. The broader replay still had `LEGACY` rows, but those were mostly routed into no-paid-AI fallback or prop evaluation rather than the AVOID block family.

Did broad unanchored rows dominate scoped rows?

No for the AVOID set joined to Stage05 dominance data. `broad_unanchored_rows=0`.

Did MIXED non-override context become hard avoid anywhere?

Not directly through `vnext_decision_avoid`. MIXED was not supposed to hard-block by config (`mixed_blocks_execution:false`). But MIXED did not produce selected trades in the production-mechanical scenario because the activated replay allowed prop and AI/no-paid policy to dominate, and because new mechanical route semantics did not cleanly preserve only executable FOLLOW rows.

Did row aggregation overweight duplicated artifacts?

For the AVOID IDs checked against Stage05 dominance rows, duplicate Stage05 rows for avoid IDs were `0`. That does not eliminate all artifact-weighting risk in the research corpus, but it rules out exact duplicate ID inflation for this specific AVOID join.

Did source-component vetoes fire too broadly?

Yes in outcome terms. Most AVOID components blocked positive net R sets, even when source-bound. That is too broad for hard execution pressure.

Did route selector/filter/router pressure become too harsh?

Yes. The hard AVOID block removed `37047` rows and included `13073` winners. It was less catastrophic than prop overblocking, but it was still not production-viable as a hard gate.

Did kill/redesign rows block more than intended?

The `rejected_candidate_*` families acted as hard pressure in Stage09. Several of those families had positive blocked R, so they need kill/redesign review before activation.

### Pre-AI and AI policy

Why did `pre_ai_skip_avoid_only` block 7,986 in new mechanical and 43,724 in baseline?

The 43,724 figure is the total pre-AI AVOID population. In new mechanical, skip-reason priority assigned many of those rows to `vnext_decision_avoid` first, leaving `7986` with final skip reason `pre_ai_skip_avoid_only`. This is a reason-priority difference, not proof that pre-AI behavior got safer.

What changed between baseline and new pre-AI behavior?

The underlying pre-AI decisions were rehydrated as:

- AVOID: `43724`
- FOLLOW: `39323`
- LEGACY: `166779`
- MIXED: `3408`

Baseline/current selected route `FOLLOW` rows. New mechanical added hard vNext AVOID and prop-safe evaluation over the broader stream.

Why did `new_ai_policy_no_paid_call` select 0 trades?

Because the no-paid-AI diagnostic policy did not mechanically resolve AI-required candidates into executable follows. It treated `CALL_AI_NARROWED_ROUTE` as blocked/no selection, skipped AVOID rows, and blocked legacy broad fallback rows. No candidate path became selected.

Does "no paid AI" mean all AI-required candidates are blocked instead of mechanically resolved?

In this replay scenario, yes. `CALL_AI_NARROWED_ROUTE` rows were not selected.

How many candidates require AI because of policy design rather than real ambiguity?

At least `39323` were marked `CALL_AI_NARROWED_ROUTE`. Of those, `35983` were route `FOLLOW` in the baseline/current shadow path. Those are policy-required AI calls under the replay design, not necessarily truly ambiguous trades.

How many candidates could be mechanical follow without AI?

The baseline/current selected count gives a lower-bound answer: `35983` route-FOLLOW candidates were mechanically selectable in the baseline/current replay.

How many MIXED rows were sent to AI, blocked by no-paid-call, or converted to non-override context?

Pre-AI `MIXED` count was `3408`; route `MIXED` count was `7634`. In no-paid AI, broad fallback and unresolved policy handling prevented these from producing selected trades.

Did malformed-response/supervisor logic suppress any candidate path?

No evidence in Stage09. The AI supervisor status joined in the replay was `HEALTHY` for all `253234` rows.

Did AI supervisor disable AI narrowing in a way that changed route outcomes?

No evidence from the replay. All rows had health checks passed. AI supervisor was not the collapse driver.

Is AI currently validator, blocker, tie-breaker, resolver, or unused logger in replay?

In Stage09:

- Baseline/current path effectively used route `FOLLOW` from rehydrated decisions.
- No-paid-AI scenario treated AI-required rows as non-selected.
- AI was not called live in Stage09; it acted as a replay policy category, not a fresh resolver.

### LTF / M1 / no-fill behavior

Did Stage06 LTF path awareness actually affect selection in Stage09?

Not materially. Stage09's LTF and pending actions were all `PLACE_LIMIT` across `253234` rows, so LTF path awareness did not become a selection-changing execution policy in Stage09.

How many candidates were changed by M1 path versus M15 close?

The Stage04 source comparison had `405729` M15-vs-LTF disagreement rows, covering `216331` unique candidate IDs. Across those disagreement rows:

- entry timing changed: `393221`
- simulated R changed: `131795`
- terminal outcome changed: `128918`

How many missed winners were M1 path-aware opportunities?

There were `90461` missed-winner rows in the M1 path-aware disagreement set.

How many stopped losers were caused by entering too late/too early versus route decision?

The existing artifacts prove large M15-vs-LTF terminal changes, but they do not fully assign causality to "late/early entry" versus route decision. That causal split must be part of the repair route.

Did `SKIP_LTF_NOFILL_AVOID`, pending policy, or no-fill source repair block material winners?

In Stage09, no. `ltf_action` and `pending_action` were `PLACE_LIMIT` for all rows. There was no material final skip reason from LTF no-fill or pending policy.

Did limit-vs-market conversion logic exist in replay or only logs?

The runtime/orchestrator code has LTF and execution paths, but Stage09 did not exercise meaningful limit-vs-market conversion. Stage09 replay actions were all `PLACE_LIMIT`.

Did the system still behave blind for 15-minute stretches anywhere?

The Stage04 data shows M1/M5/tick/Sierra path-aware disagreement versus M15. Stage09 did not convert that into selection behavior. So, for the production-mechanical replay, the LTF awareness was mostly a scoring/source diagnostic rather than an execution-changing policy.

Which source modes produced selected trades?

All 10 new production-mechanical selected trades used `OHLC_M1_CSV`.

Did tick/Sierra rows materially change decisions or only scoring?

In Stage09, tick/Sierra materially appeared in source/scoring coverage and disagreement diagnostics, but did not produce selected trades. It did not rescue the production-mechanical path.

### Data and scoring validity

Are the 253,234 candidates true candidate opportunities or all possible route-local generated candidates?

They are generated replay candidate rows, not a clean executable opportunity stream. This matters because prop budget was applied to rows that should not all be treated as executable account decisions.

Are off-KZ candidates included in selected/blocked counts?

Yes. `111762` off-KZ rows are in the universe. The new mechanical selected set included one off-KZ trade. Prop overall final skip reasons included `111755` off-KZ rows.

Did off-KZ rows distort prop budget and blocker counts?

Yes. Off-KZ rows were part of the prop-evaluated stream. Even if they were not all selected, including them in the governance path distorts blocker counts and any account pass proxy.

Are denominator rows and candidate rows joined correctly?

The row count joins were internally consistent enough for Stage09's row-count verifier to pass, and duplicate candidate IDs were not found in the checked Stage09 set. However, semantic validity is not guaranteed: denominator rows include generated rows that are not executable account candidates.

Are duplicate candidates collapsed correctly?

No exact duplicate candidate IDs were found in the checked Stage09 replay rows. That does not prove the upstream generated-candidate semantics are correct, only that the Stage09 rows were ID-unique.

Are repeated source artifacts double-counted?

For the AVOID-ID to Stage05 dominance join, duplicate matched rows were `0`. For the broader Stage04 LTF disagreement set, there are more disagreement rows than candidate IDs because multiple LTF modes can disagree for the same candidate. Those rows are useful diagnostics but must not be treated as independent trades.

Are R values source-bound or proxy?

Both exist. Stage09 source modes include M1, M5, M15, local tick parquet, Sierra converted M1 proxy, missing source, and ambiguous labels. The selected 10 were all M1 CSV. Tick/Sierra rows are source-bound/proxy depending on mode; Sierra appears as `SIERRA_SCID_CONVERTED_M1_PROXY`.

How many scoring rows used each source mode?

Universe source modes:

- `OHLC_M1_CSV`: `215610`
- `SIERRA_SCID_CONVERTED_M1_PROXY`: `17838`
- `MISSING_SOURCE`: `11631`
- `OHLC_M15_CSV`: `6183`
- `LOCAL_TICK_PARQUET`: `1650`
- `OHLC_M5_CSV`: `322`

How many rows used same-bar ambiguous labels?

Universe terminal outcomes include `same_bar_ambiguous_unresolved: 34`.

Did missing-source denominator rows affect selected counts?

Missing-source rows were included in the denominator and blocker counts. Baseline selected included `1894` missing-source rows; new selected included none. This is another reason selected/performance counts must be separated from denominator coverage.

Are spreads/costs included consistently?

Stage09 prop selector used a spread/slippage/commission buffer in account-state inputs, but scoring R consistency across all source modes needs a dedicated audit. The current forensic pass does not prove cost consistency across M1/M5/tick/Sierra/OHLC proxy modes.

Is final equity calculation meaningful?

No for production interpretation. It is distorted by one continuous account over an enormous historical generated-candidate stream. It is useful only as a diagnostic showing the replay model collapsed.

Is pass/fail proxy meaningful on a 253k-candidate continuous replay?

No. It requires account/challenge-window segmentation.

### Completion failure

Why did Stage09 verifier only check row count/scenario/leakage/math and not production viability?

Because the Stage09 verifier was written as an artifact correctness check, not a production viability gate. That was wrong for this route.

Why did Stage10 audit mark remaining executable actions empty when the replay revealed overblocking?

Because Stage10 checked whether requested artifacts existed and whether instruction-coverage keys were populated. It did not check whether metrics meant the candidate failed.

Did "owner-gated activation" language hide the candidate failure?

Yes. It correctly said no broker mutation occurred, but it obscured the more important point: the activated candidate was not safe to approve.

Did "no live trading/broker mutation" become an excuse to call bad runtime behavior complete?

Functionally, yes. It reduced the gate to "not activated yet" instead of "activation candidate passed viability."

Did the session drift into artifact completion instead of system-quality completion?

Yes.

Did the prompt lack an explicit bad-result repair gate?

No. The prompt had enough language to require repair. The missing piece was enforcement in Stage09/Stage10 and my manual decision to stop.

Did this need an additional Stage11 failure-anatomy/repair stage?

Yes. After Stage09, the correct route was a Stage11 failure-anatomy/repair stage, not Stage10 completion.

What exact assertions must be added?

See "Assertions That Must Be Added" above. The short version is: production viability must be a hard gate, not an optional dossier metric.

## Appendix B - Complete Scenario Metrics Snapshot

These are the key scenario aggregates from the inspected Stage09 metrics.

| Scenario | Selected | Performance Count | Total R | Expectancy | WR | PF | Missed Winners | Avoided Losers | Blocked Trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline/current shadow | 35,983 | 33,845 | 4008.331701256812 | 0.118432019538 | 0.447658442901 | 1.214657122925 | 89,291 | 116,614 | not applicable |
| previous hypothetical activated | 35,983 | 33,845 | 4008.331701256812 | 0.118432019538 | 0.447658442901 | 1.214657122925 | 89,291 | 116,614 | not applicable |
| new production mechanical | 10 | 10 | -4.999959196997 | -0.4999959197 | 0.2 | 0.375005100375 | 104,440 | 135,300 | 216,161 |
| external-budget-only | 10 | 10 | -4.999959196997 | -0.4999959197 | 0.2 | 0.375005100375 | not separately meaningful | not separately meaningful | 216,171 |
| new AI policy no paid call | 0 | 0 | 0 | null | null | null | not meaningful | not meaningful | 213,911 avoided/nonselected |

The baseline/current and previous hypothetical activated scenarios are identical. The new production-mechanical and external-budget-only scenarios are also performance-identical, despite two row-level differences.

## Appendix C - Complete Nonzero Skip Reason Tables

### Baseline/current shadow and previous hypothetical activated

| Skip Reason | Count |
|---|---:|
| `route_legacy_not_follow` | 166,779 |
| `pre_ai_skip_avoid_only` | 43,724 |
| `route_mixed_not_follow` | 4,198 |
| `route_avoid_not_follow` | 1,309 |
| `risk_zero` | 1,241 |

### New production mechanical

| Skip Reason | Count |
|---|---:|
| `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget` | 208,176 |
| `vnext_decision_avoid` | 37,047 |
| `pre_ai_skip_avoid_only` | 7,986 |
| `prop_safe_selector_defer_until_reset_gtos_internal_daily_overlay_budget` | 15 |

### External-budget-only

| Skip Reason | Count |
|---|---:|
| `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget` | 208,177 |
| `vnext_decision_avoid` | 37,047 |
| `pre_ai_skip_avoid_only` | 7,986 |
| `prop_safe_selector_block_redacted_account_external_daily_5pct_budget` | 9 |
| `prop_safe_selector_defer_until_reset_redacted_account_external_daily_5pct_budget` | 5 |

### New AI policy no paid call

| Skip Reason | Count |
|---|---:|
| `no_paid_ai_block_legacy_broad_fallback` | 170,187 |
| `no_paid_ai_call_ai_narrowed_route` | 39,323 |
| `no_paid_ai_skip_ai_mechanical_avoid` | 43,724 |

## Appendix D - The New Selected 10 Trades

All selected production-mechanical trades were `XAGUSD`, `OHLC_M1_CSV`, and occurred in the first three replay days.

| # | Candidate ID | Time UTC | Symbol | Session | Side | Framework | Baseline Selected | Baseline Skip | Route | Prop Action | Prop Reason | Risk Pct | R |
|---:|---|---|---|---|---|---|---|---|---|---|---|---:|---:|
| 1 | `cand_9c376be242e851c60b173d49` | 2022-01-03T10:00 | XAGUSD | london | LONG | breaker | true | null | FOLLOW | ALLOW | budget_allows | 2.5 | -1.0 |
| 2 | `cand_a14d9bf4261106d01e5b0b84` | 2022-01-03T11:30 | XAGUSD | london | LONG | fvg | true | null | FOLLOW | REDUCE_RISK | reduce_to_gtos_internal_daily_overlay_budget | 1.438461538462 | -1.0 |
| 3 | `cand_30ae8cb2567e83b3df6ca4f6` | 2022-01-04T02:00 | XAGUSD | tokyo | LONG | ob | false | route_legacy_not_follow | LEGACY | ALLOW | budget_allows | 2.0 | -1.0 |
| 4 | `cand_b26fdd7e6cc2ba4bb7ef266e` | 2022-01-04T06:30 | XAGUSD | off_kz | LONG | ob | false | route_legacy_not_follow | LEGACY | ALLOW | budget_allows | 2.0 | +1.500040803 |
| 5 | `cand_c9ae3f81c827b423349b0f73` | 2022-01-04T08:45 | XAGUSD | london | LONG | fvg | true | null | FOLLOW | ALLOW | budget_allows | 2.5 | -1.0 |
| 6 | `cand_7eb02ca78af9520ab4cff081` | 2022-01-04T09:45 | XAGUSD | london | LONG | breaker | true | null | FOLLOW | ALLOW | budget_allows | 2.5 | +1.5 |
| 7 | `cand_4a1778758fb33fc6b1c18241` | 2022-01-04T10:00 | XAGUSD | london | LONG | ob | true | null | FOLLOW | ALLOW | budget_allows | 2.0 | -1.0 |
| 8 | `cand_3385813009afec97fcd5e43d` | 2022-01-04T13:00 | XAGUSD | ny | SHORT | ob | false | risk_zero | FOLLOW | ALLOW | budget_allows | 2.0 | -1.0 |
| 9 | `cand_7f7b7490d8eef0438d22525b` | 2022-01-04T13:15 | XAGUSD | ny | SHORT | ob | false | risk_zero | FOLLOW | ALLOW | budget_allows | 2.0 | -1.0 |
| 10 | `cand_66ad6a6a03cbbd5257e9d0a3` | 2022-01-05T08:45 | XAGUSD | london | LONG | breaker | true | null | FOLLOW | REDUCE_RISK | reduce_to_redacted_account_external_overall_10pct_static_budget | 2.446862167245 | -1.0 |

Prop projections for the selected set:

| Candidate ID | Remaining Daily Cushion Before | Projected Daily Cushion | Remaining Overall Cushion Before | Projected Overall Cushion |
|---|---:|---:|---:|---:|
| `cand_9c376be242e851c60b173d49` | 5000.000 | 2400.000 | 10000.000 | 7400.000 |
| `cand_a14d9bf4261106d01e5b0b84` | 2500.000 | -35.000 | 7500.000 | 4965.000 |
| `cand_30ae8cb2567e83b3df6ca4f6` | 5000.000 | 2981.953 | 6097.500 | 4079.453 |
| `cand_b26fdd7e6cc2ba4bb7ef266e` | 3078.050 | 1100.363 | 4175.550 | 2197.863 |
| `cand_c9ae3f81c827b423349b0f73` | 5903.393 | 3381.370 | 7000.893 | 4478.870 |
| `cand_7eb02ca78af9520ab4cff081` | 3478.371 | 1019.398 | 4575.871 | 2116.898 |
| `cand_4a1778758fb33fc6b1c18241` | 7024.966 | 4964.394 | 8122.466 | 6061.894 |
| `cand_3385813009afec97fcd5e43d` | 5062.517 | 3043.157 | 6160.017 | 4140.657 |
| `cand_7f7b7490d8eef0438d22525b` | 3139.317 | 1160.343 | 4236.817 | 2257.843 |
| `cand_66ad6a6a03cbbd5257e9d0a3` | 5000.000 | 2598.846 | 2352.080 | -49.074 |

This table is the clearest proof that the selected 10 were not a healthy cross-market selection. They are an early path residue.

## Appendix E - Exact Row Examples By Category

### Selected winners

- `cand_b26fdd7e6cc2ba4bb7ef266e`
  - time: `2022-01-04T06:30`
  - symbol/session/side/framework: `XAGUSD / off_kz / LONG / ob`
  - source: `OHLC_M1_CSV`
  - baseline selected: false
  - baseline skip: `route_legacy_not_follow`
  - new route: `LEGACY`
  - new prop action: `ALLOW`
  - R: `+1.500040803`

- `cand_7eb02ca78af9520ab4cff081`
  - time: `2022-01-04T09:45`
  - symbol/session/side/framework: `XAGUSD / london / LONG / breaker`
  - source: `OHLC_M1_CSV`
  - baseline selected: true
  - new route: `FOLLOW`
  - new prop action: `ALLOW`
  - R: `+1.5`

### Selected losers

- `cand_9c376be242e851c60b173d49`
  - time: `2022-01-03T10:00`
  - symbol/session/side/framework: `XAGUSD / london / LONG / breaker`
  - baseline selected: true
  - new route: `FOLLOW`
  - prop action: `ALLOW`
  - R: `-1`

- `cand_66ad6a6a03cbbd5257e9d0a3`
  - time: `2022-01-05T08:45`
  - symbol/session/side/framework: `XAGUSD / london / LONG / breaker`
  - baseline selected: true
  - new route: `FOLLOW`
  - prop action: `REDUCE_RISK`
  - prop reason: `reduce_to_redacted_account_external_overall_10pct_static_budget`
  - projected overall cushion: `-49.0739`
  - R: `-1`

### Missed winners

- `cand_e9e17abd300afd2804223fbc`
  - time: `2022-01-03T17:00`
  - symbol/session/side/framework: `XAGUSD / off_kz / LONG / ob`
  - baseline skip: `route_legacy_not_follow`
  - new skip: `prop_safe_selector_defer_until_reset_gtos_internal_daily_overlay_budget`
  - R: `+1.499994990`

- `cand_e364d2a758634caa75e4ce10`
  - time: `2022-01-03T07:30`
  - symbol/session/side/framework: `XAGUSD / london / SHORT / ob`
  - baseline skip: `pre_ai_skip_avoid_only`
  - new skip: `vnext_decision_avoid`
  - R: `+1.499984523`

- `cand_e4fe254a12cf6c5345350166`
  - time: `2022-10-26T11:00`
  - symbol/session/side/framework: `US30_cash / london / LONG / ob`
  - baseline skip: `route_avoid_not_follow`
  - new skip: `vnext_decision_avoid`
  - R: `+1.5`

### Avoided losers

- `cand_3385813009afec97fcd5e43d`
  - time: `2022-01-04T13:00`
  - symbol/session/side/framework: `XAGUSD / ny / SHORT / ob`
  - baseline skip: `risk_zero`
  - new selected: true
  - R: `-1`
  - This is an example of a row that baseline avoided but new mechanical selected.

- `cand_3a9a37aa2351cf99d78affef`
  - time: `2022-01-04T02:15`
  - symbol/session/side/framework: `XAGUSD / tokyo / LONG / ob`
  - mechanical action: deferred by internal overlay
  - external-only action: selected with reduced external daily risk
  - R: `-1`

### Prop-blocked winners

The prop block set includes many winners. The most important aggregate is that `15150` baseline-selected winners were blocked by the new production-mechanical scenario, while the blocked baseline-selected set was net `+4011.831701R`.

Representative prop-blocked winner:

- `cand_e9e17abd300afd2804223fbc`
  - R: `+1.499994990`
  - demonstrates an early profitable row not selected by the new production-mechanical path.

## Appendix F - Universe And Baseline Selected Distributions

### Universe by session

| Session | Count |
|---|---:|
| london | 58,842 |
| ny | 56,920 |
| off_kz | 111,762 |
| tokyo | 25,710 |

### Universe by source mode

| Source Mode | Count |
|---|---:|
| `OHLC_M1_CSV` | 215,610 |
| `SIERRA_SCID_CONVERTED_M1_PROXY` | 17,838 |
| `MISSING_SOURCE` | 11,631 |
| `OHLC_M15_CSV` | 6,183 |
| `LOCAL_TICK_PARQUET` | 1,650 |
| `OHLC_M5_CSV` | 322 |

### Universe by terminal outcome

| Terminal Outcome | Count |
|---|---:|
| `stop_first` | 132,851 |
| `target_first` | 101,477 |
| `missing_source_denominator_excluded` | 11,631 |
| `timeout` | 5,424 |
| `no_fill` | 1,817 |
| `same_bar_ambiguous_unresolved` | 34 |

### Baseline selected by symbol

| Symbol | Baseline Selected |
|---|---:|
| GBPJPY | 10,099 |
| GBPUSD | 7,099 |
| US30_cash | 5,961 |
| XAUUSD | 3,465 |
| XAGUSD | 3,223 |
| USDJPY | 2,778 |
| NAS100 | 2,745 |
| EURUSD | 613 |

### Baseline selected by session

| Session | Baseline Selected |
|---|---:|
| london | 17,188 |
| ny | 16,580 |
| tokyo | 2,215 |

### Baseline selected by side

| Side | Baseline Selected |
|---|---:|
| LONG | 32,182 |
| SHORT | 3,801 |

### Baseline selected by framework

| Framework | Baseline Selected |
|---|---:|
| fvg | 16,431 |
| breaker | 11,046 |
| ob | 8,506 |

### Baseline selected by source mode

| Source Mode | Baseline Selected |
|---|---:|
| `OHLC_M1_CSV` | 31,024 |
| `SIERRA_SCID_CONVERTED_M1_PROXY` | 2,478 |
| `MISSING_SOURCE` | 1,894 |
| `OHLC_M15_CSV` | 305 |
| `LOCAL_TICK_PARQUET` | 230 |
| `OHLC_M5_CSV` | 52 |

### Baseline selected by terminal outcome

| Terminal Outcome | Baseline Selected |
|---|---:|
| `stop_first` | 18,662 |
| `target_first` | 15,108 |
| `missing_source_denominator_excluded` | 1,894 |
| `no_fill` | 241 |
| `timeout` | 75 |
| `same_bar_ambiguous_unresolved` | 3 |

## Appendix G - vNext AVOID Evidence Breakdown

Stage09 `vnext_decision_avoid` final skip reason count: `37047`.

Stage05 dominance join:

- avoid IDs: `37047`
- matched IDs: `37047`
- missing IDs: `0`
- duplicate Stage05 rows for avoid IDs: `0`

Family counts:

| Family | Count |
|---|---:|
| `gtos_vnext_rejected_candidate_l2_value_mining` | 27,192 |
| `__NULL__` | 9,855 |

Component counts:

| Component | Count |
|---|---:|
| `__NULL__` | 9,855 |
| `rejected_candidate_blocked_limit_value` | 6,408 |
| `rejected_candidate_prescreen_no_direction_value` | 4,608 |
| `rejected_candidate_ob_proximity_value` | 4,037 |
| `rejected_candidate_c3_direction_mismatch_value` | 3,187 |
| `rejected_candidate_other_unknown_value` | 3,111 |
| `rejected_candidate_c1_failed_value` | 2,433 |
| `l2_m15_choch_rejection_value` | 1,256 |
| `l2_h1_poi_rejection_value` | 1,109 |
| `l2_entry_in_ob_rejection_value` | 1,043 |

Component outcome/R classes:

| Component | Losers Avoided | Winners Missed | Null/Other | R Sum On Avoided Set |
|---|---:|---:|---:|---:|
| `__NULL__` | 5,401 | 4,056 | 398 | +680.486827 |
| `l2_entry_in_ob_rejection_value` | 606 | 416 | 21 | +18.000001 |
| `l2_h1_poi_rejection_value` | 591 | 480 | 38 | +129.000552 |
| `l2_m15_choch_rejection_value` | 761 | 471 | 24 | -52.890009 |
| `rejected_candidate_blocked_limit_value` | 3,169 | 2,834 | 405 | +1081.045633 |
| `rejected_candidate_c1_failed_value` | 1,245 | 1,058 | 130 | +339.820526 |
| `rejected_candidate_c3_direction_mismatch_value` | 1,827 | 1,270 | 90 | +76.059685 |
| `rejected_candidate_ob_proximity_value` | 2,145 | 1,703 | 189 | +402.171086 |
| `rejected_candidate_other_unknown_value` | 1,596 | 1,295 | 220 | +344.496689 |
| `rejected_candidate_prescreen_no_direction_value` | 2,400 | 1,924 | 284 | +484.573959 |

Interpretation:

- A hard AVOID gate should have negative R sum on the avoided set if it is beneficial.
- Only `l2_m15_choch_rejection_value` showed a negative avoided-set R sum in this breakdown.
- Most AVOID components were net harmful if treated as hard blockers.

Pollution checks on joined AVOID rows:

- broad unanchored rows: `0`
- stale legacy rows: `0`
- source required rows: `0`
- duplicate avoid IDs: `0`

This means the problem is not simply stale/broad pollution. The source-bound evidence itself was not viable as hard pressure at the thresholds used.

## Appendix H - Prop Selector Action Breakdown

### New production mechanical prop actions

| Prop Action | Count |
|---|---:|
| ALLOW | 37,055 |
| BLOCK | 216,161 |
| DEFER | 16 |
| REDUCE_RISK | 2 |

### New production mechanical prop reasons

| Prop Reason | Count |
|---|---:|
| `redacted_account_external_overall_10pct_static_budget` block | 216,161 |
| `budget_allows` | 37,055 |
| `gtos_internal_daily_overlay_budget` defer | 16 |
| `reduce_to_redacted_account_external_overall_10pct_static_budget` | 1 |
| `reduce_to_gtos_internal_daily_overlay_budget` | 1 |

### External-budget-only prop actions

| Prop Action | Count |
|---|---:|
| ALLOW | 37,054 |
| BLOCK | 216,171 |
| DEFER | 6 |
| REDUCE_RISK | 3 |

### External-budget-only prop reasons

| Prop Reason | Count |
|---|---:|
| `redacted_account_external_overall_10pct_static_budget` block | 216,162 |
| `budget_allows` | 37,054 |
| `redacted_account_external_daily_5pct_budget` block | 9 |
| `redacted_account_external_daily_5pct_budget` defer | 6 |
| `reduce_to_redacted_account_external_daily_5pct_budget` | 3 |

### Prop overall action count by terminal outcome

For mechanical prop action overall blocks:

| Terminal Outcome | Count |
|---|---:|
| stop | 113,121 |
| target | 86,000 |
| missing | 10,184 |
| timeout | 5,357 |
| no_fill | 1,477 |
| same_bar | 22 |

This is another proof that prop overall blocking was not selectively avoiding losers. It blocked `86,000` target outcomes in the prop-action overall-block set.

## Appendix I - Pre-AI And No-Paid-AI Breakdown

Pre-AI decisions:

| Decision | Count |
|---|---:|
| LEGACY | 166,779 |
| AVOID | 43,724 |
| FOLLOW | 39,323 |
| MIXED | 3,408 |

Pre-AI actions:

| Action | Count |
|---|---:|
| ALLOW_AI | 170,187 |
| SKIP | 43,724 |
| NARROW_AI_TO_SIDE | 39,323 |

Route decisions:

| Route Decision | Count |
|---|---:|
| LEGACY | 166,779 |
| FOLLOW | 41,774 |
| AVOID | 37,047 |
| MIXED | 7,634 |

AI policy actions:

| AI Policy Action | Count |
|---|---:|
| BLOCK_LEGACY_BROAD_FALLBACK | 170,187 |
| SKIP_AI_MECHANICAL_AVOID | 43,724 |
| CALL_AI_NARROWED_ROUTE | 39,323 |

AI replay roles:

| Role | Count |
|---|---:|
| general_trade_decision | 166,779 |
| vnext_avoid_blocker_classifier | 43,724 |
| vnext_side_validator | 39,323 |
| vnext_evidence_triage | 3,408 |

AI supervisor:

- `253234 / 253234` rows had health status `HEALTHY`.
- Supervisor did not drive the collapse.

Cross-tab summary:

| Pre-AI Decision | Pre-AI Action | AI Action | Route Decision | Count |
|---|---|---|---|---:|
| AVOID | SKIP | SKIP_AI_MECHANICAL_AVOID | AVOID | 35,738 |
| AVOID | SKIP | SKIP_AI_MECHANICAL_AVOID | FOLLOW | 4,550 |
| AVOID | SKIP | SKIP_AI_MECHANICAL_AVOID | MIXED | 3,436 |
| FOLLOW | NARROW_AI_TO_SIDE | CALL_AI_NARROWED_ROUTE | AVOID | 1,309 |
| FOLLOW | NARROW_AI_TO_SIDE | CALL_AI_NARROWED_ROUTE | FOLLOW | 35,983 |
| FOLLOW | NARROW_AI_TO_SIDE | CALL_AI_NARROWED_ROUTE | MIXED | 2,031 |
| LEGACY | ALLOW_AI | BLOCK_LEGACY_BROAD_FALLBACK | LEGACY | 166,779 |
| MIXED | ALLOW_AI | BLOCK_LEGACY_BROAD_FALLBACK | FOLLOW | 1,241 |
| MIXED | ALLOW_AI | BLOCK_LEGACY_BROAD_FALLBACK | MIXED | 2,167 |

The no-paid-AI scenario selecting zero trades is therefore not a trading result. It is a policy diagnostic showing that the no-paid path has no mechanical resolver.

## Appendix J - LTF / M1 / M5 / Tick-Sierra Details

Stage09:

- `ltf_action=PLACE_LIMIT` for all `253234` rows.
- `pending_action=PLACE_LIMIT` for all `253234` rows.
- selected production-mechanical trades by source mode: all `OHLC_M1_CSV`.

Stage04 M15-vs-LTF disagreement:

- disagreement rows: `405729`
- unique candidate IDs covered: `216331`
- entry timing changed: `393221`
- simulated R changed: `131795`
- terminal outcome changed: `128918`

Disagreement rows by LTF mode:

| LTF Mode | Count |
|---|---:|
| m1_path_aware | 211,410 |
| m5_path_aware | 148,893 |
| tick_or_sierra_path_aware | 45,426 |

Stage09 skip reason on disagreement rows:

| Stage09 Result/Reason | Count |
|---|---:|
| prop overall block | 331,438 |
| vNext decision avoid | 60,979 |
| pre-AI skip | 13,266 |
| internal overlay defer | 28 |
| selected | 18 |

Baseline/new selected transition on disagreement rows:

| Baseline Selected | New Selected | Count |
|---|---|---:|
| false | false | 349,063 |
| false | true | 7 |
| true | false | 56,648 |
| true | true | 11 |

M15 terminal to LTF terminal pairs:

| M15 Terminal | LTF Terminal | Count |
|---|---|---:|
| no_fill | same_bar | 11 |
| no_fill | stop | 98 |
| no_fill | target | 470 |
| no_fill | timeout | 97 |
| same_bar | no_fill | 4,318 |
| same_bar | same_bar | 7,008 |
| same_bar | stop | 29,313 |
| same_bar | target | 14,383 |
| same_bar | timeout | 28 |
| stop | no_fill | 11,591 |
| stop | same_bar | 588 |
| stop | stop | 122,778 |
| stop | target | 7,065 |
| stop | timeout | 174 |
| target | no_fill | 15,227 |
| target | same_bar | 1,345 |
| target | stop | 43,513 |
| target | target | 137,792 |
| target | timeout | 371 |
| timeout | no_fill | 163 |
| timeout | stop | 93 |
| timeout | target | 70 |
| timeout | timeout | 9,233 |

Stage04 terminal counts by scoring/source mode:

| Source Mode | Missing | No Fill | Same Bar | Stop | Target | Timeout |
|---|---:|---:|---:|---:|---:|---:|
| bar_close_m15 | 0 | 8,759 | 29,939 | 93,505 | 115,985 | 5,046 |
| m1_path_aware | 5,655 | 10,227 | 5,186 | 128,723 | 98,282 | 5,161 |
| m5_path_aware | 5,655 | 10,173 | 13,101 | 113,968 | 105,220 | 5,117 |
| tick_or_sierra_path_aware | 206,309 | 28,834 | 454 | 10,776 | 6,600 | 261 |

Interpretation:

- LTF path awareness is real in the data.
- Stage09 did not use it as a material execution selector.
- The repair route must separate "better scoring label" from "changed executable behavior".

## Appendix K - Simultaneous Candidate Density

The replay stream included many same-timestamp candidate clusters. Candidate-count-per-timestamp distribution:

| Candidates At Same Timestamp | Timestamp Count |
|---:|---:|
| 1 | 26,365 |
| 2 | 18,801 |
| 3 | 11,766 |
| 4 | 7,201 |
| 5 | 4,087 |
| 6 | 2,681 |
| 7 | 1,663 |
| 8 | 1,365 |
| 9 | 930 |
| 10 | 753 |
| 11 | 561 |
| 12 | 467 |
| 13 | 392 |
| 14 | 309 |
| 15 | 252 |
| 16 | 217 |
| 17 | 167 |
| 18 | 136 |
| 19 | 114 |
| 20 | 92 |
| 21 | 66 |
| 22 | 64 |
| 23 | 46 |
| 24 | 27 |
| 25 | 35 |
| 26 | 29 |
| 27 | 29 |
| 28 | 21 |
| 29 | 20 |
| 30 | 13 |
| 31 | 13 |
| 32 | 9 |
| 33 | 7 |
| 34 | 11 |
| 35 | 6 |
| 36 | 4 |
| 37 | 5 |
| 38 | 3 |
| 39 | 3 |
| 40 | 2 |
| 41 | 3 |
| 42 | 3 |
| 43 | 5 |
| 45 | 3 |
| 46 | 1 |
| 47 | 1 |
| 49 | 2 |
| 52 | 2 |
| 53 | 1 |
| 54 | 1 |
| 59 | 1 |
| 62 | 2 |
| 64 | 1 |
| 65 | 1 |
| 66 | 1 |
| 78 | 1 |
| 88 | 1 |
| 94 | 1 |
| 186 | 1 |

Interpretation:

- The stream is not a live-account order stream.
- A prop budget governor cannot treat every generated candidate in these clusters as an independent real execution opportunity without extra portfolio/order-routing modeling.

## Appendix L - Code Responsibility Index

This section lists the files/functions responsible for each major behavior. Line numbers should be rechecked by the next session if files move, but these are the inspected code paths.

### Stage09 builder

File:

- `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/build_vnext_production_change_stage09_forward_replay_2026_05_25.py`

Responsible code paths:

- `activated_replay_config`
  - forcibly enabled activated replay flags rather than using live default-off behavior.
- `select_better_score`
  - chose scoring source/R labels by non-null R and source priority.
- `selected_from_previous`
  - baseline/current selection required old route `FOLLOW`.
- `reset_window_start_utc`
  - implemented GMT+3 daily reset boundary.
- `ScenarioMetrics._roll_day`
  - rolled daily reset only; no account/challenge reset.
- `ScenarioMetrics.add`
  - accumulated one continuous equity path and broad coverage counts.
- `account_state_for_selector`
  - supplied replay account state to the prop selector; open/pending/correlation mostly synthetic/zero.
- replay loop
  - reconstructed current/hyp baseline, pre-AI, route, prop, and mechanical scenarios.
- mechanical selected logic
  - allowed selection when not blocked/deferred by the activated gates; this did not cleanly preserve "FOLLOW-only executable" semantics.
- output row writing
  - wrote decision fields and post-decision scoring fields into shard rows.
- `verify_summary`
  - checked rows/scenarios/leakage/math but not production viability.

Missing assertion:

- Stage09 should fail or mark `production_candidate_failed=true` when selected count collapses, expectancy is negative, PF is below 1, missed winners explode, or prop block ratio is pathological.

### Stage09 verifier/test

File:

- `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/test_vnext_production_change_stage09_forward_replay_2026_05_25.py`

Responsible function:

- `test_verify_summary_requires_all_scenarios_and_redacted_account_math`

Failure:

- The test explicitly permitted zero-selection, zero-R scenarios to pass.

### Stage10 builder

File:

- `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/build_vnext_production_change_stage10_completion_audit_2026_05_25.py`

Responsible code paths:

- `build_completion_audit`
  - artifact/instruction coverage became the completion criterion.
- `remaining_executable_actions_before_owner_activation`
  - became `[]` if artifact checklist passed.
- `write_activation_dossier`
  - carried bad metrics but did not classify activation as unsafe.
- `verify_audit`
  - did not check selected count, expectancy, PF, missed winners, or Stage09 failure.
- write order
  - wrote audit before updating session state, causing embedded Stage10 `in_progress` inconsistency.

### Stage10 verifier/test

File:

- `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/test_vnext_production_change_stage10_completion_audit_2026_05_25.py`

Failure:

- Allowed Stage10 `in_progress` inside a complete audit.
- Checked coverage and row counts, not viability.

### Runtime prop selector

File:

- `src/components/gtos_vnext_runtime.py`

Responsible functions:

- `evaluate_vnext_prop_safe_selector`
  - redacted_account external daily/overall budget math.
  - Internal 4 percent overlay separation.
  - ALLOW/REDUCE_RISK/DEFER_UNTIL_RESET/BLOCK decisions.
- `vnext_execution_block_reason`
  - Converts vNext route decisions into execution block reasons.

Important distinction:

- Runtime math mostly matches the one-time redacted_account spec.
- Stage09 replay application mis-modeled the account stream and segmentation.

### Orchestrator/runtime integration

File:

- `src/components/orchestrator.py`

Responsible paths:

- vNext block path
- LTF path
- prop selector pre-execution path
- open/pending/correlation account state assembly

Important distinction:

- Live config default flags were off. Stage09 activated replay forced them on.

### Execution

File:

- `src/components/execution.py`

Relevant fields:

- vNext/prop/LTF telemetry on order requests/pending intents.

Finding:

- No evidence that execution caused the replay collapse. Collapse was Stage09 governance/modeling.

### AI supervisor

File:

- `src/components/ai_supervisor.py`

Finding:

- No evidence of AI supervisor suppressing candidates in Stage09. Replay health status was healthy for all rows.

### Primary analyzer

File:

- `src/components/primary_analyzer.py`

Finding:

- Malformed-response/no-trade logic exists, but Stage09 replay did not show malformed/supervisor suppression as a collapse cause.

## Appendix M - Config State Relevant To Activation Safety

File:

- `config/agent_config.yaml`

Relevant settings observed:

- `gtos_vnext_runtime.apply_to_execution: false`
- AI policy apply flags default off
- LTF apply flag default off
- prop-safe selector apply flag default off
- redacted_account external daily: `5%`
- redacted_account external overall: `10%`
- reset timezone: GMT+3, reset at 00:00 GMT+3
- internal GTOS overlay: `4%` daily
- `avoid_blocks_execution: true`
- `mixed_blocks_execution: false`
- `legacy_blocks_execution: false`

Implication:

- The committed runtime changes are disabled by config, but they are unsafe to activate as-is.

## Appendix N - Stage05 Warning That Was Missed

Stage05 already contained warning signs:

- Prop replay breach rows: `24`
- deterministic pass rows: `0`
- max drawdown pct: `1645.26403930573`
- max loss streak: `54`
- max trades per day: `931`
- trade count minimum/maximum in upstream prop replay: `29952` to `210975`

Stage05 tests verified pieces of the redacted_account budget math, including reset and +2 percent intraday cushion, but did not fail on the absurd replay-level risk profile. This was an early missed gate. The correct response at Stage05 was: formula test passes, but replay stream/account model is not viable.

## Appendix O - Known Ambiguities That Must Be Pursued In Repair

The following are not excuses. They are explicit open items that must be resolved before any next activation attempt.

1. Cost consistency across source modes:
   - Need a dedicated audit for spread/slippage/commission treatment across M1, M5, M15, local tick, and Sierra proxy rows.
2. Exact causal split for LTF changes:
   - Need to classify stopped losers by too-early entry, too-late entry, route decision, no-fill, and same-bar ambiguity.
3. True executable candidate stream:
   - Need to separate generated route-local candidates from account-executable opportunities.
4. Account/challenge segmentation:
   - Need redacted_account-style Phase 1/Phase 2 windows, reset boundaries, and independent account paths.
5. Off-KZ handling:
   - Need to decide whether off-KZ rows are diagnostics only or executable candidates. They must not silently consume prop budget.
6. Baseline fairness:
   - Need an ablation where prop governance applies only to baseline executable selected rows, then to new executable selected rows.
7. AVOID family viability:
   - Need per-family promotion gates. Net-positive avoided-set R means the hard blocker is harmful.
8. AI no-paid-call semantics:
   - Need a mechanical resolver for AI-required rows or the no-paid scenario must be labeled as diagnostic non-trading.
9. Stage10 state write order:
   - Need audit after final state update, or audit must explicitly mark itself pre-final.
10. Dossier language:
   - Must distinguish "measured failed candidate" from "completed production change".

## Appendix P - Exact Repair Route Required Next

The next route should be named and scoped as a failure-anatomy/repair route, not a new route that restarts Stage00-04. It should consume the existing Stage09 shards and metrics as evidence.

Required phases:

1. Freeze current artifacts:
   - Preserve Stage09 shards, summary, ledger, dossier, session state, and this report.
   - Do not activate runtime flags.
2. Add failure classification:
   - Add `production_candidate_failed=true` to Stage09/Stage10 derived state when viability gates fail.
3. Repair replay semantics:
   - Prop selector only sees executable streams.
   - Account windows are segmented.
   - Off-KZ generated rows are diagnostic unless explicitly executable.
   - `LEGACY`/`MIXED` are not selected by absence of a block.
4. Build ablation matrix:
   - baseline current;
   - baseline + prop only;
   - baseline + vNext AVOID only;
   - baseline + LTF execution only;
   - new route without prop;
   - new route with prop on executable stream;
   - no-paid-AI diagnostic separately.
5. Add viability verifiers:
   - selected count/frequency;
   - expectancy/PF;
   - missed winners;
   - non-collapse versus baseline;
   - selected-only coverage;
   - prop block ratio;
   - account-window pass proxy.
6. Re-evaluate blocker families:
   - hard-block only families with proven avoided-set negative R and robust coverage.
   - downgrade harmful AVOID families to context/logging.
7. Produce a new Stage09 dossier:
   - If bad, it must say failed and stop.
   - If good, Stage10 can produce owner-gated activation dossier.

## Appendix Q - Activation Safety Verdict

Committed runtime changes are unsafe to activate as-is.

Reason:

- The only activated production-mechanical replay selected `10 / 253234`.
- It lost about `-5R`.
- It had negative expectancy and PF below 1.
- It blocked `15150` baseline-selected winners and destroyed about `+4011.831701R` from the baseline-selected stream.
- It concentrated selected trades in one symbol and three calendar days.
- Its prop pass/fail proxy is invalid because it used one continuous account path over all generated candidates.

Recommended treatment:

- Preserve disabled runtime changes as diagnostic base.
- Do not flip activation flags.
- Do not treat Stage10 completion as a valid production approval.
- Do not revert blindly unless the owner wants the branch/history simplified. The forensic value is high, and the disabled runtime code plus shards are useful for repair.
- The activation/completion artifacts should be amended or superseded by a failed-candidate dossier before any future activation request.

## Appendix R - Disk Artifact Timeline And File Sizes

These timestamps are filesystem `LastWriteTimeUtc` values observed during the forensic preservation pass.

| Artifact | Size Bytes | LastWriteTimeUtc |
|---|---:|---|
| `VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json` | 20,075 | `2026-05-25T11:04:05.1059697Z` |
| `VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_DOSSIER_2026-05-25.md` | 2,597 | `2026-05-25T11:04:05.4577732Z` |
| `VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json` | 7,656 | `2026-05-25T11:10:34.3859318Z` |
| `VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json` | 49,702 | `2026-05-25T11:10:34.5334287Z` |

Interpretation:

- Stage09 summary/dossier were written around `11:04:05Z`.
- Stage10 completion audit/session state were written around `11:10:34Z`.
- The bad replay numbers were already present before Stage10 marked completion.

## Appendix S - Full Universe By Symbol And Month

### Universe by symbol

| Symbol | Candidate Rows |
|---|---:|
| AUDJPY | 1,261 |
| AUDUSD | 1,252 |
| BTCUSD | 4,003 |
| CHFJPY | 1,254 |
| ETHUSD | 3,318 |
| EURGBP | 1,173 |
| EURJPY | 1,230 |
| EURUSD | 3,999 |
| GBPJPY | 34,838 |
| GBPUSD | 33,592 |
| GER40 | 4,667 |
| JP225 | 2,811 |
| NAS100 | 25,659 |
| NZDUSD | 2,505 |
| SPX500 | 2,020 |
| UK100 | 4,405 |
| UKOIL_cash | 1,142 |
| US30_cash | 27,854 |
| USDCAD | 1,044 |
| USDCHF | 1,262 |
| USDJPY | 35,716 |
| USOIL_cash | 1,013 |
| XAGUSD | 27,242 |
| XAUUSD | 29,974 |

### Universe by year-month

| Year-Month | Candidate Rows |
|---|---:|
| 2022-01 | 379 |
| 2022-02 | 674 |
| 2022-03 | 1,022 |
| 2022-04 | 1,799 |
| 2022-05 | 3,046 |
| 2022-06 | 2,801 |
| 2022-07 | 2,659 |
| 2022-08 | 2,709 |
| 2022-09 | 2,788 |
| 2022-10 | 2,749 |
| 2022-11 | 3,269 |
| 2022-12 | 3,069 |
| 2023-01 | 3,145 |
| 2023-02 | 2,603 |
| 2023-03 | 3,272 |
| 2023-04 | 3,233 |
| 2023-05 | 3,983 |
| 2023-06 | 3,675 |
| 2023-07 | 3,598 |
| 2023-08 | 3,785 |
| 2023-09 | 3,383 |
| 2023-10 | 3,881 |
| 2023-11 | 3,510 |
| 2023-12 | 3,286 |
| 2024-01 | 3,923 |
| 2024-02 | 3,347 |
| 2024-03 | 3,320 |
| 2024-04 | 3,834 |
| 2024-05 | 3,784 |
| 2024-06 | 3,404 |
| 2024-07 | 3,688 |
| 2024-08 | 4,130 |
| 2024-09 | 4,051 |
| 2024-10 | 4,218 |
| 2024-11 | 3,860 |
| 2024-12 | 3,779 |
| 2025-01 | 4,152 |
| 2025-02 | 3,906 |
| 2025-03 | 4,016 |
| 2025-04 | 4,477 |
| 2025-05 | 4,346 |
| 2025-06 | 3,948 |
| 2025-07 | 4,215 |
| 2025-08 | 3,842 |
| 2025-09 | 4,022 |
| 2025-10 | 11,074 |
| 2025-11 | 9,881 |
| 2025-12 | 10,178 |
| 2026-01 | 17,143 |
| 2026-02 | 16,597 |
| 2026-03 | 19,296 |
| 2026-04 | 18,187 |
| 2026-05 | 298 |

Interpretation:

- The replay universe expanded sharply in late 2025 and 2026.
- A one-account continuous replay is especially invalid when later periods have far more generated rows than earlier periods.

## Appendix T - Baseline Selected By Year-Month

| Year-Month | Baseline Selected |
|---|---:|
| 2022-01 | 53 |
| 2022-02 | 97 |
| 2022-03 | 118 |
| 2022-04 | 265 |
| 2022-05 | 560 |
| 2022-06 | 498 |
| 2022-07 | 491 |
| 2022-08 | 513 |
| 2022-09 | 471 |
| 2022-10 | 481 |
| 2022-11 | 584 |
| 2022-12 | 531 |
| 2023-01 | 565 |
| 2023-02 | 462 |
| 2023-03 | 556 |
| 2023-04 | 573 |
| 2023-05 | 752 |
| 2023-06 | 631 |
| 2023-07 | 651 |
| 2023-08 | 708 |
| 2023-09 | 603 |
| 2023-10 | 718 |
| 2023-11 | 612 |
| 2023-12 | 546 |
| 2024-01 | 708 |
| 2024-02 | 589 |
| 2024-03 | 604 |
| 2024-04 | 618 |
| 2024-05 | 618 |
| 2024-06 | 599 |
| 2024-07 | 654 |
| 2024-08 | 627 |
| 2024-09 | 666 |
| 2024-10 | 665 |
| 2024-11 | 621 |
| 2024-12 | 655 |
| 2025-01 | 715 |
| 2025-02 | 643 |
| 2025-03 | 607 |
| 2025-04 | 650 |
| 2025-05 | 685 |
| 2025-06 | 648 |
| 2025-07 | 645 |
| 2025-08 | 623 |
| 2025-09 | 660 |
| 2025-10 | 1,416 |
| 2025-11 | 1,398 |
| 2025-12 | 1,332 |
| 2026-01 | 1,342 |
| 2026-02 | 1,466 |
| 2026-03 | 1,594 |
| 2026-04 | 1,839 |
| 2026-05 | 57 |

Interpretation:

- Baseline selected activity was not a 10-trade system.
- The production-mechanical 10-trade result is not a minor trade-frequency reduction. It is a collapse.

## Appendix U - Major Bottleneck Dimension Breakdowns

### New mechanical final prop overall skip reason

Final skip reason:

- `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget`
- count: `208176`

By session:

| Session | Count |
|---|---:|
| london | 36,782 |
| ny | 39,401 |
| off_kz | 111,755 |
| tokyo | 20,238 |

By side:

| Side | Count |
|---|---:|
| LONG | 107,000 |
| SHORT | 101,176 |

By source mode:

| Source Mode | Count |
|---|---:|
| `OHLC_M1_CSV` | 176,780 |
| `SIERRA_SCID_CONVERTED_M1_PROXY` | 14,203 |
| `MISSING_SOURCE` | 9,928 |
| `OHLC_M15_CSV` | 5,708 |
| `LOCAL_TICK_PARQUET` | 1,309 |
| `OHLC_M5_CSV` | 248 |

By terminal outcome:

| Terminal Outcome | Count |
|---|---:|
| stop | 108,676 |
| target | 82,791 |
| missing | 9,928 |
| timeout | 5,328 |
| no_fill | 1,431 |
| same_bar | 22 |

Interpretation:

- The prop overall block was not a high-quality losing-trade filter.
- It blocked `82,791` target outcomes in this final skip-reason view.
- It also blocked almost all off-KZ generated rows, proving off-KZ rows were part of the prop-governed stream.

### New mechanical prop overall action by symbol

Raw prop action overall blocks, before final skip-reason priority:

| Symbol | Count |
|---|---:|
| AUDJPY | 1,261 |
| AUDUSD | 1,252 |
| BTCUSD | 4,003 |
| CHFJPY | 1,254 |
| ETHUSD | 3,318 |
| EURGBP | 1,173 |
| EURJPY | 1,230 |
| EURUSD | 2,870 |
| GBPJPY | 31,637 |
| GBPUSD | 33,592 |
| GER40 | 4,667 |
| JP225 | 2,811 |
| NAS100 | 19,600 |
| NZDUSD | 2,505 |
| SPX500 | 2,020 |
| UK100 | 4,405 |
| UKOIL_cash | 1,142 |
| US30_cash | 26,811 |
| USDCAD | 1,044 |
| USDCHF | 1,262 |
| USDJPY | 23,331 |
| USOIL_cash | 1,013 |
| XAGUSD | 21,857 |
| XAUUSD | 22,103 |

This proves the prop collapse was broad across instruments, not isolated to one asset class.

### New mechanical prop overall action by year-month

Raw prop action overall blocks, before final skip-reason priority:

| Year-Month | Count |
|---|---:|
| 2022-01 | 276 |
| 2022-02 | 529 |
| 2022-03 | 775 |
| 2022-04 | 1,451 |
| 2022-05 | 2,476 |
| 2022-06 | 2,301 |
| 2022-07 | 2,212 |
| 2022-08 | 2,179 |
| 2022-09 | 2,279 |
| 2022-10 | 2,286 |
| 2022-11 | 2,685 |
| 2022-12 | 2,530 |
| 2023-01 | 2,538 |
| 2023-02 | 2,156 |
| 2023-03 | 2,670 |
| 2023-04 | 2,691 |
| 2023-05 | 3,314 |
| 2023-06 | 3,042 |
| 2023-07 | 3,010 |
| 2023-08 | 3,186 |
| 2023-09 | 2,870 |
| 2023-10 | 3,223 |
| 2023-11 | 2,913 |
| 2023-12 | 2,702 |
| 2024-01 | 3,231 |
| 2024-02 | 2,792 |
| 2024-03 | 2,755 |
| 2024-04 | 3,202 |
| 2024-05 | 3,106 |
| 2024-06 | 2,832 |
| 2024-07 | 3,059 |
| 2024-08 | 3,495 |
| 2024-09 | 3,391 |
| 2024-10 | 3,508 |
| 2024-11 | 3,167 |
| 2024-12 | 3,189 |
| 2025-01 | 3,420 |
| 2025-02 | 3,280 |
| 2025-03 | 3,364 |
| 2025-04 | 3,789 |
| 2025-05 | 3,667 |
| 2025-06 | 3,341 |
| 2025-07 | 3,573 |
| 2025-08 | 3,232 |
| 2025-09 | 3,403 |
| 2025-10 | 9,382 |
| 2025-11 | 8,403 |
| 2025-12 | 8,593 |
| 2026-01 | 15,566 |
| 2026-02 | 15,075 |
| 2026-03 | 17,582 |
| 2026-04 | 16,210 |
| 2026-05 | 260 |

Interpretation:

- Once the continuous account path was damaged, the overall block continued across every later period.
- This is not a meaningful prop-account result.

### `pre_ai_skip_avoid_only` final skip reason

Final skip reason:

- `pre_ai_skip_avoid_only`
- count: `7986`

By framework:

| Framework | Count |
|---|---:|
| ob_retest | 7,986 |

By session:

| Session | Count |
|---|---:|
| london | 3,271 |
| ny | 4,715 |

By side:

| Side | Count |
|---|---:|
| LONG | 5,989 |
| SHORT | 1,997 |

By source mode:

| Source Mode | Count |
|---|---:|
| `OHLC_M1_CSV` | 6,932 |
| `SIERRA_SCID_CONVERTED_M1_PROXY` | 733 |
| `MISSING_SOURCE` | 256 |
| `LOCAL_TICK_PARQUET` | 53 |
| `OHLC_M15_CSV` | 6 |
| `OHLC_M5_CSV` | 6 |

By symbol:

| Symbol | Count |
|---|---:|
| NAS100 | 3,210 |
| XAUUSD | 2,492 |
| USDJPY | 1,147 |
| XAGUSD | 1,137 |

By terminal outcome:

| Terminal Outcome | Count |
|---|---:|
| stop | 4,446 |
| target | 3,209 |
| missing | 256 |
| no_fill | 46 |
| timeout | 29 |

By year-month:

| Year-Month | Count |
|---|---:|
| 2022-01 | 17 |
| 2022-02 | 43 |
| 2022-03 | 61 |
| 2022-04 | 78 |
| 2022-05 | 87 |
| 2022-06 | 97 |
| 2022-07 | 77 |
| 2022-08 | 87 |
| 2022-09 | 88 |
| 2022-10 | 89 |
| 2022-11 | 109 |
| 2022-12 | 102 |
| 2023-01 | 101 |
| 2023-02 | 88 |
| 2023-03 | 112 |
| 2023-04 | 136 |
| 2023-05 | 153 |
| 2023-06 | 165 |
| 2023-07 | 145 |
| 2023-08 | 159 |
| 2023-09 | 143 |
| 2023-10 | 171 |
| 2023-11 | 147 |
| 2023-12 | 145 |
| 2024-01 | 156 |
| 2024-02 | 154 |
| 2024-03 | 146 |
| 2024-04 | 165 |
| 2024-05 | 174 |
| 2024-06 | 160 |
| 2024-07 | 151 |
| 2024-08 | 138 |
| 2024-09 | 146 |
| 2024-10 | 178 |
| 2024-11 | 150 |
| 2024-12 | 126 |
| 2025-01 | 151 |
| 2025-02 | 147 |
| 2025-03 | 152 |
| 2025-04 | 136 |
| 2025-05 | 152 |
| 2025-06 | 133 |
| 2025-07 | 165 |
| 2025-08 | 124 |
| 2025-09 | 160 |
| 2025-10 | 307 |
| 2025-11 | 282 |
| 2025-12 | 326 |
| 2026-01 | 330 |
| 2026-02 | 304 |
| 2026-03 | 305 |
| 2026-04 | 365 |
| 2026-05 | 3 |

Interpretation:

- Pre-AI final skips were not the dominant collapse cause.
- They still blocked `3209` target outcomes, so the pre-AI AVOID set also needs outcome review.

### Internal overlay defer

Raw prop action internal overlay defer count: `16`; final skip reason count: `15`.

By framework:

| Framework | Count |
|---|---:|
| breaker | 5 |
| fvg | 5 |
| ob | 6 |

By session:

| Session | Count |
|---|---:|
| ny | 8 |
| off_kz | 6 |
| tokyo | 2 |

By side:

| Side | Count |
|---|---:|
| LONG | 6 |
| SHORT | 10 |

By source mode:

| Source Mode | Count |
|---|---:|
| `OHLC_M1_CSV` | 16 |

By symbol:

| Symbol | Count |
|---|---:|
| XAGUSD | 16 |

By terminal:

| Terminal Outcome | Count |
|---|---:|
| stop | 10 |
| target | 6 |

Interpretation:

- The internal 4 percent overlay was not the main bottleneck.
- It did affect early XAGUSD rows and changed one row between mechanical and external-only scenarios.

## Appendix V - Mechanical Versus External-Budget-Only Row-Level Difference

The two scenarios had identical aggregate selected count and R, but two row-level differences:

| Candidate ID | Time UTC | Symbol | Mechanical Scenario | External-Only Scenario | R | Meaning |
|---|---|---|---|---|---:|---|
| `cand_3a9a37aa2351cf99d78affef` | 2022-01-04T02:15 | XAGUSD | deferred by internal overlay | selected with reduced risk to external daily budget | -1 | Removing internal overlay allowed this loser. |
| `cand_66ad6a6a03cbbd5257e9d0a3` | 2022-01-05T08:45 | XAGUSD | selected with external overall reduction | blocked by external overall budget | -1 | Equity path changed because the previous row was selected externally. |

Interpretation:

- The internal overlay is not what collapsed the system.
- External redacted_account overall budget, applied to the wrong continuous stream, is the collapse driver.

## Appendix W - What The Next Session Must Not Lose

The next implementation session must keep these facts in front of it:

1. The Stage09 result is not an acceptable production result.
2. The production-mechanical replay selected only 10 rows and lost about 5R.
3. The baseline/current shadow selected 35,983 rows and produced about 4008R.
4. The collapse is not just a bad trade filter. It is mostly prop-budget modeling applied to the wrong stream/window.
5. The runtime prop formula mostly matches the redacted_account one-time math, but Stage09 replay semantics do not.
6. The route prompt required redesign on trivial no-trade collapse.
7. Stage09 and Stage10 verifiers did not enforce that requirement.
8. Stage10 completion state is invalid as a production approval.
9. Default live config remains off, but activation is unsafe.
10. The correct next work is repair/segmentation/viability gating, not a new feature route.
