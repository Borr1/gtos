# LANE 5 — the space this program has never entered, priced

**Owner-commissioned swarm 2, lane 5. 2026-08-11.** Analysis only. No live path, no config, no VPS, no
broker, no git write. Receipts: `lane5_receipts/` (10 JSON artifacts + the 8 scripts that wrote them).

Commission: *"where are we not looking"* — enumerate the space GTOS has never entered, establish for each
whether the data is already on this machine, and rank by (prior odds of edge) × (prize) ÷ (cost to test).

---

## 0. THE ANSWER, IN SIX SENTENCES

1. **The commission's premise is two-thirds right, and the third that is wrong matters.** Cross-sectional
   and pairs trading HAVE been built here — twice — and killed; carry HAS been tested and closed; limit
   execution HAS been studied. What is genuinely untouched is **volatility as a position** (architecturally
   impossible: `admission.py:845` types direction as `int`), **event/calendar conditioning on the armed
   book** (zero references in `src/components/ultimate_book/`), **sub-hour horizons**, and
   **signal ensembling** (the wave-21 ridge is argmax-selection, not combination).

2. **But the three closed doors were closed on defective evidence, and all three reopen at a measured
   price.** Carry was closed by a verdict note stating *"pure-rollover swap return is ~1e-8/night"* — its
   own result table's largest value is **8.571e-05, four orders of magnitude larger** — and it was run on
   an `is_fx()`-restricted universe (`wave7_carry_overnight.py:357-358, :385`) that structurally excluded
   the two symbols carrying by far the largest positive carry in the broker's own book. Cross-sectional was
   killed on a 13→45-symbol universe as a universe-growth artifact; **166 symbols with D1+H4 back to 2014
   sit on this machine unused**. LIMIT was studied as an entry variant, never as the population it is.

3. **The single largest unexploited number in the estate is that it discards 87.0 % of its own candidate
   population by construction.** 550,966 of 632,934 cached candidates are LIMIT
   (`LANE5_CANDIDATE_CACHE_STATS_V1.json`), the deployed rule abstains on LIMIT
   (`shadow_select.py:69-71`), and the LIMIT population is **31.9 % cheaper** (cost_r 0.2249 vs 0.3303) and
   **+0.0819 R/fill better on realized outcome** (−0.1907 vs −0.2725, difference t = **+12.8**,
   n = 72,496 / 74,249).

4. **The second largest is that the cost engine floors favourable carry to exactly zero, and the credit it
   throws away is up to 27.1 % of total cost.** `broker_net_cost_engine.py:465-468` and
   `costs/model.py:1034` clamp positive swap to 0; the cache confirms it — **0 negative values in 632,934
   rows**. Priced in the estate's own R unit: `USOIL_cash` LONG is **+0.0647 R/night**, `UKOIL_cash` LONG
   **+0.0414 R/night**, against a mean total `cost_r` of 0.2386. `energy_agri`, one of the four **armed**
   sleeves, trades those instruments.

5. **The third is hour-of-day, and it is 17.6×.** Median `spread_r` for MARKET candidates runs 0.0514 at
   UTC h14 to 0.9039 at UTC h21 (= broker h00, the rollover). Independently corroborated on the tick
   archive at **41× for EURUSD** (0.091 → 3.745 bps) and **11.6× for GBPJPY** (0.969 → 11.257 bps) —
   measurements the estate's bar `spread` column is structurally blind to, because it is the within-bar
   *minimum*. Spread is **50.3 %** of total cost.

6. **I refuted my own best-looking positive.** A quote-imbalance signal on the never-used tick archive gave
   IC = −0.105, **t = −20.1** on US500_cash. Under a one-minute anchor gap it collapses to −0.0076
   (t = −1.44) and at two minutes to +0.0035 (t = +0.67). It is bid-ask bounce, entirely. **Naive quote-OFI
   from this archive is not a signal and the swarm should not spend a week finding that out.**

---

## 1. THE DATA THAT IS ALREADY HERE — full inventory

| asset | location | size / coverage | ever used for signal? |
|---|---|---|---|
| **D1 + H4 bars, 166 symbols** | `/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_h4d1_2014_2026/` | 332 files; 4,257 dates **2014-01-01 → 2026-06-17**; median 1,679 D1 rows/symbol, max 3,534 | **Only single-instrument.** Never as a cross-section wider than 45. |
| **M15 bars, 167 symbols** | `.../deep_universe_m15_2014_2026/` | 167 files | single-instrument only |
| **D1, 166 symbols (2nd cut)** | `.../cycle4_universe_d1/` | 166 files | — |
| **M1 bars, 25 symbols/month** | `.../bridge_ftmo_m1_2024xx … 202606/` + `bridge_ftmo_ext_m1_*` | 30 monthly dirs × 25 + 13 × 23 | fill simulation only |
| **Tick quotes** | `/Users/borr/GTOSActive/vps-ticks-20260726/` | **263,894,769 rows**, 122 files, FTMO 72 + FN 50, **2026-06-18 → 07-26** | **cost/spread only — 23 consumer files, zero signal** |
| **Candidate cache** | `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` | **632,934 rows**, 56 fields, 5 months of 2026 | funnel selection only |
| **Broker swap tables** | `config/profiles/operator_profile.yaml` (42 symbols), `config/profiles/redacted_account.yaml` (32) | one snapshot each | cost only |
| **Realized per-position swap** | `/Users/borr/GTOSActive/vps-export-20260725/extracted/.../trade_records/*.json` | n=300, 74 nonzero, validated to the cent | cost only |
| **Economic calendar** | `data/economic_calendar.csv` | **14 lines, starts 2026-06-01 — effectively empty** | never |

