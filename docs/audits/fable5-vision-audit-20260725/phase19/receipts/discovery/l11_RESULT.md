# Lane l11 — the exit contract this pool actually deserves

**Population** TAKEABLE = the 24,142 of 27,658 January candidates whose stop was not already
breached at the decision instant (w0-capture `born_past_stop`, zero look-ahead).
**Fill** REAL — fill at bar 0 when the order was born at-or-through the market
(`mkt_r_prev_close <= 0`), otherwise the first bar with `adv <= 0`. **Tie inside a bar** the STOP.
**Horizon** hard 2 h (≤120 M1 bars). **Sizing** position size held fixed, so costs are constant in
R across contracts unless the table says otherwise. Every number below is gross-of-cost unless
labelled `net`; `net73` = `spread_r/7.3 + commission_r + expected_slippage_r + swap_cost_r`.

**Engine validation.** `l11_walk.Engine` reproduces l1 exactly at the incumbent cell: T2/S1 on
TAKEABLE gives gross **-0.084151**, 12,156 stops, 4,127 targets, 7,856 marks, 3 no-fills —
identical to `l1_RESULT.json → VARIANTS.T2.0_S1.0` and to its `TIME_TO_OUTCOME` counts. Nothing
here rests on a re-derivation of the substrate.

---

## 0. Headline

**On the takeable pool the incumbent 2R/-1R exit contract is worth -0.0455 R/trade against having
no exit contract at all** (-0.084151 vs -0.038647, n=24,142). It is dominated in **16 of 16**
whole-month convention cells (`L11_CONFIRM_V1.json`) and in **14 of 16** cells once the test half is
scored separately (`L11_MINIMAX_V1.json`; the two exceptions are both first-emission × test-window ×
zero-stop-slippage). The reason is an identity, not a search result: for every one of 13
favourable and 9 adverse levels, `E[wall mark | first touch of L] > L` — the pool CONTINUES
through every level in both directions, so **every fixed exit level on either side is
value-destroying**. The contract only looks necessary on the population that includes the 3,516
`born_past_stop` rows, where the same stop is worth **+0.958 R/trade**.

The prescription does not survive deduplication intact: on first-emission rows only it shrinks to
-0.0064 over the month and **reverses to +0.0098 in the test half**. So the honest bound on
"delete the exit contract" is **+0.006 … +0.074 R/trade**, and the large end of that range is
pseudo-replication.

---

## 1. The shape of the excursion (lane item 1)

Post-FILL clock, no exit logic anywhere. `L11_SHAPE_V1.json`.

### 1.1 The pool's mark-to-market path

| t (bars after fill) | 1 | 3 | 10 | 20 | 30 | 45 | 60 | 90 | 119 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mean mark R | -0.0924 | -0.1002 | -0.0856 | -0.0981 | -0.0647 | -0.0744 | -0.0630 | -0.0651 | -0.0889 |
| `E[wall − r(t)]` | +0.0538 | +0.0614 | +0.0473 | +0.0591 | +0.0242 | +0.0263 | +0.0073 | -0.0054 | 0 |
| its t-stat | 2.37 | 2.74 | 2.14 | 2.74 | 1.15 | 1.35 | **0.42** | -0.41 | — |

**The entire loss is booked in the first minute.** The mark is -0.0924 R one bar after the fill and
-0.0386 R at the wall two hours later: holding the remaining 119 minutes *recovers* +0.054 R. No
exit contract can address a loss that is already complete before the first bar closes.

**Holding becomes pure variance at bar ~60.** `E[wall − r(t)]` carries t = 2.4–2.7 up to bar 20,
falls through 1.15 at bar 30, and is **+0.0073 ± 0.0175 (t = 0.42)** at bar 60 and
-0.0054 ± 0.0131 at bar 90. Bar 60 is the pool's variance onset; it is family-specific (table 1.3).

### 1.2 Where the trade peaks and what is left of it

Peak bar (running favourable extreme, post-fill): mean 48.2, **median 41**, p25 10, p75 84, p90 110.
17.98 % peak within 5 bars, 29.63 % within 15, 42.33 % within 30, and **21.20 % peak in the last
10 % of the window** — i.e. a fifth of paths are still making new highs when the wall arrives.

Give-back MFE − r_end: mean 1.934 R, **median 1.114 R**.
**Fraction of its own MFE the median trade keeps: 2.76 %.** The median path reaches +1.008 R and
marks out at +0.028 of it. That is the single most striking number in the shape pass and it is what
makes a naive reading say "capture the excursion" — §2 shows why that reading is wrong.

50.24 % of paths touch +1R, 54.28 % touch -1R.

### 1.3 Per family

| family | n | r_end | MFE med | MAE med | peak bar med | % of MFE kept (med) | touch +1R | touch -1R | variance onset |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| POOL | 24,139 | -0.0386 | 1.008 | -1.130 | 41 | 2.8 % | 50.2 % | 54.3 % | bar 60 |
| cross_asset_lead_lag | 2,083 | -0.0308 | 1.705 | -1.955 | 49 | 3.1 % | 67.1 % | 72.2 % | bar 1 |
| current_breaker_re_entry | 796 | -0.0207 | 0.899 | -1.132 | 30 | 0.0 % | 46.0 % | 55.8 % | bar 10 |
| current_fvg_fill | 7,143 | **+0.0369** | 1.049 | -1.193 | 31 | 4.6 % | 51.2 % | 56.5 % | bar 75 |
| current_ob_retest | 1,291 | **+0.0703** | 0.690 | -0.693 | 26 | 13.3 % | 36.3 % | 37.1 % | bar 105 |
| displacement_continuation | 4,469 | -0.1143 | 0.712 | -0.855 | 46 | -6.1 % | 37.4 % | 43.3 % | never |
| liquidity_sweep_reclaim | 4,475 | **+0.0130** | 1.246 | -1.268 | 54 | 7.3 % | 57.7 % | 58.3 % | bar 60 |
| regime_transition_break | 297 | -0.0221 | 0.314 | -0.334 | 45 | 10.2 % | 10.4 % | 9.8 % | bar 1 |
| session_open_range_break | 987 | -0.1566 | 0.659 | -0.735 | 49 | -6.3 % | 32.9 % | 37.2 % | bar 90 |
| structural_distance_extreme | 1,993 | -0.2749 | 2.978 | -3.140 | 50 | 2.5 % | 79.1 % | 81.7 % | bar 1 |
| volatility_compression_expansion | 605 | -0.0745 | 0.258 | -0.350 | 49 | -6.9 % | 7.9 % | 11.6 % | never |

