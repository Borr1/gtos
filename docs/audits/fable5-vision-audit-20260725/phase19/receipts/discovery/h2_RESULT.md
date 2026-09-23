# h2 — where is the EDGE biggest

Lane key `h2`. Wave-19 broad-forensic follow-on. **The hunt succeeded: cells where edge/cost > 1
exist, they are measured, and they replicate out of sample.** Machine-readable companions:
`h2_RESULT.json`, `H2_CELLS_V1.json`, `H2_FRONTIER_V1.json`, `H2_WINNERS_V1.json`,
`H2_DEEP_V1.json`, `H2_HOURCOST_V1.json`, `H2_CASH_V1.json`, `H2_FINAL_V1.json`.

**Population.** The LIVE-EXPRESSIBLE (at-market) cohort, January + February + March 2026,
**n = 43,755**, from `e_{JAN,FEB,MAR}_ATMKT_V1.jsonl.gz`. Repaired contract = market entry delayed
5 M1 bars + TRAIL025 (no target, initial stop −1R, stop trails 0.25R behind running MFE).
Reference cell reproduced **exactly**: gross +0.038342, t +12.345, cost 0.181834, net −0.143492,
53/63 days (`E_ATMKT_POOLED_V1.json → D1E1G0`).

---

## 0. THE ANSWER IN ONE TABLE

**GER40 and NAS100, traded only while their own underlying exchange's cash market is open.**

| | n | share of book | gross R | toll R | **net R** | **edge:toll** | gross bps | toll bps | margin bps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **GER40 + NAS100, cash session** | **1,557** | 3.6 % | +0.065401 | 0.031269 | **+0.034132** | **2.092** | +1.2795 | 0.4894 | **+0.7901** |
| GER40, cash session | 903 | 2.1 % | +0.071149 | 0.032487 | +0.038662 | 2.190 | +1.3539 | 0.4844 | +0.8695 |
| NAS100, cash session | 654 | 1.5 % | +0.057465 | 0.029587 | +0.027878 | 1.942 | +1.1768 | 0.4963 | +0.6805 |
| *whole book, hour-true cost* | 43,755 | 100 % | +0.038342 | 0.220328 | −0.181986 | 0.174 | +0.2312 | 2.6692 | −2.4381 |

The headline cell, in full: **day-clustered t = +2.02**, day-block bootstrap 95 % CI
**[+0.002287, +0.067211]**, **P(net ≤ 0) = 0.0194**, **positive in all three months**
(+0.039816 / +0.025693 / +0.037024), 34 of 63 days positive.

**It is not sitting on one contract rung.** Net R at delay k ∈ {2,3,5,10,15,20,30} =
+0.0041 / +0.0023 / **+0.0341** / +0.0173 / +0.0049 / +0.0002 / +0.0050 — positive at every rung
from k=2 out to k=30, negative only at k=0 (−0.0700) and k=1 (−0.0100), which *is* the
first-minute give-back the swarm already priced. And at k=5 it is positive under **all five**
exit contracts: TRAIL025 +0.0341, TS90S1 +0.0257, T3S1 +0.0248, TS60S1 +0.0208, STOPONLY +0.0145,
INC (the shipped 2R/−1R) +0.0084.

**Out of sample.** The rule that selects it never sees February or March: define the cash window
from each exchange's own calendar, then keep the instruments that were net-positive in **January
only**. That picks exactly `{GER40, NAS100}` and they read **+0.031332 R/trade on February+March**
(n = 1,043, day-clustered t +1.44, +0.025693 Feb / +0.037024 Mar, 23 of 42 days positive).

---

## 1. The cost model everybody has been dividing by is HOUR-BLIND, and the hour is the biggest
   cost axis in the estate

`e_lib.real_cost_parts:108` charges `tk["spread_bps_median"]` — **one constant per symbol, for
every hour of every day**. Measured consequence: `cost_bps` has **coefficient of variation exactly
0.0000** within GER40, US30_cash, NAS100, UK100, USDCAD, USDCHF, JP225, BTCUSD, UKOIL_cash and
USOIL_cash, and ≤ 0.0135 for every other symbol but ETHUSD. The whole swarm's cost side therefore
has **no intra-symbol structure at all**.

The very same artifact (`L10X_TICK_SPREAD_V1.json`) already carries
`spread_bps_median_by_broker_hour`, on 24 of 24 symbols. Its within-symbol dispersion:

