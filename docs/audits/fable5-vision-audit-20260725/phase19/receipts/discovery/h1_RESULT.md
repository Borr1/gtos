# h1 — THE COST SURFACE, IN MONEY, AT FULL RESOLUTION

Lane key `h1`. Population: the **43,755 live-expressible at-market candidates** the swarm
established (January + February + March 2026), scored under its repaired contract
(`K5_TRAIL025`: market entry delayed 5 minutes, 0.25 R trail). Nothing sampled; every table
is the whole population. Reproduce with `h1_01_cost_rows.py` → `h1_08_stress.py`.

---

## 0. THE HEADLINE

> **The toll is 35 % bigger than the swarm priced it, and the reason is that cost is not a
> constant of the instrument — it is a function of the HOUR. Broker-true, hour-aware, all-in
> cost is 0.245214 R/trade (2.9744 bps) against the swarm's 0.181834 R (2.457 bps), so
> edge:toll falls from 0.211 to 0.1564. But the same hour-resolution that raises the average
> is what finds the cells: 651 cells clear edge:toll > 1, 152 of them at n ≥ 100. The
> deepest survivor of every stress this estate can defend is `NAS100` at a broker-true cost
> ≤ 0.50 bps — n = 526, net +0.04621 R/trade, edge:toll 2.469, positive in all three months,
> and still 1.077 with the spread doubled, the January era charged, and l10-F9's full exit
> slippage applied.**

Second headline, because it changes how every cost number in this estate should be read:

> **The 12.1× family cost dispersion the swarm pointed at is 12.35× in R and 3.08× in money
> — and Spearman(cost_bps, cost_R) across families is −0.5714. The two views do not merely
> rank differently; on the family and class axes they rank in OPPOSITE order.
> `structural_distance_extreme` is the most expensive family in R (0.5470) and the fifth
> CHEAPEST of ten in money (2.564 bps). Its stops are 0.066 % of price. What was read as a
> broker-cost axis is a stop-geometry axis.**

---

## 1. THE COST BASIS — four terms, each with a provenance class

`h1_01_cost_rows.py` → `h1_COST_ROWS_V1.jsonl.gz` (43,755 rows, 0 dropped) +
`h1_COST_ROWS_V1_BUILD.json`.

| term | source | class | coverage over the 43,755 |
|---|---|---|---|
| **spread** | `L10X_TICK_SPREAD_V1.json` `spread_bps_median_by_broker_hour`, FTMO, 300,538,915 ticks, full population, **keyed on the candidate's own broker wall hour** | MEASURED | 43,610 by-hour; 145 fall back to the flat median on a thin hour (< 500 ticks) |
| **commission** | the repo's shipped `BROKER_TRUE_COSTS_V1.json` (FTMO), round turn, `notional_bp` or `per_lot`, converted through `usd_per_price_unit_per_lot` | MEASURED 31,481 / TRANSFERRED 12,274 | 24/24 symbols priced |
| **slippage (entry)** | `L10X_LIVE_COST_PRICEUNITS_V1.json` measured price-unit slippage, clamped ≥ 0 | MEASURED 22,393 / MODELLED class median 21,362 | 12 of 24 symbols measured |
| **swap** | instrument spec `swap_long`/`swap_short`/`swap_mode`/`point`, adverse side only, charged **per broker-midnight crossing inside the 2 h horizon**, triple on the Wednesday rollover | MEASURED spec | 1,665 rows charged (3.81 %) |

Convention: **one full bid/ask crossing per round turn**
(`BROKER_TRUE_COSTS_V1.conventions.spread`, `broker_net_cost_engine.py:294`). §8 prices the
two-crossing alternative.

**The broker clock is not UTC and the offset is not constant.** FTMO-Server3 =
`America/New_York + 7 h`, so January and February 2026 are **UTC + 2 h** and March (from
2026-03-08) is **UTC + 3 h** (`src/utils/broker_clock.py`, verified inline). Keying the
hourly spread on UTC would mis-bucket the rollover by two to three hours and would not even
be consistent across the three months.

### 1.1 Three corrections to the basis the swarm used

**H1-F9 — `e_lib._CRYPTO_BPS` charges BTCUSD commission 1.47× too low.** It stores
`39.2778 / 88599.74 * 1e4 = 4.4332 bps`, i.e. it normalises a **price-unit** commission
measured in the June–July live window (BTC ≈ 60 k) by a **January** price (88.6 k). The
broker-true schedule is `6.51631 bp of notional, round turn, MEASURED, 9 round turns`
(`BROKER_TRUE_COSTS_V1`). Ratio **6.51631 / 4.4332 = 1.470**. The same shape applies to
ETHUSD, which `e_lib` charges as a flat `1.09905` price units against a broker-true
`6.47324 bp of notional`. Commission is 90.6 % of BTCUSD's whole toll and 51.6 % of ETHUSD's,
so this is not a rounding correction on those two symbols.

**H1-F10 — the flat per-symbol spread median understates the pooled toll by 19.78 %.**
Hour-aware 0.233067 R vs flat 0.194573 R, **+0.038494 R/trade**. The flat median is a
tick-mass-weighted number and the pool's candidates are not distributed like the tick mass:
GER40 quotes 0.457–0.501 bps through London/NY (132 k–245 k ticks/hour) and 1.35–1.51 bps
overnight (34 k–58 k ticks/hour), so its 0.5012 flat median describes its cheap hours and
prices its expensive ones at a 3.0× discount.

**H1-F11 — swap was charged zero on this pool and 3.81 % of it crosses a rollover.**
1,665 of 43,755 rows have a broker midnight inside their own 2 h horizon — **all of them at
broker hours 22 (811) and 23 (854)** — and pay a mean **0.3192 R / 3.1626 bps** when charged.
That is **4.95 % of the entire book's toll**, from a term every prior pass set to 0 by
appeal to the 2 h horizon. The horizon argument is right about elapsed time and wrong about
the charging rule: swap is charged per crossing (`BROKER_TRUE_COSTS_V1.conventions.swap`,
corroborated by l10-F6 — swap present at a 2.2 h hold, absent at a 24.3 h hold).

---

## 2. THE POOL, AND WHAT THE CORRECTIONS COST