Three families mark out **positive** at the wall with no exit management whatsoever
(`current_ob_retest` +0.0703, `current_fvg_fill` +0.0369, `liquidity_sweep_reclaim` +0.0130).
`structural_distance_extreme` has 2.98 R of median MFE against -0.2749 at the wall — the largest
excursion in the pool and the worst terminal mark.

### 1.4 By order birth

| born | n | r_end at wall | % of MFE kept (med) |
|---|---:|---:|---:|
| `born_resting` (a genuine resting limit) | 7,946 | **+0.0806** | 5.4 % |
| `born_at_limit` (entry == decision-instant market) | 14,911 | -0.0859 | 0.4 % |
| `born_marketable` | 1,265 | -0.2586 | 8.2 % |

The 28.8 % of the pool that is a real resting limit order ends **positive** at the wall; the 54 % that
is an at-market order ends negative. This is an entry-mechanism split, reported here because it
bounds what any exit contract is working with.

---

## 2. The analytic derivation (lane item 2)

`L11_ANALYTIC_V1.json`. An exit at level L is worth, per candidate, exactly

```
value(L) = P(first touch of L) x ( L − E[ wall mark | first touch of L ] )
```

against the do-nothing baseline. **This is an identity, and it is verified to 0.00000 R** — twelve
level-by-level predictions checked against the engine, `max_abs_err = 0.000000`
(`L11_CONTRACTS_V1.json → ANALYTIC_VERIFICATION`). Contract design on this pool is therefore
arithmetic, not search.

### 2.1 Every level, both sides, is negative

| level | P(touch) | E[wall \| touch] | delta/touch | value/candidate | med touch bar |
|---|---:|---:|---:|---:|---:|
| +0.25 | 0.8106 | +0.3408 | -0.0908 | -0.0736 | 4 |
| +0.50 | 0.6901 | +0.5900 | -0.0900 | -0.0621 | 10 |
| +1.00 | 0.5024 | +1.1029 | -0.1029 | -0.0517 | 23 |
| +1.50 | 0.3756 | +1.5990 | -0.0990 | -0.0372 | 30 |
| **+2.00 (incumbent)** | 0.2834 | **+2.1458** | **-0.1458** | **-0.0413** | 36 |
| +3.00 | 0.1770 | +3.2454 | -0.2454 | -0.0435 | 44 |
| +5.00 | 0.0866 | +5.1334 | -0.1333 | -0.0115 | 53 |
| +6.00 | 0.0630 | +6.0208 | -0.0208 | -0.0013 | 59 |
| -0.25 | 0.8740 | -0.2492 | -0.0008 | **-0.0007** | 2 |
| -0.50 | 0.7498 | -0.4556 | -0.0445 | -0.0333 | 6 |
| **-1.00 (incumbent)** | 0.5428 | **-0.9290** | **-0.0710** | **-0.0385** | 17 |
| -1.50 | 0.4023 | -1.4480 | -0.0520 | -0.0209 | 25 |
| -2.00 | 0.3103 | -1.9284 | -0.0717 | -0.0222 | 31 |
| -3.00 | 0.1924 | -2.8720 | -0.1280 | -0.0246 | 41 |

`E[wall | touch] > L` at **22 of 22 levels**. Touching +2R predicts a wall mark of +2.146; taking the
2R target throws 0.146 R away on 28.34 % of paths. Touching -1R predicts -0.929; stopping there
throws 0.071 R away on 54.28 %. The one level that is approximately free is **-0.25R
(value -0.0007)** — a stop four times tighter than the incumbent is expectation-neutral.

This is the mechanism behind §1.2's "the median trade keeps 2.8 % of its MFE". The give-back is real
and it is **not capturable**, because reaching a level is a *positive* predictor of going further,
not a signal to leave.

### 2.2 The sign flips with elapsed time

| level | early (bars 1-10) | mid (11-45) | late (46+) |
|---|---|---|---|
| +1.00 | n 3,872, **-0.3306** | n 4,945, **+0.0488** | n 3,311, -0.0632 |
| +2.00 | n 1,126, -0.4859 | n 2,962, -0.1207 | n 2,754, -0.0337 |
| +3.00 | n 453, -0.3013 | n 1,769, -0.3742 | n 2,052, -0.1221 |
| -0.50 | n 10,630, -0.0664 | n 5,213, -0.0598 | n 2,259, **+0.0944** |
| -1.00 | n 5,094, **-0.1545** | n 4,965, -0.0724 | n 3,045, **+0.0712** |
| -2.00 | n 1,709, -0.0189 | n 3,001, -0.1200 | n 2,782, -0.0519 |

**Early moves continue; late moves are exhausted.** Part of the late-bucket effect is mechanical
(a level touched at bar 100 has 20 bars left to continue), but the mid-bucket +0.0488 at +1R and the
late-bucket +0.0712 at -1R are sign changes, not attenuations. This is the one place where a
*time-conditional* exit has an analytic case, and §3.4 prices it.

