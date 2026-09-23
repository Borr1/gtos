# h5 — the direct hunt: every cell where edge/cost > 1

Lane key `h5`. Wave 19 broad-forensic. Every number below is measured on this machine and
reproduces from the scripts named in §12. Machine-readable companion: **`h5_RESULT.json`**
(3.4 MB — it carries the FULL enumeration, 243 + 439 + 193 + 68 cells with their split-halves,
their three hunt months and their April+May out-of-sample read; this file is the summary).

---

## 0. The answer in eight lines

| | measured |
|---|---|
| **Do cells with edge/cost > 1 exist?** | **YES, and they are not rare.** 243 of 4,130 cells at n ≥ 50 (flat toll), **193** at the honest hour-aware toll |
| **Best single cell, hunt window** | `hour × cost_dec = 11\|0` ratio **6.76** (n 167) · `GER40 × hour 14` ratio **6.20** (n 120) · `GER40 × hour 08` ratio **4.45** (n 213) |
| **Does the count beat a null?** | **Barely.** Null that keeps symbol + cost structure and destroys cell structure yields 174.8 ± such cells; real 201. emp p **0.049** |
| **Does any single cell beat the null?** | **NO. Zero cells at Westfall–Young p ≤ 0.20.** Real max day-clustered t over all 4,130 cells = **2.725**; the null's *maximum* averages **2.745** (P2) and **2.80** (P3) |
| **Do they survive out of sample?** | **28.2 %** of ratio > 1 cells stay > 1 on April+May, against a **4.5 %** base rate — a **6.2×** lift, monotone in the hunt ratio (>2.5 bucket: **54.5 %**) |
| **Is that lift edge or cost?** | **Cost.** Spearman(cell cost, hunt→OOS) **0.948**; Spearman(cell gross) **0.299**. Across the 24 instruments: cost **0.826**, **gross 0.024** |
| **Does any cost-only rule pay?** | **No.** "Trade only in your own cheap hours" is worth **+0.000 R** (ratio 0.213 vs the book's 0.213). Every cost cut is ≈ break-even and contract-fragile |
| **What is left standing** | **One cell positive in all five months**: `GER40 @ UTC h14`, n 193, ratio **5.42**, net **+0.1348 R/trade**, 51 of 66 contract arms positive — and it is 1 of 4,130 looks with WY p ≈ 1 |

**The lane's premise was half right.** Cost does disperse 12×, edge/cost > 1 cells do exist, and
they carry real out-of-sample information. But the information they carry is **the broker's fee
schedule, not an edge**: a cell's cost rank is 0.95-persistent and its gross rank is 0.30-persistent
across cells and **0.02-persistent across instruments**. Selecting on affordability re-discovers
which symbols are cheap. It does not find where the edge is, because the edge does not sit still.

**The one number to take away:** at the hour-aware toll the five-month live-expressible book is
gross **+0.03831**, toll **0.23020**, net **−0.19188 R/trade** over **69,480 trades**, and **0 of
66 (entry-delay × exit-contract) arms is net-positive**.

---

## 1. Substrate, contract and reproduction

The hunt runs on the **LIVE-EXPRESSIBLE** cohort — `born_at_limit`, the only order type the live
engine can place (l10-X3: 296/296 live entries equal the executable quote to floating-point
exactness) — under the swarm's repaired contract: **market entry at the close of path bar k = 5,
TRAIL025 exit** (no target, initial stop −1R, stop trails 0.25R behind the running MFE).

| month | source pack | at-market rows |
|---|---|--:|
| 2026-01 | `CJ_RECLOCKED_S0R0_POOL_V1` | 14,905 |
| 2026-02 | `CP_FEBRUARY_S0R0_POOL_V1` | 13,966 |
| 2026-03 | `FA2_M_R0` missed-opportunity ledger | 14,884 |
| **hunt window** | | **43,755** |
| 2026-04 | `CS_APRIL_S0R0_POOL_V1` | **13,837** |
| 2026-05 | `CS_MAY_S0R0_POOL_V1` | **11,888** |
| **five months** | | **69,480** |

**April and May were built by this lane and were never seen during the hunt.** `e_build_atmkt.py`
ran unchanged against `bridge_ftmo_m1_202604` / `202605`; every quantile cut, decile boundary and
rule carried into them is the one frozen on January.

The swarm headline reproduces exactly before anything is added:

```
n 43,755   gross +0.038342   t +12.345   cost(flat) 0.181834
edge 0.2312 bps   toll 2.4571 bps   ratio_bps 0.0941
```

### 1.1 Two ratios, and they are different books — report both, always

```
ratio_R   = mean(gross_R) / mean(cost_R)          net R/trade > 0  <=>  ratio_R > 1
ratio_bps = mean(gross_R*rdp) / mean(cost_R*rdp)  rdp = risk_distance/entry_price
```

`ratio_R` is a **constant-risk** book — how this estate sizes — and is the money-relevant one.
`ratio_bps` is a **constant-notional** book and is the framing the swarm headline used
(0.231 vs 2.457 bps). They can disagree in the sign of (ratio − 1): **60 of the 243 flat-toll
ratio_R > 1 cells have ratio_bps ≤ 1**, so a cell is only called affordable on `ratio_R`.

### 1.2 The toll was wrong in the way most dangerous to an hour-conditioned hunt — and is now right

`e_lib.real_cost_parts` charges every symbol a **FLAT** tick-median spread. `L10X_TICK_SPREAD_V1.json`
already carries `spread_bps_median_by_broker_hour`, so the flat charge is a choice, not a limit. h5
re-runs the entire hunt on the hour-aware toll using **h3_lib's** transfer convention (imported, not
re-derived: the intraday spread shape is a property of the **New York** wall clock, so the tick
window's broker hour maps through `ny_hour = (broker_hour − 7) % 24` and the pool row through its
own America/New_York hour — which keeps session alignment across the 2026-03-08 US DST change).