| basis | mean cost R/trade | mean cost bps | gross R | net R | edge:toll R |
|---|---:|---:|---:|---:|---:|
| frozen research model | 0.468424 | — | +0.038342 | −0.430082 | 0.082 |
| swarm `cost_true` (flat symbol median) | 0.181834 | 2.457 | +0.038342 | −0.143492 | 0.211 |
| **h1: flat median, broker-true commission + slippage** | 0.194573 | — | +0.038342 | −0.156231 | 0.197 |
| **h1: + hour-aware spread** | 0.233067 | 2.8541 | +0.038342 | −0.194725 | 0.165 |
| **h1: + swap at rollover crossings — THE BASIS** | **0.245214** | **2.9744** | **+0.038342** | **−0.206871** | **0.1564** |
| h1 basis, era-adjusted to Jan/Feb/Mar | 0.243840 | 2.7883 | +0.038342 | −0.205498 | 0.157 |

Gross reproduces the swarm exactly (`+0.038342` on 43,755, and 19 of 24 symbols
gross-positive in price space) — the entire difference is the cost side.

### 2.1 Term decomposition, pool-wide

| term | bps | share | R | share | dominant on |
|---|---:|---:|---:|---:|---:|
| spread | 2.0225 | 68.0 % | 0.15369 | 62.7 % | 30,647 rows (70.0 %) |
| commission | 0.6942 | 23.3 % | 0.06363 | 25.9 % | 11,952 rows (27.3 %) |
| slippage (entry) | 0.1373 | 4.6 % | 0.01574 | 6.4 % | 0 |
| swap | 0.1203 | 4.0 % | 0.01215 | 5.0 % | 1,156 rows (2.6 %) |

**Which term dominates where** (`H1_DECOMP_V1.json` → `TERM_DOMINANCE`):

- **spread-dominated, 92–98 %**: `USOIL_cash` 98.3 %, `XAGUSD` 97.5 %, `UK100` 94.4 %,
  `JP225` 94.4 %, `UKOIL_cash` 92.6 %, `GER40` 92.0 %. Zero-commission CFDs — nothing but
  the quote matters.
- **commission-dominated**: `BTCUSD` 90.6 % (6.5163 of 7.1886 bps), `EURUSD` 56.1 %,
  `ETHUSD` 51.6 %, `USDJPY` 50.4 %, `AUDUSD` 47.8 %, `USDCAD` 43.2 %. On the tightest-spread
  FX the $5/lot round turn is the whole cost, and on crypto the notional-bp schedule is.
- **swap-dominated**: only inside broker hours 22–23, where it is 2.6 % of rows overall but
  the largest single term on those rows.

---

## 3. FULL DISPERSION — every axis, both units

`H1_SURFACE_V1.json` → `AXES`, `AXIS_DISPERSION`, `AXIS_ETA2`.
η² is the share of variance in log(cost) the axis explains — a range is dominated by its
thinnest cell, η² is not.

| axis | k | **bps range** | **R range** | η²(bps) | η²(R) |
|---|---:|---|---|---:|---:|
| **symbol** | 24 | **24.26×** — US30_cash 0.5172 → ETHUSD 12.5488 | 8.08× — NAS100 0.0605 → EURGBP 0.4888 | **0.8578** | 0.3009 |
| instrument_class | 5 | 6.69× — fx 1.4687 → crypto 9.8215 | 2.24× — metals 0.1425 → fx 0.3197 | 0.2931 | 0.1295 |
| origin_family | 10 | 3.08× — ob_retest 1.0741 → vol_compression 3.3076 | **12.35×** — regime_transition_break 0.0443 → structural_distance_extreme 0.5470 | 0.0053 | 0.3006 |
| **broker_hour** | 24 | 3.66× — bh10 2.3779 → **bh00 8.7113** | **12.69×** — bh17 0.1204 → **bh00 1.5281** | 0.0692 | 0.1413 |
| utc_hour | 24 | 2.96× — uh07 2.3895 → uh22 7.0673 | 9.40× — uh15 0.1247 → uh22 1.1723 | 0.0556 | 0.1273 |
| kill_zone | 27 | 6.06× — tokyo 1.5146 → moonshot_h14_15 9.1826 | 9.65× — h07_08 0.1132 → h22_23 1.0933 | 0.0958 | 0.1296 |
| **rdp_decile** (stop width) | 10 | 5.55× — d1 1.4196 → d9 7.8727 | 11.76× — d9 0.0683 → d0 0.8033 | 0.2510 | **0.4415** |
| broker_dow | 6 | 3.36× (Sat n=32) — Mon 2.8408 → Wed 3.1002 among weekdays | 1.35× | 0.0026 | 0.0020 |
| side | 2 | 1.01× | 1.14× | 0.0000 | 0.0033 |
| month | 3 | 1.03× | 1.44× | 0.0001 | 0.0215 |
| **symbol × broker_hour** | 574 | — | — | **0.9852** | — |
| symbol × kill_zone | 469 | — | — | 0.9522 | — |
| symbol × session | 74 | — | — | 0.8855 | — |
| symbol × family | 172 | — | — | 0.8640 | — |
| class × broker_hour | 120 | — | — | 0.3979 | — |
| family × broker_hour | 175 | — | — | 0.0833 | — |

**Which axis carries the most, stated in both units, because the answer differs:**

- **In money (bps) — the INSTRUMENT, decisively.** η² 0.8578 on its own; adding the hour
  takes it to **0.9852**, i.e. `symbol × broker_hour` explains 98.5 % of the cross-sectional
  variance in what a trade costs. **Family explains 0.5 %.** Instrument selection is the
  cost lever; family selection is not a cost lever at all.
- **In R (what the gate reads) — STOP GEOMETRY.** `rdp_decile` η² 0.4415 beats symbol
  (0.3009) and family (0.3006). The R view is the money view divided by stop width, and
  stop width has more variance than the broker does.