### 2.3 What the whole battery measures (n=24,142, `L11_CONTRACTS_V1.json`)

| contract | gross | net73 | t | stops | targets | marks |
|---|---:|---:|---:|---:|---:|---:|
| **TIMESTOP_90** (no target, no stop, mark at bar 90) | **-0.03090** | -0.20653 | -1.52 | 0 | 0 | 24,139 |
| HOLD_TO_WALL | -0.03865 | -0.21427 | -1.69 | 0 | 0 | 24,139 |
| stop_only S0.25 | -0.03933 | -0.21495 | -6.25 | 21,101 | 0 | 3,038 |
| target_only T5 | -0.05019 | -0.22581 | -2.61 | 0 | 2,090 | 22,049 |
| trail arm2.0/gap1.0 + S1 (lagged, honest) | -0.06010 | -0.23573 | -7.17 | — | — | — |
| stop_only S1 | -0.07717 | -0.25279 | -7.10 | 13,104 | 0 | 11,035 |
| BE at 2.0 + S1, no target | -0.07648 | -0.23... | -7.36 | — | — | — |
| partial 1.0R x0.5 + S1, no target | -0.07875 | — | -10.62 | — | — | — |
| target_only T2 | -0.07996 | -0.25558 | -4.97 | 0 | 6,842 | 17,297 |
| **INCUMBENT T2/S1** | **-0.08415** | **-0.25977** | -11.42 | 12,156 | 4,127 | 7,856 |
| BE at 0.25 + S1, no target | -0.09734 | — | -13.74 | — | — | — |
| target_only T0.5 | -0.10074 | -0.27637 | -10.08 | 0 | 16,661 | 7,478 |

Ladders in full: targets T0.5 -0.1007 / T1.0 -0.0903 / T1.5 -0.0758 / T2 -0.0800 / T3 -0.0821 /
T5 -0.0502; stops S0.25 -0.0393 / S0.5 -0.0720 / S1 -0.0772 / S1.5 -0.0596 / S2 -0.0609 /
S3 -0.0633; pure time stops (no target, no stop) at bars 30 / 45 / 60 / **90** / 120 =
-0.0595 / -0.0550 / -0.0446 / **-0.0309** / -0.0386.

**Trailing, break-even and scale-out are all value-destroying without exception.** Best trail
-0.0601, best BE -0.0765, best partial -0.0788, against -0.0386 for doing nothing. Moving the stop
to break-even at +0.25R is the worst single idea tested (-0.0973), which the drift surface predicts:
`E[wall − r(t)]` is **positive** for every negative mark bucket at every t (+0.361 at t1 for
r < -0.75R, +0.198 at t20, +0.114 at t60), so protecting a small gain by exiting on a pullback
sells exactly the state with the best continuation.

### 2.4 Limb decomposition

target limb alone -0.0413, stop limb alone -0.0385, sum -0.0798, joint -0.0455 (the +0.0343
difference is the interaction — a path stopped first never reaches its target). Both limbs of the
incumbent contract are independently negative.

---

## 3. Per family (lane item 3)

### 3.1 What the shared contract costs each family — whole month, `L11_FAMILY_LIMBS_V1.json`

| family | n | INCUMBENT | HOLD | target-only | stop-only | **inc − hold** | best − inc |
|---|---:|---:|---:|---:|---:|---:|---:|
| POOL | 24,142 | -0.0842 | -0.0386 | -0.0800 | -0.0772 | **-0.0455** | +0.0532 |
| current_fvg_fill | 7,145 | -0.1391 | +0.0369 | -0.0368 | -0.1468 | **-0.1760** | +0.1760 |
| current_ob_retest | 1,292 | -0.0546 | +0.0702 | +0.0537 | -0.0454 | **-0.1248** | +0.1248 |
| current_breaker_re_entry | 796 | -0.1028 | -0.0207 | -0.0487 | -0.0902 | -0.0821 | +0.1126 |
| cross_asset_lead_lag | 2,083 | -0.0746 | -0.0308 | -0.1545 | -0.0521 | -0.0438 | +0.0438 |
| liquidity_sweep_reclaim | 4,475 | -0.0191 | +0.0130 | -0.0208 | **+0.0162** | -0.0320 | +0.0423 |
| volatility_compression_expansion | 605 | -0.0918 | -0.0745 | -0.0816 | -0.0841 | -0.0173 | +0.0446 |
| regime_transition_break | 297 | -0.0035 | -0.0221 | -0.0111 | -0.0145 | **+0.0186** | +0.0000 |
| displacement_continuation | 4,469 | -0.0812 | -0.1143 | -0.1139 | -0.0797 | **+0.0331** | +0.0043 |
| session_open_range_break | 987 | -0.0673 | -0.1566 | -0.1691 | -0.0576 | **+0.0893** | +0.0097 |
| structural_distance_extreme | 1,993 | -0.0797 | -0.2749 | -0.2781 | -0.0899 | **+0.1952** | +0.0181 |

**Six families are hurt by the shared contract and four are helped, over a 0.371 R/trade span**
(-0.1760 to +0.1952). One geometry for ten families is not a compromise; it is simultaneously far too
tight for `current_fvg_fill` and the only thing keeping `structural_distance_extreme` alive.
`liquidity_sweep_reclaim` is the one family whose stop-only contract is gross-positive (+0.0162).

In-sample value of per-family choice over the incumbent, weighted by n: **+0.0779 R/trade**; over the
best shared contract (TIMESTOP_90, +0.0532): **+0.0247 R/trade**.

### 3.2 Out of sample — designed on days 01-15, read on days 16-31