**It changes the headline of the swarm's own §7.5 table.**

| | flat toll | hour-aware toll |
|---|--:|--:|
| book cost (3 M) | 0.181834 | **0.220328** |
| book ratio_R | 0.2109 | **0.1740** |
| **GER40 cost** | 0.04661 | **0.08179** (×1.755) |
| **GER40 ratio_R** | **1.387** | **0.790** |
| UK100 cost | 0.10145 | **0.27043** (×2.666) |
| cells ratio > 1 at n ≥ 50 | 243 | **193** |

> **CORRECTION TO THE SYNTHESIS. "GER40 is the only symbol net-positive at broker truth" is an
> artifact of a flat spread charge.** GER40's trades concentrate in hours whose real quoted spread
> is 1.755× its own median; at the hour-aware toll the instrument books **−0.01714 R/trade**, and on
> April+May **−0.04666** (t_day −2.53). **No instrument of 24 is net-positive over five months.**
> The correction runs the other way on the *hour* cells: `GER40|8` gets **cheaper** (0.02906 →
> 0.02872) because 08:00 UTC is the Xetra cash open, where the DAX spread is at its daily floor.

---

## 2. The census — how many looks this lane took

Twelve axes, all ex-ante knowable at the decision instant:
`symbol · family · session · hour · side · dow · rdp_dec · cost_dec · rv_q · rdp_rel_q · prob_q · efp_q`
(`rv_q` = quintile of realised 60-minute volatility relative to that symbol's January median, computed
from bars that close **at or before** the decision instant — zero look-ahead; `rdp_rel_q` = stop width
relative to the symbol's own January median; all cuts frozen on January).

12 singles + 66 pairs = **78 groupings, 4,664 cells, 4,130 at n ≥ 50.**

| floor | cells examined | ratio_R > 1 | ratio_R > 0.5 |
|---|--:|--:|--:|
| n ≥ 20 | 4,437 | 310 | 785 |
| **n ≥ 50** | **4,130** | **243** | **682** |
| n ≥ 100 | 3,671 | 194 | 567 |
| n ≥ 200 | 2,929 | 128 | 395 |
| n ≥ 500 | 1,598 | 36 | 143 |

At the hour-aware toll, same cell definitions: **193** > 1 and **564** > 0.5.
Exploratory triple scan (220 three-axis groupings, reported for completeness, not used for any
claim): **39,835 cells at n ≥ 50, 3,303 ratio > 1, 68 surviving all seven sub-samples.**

---

## 3. THE ENUMERATION — top 30 of the 193, hour-aware toll, ranked by (ratio − 1) × n

Full list of all 193 (plus all 243 at the flat toll and all 439 in the 0.5–1.0 band) is in
`h5_RESULT.json → ENUMERATION`. Jan/Feb/Mar are `ratio_R` per month; the last three columns are the
**April+May out-of-sample read**, which the hunt never saw.

> Cell definitions here keep the January-frozen **flat-cost** deciles and change only the toll, so
> the cells are the same objects as the flat-toll run and the two are comparable line by line.
> §8.2's Westfall–Young run re-cuts `cost_dec` on the hour-aware cost as well (201 cells > 1 instead
> of 193), which is why `hour×cost_dec 11|0` reads n 167 here and n 180 there. Both are in the JSON.

