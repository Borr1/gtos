# Lane l1 — the prize in the capture gap, measured

**Population.** `TAKEABLE` = the **24,142** of 27,658 January candidates whose stop price was **not
already breached at the decision instant** (w0-capture's `born_past_stop`, classified with zero
look-ahead from the M1 bar closing AT the decision). The 3,516 excluded rows book a mechanical
**−0.9958 R** each under every contract in this receipt and would drown every other signal.

**Fill convention.** `REAL` — fill at bar 0 when the order was born at-or-through the market
(`mkt_r_prev_close <= 0`: 53.95 % at-market + 4.58 % already-marketable), otherwise wait for the
first bar in which price actually trades at `entry_price`. Fill rate **99.99 %** (3 no-fills).
The pool's own `BLIND` convention is quoted only where the contrast is the point.

**Tie rule.** Stop and target reachable inside the same M1 bar → the **STOP** is taken.

**Horizon.** Hard 2 hours (≤120 M1 bars; 86.12 % of paths are exactly 120). Every number below is
bounded by that wall and no question beyond it is answerable from this asset.

**Substrate built.** `l1_TOUCH_INDEX_V1.jsonl.gz` — per candidate, the first-touch bar index for 18
favourable and 10 adverse levels under all three fill conventions, so any (target, stop) cell is an
O(1) lookup. Built in 3.6 s; the whole 180-cell surface then costs seconds, not the 15-minute stall
of a raw sidecar pass.

---

## 0. The one-paragraph answer

The capture gap is **enormous and almost entirely uncapturable.** Mean MFE over the takeable
population is **+1.8956 R** and mean MAE is **−2.0153 R** — near-symmetric, tilted *adverse* by
0.1197 R. Because the two excursions are symmetric, the paths behave as a martingale with a small
negative drift, and the optional-stopping theorem is visible in the data: **all 275 exit contracts
tested (180 fixed cells + 95 trail / break-even / partial / time-stop variants) land in a band from
−0.1077 to −0.0190 R/trade — a span of 0.0887 R — and not one is positive.** The best contract found by fitting on
Jan 01–15 held almost exactly on Jan 16–31 (**+0.0007** shrinkage) and is worth **+0.0423 R/trade**
against the declared 2R/1R contract — real, tested, and far too small to matter, because the
corrected cost is **0.1756 R/trade**. Of the pool's published **−0.2175** gross, exit geometry
accounts for **+0.0414**; the fill convention accounts for **+0.2404** and the already-stopped
artifact for **+0.1266**. The only net-positive subset that survives out of sample is
**XAUUSD at a 0.75R target / 3R stop (+0.1091 R/trade net, t = 4.545, n = 2,329)** — and its
signal/direction decomposition shows it is **half a January gold rally**: LONG +0.2967, SHORT
−0.0711. Pool-wide the direction-neutral **SIGNAL is −0.0291 R (t = −1.286)** while the
**DIRECTION term is +0.0905 R (t = 4.005)**. The entries carry no measurable predictive content;
what the January pool contains is the month's move.

---

## 1. MFE and MAE — full distributions (deliverable 1)

Takeable population, REAL fill, n filled = 24,139.

| | mean | sd | p05 | p25 | median | p75 | p90 | p95 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **MFE** | **+1.8956** | 3.0749 | +0.0060 | +0.3726 | **+1.0083** | +2.2638 | +4.5480 | +6.6452 | −5.8954 | +75.8922 |
| **MAE** | **−2.0153** | 3.0275 | −6.7879 | −2.4161 | **−1.1298** | −0.4998 | −0.2020 | −0.1070 | −150.9662 | +9.1654 |

(MFE `min` is negative and MAE `max` is positive because a few paths never trade back through the fill in the favourable — or the adverse — direction at all before the wall.)

Excursion asymmetry `E[MFE] − E[|MAE|]` = **−0.1197 R**. A driftless path gives 0.

**Perfect-foresight ceiling** (exit exactly at MFE on every trade) = **+1.8956 R/trade**.
**Realized at the declared 2R/1R contract** = **−0.0842**. Capture ratio **−0.0444**.
The entire 1.98 R gap between them is the price of not knowing the future — the floor
(exit at MAE) is −2.0153, and the two bracket zero almost exactly.

**MFE ladder** — share of filled trades ever touching each favourable level:

| ≥0.10 | ≥0.25 | ≥0.50 | ≥0.75 | ≥1.00 | ≥1.25 | ≥1.50 | ≥1.75 | ≥2.00 | ≥2.25 | ≥2.50 | ≥3.00 | ≥3.50 | ≥4.00 | ≥5.00 | ≥6.00 | ≥8.00 | ≥10.0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| .9079 | .8107 | .6902 | .5881 | .5024 | .4330 | .3757 | .3288 | **.2834** | .2519 | .2226 | .1771 | .1426 | .1197 | .0866 | .0630 | .0340 | .0201 |

**MAE ladder** — share ever touching each adverse level:

| ≤−0.25 | ≤−0.50 | ≤−0.75 | ≤−1.00 | ≤−1.25 | ≤−1.50 | ≤−1.75 | ≤−2.00 | ≤−2.50 | ≤−3.00 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| .8741 | .7499 | .6355 | **.5429** | .4649 | .4023 | .3533 | .3104 | .2409 | .1925 |

> **The declared stop sits inside the noise.** 54.29 % of takeable candidates touch −1R inside two
> hours and the median MAE is −1.1298 R. The stop is at roughly the 46th percentile of adverse
> excursion while the 2R target is at the 28th percentile of favourable excursion. Bars to MFE:
> median **63**, mean 61.8, p25 22, p75 102 — the best moment of the trade is typically an hour in.

### Per family (takeable, REAL fill)