`L11_FAMILY_V1.json`. DESIGNED = the two analytic level choices from §2 taken on TRAIN days only
(2 free parameters per family). FITTED = argmax over a 3,840-cell contract space on TRAIN.

| test-window portfolio (n = 12,720) | gross | net73 |
|---|---:|---:|
| shared INCUMBENT T2/S1 | -0.07930 | -0.23839 |
| shared HOLD | -0.01713 | -0.17623 |
| shared TIMESTOP_90 | -0.01140 | — |
| **per-family DESIGNED** | **+0.01298** | -0.14612 |
| per-family FITTED (3,840-cell argmax) | +0.00390 | -0.15519 |

**+0.0923 R/trade over the shared incumbent, out of fit, and +0.0301 over the best shared
alternative.** DESIGNED beats FITTED by 0.0091 — the 3,840-cell search overfits and the 2-parameter
analytic design does not.

Per family on TEST:

| family | n_train | n_test | DESIGNED spec | inc TEST | hold TEST | **DESIGNED TEST** | net73 |
|---|---:|---:|---|---:|---:|---:|---:|
| cross_asset_lead_lag | 975 | 1,108 | no target / S0.25 | -0.0566 | +0.0501 | **+0.0357** | -0.1744 |
| current_breaker_re_entry | 309 | 487 | T0.25 / S0.25 | -0.0513 | +0.1599 | -0.1006 | -0.2377 |
| current_fvg_fill | 3,190 | 3,955 | T6.00 / no stop | -0.1166 | +0.1449 | **+0.0848** | -0.1010 |
| current_ob_retest | 659 | 633 | no target / no stop | -0.1297 | -0.0608 | -0.0608 | -0.1526 |
| displacement_continuation | 2,136 | 2,333 | T0.25 / S0.25 | -0.0687 | -0.0910 | -0.0339 | -0.1204 |
| liquidity_sweep_reclaim | 2,242 | 2,233 | T1.75 / S1.50 | -0.0317 | +0.0084 | -0.0532 | -0.2111 |
| regime_transition_break | 130 | 167 | T0.75 / S0.75 | -0.0044 | +0.0024 | +0.0014 | -0.0437 |
| session_open_range_break | 476 | 511 | T0.50 / S0.25 | -0.0626 | -0.2400 | -0.0244 | -0.0932 |
| structural_distance_extreme | 1,015 | 978 | T6.00 / S0.25 | -0.0780 | -0.5476 | **+0.1053** | -0.2187 |
| volatility_compression_expansion | 290 | 315 | T0.50 / S0.25 | -0.1190 | -0.1097 | -0.0481 | -0.1037 |

### 3.3 Family conditioning is real; the positive LEVEL is not

`L11_ROBUST_V1.json`, five attacks on the +0.01298:

| attack | result | verdict |
|---|---|---|
| **label permutation** (400x, shuffle family labels, re-derive, re-read) | observed +0.01298 vs null mean **-0.04496**, sd 0.01599, p95 -0.01899, **p = 0/400** | **SURVIVES.** True family conditioning is worth **+0.0579 R/trade over a shuffled null**, and the design procedure applied to random groups *loses* 0.045. |
| **deduplication** (first emission only, W0-F1) | +0.01298 → **-0.03907** (Δ **-0.05205**), n 12,720 → 9,494 | **FAILS.** The positive level is pseudo-replication. |
| **day bootstrap** (11 test days, 4,000 resamples) | ci05 **-0.03083**, ci50 +0.01472, ci95 +0.05716; 70.0 % of resamples positive; 7/11 days positive | **INCONCLUSIVE.** |
| **stop-fill slippage** | 0R +0.01298 / 0.02R +0.00495 / **0.05R -0.00709** / 0.10R -0.02716 / 0.20R -0.06729 | **FAILS at 0.05 R.** |
| **strict fill** (no bar-0 assumption for anyone) | -0.02420 (Δ -0.03717) | **FAILS.** |

The slippage failure is not a technicality: seven of the ten DESIGNED stops are **0.25 R**, and the
pool's truthed round-trip cost is **0.1756 R mean** with the spread alone at 0.0773 R mean. A 0.25 R
stop is a level the cost model eats 20.7 % of the time (`share_rows_total_cost >= 0.25R = 0.2066`).

### 3.4 The time-conditional contract §2.2 pointed at does not survive

Arming both limbs at bar G (grace period), after the no-time-travel fix of §5.1:
G1 -0.0772, G5 -0.0692, G10 -0.0665, G15 -0.0667, G20 -0.0658, G30 -0.0561, G45 -0.0636,
G60 -0.0549 (stop-only, S1). Every grace period is better than arming immediately and **every one is
still worse than never arming at all** (-0.0386). Arming the *target* late is monotonically worse:
G1 -0.0800 → G45 -0.2108. The §2.2 sign flip is real in the conditional table and is not worth a
contract.

---

## 4. Sensitivity (lane item 4)

### 4.1 The invariance grid — `L11_CONFIRM_V1.json`, 24 cells

`incumbent − hold` on the 16 takeable **whole-month** cells spans **-0.0064 … -0.0740** and is
negative in all 16 (smallest gap: first-emission + real fill + no slippage; largest: strict fill +
0.05 R slippage). Scoring the test half separately (§9) flips 2 of 16.
The best contract in each cell is TIMESTOP_90, HOLD_TO_WALL, TIMESTOP_90_S3 or STOP_ONLY_S1, and
`best − incumbent` spans **+0.0140 … +0.0784**.

**On the 8 cells that include `born_past_stop`, the sign inverts: `incumbent − hold` = +0.9264 …
+0.9576.** The 12.7 % of rows that were never takeable are worth +0.96 R/trade to the stop, because
they book a bounded -1.00 R with it and -1.16 R without it. Any exit-geometry conclusion drawn on the
full pool is a conclusion about that artifact.