- **Day of week is a non-axis** (η² 0.0026 / 0.0020). Wednesday is the most expensive
  weekday (3.1002 bps vs Monday's 2.8408) — the triple-swap rollover — but it is a 9 %
  effect. The 9.5320 bps Saturday cell is 32 rows and should not be quoted.

### 3.1 The instrument table (24 symbols, sorted by money cost)

| symbol | n | cost bps | cost R | gross R | net R | edge:toll R | edge:toll bps | rdp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| US30_cash | 1,942 | 0.5172 | 0.0654 | +0.03254 | −0.03288 | 0.497 | 0.724 | 0.00194 |
| NAS100 | 1,904 | 0.7010 | 0.0605 | +0.02370 | −0.03680 | 0.392 | 0.370 | 0.00252 |
| EURUSD | 1,863 | 0.7624 | 0.1962 | +0.05860 | −0.13757 | 0.299 | 0.109 | 0.00084 |
| **GER40** | 1,858 | **0.8599** | 0.0871 | +0.06465 | −0.02246 | 0.742 | **1.059** | 0.00254 |
| GBPUSD | 2,054 | 1.0100 | 0.2420 | +0.03439 | −0.20756 | 0.142 | −0.036 | 0.00092 |
| SPX500 | 1,850 | 1.0253 | 0.1254 | +0.02489 | −0.10055 | 0.198 | 0.418 | 0.00188 |
| USDJPY | 2,442 | 1.0367 | 0.2632 | +0.06433 | −0.19891 | 0.244 | 0.306 | 0.00090 |
| USDCAD | 2,010 | 1.1816 | 0.3949 | +0.02049 | −0.37441 | 0.052 | −0.100 | 0.00065 |
| EURJPY | 1,564 | 1.3760 | 0.2670 | +0.02783 | −0.23922 | 0.104 | 0.064 | 0.00095 |
| XAUUSD | 1,996 | 1.4115 | 0.0787 | +0.04661 | −0.03213 | 0.592 | 0.642 | 0.00414 |
| AUDUSD | 1,627 | 1.5046 | 0.2024 | +0.02944 | −0.17295 | 0.145 | −0.092 | 0.00153 |
| EURGBP | 1,865 | 1.6299 | 0.4888 | +0.03766 | −0.45116 | 0.077 | 0.016 | 0.00056 |
| USDCHF | 1,854 | 1.6377 | 0.3095 | +0.04427 | −0.26523 | 0.143 | 0.076 | 0.00100 |
| JP225 | 1,627 | 1.6644 | 0.0895 | +0.03476 | −0.05476 | 0.388 | 0.779 | 0.00389 |
| GBPJPY | 1,978 | 1.7260 | 0.3419 | +0.04567 | −0.29622 | 0.134 | 0.085 | 0.00093 |
| UK100 | 2,002 | 1.9653 | 0.2845 | +0.06153 | −0.22302 | 0.216 | 0.370 | 0.00176 |
| AUDJPY | 1,604 | 2.2075 | 0.2907 | +0.03606 | −0.25462 | 0.124 | 0.046 | 0.00150 |
| CHFJPY | 1,547 | 2.3950 | 0.3579 | +0.04283 | −0.31503 | 0.120 | 0.102 | 0.00107 |
| NZDUSD | 1,943 | 2.5819 | 0.3883 | +0.03710 | −0.35124 | 0.096 | 0.008 | 0.00128 |
| BTCUSD | 1,415 | 7.1886 | 0.1917 | +0.04220 | −0.14947 | 0.220 | −0.035 | 0.00670 |
| UKOIL_cash | 1,699 | 9.3027 | 0.3577 | +0.01524 | −0.34250 | 0.043 | 0.057 | 0.00703 |
| XAGUSD | 1,968 | 9.7122 | 0.2072 | +0.03596 | −0.17125 | 0.174 | 0.058 | 0.01040 |
| USOIL_cash | 1,777 | 10.0539 | 0.3472 | +0.03525 | −0.31198 | 0.102 | 0.035 | 0.00740 |
| ETHUSD | 1,366 | 12.5488 | 0.2451 | +0.00225 | −0.24281 | 0.009 | −0.169 | 0.00891 |

### 3.2 The family table — and the trap in it

| family | n | cost bps | cost R | gross R | net R | edge:toll R | rdp |
|---|---:|---:|---:|---:|---:|---:|---:|
| current_ob_retest | 3 | 1.0741 | 0.1374 | +0.70701 | +0.56963 | 5.146 | 0.00078 |
| current_breaker_re_entry | 3 | 1.2781 | 0.1875 | −0.22913 | −0.41661 | −1.222 | 0.00088 |
| session_open_range_break | 2,943 | 2.2218 | 0.0804 | +0.01641 | −0.06397 | 0.204 | 0.00385 |
| current_fvg_fill | 15 | 2.3871 | 0.3097 | −0.10881 | −0.41847 | −0.351 | 0.00182 |
| **structural_distance_extreme** | 5,696 | **2.5640** | **0.5470** | +0.14149 | −0.40547 | 0.259 | 0.00066 |
| liquidity_sweep_reclaim | 13,372 | 2.8769 | 0.2428 | +0.02914 | −0.21365 | 0.120 | 0.00199 |
| cross_asset_lead_lag | 6,075 | 3.2292 | 0.3708 | +0.05260 | −0.31820 | 0.142 | 0.00153 |
| displacement_continuation | 13,022 | 3.2422 | 0.1309 | +0.00864 | −0.12228 | 0.066 | 0.00396 |
| **regime_transition_break** | 828 | **3.2661** | **0.0443** | +0.04919 | **+0.00489** | **1.110** | 0.00979 |
| volatility_compression_expansion | 1,798 | 3.3076 | 0.0728 | −0.02160 | −0.09439 | −0.297 | 0.00762 |

The three POI-limit families (`current_ob_retest`, `current_breaker_re_entry`,
`current_fvg_fill`) have 3, 3 and 15 rows here because they are almost entirely the limit
cohort the live engine cannot place. **Do not quote them.**

**Read the last two columns against the second.** `regime_transition_break` is the **most
expensive family in money of the seven that have depth** (3.2661 bps) and the **cheapest in R
by a factor of 12.35** (0.0443), because its stops are 0.98 % of price — 15× wider than
`structural_distance_extreme`'s 0.066 %. It is the only deep family that is net-positive, and
the reason is not that it is cheap: it is that it commits enough risk per trade for a flat
edge to clear a flat toll. Symmetrically, `structural_distance_extreme` is the R-view's most
expensive family and the money-view's fifth cheapest.

---

## 4. bps AND R RANK DIFFERENTLY — and on two axes they INVERT

`H1_DECOMP_V1.json` → `BPS_VS_R` (cells with n ≥ 25).

| axis | Spearman(cost_bps, cost_R) | dispersion bps | dispersion R | max rank move |
|---|---:|---:|---:|---:|
| symbol | **+0.5017** | 24.26× | 8.08× | **15 of 24 places** |
| broker_hour | +0.5174 | 3.66× | 12.69× | 14 of 24 |
| kill_zone | **+0.1593** | 6.06× | 9.65× | **24 of 27** |
| **origin_family** | **−0.5714** | 1.49× | 12.35× | 5 of 7 |
| **instrument_class** | **−0.7000** | 6.69× | 2.24× | 4 of 5 |

**The kill-zone axis is essentially uncorrelated between the two units (ρ = 0.159) and one
cell moves 24 of 27 places.** The family and class axes are *negatively* correlated. Any
statement of the form "cell X is the cheap one" is unsafe unless the unit is named.

**Where this has already cost the estate a decision.** l10-X6 measured that the frozen gate
admitted SPX500 0 of 1,943 times and NAS100 0 of 1,622 times on a *spread charge* 18× and 34×
the broker's. The unit compounds the error: the gate is R-denominated, and the index complex
carries the pool's tightest R-denominated costs *only after* you divide by its stop, so the
gate was reading a quantity in which index CFDs look expensive (frozen `spread_r` medians
1.808 and 1.642) while in money they are the **cheapest instruments in the universe**
(US30_cash 0.5172 bps, NAS100 0.7010, GER40 0.8599 — against ETHUSD's 12.5488). §6 shows
that is exactly where every affordable cell lives.

---

## 5. THE EXPENSIVE STRUCTURE NOBODY HAD PRICED: THE ROLLOVER

`H1_DECOMP_V1.json` → `ROLLOVER_HOUR`.

**Broker hour 00 — n = 926 (2.12 % of the book) — costs 1.5281 R / 8.7113 bps per trade and
carries 13.19 % of the entire book's toll.** Its spread is 7.7362 bps against a 1.1097 bps
flat-median basis for the same rows: **a 7.0× charge the per-symbol median completely
hides.**

It is an **FX phenomenon**, per symbol, hour-00 tick median vs that symbol's flat median:

| symbol | n | bh00 spread bps | flat bps | ratio | cost R |
|---|---:|---:|---:|---:|---:|
| EURUSD | 17 | 3.0549 | 0.0881 | **34.7×** | 1.4769 |
| GBPUSD | 53 | 7.6736 | 0.2265 | **33.9×** | 2.8727 |
| USDJPY | 59 | 3.5892 | 0.1862 | 19.3× | 1.5935 |
| USDCAD | 42 | 5.6885 | 0.3508 | 16.2× | 3.7165 |
| CHFJPY | 109 | 14.7911 | 0.9441 | 15.7× | 1.6353 |
| NZDUSD | 63 | 16.2181 | 1.0351 | 15.7× | 2.5205 |
| AUDUSD | 30 | 6.2373 | 0.4365 | 14.3× | 1.0982 |
| EURGBP | 97 | 8.3176 | 0.5888 | 14.1× | 2.1900 |
| GBPJPY | 73 | 11.0917 | 0.8913 | 12.5× | 2.2657 |
| USDCHF | 82 | 5.9566 | 0.6166 | 9.7× | 1.0671 |
| AUDJPY | 52 | 9.7724 | 1.0593 | 9.2× | 1.3265 |
| EURJPY | 56 | 4.9545 | 0.6531 | 7.6× | 0.7081 |

**A data flag found on the way** (not priced, filed): **ten of the twenty-four symbols carry
ZERO ticks at broker hour 00** — every index CFD (`GER40, NAS100, SPX500, US30_cash, UK100,
JP225`), both metals (`XAUUSD, XAGUSD`) and both oils (`USOIL_cash, UKOIL_cash`). GER40's
hourly histogram runs h01…h23. The instruments are in their daily break. The pool
nevertheless emits **145 candidates on them at that hour, 76 of those on the index complex**
— decisions in a closed market. They are priced here at the flat median, which is the honest
fallback and is not a measurement of that hour; the FX rollover table above is unaffected
because FX quotes through it.

**Swap lands one hour earlier and is a separate cost**: 1,665 rows, **all** at broker hours
22 (811) and 23 (854), 0.3192 R / 3.1626 bps when charged, 4.95 % of the pool toll.

**Consequence for any hour rule.** Dropping broker hour 00 alone moves the book's toll
0.24521 → 0.21750 R (−11.3 %) for 2.1 % of its trades. Dropping 00, 22 and 23 moves it to
0.20097 R (−18.0 %) for 7.7 % of trades, and edge:toll 0.156 → 0.178. Restricting to broker
hours 08–20 gives 0.17880 R and edge:toll **0.232** on 65.6 % of the book. None of these is
positive; all of them are strictly better than the incumbent.

---

## 6. CHEAP **AND** DEEP — ranked

`H1_HUNT_V1.json` → `CHEAPEST_CELLS_n_ge_300`. Money cost first, because that is the
quantity a broker charges.

| rank | cell | n | cost bps | cost R | gross R | net R | edge:toll R |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | US30_cash \| broker hours 16–19 | 524 | 0.3981 | 0.0280 | +0.02842 | +0.00046 | 1.016 |
| 2 | US30_cash \| ny | 465 | 0.4032 | 0.0295 | +0.02810 | −0.00135 | 0.954 |
| 3 | **US30_cash \| london** | 406 | 0.4132 | 0.0582 | +0.09250 | **+0.03427** | **1.589** |
| 4 | US30_cash \| broker hours 08–11 | 554 | 0.4247 | 0.0628 | +0.05687 | −0.00597 | 0.905 |
| 5 | **GER40 \| london** | 504 | 0.4817 | 0.0330 | +0.09088 | **+0.05794** | **2.758** |
| 6 | cheapest cost-decile of the whole book | 4,376 | 0.4863 | 0.0504 | +0.04436 | −0.00604 | 0.880 |
| 7 | **NAS100 \| broker hours 16–19** | 547 | 0.4972 | 0.0272 | +0.04891 | **+0.02175** | **1.800** |
| 8 | **GER40 \| broker hours 16–19** | 390 | 0.5115 | 0.0365 | +0.05898 | **+0.02246** | **1.615** |
| 9 | US30_cash (all) | 1,942 | 0.5172 | 0.0654 | +0.03254 | −0.03288 | 0.497 |
| 10 | **NAS100 \| ny** | 612 | 0.5202 | 0.0309 | +0.04398 | **+0.01311** | **1.425** |
| 11 | **GER40 \| ny** | 429 | 0.5516 | 0.0427 | +0.06120 | **+0.01853** | **1.434** |

**Every cell in the cheap-and-deep top eleven is GER40, NAS100 or US30_cash.** The affordable
universe is the index complex, and the affordable *hours* inside it are London and the
London/NY overlap.

---

## 7. THE HUNT — cells where the edge already pays its own toll

`H1_HUNT_V1.json`. 28 cell definitions, one-way through three-way, every combination the
whole population. **No multiplicity correction is applied**; a later stage tests whether
these travel.

**651 cells clear `edge:toll > 1` (R or bps) or `net > 0`.** By depth:
n ≥ 10 → 495 · n ≥ 25 → 413 · n ≥ 50 → 295 · **n ≥ 100 → 152** · n ≥ 200 → 82 · n ≥ 400 → 34.

### 7.1 The decision-shaped result: an EX-ANTE money gate

Every input is knowable at the decision instant (tick-anchored spread at that broker hour,
the commission schedule, the swap schedule, the measured slippage), so `cost_bps ≤ X` is a
rule the live engine could evaluate before sending. `H1_FRONTIER_V1.json`.

| gate | n | frac | cost bps | gross R | **net R** | e:t R | e:t bps | t_net | days+ | Jan / Feb / Mar net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cost_bps ≤ 0.40 | 757 | 1.7 % | 0.3981 | +0.02587 | −0.00861 | 0.750 | 1.180 | −0.39 | 31/63 | −0.0282 / +0.0252 / −0.0218 |
| cost_bps ≤ 0.45 | 1,334 | 3.0 % | 0.4057 | +0.03998 | −0.00420 | 0.905 | 1.089 | −0.26 | 33/63 | −0.0255 / +0.0127 / +0.0018 |
| **cost_bps ≤ 0.50** | **3,191** | **7.3 %** | 0.4506 | +0.05462 | **+0.00956** | **1.212** | **1.956** | +0.90 | 37/63 | −0.0147 / +0.0142 / +0.0304 |
| cost_bps ≤ 0.55 | 3,570 | 8.2 % | 0.4563 | +0.04875 | +0.00323 | 1.071 | 1.729 | +0.32 | 33/63 | −0.0225 / +0.0085 / +0.0249 |
| cost_bps ≤ 0.60 | 3,728 | 8.5 % | 0.4616 | +0.04942 | +0.00275 | 1.059 | 1.736 | +0.28 | 35/63 | −0.0217 / +0.0056 / +0.0257 |
| cost_bps ≤ 0.65 | 4,408 | 10.1 % | 0.4874 | +0.04424 | −0.00628 | 0.876 | 1.311 | −0.69 | 31/63 | |
| cost_bps ≤ 0.70 | 6,948 | 15.9 % | 0.5593 | +0.04205 | −0.03841 | 0.523 | 0.673 | −5.02 | 16/63 | |
| cost_bps ≤ 1.00 | 13,945 | 31.9 % | 0.7007 | +0.04091 | −0.07503 | 0.353 | 0.543 | −13.97 | 7/63 | |
| **no gate** | 43,755 | 100 % | 2.9744 | +0.03834 | −0.20687 | 0.156 | 0.078 | −56.75 | 0/63 | |

**The frontier is a cliff at ~0.6 bps, not a slope.** Between 0.60 and 0.70 bps the book
goes from net +0.00275 to −0.03841 and from 35 positive days to 16.

**Composed with the hour rule** (`cost_bps ≤ 0.50` **and** broker hour 08–20): n = 2,759,
cost 0.4486 bps / 0.03977 R, gross +0.05678, **net +0.01701 R/trade, edge:toll 1.428 R /
2.045 bps, t +1.49, and positive in ALL THREE MONTHS** (+0.0028 Jan, +0.0221 Feb, +0.0262 Mar).

**Train / test.** The threshold is chosen on the data, so: fit on Jan+Feb, read March.
At 0.50 — train n = 2,144 net −0.00062 (e:t 0.988), **test n = 1,047 net +0.03039 (e:t 2.099,
t +1.69, 16 of 22 days positive)**. At 0.60 — train −0.00842, test +0.02568. At 0.70 both
sides are negative. So the gate is not a March artifact, but it is **breakeven in-sample and
positive out-of-sample**, which is the honest way to state it.

### 7.2 The gate is denominated in the wrong unit — measured

| gate | n | admitted | cost R | edge:toll R |
|---|---:|---:|---:|---:|
| shipped limbs at broker-true cost: `spread_r ≤ 0.10 ∧ total_r ≤ 0.15` | 22,072 | 50.4 % | 0.0661 | **0.188** |
| shipped `spread_r ≤ 0.10` alone | 27,359 | 62.5 % | 0.1019 | 0.183 |
| R gate `total_r ≤ 0.02` (the tightest that reaches parity) | 2,622 | 6.0 % | 0.0131 | **0.999** |
| **money gate `cost_bps ≤ 0.50 ∧ bh 08–20`** | **2,759** | **6.3 %** | 0.0398 | **1.428** |

**At matched depth (≈ 2,700 admitted) the money gate delivers 1.428 against the R gate's
0.999 — 43 % more edge per unit of toll.** And the R gate as actually shipped, even fed
broker-true costs, admits half the book and buys 0.188.

### 7.3 Every cell with n ≥ 300 that clears, ranked by edge:toll

| cell | n | cost bps | cost R | gross R | net R | e:t R | e:t bps | t_net | days+ | months+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GER40 \| london | 504 | 0.4817 | 0.0330 | +0.09088 | +0.05794 | 2.758 | 5.482 | +2.25 | 39/63 | **3/3** |
| XAUUSD \| rdp decile 9 | 330 | 1.4140 | 0.0137 | +0.03308 | +0.01935 | 2.410 | 1.785 | +0.67 | 32/55 | 2/3 |
| NAS100 \| broker hours 16–19 | 547 | 0.4972 | 0.0272 | +0.04891 | +0.02175 | 1.800 | 2.445 | +0.85 | 35/63 | **3/3** |
| GER40 \| broker hours 08–11 | 599 | 0.7072 | 0.0636 | +0.11344 | +0.04981 | 1.783 | 3.080 | +1.82 | 34/63 | **3/3** |
| JP225 \| rdp decile 8 | 378 | 1.6821 | 0.0345 | +0.06144 | +0.02697 | 1.783 | 1.955 | +0.97 | 36/63 | 2/3 |
| GER40 \| broker hours 16–19 | 390 | 0.5115 | 0.0365 | +0.05898 | +0.02246 | 1.615 | 0.721 | +0.66 | 32/63 | 2/3 |
| NAS100 \| rdp decile 7 | 306 | 0.6851 | 0.0237 | +0.03794 | +0.01425 | 1.602 | 1.716 | +0.47 | 33/63 | 2/3 |
| US30_cash \| london | 406 | 0.4132 | 0.0582 | +0.09250 | +0.03427 | 1.589 | 1.732 | +1.19 | 36/63 | **3/3** |
| GER40 \| ny | 429 | 0.5516 | 0.0427 | +0.06120 | +0.01853 | 1.434 | 0.864 | +0.58 | 32/63 | 2/3 |
| NAS100 \| ny | 612 | 0.5202 | 0.0309 | +0.04398 | +0.01311 | 1.425 | 2.011 | +0.55 | 35/63 | 2/3 |
| regime_transition_break \| rdp decile 9 | 340 | 5.9225 | 0.0340 | +0.04596 | +0.01196 | 1.352 | 1.060 | +0.62 | 35/62 | 2/3 |
| XAUUSD \| ny | 519 | 1.3046 | 0.0520 | +0.06838 | +0.01642 | 1.316 | 0.459 | +0.60 | 34/63 | 2/3 |
| regime_transition_break \| off_configured_session | 366 | 4.4664 | 0.0531 | +0.06097 | +0.00789 | 1.149 | 0.967 | +0.37 | 32/63 | 2/3 |
| US30_cash \| displacement_continuation | 563 | 0.4658 | 0.0285 | +0.03195 | +0.00347 | 1.122 | 0.798 | +0.15 | 36/63 | 1/3 |
| **regime_transition_break (family)** | 828 | 3.2661 | 0.0443 | +0.04919 | +0.00489 | 1.110 | 1.105 | +0.34 | 32/63 | 2/3 |
| UK100 \| london | 637 | 0.9487 | 0.1010 | +0.11009 | +0.00910 | 1.090 | 1.438 | +0.35 | 31/63 | 2/3 |
| metals \| broker hour 15 | 318 | 5.0595 | 0.1047 | +0.11257 | +0.00791 | 1.076 | 1.276 | +0.24 | 33/61 | 2/3 |
| XAUUSD \| broker hours 16–19 | 397 | 1.3012 | 0.0514 | +0.05395 | +0.00251 | 1.049 | −0.051 | +0.08 | 34/62 | 2/3 |
| US30_cash \| broker hours 16–19 | 524 | 0.3981 | 0.0280 | +0.02842 | +0.00046 | 1.016 | 0.905 | +0.02 | 31/62 | 2/3 |

Thinner cells with the highest ratios, for completeness (n ≥ 100): `GER40|bh16` n=108 e:t
**6.982** net +0.21705 · `GER40|session_open_range_break` n=114 e:t 6.567 · `NAS100|rdp9`
n=117 e:t 5.729 · `NAS100|displacement_continuation|bh16-19` n=175 e:t 4.590 · `NAS100|bh18`
n=105 e:t 4.417 · `GER40|bh10` n=206 e:t 3.731 · `US30_cash|rdp7` n=235 e:t 3.433 ·
`NAS100|bh17` n=223 e:t 3.372 · `volatility_compression_expansion|bh10` n=138 e:t 3.251 ·
`index|regime_transition_break` n=292 e:t 2.802. Full list in
`H1_HUNT_V1.json → ALL_HITS` (651 rows).

### 7.4 The exact hour map of the index complex

`H1_STRESS_V1.json → HOUR_MAP` (broker hour; UTC hours given because they differ by month).

| cell | n | spread bps | cost bps | gross R | net R | e:t R | UTC hours |
|---|---:|---:|---:|---:|---:|---:|---|
| GER40 \| bh16 | 108 | 0.4898 | 0.4898 | +0.25334 | +0.21705 | **6.982** | 13–14 |
| GER40 \| bh20 | 35 | 0.5754 | 0.5754 | +0.22162 | +0.17398 | 4.652 | 17–18 |
| NAS100 \| bh18 | 105 | 0.4955 | 0.4955 | +0.13343 | +0.10322 | 4.417 | 15–16 |
| US30_cash \| bh21 | 42 | 0.3981 | 0.3981 | +0.18233 | +0.14005 | 4.312 | 18–19 |
| GER40 \| bh10 | 206 | 0.4955 | 0.4954 | +0.11274 | +0.08253 | 3.731 | 7–8 |
| NAS100 \| bh17 | 223 | 0.4955 | 0.4955 | +0.07187 | +0.05056 | 3.372 | 14–15 |
| US30_cash \| bh10 | 175 | 0.4169 | 0.4169 | +0.11317 | +0.06257 | 2.237 | 7–8 |
| XAUUSD \| bh15 | 167 | 1.1220 | 1.3113 | +0.11898 | +0.06539 | 2.220 | 12–13 |
| UK100 \| bh11 | 151 | 0.7161 | 0.7161 | +0.14811 | +0.08042 | 2.188 | 8–9 |
| GER40 \| bh08 | 118 | 1.3804 | 1.3804 | +0.22000 | +0.06007 | 1.376 | 5–6 |

`GER40|bh08` is the instructive one: its **gross is the largest in the table (+0.220)** and
its edge:toll is 1.376 because it is priced at 1.3804 bps — the pre-open. The same signal
one hour later at 0.4955 bps returns 3.731. **The hour is not selecting the signal; it is
selecting the price of expressing it.**

---

## 8. HOW MUCH COST MOVES WITH ENTRY TIMING

### 8.1 The delay is a gross lever, NOT a cost lever

Re-pricing the spread at the broker hour of `decision + k minutes` (`ENTRY_DELAY_JOINT`):

| k (min) | cost R | cost bps | gross R | net R | edge:toll R |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.24521 | 2.9744 | −0.02247 | −0.26768 | −0.092 |
| 1 | 0.24521 | 2.9744 | +0.03000 | −0.21521 | 0.122 |
| **5** | **0.24521** | **2.9744** | **+0.03834** | **−0.20687** | **0.156** |
| 15 | 0.24508 | 2.9647 | +0.03785 | −0.20722 | 0.154 |
| 30 | 0.24124 | 2.9325 | +0.04451 | −0.19673 | **0.185** |
| 60 | 0.24097 | 2.8732 | +0.03593 | −0.20504 | 0.149 |

**Cost is flat to within 1.7 % across a 60-minute delay** while gross swings 0.061 R. A
plausible hypothesis — "delay because it lets you enter in a cheaper hour" — is refuted:
the whole value of the delay is the entry price, not the toll. (k = 30 is the best joint
cell, 0.185, and is 0.029 better than the swarm's k = 5; that is a gross finding, filed
here because it is free.)

### 8.2 Where the spread actually lands: at-market vs a resting limit

A passive limit fill crosses the spread once (on exit) instead of over the round turn, so it
pays half. The live engine **cannot place one** (l10-X3: 296/296 live entries equal the
executable quote to floating-point equality; `TRADE_ACTION_PENDING` is never set), so this
prices a *capability*, not a strategy:

| entry mode | spread charged | cost R | cost bps | net R | edge:toll R |
|---|---:|---:|---:|---:|---:|
| at market (what the engine does) | 1.0× | 0.24521 | 2.9744 | −0.20687 | 0.156 |
| **resting limit, passive fill** | 0.5× | **0.16837** | 1.9632 | −0.13003 | **0.228** |
| free spread (arithmetic bound) | 0.0× | 0.09152 | 0.9519 | −0.05318 | 0.419 |

**The limit capability is worth 0.07684 R/trade of toll — 31.3 % of the whole bill.** And the
bound matters more than the value: **even at zero spread the pooled book is −0.0532 R/trade.**
Commission and slippage alone (0.0915 R) exceed the gross edge (0.0383 R) by 2.4×. No
execution improvement rescues the pooled book; only cell selection does.

### 8.3 The first-minute cancel is an EDGE rule, not a cost rule

The established refusal (entry touched within 60 s → cancel) costed on the full January pool
(27,658 rows, `FIRST_MINUTE_CANCEL_COST`):

| cohort | n | frac | cost R | cost bps | spread bps | rdp | gross R |
|---|---:|---:|---:|---:|---:|---:|---:|
| refused — touch ≤ 60 s | 16,951 | 61.29 % | **0.2891** | 2.7482 | 1.8172 | 0.00192 | **−0.36991** |
| kept — touch > 60 s | 10,707 | 38.71 % | **0.2354** | 2.7910 | 1.6569 | 0.00190 | **+0.02380** |

The refused cohort is **22.8 % more expensive in R and 1.5 % CHEAPER in money.** Same
instruments, same hours, near-identical stop widths in the mean — the R gap is the tight-stop
tail. **The cancel rule's value is the −0.394 R gross gap, not a toll saving**; do not
attribute any of it to cost.

---

## 9. STRESS — every disclosed uncertainty pushed the expensive way, together

`H1_ROBUST_V1.json`, `H1_EXITSLIP_V1.json`, `H1_STRESS_V1.json`.

**The fifth term this lane does NOT charge in its headline: EXIT slippage.** l10-F9 measured
167 clean live stop exits filling **+0.032236 R worse than the recorded stop** (83.83 %
adverse), by class: fx 0.059002, crypto 0.026603, metals 0.011636, **index 0.007240**. Those
R values are denominated in the *live* book's stop distances (0.19–1.77 % of price) and the
pool's are 0.03–0.75 %, so they transfer as **price**, not as R:
`exit_slip_price = class_R × live_stop_pct × price`. That gives, in bps of notional:
ETHUSD 2.607 · BTCUSD 2.033 · JP225 1.033 · **GER40 0.629** · SPX500 0.542 · UK100 0.508 ·
US30_cash 0.475 · XAUUSD 0.303 · fx 0.171–0.289 · **NAS100 0.137**. On GER40 that is
**73 % of its entire modelled toll**, so it is not a rounding term — it is quarantined
because it rests on 46 index observations against a 300 M-tick spread anchor, and because its
incidence depends on the exit contract.

**The joint stress** = spread ×2 (two crossings) **and** the January/February/March era ratio
**and** exit slippage at multiplier 1.0 **and** entry slippage ×2:

| cohort | n | base e:t | base net R | **mid** e:t | mid net R | **worst joint** e:t | worst net R | months+ (base) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 43,755 | 0.156 | −0.20687 | 0.144 | −0.22851 | 0.084 | −0.41586 | 0/3 |
| cost_bps ≤ 0.50 | 3,191 | 1.212 | +0.00956 | 0.767 | −0.01655 | 0.395 | −0.08357 | 2/3 |
| cost_bps ≤ 0.50 ∧ bh08–20 | 2,759 | 1.428 | +0.01701 | 0.889 | −0.00707 | 0.458 | −0.06712 | **3/3** |
| GER40 ∧ cost ≤ 0.50 | 868 | 2.289 | +0.04165 | 1.273 | +0.01587 | 0.658 | −0.03851 | **3/3** |
| **NAS100 ∧ cost ≤ 0.50** | **526** | **2.469** | **+0.04621** | **2.132** | **+0.04124** | **1.077** | **+0.00557** | **3/3** |
| GER40+NAS100 ∧ cost ≤ 0.50 | 1,394 | 2.356 | +0.04337 | 1.510 | +0.02544 | 0.775 | −0.02188 | **3/3** |
| GER40+NAS100 ∧ cost ≤ 0.50 ∧ bh08–20 | 1,298 | 2.482 | +0.04542 | 1.543 | +0.02675 | 0.793 | −0.01985 | **3/3** |
| GER40 \| london | 504 | 2.758 | +0.05794 | 1.533 | +0.03159 | 0.792 | −0.02391 | **3/3** |
| regime_transition_break | 828 | 1.110 | +0.00489 | 1.010 | +0.00051 | — | — | 2/3 |
| R gate `total_r ≤ 0.02` | 2,622 | 0.999 | −0.00001 | — | — | 0.518 | −0.01214 | 1/3 |

**`NAS100 ∧ cost_bps ≤ 0.50` is the only cohort that clears edge:toll 1.0 under the full
joint stress** (1.077, net +0.00557 R/trade, 36 of 63 positive days, 2 of 3 months). It
survives because its exit-slippage charge is 0.137 bps — the live book's NAS100 stop is
0.189 % of price against GER40's 0.868 %. **That asymmetry rests on 4 and 6 live captures
respectively and is the single weakest input in this table**; if NAS100's true live stop is
GER40-like, its worst-joint edge:toll falls toward GER40's 0.658. Capture is what settles it.

At the **mid** stress (era ratio + exit slippage at the pool's own 54.4 % stop-out rate)
`GER40+NAS100 ∧ cost ≤ 0.50` holds at 1.510 with net +0.02544 and all three months positive,
and `GER40|london` at 1.533.

Terms that do **not** move any verdict: entry slippage (±2× moves the pooled book 0.147↔0.167
and the index cells not at all — their measured slip is 0), swap (removing it entirely moves
the pool 0.156 → 0.165 and the index cells not at all), and the era ratio (pool 0.156 →
0.157; per-symbol it ranges 0.41× on JP225 to 1.91× on USDJPY and it matters where it
matters — GER40 1.077×, so GER40's cells lose ~8 % of their margin).

---

## 10. WHAT THIS LANE ESTABLISHES, AND WHAT IT DOES NOT

**Establishes.**

1. The broker-true, hour-aware, all-in toll on the live-expressible book is **0.245214 R /
   2.9744 bps**, 34.9 % above the basis the swarm used, and edge:toll is **0.1564**, not 0.211.
2. **Cost dispersion is real and the axes are now ranked.** In money the instrument carries
   it (η² 0.858; with hour, 0.985) and family carries essentially none (η² 0.005). In R the
   stop width carries the most (η² 0.442). The 12.1× family figure is 12.35× in R, 3.08× in
   money, and the two views rank families in *opposite* order (ρ = −0.5714).
3. **Cells where edge already exceeds toll exist, and there are 651 of them** — 152 at
   n ≥ 100, 50 at n ≥ 300. They are concentrated, without exception at depth, in the index
   complex during London and the London/NY overlap.
4. **An ex-ante money gate expresses them.** `cost_bps ≤ 0.50` admits 7.3 % of the book at
   edge:toll 1.212 (train −0.0006 / test +0.0304); with broker hours 08–20 it is 1.428 and
   positive in all three months. The shipped R gate, even fed broker-true costs, buys 0.188.
5. **Two structural cost objects nobody had priced**: the broker-hour-00 rollover (2.12 % of
   trades, 13.19 % of the toll, 7.0× the flat basis, FX-only) and the swap crossing at broker
   hours 22–23 (3.81 % of trades, 4.95 % of the toll).
6. **Entry timing moves gross, not toll.** A 60-minute delay changes cost by 1.7 %. A resting
   limit halves the spread and is worth 0.0768 R/trade — and the engine cannot place one.
   Even at zero spread the pooled book is −0.0532 R/trade, so no execution repair rescues it.

**Does not establish.**

- **That any cell travels.** Every cell here is chosen after seeing three months. The
  train/test split in §7.1 is the only out-of-sample statement, it covers only the gate
  threshold, and it is one month.
- **Multiplicity.** 651 hits from 28 cell definitions over 3,472 non-empty cells. No
  correction is applied, deliberately. At the estate's ratified `CANDIDATE_BOOK_V1` standard
  none of these has been declared, gated or billed.
- **Exit slippage as a headline term.** §9 prices it both ways; the headline excludes it.
  It is the largest single number this lane leaves outside its own basis, and on GER40 it is
  73 % of the modelled toll.
- **Anything about the 46 % limit cohort.** This lane is the at-market book only.
- **Anything about redacted_account.** All costs are FTMO. l10-X12 measured redacted_account BTCUSD at
  21.9× FTMO's spread, so this surface does not transfer across brokers.

**The one-line prescription.** The estate's affordability gate is R-denominated, and R is
the wrong unit for a broker toll: it divides by a stop width whose variance exceeds the
broker's. Re-denominate the gate in basis points of notional, key the spread on the broker
hour, charge commission from the shipped broker-true schedule and swap on rollover crossings
— and the same 43,755 candidates that lose 0.207 R/trade contain a 2,759-trade,
three-months-positive book at edge:toll 1.428.

---

## 11. ARTIFACTS

| file | what |
|---|---|
| `h1_01_cost_rows.py` → `h1_COST_ROWS_V1.jsonl.gz`, `h1_COST_ROWS_V1_BUILD.json` | the per-candidate cost ledger: 43,755 rows, every term in price/bps/R, every axis, the repaired-contract gross, provenance stamps |
| `h1_02_tables.py` → `H1_SURFACE_V1.json` | all axes and crosses, η², dispersion, bps-vs-R ranks, first hit list |
| `h1_03_hunt.py` → `H1_HUNT_V1.json` | 29 cell definitions, 651 hits with n/t/day/month splits, cheapest-and-deepest tables |
| `h1_04_decompose.py` → `H1_DECOMP_V1.json` | term dominance, bps-vs-R Spearman, affordability sweeps, entry-delay joint curve, entry-mode incidence, first-minute-cancel cost, rollover forensics |
| `h1_05_frontier.py` → `H1_FRONTIER_V1.json` | the ex-ante money gate at fine grid, era variant, R-gate comparison, train/test, per-symbol composition |
| `h1_06_robust.py` → `H1_ROBUST_V1.json` | one-at-a-time sensitivities (spread ×2/×0.5, era, slip, swap) over 11 cohorts, symbol×hour grid, day-of-week |
| `h1_07_exitslip.py` → `H1_EXITSLIP_V1.json` | l10-F9 exit slippage converted to bps per symbol and applied at three incidences |
| `h1_08_stress.py` → `H1_STRESS_V1.json` | the joint worst case, and the index-complex hour map |
| `h1_00_march_zones.py` → `h1_MAR_ZONES_V1.jsonl.gz` | March kill-zone / session join keys (26,500 rows) |
| `h1_RESULT.md` / `h1_RESULT.json` | this receipt |