### 1.1 The cross-section by year — this is the asset nobody has spent

| year | median symbols with a D1 bar that day | max |
|---|---:|---:|
| 2014 | 39 | 39 |
| 2017 | 50 | 58 |
| 2020 | 77 | 116 |
| 2021 | **134** | 140 |
| 2023 | **150** | 152 |
| 2025 | **162** | 163 |
| 2026 | **166** | 166 |

Composition: 59 equity CFDs (AAPL, NVDA, TSLA, MSFT, META, AMZN, GOOG, ASML, MSTR, PLTR…), 43 FX
(including EM: USDMXN, USDZAR, USDCZK, EURHUF, EURPLN, USDILS), 30 crypto, 17 index, 17 commodity.
The live surface is **24 symbols**. The archive is **166**. `LANE5_D1_ARCHIVE_INVENTORY_V1.json`.

### 1.2 The one hazard in that archive, stated up front

**Every one of the 166 symbols has a last bar in 2026-06. Zero symbols end early. This is a 100 %
survivor-selected universe** — it is FTMO's *current* symbol list, not a point-in-time list. For alt-coins
and single-stock CFDs the delisting bias is real and it hits the **short leg hardest** (the losers that
would have been dropped are absent). Long/short partially nets it; it does not remove it. Any absolute
long-only claim from this archive is inadmissible. This is disclosed in every cell below.

### 1.3 What the tick archive does NOT contain — be honest before designing on it

`time,bid,ask,last,volume,time_msc,flags,volume_real`. Checked across FX, metals, crypto, indices and
energy: **`last` is 0.0, `volume` is 0 and `volume_real` is 0.0 on every symbol.** These are **pure quote
ticks**. There is no trade print, no signed trade, no volume, no depth. Anything requiring true order-flow
imbalance, trade-size clustering, or DOM is **not buildable from this archive** and no capture on this
machine can supply it. What IS buildable: quote intensity, quote-revision counts, time-weighted effective
spread, spread dynamics, quote-life, and mid-path realised variance. `flags` is constant 1158 on the rows
sampled (bid+ask update bits plus two undocumented high bits) and carries no trade-side information.

---

## 2. THE EIGHT AREAS, EACH PRICED

### 2.1 Cross-sectional / relative value — **PARTIALLY ENTERED, ABANDONED AT 1/4 SCALE**

**(i) Data: yes, and 3.7× wider than anything previously tested.** See §1.1.

**What already happened, so the swarm does not rediscover it.** `wave7_pairs_statarb.py` is a complete
pairs stat-arb (OLS hedge ratio, z-scored spread, per-leg cost, random + invert nulls) — every pair
`"status": "DEAD"`. `wave1_cross_sectional.py:126-195` is a real XS rank engine (long top-k / short
bottom-k, dollar-neutral) — killed by `wave3_leak_audit.py:194-240` as a **universe-growth artifact, on a
universe that grew 13 → 45 symbols**. `XSEC_harness.py`, `CYCLE48_xsec_gauntlet.py`,
`cycle5_xsec_equity_rv.py`, `idxdeep_xsec.py`, `xs_class_neutral_pairs_scan.py` all exist in the external
research root. **Live reachability is nil**: `session_leadlag.py:16-23` states it outright — *"There is no
cross-symbol channel in the generation path at all"* — and `walkforward/supply.py:503-505` marks
`session_leadlag_genuine` `LIVE_WIRING_GAP / needs_cross_symbol_feed=True`.
`cross_asset_lead_lag` is **not** a spread: `broader_origin_generators.py:1902-1907` sets side from the
leader and puts entry and stop **entirely on the lag symbol**.

**(ii) Cheapest decisive experiment — already run, as a pilot.** I built the 166-symbol panel and ran a
5-cell × 6-subgroup grid with a correct within-date permutation null (2,000 draws), risk-parity
vol-normalised legs, quintile long/short, own-observation-sequence returns (the naive global-grid
construction silently collapses the universe to the 30 crypto symbols — weekends). **Total compute: 9
minutes on this laptop.** `LANE5_XS_PILOT_GRID_V1.json`, `LANE5_XS_CONTROLS_AND_COST_V1.json`.