Window instability, stated plainly: on first-emission TEST rows the incumbent is **better** than
holding (-0.07519 vs -0.08501, i.e. `inc − hold` = **+0.0098**), while on first-emission whole-month
rows it is worse (-0.0064). Dedup collapses the effect to noise.

### 4.2 Cost — no exit contract closes the gap

Net of the DESIGNED portfolio (gross +0.01298) by cost model:

| spread divisor | ×0 slip | ×1 slip | ×2 slip | ×3 slip |
|---|---:|---:|---:|---:|
| 1.0 (frozen) | — | **-0.56935** | — | — |
| 2.0 | — | -0.32415 | — | — |
| 4.0 | — | -0.20155 | — | — |
| 7.3 (truthed) | -0.12613 | **-0.14613** | -0.16613 | -0.18613 |
| 8.5 | — | -0.13664 | — | — |
| ∞ (spread free) | **-0.05895** | -0.07895 | — | — |

**At zero spread and zero slippage the best exit contract measured here is still -0.059 R/trade net**,
because commission (0.0652 R mean) + swap (0.0137 R mean) = 0.0789 R against a best-case gross of
+0.0130. Exit design cannot pay this pool's cost floor.

### 4.3 The cost-to-risk ratio is the real geometry constraint

Costs are charged per trade; risk is defined by the stop. Tightening the stop therefore multiplies
the toll. `L11_CONFIRM_V1.json → FIXED_RISK_FRAMING` (risk unit = the contract's own stop, or the
realised 1st-percentile loss when there is none):

| contract | risk unit (R) | gross, fixed size | gross / unit risk | net / unit risk | cost / unit risk |
|---|---:|---:|---:|---:|---:|
| INCUMBENT T2/S1 | 1.000 | -0.08415 | -0.08415 | **-0.25977** | **17.6 %** |
| STOP_ONLY S1 | 1.000 | -0.07717 | -0.07717 | -0.25279 | 17.6 % |
| WIDE T5/S3 | 3.000 | -0.06367 | -0.02122 | -0.07976 | 5.9 % |
| TIMESTOP_90_S3 | 3.000 | -0.03789 | -0.01263 | -0.07117 | 5.9 % |
| TIMESTOP_90 | 8.495 | -0.03090 | -0.00364 | -0.02431 | 2.1 % |
| HOLD_TO_WALL | 9.498 | -0.03865 | **-0.00407** | **-0.02256** | **1.8 %** |

**At the incumbent's geometry the round-trip cost is 17.6 % of the risk taken** (66.2 % under the
frozen cost model). Per unit of risk actually committed, holding is **11.5× less bad** than the
incumbent. To bring the toll to 5 % the stop distance must be ≈ 3.5× wider than the pool's current
geometry — which is the same direction as l1's independent finding that wide-stop cells dominate,
reached from a different quantity.

This also disposes of §2.1's "-0.25R is a free stop": free at fixed size, and a **70 % toll** at
fixed risk (0.1756 / 0.25).

---

## 5. Two engine defects found and priced

### 5.1 Time-travel on a late-armed or tightened stop — mine, found and fixed

A stop that is armed or tightened onto a price the market has **already** passed is a market order;
it fills at the last knowable price, not at its level. Booking the level instead manufactured, on
this pool:

| contract | before fix | after fix | fiction |
|---|---:|---:|---:|
| stop S1 armed at bar 60, no target | **+0.30664** | -0.05487 | **+0.36151** |
| stop S1 armed at bar 45 | +0.23915 | -0.06358 | +0.30273 |
| trail arm 0.25 / gap 0.25 + S1 | -0.01903 | -0.06693 | +0.04790 |

The first row would have been a lane headline: a positive-gross, positive-net contract at t = 19.7.
It is entirely an artifact of booking a stop 40 minutes in the past. Fixed at
`l11_walk.py:109-122`; the fix is unreachable for a continuously-live stop (`d[t-1] <= cls[t-1]`
would already have fired), which is why the validated T2/S1 and HOLD baselines are byte-unchanged.

### 5.2 The intrabar trail convention is not a one-signed bias — cross-check with the estate

`src/research_infra/walkforward/exits.py:395-406` documents its own version (B613): the default
`trail_lag_extremes=False` arms off bar *j*'s high and fills off bar *j*'s low, and under it
**95.8 % of `asian_fade`'s trail exits land on the first bar after entry, carrying the whole of a
+0.759 R/trade apparent improvement**. My engine is structurally the *lagged* variant (the trail set
at bar *t* can only fire at *t+1*), so all trail numbers above are the honest ones. Running the
optimistic convention on this pool for comparison (`L11_TRAIL_CONVENTION_V1.json`):

| trail | lagged (honest) | same-bar (optimistic) | bias | share of stop exits on bar 1 |
|---|---:|---:|---:|---:|
| arm 0.25 / gap 0.25 | -0.06693 | -0.08743 | **-0.02050** | 22.0 % |
| arm 0.50 / gap 0.25 | -0.06277 | -0.08184 | -0.01907 | 15.7 % |
| arm 1.00 / gap 0.50 | -0.06255 | -0.09857 | -0.03603 | 10.2 % |
| arm 2.00 / gap 1.00 | -0.06010 | -0.08888 | -0.02877 | 8.6 % |

**The bias runs the other way here.** On a mean-reverting population the optimistic convention
flatters (+0.759 on `asian_fade`); on this continuation population it *penalises* by 0.019–0.036
R/trade. Either way it moves the number by more than the exit-design effect being measured, so no
trail result from either engine is interpretable without the convention stated.