| family | n | MFE mean | MFE med | MFE p75 | MFE p90 | MAE mean | MAE med | MAE p25 | ASYM | ≥1R | ≥2R | ≤−1R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| current_fvg_fill | 7,145 | +2.012 | 1.049 | 2.441 | 4.908 | −2.126 | −1.193 | −2.536 | −0.1141 | .512 | .303 | .565 |
| liquidity_sweep_reclaim | 4,475 | +1.945 | 1.246 | 2.462 | 4.449 | −1.946 | −1.268 | −2.564 | **−0.0005** | .577 | .319 | .583 |
| displacement_continuation | 4,469 | +1.043 | 0.712 | 1.399 | 2.299 | −1.180 | −0.855 | −1.527 | −0.1366 | .374 | .137 | .433 |
| cross_asset_lead_lag | 2,083 | +2.703 | 1.705 | 3.494 | 6.342 | −2.866 | −1.955 | −3.848 | −0.1630 | .671 | .438 | .722 |
| structural_distance_extreme | 1,993 | +4.336 | 2.978 | 5.730 | 9.573 | −4.695 | −3.140 | −6.059 | −0.3589 | .791 | .634 | .817 |
| current_ob_retest | 1,292 | +0.982 | 0.690 | 1.314 | 2.207 | −1.073 | −0.693 | −1.423 | −0.0908 | .363 | .120 | .371 |
| session_open_range_break | 987 | +0.924 | 0.659 | 1.190 | 1.949 | −1.138 | −0.735 | −1.384 | −0.2132 | .329 | .095 | .372 |
| current_breaker_re_entry | 796 | +1.493 | 0.899 | 2.004 | 3.601 | −1.526 | −1.132 | −2.103 | −0.0322 | .460 | .251 | .558 |
| volatility_compression_expansion | 605 | +0.399 | 0.258 | 0.533 | 0.922 | −0.483 | −0.350 | −0.682 | −0.0834 | .079 | .013 | .116 |
| regime_transition_break | 297 | +0.458 | 0.314 | 0.614 | 1.056 | −0.463 | −0.334 | −0.616 | −0.0054 | .104 | .020 | .098 |

**MFE scales inversely with how tight the stop was set.** `structural_distance_extreme` has a median
risk distance of **0.0300 %** of price and an MFE of 4.34 R; `regime_transition_break` has 0.4454 %
and an MFE of 0.46 R. Both are the same price move measured in different denominators — see §6.

---

## 2. The money surface (deliverable 2)

Realized R **per candidate** (a no-fill books exactly 0.0), takeable population, REAL fill, the
actual paths, true first-touch semantics.

### The requested 10 × 6 grid

| T \\ S | 0.50 | 0.75 | 1.00 | 1.25 | 1.50 | 2.00 |
|---|---:|---:|---:|---:|---:|---:|
| **0.50** | −0.0684 | −0.0829 | −0.0865 | −0.0915 | −0.0924 | −0.0949 |
| **0.75** | −0.0678 | −0.0804 | −0.0831 | −0.0858 | −0.0858 | −0.0857 |
| **1.00** | −0.0673 | −0.0790 | −0.0803 | −0.0847 | −0.0865 | −0.0858 |
| **1.25** | −0.0683 | −0.0807 | −0.0815 | −0.0838 | −0.0859 | −0.0839 |
| **1.50** | −0.0702 | −0.0799 | −0.0814 | −0.0802 | −0.0804 | −0.0770 |
| **2.00** | −0.0750 | −0.0828 | **−0.0842** | −0.0822 | −0.0815 | −0.0823 |
| **2.50** | −0.0752 | −0.0822 | −0.0831 | −0.0786 | −0.0787 | −0.0800 |
| **3.00** | −0.0753 | −0.0812 | −0.0810 | −0.0761 | −0.0768 | −0.0800 |
| **4.00** | −0.0737 | −0.0785 | −0.0794 | −0.0726 | −0.0721 | −0.0733 |
| **5.00** | −0.0681 | −0.0718 | −0.0695 | **−0.0608** | −0.0611 | −0.0626 |

**The whole 60-cell surface spans 0.0341 R.** Best +(−0.0608) at T5.00/S1.25 (win 36.95 %, target
4.85 %, stop 45.90 %, path-end 49.26 %). Declared contract T2/S1 = −0.0842.

Extended to the full 18 × 10 ladder the maximum is **−0.03263 at T8.00/S0.25** — still a corner, and
still negative. Riding to the wall with no target and no stop at all is **−0.0386**; with no target
and a stop it ranges −0.0393 (S0.25) to −0.0772 (S1.00). **Every road leads to the same place.**

### The same surface under the other conventions (the contrast that matters)

| population | fill | best cell | best R | T2/S1 |
|---|---|---|---:|---:|
| ALL 27,658 | REAL | T1.00/S0.50 | −0.1222 | −0.2000 |
| ALL 27,658 | STRICT | T0.50/S0.50 | −0.1553 | −0.2372 |
| ALL 27,658 | **BLIND** | T2.00/S0.50 | **+0.1164** | **+0.0404** |
| TAKEABLE 24,142 | REAL | T8.00/S0.25 | −0.0326 | −0.0842 |
| TAKEABLE 24,142 | STRICT | T5.00/S1.25 | −0.1036 | −0.1267 |
| TAKEABLE 24,142 | **BLIND** | T2.00/S0.50 | **+0.2060** | **+0.1913** |

The fill convention alone is worth **+0.2404 R/trade of fiction** at the declared cell
(+0.0404 blind vs −0.2000 real, whole pool). This corroborates W0-F2 through an independent path.

### Is the best cell a fit or a finding?

Fitted on **Jan 01–15** (n = 11,422), evaluated on **Jan 16–31** (n = 12,720):

