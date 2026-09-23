# LANE l8 — WHERE IS THE HIT RATE ACTUALLY HIGH

Wave 19 broad forensic. January 2026 diagnostic pool, true-UTC re-clock (CJ), 27,658 candidates.
Every number below was measured by a script in this directory over the whole population — nothing
is sampled, nothing is estimated. **578,640 conditioning cells were examined**; the multiplicity
ledger is §K of `l8_CELLS_APPENDIX.md`. No multiplicity correction is applied anywhere.

Full tables: `l8_TABLES_APPENDIX.md` (§A-J) and `l8_CELLS_APPENDIX.md` (§K-O).
Machine-readable: `l8_RESULT.json` plus the 12 `L8_*_V1.json` measurement files.

---

## 0. HEADLINE

**Nowhere on any single conditioning axis is the hit rate high. The hit rate is not the problem
and never was — the pool's realized payoff is 1.1768:1 against a declared 2.00:1, so its own
realized breakeven win rate is 45.94% and it wins 34.68%: it is 11.25 percentage points below
break-even, not 1.4 above it.** The established framing ("34.7% vs 33.3% breakeven, eight of ten
families beat their own breakeven") compares an actual win rate against a breakeven computed from
a payoff the system does not achieve. At the payoff it does achieve, **zero of ten families beat
breakeven.**

**What IS mechanically true, and is the whole find: 55.65% of the takeable January pool has its
entry level touched inside the first minute after the decision, and that cohort is adversely
selected. It books -0.19754 R honest / -0.20643 R gross. The other 43.35% books -0.03861 /
-0.01119. Refusing the first-minute fills — a pure entry-timing rule with no directional model,
no new data and no look-ahead — moves the raw January pool from -0.23715 to -0.01464 R per
candidate-opportunity, recovering 93.8% of the entire honest deficit.**

---

## 1. THE CORRECTION THAT REFRAMES THE LANE (measured, n=27,658)

| quantity | pool as shipped | pool clean (born_past_stop dropped) |
|---|--:|--:|
| n | 27,658 | 24,142 |
| gross win rate | 0.34684 | 0.39723 |
| gross mean R | -0.217496 | -0.104290 |
| realized payoff (meanWin / -meanLoss) | **1.1768** | **1.2124** |
| **realized breakeven win rate** | **0.45939** | **0.45200** |
| win rate MINUS realized breakeven | **-11.25 pp** | **-5.48 pp** |
| declared-payoff breakeven (the number in use) | 0.3333 | 0.3333 |

The 33.3% figure is only correct if every winner books +2R. Measured honestly on the M1 paths with
the entry required to trade first, **only 15.40% of the clean pool ever reaches +2R before -1R**
while **51.11% takes the full stop** — a resolution win rate of **0.2315** against the 0.3333 the
2:1 contract needs (`L8_RESWIN_V1.json`). On the raw pool it is **0.1902**.

Everything else in this receipt is measured on that honest contract: first touch of +2R vs -1R,
entry must be traded before the walk starts, conservative same-bar tie to the stop, unresolved
positions marked at the 2-hour wall close, unfilled candidates booked 0.0 R.

---

## 2. THE FIND — FIRST-MINUTE FILLS ARE ADVERSELY SELECTED (n=13,436 of 24,142)

`l8_LADDER.jsonl.gz` records, for every candidate, the bar at which the entry level was first
traded and the bar at which each target/stop rung was first touched, all after the fill.

| cohort | n | share | honest 2R/-1R mean | gross_r mean | resolution win rate | targetRate | stopRate | markRate |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| entry touched on bar 1 (<= 60 s) | 13,436 | 55.65% | **-0.19754** | **-0.20643** | **0.2074** | 0.1451 | 0.5544 | 0.3005 |
| entry touched at bar 2-5 | 2,550 | 10.56% | -0.04570 | -0.02700 | 0.2738 | 0.1894 | 0.5024 | 0.3082 |
| entry touched at bar 6-15 | 1,918 | 7.94% | -0.02440 | -0.01460 | 0.2866 | 0.2143 | 0.5334 | 0.2523 |
| entry touched at bar 16-60 | 3,639 | 15.07% | -0.04950 | -0.02010 | 0.2607 | 0.1770 | 0.5018 | 0.3212 |
| entry touched at bar 61-120 | 2,358 | 9.77% | -0.02570 | +0.02250 | 0.2321 | 0.0975 | 0.3227 | 0.5797 |
| entry NEVER traded in 2 h | 241 | 1.00% | 0.00000 | **+1.54767** | - | - | - | - |

The last row is W0-F2 in one line: 241 candidates the pool scores at **+1.548 R average that never
traded at all**, worth +373 R of pure fiction.

**The penalty is inside both order kinds, so it is not an order-type artifact** (`L8_FILLSPEED_V1.json`):

| depth at decision | fill speed | n | resWin | honest mean | gross mean |
|---|---|--:|--:|--:|--:|
| at market (`mkt_r`=0) | bar 1 | 11,308 | 0.2163 | -0.17070 | -0.18770 |
| at market | bar 2-5 | 1,808 | 0.2893 | -0.00890 | +0.00300 |
| at market | bar 6-15 | 761 | 0.3008 | **+0.04700** | +0.10010 |
| at market | bar 16-60 | 648 | 0.2891 | **+0.04100** | +0.31340 |
| resting limit (`mkt_r`>0) | bar 1 | 909 | 0.1837 | -0.34440 | -0.32520 |
| resting limit | bar 6-15 | 1,145 | 0.2790 | -0.07010 | -0.08920 |
| resting limit | bar 61-120 | 2,197 | 0.2307 | -0.02220 | -0.03850 |
| already through entry (`mkt_r`<0) | bar 1 | 1,205 | 0.1402 | -0.33330 | -0.28740 |

### 2.1 It is not the same-bar tie rule
Of the 13,436 bar-1 fills, only **1,028 (7.65%)** touch the stop on the fill bar itself; 3 touch the
target and 2 touch both. Exempting the fill bar from the stop entirely (a deliberately optimistic
bound) makes the cohort **worse**, -0.22820 vs -0.19754, because those rows then ride on to a worse
outcome. The penalty is real.

### 2.2 It is not the 2-hour measurement wall — EQUAL-EXPOSURE CONTROL
Resolve every cohort inside a fixed H-bar window measured from its OWN fill bar, discarding any
candidate whose window does not fit before the wall. Equal exposure, equal wall distance
(`L8_HORIZONMATCH_V1.json`):

| H (bars from fill) | bar-1 eligible | bar-1 resWin | later eligible | later resWin | ratio |
|--:|--:|--:|--:|--:|--:|
| 15 | 13,414 | **0.0947** | 9,932 | **0.1801** | 1.90x |
| 30 | 13,384 | 0.1410 | 9,300 | 0.2208 | 1.57x |
| 45 | 13,342 | 0.1632 | 8,549 | 0.2399 | 1.47x |
| 60 | 13,140 | 0.1758 | 7,763 | 0.2562 | 1.46x |
| 90 | 12,918 | 0.1974 | 5,756 | 0.2737 | 1.39x |

At every horizon the delayed cohort resolves to target 1.4-1.9x as often. **This is adverse
selection at the entry, not a measurement artifact.**

### 2.3 It is not one family
`k5 - k0` is positive for all ten families (`L8_DELAY_V1.json` -> `by_family`):

| family | n | k=0 R/opp | k=1 R/opp | k=5 R/opp | k5-k0 |
|---|--:|--:|--:|--:|--:|
| structural_distance_extreme | 1,993 | -0.27320 | +0.00404 | +0.00575 | **+0.27895** |
| cross_asset_lead_lag | 2,083 | -0.19659 | +0.00055 | -0.00745 | +0.18914 |
| current_breaker_re_entry | 796 | -0.11273 | +0.03010 | +0.04180 | +0.15453 |
| displacement_continuation | 4,469 | -0.10218 | -0.00495 | +0.00088 | +0.10306 |
| session_open_range_break | 987 | -0.10229 | -0.01671 | -0.00397 | +0.09832 |
| volatility_compression_expansion | 605 | -0.09332 | -0.01906 | +0.00271 | +0.09603 |
| current_fvg_fill | 7,145 | -0.14062 | -0.06351 | -0.05110 | +0.08952 |
| liquidity_sweep_reclaim | 4,475 | -0.07061 | +0.01676 | +0.01123 | +0.08184 |
| current_ob_retest | 1,292 | -0.05708 | -0.00824 | -0.00642 | +0.05066 |
| regime_transition_break | 297 | -0.01979 | +0.00812 | +0.01613 | +0.03592 |

### 2.4 The price of the repair
`L8_DELAY_V1.json` -> `delay_sweep`. R per candidate-OPPORTUNITY (refused and unfilled book 0.0):

| k (refuse fills inside k bars) | traded | share | R/opportunity | R/trade | resWin |
|--:|--:|--:|--:|--:|--:|
| 0 (as shipped) | 23,901 | 0.9900 | **-0.12667** | -0.12795 | 0.2315 |
| **1** | 10,465 | 0.4335 | **-0.01674** | -0.03861 | **0.2655** |
| 2 | 9,413 | 0.3899 | -0.01322 | -0.03391 | 0.2668 |
| 5 | 7,915 | 0.3279 | -0.01191 | -0.03633 | 0.2625 |
| 10 | 6,747 | 0.2795 | -0.00992 | -0.03550 | 0.2590 |
| 20 | 5,342 | 0.2213 | -0.00704 | -0.03179 | 0.2539 |
| 60 | 2,358 | 0.0977 | -0.00251 | -0.02568 | 0.2321 |

**k=1 is worth +0.10993 R per candidate on the clean pool and +0.22251 on the raw pool
(-0.23715 -> -0.01464).** Stable in every third: J1 -0.13839 -> -0.03282, J2 -0.09672 -> **+0.01533**,
J3 -0.14019 -> -0.02862.

**Honest accounting of where the value comes from.** The whole +0.10993 is "do not take the
adversely-selected half"; the trades that remain are still -0.03861 each. The resolution win rate
improves only 0.2315 -> 0.2655, so this is a *selection* repair, not an edge. It is nonetheless the
single largest recoverable quantity this lane found, it needs no new data, and it is implementable
as a pure entry-timing rule (place the order, refuse a fill inside the first M1 bar).

---

## 3. THE POSITIVE CELLS (lane item 2)

### 3.1 On the pool as shipped, there are almost none
Of **269** single-axis cells with n>=50 (294 examined), exactly **10** have a positive raw mean, and
two of those (`which_came_first`) are outcome-conditioned and unusable. The best causally-available
single-axis cell with n>=300 in the whole month is `session`/`kill_zone == moonshot_h09_10`:
n=312 clean, mean **+0.0970**, t=+1.65. Nothing else clears +0.04 with n>=300.
Full list: `l8_CELLS_APPENDIX.md` §O.1.

### 3.2 On the delayed-fill population there are real ones, and one is a single axis
Base: n=10,465, mean -0.03861, resWin 0.2655. 237,384 cells examined at orders 1-3, 68,762 reported
at n>=50, **27,175 positive**. Ranked by n x mean, with the January-thirds check:

| rank | cell | n | mean | resWin | t | total R | thirds |
|--:|---|--:|--:|--:|--:|--:|---|
| single axis | **`cost_r` in (0.10, 0.15]** | **1,412** | **+0.09974** | **0.3222** | **+3.20** | +140.8 | **3/3** (+0.096/+0.150/+0.061) |
| 1 | side=SHORT + prob 0.70-0.75 + ev 0.6-0.8 | 1,550 | +0.1235 | 0.3529 | +4.04 | +191.4 | 2/3 |
| 2 | prob 0.70-0.75 + ev 0.6-0.8 | 2,097 | +0.0840 | 0.3294 | +3.21 | +176.2 | 1/3 |
| 3 | prob 0.70-0.75 + ev 0.6-0.8 + not-first-emission | 732 | +0.2096 | 0.3783 | +4.53 | +153.4 | **3/3** |
| 4 | dow=Tue + risk_pct 1.0 + limit | 493 | +0.3096 | 0.4270 | +5.23 | +152.7 | **3/3** |
| 5 | dow=Mon + prob 0.70-0.75 + ev 0.6-0.8 | 483 | +0.3140 | 0.4111 | +5.89 | +151.7 | **3/3** |
| 6 | `cost_r` 0.10-0.15 + limit | 1,196 | +0.1258 | 0.3351 | +3.65 | +150.4 | **3/3** |
| 7 | dow=Mon + prob 0.70-0.75 + not-first-emission | 274 | +0.5199 | 0.5032 | +7.22 | +142.4 | **3/3** |
| 8 | `cost_r` 0.10-0.15 + prob 0.70-0.75 + ev 0.6-0.8 | 375 | +0.3750 | 0.4644 | +5.84 | +140.6 | **3/3** |
| 9 | `cost_r` 0.10-0.15 + ev 0.6-0.8 | 388 | +0.3520 | 0.4516 | +5.58 | +136.6 | **3/3** |
| 10 | dow=Tue + XAUUSD + limit | 320 | +0.4203 | 0.4735 | +5.43 | +134.5 | **3/3** |

Top 300 in `l8_CELLS_APPENDIX.md` §L; all 27,175 in `L8_POSITIVE_V1.json`.

**`cost_r` in (0.10, 0.15] is the one to spend a held-out month on.** It is a SINGLE axis (6 cells
examined, not 237,384), it is positive in all three January thirds, its resolution win rate 0.3222
is the only large-n cell that comes within a point of the 0.3333 the 2:1 contract needs, and it is
knowable at the decision instant. Its shape is a sweet spot, not a monotone: <=0.10 books -0.03426,
0.10-0.15 books +0.09974, 0.15-0.25 books -0.05638, >1.0 books -0.18436. Since `cost_r` is
R-denominated it is a proxy for stop width — the band is "stop wide enough that the spread is not
material, tight enough that the target is reachable inside two hours".

### 3.3 Per-symbol on the delayed-fill population (n>=100), all 3/3-stable positives
USDCHF n=236 +0.16913 resWin 0.3248 **3/3**; XAGUSD n=321 +0.12473 resWin 0.3632 **3/3**;
UKOIL_cash n=237 +0.08074 resWin 0.3214 **3/3**. GER40 n=752 +0.15416 resWin 0.3552 (2/3, one third
is +0.430 and drives it). Full table §J of `l8_TABLES_APPENDIX.md`.

---

## 4. THE CONVERSE — WHAT TO EXCLUDE (lane item 3)

Single-cell exclusion value on the clean pool (base -0.10429), `L8_EXCLUDE_V1.json`. All of these
are negative in **all three** January thirds:

| axis | value | n | share | cell mean | pool lift if dropped |
|---|---|--:|--:|--:|--:|
| cost_b | > 1.0 | 4,059 | 16.8% | -0.2176 | +0.0229 |
| spread_b | > 1.0 | 3,660 | 15.2% | -0.2262 | +0.0218 |
| symbol | NAS100 | 1,483 | 6.1% | **-0.2842** | +0.0118 |
| dup_count | 2-5 emissions | 1,525 | 6.3% | **-0.3160** | - |
| born | born_marketable | 1,265 | 5.2% | -0.2566 | - |
| dow | Thursday | 4,914 | 20.3% | -0.1605 | +0.0144 |
| prob_b | 0.65-0.70 | 4,097 | 17.0% | -0.1740 | +0.0143 |
| rdp_b | <= 0.02% of price | 944 | 3.9% | -0.1948 | - |
| hour | 22 UTC | 677 | 2.8% | -0.2481 | - |
| hour | 4 UTC | 872 | 3.6% | -0.2124 | - |
| fillp_b | > 0.92 | 558 | 2.3% | -0.2037 | - |
| family | current_fvg_fill | 7,145 | 29.6% | -0.1415 | +0.0156 |

The largest single exclusions by lift are structural rather than economic (`fill_class ==
passive_queue_confirmed` +0.0852 on 76.8% of the pool; `route_session == off_configured_session`
+0.0403 on 58.6%). The greedy cascade saturates after four steps at +0.0061 on 4,005 rows —
**exclusion alone cannot make this pool positive.** Cascade in §N.1.

On the delayed-fill population the reliably-negative census is 7,953 cells; worst by impact:
`spread_r > 1.0` n=1,893 -0.19947 (-377.7 R), `current_fvg_fill` + off-session n=4,102 -0.10230
(-419.5 R), `risk_rank > 30` n=6,031 -0.06440 (-388.5 R). Top 150 in §M.

---

## 5. TWO MORE MECHANISMS THE SWEEP EXPOSED

### 5.1 The shipped cost gate SELECTS — and correcting the spread overcharge DESTROYS value
On the delayed-fill population (`L8_GATEVALUE_V1.json`):

| split | n | honest mean | resWin | total R |
|---|--:|--:|--:|--:|
| passes both shipped limbs (spread_r<=0.10 AND cost_r<=0.15) | 2,966 | **+0.00249** | 0.2737 | +7.4 |
| refused by at least one limb | 7,499 | -0.05486 | 0.2628 | -411.4 |

Re-running the same gate with the spread divided by the measured overcharge:

| spread divided by | passing n | passing mean | passing total R |
|--:|--:|--:|--:|
| 1.0 (as shipped) | 2,966 | **+0.00249** | +7.4 |
| 2.0 | 4,139 | -0.00038 | -1.6 |
| 4.0 | 5,324 | -0.01169 | -62.2 |
| **7.3 (measured)** | 6,423 | **-0.01587** | **-101.9** |
| 8.5 (measured) | 6,647 | -0.01530 | -101.7 |

The 3,457 candidates the 7.3x correction newly admits average **-0.0316 R each and destroy 109.3 R**
over one month of the delayed-fill pool. The resolution win rate is flat across the whole sweep
(0.2737 -> 0.2657), so the gate is not selecting for direction — it is acting as a **minimum
stop-width filter**, and that is why it works. **Repairing the spread overcharge without replacing
the stop-width function it was accidentally performing is a value-destroying change.** This
independently reproduces "fixing costs makes the system trade 2.2-2.4x more and earn no more",
with the mechanism named.

### 5.2 The 2-hour wall truncates families 38x unevenly — two families are effectively unmeasured
Share of each family still open at the wall, honest 2R/-1R, clean population (`L8_RESWIN_V1.json`):

| family | n | markRate | stopRate | targetRate | resWin |
|---|--:|--:|--:|--:|--:|
| volatility_compression_expansion | 605 | **0.8694** | 0.1157 | 0.0116 | 0.0909 |
| regime_transition_break | 297 | **0.8653** | 0.0976 | 0.0168 | 0.1471 |
| current_ob_retest | 1,292 | 0.5488 | 0.3669 | 0.0820 | 0.1828 |
| session_open_range_break | 987 | 0.5380 | 0.3698 | 0.0689 | 0.1570 |
| displacement_continuation | 4,469 | 0.4576 | 0.4252 | 0.1072 | 0.2013 |
| current_fvg_fill | 7,145 | 0.3131 | 0.5254 | 0.1607 | 0.2342 |
| current_breaker_re_entry | 796 | 0.2852 | 0.5377 | 0.1746 | 0.2451 |
| liquidity_sweep_reclaim | 4,475 | 0.2355 | 0.5533 | 0.1966 | 0.2622 |
| cross_asset_lead_lag | 2,083 | 0.1023 | 0.6654 | 0.2093 | 0.2393 |
| structural_distance_extreme | 1,993 | **0.0226** | **0.7316** | 0.2253 | 0.2354 |

`volatility_compression_expansion` and `regime_transition_break` have 87% of their trades still
open when the measurement stops: **their published economics describe a 2-hour snapshot, not a
strategy.** At the other end `structural_distance_extreme` resolves 97.7% of its trades inside two
hours and takes a full stop on **73.16%** of them — its stop is too tight for its own entry.
Any cross-family comparison drawn from this pool is confounded by resolution speed.

---

## 6. THE STACK (lane item 2, aggregate)

Priced per candidate-opportunity over all 27,658 pool rows; skipped candidates book 0.0 R.

| step | n traded | R/trade | resWin | **R/opportunity** | total R |
|---|--:|--:|--:|--:|--:|
| 0. raw pool, honest 2R/-1R | 27,658 | -0.23715 | 0.1902 | **-0.23715** | -6,559.1 |
| 1. drop born_past_stop (untakeable; W0-capture) | 24,142 | -0.12667 | 0.2315 | -0.11057 | -3,058.1 |
| 2. + one-minute entry delay | 10,465 | -0.03861 | 0.2655 | **-0.01461** | -404.0 |
| 3. + shipped cost gate passes | 2,966 | +0.00249 | 0.2737 | **+0.00027** | **+7.4** |
| 3b. + `cost_r` in (0.10,0.15] only | 1,412 | **+0.09974** | **0.3222** | +0.00509 | **+140.8** |
| 4. (alt) + drop spread_r>1.0 | 8,572 | -0.00307 | 0.2752 | -0.00095 | -26.3 |
| 5. (alt) + drop hours 00-03 and 12-15 | 6,606 | -0.01687 | 0.2724 | -0.00403 | -111.5 |

Steps 1 and 2 are mechanical repairs with no directional content and no look-ahead; together they
recover **93.8%** of the honest deficit. Step 3 is the first non-negative book in the January
diagnostic pool. It is +7.4 R over a month on 2,966 candidates — economically trivial, and that is
the honest statement: **the mechanisms are large, what is left after them is not an edge yet.**

---

## 7. STABILITY WITHIN JANUARY (lane item 4)

Every table in the appendices carries a per-third column. Summary of what survives 3/3:

| finding | J1 (d1-10) | J2 (d11-20) | J3 (d21-31) | verdict |
|---|--:|--:|--:|---|
| entry delay k=1, R/opportunity | -0.03282 (was -0.13839) | **+0.01533** (was -0.09672) | -0.02862 (was -0.14019) | **holds 3/3** |
| bar-1 penalty (resWin, equal exposure H=60) | - | - | - | holds at every H |
| `cost_r` (0.10,0.15] on delayed pop | +0.096 | +0.150 | +0.061 | **holds 3/3** |
| USDCHF delayed | +0.043 | +0.215 | +0.230 | **holds 3/3** |
| XAGUSD delayed | +0.124 | +0.296 | +0.018 | **holds 3/3** |
| UKOIL_cash delayed | +0.193 | +0.023 | +0.039 | **holds 3/3** |
| GER40 delayed | +0.011 | +0.430 | -0.071 | 2/3, one third carries it |
| hour 8 UTC (pre-delay, gross) | +0.02 | +0.02 | +0.01 | holds 3/3 but tiny |
| `moonshot_h09_10` session | - | - | - | 2/3 only (see §A) |
| dow=Monday delayed | +0.056 | +0.203 | -0.166 | **fails** |
| spread_r>1.0 negative | -0.28 | -0.22 | -0.17 | **holds 3/3 (negative)** |
| NAS100 negative | - | - | - | **holds 3/3 (negative)** |

---

## 8. MULTIPLICITY (lane item 5)

**578,640 cells examined.** Breakdown in `l8_CELLS_APPENDIX.md` §K. The two findings this lane puts
forward for a held-out month were selected from very different search sizes and that difference is
the point:

- **The entry-delay finding was not searched for at all** — it fell out of one axis (`fill_bar`)
  with 6 buckets, was then subjected to three adversarial controls (tie rule, equal exposure,
  per family) and survived all three. Effective look count: **single digits.**
- **`cost_r` in (0.10, 0.15]** came from a 6-cell single axis inside a 237,384-cell census. Treat
  it as one look among 6 on its own axis, or as one among 237,384 if you want the pessimistic bill.
- **Everything in §3.2 ranks 2 and below** came from the 237,384-cell census and should be priced
  at that family size. They are reported because the brief requires reporting, not because they
  are believed.

---

## 9. WHAT WAVE 2 SHOULD SPEND A HELD-OUT MONTH ON, IN ORDER

1. **The one-minute entry delay.** +0.22251 R/candidate on the raw January pool, +0.10993 on the
   clean one, 3/3 thirds, all ten families, survives an equal-exposure control. April and May lane
   packs have paths; February does not (its pool has first-touch timestamps inline, which is enough
   to reproduce the resolution rates but not the fill bar). **This is the cheapest large thing in
   the estate.**
2. **`cost_r` in (0.10, 0.15] on the delayed-fill population.** The only large-n cell whose
   resolution win rate (0.3222) approaches the 0.3333 the 2:1 contract requires.
3. **The spread-overcharge repair, as a NEGATIVE result to confirm.** -0.0316 R per newly admitted
   candidate, -109.3 R in one month. If this replicates, the pending cost repair must be paired
   with an explicit minimum-stop-width rule or it will cost money.
4. **The family resolution-speed asymmetry.** Not a trade; a measurement-validity finding. Two
   families' published economics are a 2-hour snapshot of trades that are 87% still open.

## 10. WHAT THIS LANE LOOKED FOR AND DID NOT FIND

- **No hour, session, symbol, family, side, timeframe, risk-size, sleeve-count, confidence or EV
  bucket is materially positive on its own.** 10 of 269 single-axis cells are positive at all, the
  best causally-usable one is +0.0970 on n=312 at t=+1.65.
- **`decision_timeframe`, `market_timeframe`, `setup_family`, `bucket_source_family`,
  `dynamic_geometry_policy`, `candidate_confidence` and `source_completeness` are constants** in
  this pool (cardinality 1) and cannot condition anything. `framework` collapses 1:1 onto
  `origin_family`; `kill_zone` and `authority_session` collapse onto `session`; `direction` onto
  `side`.
- **The belief layer orders weakly and levels catastrophically.** `candidate_ev_r` deciles span only
  0.1345 R (top decile -0.0375, bottom -0.1721) and are monotone in only 5 of 9 steps;
  `candidate_probability` spans 0.1390 and is also 5/9. Both are positive on 100% of rows against a
  pool that loses. Ordering information exists; it is worth about 0.07 R/trade between the top and
  bottom halves and nothing like enough to close an 11.25 pp breakeven gap.
- **No exit geometry rescues the pool.** The full 15-target x 8-stop honest grid
  (`L8_GRID_CLEAN_V1.json`) has **no positive cell**; the best is T=0.40/S=-0.25 at -0.07389, which
  is position-size reduction wearing a costume.

---

## 11. ARTIFACT INDEX

Scripts (all in this directory, all runnable from it):
`l8_frame.py` (frame builder), `l8_lib.py`, `l8_sweep1.py`, `l8_sweepN.py`, `l8_tables.py`,
`l8_decile.py`, `l8_exclude.py`, `l8_ladder_build.py`, `l8_grid.py`, `l8_hitrate.py`,
`l8_reswin.py`, `l8_depth.py`, `l8_fillspeed.py`, `l8_delay.py`, `l8_horizonmatch.py`,
`l8_gatevalue.py`, `l8_positive.py`, `l8_final.py`, `l8_receipt.py`, `l8_cells.py`.

Derived data: `l8_FRAME.jsonl.gz` (27,658 x 70 analysis frame),
`l8_LADDER.jsonl.gz` (per-candidate first-touch bar for 15 targets x 8 stops, after the fill).

Measurements: `L8_SWEEP1_SINGLE_V1.json`, `L8_SWEEP2_V1.json`, `L8_SWEEP3_V1.json` (80 MB),
`L8_TABLES_V1.json`, `L8_DECILES_V1.json`, `L8_EXCLUDE_V1.json`, `L8_GRID_ALL_V1.json`,
`L8_GRID_CLEAN_V1.json`, `L8_HITRATE_V1.json`, `L8_RESWIN_V1.json`, `L8_DEPTH_V1.json`,
`L8_FILLSPEED_V1.json`, `L8_DELAY_V1.json`, `L8_HORIZONMATCH_V1.json`, `L8_GATEVALUE_V1.json`,
`L8_POSITIVE_V1.json`, `L8_FINAL_V1.json`.

Citable rows: bar-1 fill cohort e.g. `broadorigin_37d6573709e9baf0e4e1d4` @ 2026-01-02T00:15:00Z
GER40 (gross -1.0) and `broadorigin_61da0b039406b173f3a2f1` @ same minute UK100 (gross -1.0);
delayed cohort e.g. `broadorigin_69fa1abd62949b698ed44f` @ 2026-01-02T00:15:00Z JP225; the
`cost_r` (0.10,0.15] band e.g. `broadorigin_438c5b07c0d1ea9633` @ 2026-01-02T01:00:00Z.
Join key is always `(candidate_id, decision_time_utc)` — `candidate_id` alone is not unique (W0-F1).

---

## 12. VALIDATION

`l8_LADDER.jsonl.gz` was cross-checked against the shared wave-0 helper on 3,000 paths:
**0 R mismatches and 0 fill-bar mismatches** against `w0_ws.walk(target_r=2.0, stop_r=-1.0,
require_fill=True)` and against the independent recomputation of the first bar with `adv <= 0`.
The pool-level reproductions also match the established substrate exactly: gross mean -0.217496
(established -0.2175), gross win 0.34684 (0.347), mean winner +1.044775 (1.044), mean loser
-0.887796 (-0.888), n 27,658, clean n 24,142 after dropping W0-capture's 3,516 `born_past_stop`
rows (reconstructed independently here from `mkt_r_prev_close <= -1.0` in
`w0cap2_DECISION_ANCHOR_V1.jsonl.gz`, count 3,516 exact).