| cell | n rebal | univ | mean (σ-units) | t | perm p | turnover | gross bps/rebal | **break-even cost, bps/leg** | pos yrs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XS_MOM_12_1 \| EQUITY | 81 | 55 | +0.784 | **+2.34** | 0.0020 | 0.24 | +137.8 / 21 d | **291.8** | 5/6 |
| XS_MOM_12_1 \| ALL | 188 | 67 | +0.139 | +0.48 | 0.330 | 0.26 | +10.0 | 19.4 | 9/12 |
| XS_MOM_1M \| NOCRYPTO | 196 | 65 | **−0.461** | −1.64 | 0.0090 | 0.71 | −34.3 | −24.0 | 3/13 |
| **XS_REV_1D \| FX-ONLY** | **3,112** | 40 | **−0.0416** | **−1.98** | **0.0010** | 0.80 | −2.04 / 1 d | **−1.27** | 4/13 |
| XS_REV_1D \| ALL | 3,626 | 57 | −0.0327 | −2.21 | 0.0005 | 0.82 | −3.1 | −1.9 | 4/13 |
| XS_REV_5D \| ALL | 728 | 57 | +0.0995 | +1.34 | 0.048 | 0.79 | +11.3 / 5 d | +7.2 | 8/13 |

Sign convention: the portfolio is long the high-trailing-return quintile. A **negative** mean is therefore
**cross-sectional reversal**.

**(iii) Adversarial checks — one headline dies, one survives.**