| | fit cell | train R | **test R** | shrinkage | test flat T2/S1 | test delta |
|---|---|---:|---:|---:|---:|---:|
| POOL | T0.75/S0.25 | −0.03636 | **−0.03702** | **+0.0007** | −0.07930 | **+0.04228** |

**It holds.** A per-family fitted policy does *not* beat it (test −0.04119 vs the single pool cell's
−0.03702); per-born does slightly (−0.01773, delta +0.06157); per-symbol −0.02986. Per-family fits
shrink badly — `current_ob_retest` −0.2755, `current_breaker_re_entry` −0.0872,
`liquidity_sweep_reclaim` −0.0865, `displacement_continuation` −0.0705 — while two hold:

| family | fit cell | train | **test** | shrinkage | test T2/S1 |
|---|---|---:|---:|---:|---:|
| structural_distance_extreme | T3.00/S0.25 | +0.0817 | **+0.0856** | +0.0039 | −0.0780 |
| cross_asset_lead_lag | T3.50/S0.25 | +0.0033 | **+0.0039** | +0.0006 | −0.0566 |

`structural_distance_extreme` is the widest single-family capture gap in the pool: **+0.164 R/trade**
between the declared contract and a tested one, on 1,993 candidates. It does not survive costs (§6).

---

## 3. Time to outcome and the 2-hour wall (deliverable 3)

Declared contract T2/S1, takeable, REAL fill:

| | n | median | mean | p25 | p75 | p90 |
|---|---:|---:|---:|---:|---:|---:|
| bars (minutes) to **target** | 4,127 | **41** | 47.52 | 18.0 | 74.0 | 98.4 |
| bars (minutes) to **stop** | 12,156 | **27** | 36.53 | 8.0 | 58.0 | 91.0 |

**Losers resolve 1.5× faster than winners.** 7,856 trades (**32.54 %**) are still open at the wall;
their unrealized R is mean **+0.2381**, median +0.1552, and **61.47 % of them are positive** — i.e.
the wall systematically truncates the winning tail, which is exactly what makes the realized payoff
1.18 : 1 against a declared 2.00 : 1.

Per family, at the declared contract:

| family | bars→target (med) | bars→stop (med) | open at 2 h | unrealized mean |
|---|---:|---:|---:|---:|
| structural_distance_extreme | 10 | 3 | 1.9 % | +0.2913 |
| cross_asset_lead_lag | 24 | 12 | 10.0 % | +0.5003 |
| liquidity_sweep_reclaim | 41 | 19 | 23.4 % | +0.3773 |
| current_breaker_re_entry | 55 | 33 | 28.3 % | +0.2675 |
| current_fvg_fill | 55 | 38 | 31.3 % | +0.2026 |
| volatility_compression_expansion | 44 | 86 | **87.3 %** | +0.0009 |
| displacement_continuation | 61 | 42 | 46.0 % | +0.2443 |
| regime_transition_break | 72 | 67 | **88.2 %** | +0.0609 |
| session_open_range_break | 72 | 53 | 55.2 % | +0.2542 |
| current_ob_retest | 80 | 60 | 55.0 % | +0.2668 |

Two families (`volatility_compression_expansion`, `regime_transition_break`) essentially **never
resolve inside two hours** — 87–88 % marked at the wall at ~0 R. Their published economics describe
a horizon this asset cannot see.

Independent of exit choice: w0-capture measured that continuing marked trades into raw M1 for 24 h
past the wall is worth **+0.017 R per filled trade**. The wall is real but small.

---

## 4. Trailing, break-even and partial variants (deliverable 4)

95 variants, same paths, same fill, same tie rule (worst is `T2.0/S1.0 + BE@0.50` at −0.08902). Fitted and tested on the same date split.

| variant | ALL takeable | train (01–15) | **test (16–31)** | shrinkage | win rate |
|---|---:|---:|---:|---:|---:|
| **no target, 1R stop, trail 0.25R** | **−0.01904** | −0.01441 | **−0.02320** | −0.0088 | 0.6903 |
| T5.0, 1R stop, trail 0.25R | −0.02424 | −0.02222 | −0.02605 | −0.0038 | 0.6903 |
| T3.0, 1R stop, trail 0.25R | −0.02738 | −0.02559 | −0.02899 | −0.0034 | 0.6903 |
| T2.0, 1R stop, trail 0.25R | −0.03132 | −0.02922 | −0.03321 | −0.0040 | 0.6903 |
| no target, 1R stop, trail 0.75R | −0.05127 | −0.05985 | −0.04356 | +0.0163 | 0.5064 |
| no target, 1R stop, trail 0.50R | −0.04568 | −0.04473 | −0.04653 | −0.0018 | 0.5813 |
| best fixed cell (T8.00/S0.25) | −0.03263 | — | — | — | — |
| declared T2.0/S1.0 | −0.08415 | — | — | — | 0.3710 |
| T5.0/S1.25 | −0.06078 | — | — | — | 0.3695 |

**Yes — a trail beats the best fixed cell, by +0.0136 R/trade, and it holds out of sample.** The
winner is the *tightest* trail on the ladder (0.25 R), which is the martingale result in disguise:
the closer a stopping rule gets to "exit immediately", the closer its expectation gets to zero. Its
69 % win rate is not skill; it is a 0.25 R average win against occasional full losses.

**Break-even moves, partial scale-outs and time stops are all worse.** No BE variant, no partial
(50 % at 0.5/1.0/1.5 R, with or without BE on the remainder), and no time stop (5/15/30/45/60/90
bars) reached the top 10 by test R at any target. The best time-stop variant, T5.0/S1.25 capped at
90 bars, is −0.06027.

Applied to the two strata that matter, the same trail gives `structural_distance_extreme`
**+0.04554** and `born_resting|LONG` **+0.00288** — the only positives in the variant table, and
both are subsets, not the pool.

---

## 5. Where the gap is widest (deliverable 5)