| symbol | min bps | max bps | ratio | flat median actually charged |
|---|---:|---:|---:|---:|
| EURUSD | 0.0881 | 3.0549 | **34.67×** | 0.0881 — *the minimum* |
| GBPUSD | 0.2239 | 7.6736 | 34.28× | 0.2265 |
| USDCAD | 0.2818 | 5.6885 | 20.18× | 0.3508 |
| USDJPY | 0.1862 | 3.5892 | 19.28× | 0.1862 — *the minimum* |
| NZDUSD | 0.8710 | 16.2181 | 18.62× | 1.0351 |
| UK100 | 0.6237 | 5.6885 | 9.12× | 0.8222 |
| GER40 | 0.4571 | 1.5136 | 3.31× | 0.5012 |
| JP225 | 1.4454 | 2.9174 | 2.02× | 1.4622 |
| NAS100 | 0.4955 | 0.7161 | 1.45× | 0.5754 |
| US30_cash | 0.3981 | 0.5309 | 1.33× | 0.4027 |

**h2-F1 — the swarm's closing observation was pointed at the wrong axis, and understated the
right one.** "Real cost per family disperses 12.1×" reproduces here at **12.40× in R** — and at
only **2.81× in bps**. So **77 % of the family cost dispersion is a stop-width artifact**, not a
toll difference. The genuine price-space dispersion lives on two other axes: **instrument, 25.71×**
(US30_cash 0.4027 → ETHUSD 9.8318 bps) and **hour-within-instrument, up to 34.67×**.

**h2-F2 — re-costing hour-true is not cosmetic; it changes the answer.** Broker hour from
`src/utils/broker_clock.py` `NEW_YORK_PLUS_7` (UTC+2 on EST, UTC+3 on EDT — the measured
FTMO-Server3 rule, correct through the 2026-03-08..03-28 window inside March):

- Pooled toll **0.181834 → 0.220328 R** (2.4571 → 2.6692 bps). The flat model was **under**-charging.
- **GER40, the swarm's one instrument clearing 1.0, goes from net +0.01803 to −0.01714** and from
  3/3 months positive to 1/3. Its edge:toll of 1.387 was measured against a spread constant that
  undercharges its overnight hours by up to 2.8× (broker hours 3–8 true 1.26–1.41 bps, charged 0.501).
- Of the cells that pay under one cost frame or the other: **189 win under both, 34 are killed by
  the re-cost, 2 are created by it.**
- Under hour-true cost, **zero of 24 instruments is net-positive at the whole-instrument level.**

---

## 2. Where the edge actually is — and why the biggest edge is the worst place to look

### 2.1 Edge magnitude census (flat-cost frame, 1,526 cells at n ≥ 100)

| | count |
|---|---:|
| cells with gross ≥ **2×** the pooled +0.038342 R | 267 |
| cells with gross ≥ **3×** | 102 |
| cells with gross ≥ 2× the pooled +0.23119 bps | 515 |
| cells with gross ≥ 3× bps | 372 |
| of the ≥2×-R cells, **net-positive** | **50** |

### 2.2 The largest genuine edge concentration is the estate's most expensive family

Ranked by t of (cell gross − pooled gross):

| cell | n | gross R | × pooled | toll R | net R | gross bps | toll bps | t |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `structural_distance_extreme` | 5,696 | +0.14149 | **3.69×** | 0.42084 | **−0.27936** | +0.693 | 2.183 | **8.52** |
| `structural_distance_extreme \| lo` vol | 5,247 | +0.14237 | 3.71× | 0.44658 | −0.30421 | +0.677 | 2.181 | 8.12 |
| vol tercile `lo` (tightest stops) | 14,601 | +0.09039 | 2.36× | 0.36125 | −0.27086 | +0.545 | 2.453 | 7.94 |
| `SHORT \| lo` | 8,640 | +0.10068 | 2.63× | 0.37184 | −0.27115 | +0.605 | 2.530 | 7.49 |
| `structural_distance_extreme \| london \| LONG` | 425 | +0.28950 | **7.55×** | 0.43974 | −0.15024 | +1.107 | 1.646 | 5.42 |

**h2-F3 — the highest-edge cells are the tight-stop cells, and tight stops are where the toll is
largest in R.** The identity that governs everything here:

```
net_r  =  (gross_bps − cost_bps) / (rdp × 1e4)          rdp = risk_distance / entry_price
```

Both limbs scale as 1/rdp, so **the per-trade edge:toll ratio is exactly scale-free in stop
width** — this is `l2-F2` and `e5-F3`'s WIDEN result reproduced from a third direction, and it is
why the naive fix fails.

**Measured, at trade level:** select the 16.6 % of trades whose `cost_true` is below the pooled
gross edge (n = 7,271) — the R-denominated "affordable" set — and you get gross **+0.01198**, toll
0.02252, **net −0.01054** (t −1.74). Mean rdp there is **67.8 bps** against the book's 28.4:
you have selected wide stops, and their gross R collapsed by the same factor their toll did.
**R-denominated affordability selection is a stop-width filter and it loses money.** Only
price-space (bps) affordability selects anything real.

---

## 3. Q3 — is edge concentration independent of cost concentration?

**Yes in price space, and that is the whole reason a cell can cross 1.**

| frame | statistic | value |
|---|---|---:|
| 24 symbols, hour-true | Spearman(gross **bps**, cost **bps**) | **−0.095** |
| 1,526 cells, flat cost | Spearman(gross **bps**, cost **bps**) | **+0.007** |
| 24 symbols, hour-true | Spearman(gross **R**, cost **R**) | +0.047 |
| 1,526 cells, flat cost | Spearman(gross **R**, cost **R**) | **+0.266** |
| 24 symbols, hour-true | Spearman(net R, cost R) | **−0.975** |
| 24 symbols, hour-true | R²(net R \| cost R) | **0.9810** |
| 24 symbols, hour-true | R²(net R \| gross R) | **0.0361** |
| 24 symbols, hour-true | R²(margin bps \| cost bps) | 0.9706 |
| 24 symbols, hour-true | R²(margin bps \| gross bps) | 0.2340 |

Per axis (flat cost, Spearman gross_bps vs cost_bps): **symbol −0.125** (mildly favourable),
**session −0.800** (favourable), hour +0.101, **family +0.464** (adverse — the expensive families
carry more edge), symbol×session −0.171, symbol×vol +0.048.

So: **cheap cells are not low-edge cells** — the two are statistically independent, and on the
symbol axis the relationship is mildly in our favour. But cost still writes the cross-section:
98.1 % of the variance in net across instruments is cost, 3.6 % is gross.

---

## 4. The permutation null — the winners are winning on CHEAPNESS, not on edge

H0 is **flat edge**, not zero edge: shuffle every trade's gross within its own month, leave its
real cost attached. 2,000 draws, all 1,792 cell definitions.

| | observed | null |
|---|---:|---|
| winner cells (net > 0, n ≥ 100) | **125** | mean 137.0, p05 110, p50 137, p95 164, max 197 → **p = 0.783** |
| max cell excess over pooled gross | **+0.334563** | p95 +0.237708 → **p = 0.0020** |
| max t of (cell gross − pooled) | **+8.519** | p95 +4.472 → **p = 0.0000** |

**h2-F4 — read both rows.** The *number* of paying cells is exactly what a perfectly flat edge
predicts (p 0.78): a cell pays when its toll falls below the pooled +0.038342 R, and 59 of the 125
winners are cheap enough to pay at the pooled edge alone. **But genuine edge concentration also
exists** — the extremes are far outside the null (p 0.002, p 0.000). The two facts coexist because
the concentrated edge sits in the expensive cells (§2.2) and the paying cells are the cheap ones.

Flat-edge prediction vs realized net across 1,526 cells: **Pearson 0.9243, Spearman 0.9133**;
variance shares — cost 1.152, edge 0.168, covariance −0.320.

---

## 5. The ex-ante rule: trade an instrument only while its own cash market is open

Not a fitted cell. Each window is written in the **exchange's own local wall clock** and converted
per day, so it is right through the US/EU DST disagreement window inside March. No outcome column
was consulted to define it.

| instrument class | window (exchange local) |
|---|---|
| GER40 | Xetra 09:00–17:30 Europe/Berlin |
| UK100 | LSE 08:00–16:30 Europe/London |
| US30_cash, NAS100, SPX500 | NYSE 09:30–16:00 America/New_York |
| JP225 | TSE 09:00–15:00 Asia/Tokyo |
| XAUUSD, XAGUSD | 08:00–21:00 Europe/London |
| USOIL_cash | NYMEX 09:00–14:30 America/New_York; UKOIL_cash ICE 08:00–17:30 London |
| 12 FX pairs | 08:00–17:00 Europe/London |
| BTCUSD, ETHUSD | 24/7, no window |

