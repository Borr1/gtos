# Lane l2 — the full stops. Were they right?

**Answer: yes, and that is the finding.** The stop is not what kills this system. Removing it
entirely — no stop at all — changes the price-space expectancy by **+0.00264 R/trade**. Moving it
over a **12× range** (0.25× to 3.0× the structural risk distance) changes it by **nothing that
survives a bootstrap CI**. Every dynamic variant (break-even at five levels, trailing at five
levels, partial scale-outs, four time stops) moves it by **≤ +0.047 R/trade**, and the best of them
is a 0.25R trail. The 15,057 stop-outs are not a defect being suffered; they are the honest
resolution of a process that has **no drift after the fill**.

Where the money actually goes is measured here too, because the same substrate localises it: for a
market-order entry (`born_at_limit`, n=14,911, zero fill conditioning) the mean signed R is
**−0.0028 at the decision instant**, **−0.0766 twenty minutes later, and flat thereafter** — while
the charged cost is **0.6652 R/trade** (frozen) or ~**0.176 R/trade** at the measured 7.3×
spread over-charge. **The cost is 2.3× to 8.7× the entire directional deficit.** The deficit is not
in the exit.

Everything below is measured on the January 2026 true-UTC diagnostic pool via the wave-0 working
set. Scripts and JSON are listed in §10.

---

## 0. Population discipline — read before comparing any number here to the brief

| rule | value |
|---|---|
| born-state anchor | `mkt_r_prev_close` (close of the M1 bar stamped decision−1 min; bars are OPEN-stamped — w0-capture) |
| excluded | `born_past_stop` — the stop price was already breached at the decision instant. **3,516 rows, never takeable** |
| fill | resting limit at `entry_price`; the walk starts at the first bar with `adv ≤ 0` |
| tie | stop wins same-bar ties (M1 OHLC carries no intrabar ordering) |
| horizon | hard 120 M1 bar / 2 h cap on every path |
| **honest population** | **23,901** |

**The brief's "15,057 full stops" is the fill-blind count over all 27,658 rows.** On the honest
population the stop count is **12,341 (51.634 %)**; including untakeable rows it is 15,852. Both are
reported. Born census: `born_at_limit` 14,911 · `born_resting` 7,949 · `born_marketable` 1,265 ·
`born_past_stop` 3,516 · unknown 17.

Honest first-touch book at k=1: **gross −0.12780 R/trade**, win 35.647 %, stop 51.634 %,
target 15.518 %, mark-at-horizon 32.848 %.

---

## 1. Q1 — stopped, then reversed

Of **12,341** honest stops, inside the same 2 h window:

| | n | share |
|---|---:|---:|
| later reached the 2R target | **2,768** | **22.429 %** |
| later got back to break-even | 6,925 | 56.114 % |
| MFE after the stop ≥ +1R | — | 34.885 % |
| MFE after the stop ≥ +2R | — | 22.660 % |
| MFE after the stop ≥ 0R | — | 56.365 % |

Timing, bars after the stop bar: median **37**, p25 17, p75 62, p90 85, mean 41.66. Bars still
remaining in the path after the stop: median 90, mean 80.57. MFE after the stop: mean +1.2496,
median +0.2278, p75 +1.7949, p90 +4.3167.

**And it is worth nothing.** The no-stop counterfactual on exactly those rows — target if reached,
else mark at the 2 h wall:

| | value |
|---|---:|
| mean R with the stop | −1.00000 |
| **mean R with NO stop** | **−0.99732** |
| forgone per stopped trade | **+0.00268** |
| forgone per population trade | +0.00138 |
| mean mark at the wall on stopped rows | −0.94422 |

The 22.4 % that revert are paid for exactly by the 77.6 % that do not: reached-target cohort
n=2,768 mean **+2.0064**; never-target cohort n=9,573 mean **−1.8658**, median −1.2221. The
never-target tail is what the stop is buying: p25 −1.955, p10 −3.834, p05 −5.664, p01 −11.262,
min **−135.213**; 24.35 % of no-stop outcomes are ≤ −2R, 14.93 % ≤ −3R, 6.27 % ≤ −5R.

**The −1R stop is fairly priced by the market to three decimal places.** On all rows including the
untakeable ones the reversal share is 18.174 % of 15,852.

---

## 2. Q2 — how close did the winners come to dying?

n = **3,709** honest target-winners. The MAE-before-target histogram is **flat** — there is no
cluster the stop is sitting on top of, and no cluster it is safely clear of.