### By family — excursion asymmetry, declared contract, and the best cell

| family | n | ASYM | R @T2/S1 | R best | best cell | recoverable |
|---|---:|---:|---:|---:|---|---:|
| structural_distance_extreme | 1,993 | −0.3589 | −0.0797 | **+0.0934** | T8.00/S0.25 | **+0.1731** |
| liquidity_sweep_reclaim | 4,475 | −0.0005 | −0.0191 | +0.0368 | T6.00/S1.25 | +0.0559 |
| cross_asset_lead_lag | 2,083 | −0.1630 | −0.0746 | +0.0164 | T10.0/S0.25 | +0.0910 |
| current_breaker_re_entry | 796 | −0.0322 | −0.1028 | +0.0066 | T1.75/S3.00 | +0.1094 |
| current_ob_retest | 1,292 | −0.0908 | −0.0546 | +0.0138 | T0.75/S3.00 | +0.0684 |
| regime_transition_break | 297 | −0.0054 | −0.0035 | +0.0191 | T0.50/S0.50 | +0.0226 |
| session_open_range_break | 987 | −0.2132 | −0.0673 | −0.0139 | T0.50/S1.00 | +0.0534 |
| volatility_compression_expansion | 605 | −0.0834 | −0.0918 | −0.0195 | T0.10/S0.25 | +0.0723 |
| displacement_continuation | 4,469 | −0.1366 | −0.0812 | −0.0289 | T0.50/S0.25 | +0.0523 |
| current_fvg_fill | 7,145 | −0.1141 | −0.1391 | −0.0291 | T0.10/S3.00 | +0.1100 |

(The "best" column is in-sample over 180 cells; §2 shows only two of these survive a date split.)

### By direction and born state

| stratum | n | ASYM | R @T2/S1 | 2 h drift | drift t |
|---|---:|---:|---:|---:|---:|
| LONG | 10,792 | −0.1791 | −0.0741 | **+0.0614** | +1.96 |
| SHORT | 13,350 | −0.0716 | −0.0922 | **−0.1196** | −3.68 |
| born_resting | 7,949 | −0.0388 | −0.0947 | **+0.0806** | +1.94 |
| born_at_limit | 14,911 | −0.1301 | −0.0597 | −0.0859 | −2.96 |
| born_marketable | 1,265 | −0.4964 | −0.2994 | **−0.2586** | −4.45 |

**`born_marketable` is the worst thing in the pool after `born_past_stop`** — chasing a level the
market has already gone through costs 0.2586 R of drift and 0.2994 R at the declared contract, on
1,265 candidates. It is decision-time observable and declining it is worth **+0.0072 R per original
candidate** at zero cost.

Intersections (2 h mark-to-market drift, no exit logic):

| stratum | n | drift | t |
|---|---:|---:|---:|
| born_resting \| LONG | 3,612 | **+0.1500** | +2.596 |
| born_resting \| SHORT | 4,334 | +0.0227 | +0.383 |
| born_at_limit \| LONG | 6,789 | +0.0167 | +0.433 |
| born_marketable \| LONG | 375 | −0.0758 | −0.598 |
| born_at_limit \| SHORT | 8,122 | −0.1716 | −4.038 |
| born_marketable \| SHORT | 890 | **−0.3357** | −5.345 |
| born_resting \| LONG \| current_ob_retest | 631 | **+0.2446** | +4.43 |
| born_resting \| LONG \| current_breaker_re_entry | 207 | +0.2779 | +2.294 |
| born_at_limit \| LONG \| liquidity_sweep_reclaim | 1,955 | +0.1541 | +2.396 |

### The drift curve — the reason the surface is flat

Mean mark-to-market R at bar k, **no exit logic at all**, takeable, REAL fill, n = 24,139:

| bar | 1 | 2 | 3 | 5 | 10 | 15 | 20 | 30 | 45 | 60 | 90 | 120 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mean R | −0.0969 | −0.0924 | −0.0980 | −0.0960 | −0.0836 | −0.0841 | −0.0926 | −0.0595 | −0.0550 | −0.0446 | −0.0309 | −0.0387 |

se@120 = 0.0228, t = −1.69, median −0.0522, share positive 48.13 %.

**A trade is worth −0.0969 R one minute after it is filled and recovers to −0.0387 by the wall.**
The damage is a level shift at the fill, not a drift over the holding period. For a martingale
E[R_τ] = 0 for every bounded stopping time — which is precisely why 275 different exit contracts all
land within 0.0887 R of each other (worst T0.25/S1.25 −0.10769, best trail-0.25 −0.01904). **There is no drift for an exit rule to harvest.**

Per family at the wall (t in brackets): current_ob_retest **+0.0703** (1.82), current_fvg_fill
+0.0369 (0.80), liquidity_sweep_reclaim +0.0130 (0.30), current_breaker_re_entry −0.0207 (−0.27),
regime_transition_break −0.0221 (−0.62), cross_asset_lead_lag −0.0308 (−0.34),
volatility_compression_expansion −0.0745 (−2.85), **displacement_continuation −0.1143 (−4.64)**,
session_open_range_break −0.1566 (−3.08), structural_distance_extreme −0.2749 (−1.75).

`displacement_continuation` is significantly negative at t = −4.64 on n = 4,469 — the same
inverse-edge shape CQ found in `current_breaker_re_entry`, on a family 5.6× larger. Filed for
another lane; it is an entry finding, not an exit one.

### By session / hour (best cells are in-sample; treat as a map, not a policy)