- **The equity 12-1 headline is a half-sample artifact and I am killing it.** Split at 2024-01-01:
  2021-09→2023-12 t = **+1.78** (n=40, 3/3 positive years); **2024-01→2026-05 t = −0.07, mean −0.027,
  1/3 positive years.** The entire effect is in the first half of a 4.7-year equity sample. Do not build on
  it. (It is also the cell most exposed to §1.2's survivor bias.)
- **The 1-day cross-sectional reversal survives every control I applied.** Same sign in both halves
  (pre-2020 t = −1.74, 2020+ t = −1.37), in FX-only (t = −1.98), crypto-only (t = −1.73) and
  equity-only (t = −1.06). **FX-only is the important cell**, because all FX D1 bars close at the same
  broker instant — which removes the non-synchronous-close artifact that is the standard killer of
  short-horizon cross-sectional work. It is the strongest cell and the cleanest one.
- **Reported magnitude even though small:** −2.04 bps per day on a vol-scaled dollar-neutral FX book,
  break-even **1.27 bps per leg per rebalance**. Measured FTMO EURUSD median hourly spread is **0.091 bps**
  and FX commission ≈ 0.35 bps/leg — so the headroom is roughly **3×**, not 30×, and the strategy
  rebalances daily. It is marginal, not comfortable.
- **The residual threat I could not eliminate:** within FX, ranking overlapping pairs (EURUSD, EURGBP,
  EURJPY) mechanically produces a currency-basket position, so part of the "cross-sectional" content is a
  restatement of single-currency reversal. The fix is a currency-factor decomposition, not more data.

**(iv) Prize.** A structurally market-neutral, near-zero-beta return stream at daily frequency that shares
no mechanism with any sleeve in the book — the only such thing available on this machine — plus the
diversification multiplier in §2.8 (2.65× measured). **(v) What would make it fail:** the 3× cost headroom
being consumed by slippage on 40 simultaneous small CFD legs; the currency-overlap restatement; prop-firm
`max_concurrent` limits (`risk.max_concurrent` in both profiles) making a 16-leg book unrunnable.

---

### 2.2 Microstructure from the unused tick archive — **ENTERED BY ME, AND CLOSED**

**(i) Data: yes** — 263.9 M rows, but quote-only (§1.3), and only **38 days** (2026-06-18 → 07-26). The
`MARKET_DATA_DEPTH_PROBE.json` establishes FTMO serves ticks back to **2023-09** for 19 symbols and
2023-01 for US100 — i.e. deeper history is a *capture*, not a read.

**(ii)–(iii) I ran the decisive experiment and it is negative.** Quote-revision imbalance
`OFI = ((bid↑ + ask↓) − (bid↓ + ask↑)) / total`, per minute, against forward mid returns, 4 symbols,
36 k–53 k minutes each. `LANE5_TICK_MICROSTRUCTURE_V1.json`, `LANE5_OFI_BOUNCE_CONTROL_V1.json`.

| symbol | naive IC (fwd 1 m, last-mid, gap 0) | t | **gap 1 min, time-weighted mid** | t | gap 2 min | t |
|---|---:|---:|---:|---:|---:|---:|
| **US500_cash** | **−0.1047** | **−20.06** | **−0.0076** | **−1.44** | +0.0035 | +0.67 |
| BTCUSD | +0.0050 | +1.14 | +0.0062 | +1.41 | +0.0007 | +0.17 |
| XAUUSD | −0.0052 | −0.99 | +0.0001 | +0.02 | +0.0051 | +0.98 |
| EURUSD | +0.0007 | +0.14 | +0.0046 | +0.89 | −0.0021 | −0.41 |

**Verdict: the t = −20 is bid-ask bounce and nothing else.** 93 % of the IC evaporates when the forward
window starts one minute after the signal window ends, and the last-mid anchor even flips sign
(+0.023, t = +4.32) — the signature of a stale-extreme anchor, not of information. **This closes the naive
quote-OFI lane.** What it does not close: quote *intensity* (ticks/minute) as a **regime/vol-state
conditioner** rather than a directional signal, and time-weighted spread as a cost instrument (§2.7),
both of which are real and both of which are cheap.

**(iv) Prize if a non-bounce construction worked:** sub-hour is a genuinely uncorrelated pool. **(v) What
makes it fail — and it did:** no trade prints means every "flow" proxy is a quote proxy, and quote proxies
are contaminated by the bounce at exactly the horizon where the signal would live. Add: 38 days is
~5.4 weeks of sample for a strategy that would trade every minute; and the archive stops 2026-07-26 while
the live books are armed today.

---

### 2.3 Carry / swap as ALPHA — **CLOSED ON A FOUR-ORDERS-OF-MAGNITUDE ERROR. REOPEN IT.**

**(i) Data: yes, three independent sources** — the two live profile swap tables (42 + 32 symbols), the
632,934-row cache's `swap_cost_r`, and 300 broker deal records with realized per-position swap.

**The structural fact first.** `swap_long + swap_short < 0` on **42 of 42** FTMO symbols and **32 of 32**
redacted_account symbols — zero exceptions (`LANE5_BROKER_SWAP_CROSS_SECTION_V1.json`). The broker has taken the
entire carry plus a markup on every instrument. **A market-neutral carry harvest is arithmetically
impossible here.** That is a real and permanent constraint and it should be stated whenever carry is
discussed.

**But one side is positive on 15 symbol/sides, and the estate records that credit as exactly zero.**
`broker_net_cost_engine.py:465-468` (`elif swap >= 0: adverse_swap_points = 0.0`) and
`costs/model.py:1034` (*"favourable or zero swap → no cost"*). The cache proves it empirically: of 632,934
`swap_cost_r` values, **0 are negative**, 507,299 are exactly 0.0, 125,635 are positive. And the twelve
symbol/sides whose mean `swap_cost_r` is exactly 0.00000 in the cache are **precisely** the positive-swap
sides in the profile table — an exact cross-validation between config and data.

**(ii) The decisive number, in the estate's own unit.** Foregone carry per night, divided by each symbol's
median `risk_fraction_of_entry` from the cache, against a mean total `cost_r` of 0.23855
(`LANE5_LIMIT_VS_MARKET_AND_CARRY_V1.json`):

| symbol / side | swap pts | carry/night | annualised | **R/night** | **% of mean cost_r** |
|---|---:|---:|---:|---:|---:|
| **USOIL_cash LONG** | +36.56 | 4.811e-04 | **17.56 %** | **+0.0647** | **27.1 %** |
| **UKOIL_cash LONG** | +27.64 | 3.613e-04 | **13.19 %** | **+0.0414** | **17.3 %** |
| USDJPY LONG | +1.93 | 1.245e-05 | 0.45 % | +0.0277 | 11.6 % |
| AUDJPY LONG | +2.00 | 2.062e-05 | 0.75 % | +0.0260 | 10.9 % |
| GBPJPY LONG | +2.80 | 1.346e-05 | 0.49 % | +0.0203 | 8.5 % |
| USDCHF LONG | +1.15 | 1.437e-05 | 0.52 % | +0.0191 | 8.0 % |
| UK100 SHORT | +10.80 | 1.125e-05 | 0.41 % | +0.0163 | 6.8 % |
| US30_cash LONG | +37.00 | 8.409e-06 | 0.31 % | +0.0151 | 6.3 % |
| *(7 more, +0.0014 … +0.0092 R/night)* | | | | | |

At the armed sleeves' median hold of ~3 days, **`USOIL_cash` LONG accrues ≈ +0.19 R of financing that the
cost engine books as 0.00.** `energy_agri` — one of the four armed sleeves — trades that instrument.

**Why the door was closed, and why the closure does not hold.** `wave7_carry_overnight_RESULT.json`'s
verdict reads *"Pure-rollover swap return is ~1e-8/night, negligible vs ~5e-4/day price drift, so no symbol
is a genuine carry edge."* **Its own `carry` table's largest `swap_only_mean_daily` is 8.571e-05
(GBPJPY)** — 8,571× the quoted figure. And `wave7_carry_overnight.py:357-358` defines
`is_fx(sym) = ASSET_CLASS_BY_SYMBOL.get(sym) in ("fx","jpy_fx")`, applied as a hard skip at `:385-386`, so
of its own 21-symbol declared `universe_long_history` **only 12 were carry-tested — all FX**.

**The exclusion was deliberate, and its stated reason is the reason to revisit it.** The comment at
`:355-356` reads: *"FX/jpy_fx subset for the classic carry trade (swap differential is meaningful;
**avoid index/crypto/energy where swap_mode=5 flat -30 or huge financing dominates**)."* The judgement is
defensible for `swap_mode=5` crypto (a flat −30 both sides, which is a fee, not a carry). It is not
defensible for energy: `UKOIL_cash` and `USOIL_cash` are `swap_mode=1` **points**, their long carry is
**5.6× the largest FX carry the study did test**, and "financing dominates" is a description of the
hypothesis, not a reason to drop the symbol from the test of it.

**(iii) Prior on edge: LOW for carry-as-standalone-alpha, HIGH for carry-as-accounting-repair.** The
literature's commodity-carry factor is real, but a CFD's positive swap is the futures roll being passed
through and the price series should give it back. **I tested that and could not find the give-back, with a
disqualifying caveat:** `USOIL_cash` price drift over the archive is **+8.10 %/yr** *alongside* +17.6 %/yr
carry, total +25.7 %/yr at 38.8 % vol. But the series starts **2020-12-31**, at the COVID-crash recovery —
a start-date artifact large enough to explain the whole thing. `LANE5_OIL_CARRY_VS_DRIFT_V1.json`.