**One gap the estate's walker still has.** `exits.py` applies a gap-aware fill (`lvl = min(lvl, b.o)`)
**only** in the lagged trail branch, at `:405`. The plain stop (`:375`, `:430`), the target (`:377`,
`:432`) and the break-even move after a partial (`:382-383`, `:437-438`) all book their level with no
open-price clamp. The BE-after-partial case is exactly my §5.1 defect one bar later, and
`partial_be_runner` is the live contract of `metals_core`, `metals_softband`, `metals_ob_micro` and
`energy_agri` — two of which are armed. On M1 bars the effect here is small; on the H4/D1 bars the
estate walks it is not bounded by anything measured. **Not quantified on estate data by this lane** —
flagged with file:line for whoever owns that walker.

---

## 6. Cross-check with the estate's existing exit work (lane item 5)

**T1's Screen B — "the exit-shape family is measured EMPTY on this pool"**
(`forensic/t1/T1_SCREENS_V1.md:49-58`). Pool-wide: base -0.199; stop ×1.5 -0.179, ×2 -0.166,
×3 -0.149; target 1.5R -0.205, 3R -0.236, 5R -0.295; conclusion "the 2R target is locally optimal
among {1.5, 2, 3, 5}", "exit-shape deltas are ±0.05 R".

*Where I agree.* The magnitude. My best-minus-incumbent is +0.053 pool-wide and +0.014 … +0.078
across conventions — the same ±0.05 R order, and an order of magnitude below T1's fill-axis gap.
And no pool-wide cell is net-positive at any cost model, which T1 also concluded.

*Where I differ, and why.* (a) T1 measured on the **fill-free** contract over all 27,658 rows
including the 3,516 `born_past_stop` — the population where a stop is worth **+0.96 R/trade** (§4.1).
That is why T1's cells improve monotonically with a wider stop and never approach zero: they are
measuring the artifact's containment, not exit geometry. (b) T1's cell set has no **do-nothing**
baseline; every cell carries both a stop and a target, so the grid is bounded below by the assumption
that both limbs are wanted. The cell that wins is the empty one. (c) "The 2R target is locally
optimal among {1.5, 2, 3, 5}" does not reproduce on the takeable, fill-honest population: target-only
gives T1.5 -0.0758, **T2 -0.0800**, T3 -0.0821, T5 -0.0502 — 2R is a local *minimum* between 1.5 and
5, and the ladder improves monotonically toward no target at all. The "driftless-barrier" reading is
refuted by the identity in §2.1: the pool is not driftless conditional on an excursion, it continues.
(d) T1's prescription "exit shape is empty" understates the finding by one sign: the exit contract is
not neutral, it is **actively costing 0.0455 R/trade** on the takeable pool, and deleting it is free.

**`SLEEVE_EXIT_PROFILES` / `time_stop_bars`.** The armed sleeves declare
`crypto` and `sub_xvol_pullback` at `time_stop_bars=1280` M15 bars = **320 hours**
(`src/components/ultimate_book/execution_packets.py:80,84`); `energy_agri` runs
`partial_be_runner` with `trigger_r=2.0`, `final_target_r=4.0` (`:93`). This pool's entire horizon
is **2 hours** — `REPAIRED_PENDING_EXPIRY_MINUTES = 120`
(`src/research_infra/v4_timewarp_simulated_live_research_loop.py:378`), passed as the oracle's
`expiry` at `:63902`. **The ratio is 160×.** Nothing in this receipt transfers to a live sleeve's exit
contract; it describes the diagnostic pool's own pending-order window. What *does* transfer is the
method (§2's identity), the cost-to-risk arithmetic (§4.3) and the two engine defects (§5).

The direction agrees with AQ's `time_stop_bars` repair and with AD's finding that exit geometry is
worth more than eliminating carry: on this pool too the largest single exit lever (+0.053 shared,
+0.092 per-family out of fit) is geometry, not holding cost — swap is 0.0137 R of a 0.1756 R bill
(7.8 %).

Corroboration from w0-capture, not re-derived here: continuing marked trades past the 2 h wall for
24 h resolves 41.31 % at target and improves the mark from +0.2551 to +0.3030 — continuation past
the wall, the same sign as §2.1.

---

## 7. The contract this pool deserves, stated as a design

1. **Delete the shared 2R/-1R contract.** It is dominated in 16/16 takeable convention cells, by
   -0.0455 R/trade at the pool's shipped composition (bound: -0.0064 … -0.0740; the large end is
   pseudo-replication).
2. **The replacement is a pure time stop at ~90 minutes with no target and no stop** (-0.0309 vs
   -0.0842), or a 3R stop if a bound is mandatory (TIMESTOP_90_S3, -0.0379, and 5.9 % cost-to-risk
   instead of 17.6 %).
3. **Geometry must be per family, and the family axis is real** (permutation p = 0/400, +0.0579
   R/trade over a shuffled null). Six families are hurt by the shared contract and four helped, over
   a 0.371 R/trade span.
4. **Do not tighten the stop.** Every tight-stop cell that looks good at fixed size is a 40–70 %
   cost-to-risk toll at fixed risk, which is how the live book sizes.
5. **No trail, no break-even, no scale-out.** All three are value-destroying at every parameter
   tested, for the reason in §2.1 — reaching a level predicts continuation, so any rule that exits on
   a pullback sells the best state.
6. **None of this makes the pool profitable.** Best measured gross is +0.0130 (out-of-fit, dies to
   dedup); the cost floor is 0.0789 R/trade even with a free spread. Exit design is worth roughly
   +0.05 to +0.09 R/trade and the gap to net-positive is ~0.20 R/trade. The money is not in the exit.

---

## 10. The cohort where the exit repair is worth the most — and the trap inside it

### 10.1 The first-minute loss is neither spread nor fill selection