Positive-asymmetry buckets: `moonshot_h13_14` +0.8762 (n 133), `moonshot_h23_00` +0.5579 (n 451),
`london` +0.0708 (n 4,055), `moonshot_h09_10` +0.0585 (n 312), `ny` +0.0523 (n 4,261).
Worst: `moonshot_h21_22` −0.4581 (n 1,031), `moonshot_h20_21` −0.4398 (n 672),
`moonshot_h03_04` −0.4068 (n 800), `moonshot_h01_02` −0.3989 (n 793), `tokyo` −0.2681 (n 1,176).
London's declared-contract R is −0.0049, the least-bad large bucket in the pool.

---

## 6. Why the best geometry still loses — cost is a function of the stop, not the path

The corrected cost model (spread/7.3 + commission + slippage + swap) charged per family:

| family | n | corrected cost R | frozen cost R | median spread R | median risk distance (% of price) | MFE mean | share cost > own MFE |
|---|---:|---:|---:|---:|---:|---:|---:|
| structural_distance_extreme | 1,993 | **0.3426** | 1.2308 | 0.3554 | **0.0300 %** | 4.336 | 10.2 % |
| cross_asset_lead_lag | 2,083 | 0.2327 | 0.8057 | 0.2016 | 0.0594 % | 2.703 | 11.8 % |
| current_fvg_fill | 7,145 | 0.2119 | 0.9750 | 0.3965 | 0.0982 % | 2.012 | 13.4 % |
| liquidity_sweep_reclaim | 4,475 | 0.1726 | 0.5668 | 0.1638 | 0.0770 % | 1.945 | 9.4 % |
| current_breaker_re_entry | 796 | 0.1406 | 0.5086 | 0.2053 | 0.0921 % | 1.493 | 11.2 % |
| current_ob_retest | 1,292 | 0.1072 | 0.3027 | 0.0904 | 0.1109 % | 0.982 | 7.6 % |
| displacement_continuation | 4,469 | 0.0927 | 0.2757 | 0.0809 | 0.1642 % | 1.043 | 10.8 % |
| session_open_range_break | 987 | 0.0722 | 0.1933 | 0.0670 | 0.1681 % | 0.924 | 8.9 % |
| volatility_compression_expansion | 605 | 0.0590 | 0.1706 | 0.0449 | 0.3392 % | 0.399 | 14.9 % |
| regime_transition_break | 297 | 0.0488 | 0.1145 | 0.0295 | 0.4454 % | 0.458 | 12.1 % |

**Cost and MFE are the same quantity in different clothes.** Both are price distances divided by the
risk distance, so the family with the tightest stops has both the biggest MFE (4.34 R) and the
biggest cost (0.34 R). Ordering families by MFE alone is meaningless; the invariant is the MFE-to-cost ratio, which ranges
**6.78 → 12.80** across all ten (volatility_compression_expansion 6.78, current_ob_retest 9.16,
regime_transition_break 9.38, current_fvg_fill 9.50, current_breaker_re_entry 10.62,
displacement_continuation 11.25, liquidity_sweep_reclaim 11.27, cross_asset_lead_lag 11.62,
structural_distance_extreme 12.66, session_open_range_break 12.80) — a 1.9x spread against the
10.9x spread in raw MFE.

Pool-wide: **11.22 % of takeable candidates have a corrected cost larger than their entire
favourable excursion** — the trade cannot win at any exit. At the frozen model it is **25.78 %**.
Mean corrected cost 0.1756 R, median 0.1059 R.

**The re-sizing caveat, priced.** Every winning cell in §2 and §5 wants a stop tighter than 1R. If
you actually place a 0.25R stop and re-size to keep the account risk constant, the return and the
R-denominated cost both scale by 1/S — the sign is invariant, the level is not. At the corrected
cost model, same size:

| stratum | cell | gross | cost | **net** |
|---|---|---:|---:|---:|
| regime_transition_break | T0.75/S0.75 | +0.0122 | 0.0488 | −0.0366 |
| volatility_compression_expansion | T0.10/S0.25 | −0.0195 | 0.0590 | −0.0784 |
| session_open_range_break | T0.50/S1.00 | −0.0139 | 0.0722 | −0.0861 |
| current_ob_retest | T8.00/S3.00 | −0.0119 | 0.1072 | −0.1192 |
| POOL | T0.75/S0.25 | −0.0367 | 0.1756 | −0.2123 |
| cross_asset_lead_lag | T3.50/S0.25 | +0.0036 | 0.2327 | −0.2291 |
| **structural_distance_extreme** | T3.00/S0.25 | **+0.0836** | **0.3426** | **−0.2590** |

The lane's best tested family result is also its most expensive, and cost wins by 4×.

---

## 7. The policy ladder — where the −0.2175 actually goes

Every rung is **R per ORIGINAL candidate** (denominator 27,658; a candidate the policy declines
books exactly 0.0 R), so the rungs are additive and directly comparable with the published figure.

| rung | n taken | gross / original | net @corrected / original |
|---|---:|---:|---:|
| **P0** as-shipped engine (fill-blind, engine exit) | 27,658 | **−0.21750** | — |
| P0b BLIND fill, declared T2/S1 | 27,658 | +0.04038 | −0.13586 |
| **P1** REAL fill, declared T2/S1 | 27,658 | **−0.20004** | −0.37627 |
| **P2** + decline `born_past_stop` | 24,142 | **−0.07345** | −0.22676 |
| P3 + decline `born_marketable` | 22,877 | −0.05976 | −0.20635 |
| **P4** P2 + pool's tested cell T0.75/S0.25 | 24,142 | **−0.03204** | −0.18534 |
| P5 P3 + tested cell | 22,877 | −0.02479 | −0.17139 |
| P6 *test half only*: per-family fitted cells | 12,720 | −0.01894 | −0.09211 |
| P6c *test half only* control: flat T2/S1 | 12,720 | −0.03647 | −0.10964 |
| P6d *test half only*: pool fitted cell | 12,720 | −0.01702 | −0.09020 |

**Attribution of the −0.2175:**