| MAE band | n | % of winners |
|---|---:|---:|
| [−0.1, 0.0) | 367 | 9.895 |
| [−0.2, −0.1) | 464 | 12.510 |
| [−0.3, −0.2) | 459 | 12.375 |
| [−0.4, −0.3) | 397 | 10.704 |
| [−0.5, −0.4) | 438 | 11.809 |
| [−0.6, −0.5) | 395 | 10.650 |
| [−0.7, −0.6) | 308 | 8.304 |
| [−0.8, −0.7) | 334 | 9.005 |
| [−0.9, −0.8) | 244 | 6.579 |
| [−1.0, −0.9) | 303 | 8.169 |

mean −0.45823 · median −0.43720 · p10 −0.879 · p25 −0.6864 · p75 −0.2231 · p90 −0.101 · min −0.9998.
Share worse than −0.5R **42.707 %**; worse than −0.75R **18.603 %**; **14.748 % of winners came
within 0.2R of the stop** and 8.169 % within 0.1R. The other winner class — 4,811 rows marked
positive at the 2 h wall — has mean MAE −0.40561, median −0.3616, 34.774 % worse than −0.5R.

Because the density is flat, tightening removes winners at a near-constant ≈10 % per 0.1R of stop
distance. There is no sweet spot to find.

---

## 3. Q3 — the stop-distance sweep, done in price and converted once

The stop is moved to `k × risk_distance` in **price**. Since every `*_r` column is normalised by the
original risk distance `d`, the new stop is `adv ≤ −k` and the realised R in the **new** risk unit is
`R_old / k` (position size scales 1/k to hold cash risk constant). `mean_r_oldunit` is the
price-space expectancy — **the only quantity a stop change can create or destroy**.

### 3a. Convention A — structural price target held fixed

| k | mean R (new unit) | **mean R (price space)** | win % | stop % | target % | mark % | L→W | W→L |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | −0.34220 | **−0.08555** | 11.702 | 87.16 | 4.48 | 8.36 | 0 | 5,723 |
| 0.40 | −0.28351 | −0.11341 | 17.987 | 79.06 | 7.04 | 13.90 | 0 | 4,221 |
| 0.50 | −0.23821 | −0.11911 | 22.020 | 73.60 | 8.89 | 17.51 | 0 | 3,257 |
| 0.60 | −0.20248 | −0.12149 | 25.656 | 68.22 | 10.54 | 21.24 | 0 | 2,388 |
| 0.70 | −0.18485 | −0.12940 | 28.467 | 63.74 | 11.83 | 24.43 | 0 | 1,716 |
| 0.75 | −0.16882 | −0.12662 | 30.003 | 61.42 | 12.63 | 25.95 | 0 | 1,349 |
| 0.80 | −0.16186 | −0.12949 | 31.166 | 59.39 | 13.23 | 27.38 | 0 | 1,071 |
| 0.90 | −0.14915 | −0.13424 | 33.384 | 55.48 | 14.25 | 30.27 | 0 | 541 |
| **1.00** | **−0.12780** | **−0.12780** | 35.647 | 51.63 | 15.52 | 32.85 | 0 | 0 |
| 1.10 | −0.11273 | −0.12401 | 37.551 | 48.14 | 16.57 | 35.29 | 455 | 0 |
| 1.25 | −0.10100 | −0.12626 | 39.634 | 43.59 | 17.80 | 38.61 | 953 | 0 |
| 1.50 | −0.08350 | −0.12525 | 42.484 | 37.10 | 19.49 | 43.41 | 1,634 | 0 |
| 1.75 | −0.07348 | −0.12859 | 44.538 | 32.10 | 20.82 | 47.08 | 2,125 | 0 |
| 2.00 | −0.06367 | −0.12734 | 46.136 | 27.75 | 21.93 | 50.32 | 2,507 | 0 |
| 2.50 | −0.05163 | −0.12909 | 48.241 | 21.07 | 23.36 | 55.58 | 3,010 | 0 |
| 3.00 | −0.04210 | **−0.12630** | 49.655 | 16.48 | 24.40 | 59.12 | 3,348 | 0 |

**The price-space column is flat.** From k=0.75 to k=3.00 — a 4× range — it moves between −0.12401
and −0.12949, a spread of 0.0055 R. The entire apparent improvement in the first column is the
1/k denominator.

### 3b. Bootstrap, 400 resamples, seed 20260806 — price-space delta vs k=1