**(iv) Prize.** Two tiers. Tier 1 (near-certain): a cost model that is *correct* rather than conservative,
worth up to 27 % of the cost term on instruments already armed, and a side-preference input the sizing
layer has never had. Tier 2 (speculative): a genuine positive-carry tilt on the two oil CFDs.
**(v) What makes it fail:** the swap snapshot is a **single point in time** applied to years of history —
oil backwardation flips to contango and the sign goes with it. **This is the binding blocker and it is a
capture, not an analysis:** there is no swap time series anywhere on this machine. One read-only
`symbol_info(sym).swap_long/swap_short` per symbol per day, appended to a JSONL, costs nothing, touches no
order path, and starts a clock that cannot be started retroactively. **Start it this week regardless of
what else is prioritised.**

---

### 2.4 Event and calendar conditioning — **THE ARMED BOOK IS COMPLETELY BLIND, AND THE DATA IS ABSENT**

**(i) Data: NO.** `data/economic_calendar.csv` is **14 lines** beginning 2026-06-01;
`data/news_calendar.json` carries `"week_of": "2026-05-31"`. Both ~10 weeks stale.
`scripts/refresh_economic_calendar.py:1-9` states it *"does NOT fetch data automatically… a monitor +
alerter, not an auto-refresher"*, and `phase3/WAVE3_INTEGRATION.md:253` records it as ungranted and inert.
**Even the staleness alarm is not firing.**

**Two live lineages, and the armed one has no news code at all.** Lineage A (`run_agent.py` →
`orchestrator.py`) has three real gates — `:1757-1785`, `:7269-7300`, `:8190-8214` — over
`src/utils/economic_calendar.py` and `src/components/news_calendar.py`, both `enabled: true`
(`agent_config.yaml:3921-3969`). Lineage B (`run_book.py` → `src/components/ultimate_book/`, **the four
armed sleeves on two funded accounts**) returns **zero hits** for news/economic_calendar/blackout.
`broker_truth_layer_2026_07_27/FIRM_RULES_V1.json:5` already logs this under `absent`.

**Calendar seasonality: month-end, quarter-end, turn-of-month, OPEX, triple witching, index rebalance are
ABSENT everywhere** — proposed in `KB_architecture_spec.md:50` and `research_execution_plan_113q.md:86`,
never built. Day-of-week exists only as a post-hoc reporting dimension (`trade_models.py:127`,
`adaptive_review.py:154`); the one DOW *signal* study exists to falsify itself
(`wave3_leak_audit.py:527-591`). Rollover exists as **swap-night counting** (`costs/model.py:986-1023`),
not as a seasonality signal. Weekend exists as a live **filter** (`run_book.py:233-239`).

**(ii) Cheapest decisive experiment: the free half first.** Month-end / turn-of-month / day-of-week /
quarter-end need **no new data** — they are derivable from the 4,257-date D1 panel and from the 632,934-row
cache's existing `weekday` and `trading_day` fields. That is hours of compute for the whole grid. The
macro-event half (NFP/CPI/FOMC) needs a calendar that **does not exist on this machine** and must be
acquired before anything can be measured.

**(iii) Prior.** Turn-of-month in equity indices and month-end FX rebalancing flows are among the
better-documented calendar effects; the prior is genuinely moderate, and unusually, **the search cost is
near zero and the multiplicity bill is tiny** (a handful of pre-declarable cells, not a grid of thousands).
Macro-event conditioning: high prior that it changes *variance* and *cost*, low prior that it produces
directional edge at this frequency. **(iv) Prize:** a conditioning axis orthogonal to every geometry
feature the funnel measured, plus — separately and independently — closing the operational gap that the
armed book holds positions through scheduled high-impact releases with no awareness of them.
**(v) What makes it fail:** turn-of-month is a *few* observations per year (13 × 12 = 156 month-ends in the
whole panel); the effect must be large to clear any honest bar at that n.

---

### 2.5 Horizon diversity — **THE LONG END IS COVERED; THE SHORT END IS EMPTY**

**Long end: entered.** `execution_packets.py:70` sets `RESEARCH_HORIZON_NATIVE_BARS = 80`, applied as
`time_stop_m15(80, "D1")` = 7,680 M15 bars ≈ **16 weeks**. Measured realized holds
(`phase6/receipts/REPAIR_QUEUE_V1.json`): `vol_compression` median 240 h / max 2,303 h (96 days);
`mx_ger40_cash_d1_volume_surge_reversal` max **5,736 h (239 days)**. All four armed sleeves hold multi-day
with a p99 tail of 2.5–4 weeks. The declared horizon grid `[1,2,3,5,10,20,40,80]` own-bars is in
`AU_D1_HORIZONS_V1.json:9-23`. **Nothing is unexplored here; do not re-buy it.**

**Short end: empty, and it is the one place the tick archive is uniquely qualified.** No strategy or
measurement in the estate runs below M15. §2.2 shows the naive construction fails; the surviving question
is whether a **spread-aware, bounce-controlled** sub-hour signal exists. Given §2.2's result my prior is
**low** and I rank it accordingly.