| mechanism | worth (R per original candidate) |
|---|---:|
| fill convention (blind → honest) | **+0.2404** (measured as +0.0404 → −0.2000 at T2/S1) |
| declining the already-stopped 12.72 % | **+0.1266** |
| exit geometry, best tested cell | **+0.0414** |
| declining `born_marketable` | +0.0072 |
| **residual after all four** | **−0.0248 gross / −0.1714 net** |

Adding a pre-trade cost filter (corrected cost ≤ 0.15 R, which the engine already computes) on top:

| composed policy | n taken | gross/orig | **net/orig** | gross/taken | net/taken |
|---|---:|---:|---:|---:|---:|
| takeable, declared T2/S1 | 24,142 | −0.07345 | −0.22676 | −0.0842 | −0.2598 |
| takeable, tested cell | 24,142 | −0.03204 | −0.18534 | −0.0367 | −0.2123 |
| + decline marketable | 22,877 | −0.02479 | −0.17139 | −0.0300 | −0.2072 |
| + cost ≤ 0.15 R, declared cell | 15,310 | −0.03873 | −0.07948 | −0.0700 | −0.1436 |
| + cost ≤ 0.15 R, tested cell | 15,310 | −0.01828 | **−0.05904** | −0.0330 | −0.1067 |
| cheap + `born_resting` only | 4,806 | −0.00809 | **−0.02088** | −0.0466 | −0.1201 |
| cheap + resting + LONG *(directional)* | 2,183 | −0.00355 | **−0.00943** | −0.0450 | −0.1194 |

The best composed policy removes **94.7 %** of the net deficit (from −0.3935 at w0-capture's
corrected-cost book to −0.0209 per original candidate) by trading **17.4 %** of the pool. It still
does not cross zero.

---

## 8. The exhaustive search, and the one survivor

Objective = net R/trade at corrected cost. Filters all decision-time observable (born state,
pre-trade cost, family, symbol, side, session). Fit on Jan 01–15, report Jan 16–31.

**387 fits × 180 cells = 69,660 cell evaluations. 142 positive on train. 19 positive on test.
Median shrinkage −0.101; 85.01 % of fits shrink.** Controls on the test half: flat T2/S1 net
−0.23840, pool cell T0.75/S0.25 net −0.19612.

Top survivors by test net:

| dim | stratum | cost filter | n train | n test | cell | train | **test** | test @T2/S1 | shrink |
|---|---|---|---:|---:|---|---:|---:|---:|---:|
| family_side | cross_asset_lead_lag \| LONG | ≤0.10 | 157 | 208 | T6.00/S1.00 | +0.3806 | **+0.1082** | −0.0332 | −0.2724 |
| session | moonshot_h04_05 | ≤0.10 | 117 | 177 | T1.50/S3.00 | +0.2576 | +0.0955 | −0.1321 | −0.1620 |
| born_side | born_resting \| LONG | ≤0.10 | 721 | 969 | T0.75/S3.00 | +0.2031 | +0.0585 | −0.1406 | −0.1446 |
| symbol | **XAUUSD** | ≤0.10 | 1,202 | 1,116 | **T0.75/S3.00** | +0.1615 | **+0.0575** | −0.0709 | −0.1039 |
| symbol | XAUUSD | none | 1,211 | 1,118 | T0.75/S3.00 | +0.1589 | +0.0552 | −0.0727 | −0.1037 |
| family | cross_asset_lead_lag | ≤0.10 | 254 | 387 | T6.00/S1.00 | +0.1952 | +0.0551 | −0.0473 | −0.1401 |
| family_side | liquidity_sweep_reclaim \| LONG | ≤0.10 | 354 | 438 | T6.00/S3.00 | +0.3154 | +0.0500 | +0.0197 | −0.2655 |
| family_side | current_fvg_fill \| LONG | ≤0.10 | 610 | 747 | T0.75/S3.00 | +0.1982 | +0.0440 | −0.1388 | −0.1542 |
| family_born | current_fvg_fill \| born_resting | ≤0.10 | 1,149 | 1,646 | T0.75/S3.00 | +0.1194 | +0.0065 | −0.0992 | −0.1129 |

**Every survivor shares one shape: a stop far WIDER than the declared −1R** (S = 3.00 in six of nine)
and a small target. That is the structural claim: the declared stop is inside the two-hour noise.
Note also that the shape is `LONG` in five of nine.

### XAUUSD, taken apart

Whole month, n = 2,329, at T0.75/S3.00 vs the declared T2/S1:

| | gross | **net @corrected** | t | win | days positive | 3-fold net (d1–10 / 11–20 / 21–31) | outcomes |
|---|---:|---:|---:|---:|---:|---|---|
| T0.75/S3.00 | +0.1554 | **+0.1091** | +4.545 | 75.8 % | 16 / 21 | +0.1666 / +0.1531 / +0.0290 | target 71.5 %, path-end 19.7 %, stop 8.7 % |
| declared T2/S1 | −0.0469 | −0.0932 | −3.608 | 36.3 % | 7 / 21 | −0.1016 / −0.0762 / −0.0994 | stop 56.1 %, path-end 21.2 %, target 22.6 % |

**A +0.2023 R/trade swing on 2,329 candidates from exit geometry alone**, all three folds positive,
top day 27.2 % of total. Re-sized so the 3R stop is one unit of account risk it is +0.0364 R/trade.

**But it is half a gold rally.** Split by side and by born state:

| XAUUSD stratum | n | net @shape | t | win | 2 h drift | net @declared |
|---|---:|---:|---:|---:|---:|---:|
| **LONG** | 1,141 | **+0.2967** | +9.836 | 85.0 % | **+0.4355** | −0.0621 |
| **SHORT** | 1,188 | **−0.0711** | −1.956 | 67.0 % | −0.0534 | −0.1231 |
| born_resting | 1,522 | +0.2258 | +8.278 | 81.1 % | +0.3720 | −0.1003 |
| born_at_limit | 729 | −0.0971 | −2.020 | 67.2 % | −0.1759 | −0.0568 |
| born_marketable | 78 | −0.2400 | −1.743 | 53.8 % | −0.0583 | −0.2951 |

