# LANE e6 — HOW FAR DOES L8-F1 REACH?

Wave 19 broad forensic, extension lane. Handed one Wave-1 finding — **L8-F1, first-minute fills are
adversely selected** — with the instruction to establish its boundary, not to refute it.

**Answer: there is no boundary. It is the most general thing measured in this programme so far.**

Five months, **124,722 candidates**, an instrument reproduced digit-for-digit from l8 and then ported
unchanged. It holds in every month, is **larger** in the two months whose economics had never been
read, holds in all ten families, all 24 symbols, all 24 hours, both sides, every born-state, every
spread band, and on **101 of 101 trading days**. Of 569 conditioning cells only 11 are negative and
the worst is −0.081 on n=167.

Everything below was measured by a script in this directory over whole populations. Nothing sampled,
nothing estimated. Machine-readable: `e6_RESULT.json`.

---

## 0. HEADLINE

**The value is 100 % in the CANCEL and 0 % in the CLOCK — and l8 never separated the two.**

l8's rule refuses a candidate whose entry level trades in the first M1 bar. There are two different
live implementations of "refuse", and only one of them works:

| implementation | what it does | pooled R per candidate-opportunity |
|---|---|--:|
| as shipped | place at the decision, take the first touch | **−0.13929** |
| **DEFER** — hold the order 60 s, then take the next touch of the same level | delays entry only | **−0.14557** (WORSE by −0.00628) |
| **CANCEL** — hold 60 s, and if the level printed during that minute ABANDON the candidate | refuses entry | **−0.01726** (better by **+0.12203**) |

`E6_CONFIRM_V1.json -> C1_cancel_vs_defer`. The delay half is **negative in all five months
independently** (−0.0044 to −0.0106). A 60-second arming delay on its own is not a repair; it is a
small tax. The entire +0.122 is the decision *not to trade that candidate at all*.

**And one rule does two repairs.** 99.98 % of `born_past_stop` candidates — Wave 0's 12,619-row
capture artifact, the one that explains CQ's live V27 factory candidate — fill on bar 1. The CANCEL
rule removes them without ever consulting a decision anchor:

| book (raw pool, 124,722, incl. `born_past_stop`) | R/opportunity | t | share of the raw deficit recovered |
|---|--:|--:|--:|
| as shipped | −0.22609 | −74.71 | — |
| **CANCEL k=1 only** | **−0.01551** | −8.02 | **93.1 %** |
| W0-capture's `born_past_stop` drop only | −0.13929 | −42.66 | 38.4 % |

---

## 1. REPRODUCTION — the instrument matches l8's to the digit

`e6_repro_jan.py` re-implements the measurement from `w0_R_PATHS` + `w0cap2_DECISION_ANCHOR` without
importing any `l8_*` module. Receipt `E6_JAN_REPRO_V1.json`.

| quantity | l8 published | e6 independent |
|---|--:|--:|
| bar-1 cohort n | 13,436 (55.65 %) | **13,436 (55.65 %)** |
| bar-1 honest mean | −0.19754 | **−0.19754** |
| bar-1 gross mean | −0.20643 | **−0.20643** |
| bar-1 resolution win | 0.2074 | **0.2074** |
| bar 2-5 / 6-15 / 16-60 / 61-120 honest | −0.0457 / −0.0244 / −0.0495 / −0.0257 | **−0.04568 / −0.02438 / −0.04952 / −0.02568** |
| never traded n, pool-scored gross | 241, +1.54767 | **241, +1.54767** |
| clean sweep k=0 → k=1 | −0.12667 → −0.01674 | **−0.12667 → −0.01674** |
| clean k=2 / k=5 / k=20 / k=60 | −0.01322 / −0.01191 / −0.00704 / −0.00251 | **identical** |
| raw pool k=0 → k=1 → k=5 → k=15 | −0.23715 → −0.01464 → −0.01040 → −0.00871 | **identical** |

**Reproduced exactly.** The instrument is sound and the port below is like-for-like.

