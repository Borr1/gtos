# Lane l10 — BROKER GROUND TRUTH

**Scope discipline: EXECUTION MECHANICS ONLY.** No live-forward P&L is computed, tabulated or
reported anywhere in this receipt or its artifacts. Where a record could not be separated into
mechanics and outcome it was dropped and the drop is stated.

**Provenance of this file.** A first l10 pass produced findings **F1–F14** and `l10_RESULT.json`
(2026-08-06 08:33) and died before writing its `.md`. This pass preserves F1–F14, **corrects two of
them on a unit-mismatch defect (F7/F8)**, and adds thirteen new measurements **X1–X13** built on a
full-population pass over the tick archive that the first pass launched and lost. Everything is
reproducible from `l10_scripts/`.

---

## 0. THE HEADLINE

> **The frozen research cost model overcharges the January pool by 3.503× all-in and 4.520× on
> spread — but it is not uniformly biased, it is SCRAMBLED: 33.9× over on NAS100, 18.2× over on
> SPX500, and 58× UNDER on BTCUSD. The consequence is that the 0.10 R spread cap admitted
> 550 of 9,905 index-CFD candidates (5.6%) where real broker spread admits 5,863 (59.2%) — SPX500
> and NAS100 were admitted ZERO times out of 3,565 rows. Correcting the whole cost model is worth
> +0.4739 R/trade to the book and still leaves it at −0.4068, because the gross deficit, not cost,
> is what is binding.**

Second headline, equally load-bearing:

> **The live engine has never placed a limit order and cannot: `TRADE_ACTION_PENDING` is defined
> once and referenced only by a classifier. On 296/296 live captures the requested entry price is
> EXACTLY the executable quote (ask for long, bid for short), to floating-point equality — zero
> displacement, zero born-past-stop. 41.5% of the January pool describes an order type this system
> is structurally incapable of sending.**

---

## 1. COVERAGE — and a correction to this lane's own brief

The lane brief says *"Both accounts have been placing real orders since 2026-07-29. Every modelled
fill assumption in this entire program is untested against a single real fill."* The second sentence
is true. **The first cannot be tested from this machine: there are ZERO broker records at or after
2026-07-29 anywhere on it.**

Measured (`l10x_01_clock.py` → `L10X_CLOCK_V1.json`):

| | FTMO | redacted_account |
|---|---:|---:|
| orders | 267 | 366 |
| deals | 269 | 362 |
| strategy-magic (20260401) orders | 255 | 337 |
| distinct trading days | 20 | 27 |
| window (raw broker epoch) | 2026-06-02T13:57:12 → 2026-07-03T04:24:32 | 2026-04-27T03:44:34 → 2026-07-02T19:03:00 |
| **window (TRUE UTC, −3 h)** | **2026-06-02T10:57:12Z → 2026-07-03T01:24:32Z** | **2026-04-27T00:44:34Z → 2026-07-02T16:03:00Z** |
| orders on/after 2026-07-29 | **0** | **0** |
| deals on/after 2026-07-29 | **0** | **0** |

Verified absence of any newer pull: `vps-export-20260725` (host export), `vps-bars-20260727`,
`vps-ticks-20260726` are the newest three; `find /Users/borr/GTOSActive/{repo/shadow_logs,repo/pipeline_state,vps-export-20260725} -newermt 2026-07-28` returns nothing;
`/Users/borr/GTOSActive/repo/shadow_logs/` contains one zero-byte lock file.

**So the broker ground truth available is the pre-arming live W7 window**: 633 orders, 631 deals,
2026-04-26 → 2026-07-02 true UTC. These are real orders on real funded accounts with real
commission and swap, so every mechanics question in the brief is answerable. Only the *post-arming*
period is unavailable, and no claim here should be read as describing it.

**Non-broker execution evidence inventoried** (all under
`/Users/borr/GTOSActive/vps-export-20260725/extracted/`):

| file | rows |
|---|---:|
| `05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl` | 594 (pre_send 147, entry_fill_reconciled 149, sltp_modify_result 271, close_position_result 10, sltp_modify_deferred 15, sltp_modify_blocked 2) |
| `05_shadow_logs/slippage.jsonl` | 192 |
| `05_shadow_logs/slippage_runtime.jsonl` | 165 |
| `05_shadow_logs/nofill_forward_source_capture.jsonl` | 446 (**all statuses fail-closed — see F12**) |
| `05_shadow_logs/broker_actual_r_audit.jsonl` | 285 |
| `05_shadow_logs/time_in_trade.jsonl` | 51 |
| `05_shadow_logs/execution_manager_v4_decisions.jsonl` | 6,090,235 bytes |
| tick archive `/Users/borr/GTOSActive/vps-ticks-20260726/` | **300,538,915 ticks measured, 61 series, full population** |

Reconciled fills carrying BOTH a request price and a broker fill price: **140**.

---

## 2. X1 — THE BROKER CLOCK IS +3.00 h, MEASURED FROM PAIRED RECORDS

`l10x_01_clock.py`. Method: join `broker_order_lifecycle_capture_v4.jsonl` stage
`entry_fill_reconciled` (whose `order_send_time_utc` is the VPS runtime's own
`datetime.now(timezone.utc)`) to the raw MT5 `history_deals_get` row by `deal_ticket`, and difference
the raw epoch against the runtime clock.

| | n | mean s | median s | min s | max s | within ±2 s | in [10790,10810] |
|---|---:|---:|---:|---:|---:|---:|---:|
| FTMO | 79 | 10799.707 | 10799.711 | 10799.185 | 10800.658 | **0.0000** | **1.0000** |
| redacted_account | 61 | 10801.378 | 10800.303 | 10799.511 | 10835.973 | **0.0000** | 0.9672 |

140 matched, 0 unmatched. **Not one record is true UTC.** MT5 `history_orders_get.time_setup` and
`history_deals_get.time` are **broker wall clock emitted as a Unix epoch** — true UTC + 10,800 s in
this window (June–July 2026; consistent with `America/New_York + 7 h` = UTC+3 in US summer, per
`src/utils/broker_clock.py`).

**Consequence:** any session, hour or kill-zone attribution computed with
`datetime.fromtimestamp(t, utc)` on these files is **3 hours late**. The first l10 pass's
`per_session_utc` table is affected; §7 below re-derives it on the corrected clock. The redacted_account
36 s tail is deal-time second-granularity plus the one 148 s close, not a second clock.

---

## 3. X3 — THE LIVE ENGINE CANNOT PLACE A LIMIT, AND ITS ENTRY IS ALWAYS THE LIVE QUOTE

### 3.1 Source (three citations, exhaustive)

- `src/components/execution.py:3534` — the **only** entry `order_send` request in the tree, hardcoded
  `"action": 1,  # TRADE_ACTION_DEAL` with `"type_time": 0` (GTC, inert for a market order).
- `src/mt5/mt5_interface.py:63` — `TRADE_ACTION_PENDING = 5` is *defined*.
- `src/safety/activation_token.py:70, :625` — the only *references*, inside the token's
  risk-direction classifier. **No request anywhere in `src/` ever sets `action = 5`.**

Every other `"action": 1` site in `execution.py` (`:8101, :8258, :8312, :8427, :8501, :8578, :8643,
:8699, :8823`) is a **close**; `:9893` and `:10047` are `TRADE_ACTION_SLTP`.

### 3.2 Measurement — `l10x_04_bornstate.py` → `L10X_LIVE_BORNSTATE_V1.json`