Applying that **one** shape (chosen once, not fitted per symbol) to all 24 symbols: **1 of 24 is net
positive** — XAUUSD. The next best is XAGUSD at −0.0906. NAS100 −0.6036, ETHUSD −0.6302, SPX500
−0.4889.

---

## 9. Signal versus direction — the decisive test

Within a stratum, a market that moved by `d` adds +d to every LONG and −d to every SHORT; genuine
predictive content `s` adds +s to **both**. So `SIGNAL = (L+S)/2` is direction-neutral and
`DIRECTION = (L−S)/2` is the month.

| measure | pool LONG | pool SHORT | **SIGNAL** | t | **DIRECTION** | t |
|---|---:|---:|---:|---:|---:|---:|
| 2 h drift | +0.0614 | −0.1196 | **−0.02906** | **−1.286** | **+0.09049** | **+4.005** |
| net @T0.75/S3.00 | −0.2397 | −0.2771 | −0.25841 | −31.25 | +0.01871 | +2.263 |
| net @declared T2/S1 | −0.2450 | −0.2718 | −0.25839 | −34.12 | +0.01338 | +1.766 |

**The only statistically significant property of the January pool's paths is that the market moved.**
Across 24 symbols: 12 have positive signal, **2 have signal t > 2** (XAUUSD +0.1911 t 2.122, GER40
+0.1729 t 2.370) — exactly the count 24 looks produce by chance — while **7 have |direction| t > 2**.

Per family, direction-neutral signal on the 2 h drift:

| family | n LONG | n SHORT | drift L | drift S | **SIGNAL** | t | DIRECTION |
|---|---:|---:|---:|---:|---:|---:|---:|
| current_ob_retest | 717 | 574 | +0.2353 | −0.1358 | **+0.0497** | 1.314 | +0.1856 |
| current_fvg_fill | 2,999 | 4,144 | +0.1078 | −0.0144 | +0.0467 | 1.004 | +0.0611 |
| current_breaker_re_entry | 282 | 514 | +0.2013 | −0.1424 | +0.0294 | 0.379 | +0.1719 |
| liquidity_sweep_reclaim | 1,955 | 2,520 | +0.1541 | −0.0965 | +0.0288 | 0.657 | +0.1253 |
| regime_transition_break | 151 | 146 | +0.0326 | −0.0787 | −0.0230 | −0.651 | +0.0556 |
| cross_asset_lead_lag | 1,086 | 997 | −0.0704 | +0.0123 | −0.0290 | −0.315 | −0.0413 |
| volatility_compression_expansion | 331 | 274 | −0.0810 | −0.0667 | −0.0738 | −2.822 | −0.0071 |
| displacement_continuation | 2,194 | 2,275 | −0.0612 | −0.1655 | **−0.1134** | **−4.600** | +0.0522 |
| structural_distance_extreme | 587 | 1,406 | +0.1506 | −0.4526 | −0.1510 | −0.899 | +0.3016 |
| session_open_range_break | 488 | 499 | −0.0881 | −0.2235 | −0.1558 | −3.063 | +0.0677 |

**Not one family has positive signal at t > 1.32.** Two have significantly NEGATIVE signal —
`displacement_continuation` (−0.1134, t −4.60, n 4,469) and `session_open_range_break` (−0.1558,
t −3.06, n 987) — which are inverse-edge candidates in the CQ mould and belong to an entry lane.

---

## 9b. Pricing the inverse — measured, not inferred

A significantly negative direction-neutral signal is an edge with the sign flipped, so it was
measured rather than assumed. Restricted to the **14,911 `born_at_limit` rows** where
`entry_price` equals the decision-instant market price exactly, the inverse is unambiguously a
market order at the same price and the R path reflects exactly (`fav' = −adv`, `adv' = −fav`,
`cls' = −cls`). Costs are charged symmetrically. Mean corrected cost on this population 0.1661 R.

| family | n | cost | FORWARD net @T2/S1 | **INVERSE net @T2/S1** | t | inverse SIGNAL | t | train → test |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| volatility_compression_expansion | 605 | 0.059 | −0.1507 | **+0.0230** | 0.998 | +0.0216 | 0.919 | −0.0164 → +0.0594 |
| session_open_range_break | 987 | 0.072 | −0.1395 | **+0.0166** | 0.505 | +0.0161 | 0.489 | −0.0111 → +0.0425 |
| displacement_continuation | 4,465 | 0.093 | −0.1742 | −0.0106 | −0.661 | −0.0108 | −0.673 | −0.0270 → +0.0043 |
| regime_transition_break | 297 | 0.049 | −0.0523 | −0.0399 | −1.170 | −0.0390 | −1.144 | −0.0397 → −0.0400 |
| cross_asset_lead_lag | 2,083 | 0.233 | −0.3073 | −0.1070 | −3.519 | −0.1081 | −3.550 | −0.1372 → −0.0804 |
| liquidity_sweep_reclaim | 4,475 | 0.173 | −0.1917 | −0.1207 | −6.258 | −0.1240 | −6.420 | −0.1840 → −0.0571 |
| structural_distance_extreme | 1,993 | 0.343 | −0.4223 | −0.1511 | −4.633 | −0.1316 | −3.664 | −0.1645 → −0.1373 |
| **POOL** | **14,911** | **0.166** | **−0.2258** (t −23.2) | **−0.0730** (t −7.30) | | −0.0730 (t −7.31) | | −0.1078 → −0.0399 |