**h2-F5 — the rule keeps 47.6 % of the book, cuts the hour-true toll by 29.2 % and RAISES gross by
8.3 %.** Toll 0.220328 → 0.156075 R; gross +0.038342 → +0.041519; net −0.181986 → −0.114556.
Both limbs move the right way, which is what a mechanism looks like and what a fitted filter
usually does not.

Per instrument, inside its own cash session, hour-true (top of 24):

| symbol | n | gross R | toll R | net R | gross bps | toll bps | margin bps | t_clu | months + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **GER40** | 903 | +0.07115 | 0.03249 | **+0.03866** | +1.354 | 0.484 | **+0.869** | **+1.95** | **3/3** |
| **NAS100** | 654 | +0.05747 | 0.02959 | **+0.02788** | +1.177 | 0.496 | **+0.680** | +1.05 | **3/3** |
| UK100 | 974 | +0.05710 | 0.06583 | −0.00873 | +1.031 | 0.727 | +0.304 | −0.40 | 1/3 |
| XAUUSD | 1,101 | +0.05472 | 0.06409 | −0.00937 | +1.363 | 1.261 | +0.101 | −0.60 | 1/3 |
| US30_cash | 610 | +0.01907 | 0.02925 | −0.01018 | +0.226 | 0.398 | −0.172 | −0.39 | 1/3 |
| SPX500 | 651 | +0.05424 | 0.07953 | −0.02529 | +1.041 | 0.931 | +0.110 | −0.94 | 1/3 |

Inside the rule, by side: GER40|LONG n=413 net **+0.05608** (3/3 months); NAS100|SHORT n=348
+0.03730; US30_cash|LONG n=283 +0.03454 (3/3); UK100|LONG n=450 +0.03256; GER40|SHORT n=490
+0.02398; NAS100|LONG n=306 +0.01716; JP225|LONG n=202 +0.01274.

**h2-F6 — widening past two instruments destroys it.** GER40+NAS100+UK100+SPX500+XAUUSD+US30_cash
inside cash: n = 4,893 (11.2 % of the book), net **+0.00238**, edge:toll 1.046, bootstrap
**P(≤0) = 0.41**. The affordable set is two names, not six.

---

## 6. Out-of-sample — selection on January, read on February + March

| test | selected | out-of-sample read |
|---|---|---|
| instruments, flat cost, no window | `{GER40}` (the only Jan-positive one) | n=1,243, **net +0.021021**, t_clu +1.39, Feb +0.0187 / Mar +0.0230 |
| instruments, hour-true, inside cash rule | `{GER40, NAS100}` | n=1,043, **net +0.031332**, t_clu +1.44, Feb +0.0257 / Mar +0.0370, 23/42 days |
| instruments, hour-true, no window | none — 0 of 24 positive in Jan | — |
| **all cell definitions, flat cost** | 118 cells net-positive in Jan | 57 of 118 still positive = **hit 48.3 %** vs a **12.4 %** baseline; mean OOS net −0.010683 vs baseline −0.128825 |
| **all cell definitions, hour-true** | 138 cells | 61 of 138 = **hit 44.2 %** vs **11.7 %** baseline; mean OOS net −0.019183 vs −0.164940 |

**h2-F7 — cell selection travels.** A 3.8–3.9× lift in hit rate and a 12× improvement in the level
(−0.129 → −0.011). It does not, on average, reach profitability: the mean January-selected cell is
still net-negative out of sample. Two instruments do reach it.

---

## 7. Full enumeration — every cell that pays

Nothing below is filtered for multiplicity. Counts first, then the robust tier; the complete lists
are in `H2_HOURCOST_V1.json → winners_hour_true_n50` (191 rows) and
`H2_WINNERS_V1.json → winners_net_positive_n100` (125 rows, flat cost) with per-month, split-half
and day-positivity fields on every one.