| k | delta | 95 % CI |
|---:|---:|---|
| 0.25 | +0.04225 | [+0.02944, +0.05433] ✓ |
| 0.40 | +0.01440 | [+0.00130, +0.02515] ✓ |
| 0.50 | +0.00870 | [−0.00165, +0.01808] |
| 0.60 | +0.00631 | [−0.00250, +0.01532] |
| 0.70 | −0.00160 | [−0.00993, +0.00587] |
| 0.75 | +0.00119 | [−0.00563, +0.00791] |
| 0.80 | −0.00169 | [−0.00829, +0.00439] |
| 0.90 | −0.00643 | [−0.01127, −0.00104] ✓ |
| 1.10 | +0.00379 | [−0.00111, +0.00807] |
| 1.25 | +0.00155 | [−0.00434, +0.00811] |
| 1.50 | +0.00255 | [−0.00623, +0.01096] |
| 1.75 | −0.00079 | [−0.01177, +0.00995] |
| 2.00 | +0.00046 | [−0.01270, +0.01230] |
| 2.50 | −0.00128 | [−0.01501, +0.01421] |
| 3.00 | +0.00150 | [−0.01477, +0.01586] |

Only the two tightest stops (k ≤ 0.4) and k=0.9 exclude zero, and the k≤0.4 effect is trivially
mechanical (a stop that fires almost always truncates the price-space loss). **Across the whole
region a trader would actually consider, the stop distance carries no information.**

### 3c. On de-duplicated setups the sign flips — and it matters

W0-F1: 24.39 % of the pool is the same setup re-emitted every 15 min. On first-emission-only rows:

| k | price-space | delta vs k=1 | 95 % CI |
|---:|---:|---:|---|
| 0.50 | −0.114106 | +0.016634 | [+0.00472, +0.02734] ✓ |
| 0.75 | −0.122398 | +0.008341 | [+0.00080, +0.01662] ✓ |
| 1.00 | −0.130739 | 0 | — |
| 1.50 | −0.136860 | −0.006121 | [−0.01625, +0.00376] |
| 2.00 | −0.149018 | −0.018279 | [−0.03274, −0.00255] ✓ |
| 3.00 | −0.154541 | −0.023802 | [−0.04204, −0.00433] ✓ |

**De-duplicated, widening the stop measurably HURTS.** Every family that looked like it gained from
a wider stop in §5 is a pseudo-replication artifact. This is the single most important caveat in
this receipt for any lane tempted to widen stops.

### 3d. Convention B — proportional 2:1 target (target at 2k)

k=0.25 −0.30313 · 0.50 −0.22092 · 0.75 −0.16435 · 1.00 −0.12795 · 1.50 −0.08077 · 2.00 −0.05825 ·
2.50 −0.04269 · 3.00 −0.03443 (new unit). Same monotone denominator shape; target share collapses
15.55 % → 4.71 % and mark share rises 32.82 % → 76.19 %.

### 3e. Exit decomposition — what the sweep is actually trading off

| k | exit | n | share | mean R (new) | contribution |
|---:|---|---:|---:|---:|---:|
| 1.0 | stop | 12,341 | 51.634 % | −1.0000 | −0.51634 |
| 1.0 | target | 3,709 | 15.518 % | +2.0020 | +0.31068 |
| 1.0 | mark | 7,851 | 32.848 % | **+0.2370** | +0.07786 |
| 2.0 | stop | 6,633 | 27.752 % | −1.0000 | −0.27752 |
| 2.0 | target | 5,242 | 21.932 % | +1.0020 | +0.21976 |
| 2.0 | mark | 12,026 | 50.316 % | **−0.0117** | −0.00591 |
| 3.0 | stop | 3,938 | 16.476 % | −1.0000 | −0.16476 |
| 3.0 | target | 5,832 | 24.401 % | +0.6681 | +0.16301 |
| 3.0 | mark | 14,131 | 59.123 % | **−0.0682** | −0.04035 |

Widening converts stops into marks, and the mark class **deteriorates from +0.237 to −0.068** as it
does. That is the mechanism by which the price-space number stays flat.

---

## 4. Q3 continued — the net picture, and what the R denominator is really hiding

Cost terms on the honest population, k=1: `spread_r` **0.566996** · `commission_r` 0.063577 ·
`swap_cost_r` 0.014666 · `expected_slippage_r` 0.020000 (flat constant) · **`expected_cost_r`
0.665239**. Every term except the flat slippage allowance is denominated in price, so
`cost_new(k) = (spread_r + commission_r + swap_cost_r)/k + expected_slippage_r`.