| # | grouping | cell | n | gross R | cost R | net R | ratio | t_day | d+/d | Jan | Feb | Mar | OOS n | OOS ratio | OOS net |
|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | hour×cost_dec | 14\|0 | 755 | +0.06889 | 0.01812 | +0.05077 | **3.80** | +1.54 | 38/63 | 6.23 | 2.96 | 2.97 | 386 | 2.73 | +0.03084 |
| 2 | hour×cost_dec | 8\|0 | 514 | +0.06447 | 0.02036 | +0.04411 | **3.17** | +1.38 | 41/61 | 4.29 | 2.54 | 2.97 | 206 | 1.06 | +0.00144 |
| 3 | cost_dec×prob_q | 0\|0 | 844 | +0.04717 | 0.02049 | +0.02668 | **2.30** | +0.89 | 31/63 | 3.03 | 4.66 | 0.11 | 396 | 0.89 | −0.00234 |
| 4 | hour×cost_dec | 11\|0 | 167 | +0.11753 | 0.01739 | +0.10014 | **6.76** | **+2.77** | 32/38 | 6.10 | 5.48 | 7.24 | 112 | −0.65 | −0.03523 |
| 5 | symbol×session | GER40\|london | 504 | +0.09088 | 0.03295 | +0.05794 | **2.76** | +2.36 | 39/63 | 2.46 | 1.52 | 5.88 | 232 | −0.21 | −0.03475 |
| 6 | family×cost_dec | regime_transition_break\|0 | 477 | +0.05196 | 0.01858 | +0.03337 | **2.80** | +1.71 | 33/63 | 1.61 | 3.05 | 3.78 | 201 | **1.74** | **+0.01404** |
| 7 | session×cost_dec | london\|0 | 1005 | +0.03496 | 0.02014 | +0.01482 | **1.74** | +0.75 | 38/63 | 1.68 | 3.10 | 0.90 | 436 | 0.72 | −0.00588 |
| 8 | symbol×hour | **GER40\|8** | 213 | +0.12787 | 0.02872 | +0.09915 | **4.45** | **+2.70** | 44/62 | 3.12 | 3.73 | 8.66 | 83 | **1.79** | **+0.02108** |
| 9 | symbol×rdp_dec | US30_cash\|7 | 271 | +0.06284 | 0.01802 | +0.04482 | **3.49** | +1.36 | 35/61 | −1.39 | 7.95 | 3.48 | 131 | **4.75** | **+0.06734** |
| 10 | symbol×family | GER40\|session_open_range_break | 114 | +0.08368 | 0.01274 | +0.07094 | **6.57** | +1.35 | 38/62 | 3.85 | 10.01 | 6.72 | 73 | −1.00 | −0.02357 |
| 11 | symbol×rv_q | US30_cash\|4 | 948 | +0.04616 | 0.02771 | +0.01845 | **1.67** | +0.92 | 36/62 | 0.56 | 2.16 | 1.94 | 493 | **1.34** | **+0.01142** |
| 12 | symbol×hour | **GER40\|14** | 120 | +0.20463 | 0.03303 | +0.17160 | **6.20** | +2.02 | 36/51 | 3.30 | 10.09 | 5.29 | 73 | **3.82** | **+0.07440** |
| 13 | symbol×rdp_dec | XAUUSD\|9 | 487 | +0.03526 | 0.01566 | +0.01960 | **2.25** | +0.70 | 36/60 | 6.95 | −2.80 | 3.32 | 145 | −1.33 | −0.04423 |
| 14 | symbol×rdp_rel_q | US30_cash\|4 | 756 | +0.02539 | 0.01432 | +0.01107 | **1.77** | +0.50 | 31/63 | 4.16 | 2.46 | −0.02 | 340 | **3.43** | **+0.03549** |
| 15 | symbol×rv_q | GER40\|4 | 751 | +0.05188 | 0.03010 | +0.02178 | **1.72** | +1.03 | 33/57 | −0.43 | 2.25 | 2.05 | 507 | **1.19** | **+0.00652** |
| 16 | hour×cost_dec | 18\|0 | 98 | +0.12798 | 0.02151 | +0.10646 | **5.95** | +1.30 | 22/35 | 17.61 | 3.66 | −2.36 | 53 | −4.29 | −0.11897 |
| 17 | family×cost_dec | structural_distance_extreme\|1 | 161 | +0.18057 | 0.04652 | +0.13404 | **3.88** | +1.67 | 24/33 | 3.14 | 2.74 | 4.58 | 53 | **1.65** | **+0.03861** |
| 18 | family×cost_dec | session_open_range_break\|0 | 665 | +0.03351 | 0.02010 | +0.01341 | **1.67** | +0.57 | 31/63 | 1.31 | 3.65 | 0.42 | 344 | **1.16** | **+0.00280** |
| 19 | cost_dec×rdp_rel_q | 1\|2 | 916 | +0.08000 | 0.05498 | +0.02502 | **1.46** | +0.90 | 32/63 | 0.86 | 1.27 | 2.39 | 545 | 0.77 | −0.01270 |
| 20 | symbol×cost_dec | US30_cash\|0 | 969 | +0.02478 | 0.01772 | +0.00707 | **1.40** | +0.34 | 36/63 | 3.07 | 1.40 | 0.27 | 492 | **2.16** | **+0.02248** |
| 21 | symbol×hour | US30_cash\|8 | 187 | +0.14886 | 0.04988 | +0.09898 | **2.98** | +2.38 | 40/57 | 2.31 | 1.52 | 5.62 | 95 | **1.27** | **+0.01832** |
| 22 | rdp_dec×cost_dec | 5\|1 | 609 | +0.08514 | 0.05333 | +0.03181 | **1.60** | +1.02 | 37/63 | 1.45 | 1.42 | 1.96 | 358 | 0.37 | −0.03506 |
| 23 | symbol×hour | NAS100\|16 | 87 | +0.15867 | 0.03270 | +0.12596 | **4.85** | +2.20 | 31/43 | 3.55 | 6.92 | 4.85 | 37 | **1.45** | **+0.01769** |
| 24 | family×rdp_rel_q | regime_transition_break\|4 | 805 | +0.05135 | 0.03638 | +0.01497 | **1.41** | +0.99 | 32/63 | 1.35 | 1.53 | 1.34 | 431 | 0.18 | −0.04113 |
| 25 | symbol×hour | UK100\|8 | 257 | +0.13263 | 0.05809 | +0.07454 | **2.28** | +1.93 | 41/62 | 0.92 | 1.95 | 4.59 | 103 | −1.19 | −0.12189 |
| 26 | family×rdp_dec | regime_transition_break\|9 | 410 | +0.05128 | 0.02866 | +0.02262 | **1.79** | +1.20 | 37/63 | 1.82 | 1.06 | 2.59 | 202 | 0.84 | −0.00517 |
| 27 | rdp_dec×cost_dec | 4\|1 | 291 | +0.12122 | 0.05759 | +0.06363 | **2.10** | +1.27 | 39/61 | 2.20 | 1.98 | 2.15 | 195 | **1.22** | **+0.01345** |
| 28 | symbol×hour | NAS100\|15 | 194 | +0.05765 | 0.02179 | +0.03587 | **2.65** | +0.77 | 40/60 | 3.75 | 0.73 | 3.79 | 67 | **1.15** | **+0.00605** |
| 29 | symbol×hour | XAUUSD\|14 | 153 | +0.14963 | 0.04901 | +0.10062 | **3.05** | +1.88 | 36/54 | 3.69 | 0.39 | 5.70 | 73 | **1.24** | **+0.00971** |
| 30 | symbol×rdp_dec | NAS100\|5 | 201 | +0.12735 | 0.04980 | +0.07756 | **2.56** | +1.26 | 33/57 | 2.26 | 2.15 | 3.40 | 154 | 0.25 | −0.03824 |

**Cells in the 0.5–1.0 band** — the ones h3 would make viable if it cuts the toll — number **439**
at the flat toll and **371** at the hour-aware toll (n ≥ 50). All are enumerated in the JSON. Their
out-of-sample survival rate to ratio > 1 is **12.4 %**, three times the base rate but half the rate
of the > 1 band.

---

## 4. What buys the ratio — and it is NOT mostly cheapness

Decomposition of all 243 flat-toll ratio > 1 cells against the book (gross 0.03834, cost 0.18183):