| threshold | flat cost | hour-true |
|---|---:|---:|
| cells scanned | 1,792 (n≥20) / 1,526 (n≥100) | 2,421 (n≥50) |
| **cells with net > 0** | 125 at n≥100; 153 at n≥50 | **191 at n≥50; 140 at n≥100; 90 at n≥200** |
| of those, positive in all 3 months | 23 at n≥100 (also both split-halves) | **43 at n≥50; 36 at n≥100** |
| of those, day-clustered t ≥ 2 | — | 8; **6 also 3/3 months** |

**The robust tier — hour-true, n ≥ 100, positive in all three months, day-clustered t ≥ 1.0
(17 cells):**

| axis | cell | n | gross R | toll R | net R | edge:toll | t_clu |
|---|---|---:|---:|---:|---:|---:|---:|
| symbol×broker-hour | GER40 \| b16 | 108 | +0.25334 | 0.03628 | **+0.21705** | **6.98** | +2.47 |
| symbol×broker-hour | NAS100 \| b18 | 105 | +0.13342 | 0.03021 | +0.10322 | 4.42 | +1.76 |
| symbol×family×session | GER40 \| liquidity_sweep_reclaim \| ny | 114 | +0.12991 | 0.03842 | +0.09149 | 3.38 | +1.59 |
| symbol×broker-hour | GER40 \| b10 | 206 | +0.11274 | 0.03021 | +0.08253 | 3.73 | +2.27 |
| symbol×session×side | GER40 \| london \| LONG | 228 | +0.11385 | 0.03231 | +0.08153 | 3.52 | +1.77 |
| symbol×session×side | US30_cash \| london \| LONG | 195 | +0.13683 | 0.05901 | +0.07782 | 2.32 | +1.62 |
| symbol×family | GER40 \| session_open_range_break | 114 | +0.08368 | 0.01274 | +0.07094 | 6.57 | +1.35 |
| family×hour-block | regime_transition_break \| h00_06 | 171 | +0.10566 | 0.03957 | +0.06609 | 2.67 | +2.08 |
| symbol×broker-hour | US30_cash \| b10 | 175 | +0.11317 | 0.05060 | +0.06257 | 2.24 | +1.42 |
| symbol×hour-block×side | NAS100 \| h17_23 \| SHORT | 188 | +0.11665 | 0.05623 | +0.06041 | 2.07 | +1.01 |
| symbol×session | GER40 \| london | 504 | +0.09088 | 0.03295 | +0.05794 | 2.76 | +2.36 |
| symbol×bh-block×side | NAS100 \| b18_23 \| SHORT | 211 | +0.10007 | 0.04749 | +0.05259 | 2.11 | +1.28 |
| symbol×session×side | USDJPY \| london \| LONG | 178 | +0.17077 | 0.12241 | +0.04836 | 1.40 | +1.02 |
| symbol×bh-block | GER40 \| b08_12 | 698 | +0.10436 | 0.05953 | +0.04483 | 1.75 | +1.91 |
| symbol×hour-block | GER40 \| h07_11 | 620 | +0.07863 | 0.03743 | +0.04120 | 2.10 | +2.06 |
| symbol×session | US30_cash \| london | 406 | +0.09250 | 0.05823 | +0.03427 | 1.59 | +1.19 |
| family×side | regime_transition_break \| LONG | 431 | +0.05869 | 0.03442 | +0.02427 | 1.71 | +1.05 |

Thin cells that pay large and are reported for completeness, **n < 100, treat as leads only**:
`EURUSD|b14` n=57 net +0.28331 · `GER40|structural_distance_extreme|london` n=69 +0.18606 ·
`CHFJPY|b23` n=58 +0.15957 · `GER40|session_open_range_break|london` n=57 +0.15178 (t_clu +3.08) ·
`GER40|structural_distance_extreme|ny` n=60 +0.09940 · `XAUUSD|b20` n=50 +0.08150 ·
`UK100|session_open_range_break|london` n=59 +0.08125 · `JP225|b08` n=65 +0.06866 ·
`SPX500|b21` n=54 +0.06381 · `XAUUSD|volatility_compression_expansion|*` n=53 +0.07488.

### The family table (hour-blind cost, for comparison with the swarm's 12.1×)

