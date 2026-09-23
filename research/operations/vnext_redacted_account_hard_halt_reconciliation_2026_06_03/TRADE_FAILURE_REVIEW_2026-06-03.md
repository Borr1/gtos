# redacted_account Hard-Halt Trade Failure Review - 2026-06-03

Status: current hard-halt review after emergency close and read-only broker-history extraction.

## Scope

Broker truth source:

- `BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json`
- `BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json`
- `BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json`

Account state in extracted broker truth:

- Login: `0`
- Server: `redacted_account-Server 2`
- Balance/equity: `$99,965.20`
- Open positions: `0`
- Pending orders: `0`
- Grouped trades: `91`
- Deals/orders: `205` deals, `207` orders

## Full Account Attribution

| Source | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| GTOS_SYSTEM | 82 | +$988.47 | 34 | 48 |
| MANUAL_OR_TEST | 8 | -$5.17 | 2 | 6 |
| OTHER | 1 | -$1,018.10 | 0 | 1 |

The full-account number hides the failure. GTOS is positive over the full April-to-halt extraction only because earlier winners offset the current vNext activation drawdown. The `OTHER` loss is a separate non-GTOS XAGUSD trade, position `238398641`, net `-$1,018.10`.

## Current vNext Activation Window

Using GTOS trades from `2026-05-29` through the halt:

- Trades: `77`
- Net P/L: `-$859.69`
- Wins/losses: `31` / `46`
- Win rate: `40.26%`

| Day | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| 2026-05-29 | 8 | -$34.04 | 3 | 5 |
| 2026-06-01 | 11 | -$601.06 | 4 | 7 |
| 2026-06-02 | 47 | +$889.41 | 19 | 28 |
| 2026-06-03 | 11 | -$1,114.00 | 5 | 6 |

The `2026-06-02` profit was not healthy distribution. One GER30 winner contributed `+$1,318.24`; excluding that outlier, the recent window is about `-$2,177.93`.

## Worst Symbol Damage

| Symbol | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| XAUUSD | 12 | -$1,327.23 | 2 | 10 |
| NDX100 | 15 | -$1,151.56 | 3 | 12 |
| ETHUSD | 6 | -$696.18 | 2 | 4 |
| GBPJPY | 2 | -$543.61 | 0 | 2 |
| UKOUSD | 3 | -$297.35 | 1 | 2 |
| AUDJPY | 1 | -$274.05 | 0 | 1 |

XAUUSD plus NDX100 alone lost `-$2,478.79`. That is not noise. The router kept sending trades into symbols that were actively failing.

## Exit Anatomy

Recent GTOS stop-loss/broker-SL exits:

- Count: `54`
- Net P/L: `-$9,280.84`

Recent trades with partial/TP1 activity:

- Trades with TP1/partial in comments: `22`
- Final-classified partial/TP winners: `13`
- Final-classified partial/TP net: `+$4,677.44`

This means the exit layer did work sometimes, but it did not protect the system from repeated full-stop damage. The loser stream overwhelmed the partial winners, especially after symbol concentration and trade clustering.

## Overtrading And Concentration

The system fired too many trades in too small a window:

- `77` GTOS trades from `2026-05-29` through halt.
- `47` GTOS trades on `2026-06-02`.
- Multiple 2-minute trade clusters were allowed.

Examples:

| Approx entry time | Count | Symbols | Cluster P/L |
|---|---:|---|---:|
| 2026-06-01 16:16 | 4 | NDX100, US30, USOUSD, UKOUSD | -$673.03 |
| 2026-06-02 10:46 | 3 | USOUSD, UK100, UKOUSD | -$782.24 |
| 2026-06-02 16:31 | 3 | BTCUSD, NZDUSD, NDX100 | -$522.56 |
| 2026-06-02 17:45 | 3 | GBPJPY, USDCAD, JP225 | -$311.25 |

Config and code evidence:

- `config/profiles/redacted_account.yaml` sets `risk.max_concurrent: null`.
- The same profile sets `max_concurrent_policy: disabled_for_vnext_selected_cell_aggregate_drawdown_budget`.
- `src/components/permissions.py` bypasses the old count cap when `_vnext_risk_budget_governed_trade(...)` is true.

So the old concurrent-count safety was intentionally not authoritative for current vNext selected-cell trades. The system relied on selected-cell and prop-safe aggregate budget logic, but that allowed multi-symbol baskets and repeated correlated stop-outs.

## Weak Selector Thresholds