| | count |
|---|--:|
| median gross vs book | **2.065×** |
| median cost vs book | **0.252×** |
| cells with cost **below** book | 228 / 243 |
| cells with gross **above** book | 218 / 243 |
| **both** | **203** |
| cheap only | 25 |
| high-edge only | 15 |

So the winning cells are simultaneously cheaper *and* higher-gross than the book. That is not what a
pure cost story predicts — and it is exactly what §7's control shows is **not stable**.

**Why it happens at all**: `cost_R = cost_px / risk_distance` and `gross_R` is also denominated in
`risk_distance`, so both scale as 1/stop-width. Trade-level Spearman(gross, cost) is only **+0.0753**,
but the *cell-level* coupling is strong: the top decile of cells by hunt gross carries mean cost
**0.507** and books mean OOS net **−0.475**. **Sorting cells by gross sorts them by stop tightness.**

---

## 5. The affordability frontier — selecting on cost does NOT produce a paying book

The break-even broker-true cost is the pooled gross edge, **0.038342 R**. **16.62 %** of the book
sits below it. Sweeping the cutoff (flat toll, 3 months):

| cut (R) | n | share | gross | cost | net | ratio | t_day | d+/d |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 0.0050 | 118 | 0.003 | 0.02768 | 0.00380 | **+0.02388** | 7.28 | +0.58 | 16/31 |
| 0.0075 | 376 | 0.009 | 0.03526 | 0.00554 | **+0.02971** | 6.36 | +2.00 | 30/48 |
| 0.0100 | 819 | 0.019 | 0.01731 | 0.00729 | +0.01002 | 2.38 | +0.54 | 35/60 |
| 0.0150 | 1,798 | 0.041 | 0.01138 | 0.01018 | +0.00120 | 1.12 | +0.08 | 33/63 |
| 0.0200 | 2,963 | 0.068 | 0.01570 | 0.01307 | +0.00263 | 1.20 | +0.22 | 35/63 |
| **0.0383** (break-even) | 7,261 | 0.166 | 0.01185 | 0.02250 | **−0.01064** | 0.53 | −1.16 | 30/63 |
| 0.1000 | 19,724 | 0.451 | 0.01387 | 0.05082 | −0.03695 | 0.27 | −5.89 | 15/63 |
| all | 43,755 | 1.000 | 0.03834 | 0.18183 | −0.14349 | 0.21 | −23.79 | 0/63 |

**The trap is visible in the `gross` column.** The book's gross is +0.03834; below any cost cutoff it
collapses to +0.011…+0.016. Cheap trades in R terms are wide-stop trades, and a wide stop shrinks the
gross by the same factor it shrinks the cost. By cost decile the ratio is **0.512 / 0.408 / 0.055 /
0.313 / 0.087 / 0.118 / 0.224 / 0.234 / 0.250 / 0.190** — best at the cheap end and never near 1.

**And the purest cost rule of all measures exactly zero.** "Trade this instrument only in the hours
when its own tick-measured quoted spread is at or below its own median" uses **no outcome
information whatsoever** and therefore carries **no selection bill**:

| rule (COST-ONLY, hour-aware toll) | n | gross | cost | net | ratio | t_day | holdout net |
|---|--:|--:|--:|--:|--:|--:|--:|
| spread_hour ≤ 1.30 × own median | 39,285 | 0.03545 | 0.18472 | −0.14927 | 0.192 | −25.3 | −0.13688 |
| **spread_hour ≤ 1.00 × own median** | **30,149** | 0.03814 | 0.17941 | **−0.14128** | **0.213** | −23.5 | −0.13044 |
| spread_hour ≤ 0.90 × own median | 2,200 | 0.03669 | 0.12356 | −0.08687 | 0.297 | −5.3 | −0.08819 |
| cost_true_hour ≤ 0.02 | 2,757 | 0.01404 | 0.01308 | +0.00095 | 1.073 | +0.07 | −0.00564 |
| cost_true_hour ≤ 0.0383 | 6,839 | 0.01431 | 0.02262 | −0.00830 | 0.633 | −0.86 | −0.01199 |
| index cluster × cheap hour | 6,483 | 0.03900 | 0.07060 | −0.03160 | 0.552 | −2.81 | −0.01323 |

**The whole book's ratio is 0.213 and the cheap-hour book's ratio is 0.213.** Restricting to the
30,149 trades that happen in a cheap hour changes the answer by nothing at all.

---

## 6. Split-half, month persistence, and the pre-specified mechanism test

**Seven sub-samples** were applied to every ratio > 1 cell: Jan, Feb, Mar, Jan calendar halves
(01–15 / 16–31) and Jan parity halves (even/odd trading-day index).

| toll | ratio > 1 (n ≥ 50) | > 1 in all 3 months | in both calendar halves | in both parity halves | **all seven** |
|---|--:|--:|--:|--:|--:|
| flat | 243 | 59 | 50 | 60 | **12** |
| hour-aware | 193 | — | — | — | **8** |

### 6.1 One mechanism was declared before it was read, and it failed out of sample

The grid surfaced `GER40|8`. 08:00 UTC is the **Xetra cash open** (09:00 CET). If that is a mechanism
and not a grid artifact it must appear on the other index instruments, so h5 declared six cells —
each index at *its own* cash open — in `h5_05_robust.py` before reading them:

All figures hour-aware toll. Hunt window = Jan+Feb+Mar; OOS = Apr+May.