`L11_FIRSTMINUTE_V1.json`. The mark is already **-0.0969 R at the close of the FILL BAR itself**,
before any subsequent bar exists.

| cohort | n | r at bar 0 | r at bar 1 | r at wall | mean truthed spread (R) |
|---|---:|---:|---:|---:|---:|
| ALL TAKEABLE | 24,116 | -0.0969 | -0.0924 | -0.0386 | 0.0773 |
| `born_at_limit` (at-market, no fill selection at all) | 14,911 | -0.0647 | -0.0679 | -0.0859 | 0.0613 |
| `born_marketable` | 1,265 | -0.3157 | -0.3157 | -0.2586 | 0.0790 |
| `born_resting` (a genuine resting limit) | 7,923 | -0.1207 | -0.1035 | **+0.0811** | 0.1070 |
| spread tercile LOW | 8,045 | -0.0721 | -0.0604 | **+0.0048** | 0.0043 |
| spread tercile MID | 8,038 | -0.0662 | -0.0622 | -0.0032 | 0.0247 |
| spread tercile HIGH | 8,033 | -0.1525 | -0.1546 | **-0.1175** | 0.2029 |
| LONG | 10,778 | -0.0956 | -0.0798 | **+0.0616** | 0.0730 |
| SHORT | 13,338 | -0.0980 | -0.1026 | -0.1196 | 0.0807 |

It is not the spread: the LOW tercile's truthed spread is **0.0043 R**, essentially zero, and it still
opens -0.0721 R. It is not fill selection: `born_at_limit` orders are at-market and still open
-0.0647 R. **Whatever books that first bar is upstream of both the exit and the fill.**

### 10.2 Gross negativity co-locates with the spread-to-risk ratio, and that is a GEOMETRY axis

`spread_r` is spread divided by the risk distance, so a high `spread_r` means a **stop that is tight
relative to the instrument's own noise**, not an expensive instrument. `L11_SPREAD_TERCILE_V1.json`:

| tercile | n | truthed spread (R) | MFE med | MAE med | INCUMBENT | HOLD | **TIMESTOP_90** | best |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| LOW | 8,047 | 0.0043 | 0.807 | -0.881 | -0.0614 | +0.0047 | **+0.0313** | TS90 |
| MID | 8,050 | 0.0247 | 1.091 | -1.125 | -0.0556 | -0.0033 | **+0.0197** | TS90_S3 +0.0229 |
| HIGH | 8,042 | 0.2029 | 1.194 | -1.447 | -0.1355 | -0.1174 | -0.1438 | HOLD |

**The entire gross deficit of the takeable pool lives in the third whose stop is tight relative to its
spread.** On the other two-thirds a 90-minute time stop with no target and no stop is gross-POSITIVE.
This is the same mechanism as §4.3 measured on gross rather than on cost: tight-relative-to-noise
geometry loses before any cost is charged.

### 10.3 The production cost gate already selects that cohort — and the incumbent exit contract
throws it away

`L11_PRODGATE_V1.json`. Restricting to rows that pass the engine's own frozen gate
`total_cost_r <= 0.15` (w0-dictionary D1):

| cell | n | INCUMBENT gross | HOLD gross | **TS90 gross** | INCUMBENT net73 | **TS90 net73** |
|---|---:|---:|---:|---:|---:|---:|
| ALL \| MONTH \| real | 7,357 | -0.0487 | +0.0463 | **+0.0717** | -0.1001 | **+0.0203** |
| ALL \| MONTH \| strict | 7,357 | -0.0696 | +0.0299 | +0.0531 | -0.1207 | +0.0020 |
| ALL \| TEST \| real | 4,313 | -0.0475 | +0.0662 | **+0.1053** | -0.0973 | **+0.0555** |
| ALL \| TEST \| strict | 4,313 | -0.0690 | +0.0491 | +0.0836 | -0.1185 | +0.0342 |
| FIRSTEM \| MONTH \| real | 5,859 | -0.0601 | -0.0452 | -0.0375 | -0.1135 | -0.0908 |
| FIRSTEM \| MONTH \| strict | 5,859 | -0.0863 | -0.0658 | -0.0604 | -0.1393 | -0.1133 |
| FIRSTEM \| TEST \| real | 3,403 | -0.0757 | -0.0802 | -0.0647 | -0.1282 | -0.1171 |
| FIRSTEM \| TEST \| strict | 3,403 | -0.1030 | -0.1019 | -0.0915 | -0.1550 | -0.1435 |

TS90 beats the incumbent in **8 of 8** cells, by **+0.0110 … +0.1528**. On the rows the system
already admits, replacing 2R/-1R with a 90-minute mark-out is the largest single exit-side number
in this lane. **And on the shipped population it makes the gated cohort NET-POSITIVE** (+0.0203
whole month, +0.0555 on the test half).

### 10.4 …and that net-positive number is 1,498 duplicated FVG emissions

`L11_DUPLICATE_ATTRIBUTION_V1.json`. Splitting the same gated cohort by W0-F1's pseudo-replication:

| contract | gate ALL (7,357) | gate FIRST-EMISSION (5,859) | **gate REPEATS (1,498)** |
|---|---:|---:|---:|
| TS90 gross | +0.07173 | **-0.03746** | **+0.49876** |
| TS90 net73 | +0.02031 | -0.09084 | +0.45504 |
| HOLD gross | +0.04633 | -0.04524 | +0.40452 |
| INCUMBENT gross | -0.04872 | -0.06011 | -0.00417 |

The 1,498 repeated emissions are **20.4 %** of the gated cohort and **97.26 % of them are
`current_fvg_fill`**. They book **+0.4988 R/trade** under TS90 against **-0.0375** for the 5,859
distinct setups — a **0.536 R/trade** gap.