| k | gross (new) | gross (price) | net FROZEN | net /7.3 | net /8.5 |
|---:|---:|---:|---:|---:|---:|
| 0.25 | −0.34220 | −0.08555 | −2.94315 | −0.98585 | −0.94199 |
| 0.50 | −0.23821 | −0.11911 | −1.54869 | −0.57004 | −0.54811 |
| 0.75 | −0.16882 | −0.12662 | −1.04914 | −0.39671 | −0.38209 |
| **1.00** | −0.12780 | −0.12780 | **−0.79304** | **−0.30372** | −0.29275 |
| 1.50 | −0.08350 | −0.12525 | −0.53366 | −0.20744 | −0.20013 |
| 2.00 | −0.06367 | −0.12734 | −0.40629 | −0.16163 | −0.15615 |
| 2.50 | −0.05163 | −0.12909 | −0.32973 | −0.13400 | −0.12961 |
| 3.00 | −0.04210 | −0.12630 | −0.27718 | −0.11407 | −0.11042 |

**This is a loss-reduction curve, not an edge curve, and the algebra says it can never be anything
else.** `net_new(k) = (gross_price − cost_price)/(k·d)`. Both numerator terms are price-fixed and
measured k-invariant, so the sign is k-invariant and only the magnitude scales. As k→∞ the number
approaches 0 from below. **No stop width can make this positive.** It is arithmetically identical
to trading a smaller position — which is exactly what an honest expected-value computation already
does (the twelve month-replays' stand-down).

### 4a. The cost gate is paying for a stop-placement defect

The gate is R-denominated (`broker_net_cost_engine.py:859-866` spread limb, `:923-927` total limb),
so a wider stop pushes candidates through it without any change in the trade:

| k | regime | passers | pass % | gross (price) of passers | net (new) of passers |
|---:|---|---:|---:|---:|---:|
| 1.00 | frozen | 6,932 | 29.00 | −0.08063 | −0.16753 |
| 3.00 | frozen | 13,864 | 58.01 | −0.08500 | −0.09572 |
| 1.00 | /7.3 | 14,680 | 61.42 | −0.10288 | −0.17445 |
| 3.00 | /7.3 | 21,248 | 88.90 | −0.10952 | −0.08998 |

A spread-floored stop with the **same** gate: `S(10)`+gate passes **17,657 (73.9 %)** at
net/7.3 **−0.09011**, against the incumbent's 6,932 (29.0 %) at −0.13269. **2.55× the trades at
32 % better R/trade — from a stop change, with the gate untouched.**

---

## 5. Q4 — what the stop is actually too tight *relative to*

### 5a. NOT volatility. The stops are wide.

Pre-decision ATR60 computed from raw M1 bars with strict no-look-ahead (`l2_04_atr.py`; the last
bar stamped before the decision, robust to gaps):

| statistic | value |
|---|---:|
| median stop / ATR60 | **4.030** |
| p10 / p90 | 1.661 / 10.187 |
| share of stops below 1 × ATR60 | **1.206 %** |
| share below 0.5 × ATR60 | 0.004 % |
| median **spread** / ATR60 | **0.6635** |

**The "stop too tight vs market noise" hypothesis is refuted.** The median stop is four one-minute
ATRs away. The number that is out of line is the spread: two thirds of a 1-minute ATR.

| stop / ATR60 | n | gross (price) | net /7.3 | stop % | target % | mean spread_r |
|---|---:|---:|---:|---:|---:|---:|
| [0.5, 1) | 287 | −0.30336 | −0.65837 | 76.7 | 22.6 | 1.143 |
| [1, 2) | 3,629 | −0.22001 | −0.52182 | 71.9 | 24.0 | 1.009 |
| [2, 4) | 7,949 | −0.14639 | −0.36191 | 62.1 | 20.4 | 0.739 |
| [4, 8) | 7,877 | −0.08067 | −0.20346 | 45.7 | 12.7 | 0.356 |
| [8, ∞) | 4,140 | −0.08701 | −0.16526 | 23.4 | 3.7 | 0.209 |

The gradient tracks `spread_r`, not the ATR multiple — every band's k-curve is flat within itself
(full curves in `L2_TIGHTNESS_V1.json → stop_in_atr60_bands`).

### 5b. YES the spread. 15.267 % of the pool has a stop inside the spread.

`spread_r ≥ 1.0` means the quoted spread is at least the entire risk distance — the trade is dead on
arrival:

| | value |
|---|---:|
| n | **3,649** |
| share of honest population | **15.267 %** |
| their gross (price space) | −0.256679 |
| their net FROZEN | **−2.896394** |
| their net /7.3 | −0.699646 |
| **their contribution to pool net FROZEN** | **−0.442197 R/trade** |
| pool gross excluding them | −0.104581 (vs −0.12780) |
| pool net FROZEN excluding them | **−0.414060** (vs −0.79304) |
| pool net /7.3 excluding them | −0.232377 (vs −0.30372) |

By symbol — this is a **symbol-level generator defect, not a market fact**: SPX500 **67.25 %** of
its rows (1,152), NAS100 **69.59 %** (1,030), UK100 31.98 %, JP225 30.88 %, ETHUSD 41.27 %,
EURJPY 13.69 %, CHFJPY 8.76 %, US30_cash 2.59 %, GER40 1.80 %. By family: current_fvg_fill 27.72 %
(1,979), structural_distance_extreme 24.33 % (475), cross_asset_lead_lag 16.81 %,
current_breaker_re_entry 13.73 %, liquidity_sweep_reclaim 10.98 %, everything else ≤ 4.3 %.

Monotone gradient across the whole spread ladder:

| spread_r band | n | gross (price) | net /7.3 | stop % | median risk dist % of price |
|---|---:|---:|---:|---:|---:|
| [0, 0.05) | 6,071 | −0.07504 | −0.19759 | 43.3 | 0.2323 |
| [0.05, 0.1) | 3,459 | −0.09644 | −0.17263 | 47.8 | 0.1041 |
| [0.1, 0.25) | 4,500 | −0.12104 | −0.23965 | 52.5 | 0.0737 |
| [0.25, 0.5) | 3,645 | −0.09985 | −0.24911 | 48.9 | 0.0689 |
| [0.5, 1.0) | 2,577 | −0.16304 | −0.35817 | 57.6 | 0.0803 |
| [1.0, 2.0) | 1,916 | −0.24187 | −0.53681 | 64.2 | 0.0882 |
| [2.0, 5.0) | 1,408 | −0.26927 | −0.78584 | 67.8 | 0.0509 |
| [5.0, ∞) | 325 | −0.28948 | −1.28623 | 74.2 | 0.0252 |

Note the caveat that keeps this honest: `spread_r` is the **frozen** spread, measured 7.3–8.5×
over-charged. At the corrected spread the dead-on-arrival set shrinks to ~2 % — which is why the
`/7.3` column is reported everywhere, and why the repair below is also priced on the corrected
spread (§7).

### 5c. The untakeable cohort is not a tightness story either

`born_past_stop` (3,516) vs the takeable population: median stop/ATR60 **3.539 vs 4.030**, median
risk distance **0.0499 % vs 0.1016 %** of price, median `spread_r` 0.2367. Tighter, but only
mildly — it is a staleness defect (w0-capture), not a stop-width defect.

---

## 6. Q5 — per family, per symbol, per session

`delta_px` = price-space change from k=1 to k=2.5. `salv %` = share of that cut's stops that later
reach the 2R target inside the 2 h wall.

| family | n | stop % | gross k=1 | gross k=2.5 | delta_px | spread_r | net/7.3 k=1 | salv % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current_fvg_fill | 7,139 | 52.60 | −0.14105 | −0.07648 | +0.06457 | 0.8847 | −0.3530 | 26.7 |
| displacement_continuation | 4,424 | 42.95 | −0.10322 | −0.12912 | −0.02589 | 0.2124 | −0.1961 | 5.0 |
| liquidity_sweep_reclaim | 4,410 | 56.15 | −0.07165 | −0.09833 | −0.02668 | 0.4602 | −0.2445 | 18.1 |
| cross_asset_lead_lag | 2,035 | 68.11 | −0.20123 | −0.27150 | −0.07027 | 0.6749 | −0.4357 | 28.6 |
| structural_distance_extreme | 1,952 | 74.69 | −0.27893 | −0.34714 | −0.06821 | 1.0390 | −0.6229 | **48.9** |
| current_ob_retest | 1,289 | 36.77 | −0.05605 | −0.05273 | +0.00332 | 0.2267 | −0.1634 | 9.1 |
| session_open_range_break | 964 | 37.86 | −0.10473 | −0.17049 | −0.06576 | 0.1410 | −0.1773 | 4.1 |
| current_breaker_re_entry | 794 | 53.90 | −0.10766 | −0.01694 | +0.09072 | 0.4234 | −0.2479 | 12.2 |
| volatility_compression_expansion | 603 | 11.61 | −0.09363 | −0.08435 | +0.00928 | 0.1296 | −0.1527 | 1.4 |
| regime_transition_break | 291 | 9.97 | −0.02020 | −0.02634 | −0.00614 | 0.0766 | −0.0692 | 0.0 |

Bootstrap-significant (2 SE) price-space deltas: **current_fvg_fill** +0.0276/+0.0528/+0.0748 at
k=1.5/2/3 and **current_breaker_re_entry** +0.1060 at k=3 are the only positives — and
current_fvg_fill is **91.9 % pseudo-replicated**, so §3c applies. Significant negatives:
displacement_continuation −0.0285 at k=3, session_open_range_break −0.0748 at k=3,
cross_asset_lead_lag −0.1045 at k=3, liquidity_sweep_reclaim −0.0282 at k=0.5,
structural_distance_extreme +0.0891 at k=0.5 (i.e. it wants a *tighter* stop).

**`structural_distance_extreme` has the most salvageable stop-outs by far — 48.9 % of its stops
later reach target** — and it is still the worst family in the estate (gross −0.27893, net/7.3
−0.6229, spread_r 1.0390, 24.33 % dead on arrival). Salvageability and value are unrelated here:
its reversals are overshoot noise, and its k=2.5 delta is −0.068.

Per symbol (24 symbols, full table in `L2_CUTS_V1.json → symbol`): worst gross NAS100 −0.30800
(spread_r 2.282), UK100 −0.21530, GBPUSD −0.20788, USDCAD −0.20517; best BTCUSD −0.02169
(spread_r 0.000), XAGUSD −0.00477, GER40 −0.02970. Salvage % runs 14.1 (AUDUSD) to 34.3 (XAUUSD).

Session (full table in the JSON): worst tokyo −0.20578 (salv 13.4 %), best london −0.08389.
Side: SHORT n=13,217 gross −0.13851 salv 21.4 % · LONG n=10,684 −0.11455 salv 23.7 %.
Timeframe: M15 on every row — there is no timeframe contrast to measure.

---

## 7. The dynamic levers — everything else a stop can do

All at k=1, price space, honest fill, 2 h wall. n=24,142.

| config | gross | **delta vs baseline** | win % | net FROZEN | net /7.3 | L→W | W→L |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | −0.12653 | 0 | 35.291 | −0.78888 | −0.30216 | 0 | 0 |
| be_at 0.25 | −0.12377 | +0.00275 | 13.669 | −0.78612 | −0.29940 | 0 | 5,220 |
| be_at 0.5 | −0.13088 | −0.00435 | 21.456 | −0.79323 | −0.30651 | 0 | 3,340 |
| be_at 0.75 | −0.12626 | +0.00026 | 26.903 | −0.78862 | −0.30190 | 0 | 2,025 |
| be_at 1.0 | −0.12448 | +0.00204 | 30.258 | −0.78683 | −0.30011 | 0 | 1,215 |
| be_at 1.5 | −0.12451 | +0.00202 | 33.717 | −0.78686 | −0.30014 | 0 | 380 |
| **trail 0.25** | **−0.08006** | **+0.04646** | 66.154 | −0.74241 | −0.25569 | 7,456 | 5 |
| trail 0.5 | −0.10849 | +0.01803 | 54.913 | −0.77085 | −0.28412 | 4,739 | 2 |
| trail 0.75 | −0.11503 | +0.01150 | 47.647 | −0.77738 | −0.29066 | 2,984 | 1 |
| trail 1.0 | −0.11906 | +0.00746 | 43.257 | −0.78142 | −0.29469 | 1,924 | 1 |
| trail 1.5 | −0.12256 | +0.00397 | 37.942 | −0.78491 | −0.29819 | 640 | 0 |
| partial @1.0 | −0.12391 | +0.00261 | 36.894 | −0.78627 | −0.29954 | 387 | 0 |
| partial @0.5 | −0.12483 | +0.00170 | 38.597 | −0.78718 | −0.30046 | 798 | 0 |
| be1.0 + trail1.0 | −0.11906 | +0.00746 | 43.257 | −0.78142 | −0.29469 | 1,924 | 1 |
| time stop 15 | −0.11820 | +0.00832 | 27.939 | −0.78056 | −0.29383 | 2,711 | 4,486 |
| time stop 30 | −0.12241 | +0.00411 | 30.901 | −0.78477 | −0.29804 | 2,331 | 3,391 |
| time stop 60 | −0.12402 | +0.00250 | 33.311 | −0.78638 | −0.29965 | 1,689 | 2,167 |
| time stop 90 | −0.12400 | +0.00252 | 34.359 | −0.78636 | −0.29963 | 1,018 | 1,243 |
| be0.5 + time60 | −0.12600 | +0.00052 | 22.678 | −0.78836 | −0.30163 | 1,081 | 4,126 |
| **NO STOP AT ALL** | −0.12388 | **+0.00264** | 52.498 | −0.78624 | −0.29951 | 4,154 | 0 |

**Break-even moves are worthless** (±0.004) and cost 5,220 winners at the 0.25R setting.
**The 0.25R trail is the only lever above noise** at +0.04646 — it converts 7,456 losers to winners
against 5 losses and lifts the win rate to 66.2 %, but it is still −0.256 net at the corrected
spread. Per family the trail is sign-mixed: current_fvg_fill +0.11368, cross_asset_lead_lag
+0.06005, session_open_range_break +0.04610, structural_distance_extreme +0.04070,
volatility_compression_expansion +0.03297, displacement_continuation +0.02682,
regime_transition_break +0.01415, current_ob_retest −0.00159, current_breaker_re_entry −0.01571,
liquidity_sweep_reclaim −0.01600.

### 7a. The best combined rule, priced end to end

`S(c)`: per-row `k_i = max(1, c × spread_r)` — never risk less than c spreads. Trail held at
0.25 × the **original** risk distance in price at every k.

| rule | gross (new) | win % | net FROZEN | net /7.3 |
|---|---:|---:|---:|---:|
| baseline k=1 | −0.12653 | 35.291 | −0.78888 | −0.30216 |
| k=1 + 0.25R trail | −0.08006 | 66.154 | −0.74241 | −0.25569 |
| S(5) | −0.07472 | 42.474 | −0.27960 | −0.16913 |
| S(5) + trail | −0.04132 | 72.508 | −0.24621 | −0.13573 |
| S(10) | −0.05649 | 45.000 | −0.19934 | −0.13357 |
| S(10) + trail | −0.02408 | 74.812 | −0.16692 | −0.10115 |
| S(20) | −0.03917 | 47.606 | −0.13915 | −0.10221 |
| **S(20) + trail** | −0.01483 | 76.758 | **−0.11481** | **−0.07786** |
| flat k=3.0 | −0.04168 | 49.159 | −0.27580 | −0.11356 |
| flat k=3.0 + trail | −0.02059 | 78.063 | −0.25471 | −0.09247 |

**Recoverable: +0.67407 R/trade at frozen cost, +0.22430 R/trade at the corrected spread.**
Both are loss-reduction. Neither crosses zero. Full ladders — S(c) for c ∈ {1,2,3,5,8,10,15,20} on
both the frozen and corrected spread, and an ATR-floor variant A(c) for c ∈ {0.5,1,2,3,5} — are in
`L2_ADAPTIVE_STOP_V1.json`. Applying the floor to the **corrected** spread instead of the frozen one
moves far less (S(10)/7.3 net_frozen −0.48090 vs S(10)/frozen −0.19983), confirming that most of the
frozen-cost recovery is the known over-charge and not a real repair.

---

## 8. Why no stop rule works — the deficit is created at the fill, not during the hold

Measured **unconditionally**: every honest candidate's mean signed R at each clock offset from its
own decision, whether or not it would ever have filled. `t=0` is the open of the decision-stamped M1
bar (= the decision instant, bars being open-stamped); `t=+1 min` is that bar's close; `p0…p19` are
the path sidecar's closes, which begin at decision+1 min.

| group | n | fill % | t0 | t+1 m | p0 | p5 | p19 | t0→t1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **born_at_limit** (market orders — **no fill conditioning**) | 14,911 | 98.46 | **−0.0028** | −0.0298 | −0.0647 | −0.0744 | **−0.0766** | −0.02704 |
| born_resting (true limits) | 7,949 | 99.96 | +1.6569 | +1.5764 | +1.4882 | +1.3455 | +1.0205 | −0.08043 |
| born_marketable | 1,265 | 99.37 | −0.2983 | −0.3066 | −0.3157 | −0.2927 | −0.2842 | −0.00824 |
| all honest | 24,142 | 99.00 | +0.5285 | +0.4849 | +0.4332 | +0.3826 | +0.2752 | −0.04365 |

`born_at_limit` is the clean instrument: the entry price **is** the last observable market price, so
there is no adverse-selection conditioning at all. It starts at **−0.0028 R** — indistinguishable
from zero, exactly as it must — and reaches **−0.0766 R** twenty minutes later, then stops moving.
**That −0.077 R is the entire directional content of the signal**, and it is the wrong sign.

Conditioned on an actual fill (`l2_11`), the same picture at higher resolution: mean R at the close
of the **fill bar itself** is −0.1644 (all) / −0.2429 (filled on bar 1) / −0.3352 (born_marketable),
and nineteen minutes later it is −0.1553 / −0.2285 / −0.3044. **Everything is present at the fill;
the following nineteen minutes contribute +0.009 R.**

Family-level unconditional drift at t0 → p19: structural_distance_extreme −0.0037 → −0.1670 (worst),
cross_asset_lead_lag −0.0053 → −0.1013, liquidity_sweep_reclaim −0.0029 → −0.0759,
displacement_continuation −0.0018 → −0.0474, session_open_range_break −0.0015 → −0.0227,
volatility_compression_expansion −0.0006 → −0.0254, regime_transition_break −0.0004 → −0.0205.
Symbol drift t0→t1 ranges NAS100 −0.10551 (worst) to AUDUSD +0.01414, EURUSD +0.01022,
NZDUSD +0.00587 (the only three positive).

Set that against the charged cost: **0.665 R/trade frozen, ≈0.176 R/trade at the corrected spread.**
The cost is **8.7×** the directional deficit at frozen prices and **2.3×** at corrected ones. No exit
policy can close a gap of that shape, and this lane's exhaustive sweep is the proof: the largest
effect any stop change produces is +0.047 R against a 0.176–0.665 R cost.

---

## 9. What this lane hands the next wave

1. **Stop placement is closed as a hypothesis.** Distance, break-even, trail, partial, time stop and
   outright removal are all measured. Ceiling from the exit side: **+0.047 R/trade** (0.25R trail).
   Do not re-open it without new evidence about the *entry*.
2. **`spread_r` is the single strongest conditioning variable in the pool** and it is available at
   the decision instant. Monotone across eight bands, 15.267 % of rows have `spread_r ≥ 1`, and
   those rows carry **−0.442 R/trade** of the pool's frozen net. Two symbols — SPX500 and NAS100 —
   account for 2,182 of the 3,649 at 67–70 % of their own rows. That is a generator/symbol-surface
   defect and it is cheap to fix.
3. **The R denominator is a measurement hazard the estate has not priced.** Any R-denominated
   number here can be improved arbitrarily by widening the stop with no change in the underlying
   trade — measured over a 12× range in §3a. Every published R/trade figure in the estate is
   implicitly quoting a stop-width convention. Related: the incumbent cost gate is R-denominated,
   so it is partly a stop-width filter (§4a).
4. **De-duplicate before any stop or exit test** (§3c). Raw-pool and de-duplicated stop sweeps have
   opposite signs at k ≥ 2.
5. **The next lane's target is the first minute.** For a market-order entry the deficit is 0 at the
   decision and −0.077 R twenty minutes later, flat thereafter. Whatever creates it acts inside that
   window: it is the entry price, the entry timing, or the signal's sign — not the exit.

---

## 10. Artifacts

Scripts (all under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`):
`l2_01_stop_census.py` · `l2_02_stop_sweep.py` · `l2_03_net_and_gate.py` · `l2_04_atr.py` ·
`l2_05_cuts.py` · `l2_06_atr_tightness.py` · `l2_07_adaptive_stop.py` · `l2_08_dynamic_stop.py` ·
`l2_09_invariance_test.py` · `l2_10_drift.py` · `l2_11_first_minutes.py` · `l2_12_unconditional.py` ·
`l2_13_combined.py`

Results: `l2_RESULT.json` (index + every component receipt inlined) ·
`L2_STOP_CENSUS_V1.json` · `L2_STOP_SWEEP_V1.json` · `L2_NET_GATE_V1.json` · `L2_CUTS_V1.json` ·
`L2_TIGHTNESS_V1.json` · `L2_ADAPTIVE_STOP_V1.json` · `L2_DYNAMIC_STOP_V1.json` ·
`L2_INVARIANCE_V1.json` · `L2_DRIFT_V1.json` · `L2_FIRST_MINUTES_V1.json` ·
`L2_UNCONDITIONAL_V1.json` · `L2_COMBINED_V1.json`

Derived data: `l2_RECS_V1.jsonl.gz` (per-row honest walk + post-stop forensics) ·
`l2_SWEEP_ROWS_V1.jsonl.gz` (per-row R at all 16 stop multiples, both target conventions) ·
`l2_ATR_V1.jsonl.gz` (pre-decision ATR60/ATR240, no look-ahead).

Source of M1 bars for the ATR:
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601/`