| symbol | own open (UTC) | n | net R | ratio | t_day | Jan/Feb/Mar | OOS n | **OOS net** | **OOS ratio** |
|---|--:|--:|--:|--:|--:|---|--:|--:|--:|
| GER40 | 08 | 213 | +0.09915 | 4.45 | +2.70 | 3.12 / 3.73 / 8.66 | 83 | **+0.02108** | 1.79 |
| UK100 | 08 | 257 | +0.07454 | 2.28 | +1.93 | 0.92 / 1.95 / 4.59 | 103 | **−0.12189** | −1.19 |
| SPX500 | 14 | 174 | +0.02058 | 1.29 | +0.44 | 0.77 / 3.79 / −0.36 | 109 | −0.03321 | 0.53 |
| US30_cash | 14 | 215 | −0.00142 | 0.95 | −0.03 | 2.79 / −1.54 / 0.01 | 111 | +0.05222 | 3.08 |
| NAS100 | 14 | 190 | −0.00914 | 0.67 | −0.22 | −0.89 / 1.37 / 2.67 | 138 | −0.02971 | −0.15 |
| JP225 | 00 | 165 | −0.06188 | −0.05 | −1.22 | −1.24 / −0.21 / 2.27 | 115 | −0.02599 | 0.43 |
| **pooled** | | **1,214** | **+0.02603** | **1.58** | **+1.55** | 0.86 / 1.62 / 2.88 | 659 | **−0.02385** | **0.42** |
| pooled **excluding GER40** | | 1,001 | +0.01048 | 1.22 | +0.53 | 0.58 / 1.32 / 2.26 | 576 | **−0.03033** | **0.30** |

Three of six were positive on the hunt window and the pooled cell cleared 1. Out of sample the
pooled cell books **−0.02385 (ratio 0.42)**, only GER40 and US30_cash stay positive, and the two
that carried the hunt-window result (GER40 h08 and UK100 h08) **split**: +0.021 and −0.122.

On the hunt window the EU pair at h08 looked strong — n 470, net **+0.08569**, ratio **2.91**,
t_day **+3.18**, 41/63 days, and sharply localised (h07 ratio 0.92, h09 ratio 0.47).
**On April+May it books −0.05809 (ratio −0.36, t_day −0.98) and the h07 "control" turns positive
(+0.02884).** The localisation reversed. The mechanism is refuted as stated.

---

## 7. April + May — the read that decides the lane

Every one of the 4,130 cells was carried into two months the hunt never saw, definitions frozen.

| hunt-window bucket | cells | median OOS ratio | fraction still > 1 |
|---|--:|--:|--:|
| ratio ≤ 0.5 | 3,386 | 0.138 | **2.42 %** |
| 0.5 – 1.0 | 355 | 0.219 | **12.39 %** |
| 1.0 – 1.5 | 107 | 0.385 | **22.43 %** |
| 1.5 – 2.5 | 52 | 0.715 | **28.85 %** |
| **> 2.5** | 22 | **1.148** | **54.55 %** |
| **all cells** | 3,922 | — | **4.51 %** |

**Of the 181 hunt cells with ratio > 1 that have an OOS read, 28.18 % are still > 1 — 6.2× the
4.51 % base rate, and the dose-response is monotone.** 51 cells are > 1 in both windows.
Spearman(hunt ratio, OOS ratio) = **0.146**; Spearman(hunt net, OOS net) = **0.777**.

### 7.0 THE CELLS THAT TRAVELLED — ratio > 1 in BOTH windows, top 16 of 46 (OOS n ≥ 50)

This is the forward-looking list. It is reported without multiplicity self-censorship, as the lane
brief requires; §8 prices the bill and no cell on it clears WY p ≤ 0.20. Full 51 in
`h5_RESULT.json → out_of_sample.cells_gt1_in_BOTH`.

| grouping | cell | hunt n | hunt ratio | hunt net | OOS n | **OOS ratio** | OOS net | OOS t_day |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| family×rdp_dec | regime_transition_break\|8 | 211 | 1.36 | +0.01107 | 84 | **3.17** | +0.06965 | +1.78 |
| symbol×rdp_dec | UK100\|8 | 241 | 1.00 | +0.00010 | 154 | **2.74** | +0.06553 | +1.64 |
| symbol×cost_dec | JP225\|4 | 126 | 1.21 | +0.02469 | 90 | **1.73** | +0.08765 | +1.62 |
| symbol×rdp_dec | US30_cash\|7 | 271 | 3.49 | +0.04482 | 131 | **4.75** | +0.06734 | +1.47 |
| symbol×hour | GER40\|7 | 129 | 1.18 | +0.01064 | 90 | **4.07** | +0.08139 | +1.45 |
| symbol×rdp_rel_q | US30_cash\|4 | 756 | 1.77 | +0.01107 | 340 | **3.43** | +0.03549 | +1.44 |
| symbol×hour | NAS100\|12 | 83 | 1.57 | +0.02959 | 63 | **2.64** | +0.08513 | +1.30 |
| family×session | regime_transition_break\|ny | 236 | 1.28 | +0.00756 | 104 | **2.75** | +0.05673 | +1.28 |
| symbol×family | US30_cash\|session_open_range_break | 105 | 1.21 | +0.00449 | 53 | **5.84** | +0.08299 | +1.08 |
| symbol×cost_dec | US30_cash\|0 | 969 | 1.40 | +0.00707 | 492 | **2.16** | +0.02248 | +1.02 |
| hour×cost_dec | 10\|0 | 159 | 1.08 | +0.00176 | 74 | **3.20** | +0.04524 | +0.98 |
| **symbol×hour** | **GER40\|14** | 120 | 6.20 | +0.17160 | 73 | **3.82** | +0.07440 | +0.97 |
| symbol×dow | US30_cash\|Tue | 386 | 1.05 | +0.00278 | 240 | **1.66** | +0.03616 | +0.93 |
| symbol×hour | SPX500\|13 | 107 | 1.03 | +0.00272 | 87 | **2.20** | +0.09186 | +0.89 |
| symbol×rv_q | NAS100\|2 | 195 | 1.13 | +0.00896 | 202 | **1.58** | +0.04388 | +0.87 |
| family×rv_q | regime_transition_break\|4 | 395 | 1.62 | +0.01491 | 191 | **1.84** | +0.02864 | +0.87 |