**The incumbent exit contract was masking the inflation.** Under 2R/-1R the repeats book -0.0042,
indistinguishable from the rest, so nothing showed. Remove the contract and the repeats' true path
value is released and turns the whole cohort positive. Deleting the exit contract does not create
edge here; it exposes a counting artifact.

**Standing warning for later waves: any result of the form "removing the exit contract makes this
pool positive" is, at the gated cohort, 1,498 re-emissions of a small set of `current_fvg_fill`
setups walked as independent trades.** The honest read of the same cohort is
`TS90 gross -0.0375, net -0.0908` on 5,859 distinct setups — still an improvement of +0.0226 over the
incumbent, and still negative.

---

## 9. Minimax — the robust contract, and the hard bound

`L11_MINIMAX_V1.json`. Every one of **3,472** contracts (target × stop × grace × trail × time stop)
scored on **16** convention cells = {ALL, FIRST_EMISSION} × {real, strict fill} × {stop slip 0, 0.05R}
× {TEST window, whole month}, ranked by the WORST cell rather than the best.

| | worst cell | median cell | best cell | cells positive |
|---|---:|---:|---:|---:|
| minimax winner `T0.25_S0.25_G1_MB30` | **-0.11313** | -0.07817 | -0.04544 | 0/16 |
| minimax winner with a fixed-risk-honest stop (≥1R or none) `Tnone_S1.50_MB90` | -0.12358 | -0.06796 | -0.02689 | 0/16 |
| HOLD_TO_WALL | -0.13766 | -0.07294 | -0.01713 | 0/16 |
| INCUMBENT T2/S1 | **-0.15583** | -0.11502 | -0.07407 | 0/16 |

**Zero of 3,472 contracts is gross-positive in any of the 16 cells.** The incumbent ranks **606 of
3,472** by worst case; doing nothing ranks **178**. The minimax winner is a very tight symmetric
0.25/0.25 cell whose advantage is entirely fixed-size (§4.3: 70 % cost-to-risk at fixed risk), which
is why the fixed-risk-honest row is given beside it.

The only policy measured anywhere in this lane that is gross-positive in a cell is the **per-family
DESIGNED** policy (+0.01298 in `ALL|real|slip0|TEST`), i.e. it beats all 3,472 single shared
contracts in that cell — and it fails deduplication (§3.3).

Incumbent, all 16 cells: -0.0793 / -0.0842 / -0.1038 / -0.1093 / -0.1207 / -0.1267 / -0.1455 /
-0.1522 / -0.0752 / -0.0741 / -0.1004 / -0.0992 / -0.1301 / -0.1293 / -0.1558 / -0.1549.
Hold, same order: -0.0171 / -0.0386 / -0.0171 / -0.0386 / -0.0568 / -0.0783 / -0.0568 / -0.0783 /
-0.0850 / -0.0676 / -0.0850 / -0.0676 / -0.1377 / -0.1189 / -0.1377 / -0.1189.
At zero stop slippage hold beats the incumbent in **6 of 8** cells (both exceptions
first-emission × TEST, by +0.0098 and +0.0075); at 0.05 R of stop slippage it beats it in **8 of 8**.

---

## 8. Artifacts

| file | what |
|---|---|
| `l11_lib.py` | substrate builder + `Sub` (born class, REAL/STRICT fill index, cost model) |
| `l11_SUBSTRATE_V1.npz`, `l11_ALIGNED_V1.npz`, `l11_ALIGNED_STRICT_V1.npz` | (N,120) fav/adv/cls fill-aligned caches |
| `l11_walk.py` | vectorised contract engine, ~15 ms for 24k paths; no-time-travel stop at `:109-122` |
| `l11_shape.py` / `L11_SHAPE_V1.json` | §1 excursion shape, per family / born / side |
| `l11_analytic.py` / `L11_ANALYTIC_V1.json` | §2 exit-vs-hold identity, drift surface, per family |
| `l11_contracts.py` / `L11_CONTRACTS_V1.json` | §2.3 battery + the analytic verification |
| `l11_family.py` / `L11_FAMILY_V1.json` | §3.2 designed / fitted / test per family |
| `L11_FAMILY_LIMBS_V1.json` | §3.1 limb decomposition per family |
| `l11_robust.py` / `L11_ROBUST_V1.json` | §3.3 five attacks |
| `l11_confirm.py` / `L11_CONFIRM_V1.json` | §4.1 invariance grid, §4.3 fixed-risk framing |
| `l11_minimax.py` / `L11_MINIMAX_V1.json` | §9 minimax-robust contract over 16 convention cells |
| `L11_TRAIL_CONVENTION_V1.json` | §5.2 lagged vs same-bar trail |
| `L11_FIRSTMINUTE_V1.json` | §10.1 first-bar loss by born class / spread tercile / side |
| `L11_SPREAD_TERCILE_V1.json` | §10.2 contracts by spread-to-risk tercile |
| `L11_CHEAP_COHORT_V1.json` | §10.2 TS90 on the cheap two-thirds, 16 cells, train-only cuts |
| `L11_PRODGATE_V1.json` | §10.3 the repair on the engine's own gate cohort |
| `L11_DUPLICATE_ATTRIBUTION_V1.json` | §10.4 the 1,498 repeat rows |
| `l11_build_result.py` / `l11_RESULT.json` | machine-readable index, assembled from the artifacts |

**Reproduce**: `python3 l11_lib.py && python3 l11_shape.py && python3 l11_analytic.py &&
python3 l11_contracts.py && python3 l11_family.py && python3 l11_robust.py &&
python3 l11_confirm.py && python3 l11_minimax.py && python3 l11_build_result.py`
(minimax is ~13 min; everything else is seconds).