Inverting the whole `born_at_limit` population turns a −0.2258 R/trade net book into −0.0730 —
**it removes 68 % of the loss and still does not reach zero, because the cost is charged in both
directions.** The two families whose inverse is nominally positive are +0.023 and +0.017 at
t < 1.0 — below any admission standard. Even `displacement_continuation`, with the pool's strongest
negative signal (−0.1134 at t −4.60 on the 2-hour drift), inverts to only **−0.0106** at the
declared contract: its 0.0927 R cost plus the stop noise consume the whole signal. Riding its
inverse to the wall with no stop at all would gross +0.1143 against 0.0927 of cost — **+0.0216
R/trade, the entire prize in the largest inverse-signal family in the pool.**

At wider targets the picture does not change: inverse at T3/S1 gives session_open_range_break
+0.0347 (t 0.97) and volatility_compression_expansion +0.0220 (t 0.96); everything else is negative.

**This is the finding that binds the lane.** Cost — not exit geometry, not direction, not the
inverse — is what stands between this pool and zero. Mean corrected cost is **0.1756 R/trade**
against a best-case direction-neutral signal of **0.11–0.15 R** in the families that have one at
all, and against a total exit-geometry lever of **0.0414 R**.

---

## 10. Verdict

**Best exit contract on this pool:** no target, 1R stop, **0.25 R trailing stop** — −0.01904 R/trade
over the takeable population (train −0.01441 → test −0.02320). Best *fixed* cell: **T0.75 / S0.25**,
−0.03204 R per original candidate, tested with +0.0007 shrinkage.

**How much of the −0.2175 it recovers:** exit geometry alone is worth **+0.0414 R per original
candidate — 19.0 %**. Composed with the two decision-time-observable declines it reaches −0.0248
gross per original candidate, i.e. **88.6 % of the gross deficit removed**, and with a pre-trade
cost filter **94.7 % of the corrected-cost net deficit**. **None of it crosses zero.**

**And the reason it cannot.** The paths are martingales: mean MFE +1.8956 against mean MAE −2.0153,
mark-to-market drift of −0.04 to −0.10 R at every horizon from 1 to 120 minutes, and 275 different
exit contracts confined to a 0.0887 R band. Direction-neutral SIGNAL is **−0.0291 R (t −1.286)**
while DIRECTION is **+0.0905 R (t +4.005)**.

**The binding constraint is cost, and the second is the entry — never the exit.** Mean corrected
cost 0.1756 R/trade against a total exit-geometry lever of 0.0414 R and a best-family
direction-neutral signal of 0.11–0.15 R. Inverting the whole `born_at_limit` population removes
68 % of its loss and still lands at −0.0730 because the spread is charged either way (§9b).

**The capture gap is an entry problem, not an exit problem.** Two mechanisms are worth carrying
forward, both entry-side and both decision-time observable: `born_marketable` orders (chasing a
level the market has already passed) carry −0.2586 R of drift on 1,265 candidates, and
`born_resting` orders (a limit the market came back to) carry +0.0806 R on 7,949. And two families
carry significantly *negative* direction-neutral signal — `displacement_continuation` at t −4.60 on
4,469 candidates is the largest inverse-edge candidate in the pool and is 5.6× the size of the
family CQ built its inverted-breaker candidate from.

**Caveats to carry.** (1) Everything here is one month and dies at a hard 2-hour wall; 32.5 % of
trades at the declared contract never resolve inside it. (2) The XAUUSD result is one instrument out
of 24 and half of it is a gold rally — it needs February and March before anyone believes it.
(3) Every tested best cell was selected over a 180-cell grid; the honest shrinkage distribution is
median −0.101 with 85 % of fits shrinking. (4) `candidate_id` is not a primary key (W0-F1) — all
joins here use `(candidate_id, decision_time_utc)`.

---

## Artifacts

| file | what |
|---|---|
| `l1_TOUCH_INDEX_V1.jsonl.gz` | the substrate — first-touch indices, 18 fav × 10 adv × 3 fill conventions |
| `l1_lib.py` | loader + the exact `cell()` walk every pass uses |
| `l1_build_touch_index.py` | builds the substrate from `w0_R_PATHS` + `w0cap2_DECISION_ANCHOR` |
| `l1_surface.py` / `l1_SURFACE_V1.json` | the 60-cell money surface × 3 populations × 3 conventions |
| `l1_excursion.py` / `l1_EXCURSION_V1.json` | MFE/MAE distributions, ladders, extended grid, time-to-outcome |
| `l1_variants.py` / `l1_VARIANTS_V1.json` | 95 trail / BE / partial / time-stop variants |
| `l1_conditional.py` / `l1_CONDITIONAL_V1.json` | 14 stratifications with asymmetry and best cell |
| `l1_drift.py` / `l1_DRIFT_V1.json` | mark-to-market drift at 12 horizons per stratum |
| `l1_split.py` / `l1_SPLIT_V1.json` | fit Jan 01–15 → test Jan 16–31, plus drift intersections |
| `l1_final.py` / `l1_FINAL_V1.json` | the policy ladder, per-family detail, re-sizing caveat |
| `l1_close.py` / `l1_CLOSE_V1.json` | variant split test, cost-vs-geometry, composed policies |
| `l1_scan.py` / `l1_SCAN_V1.json` | 387 fits × 180 cells, fitted and tested |
| `l1_verify.py` / `l1_VERIFY_V1.json` | survivor census, day concentration, 3-fold |
| `l1_gold.py` / `l1_GOLD_V1.json` | XAUUSD decomposition + one fixed shape across 24 symbols |
| `l1_signal.py` / `l1_SIGNAL_V1.json` | signal vs direction decomposition |
| `l1_inverse.py` / `l1_INVERSE_V1.json` | the inverse of every family, priced on reflected paths |
| `l1_RESULT.json` | all of the above consolidated |