**`US30_cash` appears five times and `regime_transition_break` three times on this list** — the two
recurring names in the surviving set, and neither was in the swarm's headline. `US30_cash` is the
**cheapest instrument in the book** on median cost bps (0.4027, against GER40's 0.5012) and the
**3rd most cost-stable of 24** hunt→OOS (cost ×1.0673). Which is F4 again, in a different costume:
what travels is the cheap instrument, not the edge. The highest OOS day-clustered t on the entire
list is **+1.78**.

### 7.1 THE CONTROL — the 6.2× lift is the fee schedule, not an edge

Two explanations, opposite consequences: (a) the edge persists, or (b) the cost persists and a small
denominator lifts the ratio by itself. Three tests separate them.

**T1 — rank persistence, hunt → OOS, over 3,922 cells:**

| quantity | Spearman |
|---|--:|
| **cell cost_R** | **0.9479** |
| cell gross_R | 0.2991 |
| cell ratio_R | 0.1460 |
| cell net_R | 0.7774 |

**T2 — within each decile of cell cost** (cost held fixed by construction) the hunt ratio still
predicts, but weakly: in the cheapest decile `P(OOS>1 | hunt>1)` is **0.374** against
`P(OOS>1 | hunt≤1)` = **0.230** — a 1.6× lift, not the 6.2× the raw comparison showed. In deciles
3, 5, 6, 7, 8, 9 the lift is zero or undefined (no hunt > 1 cells survive at all).

**T3 — the cost-blind gross hunt.** Top decile of cells by hunt gross: hunt gross **0.1726** →
OOS gross **0.0999**, mean cost **0.507**, **OOS net −0.4746**. Bottom decile: hunt gross −0.0517 →
OOS gross **+0.0167**, OOS net −0.1617. Ranking cells on gross is ranking them on stop tightness.

**T4 — the same question with no cells at all, across the 24 instruments:**

| quantity | Spearman(hunt, OOS) across 24 symbols |
|---|--:|
| instrument cost_R | **0.8261** |
| instrument ratio_R | 0.6739 |
| **instrument gross_R** | **0.0243** |

**An instrument's gross edge in January–March tells you essentially nothing about its gross edge in
April–May.** GER40 ranks 1st of 24 on hunt gross (0.06465) and mid-pack on OOS gross (0.02664).
Its ratio goes 0.790 → 0.363. **The 12.1× cost dispersion the swarm pointed at is real and it is
stable; the edge that would have to exploit it is not.**

---

## 8. The multiplicity price — paid in full, twice

### 8.1 Count placebo (flat toll, 30 replicates each)

Permute `K5_TRAIL025` within blocks, keep everything else, re-run the identical 78-grouping grid.

| null | what it destroys | ratio>1: null mean (p95, max) | **real** | emp p | survive-all-7: null mean | **real** | emp p |
|---|---|--:|--:|--:|--:|--:|--:|
| **P1** within (symbol, month) | everything within symbol, **including the mechanical gross↔cost coupling** | 372.5 (417, 424) | 243 | 1.000 | 28.4 | 12 | 1.000 |
| **P2** within (symbol, month, within-symbol cost quintile) | cell structure only; coupling preserved | 218.5 (238, 245) | 243 | **0.097** | 10.1 | 12 | 0.258 |
| **P3** within (month, global cost decile) | cell structure **and instrument identity** | 155.3 (176, 178) | 243 | **0.032** | 4.9 | 12 | 0.065 |

Read P1 first, because it is the diagnostic: a null that severs the gross↔cost coupling produces
**more** affordable cells than reality does (372 vs 243). The grid manufactures ratio > 1 cells for
free whenever cheap cells are allowed a book-average gross. P2 — the honest null for the sub-symbol
axes — says the real yield is at the 90th percentile of noise. P3 says the only structure that beats
noise is **instrument identity**, and §7.1-T4 establishes that instrument identity is cost.

### 8.2 Westfall–Young maxT (hour-aware toll, 40 replicates each null)

The count is not the right statistic; the **maximum** is. For each replicate, the largest
day-clustered t on net R over all 4,130 cells:

| | real | P2 null max | P3 null max |
|---|--:|--:|--:|
| **max day-clustered t over the grid** | **2.725** | mean 2.745 · p50 2.80 · p95 3.258 · max 3.427 | mean 2.80 · p50 2.576 · p95 4.134 · max 4.607 |
| max (ratio−1)·n | 1,787.8 | mean 1,347 · p95 1,981 | mean 1,499 · p95 2,228 |
| **cells at WY p ≤ 0.05 / 0.10 / 0.20** | **0 / 0 / 0** | | |

**The best cell in the entire grid is less extreme than the grid maximum noise routinely produces.**
Best WY p-values: `hour×cost_dec 11|0` **0.537**, `GER40|8` **0.561**, `US30_cash|8` 0.805,
`GER40|london` 0.805, `NAS100|16` 0.927.

---

## 9. The leads, stressed every way the substrate allows

Five months, hour-aware toll, plus all **66 (entry-delay k ∈ 11) × (exit contract ∈ 6)** arms
`e_build_atmkt.py` wrote — a cell whose sign lives in one (k, contract) is a fit.

| lead | n | net R | ratio | t_day | Jan/Feb/Mar/**Apr/May** ratio | toll ×2.0 | best-day share | drop best 3 days | 10 % trim | arms net-positive | tr/day | net R/day |
|---|--:|--:|--:|--:|---|--:|--:|--:|--:|--:|--:|--:|
| **GER40 @ h14** | 193 | **+0.13483** | **5.42** | +2.25 | 3.30 / 10.09 / 5.29 / **5.15 / 1.51** | **+0.10430** | 0.293 | +0.06606 | +0.12327 | **51/66** | 1.84 | **+0.248** |
| GER40 @ h08 | 296 | +0.07726 | 3.75 | +2.32 | 3.12 / 3.73 / 8.66 / **5.09 / −1.86** | +0.04912 | 0.144 | +0.04998 | +0.10693 | 43/66 | 2.82 | +0.218 |
| hour 14 × cost_dec 0 | 1,141 | +0.04402 | 3.44 | +1.70 | 6.23 / 2.96 / 2.97 / **5.79 / 0.26** | +0.02601 | 0.184 | +0.02257 | +0.06634 | 52/66 | 10.87 | **+0.478** |
| GER40 @ h13 (neighbour) | 85 | +0.03800 | 2.26 | +0.64 | −2.99 / 0.94 / 5.66 / 1.70 / 4.15 | +0.00775 | 0.551 | −0.01152 | +0.05624 | 35/66 | 0.81 | +0.031 |
| GER40 @ h15 (neighbour) | 211 | **−0.04620** | −0.62 | −1.03 | 0.29 / −7.56 / 1.90 / −0.24 / 3.24 | −0.07468 | — | −0.08661 | −0.04949 | 13/66 | 2.01 | −0.093 |
| cost_true_hour ≤ 0.02 | 4,008 | +0.00857 | 1.65 | +0.85 | 2.89 / 0.27 / 0.72 / 1.90 / 4.02 | **−0.00460** | 0.317 | +0.00170 | +0.03820 | **7/66** | 38.17 | +0.327 |
| **WHOLE BOOK** | 69,480 | **−0.19188** | 0.17 | −30.28 | 0.17 / 0.17 / 0.18 / 0.14 / 0.17 | −0.42208 | 0.002 | −0.19585 | −0.15421 | **0/66** | 661.7 | −126.97 |

**`GER40 @ UTC h14` is the one cell in this lane with a five-month positive record.** It is
distributed across all five generating families that reach it (`session_open_range_break` ratio 15.6,
`displacement_continuation` 7.3, `cross_asset_lead_lag` 5.7, `liquidity_sweep_reclaim` 4.8,
`structural_distance_extreme` 1.2) and both sides (LONG +0.138, SHORT +0.131), survives a doubled
toll, survives dropping its best three days, and is net-positive in **51 of 66** contract arms.

**Its three disqualifying caveats, stated plainly.** (1) n = **193** trades in five months — 1.84 a
day. (2) It is **1 of 4,130 looks**, WY p ≈ 1, and its day-clustered t of 2.02–2.25 is below the
grid's own noise maximum. (3) Its immediate neighbour hour h15 is **−0.046** and h13 is +0.038 on
n = 85 with a 0.551 best-day share — a real hourly mechanism would not be a one-hour spike flanked by
a negative. **It is a lead for a capture, not a result.**

`cost_true_hour ≤ 0.02` is the opposite shape: 38 trades a day and +0.327 R/day, but only **7 of 66**
contract arms are net-positive and it dies at a 1.5× toll. Its positive sign lives in the exact
(k = 5, TRAIL025) contract the swarm chose.

---

## 10. Findings

**h5-F1 [MEASURED].** Cells with broker-true edge/cost > 1 **exist and are numerous**: 243 of 4,130
at n ≥ 50 on the flat toll, **193** on the honest hour-aware toll, 682 / 564 above 0.5. All are
enumerated in `h5_RESULT.json → ENUMERATION`. The lane's premise is confirmed at the descriptive level.

**h5-F2 [MEASURED — corrects the synthesis].** *"GER40 is the only symbol net-positive at broker
truth"* is an artifact of charging a **flat** per-symbol spread. GER40's trades sit in hours whose
real quoted spread is **1.755×** its own median; at the hour-aware toll GER40 books **−0.01714**
(3 M) and **−0.04666** (Apr+May). UK100's cost rises **2.666×**. **No instrument of 24 is
net-positive across five months.**

**h5-F3 [MEASURED].** The hunt's cells carry genuine out-of-sample information: **28.18 %** of
ratio > 1 cells stay > 1 on April+May against a **4.51 %** base rate (**6.2×**), monotone across
buckets (2.42 → 12.39 → 22.43 → 28.85 → **54.55 %**).

**h5-F4 [MEASURED — this is the finding that decides the lane].** That information is **the fee
schedule, not an edge.** Rank persistence hunt→OOS: cell **cost 0.9479** vs cell gross 0.2991;
across the 24 instruments, **cost 0.8261 vs gross 0.0243**. Holding cost fixed inside its decile
collapses the lift from 6.2× to 1.6×. **Affordability selection re-discovers which symbols are
cheap; it does not locate edge, because instrument-level edge does not persist at all.**

**h5-F5 [MEASURED].** **No cell survives the multiplicity bill.** Real max day-clustered t over the
grid = **2.725**; the P2 null's *maximum* averages **2.745** and the P3 null's **2.80**.
**Zero cells at WY p ≤ 0.20.** The ratio > 1 *count* is marginally above null (emp p 0.097 under P2,
0.032 under P3), and P1 shows the grid manufactures 372 such cells from pure noise when the
gross↔cost coupling is severed — i.e. the count criterion has a false-discovery rate near 1.

**h5-F6 [MEASURED].** **Cost selection alone cannot build a book.** The purest cost rule available —
"trade only in hours where this instrument's own tick-measured spread is at or below its own median",
which contains zero outcome information — moves the book's ratio from 0.213 to **0.213** on 30,149
trades. Every cost cutoff is at best break-even, negative on the Feb+Mar holdout, and contract-fragile
(7 of 66 arms).

**h5-F7 [MEASURED].** **The gross edge is not flat in cost, and that is why the ratio never opens
up.** By cost decile, gross runs 0.0102 → 0.1391 while cost runs 0.0200 → 0.7311: both are
denominated in the stop width, so selecting cheap trades selects wide stops and shrinks the numerator
by the same factor. The ratio by decile is 0.512 / 0.408 / 0.055 / 0.313 / 0.087 / 0.118 / 0.224 /
0.234 / 0.250 / 0.190 — best at the cheap end and never near 1.

**h5-F8 [MEASURED].** **The index-cash-open mechanism is refuted.** Declared before reading (six
cells, one per index at its own cash open), it measured pooled ratio **1.58** / t_day +1.55 on the
hunt window and **0.42 / t_day −0.96** on April+May. The EU pair at h08 went **+0.08569 → −0.05809**
and its own h07 control went **−0.01115 → +0.02884**. The sharp localisation reversed.

**h5-F9 [MEASURED — the one lead worth a capture].** `GER40 @ UTC h14` is net-positive in **all five
months** (ratio 3.30 / 10.09 / 5.29 / 5.15 / 1.51), n 193, net **+0.13483 R/trade**, ratio **5.42**,
survives a doubled toll, survives dropping its best three days, spread across five families and both
sides, and **51 of 66** contract arms are net-positive. It is 1 of 4,130 looks with WY p ≈ 1, it is
1.84 trades a day, and the adjacent hour h15 is **−0.046**. Report it; do not size it.

**h5-F10 [MEASURED].** **Zero of 66 (entry delay × exit contract) arms makes the five-month
live-expressible book net-positive.** The book is gross +0.03831 / toll 0.23020 / net **−0.19188**
over 69,480 trades, and the best arm of the 66 is −0.18423.

**h5-F11 [MEASURED — for h3].** The **439** flat-toll cells (371 hour-aware) sitting in the 0.5–1.0
band at n ≥ 50 are the population h3's toll reduction would move above 1. Their OOS survival to
ratio > 1 is **12.4 %** against the 4.5 % base rate. If h3 halves the toll, this band inherits the
same cost-vs-edge asymmetry F4 measured, so the honest prior on it is *cheaper cells, not more edge*.

---

## 11. What this lane tells the owner

The swarm's closing observation was: *if edge is roughly flat across instruments and cost varies
twelvefold, there may be cells where edge/cost is already above 1.* Both halves of the premise were
checked and only one holds.

- **Cost really does vary twelvefold, and it is stable** — rank correlation 0.83 across instruments
  from one 3-month window to the next. That part of the estate's picture is solid.
- **Edge is not flat, and it is not stable.** Instrument-level gross edge has rank correlation
  **0.024** across windows. The +0.038 R/trade pooled gross is a real aggregate that does not
  decompose into instruments that keep their places.

The consequence is that **affordability is not a selectable coordinate.** You can enumerate hundreds
of cells where today's edge exceeds today's toll, and 72 % of them stop paying in the next two months,
and the 28 % that keep paying are the ones that were cheap rather than the ones that had edge.

**Do not build an instrument-selection or cell-selection layer on this evidence.** The two things
that *would* change the answer are the ones this lane cannot supply: a toll that is genuinely 4–10×
smaller (h3's question), or a **larger** edge — and §4's decomposition says the estate has been
mining the edge's denominator, not its numerator.

---

## 12. Scripts and artifacts

| script | what it does | output |
|---|---|---|
| `h5_00_build.py` | joins the three at-market months, adds ex-ante 60-min realised vol, January-frozen normalisers and deciles | `h5_SUBSTRATE_V1.jsonl.gz`, `h5_SUBSTRATE_V1_BUILD.json` |
| `h5_lib.py` | one cell's full arithmetic; both ratios; day-clustered t | — |
| `h5_01_cells.py` | 78 groupings × 4,664 cells, seven sub-samples, census | `h5_CELLS_V1.json`, `h5_CELLS_CENSUS_V1.json` |
| `h5_02_costcut.py` | affordability frontier, cost sweeps, cost-decile table, ratio decomposition | `h5_COSTCUT_V1.json` |
| `h5_03_placebo.py` | count placebo, three nulls, 30 replicates each (flat toll) | `h5_PLACEBO_V1.json` |
| `h5_04_rules.py` | per-symbol table, thirteen pre-declared rules, GER40 dossier | `h5_RULES_V1.json` |
| `h5_05_robust.py` | concentration / trim / drop-best-days; the pre-specified index-open test | `h5_ROBUST_V1.json` |
| `h5_06_hourcost.py` | the whole hunt re-run on the hour-aware toll | `h5_HOURCOST_V1.json`, `h5_CELLS_HOUR_V1.json`, `h5_SUBSTRATE_V2.jsonl.gz` |
| `h5_07_maxstat.py` | Westfall–Young maxT, 40 replicates × 2 nulls, hour-aware toll | `h5_MAXSTAT_V1.json` |
| `h5_08_declared.py` | cost-only cheap-hour filter; 220-grouping triple scan | `h5_DECLARED_V1.json` |
| `h5_09_aprmay.py` | builds the 5-month substrate, reads every lead on Apr+May | `h5_APRMAY_V1.json`, `h5_SUBSTRATE_5M.jsonl.gz` |
| `h5_10_oos_all.py` | carries all 4,130 cells into Apr+May; survival table | `h5_OOS_ALL_V1.json` |
| `h5_11_control.py` | T1–T4: does EDGE persist or does COST persist | `h5_CONTROL_V1.json` |
| `h5_12_leads.py` | the leads under 66 contract arms, toll stress, concentration | `h5_LEADS_V1.json` |
| `h5_13_receipt.py` | assembles the full enumeration into the receipt | `h5_RESULT.json` |

April and May cohorts built with the unmodified `e_build_atmkt.py`:
`e_APR_ATMKT_V1.jsonl.gz` (13,837), `e_MAY_ATMKT_V1.jsonl.gz` (11,888).

No sealed replay was run, no VPS was touched, no broker-capable script was executed, nothing was
committed.