| family | n | gross bps | toll bps | margin bps | gross R | toll R | net R | edge:toll | rdp bps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `regime_transition_break` | 828 | **+3.610** | 2.626 | **+0.984** | +0.04919 | 0.03393 | **+0.01526** | **1.450** | 97.9 |
| `structural_distance_extreme` | 5,696 | +0.693 | 2.183 | −1.490 | +0.14149 | 0.42084 | −0.27936 | 0.336 | 6.6 |
| `cross_asset_lead_lag` | 6,075 | +0.576 | 2.635 | −2.059 | +0.05260 | 0.25313 | −0.20053 | 0.208 | 15.3 |
| `volatility_compression_expansion` | 1,798 | +0.407 | 2.473 | −2.066 | −0.02160 | 0.04155 | −0.06315 | −0.520 | 76.2 |
| `session_open_range_break` | 2,943 | −0.587 | 2.143 | −2.729 | +0.01641 | 0.07523 | −0.05882 | 0.218 | 38.5 |
| `liquidity_sweep_reclaim` | 13,372 | +0.058 | 2.394 | −2.335 | +0.02914 | 0.18820 | −0.15906 | 0.155 | 19.9 |
| `displacement_continuation` | 13,022 | −0.009 | 2.620 | −2.629 | +0.00864 | 0.09043 | −0.08179 | 0.096 | 39.6 |

`regime_transition_break` is the one family whose price-space margin is positive. It is 1.9 % of
the book (n=828), net +0.01526, positive in all three months (+0.0110/+0.0223/+0.0134), and its
`h00_06` block (n=171) is positive at **every** delay rung from k=0 to k=20 — the only cell in
the whole scan that does not need the entry repair at all.

---

## 8. Caveats, stated plainly

1. **The 3-month window is the entire measurable population, not a sample.** M1 bars exist for
   2026-01/02/03 only (`.../LANE_INPUTS_TRUE_UTC_V1/sources/bars/`); there are **no April or May
   2026 M1 bars anywhere on this machine**, so the at-market path cohort cannot be extended. Any
   travel test past March needs a bar capture first.
2. **Hour-true cost is a MEDIAN per broker hour**, not a per-trade quote. It is a large improvement
   on one constant per symbol and still not the tick-exact toll at the decision instant.
   `src/costs/spread_model.py` and Session LN's broker-true commission are the next refinement, and
   they belong to h1.
3. **Commission is 0.0 for every index CFD in this cost artifact** (`e_lib._COMM:85`). If FTMO
   charges index commission the GER40/NAS100 result shrinks directly by that amount; margin is
   +0.87 and +0.68 bps, so a commission above ~0.7 bps round trip erases it. **This is the single
   cheapest thing that could falsify the headline and it should be checked against a broker
   statement, not a config.**
4. **Selecting GER40 and NAS100 used all three months.** The honest number is the January-only
   selection read forward: **+0.031332** on Feb+Mar, not +0.034132.
5. Cells are reported with no multiplicity correction, by instruction. §4's permutation null is the
   calibration: 125 winners at n≥100 is *exactly* the flat-edge expectation (p 0.78), so the winner
   set as a whole should be read as "cheap", and only §7's robust tier and §0's headline as
   "conditioned".
6. **Pseudo-replication is a non-issue here** — 198 of 43,755 rows (0.45 %) sit on a repeated
   `candidate_id`, against 24.39 % on the full pool. No de-duplication was applied or needed.
7. Volatility state is a **within-symbol rdp tercile computed over all three months**; the tercile
   edges are in-sample. rdp itself is ex-ante (`risk_distance / entry_price`, both known at the
   decision instant).

---

## 9. Reproduce

```bash
cd docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery
python3 h2_scan.py       # 1,792 cells, all axes/pairs/triples      -> H2_CELLS_V1.json
python3 h2_frontier.py   # flat-vs-concentration + 2,000 permutations -> H2_FRONTIER_V1.json
python3 h2_winners.py    # merged winner tables + k-ladders          -> H2_WINNERS_V1.json
python3 h2_deep.py       # GER40 anatomy, cost frontier, OOS         -> H2_DEEP_V1.json
python3 h2_hourcost.py   # hour-true re-cost, full re-scan           -> H2_HOURCOST_V1.json
python3 h2_cash.py       # the ex-ante cash-session rule             -> H2_CASH_V1.json
python3 h2_final.py      # headline cells + bootstrap + Q3           -> H2_FINAL_V1.json
```
Shared substrate `h2_lib.py`. Deterministic; permutation and bootstrap seeded at 20260806.