### 1.1 The port is validated against sealed bytes
February and March have no ordered-path sidecar, so their paths were rebuilt from the same
`LANE_INPUTS_TRUE_UTC_V1` M1 bar CSVs the sidecars were cut from. Rebuilding **January** the same way
and diffing it against the sealed CQ sidecar gives **27,658 identical / 0 OHLC mismatches / 0 length
mismatches** (`e6_build_month.py --verify-bars`, receipt `/tmp` build log reproduced in
`E6_SWEEP_V1.json` provenance). Two bounds both matter and the first attempt got one wrong: the
sidecar caps at `horizon_end_utc` = decision + 2 h **and** a thin symbol prints fewer than 120 bars
inside it. Taking "the next 120 rows in the CSV" produced 3,793 length mismatches; bounding by the
horizon produced zero.

---

## 2. THE EXTENSION — five months, all five hold, out-of-sample is BIGGER

`E6_SWEEP_V1.json -> months`. CLEAN = `born_past_stop` dropped (W0-capture convention).
Paired t is the per-candidate delta of the rule against as-shipped.

| month | n | clean n | bar-1 share | CLEAN k=0 | CLEAN k=1 | **delta** | paired t | RAW k=0 | RAW k=1 | **raw delta** | raw t |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| JAN (l8's own) | 27,658 | 24,142 | 0.5565 | −0.12667 | −0.01674 | **+0.10994** | +20.61 | −0.23715 | −0.01464 | **+0.22251** | +44.61 |
| FEB | 24,239 | 22,412 | 0.5707 | −0.11953 | −0.00502 | **+0.11451** | +20.62 | −0.18590 | −0.00464 | **+0.18126** | +33.88 |
| MAR | 26,484 | 24,958 | 0.5619 | −0.13938 | −0.01323 | **+0.12615** | +24.52 | −0.18851 | −0.01247 | **+0.17605** | +35.15 |
| **APR** (never read) | 25,056 | 22,027 | 0.5844 | −0.15806 | −0.01965 | **+0.13840** | +25.32 | −0.25972 | −0.01728 | **+0.24244** | +47.31 |
| **MAY** (never read) | 21,285 | 18,564 | 0.5966 | −0.15719 | −0.03532 | **+0.12188** | +19.70 | −0.26465 | −0.03071 | **+0.23394** | +40.62 |
| POOLED 5 | 124,722 | 112,103 | 0.5727 | −0.13929 | −0.01726 | **+0.12203** | **+49.54** | −0.22609 | −0.01551 | **+0.21058** | — |
| POOLED OOS (Feb-May) | 97,064 | 87,961 | — | −0.14276 | −0.01741 | **+0.12535** | **+45.13** | — | — | — | — |
| POOLED never-read (Apr+May) | 46,341 | 40,591 | — | −0.15766 | −0.02682 | **+0.13084** | **+31.91** | — | — | — | — |

The bar-1 share is the most stable number in the estate: **0.5565 / 0.5707 / 0.5619 / 0.5844 /
0.5966**. Over half of every month's candidate pool has its entry level reached inside 60 seconds.

### 2.1 Cohort table, all five months (CLEAN)

| month | bar 1 | bar 2-5 | bar 6-15 | bar 16-60 | bar 61-120 | never traded |
|---|--:|--:|--:|--:|--:|--:|
| JAN n / honest | 13,436 / **−0.19754** | 2,550 / −0.04568 | 1,918 / −0.02438 | 3,639 / −0.04952 | 2,358 / −0.02568 | 241 / 0.0 |
| FEB n / honest | 12,790 / **−0.20066** | 2,254 / −0.02993 | 1,782 / −0.01376 | 3,134 / **+0.00828** | 2,114 / −0.02199 | 338 / 0.0 |
| MAR n / honest | 14,025 / **−0.22448** | 2,347 / **+0.01512** | 1,970 / −0.02749 | 3,767 / −0.05109 | 2,585 / −0.04606 | 264 / 0.0 |
| APR n / honest | 12,872 / **−0.23684** | 2,300 / −0.04777 | 1,671 / −0.05103 | 2,909 / −0.04815 | 1,984 / −0.04926 | 291 / 0.0 |
| MAY n / honest | 11,076 / **−0.20427** | 1,837 / −0.07745 | 1,422 / −0.05702 | 2,382 / −0.09095 | 1,660 / −0.12987 | 187 / 0.0 |

Resolution win rate, bar-1 cohort vs the k=1 retained book: JAN 0.2074/0.2655, FEB 0.2067/0.2720,
MAR 0.1963/0.2668, APR 0.1922/0.2634, MAY 0.2014/0.2279. **MAY is the weakest month on every axis** —
its later cohorts are themselves negative (−0.130 at bars 61-120), so the rule still fires but the
retained book is poor. That is the one genuine soft spot in the extension.

### 2.2 Full delay sweep, per month (CLEAN, R/opportunity | R/trade | traded)

| k | JAN | FEB | MAR | APR | MAY |
|--:|---|---|---|---|---|
| 0 | −0.12667 / −0.1280 / 23,901 | −0.11953 / −0.1214 / 22,074 | −0.13938 / −0.1409 / 24,694 | −0.15806 / −0.1602 / 21,736 | −0.15719 / −0.1588 / 18,377 |
| **1** | −0.01674 / −0.0386 / 10,465 | −0.00502 / −0.0121 / 9,284 | −0.01323 / −0.0309 / 10,669 | −0.01965 / −0.0488 / 8,864 | −0.03532 / −0.0898 / 7,301 |
| 2 | −0.01322 / −0.0339 / 9,413 | −0.00637 / −0.0171 / 8,350 | −0.01259 / −0.0323 / 9,734 | −0.01766 / −0.0496 / 7,849 | −0.03222 / −0.0916 / 6,531 |
| 5 | −0.01191 / −0.0363 / 7,915 | −0.00201 / −0.0064 / 7,030 | −0.01465 / −0.0439 / 8,322 | −0.01467 / −0.0492 / 6,564 | −0.02765 / −0.0940 / 5,464 |
| 10 | −0.00992 / −0.0355 / 6,747 | −0.00043 / −0.0016 / 5,921 | −0.01359 / −0.0476 / 7,131 | −0.01620 / −0.0641 / 5,565 | −0.02738 / −0.1101 / 4,615 |
| 20 | −0.00704 / −0.0318 / 5,342 | −0.00140 / −0.0066 / 4,730 | −0.01229 / −0.0539 / 5,694 | −0.00794 / −0.0398 / 4,396 | −0.01962 / −0.1008 / 3,612 |
| 60 | −0.00251 / −0.0257 / 2,358 | −0.00207 / −0.0220 / 2,114 | −0.00477 / −0.0461 / 2,585 | −0.00444 / −0.0493 / 1,984 | −0.01161 / −0.1299 / 1,660 |

R/opportunity keeps improving with k while R/trade does not. **Read that honestly: past k=1 the
remaining gain is "trade less", not "trade better."** k=1 is the point that keeps the most volume
while removing most of the loss.

### 2.3 Cross-check in the POOL'S OWN scoring — no e6 walk involved

Every number above uses the honest first-touch walk. This table uses only the pool's own
`gross_r = opportunity_net_proxy_r + cost_r`, so it is independent of the walk entirely. Refused and
never-filled candidates book 0.0. `E6_GROSS_CROSSCHECK_V1.json`.

| month | n | pool gross, as shipped | pool gross, CANCEL k=1 | delta |
|---|--:|--:|--:|--:|
| JAN | 27,658 | **−0.21750** | −0.00427 | **+0.21323** |
| FEB | 24,239 | −0.15055 | **+0.00722** | +0.15777 |
| MAR | 26,484 | −0.17675 | −0.01207 | +0.16468 |
| APR | 25,056 | −0.23189 | −0.00766 | +0.22423 |
| MAY | 21,285 | −0.23867 | −0.02203 | +0.21664 |
| **POOLED** | **124,722** | **−0.20234** | **−0.00740** | **+0.19494** |

January's −0.21750 is the estate's own published pool gross mean (−0.2175) to five decimals, which
validates the reconstruction. **In the pool's own scoring the CANCEL rule removes 96.3 % of the
five-month gross deficit, and February turns positive.** That last cell is flattering — the pool's
scoring still contains the never-filled fiction of §7 — which is exactly why the honest-walk
numbers in §2 are the ones to quote.

---

## 3. THE BOUNDARY — 569 cells, 11 negative

`E6_SWEEP_V1.json -> boundary`. Twelve axes × five months, every cell with n ≥ 100.
**569 cells, 11 negative (1.93 %), largest negative −0.08131 on n=167.**

Ten weakest cells in the whole search:

| delta | axis | month | cell | n |
|--:|---|---|---|--:|
| −0.08131 | blocker | APR | scheduler_selection | 167 |
| −0.07134 | session | JAN | moonshot_h09_10 | 312 |
| −0.04964 | session | MAY | moonshot_h15_16 | 243 |
| −0.04606 | hour | FEB | 18 | 631 |
| −0.04468 | session | FEB | moonshot_h18_19 | 554 |
| −0.02605 | session | MAY | moonshot_h22_23 | 559 |
| −0.01711 | session | MAY | moonshot_h00_01 | 793 |
| −0.00825 | blocker | MAR | selector_materialization | 391 |
| −0.00514 | session | MAR | moonshot_h08_09 | 289 |
| −0.00468 | blocker | MAR | execution_fillability | 427 |

### 3.1 Family — 50 of 50 month-cells positive

| family | pooled n | k=0 | k=1 | **delta** | paired t | bar-1 share | bar-1 mean | later mean |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| structural_distance_extreme | 8,934 | −0.33872 | −0.00264 | **+0.33608** | 30.8 | 0.7679 | −0.43769 | −0.01278 |
| cross_asset_lead_lag | 9,627 | −0.20345 | −0.01562 | +0.18783 | 17.0 | 0.7632 | −0.24611 | −0.07277 |
| current_breaker_re_entry | 3,379 | −0.17966 | −0.03083 | +0.14883 | 14.0 | 0.3131 | −0.47533 | −0.04509 |
| liquidity_sweep_reclaim | 21,036 | −0.12896 | **+0.00371** | +0.13267 | 18.5 | 0.7633 | −0.17381 | +0.01694 |
| current_fvg_fill | 33,224 | −0.14022 | −0.04572 | +0.09450 | 32.5 | 0.2818 | −0.33533 | −0.06371 |
| session_open_range_break | 4,677 | −0.07615 | **+0.00085** | +0.07700 | 6.9 | 0.7372 | −0.10444 | +0.00368 |
| displacement_continuation | 21,056 | −0.07272 | **+0.00285** | +0.07557 | 12.3 | 0.7644 | −0.09887 | +0.01284 |
| volatility_compression_expansion | 2,837 | −0.07101 | −0.01747 | +0.05354 | 5.8 | 0.7515 | −0.07125 | −0.07244 |
| current_ob_retest | 6,026 | −0.08610 | −0.03894 | +0.04716 | 9.0 | 0.1421 | −0.33202 | −0.04546 |
| regime_transition_break | 1,307 | −0.03386 | **+0.00314** | +0.03700 | 2.8 | 0.7521 | −0.04920 | +0.01358 |

Per-month deltas, all 50 cells positive (`E6_SWEEP_V1.json -> boundary.family.<MONTH>`); range
+0.01008 (`regime_transition_break` FEB) to +0.39685 (`structural_distance_extreme` MAY).

### 3.2 Born state — the effect survives inside genuine resting limits

| born | pooled n | k=0 | k=1 | delta | bar-1 share | bar-1 mean | later mean | per-month deltas |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| born_marketable | 7,096 | −0.34801 | −0.00422 | **+0.34379** | 0.9569 | −0.35929 | −0.10503 | .3175/.2854/.3929/.3848/.3135 |
| born_at_limit | 69,502 | −0.14146 | −0.00109 | +0.14037 | 0.7618 | −0.18427 | −0.00495 | .1295/.1384/.1490/.1485/.1362 |
| **born_resting** | 35,488 | −0.09309 | −0.05151 | **+0.04158** | **0.1254** | **−0.33159** | −0.05892 | .0394/.0325/.0352/.0521/.0537 |

This row settles the obvious objection. `born_resting` is the population of genuine limits sitting
*away* from the market at the decision instant — only 12.54 % of them fill on bar 1, and when they do
they book **−0.33159 against −0.05892 for the rest, a 5.6× penalty.** The effect is not an artifact
of orders that were already marketable.

### 3.3 The other axes

- **Symbol**: 120 month-cells, 0 negative. Pooled delta ranges XAUUSD +0.06228 (n=10,295) to NAS100
  +0.16873 (n=6,100). No instrument escapes it.
- **Spread band**: 30 cells, 0 negative, and monotone *above* 0.20 R — `>1.0 R` +0.19234,
  `0.40-1.0` +0.15203, `0.20-0.40` +0.13775, then it turns over: `<=0.05` +0.10575, `0.10-0.20`
  +0.09564, `0.05-0.10` +0.08075. Expensive candidates are hurt most; the cheap end is flat and
  mildly U-shaped, not ordered.
- **Side**: SHORT +0.13345 (n=59,881), LONG +0.10894 (n=52,222); 10 of 10 cells positive.
- **Hour**: all 24 pooled hours positive, +0.06499 to +0.17722.
- **Session**: 27 pooled buckets, all positive, +0.06315 (`moonshot_h00_01`) to +0.20280
  (`moonshot_h21_22`).
- **Order type**: `limit` +0.11899 (n=91,595), `none` +0.13563 (n=20,508).

---

## 4. THE MECHANISM

### 4.1 The "pre-run" is the clock — they are the same variable
`E6_MECH_V1.json -> prerun_ladder`. `prerun_r` = the largest favourable excursion, measured from the
entry level, over the bars **before** the fill. It is 0 **if and only if** the fill is on bar 1: a
later fill requires bar 1 to have closed entirely on the favourable side of entry, which forces
`prerun > 0` strictly. So the two encodings carry identical information — but the ladder is still
informative because it shows the effect is a **STEP, not a gradient**:

| prerun_r | n | share of filled | honest mean | resolution win | median fill bar |
|---|--:|--:|--:|--:|--:|
| **0** | 64,199 | 0.5795 | **−0.21309** | 0.2009 | 1 |
| 0-0.05 | 145 | 0.0013 | −0.04398 | 0.1875 | 2 |
| 0.05-0.10 | 650 | 0.0059 | −0.03461 | 0.1985 | 2 |
| 0.10-0.25 | 3,839 | 0.0347 | −0.01523 | 0.2272 | 3 |
| 0.25-0.50 | 6,549 | 0.0591 | −0.02365 | 0.2516 | 5 |
| 0.50-1.0 | 8,636 | 0.0780 | −0.02657 | 0.2676 | 11 |
| >1.0 | 26,764 | 0.2416 | −0.05468 | 0.2642 | 44 |

The penalty is not a function of *how far* price ran away first — `>1.0 R` is **worse** than
`0.10-0.25 R`. All the value is in crossing zero. And a pure prerun rule buys nothing over the clock
(`prerun ≥ 0.10` −0.01698 vs `clock k=1` −0.01726; combining them is exactly the prerun rule).

### 4.2 What it actually is: a fill into a fast first minute
`E6_MECH_V1.json -> bar1_range_r`. Bucket the pool by the FIRST post-decision minute's own range in
R units:

| first-minute range (R) | n | bar-1 share | bar-1 mean | later mean | k=0 | k=1 |
|---|--:|--:|--:|--:|--:|--:|
| ≤0.05 | 5,586 | 0.6155 | −0.20655 | −0.02399 | −0.13626 | −0.00914 |
| 0.05-0.1 | 11,765 | 0.5742 | −0.12913 | −0.01934 | −0.08228 | −0.00813 |
| 0.1-0.2 | 31,054 | 0.5939 | −0.09632 | −0.02293 | −0.06631 | −0.00911 |
| 0.2-0.4 | 36,282 | 0.5677 | −0.15600 | −0.03472 | −0.10317 | −0.01462 |
| 0.4-0.8 | 19,961 | 0.5306 | −0.36655 | −0.09828 | −0.23899 | −0.04451 |
| **>0.8** | 7,455 | 0.5870 | **−0.73720** | **−0.03040** | −0.44439 | −0.01166 |

**When the first minute's own range exceeds 0.8 R, a bar-1 fill books −0.737 R and a later fill books
−0.030 R — a 24× separation.** The bar-1 share barely moves across the buckets (0.53-0.62), so this
is not a composition effect. This is the mechanism in one table: **a level the market reaches inside
60 seconds is a level the market is moving *through*, and the faster it is moving the worse the fill
is.** Classic adverse selection at the limit, measured.

### 4.3 The control that rules out the 2-hour wall — now on all five months
l8 ran this on January only. `E6_FINAL_V1.json -> F1_equal_exposure` re-runs it over 110,782 filled
clean candidates: resolve each inside a fixed H-bar window measured from its **own** fill bar,
discarding any whose window does not fit before the wall. Equal exposure, equal wall distance.

| H (bars from fill) | bar-1 eligible | bar-1 resWin | later eligible | later resWin | ratio | bar-1 mean R | later mean R |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 15 | 18,939 | 0.0867 | 12,585 | 0.1710 | **1.97×** | −0.21674 | −0.04101 |
| 30 | 26,566 | 0.1299 | 17,619 | 0.2121 | 1.63× | −0.21579 | −0.04336 |
| 45 | 31,592 | 0.1537 | 19,893 | 0.2349 | 1.53× | −0.21268 | −0.04245 |
| 60 | 34,732 | 0.1680 | 20,470 | 0.2530 | 1.51× | −0.21239 | −0.03790 |
| 90 | 39,011 | 0.1898 | 17,242 | 0.2732 | 1.44× | −0.20674 | −0.03036 |

Per month at H=30 the ratio is JAN 1.566, FEB 1.572, MAR 1.781, APR 1.784, MAY 1.338; at H=60,
1.457 / 1.567 / 1.591 / 1.573 / 1.278. **Not a measurement artifact in any month.** At identical
exposure the bar-1 cohort still books ~5× the loss.

---

## 5. THE FOUR CONTROLS

`E6_CONFIRM_V1.json`.

### C1 — CANCEL vs DEFER, per month (the headline)

| month | n | as shipped | DEFER k=1 | CANCEL k=1 | value of delay alone | value of the cancel |
|---|--:|--:|--:|--:|--:|--:|
| JAN | 24,142 | −0.12667 | −0.13140 | −0.01674 | **−0.00473** | +0.11466 |
| FEB | 22,412 | −0.11953 | −0.13013 | −0.00502 | **−0.01060** | +0.12511 |
| MAR | 24,958 | −0.13938 | −0.14484 | −0.01323 | **−0.00546** | +0.13161 |
| APR | 22,027 | −0.15806 | −0.16419 | −0.01965 | **−0.00613** | +0.14454 |
| MAY | 18,564 | −0.15719 | −0.16155 | −0.03532 | **−0.00436** | +0.12623 |
| POOLED | 112,103 | −0.13929 | −0.14557 | −0.01726 | **−0.00628** | **+0.12831** |

Deferring to k=2 and k=5 is worse still: pooled −0.15487 and −0.17854. **The value is entirely in
refusing the candidate, never in waiting for a better price on the same level.**

### C2 — pseudo-replication (W0-F1) does not create it; it DILUTES it
85,271 distinct `candidate_id` across the 112,103 clean rows, max 235 repeats.

| population | n | k=0 | k=1 | delta |
|---|--:|--:|--:|--:|
| all rows (as shipped) | 112,103 | −0.13929 | −0.01726 | +0.12203 |
| **first emission only** | 85,271 | −0.14151 | −0.00932 | **+0.13219** |
| **setup-weighted (one vote per id)** | 85,271 | −0.14875 | −0.01277 | **+0.13598** |
| unique setups (never repeated) | 81,159 | −0.14627 | −0.00780 | **+0.13847** |
| repeated setups | 30,944 | −0.12100 | −0.04210 | +0.07890 |

Every de-duplicated view is **stronger** than the shipped one.

### C3 — per-day sign test: 101 of 101
Every calendar day with ≥30 clean candidates across the five months. **101 days, 101 positive
(100.0 %)** — JAN 21/21, FEB 20/20, MAR 22/22, APR 20/20, MAY 18/18. Worst day 2026-03-10 at
**+0.00169** (n=1,095); next worst 2026-05-12 +0.01066, 2026-02-12 +0.03839.

### C4 — the cost-aware bottom line, stated honestly
Cost charged only on the trades each rule takes. `frozen` is the pool's own cost model; the corrected
columns divide the **spread** limb by the measured 7.3×/8.5× over-charge and leave commission, swap
and the flat slippage allowance untouched.

| book | traded | net R / opportunity | net R / trade |
|---|--:|--:|--:|
| frozen, as shipped | 110,782 | −0.70356 | −0.71195 |
| frozen, CANCEL k=1 | 46,583 | −0.26211 | −0.63076 |
| frozen, CANCEL k=5 | 35,295 | −0.20281 | −0.64416 |
| spread ÷7.3, as shipped | 110,782 | −0.32298 | −0.32683 |
| **spread ÷7.3, CANCEL k=1** | 46,583 | **−0.09074** | **−0.21837** |
| spread ÷7.3, CANCEL k=5 | 35,295 | −0.06804 | −0.21611 |
| spread ÷8.5, as shipped | 110,782 | −0.31445 | −0.31820 |
| spread ÷8.5, CANCEL k=1 | 46,583 | −0.08690 | −0.20913 |

The rule improves **both** measures — +0.232 per opportunity and +0.108 per trade at the corrected
spread — so it is not purely a volume effect. **It does not make the pool profitable.** The retained
book is −0.218 R/trade.

---

## 6. THE BANKABILITY SEARCH — and it comes back empty

`E6_FINAL_V1.json -> F2_bankability`. Over the 46,583 retained (k≥2) clean trades, net of the
7.3×-corrected cost, is there ANY cell that is positive in all five months?

**No. Not one cell in any axis is positive even once pooled, and none is positive in more than 3 of
5 months.** Best cells:

| axis | best cell | n | net R/trade | t | months positive |
|---|---|--:|--:|--:|--:|
| family | regime_transition_break | 302 | −0.04528 | −1.37 | 0/5 |
| family | session_open_range_break | 1,078 | −0.08225 | −2.93 | 1/5 |
| family | displacement_continuation | 4,681 | −0.09778 | −6.62 | 0/5 |
| symbol | UKOIL_cash | 1,312 | −0.01744 | −0.63 | 2/5 |
| symbol | GER40 | 3,426 | −0.02098 | −1.09 | 3/5 |
| symbol | XAUUSD | 6,829 | −0.04826 | −3.17 | 1/5 |
| born | born_at_limit | 15,272 | −0.18622 | −19.80 | 0/5 |
| born | born_resting | 31,023 | −0.23362 | −35.97 | 0/5 |

**This is the honest boundary of the find. L8-F1 is a very large, very general LOSS-AVOIDANCE
mechanism. It is not, by itself, an edge.** It recovers 93.1 % of the raw pool's gross deficit and
leaves a residual that the corrected cost model still eats.

---

## 7. SECONDARY FIND — W0-F2's fiction reproduces in every month

The never-filled cohort — candidates the pool scores at a large positive R that **never traded at
all** — is present in all five months at almost identical magnitude:

| month | n never filled | pool-scored gross mean | pool-scored total |
|---|--:|--:|--:|
| JAN | 241 | +1.54767 | +373.0 R |
| FEB | 338 | +1.70432 | +576.1 R |
| MAR | 264 | +1.41121 | +372.6 R |
| APR | 291 | +1.58307 | +460.7 R |
| MAY | 187 | +1.70323 | +318.5 R |
| **pooled** | **1,321** | **+1.59030** | **+2,100.8 R** |

W0-F2 was measured on January. It is a permanent property of the scoring convention.

---

## 8. WHAT WOULD MAKE THIS BANKABLE

The find is measured, general and mechanistic. Three specific things stand between it and money.

1. **It applies to a decision surface that is not armed.** This pool is the broad-V4 selector's
   diagnostic exhaust — `w0_DATA_DICTIONARY.md` D3: **zero executed trades, 18.03 % of its own
   ledger, built by a filter that requires `not headline_r_scoreable`.** The live book is the
   three/five-sleeve `ultimate_book`. **The single cheapest next test is to run the same instrument
   over the `ultimate_book` sleeves' own entries** — do armed sleeves also fill inside 60 s at 56 %,
   and do those fills carry the same −0.2 R? Nothing in this receipt licenses a live change until
   that is measured, and it needs no new data.
2. **It is a filter, not a signal.** §6 is unambiguous: after the filter the retained book is still
   −0.218 R/trade at the corrected spread. Banking it requires pairing it with something that is
   positive gross. Its value is that it removes 58 % of the pool's candidates and 93 % of its
   deficit, which makes every *other* candidate-level search cheaper and less contaminated —
   **every downstream lane should run on the CANCEL-filtered population, not the raw one.**
3. **The implementation is specific and one of the two obvious forms is wrong.** Live it is:
   at decision time do **not** submit; at decision + 60 s read the closed M1 bar; if its range
   contains the entry level, **drop the candidate**; otherwise submit the limit. A 60-second arming
   delay *without* the drop is measured at **−0.00628 pooled and negative in all five months** — it
   would be a small, permanent tax that looks like the repair.

Two further tests that would sharpen it, in cost order:
- **Sub-minute resolution.** The M1 grid cannot say whether the level traded at second 3 or second 58.
  The tick archive at `/Users/borr/GTOSActive/vps-ticks-20260726/` (263.9 M rows) covers 2026-06-18..07-24
  only, so it cannot test these months — but it can test the *shape* on a live-adjacent window.
- **The `>0.8 R first-minute range` cell (§4.2, n=7,455, bar-1 mean −0.737).** If a pre-decision
  volatility state predicts that cell, the filter becomes a *pre-trade* gate rather than a
  post-decision one, which is strictly cheaper to run.

---

## 9. DATA SPENT — for the estate's record

| pack | rows used | prior status | what e6 spent it on |
|---|--:|---|---|
| **CS_APRIL_S0R0_POOL_V1 + ORDERED_PATH_SIDECAR** | 25,056 | **economics never read** | ONE pre-declared instrument ported unchanged from l8 — the entry-delay cohort split, its delay sweep and the twelve boundary axes. No search preceded it. |
| **CS_MAY_S0R0_POOL_V1 + ORDERED_PATH_SIDECAR** | 21,285 | **economics never read** | same instrument, same axes |
| FA2_M_R0_MISSED_OPPORTUNITY_LEDGER (March reference arm) | 26,484 of 26,500 diagnostic-scoreable (16 lack post-decision bars) | already read once (phase19/march-confirm) | same instrument |
| CP_FEBRUARY_S0R0_POOL_V1 | 24,239 | used-once VAL (wave 18) | same instrument |
| CJ_RECLOCKED_S0R0_POOL_V1 + CQ sidecar | 27,658 | l8's own | reproduction only |

**Declared honestly**: April and May were opened for the first time by this lane. They were used for
a single pre-specified confirmation, not a search — the rule, its k grid and its conditioning axes
were all fixed by l8's January receipt before either file was read. No multiplicity correction is
applied anywhere in this receipt; the 569-cell census in §3 is reported as a census, not as 569
independent tests.

---

## 10. ARTIFACTS

Scripts (all in this directory, all re-runnable):
`e6_repro_jan.py`, `e6_build_month.py`, `e6_sweep.py`, `e6_mech.py`, `e6_confirm.py`,
`e6_final.py`, `e6_result.py`.

Measurements: `E6_JAN_REPRO_V1.json`, `E6_SWEEP_V1.json`, `E6_MECH_V1.json`, `E6_CONFIRM_V1.json`,
`E6_FINAL_V1.json`, `e6_RESULT.json` (everything merged).

Derived frames (one row per candidate, five months):
`e6_FRAME_{JAN,FEB,MAR,APR,MAY}.jsonl.gz` — fill bar, honest R, outcome, born state, axes.
`e6_MECH_{JAN,FEB,MAR,APR,MAY}.jsonl.gz` — the above plus `prerun`, first-bar range, and the
DEFER-variant outcomes at k=1/2/5.