The live selector promoted weak positive cells to real trades. Several rows were allowed because they crossed a very low positive-EV floor, not because they had robust live-ready edge.

Examples:

| Ticket | Symbol | Net P/L | Evidence rows | Expectancy | PF | Win rate | Notes |
|---:|---|---:|---:|---:|---:|---:|---|
| 242618029 | USDCAD | -$293.67 | 43 | 0.0465R | 1.0909 | 37.21% | `micro_positive_ev_floor`, selected-cell risk `0.25%` |
| 242752405 | JP225 | -$52.40 | 21 | 0.0476R | 1.1250 | 28.57% | opened after initial halt attempt; source candidate spread R `0.1358` |
| 242705821 | CHFJPY | -$270.46 | 21 | 0.0476R | 1.1250 | 28.57% | moonshot hour cell, selected-cell risk `0.25%` |
| 242231894 | NDX100 | -$251.50 | 1677 | 0.0346R | 1.0707 | 35.00% | large denominator but tiny edge, still risked real capital |
| 242342001 | NDX100 | -$245.57 | 361 | 0.0252R | 1.0507 | 35.46% | moonshot hour cell, weak expectancy |

The failure is not only small sample size. Some high-row cells also had tiny expectancy and still went live. The threshold was too permissive for real prop capital.

## Cost And Swap Accounting Failure

The pretrade cost model did not reliably know broker-real cost before entry:

- Recent entries with unresolved entry commission/swap after history lookup: `10`
- Example entries include ETHUSD, JP225, and XAUUSD tickets.

Worst example:

- Ticket `242689402`, ETHUSD BUY
- Entry cash risk captured around `$254.66`
- Close net loss: `-$673.62`
- Close record captured `swap=-$391.16`, `commission=-$7.73`, broker profit `-$274.73`
- Close R multiple: about `-1.079R` gross before the huge swap burden

That trade shows the cost/swap model was not safe for the live crypto/CFD surface. A trade sized like a `$250` risk became a `-$673.62` account hit.

## Runtime Control Failure During Halt

The first emergency close was not enough to stop the system. Agents were still running, and a JP225 position, ticket `242752405`, appeared/continued after the initial close path. Direct process shutdown and scheduler disablement were required.

Final hard-halt state after manual/direct intervention:

- `GTOS_Watchdog`: disabled
- `TradingAgentDaily`: disabled
- GTOS runtime processes: stopped
- redacted_account broker positions/orders: `0` / `0`
- Halt flags written:
  - `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
  - `pipeline_state/RESEARCH_RUNTIME_HALT.flag`
  - `knowledge_base/meta/AUTOSTART_DISABLED.flag`

This is a system-control defect, not a trading-edge defect. Emergency close must be paired with process/scheduler/autostart shutdown, or the system can keep producing risk after flattening.

## Diagnosis

The system failed for several concrete reasons:

1. The live vNext selector was too permissive. It treated micro-positive historical cells as tradable, including cells with 0.02R to 0.05R expectancy and weak win rates.
2. The exposure model allowed too much simultaneous activity. Selected-cell governance bypassed the old count cap and permitted baskets across symbols.
3. Symbol-level kill logic was missing or ineffective. XAUUSD and NDX100 kept trading despite repeated recent failures.
4. Cost/swap accounting was not production-safe. ETHUSD proved that unresolved entry cost plus live swap can blow through intended risk.
5. Exit management helped winners but did not stop repeated full-stop losses. Partial/BE logic was not enough without hard session/day/symbol stops.
6. Emergency control was incomplete until scheduler/process shutdown was done. Flattening positions alone did not stop reruns.

## Required Reconciliation Before Any Reactivation

Do not reactivate live trading until these are fixed and independently verified:

- Broker-net selector audit: rebuild selected-cell performance using broker-real commission, swap, slippage, and stop/TP outcomes where available.
- Symbol kill audit: XAUUSD and NDX100 must be treated as failed live surfaces until repaired by evidence.
- Hard exposure limits: restore an actual concurrent cap or equivalent basket risk cap that cannot be bypassed by selected-cell rows.
- Hard daily/session stop: stop new entries after a small number of recent stop-outs or a live drawdown threshold, not only after prop-limit budget math.
- Cost gate: block any instrument/session where commission/swap is unresolved or where broker swap can exceed the intended cash risk.
- Emergency stop runbook: emergency close must always disable scheduler, kill runtime processes, remove locks, set halt flags, then verify broker flatness.

No production reactivation decision is made by this report.