**The genuinely untested horizon is neither: it is multi-week on the 166-symbol cross-section** (§2.1),
where holding 21 days at 0.24 turnover makes cost almost irrelevant (break-even 291.8 bps/leg) — the exact
opposite of the funnel's regime, where cost is 100 % of the loss.

---

### 2.6 Volatility as a tradeable object — **NEVER ENTERED, AND ARCHITECTURALLY BLOCKED**

**(i) Data: yes** (any vol construction is a function of bars already held). **Code: no, and the block is
structural.** `admission.py:845` types `direction: int  # +1 long / -1 short`;
`ultimate_book/primitives.py:35` calls its fill model *"Explicit two-sided fill. direction +1 long / −1
short"*. **There is no representation for a non-directional position anywhere in the runtime.** Every
apparent hit is vol-as-state: `vol_squeeze.py:1-16` takes the expansion *"ONLY in the HTF-trend
direction"*; `vol_compression.py:47-52` picks one side from the break; the one file literally titled
"RANGE-EXPANSION BREAKOUT BOTH-WAYS" (`wave6_new_mechanic_longshot.py:240-244`) means *the rule may fire
either way*, not that both sides are held. Zero hits for straddle-as-position, variance, or vega.

**(ii) Cheapest decisive experiment.** A synthetic straddle is expressible **without** any architecture
change: two opposing stop-entry orders bracketing a compressed range, both live, the loser cancelled on
the first touch. That is buildable inside the existing directional type system as two independent intents,
and it is measurable on M15 bars for the whole 2014–2026 archive. Cost: ~1 session to build, hours to
measure. The genuine architecture change (a variance position) is weeks and should not be bought until the
synthetic version measures positive. **(iii) Prior: moderate** — vol clustering is the single most robust
stylised fact in the literature, and the estate has never once monetised it as anything but a sizing input.
**(iv) Prize:** an axis with near-zero correlation to every directional sleeve by construction, and the
only one on this list whose payoff is not a function of getting direction right. **(v) What makes it fail:**
double spread (two legs), and the prop-firm drawdown rules penalising the whipsaw path where both legs
trigger.

---

### 2.7 Execution alpha — **THE BIGGEST MEASURED NUMBER IN THIS LANE**

**(i) Data: yes, three ways.**

**Fact 1 — the estate discards 87.0 % of its own candidates.** 550,966 LIMIT vs 81,968 MARKET in the
632,934-row cache; `shadow_select.py:69-71` abstains when the top candidate is LIMIT.

**Fact 2 — the discarded population is cheaper and better.**

| | MARKET | LIMIT | Δ |
|---|---:|---:|---:|
| n candidates | 81,968 | **550,966** | 6.7× |
| `cost_r` | 0.33025 | **0.22491** | **−31.9 %** |
| `spread_r` | 0.18398 | **0.11045** | −40.0 % |
| `commission_r` | 0.08765 | 0.05709 | −34.9 % |
| resolved `terminal_net_r` | **−0.27254** (n=74,249) | **−0.19067** (n=72,496) | **+0.0819 R/fill, t = +12.8** |

**The honest caveat, stated before anyone builds on it:** only 72,496 of 550,966 LIMIT candidates resolve
(13.2 %). The +0.0819 R is **conditional on fill**, and limit fills are adversely selected. The correct
object is `P(fill) × E[net | fill]`, and **the estate already owns the fill-probability model** —
`geometry_bound_outcome_model.py:1-33`, a Jeffreys Beta(½,½) fraction over resolved LIMIT attempts with a
100-attempt support gate. Nobody has ever composed the two. That composition is the experiment.

**Fact 3 — the hour is a 17.6× lever on the largest cost term.** Median `spread_r` for MARKET candidates by
UTC hour: **h14 = 0.0514 (best) → h21 = 0.9039 (worst), ratio 17.60×**; h20 = 0.1185, h22 = 0.1594.
UTC h21 is broker h00 — the rollover. Independently, from ticks (time-weighted, in bps of mid):

| symbol | median hour | best hour | worst hour | ratio |
|---|---:|---:|---:|---:|
| **EURUSD** | 0.091 | h18 **0.066** | **h00 3.745** | **56.8×** |
| **GBPJPY** | 0.969 | h18 0.890 | **h00 11.257** | **12.7×** |
| USOIL_cash | 9.777 | h07 8.828 | h16 10.982 | 1.24× |
| XAUUSD | 1.113 | h13 1.065 | h01 1.324 | 1.24× |
| BTCUSD | 0.184 | h10 0.172 | h00 0.196 | 1.14× |
| US500_cash | 0.774 | h07 0.770 | h23 0.825 | 1.07× |

`spread_r` is **50.3 %** of mean `cost_r` (0.11997 of 0.23855). The estate's bar `spread` column is the
within-bar **minimum** and is therefore structurally blind to the h00 spike; **the tick archive is a
strictly better instrument for this and has never been used for it.** This corroborates the estate's own
AH finding (100 % of FX D1 fills at broker hour 00) with an independent measurement, and prices it larger.

**Queue position: genuinely absent.** `QUEUE_POSITION` appears once, in
`gtos_vnext_runtime.py:640`'s `DEFAULT_ORDERFLOW_DIAGNOSTIC_TOKENS` — a list of *unavailable* things. No
maker/taker model exists and none is buildable from quote-only ticks.