Over all **296** live pretrade captures carrying a captured broker quote (147 `pre_send` +
149 `entry_fill_reconciled`), comparing the intended `entry_price` to the executable quote
(`ask` if long, `bid` if short):

| quantity | value |
|---|---:|
| entry_price **exactly equal** to the executable quote | **296 / 296 = 1.0000** |
| equal within 1e-6 relative | 296 / 296 |
| born state `at_or_through_market` | **296 (100%)** |
| born state `resting` | **0** |
| born-past-stop (stop already breached at the live quote) | **0 (0.0000)** |
| displacement (market − intended) in R: mean / median / min / max | **0.0 / 0.0 / 0.0 / 0.0** |

Corroborated independently by the first pass's displacement measurement:
`requested_minus_intended_r` mean 0.0, max 0.0, `n_requested_equals_intended = 140/140`
(`L10_DISPLACEMENT_V1.json`). **The engine never chases and never re-prices — because it has
nothing to chase from: it takes the quote and sends market.**

### 3.3 The divergence against the January research pool

| born state | January pool (W0-capture, `BORN_CENSUS`) | live (this lane, n=296) |
|---|---:|---:|
| `born_at_limit` (entry == decision market price) | 14,911 (53.95%) | **296 (100%)** |
| `born_resting` (a genuine resting limit) | 7,949 (28.76%) | **0** |
| `born_marketable` (limit through the market, stop intact) | 1,265 (4.58%) | 0 |
| `born_past_stop` (stop already gone at the decision) | **3,516 (12.72%)** | **0** |

**41.48% of the January pool (11,465 rows) describes an order the live engine is structurally
incapable of constructing**, and 46.06% once `born_marketable` is included. This is not a
calibration gap; it is a different order type.

