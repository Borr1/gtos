# Subagent A - Live Performance And Trade Lifecycle Autopsy

Generated: 2026-06-04

Scope: read-only evidence inspection from current disk plus `origin/main`. No production code, runtime code, broker state, account state, or MT5 state was modified. This report is route-local intelligence for the final moonshot rebuild.

## Evidence Inspected

Remote branch authority:

- `origin/main` at `11a51c049 research: package hard halt live evidence`
- Recent live/prod commits inspected by log:
  - `11a51c049 research: package hard halt live evidence`
  - `ce7196fb2 research: close dual broker live supervisor`
  - `b0c1a09a8 runtime: harden dual broker live risk provenance`
  - `41dda7a38 research: preserve dual broker subagent findings`
  - `5652c67e1 runtime: preserve follower target trade provenance`
  - `c90143d4c runtime: harden broker cash risk and dual follower replay`
  - `ddc3a1d00 runtime: remove redacted_account stale count cap`

Primary artifacts inspected:

- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/TRADE_FAILURE_REVIEW_2026-06-03.md`
- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json`
- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json`
- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_AUDIT.json`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_RISK_EXPOSURE_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_ANOMALY_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_REPAIR_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_TRADE_AGENT_INSPECTION_LEDGER.jsonl`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_LIVE_SUPERVISOR_FINAL_CLOSURE_AUDIT_2026-06-01.md`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_TODAY_TRADE_RECORD_AUDIT_SUMMARY_2026-06-01.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_TODAY_CANDIDATE_REJECTION_SUMMARY_2026-06-01.json`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_COMPLETION_AUDIT.json`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_VERIFICATION_RESULT.json`

Important source limitation:

- Recent `knowledge_base/redacted_account_live_bee34003/trade_records/.../*.json` files on `origin/main` are Git LFS pointers in this checkout, not materialized JSON payloads. Example pointer inspected: `knowledge_base/redacted_account_live_bee34003/trade_records/AUDJPY/2026-06-03_moonshot_h04_05_0500_broadorigin_ceb1655bfae2d550a6795dd0.json`, `size 922198`. Full row-level trade-record packet autopsy requires pulling the LFS payloads or using a machine where the LFS objects are present.

## Executive Finding

The live system did not fail because there was no monitoring or because the process was obviously dead. It failed while the process and supervisor layers were repeatedly being marked healthy or repaired. The hard-halt broker truth shows a trading/risk/selection failure:

- Too many trades in too short a window.
- Too much symbol and cluster concentration.
- Weak selected cells and tiny positive expectancy were allowed to risk real prop capital.
- XAUUSD and NDX100 kept trading while actively failing.
- Cost/swap modeling was unsafe on at least crypto/CFD surfaces.
- Selected-cell aggregate risk governance bypassed static count caps but did not provide enough live damage control.
- Emergency flattening was not atomic with process/scheduler shutdown, so risk could continue after a close attempt.

The dual-broker supervisor fixed many operational defects. Those repairs are real. They did not prove live trading quality.

## Hard-Halt Broker Truth

Source: `BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json` and `TRADE_FAILURE_REVIEW_2026-06-03.md`.

Account snapshot at extraction:

| Field | Value |
|---|---:|
| Login | `0` |
| Server | `redacted_account-Server 2` |
| Balance | `$99,965.20` |
| Equity | `$99,965.20` |
| Deals | `205` |
| Orders | `207` |
| Grouped trades | `91` |
| Open positions | `0` |
| Pending orders | `0` |

Full account attribution:

| Source | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| GTOS_SYSTEM | 82 | +$988.47 | 34 | 48 |
| MANUAL_OR_TEST | 8 | -$5.17 | 2 | 6 |
| OTHER | 1 | -$1,018.10 | 0 | 1 |

The full account hides the live failure because earlier GTOS winners offset recent vNext drawdown. The separate `OTHER` XAGUSD loss, position `238398641`, is not GTOS.

## Current vNext Activation Window

GTOS trades from `2026-05-29` through the halt:

| Metric | Value |
|---|---:|
| Trades | `77` |
| Net P/L | `-$859.69` |
| Wins | `31` |
| Losses | `46` |
| Win rate | `40.26%` |

By day:

| Day | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| 2026-05-29 | 8 | -$34.04 | 3 | 5 |
| 2026-06-01 | 11 | -$601.06 | 4 | 7 |
| 2026-06-02 | 47 | +$889.41 | 19 | 28 |
| 2026-06-03 | 11 | -$1,114.00 | 5 | 6 |

The `2026-06-02` profit is outlier-dependent. One GER30 winner produced `+$1,318.24`. Excluding that one trade, the recent window is approximately `-$2,177.93`.

## Symbol Damage

Recent GTOS by symbol, sorted worst to best:

| Symbol | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| XAUUSD | 12 | -$1,327.23 | 2 | 10 |
| NDX100 | 15 | -$1,151.56 | 3 | 12 |
| ETHUSD | 6 | -$696.18 | 2 | 4 |
| GBPJPY | 2 | -$543.61 | 0 | 2 |
| UKOUSD | 3 | -$297.35 | 1 | 2 |
| AUDJPY | 1 | -$274.05 | 0 | 1 |
| USDCAD | 3 | -$191.60 | 1 | 2 |
| NZDUSD | 2 | -$149.99 | 1 | 1 |
| UK100 | 2 | -$130.57 | 1 | 1 |
| USOUSD | 3 | -$58.31 | 1 | 2 |
| CHFJPY | 2 | +$61.05 | 1 | 1 |
| US30 | 4 | +$104.88 | 3 | 1 |
| XAGUSD | 1 | +$167.51 | 1 | 0 |
| BTCUSD | 11 | +$213.32 | 6 | 5 |
| USDJPY | 3 | +$579.57 | 3 | 0 |
| JP225 | 4 | +$677.42 | 2 | 2 |
| EURJPY | 2 | +$838.77 | 2 | 0 |
| GER30 | 1 | +$1,318.24 | 1 | 0 |

Hard conclusion: XAUUSD and NDX100 were live-failing surfaces. They lost `-$2,478.79` together and still kept receiving entries.

## Exit Anatomy

Source: hard-halt review.

| Exit class | Count | Net P/L |
|---|---:|---:|
| Recent broker SL / stop-loss exits | 54 | -$9,280.84 |
| Trades with TP1/partial activity | 22 | mixed |
| Final-classified partial/TP winners | 13 | +$4,677.44 |

The partial/TP layer worked on winners, but it was not enough. The stream of full-stop losses overwhelmed partial winners.

## Overtrading And Cluster Failure

Recent GTOS count:

- `77` trades from `2026-05-29` through halt.
- `47` trades on `2026-06-02`.
- Multiple 2-minute clusters across correlated or simultaneously stressed symbols.

Examples from broker-truth grouping:

| Approx entry time | Count | Symbols | Cluster P/L |
|---|---:|---|---:|
| 2026-06-01 16:16 | 4 | NDX100, US30, USOUSD, UKOUSD | -$673.03 |
| 2026-06-02 10:46 | 3 | USOUSD, UK100, UKOUSD | -$782.24 |
| 2026-06-02 16:31 | 3 | BTCUSD, NZDUSD, NDX100 | -$522.56 |
| 2026-06-02 17:45 | 3 | GBPJPY, USDCAD, JP225 | -$311.25 |

The count cap was intentionally non-authoritative for vNext selected-cell rows:

- `config/profiles/redacted_account.yaml` had `risk.max_concurrent: null`.
- It also used `max_concurrent_policy: disabled_for_vnext_selected_cell_aggregate_drawdown_budget`.
- `src/components/permissions.py` bypassed the old count cap when `_vnext_risk_budget_governed_trade(...)` returned true.

This is not a simple "restore max trades = 2" answer. The final system needs portfolio-real exposure, cluster, symbol-recent-damage, session-recent-damage, and correlation-aware admission. But the current selected-cell aggregate budget was not sufficient as the sole authority.

## Worst Recent Trades

From broker-truth groups:

| Net P/L | Entry UTC | Position | Symbol | Side | Volume | Exit |
|---:|---|---:|---|---|---:|---|
| -$673.62 | 2026-06-02T22:46:08.184Z | 242689402 | ETHUSD | BUY | 10.16 | `[sl 1876.36]` |
| -$293.67 | 2026-06-02T17:46:14.821Z | 242618029 | USDCAD | SELL | 2.21 | `[sl 1.38427]` |
| -$291.91 | 2026-06-03T01:31:07.826Z | 242697618 | ETHUSD | BUY | 9.42 | `[sl 1869.19]` |
| -$283.22 | 2026-06-02T17:45:13.797Z | 242617579 | GBPJPY | BUY | 1.63 | `[sl 215.186]` |
| -$275.20 | 2026-06-02T10:46:51.877Z | 242460741 | USOUSD | SELL | 3.23 | `[sl 93.616]` |
| -$274.05 | 2026-06-03T04:46:06.170Z | 242731196 | AUDJPY | BUY | 3.81 | `[sl 114.640]` |
| -$273.08 | 2026-06-01T16:17:28.966Z | 242233009 | UKOUSD | SELL | 2.93 | `[sl 97.506]` |
| -$271.95 | 2026-06-02T10:47:55.024Z | 242460993 | UKOUSD | SELL | 2.89 | `[sl 96.732]` |
| -$270.46 | 2026-06-03T02:23:06.160Z | 242705821 | CHFJPY | BUY | 2.30 | `[sl 202.871]` |
| -$268.50 | 2026-06-01T16:17:21.029Z | 242232889 | USOUSD | SELL | 2.98 | `[sl 93.912]` |

The worst single trade was ETHUSD `242689402`: entry cash risk around `$254.66`, close net loss `-$673.62`, with `swap=-$391.16`, `commission=-$7.73`, broker profit `-$274.73`. This proves cost/swap could exceed the intended risk design by a large margin.

## Best Recent Trades

From broker-truth groups:

| Net P/L | Entry UTC | Position | Symbol | Side | Volume | Exit |
|---:|---|---:|---|---|---:|---|
| +$1,318.24 | 2026-06-02T20:31:12.177Z | 242667071 | GER30 | BUY | 3.79 | `closeger30` |
| +$742.52 | 2026-06-02T06:31:14.850Z | 242403337 | NDX100 | BUY | 0.43 | `[tp 30442.82]` |
| +$727.50 | 2026-06-02T04:23:42.180Z | 242383463 | EURJPY | BUY | 4.24 | `[tp 186.055]` |
| +$716.87 | 2026-06-02T06:46:12.442Z | 242405337 | JP225 | BUY | 10.48 | `TP1_vnext_partia|[tp 67070]` |
| +$682.09 | 2026-05-29T04:25:13.109Z | 241739921 | XAUUSD | BUY | 0.09 | `[tp 4588.48]` |
| +$504.37 | 2026-06-02T00:34:10.908Z | 242360183 | ETHUSD | SELL | 8.26 | `TP1_vnext_partia|[tp 1902.90]` |
| +$496.60 | 2026-06-01T16:01:15.247Z | 242212827 | USDJPY | BUY | 3.82 | `TP1_vnext_partia|[tp 159.832]` |
| +$496.09 | 2026-06-01T15:01:32.694Z | 242190777 | BTCUSD | SELL | 0.50 | `TP1_vnext_partia|[tp 70778.26]` |
| +$485.39 | 2026-06-02T16:16:08.656Z | 242556375 | USOUSD | BUY | 2.57 | `TP1_vnext_partia|[tp 96.718]` |
| +$344.25 | 2026-06-02T16:16:07.426Z | 242556366 | USDCAD | SELL | 4.23 | `TP1_vnext_partia|[tp 1.38158]` |

The system has real winning behavior. The failure is not "no edge anywhere." The failure is uncontrolled admission, weak cell thresholds, symbol damage persistence, cluster exposure, and cost-blindness.

## Weak Selector Threshold Evidence

Hard-halt report named live losers admitted on very small selected-cell expectancy:

| Ticket | Symbol | Net P/L | Evidence rows | Expectancy | PF | Win rate | Notes |
|---:|---|---:|---:|---:|---:|---:|---|
| 242618029 | USDCAD | -$293.67 | 43 | 0.0465R | 1.0909 | 37.21% | `micro_positive_ev_floor`, selected-cell risk `0.25%` |
| 242752405 | JP225 | -$52.40 | 21 | 0.0476R | 1.1250 | 28.57% | opened after initial halt attempt |
| 242705821 | CHFJPY | -$270.46 | 21 | 0.0476R | 1.1250 | 28.57% | moonshot hour cell |
| 242231894 | NDX100 | -$251.50 | 1677 | 0.0346R | 1.0707 | 35.00% | large denominator but tiny edge |
| 242342001 | NDX100 | -$245.57 | 361 | 0.0252R | 1.0507 | 35.46% | moonshot hour cell |

This is a direct selector-design problem. A cell being positive is not enough for live prop deployment. The final moonshot selector needs a margin-of-safety layer: minimum expectancy, lower confidence bound, symbol/session live-damage state, cost stress, outlier dependence, and recent failure veto.

## June 1 Supervisor Claimed Healthy But Did Not Prove Trading Quality

Source: `VPS_LIVE_SUPERVISOR_FINAL_CLOSURE_AUDIT_2026-06-01.md`.

At `2026-06-01T22:30Z`:

- redacted_account account connected and trade-enabled.
- Equity/balance at probe: `$100,214.27` / `$99,706.80`.
- Process proof: `24` live orchestrators, `24` tick captures, `1` M1 capture, `1` heartbeat monitor, `1` notification worker, `1` displacement logger, `1` MT5 terminal.
- All 24 broker symbols selected in MT5.
- No current live blocker remained from the supervisor's side.

June 1 candidate/trade summaries:

- `VPS_TODAY_TRADE_RECORD_AUDIT_SUMMARY_2026-06-01.json`: `235` trade records, `211` dynamic skips, `7` filled, `16` Gate3 rejects, `1` LTF SL-too-close cancel.
- `VPS_TODAY_CANDIDATE_REJECTION_SUMMARY_2026-06-01.json`: `256` candidates, `228` dynamic skips, `26` prescreen blocked, `1` Gate3 reject, `1` dynamic join pending.
- Selected-cell source risk rejects were `228`; account/prop rejects were `0`.

The June 1 route repaired important runtime defects:

- selected-cell risk cap semantics;
- prop/account projection after selected-cell risk;
- lower runtime risk overrides below selected-cell risk;
- crypto OHLC corruption repair/fail-closed;
- M1 repair and atomic upsert;
- direct Python watchdog maintenance launch;
- broker entry-fill truth from MT5 history when `OrderResult.price` was zero;
- broker/Telegram/daily P/L preference for broker net profit.

But those were process/data correctness repairs. They were not proof that the live selector, scheduler, and execution admission were safe.

## V3 Promotion State

Source: `VPS_V3_FTMO_COMPLETION_AUDIT.json` and `VPS_V3_FTMO_VERIFICATION_RESULT.json`.

At the V3/FTMO setup route:

- Selector V3: `package_loaded_default_off`
- Scheduler V3: `package_loaded_default_off`
- Execution Policy V3: `package_loaded_default_off`
- redacted_account: existing process group continued.
- FTMO: terminal verified, staged, flat, no run-agent activation at that time.
- Runtime boundary: `default_off_v3_package_consumption_no_live_process_reload_no_order_deal_position_mutation`.
- Verification: `113 passed`, profile verifiers ok, route verifier ok, redacted_account probe ok, FTMO probe ok.

This matters because V3 existence on disk must not be interpreted as "the final V3 decision brain was already fully active and proven." The hard-halt failure occurred in the live production chain after multiple runtime repairs and selected-cell/vNext governance changes. The final rebuild must verify exactly which V3 decisions were active, default-off, fallback, or only provenance for every live trade.

## Dual-Broker Supervisor Findings

Source: `DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_AUDIT.json`.

At `2026-06-02T11:40:58Z`:

| Metric | Value |
|---|---:|
| Trade records loaded | 105 |
| Trade records today | 102 |
| redacted_account open positions | 9 |
| FTMO open positions | 2 |
| redacted_account pending orders | 0 |
| FTMO pending orders | 0 |
| Slippage rows all | 64 |
| Pending lifecycle rows today | 61 |
| Dual intent rows | 4 |
| Follower action rows | 17 |
| Inspected rows written | 111 |

Outcome counts:

| Outcome | Count |
|---|---:|
| `LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN` | 10 |
| `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC` | 66 |
| `REJECTED_GATE3_CIRCUIT_BREAKER` | 24 |
| `LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE` | 2 |

Rejection counts:

| Reason | Count |
|---|---:|
| `same_symbol_position_conflict_multi_ticket_lifecycle_unsupported` | 21 |
| `mt5_disconnected` | 2 |
| `cross_instrument_correlation_excess` | 1 |

Policy counts:

| Policy | Count |
|---|---:|
| `partial_be_runner` | 94 |
| `momentum_exhaustion` | 6 |
| missing | 2 |

Risk snapshot:

| Field | Value |
|---|---:|
| redacted_account balance | `$100,531.27` |
| redacted_account equity | `$101,124.33` |
| redacted_account margin | `$30,816.48` |
| Known open worst-case cash risk | `$1,255.72` |
| Open worst-case risk pct of balance | `1.2491%` |
| Configured max daily loss cash | `$4,021.25` |
| Unknown open-risk tickets | `0` |
| FTMO balance | `$99,999.52` |
| FTMO equity | `$99,836.31` |

Risk exposure ledger over the route:

- `33` rows.
- redacted_account positions ranged up to `13`.
- redacted_account margin reached `$80,094.63`.
- FTMO positions reached `9`.
- Last inspected row: redacted_account `12` positions, equity `$100,710.28`, margin `$80,094.63`; FTMO `8` positions, equity `$97,753.66`.

This is a major live-intelligence signal. The portfolio was allowed to build large simultaneous exposure and high margin use while selected-cell risk math still looked "inside budget."

## Dual Supervisor Repair Ledger

Source: `DUAL_ANOMALY_LEDGER.jsonl`, `DUAL_REPAIR_LEDGER.jsonl`, `DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl`.

Counts:

- `DUAL_ANOMALY_LEDGER.jsonl`: `48` rows.
- `DUAL_REPAIR_LEDGER.jsonl`: `55` rows.
- `DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl`: `73` rows.

Important operational defects found and repaired:

| Defect / class | Evidence |
|---|---|
| Notification queue namespace collision risk | `DUAL-NOTIFICATION-QUEUE-COLLISION-RISK-001`, repaired and validated |
| RealMT5 zero/nonpositive tick poisoning | `DUAL-REALMT5-ZERO-TICK-OFFSET-POISONING-001`, repaired in `src/mt5/mt5_real.py` |
| FTMO target tick unavailable but intent could advance | `DUAL-FTMO-TARGET-TICK-DEFERRAL-001`, repaired in follower |
| Watchdog did not supervise projector + FTMO follower bridge completely | `DUAL-WATCHDOG-BRIDGE-SUPERVISION-001`, repaired |
| First BTCUSD intent lacked full vNext execution context | `DUAL-BRIDGE-VNEXT-CONTEXT-PROJECTION-001`, repaired for future intents |
| Canonical intent identity migration could duplicate source trades | `DUAL-BRIDGE-CANONICAL-IDENTITY-COMPAT-002`, repaired |
| Pending-limit source intent and later fill could duplicate FTMO entry | `DUAL-BRIDGE-PENDING-FILL-LIFECYCLE-DEDUP-003`, repaired |
| FTMO follower restart could lose target lifecycle state | `DUAL-FOLLOWER-STARTUP-LIFECYCLE-RECOVERY-004`, repaired |
| Active partial records stale for JP225/NZDUSD | `DUAL-ACTIVE-PARTIAL-RECORD-STALE-JP225-005`, `DUAL-ACTIVE-PARTIAL-RECORD-STALE-NZDUSD-006`, repaired locally |
| FTMO follower stale count-cap authority | `ftmo_follower_aggregate_drawdown_budget_repair_20260602T1309Z`, repaired |
| Impossible XAGUSD R in local ledger | `CODEX-XAGUSD-CORRUPT-R-LEDGER`, repaired to weighted result `+0.733R`, broker net `+$167.51` |
| FTMO target-state restart recovery loss caused repeated TP1 invalid-volume rows | `codex_ftmo_target_state_restore_repair_20260602T1537Z`, repaired |
| FTMO follower JSON persistence could crash on Windows file lock | `codex_ftmo_follower_json_persistence_retry_repair_20260602T1645Z`, repaired |
| Projector JSON persistence needed retry | `codex_dual_projector_json_persistence_retry_repair_20260602T1659Z`, repaired |
| Tick capture repairs | GBPUSD/GBPJPY/USOIL capture relaunch/checkpoints |

The repair ledger proves the live system had many real operational defects during the dual-broker run. Some were repaired during the session. The performance failure still occurred, so the next final moonshot pass must handle both layers: operational correctness and trading-quality correctness.

## FTMO Follower And BTC Lifecycle

Source: `DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json`.

Final BTC lifecycle parity:

| Account | Ticket | State | Residual volume | SL | TP |
|---|---:|---|---:|---:|---:|
| FTMO | 155209892 | `target_tp1_partial_and_be_verified_by_broker_readback` | 0.30 | 67171.70 | 68371.82 |
| redacted_account | 242690948 | `source_already_tp1_partial_and_be` | 0.28 | 67223.29 | 68578.18 |

The FTMO BTC repair required owner-approved manual partial close at current FTMO bid:

- close price used: `67810.07`
- volume before manual repair: `0.61`
- volume closed: `0.31`
- partial retcode: `10009`
- SLTP retcode: `10009`

This is useful but not clean autonomous proof. The final system should not require manual lifecycle repair for mirrored broker positions.

## Emergency Halt Failure

Source: hard-halt review.

The first emergency close was not enough. The system still had running agents, and JP225 ticket `242752405` appeared/continued after the initial close path. Direct process shutdown and scheduler disablement were required.

Final hard halt state:

- `GTOS_Watchdog`: disabled
- `TradingAgentDaily`: disabled
- GTOS runtime processes: stopped
- redacted_account positions/orders: `0` / `0`
- Halt flags written:
  - `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
  - `pipeline_state/RESEARCH_RUNTIME_HALT.flag`
  - `knowledge_base/meta/AUTOSTART_DISABLED.flag`

Final moonshot requirement: emergency close must be atomic with scheduler disable, watchdog disable, runtime kill, lock cleanup, halt flags, and broker-flat verification. Flatten-only is not a halt.

## Failure Mechanisms

1. **Selector threshold too low for live money**
   - Micro-positive cells around `0.02R` to `0.05R` expectancy were admitted.
   - Some had weak win rates near `28%` to `37%`.
   - Positive expectancy alone was treated as sufficient even when edge was tiny.

2. **No effective symbol kill**
   - XAUUSD and NDX100 repeatedly lost and still received more entries.
   - Live damage state was not authoritative enough.

3. **Portfolio and cluster admission too loose**
   - `47` trades in one day.
   - Multiple multi-symbol clusters within 2 minutes.
   - redacted_account positions reached `13`.
   - Margin reached `$80,094.63`.

4. **Aggregate selected-cell risk was not enough**
   - Worst-case cash risk could look acceptable while clusters and repeated stop streams damaged the account.
   - Account risk governance must include live behavior, not only theoretical worst-case SL.

5. **Cost/swap gate failed**
   - ETHUSD `242689402` converted a roughly `$254.66` intended risk into `-$673.62` net account damage due mainly to swap.
   - Instruments/sessions with unresolved or unstable swap/cost must be blocked or sized materially lower.

6. **Exit policy was not the core shield**
   - Partial/BE helped, but could not compensate for too many full stops.
   - The final system needs admission/risk damage control before exit management.

7. **Dual-broker mirroring was operationally fragile**
   - FTMO follower defects included target tick handling, context projection, identity dedupe, target-state recovery, invalid-volume TP1 loops, and JSON persistence crash risk.
   - These defects were repaired, but the architecture still needs a decision on whether FTMO remains a lightweight follower or gains broker-local management authority.

8. **Health proofs were too infrastructure-focused**
   - Process count, tick capture, M1 capture, verifier pass, and broker connection were healthy.
   - Trading quality was not healthy.
   - The final supervisor must track performance degradation, symbol damage, cluster drawdown, micro-edge admission, and cost anomalies as first-class health.

## Unresolved Gaps For Next Research Agents

1. **LFS trade-record payloads unavailable in this checkout**
   - `origin/main` recent trade records under `knowledge_base/redacted_account_live_bee34003/trade_records` are LFS pointers here.
   - Full row-level selected-cell, V3 disposition, packet, geometry, cost, and lifecycle autopsy for all `77` recent trades requires materializing those LFS objects or using the VPS/local machine that has them.

2. **Full candidate-to-trade join for June 1-3 remains incomplete from current accessible text**
   - Supervisor ledgers give strong summaries.
   - Hard-halt groups give broker truth.
   - The full join needs trade-record payloads plus runtime decisions plus candidate packet ledgers.

3. **FTMO hard-halt broker truth is not included in the redacted_account hard-halt route**
   - Dual supervisor had FTMO positions and follower repairs.
   - The hard-halt broker extraction is redacted_account-only.
   - FTMO-specific realized/unrealized damage and lifecycle truth must be exported and reconciled separately.

4. **Price-action microscope for every live trade is not complete here**
   - This report identifies broker outcomes and system mechanisms.
   - It does not yet replay tick/M1 path anatomy for all 77 trades, the failed clusters, and every skipped candidate.

5. **Which V3 packages were active versus provenance must be proven per trade**
   - V3 setup route initially loaded packages default-off.
   - Later live branch commits changed runtime behavior.
   - The final autopsy must classify every trade as Selector V3/Scheduler V3/Execution V3 active, fallback, legacy, default-off provenance, or repaired-runtime hybrid.

## Intelligence For Final Moonshot Rebuild

The final moonshot rebuild must not be "make V3 live again." It must rebuild live admission and control around the actual failure:

1. **Broker-net selector standard**
   - Replace micro-positive admission with broker-net, cost-stressed, lower-bound expectancy.
   - Require minimum edge margin by symbol/session/origin, not just positive EV.
   - Penalize small sample, low win rate, high cost, poor recent live behavior, and outlier dependence.

2. **Symbol damage state**
   - XAUUSD and NDX100 must be fail-closed or heavily reduced until repaired by evidence.
   - Every symbol needs live rolling stop-stream counters, recent P/L counters, cluster P/L counters, and drawdown-to-edge ratio.

3. **Cluster and correlation governor**
   - Add hard admission controls for 2-minute, 5-minute, 15-minute, session, and day clusters.
   - Correlated baskets must be capped by live adverse-flow state, not only static correlation or total risk.

4. **Hard daily/session/symbol stops**
   - Stop new entries after stop-out sequences or live drawdown thresholds.
   - This must trigger before prop-limit math is near failure.

5. **Cost/swap gate**
   - Instruments/sessions with unresolved commission/swap/spread/slippage cannot trade.
   - If swap can exceed intended risk, block or size near zero.

6. **Emergency halt must be atomic**
   - Disable scheduler and watchdog, kill run agents, clear locks, write halt flags, verify broker flat, verify no autostart.
   - A close-only command is not a production halt.

7. **Dual-broker lifecycle management**
   - Decide and implement either:
     - FTMO remains follower with strict source-ticket mirroring and robust target-state recovery, or
     - FTMO gets broker-local lifecycle authority for residuals/partials/BE/TP.
   - Current evidence shows follower-only can work but is fragile under restarts, invalid volume, and target context gaps.

8. **Live health must include trading-quality health**
   - Process healthy is not enough.
   - Supervisor must track symbol damage, trade density, cost anomalies, weak-cell admission, repeated SL, cluster loss, open margin stress, and divergence between expected edge and live realized behavior.

9. **Digital twin must replay the exact live runtime chain**
   - Candidate -> selector -> selected-cell risk -> scheduler -> execution policy -> broker cost/swap -> portfolio state -> lifecycle outcome.
   - Replay must include the account namespace: redacted_account full runtime versus FTMO follower/projector.

10. **All future live claims must be broker-truth-first**
   - Broker deals/orders/positions dominate local projected P/L.
   - Projected R remains useful only when exact broker truth is unavailable and must be labeled as proxy.

## Subagent A Closure

This route is not complete for the full final moonshot investigation. It completes Subagent A's read-only initial autopsy from accessible `origin/main` and local disk text artifacts. The next same-class work should materialize the LFS trade-record payloads and produce a row-level 77-trade join across broker truth, candidate packet, selector cell, scheduler state, execution policy, risk exposure, cost/swap, and tick/M1 price path.