**(iii) Prior: very high — this is measurement, not discovery.** **(iv) Prize:** the estate's central
finding is `E[net] = −E[cost]`; the cache confirms it (`terminal_net_r` −0.23209 vs `cost_r` +0.23855,
agreeing to 2.7 %). **When the entire loss is the cost term, a 31.9 % cost reduction on 87 % of the
population plus a 17.6× hour lever on 50.3 % of that cost is not an optimisation — it is the only
arithmetic in the estate that can move a negative to a zero.** **(v) What makes it fail:** the fill-rate
composition (13.2 %) being adversely selected enough to eat the whole +0.0819; broker `trade_stops_level` /
`trade_freeze_level` constraints on resting orders; and prop-firm `max_concurrent`.

---

### 2.8 Ensemble / portfolio construction — **NEVER ATTEMPTED, AND THE RAW MATERIAL IS ALREADY GOOD**

**(i) Data: yes, measured here.** The wave-21 ridge is **selection, not ensemble**:
`wave21_forward_shadow/daily_refit.py:104-121` fits one `Ridge(alpha=10.0)` over
`feature_contract.py:43-92`'s 14 categoricals + 29 numerics — **all attributes of a single candidate**,
with `origin_family` as a one-hot *feature* — and `shadow_select.py:65` takes `max(available, key=…)`,
one trade per decision window. The only genuine stacked composite in the tree,
`learned_edge_trainer.py` over `f_heuristic_probability` / `f_thesis_probability`, is gated on
`selector_v4_learned_edge_enabled`, **a key that appears in no config file** — default off, unreachable.

**(ii) I measured the thing that decides whether an ensemble is worth building.** Daily mean
`terminal_net_r` per origin family, 100 trading days, 10 families
(`LANE5_ENSEMBLE_CORRELATION_V1.json`):

- 45 off-diagonal correlations: **mean +0.0395, median +0.0159**, range −0.307 … +0.539,
  **64.4 % have |r| < 0.2**.
- **Diversification ratio = 2.649** against a theoretical maximum of √10 = 3.162 — the ten families are
  **83.8 % of the way to fully independent**.

**(iii) The honest reading, and it governs the sequencing.** Every family's daily mean is **negative**
(−0.055 to −0.561 R, t = −2.14 to −25.66). Combining ten negatives yields a negative with 2.65× less
variance. **Ensembling cannot create edge; it is a 2.65× multiplier on whatever the mean is.** So it is
worth building **only after** something moves a family's mean above zero — which is exactly what §2.7's
cost repairs are for. That is why it is ranked last in the queue and not dropped: it is the amplifier, and
it is already measured, so it costs almost nothing to apply once there is something to amplify.

**(iv) Prize:** the classical IC≈0.02 → usable-IR route, with the correlation structure already confirmed
favourable. **(v) What makes it fail:** the correlations are measured on 100 days of one cache; the two
largest (+0.539 `displacement_continuation`↔`cross_asset_lead_lag`, +0.485 ↔`session_open_range_break`)
show the clusters are real and a naive equal weight over-weights them.

---

## 3. THE RANKED, COSTED EXPERIMENT QUEUE

Ranked by (prior odds) × (prize) ÷ (cost). "Time to yes/no" is wall-clock for one competent agent on this
laptop, excluding pre-registration.

| # | experiment | data ready? | compute | **time to yes/no** | prior | prize if it works |
|---|---|---|---|---|---|---|
| **E1** | **LIMIT population: compose `P(fill)` × `E[net\|fill]` and re-decide the abstain rule** | **yes** — 550,966 rows + the Jeffreys model already built | minutes | **1 day** | **very high** (measurement) | +0.0819 R/fill on 87 % of the population; the only lever sized to close `E[net]=−E[cost]` |
| **E2** | **Hour-of-day as a GENERATION parameter, not a post-hoc stratum** | **yes** — cache + 263.9 M ticks | hours | **1–2 days** | **very high** | spread is 50.3 % of cost, hour is a 17.6× (cache) / 56.8× (tick) lever on it |
| **E3** | **Un-floor favourable swap + start the daily swap-table capture** | **yes** for the repair; **capture must start now** for persistence | minutes | **repair 1 day; persistence 90 days** | high (accounting) / low-med (alpha) | up to +0.0647 R/night = 27.1 % of total cost, on an **armed** instrument |
| **E4** | **Cross-sectional daily reversal, FX-only, 43 symbols, leak-free, cost-charged** | **yes** — 166-symbol panel built, pilot run | ~10 min/config | **2–3 days** | medium | a market-neutral daily stream sharing no mechanism with any sleeve; 3× cost headroom |
| **E5** | **Calendar seasonality grid (turn-of-month, month-end, DOW, quarter-end) on the 4,257-date panel** | **yes**, needs no new data | hours | **1–2 days** | medium | an orthogonal conditioning axis at a near-zero multiplicity bill |
| **E6** | **Cross-sectional 12-1 momentum, 166 symbols, survivorship-disclosed** | **yes** | ~10 min/config | **2 days** | **low** — I already killed the headline on the 2024+ half | a multi-week pool where cost is irrelevant (BE 291.8 bps/leg) |
| **E7** | **Synthetic straddle (paired opposing stop-entries) on compressed ranges, M15, 2014–2026** | **yes** | hours | **3–4 days** | medium | the only non-directional axis available; zero correlation by construction |
| **E8** | **Ensemble over the 10 families — build the machinery, hold it until E1–E3 land** | **yes**, correlations measured | hours | **1 day (after E1–E3)** | n/a — it is a multiplier | **2.649× variance reduction, already measured**, applied to whatever mean the repairs produce |
| **E9** | **Acquire a real macro-event calendar; wire the armed book to it** | **NO — data absent** | n/a | **acquisition first** | low for alpha / **high for operations** | the armed book currently holds through scheduled releases blind |
| — | ~~Naive quote-OFI microstructure~~ | — | — | **already answered: NO** | — | **do not run it** — killed here at t = −20 → t = −1.44 under a 1-minute anchor gap |