It also settles the status of W0-capture's headline artifact: the 3,516 born-past-stop rows worth
−0.1265 R/pool-trade (58.25% of the pool's entire gross deficit) are **not a hazard the live system
carries**. Live re-quotes the entry at send time, so "the stop was already breached before the order
could be sent" cannot arise. Whatever else is wrong with the live path, that one is a research-only
defect.

### 3.4 There is no fallback mechanism either

`guarded_market_fallback_*` (17 fields) exists **only** in
`src/research_infra/v4_timewarp_simulated_live_research_loop.py:768-787`. Measured over the pool:
`guarded_market_fallback_extra_cost_r == 0.0` on **27,658 / 27,658 rows** — never applied even in
research. The live engine has no fallback concept because it has nothing to fall back *from*.

---

## 4. X4 — REAL BROKER SPREAD, FULL POPULATION, THREE-WAY VALIDATED

`l10x_03_tickspread.py` → `L10X_TICK_SPREAD_V1.json`. Every tick of all 61 series in
`/Users/borr/GTOSActive/vps-ticks-20260726/` (FTMO 36, redacted_account 25), **300,538,915 rows, no
sampling**, spread expressed in **basis points of mid** via a 0.5%-resolution log histogram.

### 4.1 FTMO (the broker the January replay sizes from — `agent_config.yaml:3160` → `ftmo.yaml`)

| series | ticks | p10 | median | p90 | p99 | zero-spread frac |
|---|---:|---:|---:|---:|---:|---:|
| AUDJPY | 3,059,636 | 0.8035 | 1.0593 | 1.4125 | 2.2131 | 0.0 |
| AUDUSD | 2,318,113 | 0.2884 | 0.4365 | 0.7161 | 0.8710 | 0.0 |
| AUS200_cash | 594,318 | 1.1350 | 1.1350 | 1.1482 | 2.2646 | 0.0 |
| AVAUSD | 1,819,422 | 9.8538 | 32.7341 | 47.8630 | 50.1187 | 0.0 |
| BTCUSD | 12,049,443 | 0.1549 | **0.1603** | 0.2541 | 0.4842 | 0.0 |
| CADJPY | 2,654,819 | 0.6166 | 0.7852 | 1.1350 | 2.1135 | 0.0 |
| CHFJPY | 2,821,115 | 0.6998 | 0.9441 | 1.3032 | 5.4325 | 0.0 |
| DASHUSD | 1,159,997 | 5.6885 | 8.1283 | 9.2257 | 12.1619 | 0.0 |
| ETHUSD | 2,835,787 | 3.1989 | 3.5075 | 3.8459 | 4.2658 | 0.0 |
| EU50_cash | 326,530 | 1.3646 | 1.6982 | 2.6303 | 2.6915 | 0.0 |
| EURGBP | 2,125,147 | 0.4677 | 0.5888 | 0.8128 | 7.7625 | 0.0 |
| EURJPY | 2,733,291 | 0.4842 | 0.6531 | 0.8610 | 3.8905 | 0.0 |
| EURUSD | 2,536,569 | 0.0871 | **0.0881** | 0.2630 | 0.5248 | **0.3060** |
| GBPJPY | 4,261,815 | 0.6998 | 0.8913 | 1.3646 | 4.6238 | 0.0 |
| GBPUSD | 2,947,802 | 0.1496 | 0.2265 | 0.6026 | 3.6308 | 0.0 |
| GER40_cash | 2,640,759 | 0.4519 | 0.5012 | 1.3804 | 1.5136 | 0.0 |
| JP225_cash | 3,772,809 | 1.3964 | 1.4622 | 1.5668 | 2.8840 | 0.0 |
| NATGAS_cash | 231,369 | 179.887 | **192.752** | 211.349 | 213.796 | 0.0 |
| NZDJPY | 2,584,165 | 1.0471 | 1.3183 | 1.7579 | 5.8884 | 0.0 |
| NZDUSD | 1,662,084 | 0.6839 | 1.0351 | 1.4125 | 6.9984 | 0.0 |
| SPN35_cash | 297,356 | 2.7542 | 2.7861 | 2.8184 | 6.9183 | 0.0 |
| UK100_cash | 1,654,793 | 0.6237 | 0.8222 | 4.2658 | 5.8210 | 0.0 |
| UKOIL_cash | 1,627,485 | 7.0795 | 8.7096 | 10.3514 | 11.0917 | 0.0 |
| US100_cash | 11,514,123 | 0.4898 | 0.5754 | 0.6761 | 0.7244 | 0.0 |
| US30_cash | 4,055,135 | 0.3846 | 0.4027 | 0.4842 | 0.5188 | 0.0 |
| US500_cash | 3,134,919 | 0.7328 | 0.7943 | 0.8035 | 0.8511 | 0.0 |
| USDCAD | 1,847,261 | 0.2138 | 0.3508 | 0.4266 | 0.9886 | 0.0 |
| USDCHF | 1,673,058 | 0.4898 | 0.6166 | 0.8610 | 6.0954 | 0.0 |
| USDJPY | 2,035,570 | 0.1245 | 0.1862 | 0.5559 | 0.8035 | 0.0 |
| USOIL_cash | 1,980,315 | 8.3176 | 9.7724 | 12.0226 | 12.7350 | 0.0 |
| XAGAUD | 7,810,321 | 6.6834 | 8.9125 | 11.0917 | 12.4451 | 0.0 |
| XAGEUR | 6,651,057 | 7.2444 | 9.4406 | 11.6145 | 13.0317 | 0.0 |
| XAGUSD | 6,548,918 | 7.2444 | 9.5499 | 11.6145 | 12.8825 | 0.0 |
| XAUAUD | 8,107,477 | 1.1614 | 1.3804 | 1.6406 | 1.7989 | 0.0 |
| XAUEUR | 8,810,902 | 1.6596 | 1.8197 | 2.0654 | 2.3714 | 0.0 |
| XAUUSD | 6,904,623 | 0.9886 | 1.1220 | 1.2883 | 1.3964 | 0.0 |

### 4.2 redacted_account

| series | ticks | p10 | median | p90 | p99 |
|---|---:|---:|---:|---:|---:|
| AUDJPY | 3,072,163 | 0.7161 | 0.9886 | 1.4289 | 2.2646 |
| AUDUSD | 2,752,113 | 0.2884 | 0.4365 | 1.1482 | 1.7378 |
| BTCUSD | 23,646,510 | 3.2359 | **3.5075** | 4.0738 | 5.0119 |
| CHFJPY | 2,621,288 | 0.7499 | 0.7499 | 0.7499 | 0.7499 |
| ETHUSD | 17,454,109 | 2.8510 | 3.1261 | 3.4674 | 3.5481 |
| EURGBP | 2,642,870 | 0.9226 | 1.0593 | 1.4962 | 8.7096 |
| EURJPY | 3,752,399 | 0.4315 | 0.5888 | 0.8128 | 3.4674 |
| EURUSD | 3,127,247 | 0.0871 | 0.0881 | 0.6998 | 1.0593 |
| GBPJPY | 6,220,757 | 0.6095 | 0.8222 | 1.3032 | 4.5709 |
| GBPUSD | 4,106,655 | 0.1496 | 0.2265 | 0.6761 | 4.5709 |
| GER30 | 3,935,308 | 0.7943 | 0.8035 | 0.8128 | 0.8128 |
| JP225 | 6,640,502 | 2.5704 | 3.0200 | 3.2359 | 3.3884 |
| NDX100 | 33,906,232 | 0.5370 | 0.5495 | 0.7079 | 1.4622 |
| NZDJPY | 2,594,720 | 1.1885 | 1.5311 | 2.0417 | 7.0795 |
| NZDUSD | 1,981,199 | 0.3508 | 0.6839 | 1.3964 | 13.8038 |
| SPX500 | 7,609,889 | 0.7674 | 0.7852 | 0.9772 | 2.0417 |
| UK100 | 2,463,234 | 1.7179 | 1.7378 | 1.7783 | 4.5709 |
| UKOUSD | 2,042,948 | 7.1614 | 9.2257 | 10.9648 | 12.0226 |
| US30 | 7,998,677 | 0.4169 | 0.4365 | 0.5370 | 0.9016 |
| USDCAD | 2,500,919 | 0.1413 | 0.2818 | 0.5623 | 1.7783 |
| USDCHF | 1,910,981 | 1.0965 | 1.4791 | 1.8621 | 5.8884 |
| USDJPY | 2,669,828 | 0.3090 | 0.4315 | 0.8035 | 1.2303 |
| USOUSD | 2,545,957 | 6.9984 | 9.4406 | 11.0917 | 12.1619 |
| XAGUSD | 5,742,093 | 9.1201 | 10.2329 | 12.3027 | 13.4896 |
| XAUUSD | 18,449,494 | 1.0839 | 1.1885 | 2.2387 | 3.3113 |

### 4.3 Three-way validation — `l10x_02_spread_bps.py` + `L10X_SPREAD_3WAY_V1.json`

Captured live broker bid/ask at 296 real order instants (Apr–Jul 2026) vs the tick-archive
full-population medians (Jun 18–Jul 24 2026), both in bps of mid:

| captured symbol | n quotes | captured median bps | tick median bps | ratio |
|---|---:|---:|---:|---:|
| GBPJPY | 39 | 0.8429 | 0.8913 | 0.946 |
| BTCUSD | 28 | 0.2896 | 0.1603 | 1.806 |
| XAUUSD | 26 | 1.1099 | 1.1220 | 0.989 |
| USDJPY | 24 | 0.1860 | 0.1862 | 0.999 |
| EURUSD | 24 | 0.0872 | 0.0881 | 0.990 |
| ETHUSD | 19 | 3.4455 | 3.5075 | 0.982 |
| SPX500 (FN) | 14 | 0.7835 | 0.7852 | 0.998 |
| GBPUSD | 14 | 0.2268 | 0.2265 | 1.001 |
| JP225 (FN) | 12 | 3.0509 | 3.0200 | 1.010 |
| US500.cash | 12 | 0.7429 | 0.7943 | 0.935 |
| US30 (FN) | 10 | 0.4671 | 0.4365 | 1.070 |
| JP225.cash | 10 | 1.4459 | 1.4622 | 0.989 |
| GER30 (FN) | 10 | 0.8075 | 0.8035 | 1.005 |
| US30.cash | 8 | 0.4243 | 0.4027 | 1.054 |
| UK100.cash | 8 | 1.4718 | 0.8222 | 1.790 |
| AUDUSD | 6 | 0.2895 | 0.4365 | 0.663 |
| UK100 (FN) | 6 | 1.7523 | 1.7378 | 1.008 |
| GER40.cash | 6 | 0.6616 | 0.5012 | 1.320 |
| NZDJPY | 6 | 1.5226 | 1.3183 | 1.155 |
| US100.cash | 4 | 0.6715 | 0.5754 | 1.167 |
| NDX100 (FN) | 4 | 0.7195 | 0.5495 | 1.309 |
| XAGUSD | 2 | 9.9314 | 9.5499 | 1.040 |
| NZDUSD | 2 | 1.0635 | 1.0351 | 1.027 |

**n = 23 symbols, median ratio 1.008, mean 1.098, min 0.663, max 1.806.** Two independent real
sources — captured quotes at actual order instants, and a 300 M-tick population — agree to within
1%. The real-spread column used everywhere below is therefore load-bearing evidence, not a model.

### 4.4 X12 — a broker-level difference no model in the tree carries

**FTMO BTCUSD median spread is 0.1603 bps; redacted_account BTCUSD is 3.5075 bps — 21.9× wider**
(12.0 M vs 23.6 M ticks). redacted_account USDCHF is 2.4× FTMO's, USDJPY 2.3×, EURGBP 1.8×. FTMO's
EURUSD prints an **exactly zero spread on 30.60%** of its ticks (redacted_account 30.18%) — a locked-feed
artifact that any model treating spread as strictly positive will mis-handle.

---

## 5. X5 — THE FROZEN COST MODEL IS SCRAMBLED, NOT UNIFORMLY BIASED

### 5.1 Correction to F7/F8 (this lane's own first pass) and to the established 7.3–8.5× claim

The first pass reported **overcharge_ratio 10.051** by dividing the January pool's mean
`spread_r` (0.564213, denominated in the *pool's* risk distances) by the live trades' mean real
`spread_r` (0.056133, denominated in the *live book's* risk distances). Those are different
denominators: **the pool's median stop is 0.0905% of price and the live book's is 0.3063%
(3.384× wider)** — §6. The ratio is therefore unit-mismatched and is superseded.

**Matched-unit method** (`l10x_06_recost.py` → `L10X_POOL_RECOST_V1.json`): express every cost
term in **price units**, then re-denominate by each *pool row's own* `risk_distance`
(verified `risk_distance == |entry_price − stop_loss|` exactly on 27,658/27,658 rows, max relative
error 0.0).

- real spread price = tick-median bps × that row's `entry_price` / 1e4
- real commission price = measured `comm_r × sl_distance` from real broker deals (volume-invariant)
- real slippage price = measured `slip_r × sl_distance` from real broker deals
- swap charged **0** (the pool's hard horizon is 2 h — see §9)

| | frozen | real | ratio |
|---|---:|---:|---:|
| total cost mean, R/trade | **0.663161** | **0.189297** | **3.503×** |
| spread mean, R/trade | 0.564213 | 0.124828 | **4.520×** |
| commission mean, R/trade | 0.065220 | 0.057102 | 1.142× |
| slippage mean, R/trade | 0.020000 | 0.007367 | 2.715× |
| total cost median, R/trade | 0.303108 | 0.135077 | 2.244× |

**4.520× on spread is the corrected pool-wide figure.** It is below the established 7.3–8.5× band
and far below the first pass's 10.05×.

### 5.2 The per-symbol table — where the correction actually inverts

`spread_r` medians, January pool rows, frozen vs real, with the gate outcome at each:

| pool symbol | n | frozen spread_r | real spread_r | **ratio** | real total_r | gross mean | pass FROZEN gate | pass REAL gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NAS100 | 1,622 | 1.6422 | 0.0484 | **33.90×** | 0.0484 | −0.3456 | **0** | 1,277 |
| SPX500 | 1,943 | 1.8083 | 0.0996 | **18.16×** | 0.1176 | −0.2134 | **0** | 973 |
| ETHUSD | 934 | 0.8320 | 0.0894 | 9.31× | 0.2102 | −0.1901 | 7 | 326 |
| JP225 | 1,348 | 0.6285 | 0.0961 | 6.54× | 0.0961 | −0.0937 | 12 | 698 |
| UK100 | 2,016 | 0.6994 | 0.1164 | 6.01× | 0.1164 | −0.4219 | 3 | 760 |
| US30_cash | 1,563 | 0.2490 | 0.0614 | 4.06× | 0.0614 | −0.2026 | 300 | 1,105 |
| GER40 | 1,413 | 0.2164 | 0.0540 | 4.01× | 0.0540 | −0.0122 | 235 | 1,050 |
| GBPUSD | 1,474 | 0.1830 | 0.0557 | 3.29× | 0.1840 | −0.5312 | 230 | 507 |
| CHFJPY | 575 | 0.3019 | 0.1124 | 2.69× | 0.1614 | −0.0755 | 42 | 240 |
| USDJPY | 893 | 0.0547 | 0.0277 | 1.97× | 0.1238 | −0.0945 | 407 | 518 |
| AUDUSD | 654 | 0.0793 | 0.0473 | 1.68× | 0.1271 | −0.0903 | 265 | 376 |
| NZDUSD | 813 | 0.2021 | 0.1371 | 1.47× | 0.2492 | −0.1349 | 99 | 229 |
| EURGBP | 828 | 0.2435 | 0.1781 | 1.37× | 0.3067 | −0.2952 | 67 | 148 |
| USDCAD | 1,243 | 0.0709 | 0.0685 | 1.04× | 0.1662 | −0.4692 | 233 | 371 |
| USDCHF | 906 | 0.0875 | 0.0854 | 1.03× | 0.1547 | −0.1357 | 296 | 431 |
| AUDJPY | 758 | 0.1066 | 0.1098 | 0.97× | 0.1883 | −0.2293 | 194 | 257 |
| GBPJPY | 777 | 0.1352 | 0.1413 | 0.96× | 0.2021 | −0.1845 | 227 | 259 |
| XAGUSD | 928 | 0.0703 | 0.1238 | **0.57×** | 0.1253 | −0.1146 | 605 | 364 |
| XAUUSD | 2,356 | 0.0511 | 0.0905 | **0.57×** | 0.1036 | −0.0870 | 1,986 | 1,265 |
| EURUSD | 808 | 0.0073 | 0.0168 | **0.44×** | 0.1306 | −0.2029 | 526 | 478 |
| USOIL_cash | 733 | 0.0270 | 0.2949 | **0.09×** | 0.2949 | −0.1508 | 574 | 86 |
| UKOIL_cash | 790 | 0.0258 | 0.3088 | **0.08×** | 0.3088 | −0.1178 | 659 | 75 |
| BTCUSD | 1,203 | 0.0001 | 0.0059 | **0.017×** | 0.1698 | −0.0494 | 215 | 527 |

**Seven symbols are overcharged 3–34×. Six are undercharged 1.7–58×.** A uniform bias would cancel
in ranking; a scrambled one actively mis-ranks the universe, and the cost gate is precisely a ranking
device. BTCUSD's frozen spread_r median of **0.0001** means the frozen model charges a **2.8-cent
spread on Bitcoin** while the broker quotes ~$1.42.

---

## 6. X6 — THE COST GATE DELETED THE INDEX COMPLEX FROM THE UNIVERSE

Gate limbs confirmed at source (correcting the swarm brief, which names only the weaker one):
`src/components/broker_net_cost_engine.py:859-866` **`spread_r > max_spread_r`** and `:923-927`
**`total_cost_r > max_total_cost_r`**, with `config/agent_config.yaml:715` `= 0.10` and `:716` `= 0.15`.

Pool-wide gate counterfactual (`L10X_POOL_RECOST_V1.json`):

| | n pass | frac | spread limb refuses | total limb refuses | gross mean of passed |
|---|---:|---:|---:|---:|---:|
| FROZEN cost | 7,210 | 26.068% | 17,259 | 20,074 | −0.11185 |
| **REAL cost** | **12,629** | **45.661%** | 11,613 | 12,531 | −0.14874 |

**+5,419 candidates, +75.2% more admitted.** And the concentration:

| index complex (SPX500, NAS100, JP225, UK100, GER40, US30_cash) | value |
|---|---:|
| rows | 9,905 (35.81% of pool) |
| frozen mean cost | **1.235304 R/trade** |
| real mean cost | **0.109912 R/trade** (11.24× over) |
| pass the gate at FROZEN cost | **550 (5.55%)** |
| pass the gate at REAL cost | **5,863 (59.19%)** |
| SPX500 admitted at frozen cost | **0 of 1,943** |
| NAS100 admitted at frozen cost | **0 of 1,622** |
| JP225 + UK100 admitted at frozen cost | **15 of 3,364 (0.45%)** |

**SPX500 and NAS100 — 3,565 rows, 12.9% of the pool — were admitted exactly zero times, on a spread
charge 18× and 34× the real broker spread.** The January replay's admitted set was structurally
FX+metals+crypto; the entire index complex was invisible to it for a cost that does not exist.

**And it was not marginal.** Verified independently straight from the working set: the **minimum**
frozen `spread_r` over all 1,943 SPX500 rows is **0.24479** and over all 1,622 NAS100 rows is
**0.16326** — both above the 0.10 cap. **Not one candidate on either symbol could have passed under
any circumstance in the entire month.** Median frozen `spread_r` is 1.80835 (SPX500) and 1.64222
(NAS100) against real values of 0.09956 and 0.04844.

**Honest counterweight, stated because it matters more than the finding:** the index complex's
takeable gross is **−0.1333 R/trade** and its net at real cost is **−0.2430**. Admitting it would
not have rescued the month. The defect is that the decision was made *for the wrong reason*, not
that a fortune was left on the table.

---

## 7. X7 — THE HONEST LEDGER: WHAT CORRECTING THE COST MODEL IS ACTUALLY WORTH

`l10x_07_bottomline.py` → `L10X_BOTTOMLINE_V1.json`. `gross_r` is fill-blind path value (cost-free);
"takeable" removes W0-capture's `born_past_stop` cohort (rule `mkt_r_prev_close <= −1.0` on the
zero-look-ahead anchor; 17 rows unanchored, 24,142 takeable of 27,658).

| book | n | gross | frozen cost | real cost | **net @ frozen** | **net @ real** |
|---|---:|---:|---:|---:|---:|---:|
| A · all rows | 27,658 | −0.217496 | 0.663161 | 0.189297 | **−0.880657** | **−0.406793** |
| B · takeable only | 24,142 | −0.104290 | 0.662353 | 0.187624 | −0.766643 | **−0.291914** |
| C · takeable, FROZEN gate | 6,984 | −0.083539 | 0.086771 | 0.116937 | −0.170310 | −0.200476 |
| D · takeable, REAL gate | 11,879 | −0.095251 | 0.359330 | 0.067123 | −0.454582 | **−0.162374** |
| E · takeable, REAL gate, cheapest half by real cost | 5,939 | −0.077660 | 0.325980 | 0.037670 | −0.403640 | **−0.115330** |

**Correcting the cost model is worth +0.473864 R/trade** (A: −0.880657 → −0.406793). Adding the
takeability repair takes it to −0.291914; re-gating on real cost to −0.162374; the cheapest half to
−0.115330. **None of these is positive.** The gross deficit survives every cost repair available.

### 7.1 Per-symbol, takeable rows at real cost

| symbol | n | gross | real cost | net @ real | pass REAL gate |
|---|---:|---:|---:|---:|---:|
| XAUUSD | 2,329 | −0.0764 | 0.1145 | −0.1910 | 1,238 |
| SPX500 | 1,717 | −0.1099 | 0.1525 | −0.2624 | 897 |
| NAS100 | 1,483 | −0.2842 | 0.0671 | −0.3514 | 1,138 |
| US30_cash | 1,478 | −0.1567 | 0.0812 | −0.2379 | 1,020 |
| UK100 | 1,412 | −0.1854 | 0.1465 | −0.3320 | 613 |
| **GER40** | 1,400 | **−0.0030** | 0.0735 | −0.0765 | 1,037 |
| JP225 | 1,283 | −0.0478 | 0.1336 | −0.1814 | 651 |
| BTCUSD | 1,177 | −0.0284 | 0.2187 | −0.2470 | 521 |
| XAGUSD | 925 | −0.1117 | 0.2043 | −0.3160 | 364 |
| ETHUSD | 916 | −0.1742 | 0.2666 | −0.4408 | 326 |
| USDJPY | 892 | −0.0934 | 0.1798 | −0.2732 | 518 |
| GBPUSD | 823 | −0.1603 | 0.1754 | −0.3357 | 493 |
| USDCAD | 798 | −0.1770 | 0.2590 | −0.4360 | 310 |
| **USDCHF** | 774 | **+0.0117** | 0.2149 | −0.2032 | 407 |
| NZDUSD | 737 | −0.0457 | 0.3240 | −0.3697 | 229 |
| UKOIL_cash | 735 | −0.0518 | 0.4199 | −0.4717 | 75 |
| EURUSD | 728 | −0.1153 | 0.1745 | −0.2898 | 439 |
| USOIL_cash | 725 | −0.1414 | 0.4175 | −0.5589 | 86 |
| GBPJPY | 689 | −0.0803 | 0.2557 | −0.3361 | 235 |
| EURGBP | 666 | −0.1237 | 0.3335 | −0.4572 | 148 |
| AUDJPY | 640 | −0.0872 | 0.2735 | −0.3608 | 252 |
| EURJPY | 628 | −0.0233 | 0.2191 | −0.2424 | 307 |
| AUDUSD | 612 | −0.0279 | 0.1789 | −0.2068 | 335 |
| CHFJPY | 575 | −0.0755 | 0.2338 | −0.3093 | 240 |

**X11: `USDCHF` is the only symbol in the pool with positive takeable gross (+0.0117, n=774), and
`GER40` is the only other one at breakeven (−0.0030, n=1,400).** Both are drowned by real cost at
the pool's stop geometry.

### 7.2 Per-family, takeable rows at real cost — the cost dispersion is 12×

| family | n | gross | **real cost** | net @ real |
|---|---:|---:|---:|---:|
| current_fvg_fill | 7,145 | −0.1415 | 0.1503 | −0.2918 |
| liquidity_sweep_reclaim | 4,475 | −0.0415 | 0.2158 | −0.2573 |
| displacement_continuation | 4,469 | −0.0885 | 0.1057 | −0.1942 |
| cross_asset_lead_lag | 2,083 | −0.1307 | 0.2978 | −0.4285 |
| **structural_distance_extreme** | 1,993 | −0.1820 | **0.4914** | **−0.6734** |
| current_ob_retest | 1,292 | −0.0737 | 0.1306 | −0.2043 |
| session_open_range_break | 987 | −0.0747 | 0.0876 | −0.1623 |
| current_breaker_re_entry | 796 | −0.0843 | 0.1510 | −0.2353 |
| volatility_compression_expansion | 605 | −0.0868 | 0.0505 | −0.1373 |
| **regime_transition_break** | 297 | **−0.0067** | **0.0405** | **−0.0472** |

**Real cost per family ranges 0.0405 → 0.4914 R/trade, a 12.1× spread.**
`structural_distance_extreme` pays 0.49 R of real broker cost per trade because it enters at
structural extremes on the tightest stops in the pool; `regime_transition_break` pays 0.04 and is
the closest thing to breakeven anywhere in the estate (−0.0472 net at real cost, n=297).

---

## 8. X8 — STOP GEOMETRY, AND THE MINIMUM VIABLE STOP

`l10x_05_stopgeom.py` → `L10X_STOP_GEOMETRY_V1.json`. Stop distance as % of entry price.

| pool symbol | broker symbol | n pool | n live | pool stop % | live stop % | live / pool |
|---|---|---:|---:|---:|---:|---:|
| US30_cash | US30.cash | 1,563 | 8 | 0.06557 | 0.65626 | **10.01×** |
| UK100 | UK100.cash | 2,016 | 8 | 0.07062 | 0.70173 | 9.94× |
| SPX500 | SPX500 | 1,943 | 14 | 0.07978 | 0.76438 | 9.58× |
| JP225 | JP225.cash | 1,348 | 10 | 0.15209 | 1.42684 | 9.38× |
| GER40 | GER40.cash | 1,413 | 6 | 0.09276 | 0.86822 | 9.36× |
| BTCUSD | BTCUSD | 1,203 | 28 | 0.27047 | 0.76418 | 2.83× |
| ETHUSD | ETHUSD | 934 | 19 | 0.39246 | 0.97999 | 2.50× |
| XAUUSD | XAUUSD | 2,356 | 26 | 0.12404 | 0.25999 | 2.10× |
| NAS100 | US100.cash | 1,622 | 4 | 0.11879 | 0.18896 | 1.59× |
| GBPUSD | GBPUSD | 1,474 | 14 | 0.04065 | 0.03444 | 0.85× |
| EURUSD | EURUSD | 808 | 24 | 0.05255 | 0.03631 | 0.69× |
| GBPJPY | GBPJPY | 777 | 39 | 0.06309 | 0.04233 | 0.67× |
| AUDUSD | AUDUSD | 654 | 6 | 0.09220 | 0.04904 | 0.53× |
| USDJPY | USDJPY | 893 | 24 | 0.06715 | 0.02900 | 0.43× |

**Pooled: pool median stop 0.090509% of price, live 0.306320% — 3.384× wider.** The gap is entirely
in index CFDs (9.4–10.0× tighter in the pool) and inverts on FX. Because `cost_r = cost_price /
risk_distance` is an identity, the pool's index-CFD R-denominated costs are inflated ~10× by stop
choice alone, on top of the model error.

### 8.1 The minimum stop that keeps REAL spread under the 0.10 R cap

`l10x_09_hours_and_minstop.py` → `L10X_HOURS_MINSTOP_V1.json`. Widen factor = required stop /
current median stop.

| symbol | pool stop % | real spread (price) | min stop % for spread ≤ 0.10 R | widen × needed |
|---|---:|---:|---:|---:|
| UKOIL_cash | 0.2822 | 0.056144 | 0.8710 | **3.09** |
| USOIL_cash | 0.3355 | 0.058525 | 0.9772 | **2.91** |
| EURJPY | 0.0333 | 0.012009 | 0.0653 | **1.96** |
| EURGBP | 0.0331 | 5.106e-05 | 0.0589 | **1.78** |
| GBPJPY | 0.0629 | 0.018875 | 0.0891 | 1.42 |
| NZDUSD | 0.0763 | 6.039e-05 | 0.1035 | 1.36 |
| XAGUSD | 0.7501 | 0.087089 | 0.9550 | 1.27 |
| UK100 | 0.0705 | 0.833664 | 0.0822 | 1.17 |
| CHFJPY | 0.0835 | 0.018714 | 0.0944 | 1.13 |
| AUDJPY | 0.0969 | 0.011276 | 0.1059 | 1.09 |
| SPX500 | 0.0799 | 0.549450 | 0.0794 | 0.99 |
| JP225 | 0.1501 | 7.748030 | 0.1462 | 0.97 |
| ETHUSD | 0.3885 | 1.085270 | 0.3508 | 0.90 |
| XAUUSD | 0.1286 | 0.517572 | 0.1122 | 0.87 |
| USDCHF | 0.0721 | 4.886e-05 | 0.0617 | 0.86 |
| USDCAD | 0.0510 | 4.847e-05 | 0.0351 | 0.69 |
| US30_cash | 0.0654 | 1.977230 | 0.0403 | 0.62 |
| GBPUSD | 0.0406 | 3.047e-05 | 0.0226 | 0.56 |
| GER40 | 0.0926 | 1.249710 | 0.0501 | 0.54 |
| NAS100 | 0.1193 | 1.469120 | 0.0575 | 0.48 |
| AUDUSD | 0.0936 | 2.938e-05 | 0.0437 | 0.47 |
| USDJPY | 0.0666 | 0.002934 | 0.0186 | 0.28 |
| EURUSD | 0.0526 | 1.030e-05 | 0.0088 | 0.17 |
| BTCUSD | 0.2688 | 1.454360 | 0.0160 | 0.06 |

**Median widen factor 0.939; 14 of 24 symbols already sit inside the cap at real spread.** The
0.10 R cap is a *reasonable* limit — only oil (2.9–3.1×), EURJPY (1.96×) and EURGBP (1.78×) genuinely
need a wider stop. **It was the charge that was wrong, not the limit.**

---

## 9. X9 — TRADING-HOUR AVAILABILITY IS NOT A MATERIAL DEFECT

Tick mass per instrument by **true UTC** hour (broker hour − 3), crossed with the pool's decision
hours. An hour holding <0.5% of that instrument's daily tick mass is called THIN.

- **531 of 27,658 pool rows (1.92%) fall in a THIN hour.**
- **435 rows fall in an hour with literally zero ticks** for that instrument.
- Worst offenders: JP225 7.42% thin (48 zero-tick rows), XAGUSD 3.45% (32), SPX500 3.40% (66),
  XAUUSD 3.27% (77), NAS100 3.02% (49), AUDUSD 2.91% (0), USDJPY 2.80% (0), US30_cash 2.75% (43),
  UK100 2.63% (53), USOIL 2.46% (18), GER40 2.34% (33), UKOIL 2.03% (16). All FX crosses: 0.00%.

W0-dictionary D12 found 59.881% of pool rows carry `route_session = off_configured_session` with
only 1,079 blocked. **That is not the same as unquotable**: measured against real tick availability,
only 1.92% of the pool sits in an hour the broker barely quotes. Off-session generation is a
labelling question, not an executability one.

---

## 10. PRESERVED FINDINGS F1–F14 (first l10 pass), with corrections marked

### F1 — order type census: 631 of 633 orders are market
FTMO 267 orders (266 market, 1 CLOSE_BY, **0 pending**); redacted_account 366 (364 market, 2 pending).
Strategy magic `20260401`. Lifecycle corroboration: `entry_fill_reconciled` 149/149 carry
`action = 1 TRADE_ACTION_DEAL`, `type_filling = IOC`, `retcode = 10009`.
The two pending orders are both `magic 99999999`, comment `preflight_test`, XAUUSD BUY_LIMIT,
**CANCELED with `sit_seconds = 0`** — 2026-04-30T23:49:30Z and 2026-05-28T12:57:45Z (true UTC).

### F2 — real fill rate, re-derived on the corrected clock (§2)
`l10x_08_fillprob.py` → `L10X_FILLPROB_REPLACEMENT_V1.json`.

| | n market | filled | rate | strategy-magic rate |
|---|---:|---:|---:|---:|
| FTMO | 266 | 266 | **1.00000** | 1.00000 |
| redacted_account | 364 | 361 | **0.99176** | 0.99110 |
| **pooled** | **630** | **627** | **0.99524** | — |

By **true UTC** session (corrected — the first pass's buckets were 3 h late):

| session (true UTC) | FTMO n / rate | redacted_account n / rate |
|---|---:|---:|
| asia (00–07) | 97 / 1.00000 | 117 / 1.00000 |
| london (07–12) | 33 / 1.00000 | 46 / **0.97826** |
| ny_overlap (12–17) | 80 / 1.00000 | 126 / **0.98413** |
| late_ny (17–24) | 56 / 1.00000 | 75 / 1.00000 |

All three non-fills are redacted_account, strategy magic, state REJECTED, comment **"Execution not
allowed"** — a terminal/symbol permission block, not a price rejection:
ticket 248277482 GBPJPY 2026-06-25T07:05:03Z · ticket 249094091 JP225 2026-06-29T15:59:10Z ·
ticket 250099022 SPX500 2026-07-02T16:02:46Z (all true UTC).

### F3 — real entry slippage vs the flat 0.02 R model
n = 140 reconciled fills. Mean **+0.013232 R**, median **+0.000398**, p25 −0.0, p75 +0.017998,
p90 +0.050233, min −0.061404, max +0.171569. 37 fills exactly zero, 78 adverse, 25 favourable.
Modelled flat `0.02` at `config/agent_config.yaml:740`
(`selected_cell_default_expected_slippage_r`). **The model overcharges 108 of 140 fills (77.14%).**
By class (`L10_DISPLACEMENT_V1.json`): fx n=54 mean +0.030625 (median +0.021665, max +0.171569),
crypto n=23 +0.004424, metals n=14 +0.002782, index n=49 +0.001184.

### F4 — latency
| | n | min | p25 | median | p75 | p90 | p99 | max | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FTMO all | 266 | 130 | 137 | **145** | 151 | 155 | 164 | **193** | 144.5 |
| FTMO entry | 131 | — | — | 142 | — | 154 | — | 157 | — |
| FTMO close | 135 | — | — | 146 | — | 156 | — | 193 | — |
| redacted_account all | 364 | 1 | 6 | **374** | 632 | 1,104 | 12,617 | **148,112** | 1,084.5 |
| redacted_account entry | 169 | — | — | **488** | — | 1,242 | — | 14,019 | — |
| redacted_account close | 195 | — | — | **7** | — | 750 | — | 148,112 | — |

Buckets (ms): FTMO `<50` 0 / `50–250` **266** / `250–1000` 0 / `≥1000` 0. redacted_account `<50` **121** /
`50–250` 5 / `250–1000` **197** / `≥1000` 36 / `≥10000` 5.
**FTMO is uniform at ~145 ms with zero outliers. redacted_account is bimodal**: closes execute server-side
(median 7 ms, 62.05% under 50 ms) while opens take median 488 ms — 3.4× FTMO's entry latency, with a
14.0 s worst entry and a 148.1 s worst close. Not a symbol or era effect: fast and slow cohorts share
symbols, dates and filling mode.

### F5 — commission truth
**Exactly $5.00/lot round-turn on every FX pair at BOTH firms. Exactly $0.00 on every index CFD.**
FTMO total −$1,078.78 over 311.84 entry lots (blended −3.4594/lot); redacted_account −$1,345.20 over
421.00 lots (−3.19525/lot). `fee` total is 0.0 at both. Crypto is a fraction of notional, so the
per-lot figure moves with price: FTMO BTCUSD −40.02559, ETHUSD −11.33708; redacted_account BTCUSD
−26.45303, ETHUSD −0.71599.
Measured `commission_r` (live R units) n=140: mean 0.060264, median 0.051112, p10 0.0, p90 0.147399,
max 0.289211. By class: fx n=54 mean 0.116362 (median 0.108326), crypto n=23 0.090516 (0.066316),
metals n=14 0.005110, **index n=49 exactly 0.0**.
Frozen model charges 0.065220 R — **1.14× real** (matched units, §5.1). Commission is the one term
the frozen model gets nearly right.

### F6 — swap truth
FTMO −$363.08 on 37 deals (13.81% of deals); redacted_account −$824.88 on 41 (11.36%).
**34 of 140 positions (24.29%) incur any swap.** Measured `swap_r`: mean 0.020699, median −0.0,
p90 0.056946, min −0.003508, **max 0.715043 on a single position**. By class: index n=49 mean
0.031534 (max 0.715043), crypto n=23 0.058814 (max 0.364093), **fx and metals exactly 0.0**.
`swap_mode` 1 on 39 symbols, 5 on 3. **Triple-swap day differs between the firms**:
`swap_rollover3days = 3` (Wednesday) on 23 traded symbols and `5` (Friday) on 19.
Frozen model charges 0.013720 R against 0.020699 measured — **the only term the frozen model
UNDERCHARGES, by 1.51×** — though at the pool's 2 h horizon the correct charge is ~0 and this lane
charges 0 (§5.1).

### F7 — spread truth *(corrected here)*
The truthed spread model at band `mid` is validated against 135 real broker quotes at real fill
instants: **model/real ratio mean 1.002**. The LIVE cost path does not model spread at all — it uses
the broker quote itself (`tick_cost.source_status = captured` on 140/140,
`model_minus_real_max = 0.0`).
Real spread in live R units: mean 0.056133, median 0.034965, p10 0.006095, p90 0.165789, max 0.321429.
~~overcharge_ratio 10.051~~ — **STRUCK, unit-mismatched (§5.1). The matched-unit figure is 4.520× on
the mean and 0.017×–33.90× per symbol.**

### F8 — total cost truth *(corrected here)*
All-in real broker cost on 140 real fills, **in the live book's R units**: mean **0.150328 R**,
median 0.098965, p10 0.015101, p90 0.321593, min −0.002201, max 0.723611. Decomposition: spread
0.056133 + commission 0.060264 + slippage 0.013232 + swap 0.020699.
~~ratio 4.41× vs the frozen 0.663161~~ — **STRUCK, same unit mismatch. In the January pool's own R
units the real all-in cost is 0.189297 R/trade and the ratio is 3.503× (§5.1).**

### F9 — stop slippage: real stops do not fill at −1R
n = 167 clean stop exits. Mean **+0.032236 R worse than the recorded stop**, median +0.008304,
p75 +0.034884, p90 +0.066667, p95 +0.100000, p99 +0.188679, max +0.935484.
**83.83% adverse; only 13.17% fill exactly at the stop.** Tail: worse than 0.02 R 58 (34.73%),
worse than 0.05 R 30 (17.96%), worse than 0.10 R 8 (4.79%), worse than 0.25 R 2 (1.20%).
By class: **fx n=69 mean 0.059002** (p95 ~0.097), crypto n=25 0.026603, metals n=27 0.011636,
index n=46 0.007240.
Worst events: +0.9355 USDJPY 2026-06-24T09:41:25 (ftmo), +0.6167 USDJPY 2026-06-30T09:12:3x (ftmo).
Method: SL in force at exit reconstructed from the runtime `sltp_modify_result` timeline (271 rows,
retcode 10009 only) over the entry order SL; 92 of 300 positions have a captured modify timeline;
13 exits beating their recorded stop by >0.02 R excluded.
Target slippage n=58: mean +0.041455, median −0.000433, p99 +1.189655, max +1.65.
**Pool impact: the January pool takes a full stop on 54.4% of candidates; at +0.032236 R per stop
that is +0.017536 R/trade of cost the research walk never charges.**

### F10 — exit mechanics: the broker, not the book, closes most positions
| | SL | TP | EXPERT (book) | MOBILE (manual) | positions | multi-exit |
|---|---:|---:|---:|---:|---:|---:|
| FTMO | 80 (58.39%) | 28 (20.44%) | 20 (14.60%) | 9 (6.57%) | 131 | 6 (4.58%) |
| redacted_account | 101 (52.60%) | 32 (16.67%) | 58 (30.21%) | 1 (0.52%) | 169 | 22 (13.02%) |

**78.83% of FTMO exits and 69.27% of redacted_account exits are executed server-side by a resting SL/TP.**
**Partial fills: `state = PARTIAL` on 0 of 633 orders; 0 filled with residual volume; 0 positions
partially closed and left open.**

### F11 — broker behaviour: nothing the model fears ever happened
Retcodes: `entry_fill_reconciled` DONE 149/149. `sltp_modify_result` DONE 157 / NO_CHANGES 106 /
MARKET_CLOSED 8. `close_position_result` DONE 10/10.
**Never observed in 430 order_sends: REQUOTE (10004) 0 · INVALID_STOPS (10016) 0 · PRICE_CHANGED
(10020) 0 · DONE_PARTIAL (10010) 0 · TIMEOUT (10012) 0 · NO_MONEY (10019) 0 · TOO_MANY_REQUESTS
(10024) 0.**
**106 of 430 order_sends (24.65%) are SL/TP modifies that changed nothing** ("No changes").
All 8 MARKET_CLOSED are GER40.cash/GER30 SL-TP modifies at 07:52–07:59 UTC on 2026-06-27, before the
German cash index opens; the book retried 1 s later and was refused again.
**Stop-level constraints: `trade_stops_level` is 0 on 40 of 42 traded symbols** (1 point on
redacted_account BTCUSD and ETHUSD) and `trade_freeze_level` is 0 everywhere. There is effectively **no
minimum-distance constraint** at either broker.
**`order_send` returns `result.price = 0.0` on 430 of 430 results at BOTH brokers.** Any code
reading `result.price` as the fill price gets zero, always; the fill price must come from the deal.

### F12 — the no-fill logger has never captured a usable observation
All **446** rows of `nofill_forward_source_capture.jsonl` (2026-05-10T16:30:00Z → 2026-06-02T07:00:00Z)
are fail-closed on every field: `native_pending_order_type_status = SOURCE_FIELD_MISSING_FAIL_CLOSED`
446/446 · `cancel_expiry_reason_status = LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` 446/446 ·
`entry_touch_spread_status = QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` 446/446 ·
`side_aware_entry_touch_status`, `protective_area_touch_status`, `terminal_area_touch_status` all
`LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` 446/446 ·
`execution_quality_label_status = EXECUTION_QUALITY_LABEL_CLOSED_NOT_EMITTED` 446/446 ·
`slippage_label_status = SLIPPAGE_LABEL_CLOSED_NOT_EMITTED` 446/446 ·
`same_tick_same_bar_ambiguity_status = UNRESOLVED_REQUIRES_FORWARD_PATH_JOIN` 446/446 ·
`entry_touch_first_utc` and `cancel_expiry_utc` are the literal fail-closed strings on 446/446.
**The infrastructure built to answer "did the limit fill" has zero observations — which X3 explains:
there were never any limits to observe.**

### F13 — the deviation cap is inert
`src/components/execution.py:2459` → `return max(1, int(float(sym_info.spread)))`, passed at `:3541`
as `request["deviation"]`. Over 140 real fills the guard used a mean **38.49%** of its allowance and
was **exceeded up to 3.0×**; 39 fills used >50%, **20 fills (14.29%) used >90%**, and the broker
returned `10009 DONE` every single time. Worst cases include EURUSD with `deviation = 1` and 3.0
points of slippage. Deviation values actually sent range 1 → 1000 (most common: 3 ×15, 55 ×9, 1 ×9,
100 ×7, 45 ×6, 200 ×6). Corroborated by zero REQUOTE and zero PRICE_CHANGED retcodes.

### F14 — the live pretrade cost model mis-stamps 3.38% of its own quotes
`pretrade_cost_model.tick_cost.time_utc` carries **broker wall clock labelled +00:00 on 10 of 296
captures (3.38%)**, offset −10,799 to −10,798 s (exactly 3.00 h). Affected symbols: SPX500, JP225,
NZDJPY, UK100, GBPJPY — all redacted_account. The bid/ask **values** are correct (F7 validates them);
only the timestamp is wrong. Healthy quote age: n=284, median **0.864 s**, p90 2.157 s, max 10.185 s.
**This is the same +3 h defect X1 measures in the raw broker files, leaking into the runtime's own
capture.**

### Unresolved
9 fills could not be reconciled to a deal (EURUSD 2026-06-19T11:30:56Z, 5 attempts, and 8 others);
they are excluded from every n above.

---

## 11. X10 — EMPIRICAL REPLACEMENT VALUES FOR `execution_fill_probability`

Modelled: **0.92** for the `limit_marketable` branch (`src/components/poi_execution_lifecycle.py:174-176`),
a distance-scaled else-branch (`:178-181`) down to 0.0401331; pool mean 0.805058 over 7,400 distinct
values.

| quantity | empirical value | n |
|---|---:|---:|
| market-order acceptance, FTMO | **1.00000** | 266 |
| market-order acceptance, redacted_account | **0.99176** | 364 |
| market-order acceptance, pooled | **0.99524** | 630 |
| market-order acceptance, strategy magic only | FTMO 1.00000 / FN 0.99110 | 255 / 337 |
| limit-order fill probability | **UNMEASURABLE** | 0 |

Per session (true UTC) and per symbol tables are in `L10X_FILLPROB_REPLACEMENT_V1.json`
(`by_true_utc_session`, `by_true_utc_hour`, `by_symbol` for each account). Every FTMO cell is 1.0;
the only sub-1.0 cells are redacted_account london 0.97826 and ny_overlap 0.98413, each explained by one
"Execution not allowed" rejection.

> **Do not substitute 0.99524 for 0.92 in the research model.** That would be a category error. The
> research model prices whether a **resting limit gets hit**; the measurement is whether a **market
> order is accepted**. Those are different events, and the first has never occurred in this system
> (X3). The honest statement is: the research model's fill probability is **unfalsifiable from live
> evidence**, and the correct repair is to change the research contract to the one the engine
> actually runs (market at the decision quote), not to recalibrate a probability for an order type
> that is never sent.

---

## 12. WHAT THIS LANE CHANGES, AND WHAT IT DOES NOT

**Changes:**
1. The cost model's error is **3.503× all-in / 4.520× on spread**, not 7.3–8.5× and not 10.05×; and
   it is **scrambled per symbol (0.017×–33.90×)**, which is a worse failure mode than a uniform bias.
2. The cost gate **structurally deleted the index complex** — 0 of 3,565 SPX500+NAS100 rows admitted
   — for a charge 18–34× the real broker spread.
3. **The live engine cannot place a limit order.** 41.5% of the pool models an order type that has
   never been sent. W0-capture's born-past-stop artifact is a research-only defect.
4. Every broker timestamp on this machine is **true UTC + 3.00 h**, measured on 140 paired records;
   the same defect leaks into 3.38% of the runtime's own quote captures.
5. The stop-slippage charge the research walk omits is **+0.0175 R/trade**.
6. The flat 0.02 R slippage allowance **overcharges 77.14% of real fills**; real mean is 0.0132 R.
7. Real broker spread is now measured at full population (300.5 M ticks) and validated 1.008× against
   296 live quotes at real order instants.

**Does not change:** the January pool stays negative under every honest repair available here —
−0.4068 R/trade all-in, −0.2919 takeable, −0.1624 at the real gate, −0.1153 on the cheapest half.
The cost repair is worth **+0.4739 R/trade** and it is not enough. **The gross deficit is the binding
constraint and nothing in the broker's behaviour explains it.**

---

## 13. ARTIFACTS

Receipts (all under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`):

| file | contents |
|---|---|
| `l10_RESULT.md` | this file |
| `l10_RESULT.json` | machine-readable index of X1–X13 and F1–F14 |
| `L10X_CLOCK_V1.json` | X1 broker-clock offset, coverage windows, post-arming census |
| `L10X_SPREAD_BPS_V1.json` | X4 captured-quote spread in bps, frozen-vs-real overlap |
| `L10X_TICK_SPREAD_V1.json` | X4 **300,538,915-tick** full-population spread, 61 series, by broker-hour |
| `L10X_SPREAD_3WAY_V1.json` | X4.3 captured quotes vs tick archive, 23 symbols |
| `L10X_LIVE_BORNSTATE_V1.json` | X3 live born-state census, 296 captures |
| `L10X_LIVE_COST_PRICEUNITS_V1.json` | commission/slippage/spread in price units, 32 broker symbols |
| `L10X_POOL_RECOST_V1.json` | X5/X6 pool re-cost + gate counterfactual, per symbol |
| `L10X_BOTTOMLINE_V1.json` | X7 the five books, per symbol and per family |
| `L10X_STOP_GEOMETRY_V1.json` | X8 live vs pool stop distances |
| `L10X_HOURS_MINSTOP_V1.json` | X8.1 minimum viable stop, X9 hour availability |
| `L10X_FILLPROB_REPLACEMENT_V1.json` | X10 empirical fill probability, corrected clock |
| `L10_*_V1.json` (14 files) | first-pass artifacts backing F1–F14, preserved |

Scripts under `l10_scripts/`: `l10x_01_clock.py`, `l10x_02_spread_bps.py`, `l10x_03_tickspread.py`,
`l10x_04_bornstate.py`, `l10x_05_stopgeom.py`, `l10x_06_recost.py`, `l10x_07_bottomline.py`,
`l10x_08_fillprob.py`, `l10x_09_hours_and_minstop.py`, plus the first pass's `l10_01`–`l10_15`.

**Scope compliance restated:** no live-forward P&L appears anywhere above. `profit` was never read
from any deal record. `commission`, `swap`, `price`, `volume`, `time` and order state are execution
mechanics and are the only deal fields used.