### Why the top three rank where they do

**E1 first** because it is the only item on this list where the magnitude is already measured on the
estate's own population, at t = +12.8, and where the missing work is *composition of two components that
both already exist* rather than a search. It is also the item most directly aimed at the finding that
governs everything (`E[net] = −E[cost]`): it removes 31.9 % of the cost on 87 % of the candidates.

**E2 second** because the lever is the largest single multiplier found anywhere in this lane (17.6× on the
cost term that is half of all cost), because it needs no new data, and because the estate's existing
instrument for it — the bar `spread` column, a within-bar minimum — is provably the wrong one while the
better one (263.9 M ticks) sits unused. It is also nearly free to act on: the hour is a generation
parameter, not a model.

**E3 third** — and it is third only because half of it is an accounting repair with a certain answer and
the other half needs a clock started. **The capture half should be started immediately regardless of
prioritisation**, because a swap time series cannot be reconstructed retroactively and every week of delay
is a week of a persistence test that can never be run.

### Two standing warnings for whoever runs this queue

1. **Every cross-sectional result from `deep_universe_h4d1_2014_2026` carries 100 % survivor selection**
   (§1.2). Disclose it in the pre-registration, not the post-mortem.
2. **The permutation p-values and the t-statistics in §2.1 answer different questions and diverge.** The
   within-date permutation null holds the date set fixed and tests only whether the *ranking* carries
   information; the t-statistic additionally prices the time-variation of the effect and is the
   conservative one. Report both. Pre-register the t-statistic as the bar.

---

## 4. WHAT THIS LANE CHANGES ABOUT THE PROGRAM'S SELF-DESCRIPTION

- *"This system has only ever searched single-instrument directional technical geometry"* — **true of what
  is live and reachable, false of what was researched.** Cross-sectional, pairs, carry and limit-entry were
  all built and killed in `final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`. The finding is not that
  they were never tried; it is that **all four were tried at a fraction of the available scale and closed
  on defective or restricted evidence**, and none was ever wired to a live path — `session_leadlag.py:16-23`
  says the quiet part outright: *"There is no cross-symbol channel in the generation path at all."*
- **The estate's cost work has been rigorously conservative in a way that is now measurably wrong in one
  direction.** Flooring favourable swap to zero, abstaining on the cheaper 87 % of candidates, and pricing
  spread off a within-bar minimum are three independent conservatisms; each was individually defensible and
  together they mean the published economics understate the achievable book on the cost side by a margin
  that is the same order as the entire measured loss.
- **The one thing that is unambiguously, structurally never-entered is the non-directional position.** It
  is blocked by a type annotation (`admission.py:845`), and the synthetic version (E7) is the cheap way to
  find out whether the block is worth removing.

---

## 5. RECEIPTS

`lane5_receipts/` — `LANE5_XS_PILOT_GRID_V1.json` (30 cells, 2,000-draw nulls),
`LANE5_XS_CONTROLS_AND_COST_V1.json` (13 controls + break-even bps),
`LANE5_TICK_MICROSTRUCTURE_V1.json` (6 symbols, 30.8 M ticks read, spread by broker hour),
`LANE5_OFI_BOUNCE_CONTROL_V1.json` (the refutation, 5 anchors × 2 horizons × 4 symbols),
`LANE5_CANDIDATE_CACHE_STATS_V1.json`, `LANE5_LIMIT_VS_MARKET_AND_CARRY_V1.json`,
`LANE5_ENSEMBLE_CORRELATION_V1.json`, `LANE5_BROKER_SWAP_CROSS_SECTION_V1.json`,
`LANE5_OIL_CARRY_VS_DRIFT_V1.json`, `LANE5_D1_ARCHIVE_INVENTORY_V1.json`, plus the 8 scripts
(`panel.py`, `inv_d1.py`, `xs4.py`, `xs5.py`, `ticks.py`, `ofi_ctrl.py`, `cache.py`, `final.py`).

**Scope.** Everything above is exploratory and unregistered. No cell here is admission-grade, none has paid
a multiplicity bill, and the D1 archive has been read by prior `mx_*` sleeve work so it is not virgin data.
Nothing in this lane touched the four armed sleeves, any config, any decision-contract-bound file, or the
never-read 2025 validation windows.
