# Lane d5 — THE SEPARATOR, re-tested on the correct object

Wave 19 broad forensic. **Eight open windows, the reproduced sealed rosters** (Session PB), not the
counterfactual pool. **1,126,270 candidate emissions** — the whole population, in every table.
Nothing is sampled and nothing is estimated. Scripts and JSON are named at each claim. The sealed
three (Jun/Aug/Sep 2025) were never opened.

---

## 0. HEADLINE

**The separator is real, it is 2.3× the estate's standing ceiling, and it is not information — it
is a description of a fill that has already happened. At every fill a book can actually have, it
is worth zero to eight decimal places.**

| the observable, on the correct object | Cohen's d | AUC |
|---|--:|--:|
| x4's figure on the counterfactual pool (the wrong object) | 0.3348 | 0.5912 |
| **on the ROSTER, at the estate's own fill convention** | **0.3548** | 0.6130 |
| on the roster, once the order fills on the side a broker would fill it | **0.0851** | 0.5488 |
| on the roster, restricted to orders still UNFILLED when it becomes readable | **0.0438** | 0.5149 |

And the action it implies, priced per opportunity over all 1,126,270 emissions:

| | gross/opportunity | net/opportunity | achievable? |
|---|--:|--:|---|
| baseline — rest the limit at T | −0.02379 | −0.10659 | — |
| ORACLE — refuse every `c0 ≤ −0.15` | +0.01111 | −0.05347 | **NO** |
| **cancel the order at T+1m when `c0 ≤ −0.15`** | **−0.02379** | **−0.10659** | yes |
| | **Δ = +0.00000000** | **Δ = +0.00000000** | |

**64,427 of the 64,428 rows in the refused cohort are already filled at the instant the observable
exists.** The one exception was never filled and already books 0.0. The refusal rule cannot be
executed — not at a different threshold, not at a different cost, not in a different month. It is
an ordering problem and it is exact: 1.000000 prefilled in 7 of 8 windows and 0.999885 in the 8th.

**Then the mechanism behind the mechanism, which is the part that reaches the wave's question.**
`c0 ≤ −0.15` looks powerful because it selects, at 89 % concentration, the rows whose entry price
the market had **already left before the decision instant**. The estate's walk fills those at a
price that never traded again. They are **3.09 % of the roster and they carry 99.88 % of its entire
negative gross.** Fill them the way a broker would — a BUY above the market is a STOP and fills on
`high ≥ e` — and

- their gross goes **−0.76912 → +0.01042 R/opportunity** and their stop rate **84.2 % → 13.2 %**;
- the whole roster's gross goes **−0.02379 → +0.00029 per opportunity**, **−0.07963 → +0.00106 per fill**;
- its win rate lands at **38.70 % against a 38.65 % breakeven — a gap of +0.05 pp.**

**Zero. And zero separately at all three order geometries**: reachable limits +0.00034, at-market
−0.00254, stop-entries +0.01042 R per opportunity. The broad family's directional content is not
negative and not repairable-negative — it is **absent**, and the negativity every prior lane
published was the accounting, not the setups.

---

## 1. The observable, identified exactly (mission item 1)

From `x4_RESULT.md` §5, verbatim:

```
c0_close_fav_r = s * (close of the M1 bar [T, T+1m) − entry_price) / risk_distance
                 s = +1 LONG, −1 SHORT
```

Negative means price has already run **against** the entry inside the first minute after the
decision instant. x4's own V1 check established that this is byte-identical to
`w0cap2_DECISION_ANCHOR_V1.mkt_r_close` — a field the estate already had and used only as a binary
born-state classifier.

Reconstructed here on the roster in `d5_build.py`, from the same M1 source x4 used
(`lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/`
`LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_*`), for all eight open windows.

**Its PRE-decision twin, which this lane needs throughout and names once:**

```
mkt_r0 = s * (close of the M1 bar [T−1m, T) − entry_price) / risk_distance
```

the position of the market relative to the entry **at the decision instant** — knowable at T, one
minute earlier than `c0`, with no delay and no new data.

| `mkt_r0` | what the order is | share of the roster |
|---|---|--:|
| `> 0` | a genuine resting limit at price improvement | 84.52 % |
| `= 0` | the entry **is** the market — an at-market order | 12.39 % |
| `< 0` | the entry sits **beyond** the market in the losing direction | **3.09 %** |
| `≤ −1` | ... beyond its own stop: born dead | 2.08 % |

---

## 2. Does d = 0.3348 survive the object change? (mission item 2)

**Yes — and that is the least interesting thing about it.** Honest first-touch target vs stop,
whole population, every open window (`d5_01_survive.py` → `D5_01_SURVIVE.json`;
`d5_13_final.py` → `D5_13_FINAL.json`):

| window | n rows | d, estate fill convention | AUC | d among rows filled inside minute 0 | **d among rows still UNFILLED at T+1m** | d, broker-correct labels | **d, broker-correct AND actionable** |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2025-10 | 163,604 | +0.3255 | 0.6044 | 0.5885 | +0.0248 | +0.0557 | **+0.0215** |
| 2025-11 | 141,324 | +0.3986 | 0.6156 | 0.6100 | +0.0009 | +0.0338 | **−0.0043** |
| 2025-12 | 150,095 | +0.3893 | 0.6285 | 0.5585 | +0.0116 | +0.0970 | **+0.0127** |
| 2026-01 | 145,554 | +0.4016 | 0.6249 | 0.6237 | +0.0833 | +0.0916 | **+0.0610** |
| 2026-02 | 122,490 | +0.2599 | 0.5915 | 0.4961 | +0.0015 | +0.0477 | **−0.0075** |
| 2026-03 | 124,222 | +0.2308 | 0.5797 | 0.4014 | +0.0482 | +0.0738 | **+0.0449** |
| 2026-04 | 135,934 | +0.4355 | 0.6431 | 0.5662 | +0.1218 | +0.1777 | **+0.1390** |
| 2026-05 | 143,047 | +0.3607 | 0.6155 | 0.5227 | +0.0802 | +0.1123 | **+0.0849** |
| **pooled** | **1,126,270** | **+0.3548** | **0.6130** | **+0.5434** | **+0.0464** | **+0.0851** | **+0.0438** |

Pooled cohorts: 70,188 targets vs 188,239 stops (estate labels); 40,922 vs 92,424 on the actionable
population.

**The split is the whole finding.** Where the order is already filled when `c0` becomes readable it
separates at d ≈ 0.54. Where it is not — the only place a decision can be taken — it separates at
**0.0438 pooled, below the estate's own 0.152 ceiling in 8 of 8 windows.**

---

## 3. The fill question — every achievable fill, enumerated and priced (item 3)

### 3.1 The mechanical identity, proved not asserted

`d5_08_verify.py` → `D5_08_VERIFY.json`.

For a resting limit at price improvement (`mkt_r0 > 0`), a LONG's minute-0 low is ≤ its minute-0
close, so `c0 < 0` (close strictly below `e`) forces `low < e` — the level traded, the order filled.
Measured on the exact population that could falsify it:

> **4,437 rows with `mkt_r0 > 0` and `c0 < 0`. Violations (`j ≠ 0`): 0.**

The identity holds exactly, in both sign conventions, in every window.

### 3.2 The refused cohort, partitioned by when it fills

| threshold | n refused | gross of the refused set | already filled at T+1m | still pending (cancellable) | **% of the avoided loss a cancel can reach** |
|---|--:|--:|--:|--:|--:|
| `c0 ≤ −0.30` | 45,447 | −0.7781 | **45,447** | 0 | **0.0 %** |
| `c0 ≤ −0.15` | 64,428 | −0.6101 | 64,427 | 0 | **0.0 %** |
| `c0 ≤ −0.05` | 89,479 | −0.4677 | 89,478 | 0 | **0.0 %** |
| `c0 ≤ 0.00` | 110,315 | −0.3842 | 110,314 | 0 | **0.0 %** |

The one non-prefilled row in the last three bands is the same row, never filled, already booking
0.0. At `c0 ≤ −0.30` there is not even that.

### 3.3 Every physically achievable action, priced per opportunity

`d5_10_arms.py` / `d5_13_final.py`. All arms share one denominator (the emission count), so a
refusal books exactly 0.0 and the arms are directly comparable. Intervals are day-clustered on the
**paired** per-row difference, so the toll and the row set cancel exactly. N = 1,126,270.

| arm | legal from | gross/opp | net/opp | Δnet vs baseline | 95 % CI, day-clustered | windows improving |
|---|---|--:|--:|--:|---|--:|
| **A0** rest the limit at T (shipped) | T | −0.02379 | −0.10659 | — | [−0.11102, −0.10216] abs | — |
| **A1** ORACLE refuse `c0 ≤ −0.15` | *never* | +0.01111 | −0.05347 | +0.05313 | [+0.04993, +0.05632] | 8/8 |
| **A2** cancel at T+1m when `c0 ≤ −0.15` | T+1m | −0.02379 | −0.10659 | **+0.00000000** | **[0.00000, 0.00000]** | 0/8 |
| **A3** place nothing at T; place the same limit at T+1m if `c0 > −0.15` | T+1m | −0.00180 | −0.06512 | **+0.04148** | [+0.03826, +0.04470] | 8/8 |
| A3b place at T+1m unconditionally | T+1m | −0.03553 | −0.11706 | −0.01047 | — | 0/8 |
| **A5** at T, place only orders at price improvement (`mkt_r0 > 0`) | **T** | +0.00029 | **−0.03800** | **+0.06860** | [+0.06481, +0.07238] | 8/8 |
| **A11** broker-correct fill side, nothing else changed | T | +0.00029 | −0.07664 | +0.02995 | [+0.02677, +0.03313] | 8/8 |
| A11b A11 then cancel on `c0 ≤ −0.15` | T+1m | +0.00002 | −0.07587 | +0.03073 | — | 8/8 |
| A6 market order at T on every candidate | T | +0.01247 | −0.22786 | −0.12127 | — | 0/8 |

A2's interval is not rounded. It is a **degenerate zero interval**: the paired per-row difference
is identically 0.0 on all 1,126,270 rows, because there is no row on which the arm acts.

**Read it in this order.**

1. **A2 is the honest form of x4's rule and it is worth exactly nothing** — to eight decimals, in
   every window. Not small: zero.
2. **A3 is the only construction that makes the confirm minute legal**, and it does work: +0.04148
   net, 8/8. But it decomposes as **+0.05194 from the conditioning and −0.01047 from the delay**, and
   the delay's cost is concrete and measured: waiting one minute forgoes **4,726 of 336,464 fills
   (1.40 %)**, and those forgone fills average **+1.7010 R gross** — they are precisely the fills
   where the market came to the limit and left immediately in the trade's favour.
3. **A5 beats it, is available a full minute earlier, and needs no confirm minute at all**
   (+0.06860 vs +0.04148 net). It is the same information: 48.2 % of the `c0`-adverse cohort was
   already flagged at T by `mkt_r0 < 0`, and those rows carry **68.1 %** of the R it "avoids"
   (`d5_02b_arms.py` → `D5_02B_ARMS.json` `overlap`).
4. **A6 is the reminder of what this estate's problem actually is.** A market order at T has the
   best gross of any arm (+0.01247) and the worst net (−0.22786), because it fills 100 % of
   candidates and pays the toll on every one. Nothing in this lane changes that arithmetic.

### 3.4 The fill convention itself is the largest single number in this lane

`d5_09_delayed.py` (`gs`/`js`), `d5_11_residual.py` → `D5_11_RESIDUAL.json`.

The estate's walk fills a BUY on `low ≤ e` **whatever side of `e` the market is on**. For an entry
above the market that is neither a limit nor a stop — it is a fill at a price that never traded.
Selecting the touch side by the market's own position at T changes **only those rows**:

| segment (by `mkt_r0` at T) | share | share with `c0 ≤ −0.15` | fill rate, estate → broker-correct | gross/opp, estate → broker-correct | total R, estate → broker-correct | stop share, estate → broker-correct |
|---|--:|--:|--:|--:|--:|--:|
| reachable limit `> 0` | 84.52 % | 0.26 % | 0.1715 → 0.1715 | +0.00034 → +0.00034 | +322 → +322 | 9.5 % → 9.5 % |
| at market `= 0` | 12.39 % | 22.13 % | 0.9923 → 0.9923 | −0.00254 → −0.00254 | −354 → −354 | 49.3 % → 49.3 % |
| **beyond the market `< 0`** | **3.09 %** | **89.28 %** | **0.9998 → 0.3033** | **−0.76912 → +0.01042** | **−26,759 → +362** | **84.2 % → 13.2 %** |

Total estate R over the eight windows is **−26,791.7**; the third row alone is **−26,759.1**, i.e.
**99.88 %**. The 0.3033 broker-correct fill rate is the honest one: a breakout entry triggers 30 %
of the time within the 120-minute cap.

**Whole-roster consequence** (`d5_13_final.py` `contracts`):

| contract | fills | gross/fill | toll/fill | net/opp | win rate | breakeven | gap |
|---|--:|--:|--:|--:|--:|--:|--:|
| estate limit-from-T | 336,464 | −0.07963 | 0.27718 | −0.10659 | 35.51 % | 38.91 % | **−3.40 pp** |
| **broker-correct fill side** | 312,234 | **+0.00106** | 0.27752 | −0.07664 | **38.70 %** | **38.65 %** | **+0.05 pp** |
| market at T | 1,126,270 | +0.01247 | 0.08280 | −0.07034 | 39.27 % | 38.73 % | +0.54 pp |
| limit placed at T+1m | 331,738 | −0.12062 | 0.27680 | −0.11706 | 34.10 % | 39.30 % | −5.20 pp |

(The market arm's smaller toll per fill is composition, not a cheaper broker: it fills every
candidate including the wide-stop POI rows, where `cost_r = cost_px / d` is small by construction.)

---

## 4. Genuine separator or a proxy? (item 4)

`d5_03_hunt.py` → `D5_03_HUNT.json` (8 controls × 20 features × 3 populations);
`d5_12_hunt2.py` → `D5_12_HUNT2.json` (the same, on broker-correct labels).

**It survives all eight conventional controls and dies on the ninth.** Raw d = 0.3548.

| control | `c0`'s within-stratum d | rank-normalised inside the stratum |
|---|--:|--:|
| symbol | 0.3413 | 0.3848 |
| hour | 0.3528 | 0.3925 |
| family | 0.3550 | 0.4130 |
| cost decile | 0.3522 | 0.3949 |
| risk-distance decile | 0.3565 | 0.3908 |
| ATR decile | 0.3211 | 0.3313 |
| geometry decile | 0.3270 | 0.3360 |
| `mkt_r0` decile (the PRE anchor) | 0.3425 | **0.2454** |
| **the fill contract (broker-correct labels)** | **0.0851** | — |
| **the fill contract + actionability** | **0.0438** | — |

Within-symbol rank normalisation *raises* it (x4 saw the same), so it is not a re-discovery of
`symbol`; cost, hour, volatility, geometry and family each remove ≤ 0.034. The only conventional
control that bites is rank-normalising inside `mkt_r0` deciles (0.3548 → 0.2454) — the first sign
of where this goes. **The ninth control is not a covariate at all; it is the measurement.**

The cleanest form of the same test: **restrict to the 951,978 rows that are physically reachable
resting limits and nothing else changes.** There, `c0`'s d is **0.0539** (AUC 0.5189, n = 130,035
resolved), its adverse cohort is 0.26 % of rows and 100 % prefilled, the ORACLE refusal is worth
**+0.00123** R/opportunity and the achievable cancel **+0.00000**. The segment's own gross is
**+0.00034**.

And the strongest **PRE** field says it from the other side: `mkt_r0` alone scores **d = +0.3284 /
AUC 0.5792** under the estate convention and **+0.0460 / 0.5123** under the broker-correct one.

---

## 5. Hunting for more separators in the same place (item 5)

Nineteen observables built from the M1 tape — everything inside the decision bar, the confirm
minute, and the four minutes after it — each stamped with the instant it becomes legal, ranked on
the population that can act on it. The estate's standing ceiling is |d| = 0.152.

**On the population where a refusal is available** (unfilled at T+1m, broker-correct labels,
n = 133,346 resolved):

| feature | class | d | AUC | min \|d\| after any single control |
|---|---|--:|--:|--:|
| `geo` = risk distance ÷ decision-bar range | PRE | −0.1173 | 0.4710 | 0.0208 |
| `risk_bps` | PRE | −0.0939 | 0.4763 | 0.0258 |
| `atr60_r` | PRE | +0.0816 | 0.5283 | 0.0138 |
| `barrng_r` | PRE | +0.0752 | 0.5290 | 0.0194 |
| `mom5` = c4 − c0 | CONFIRM+ | +0.0669 | 0.5156 | 0.0665 |
| `c4` (T+5m) | CONFIRM+ | +0.0632 | 0.5226 | 0.0439 |
| `c0_rng` | CONFIRM | +0.0596 | 0.5275 | 0.0378 |
| `fav5`, `c1`, `c0_fav`, **`c0`**, `adv5`, `mkt_r0`, `c0_adv`, `cost_r`, `vol0_ratio`, `disp0`, `touch0` | — | ≤ 0.054 | ≤ 0.521 | — |

> **Nothing reaches 0.152. The maximum over all nineteen is 0.1173, and it is a PRE field that
> collapses to 0.021 under one control.** The estate's ceiling stands exactly where it was, on the
> only population where beating it would mean anything.

Features that *do* beat the ceiling, and why each is disqualified:

| feature | d | population | why it is not a usable separator |
|---|--:|---|---|
| `c4` (T+5m) | +0.4134 | estate labels | postdates the fill *and* the label; 6.2 % of targets and 12.1 % of stops are already resolved at the observation instant (`D5_04_ACTIONABLE.json`) |
| `fav5` / `c1` / `adv5` | 0.37–0.38 | estate labels | same |
| **`c0`** | +0.3548 | estate labels | postdates its own fill (§3.1) |
| `mkt_r0` | +0.3284 | estate labels | the fill artifact itself, seen directly |
| `mom5` = c4 − c0 | +0.3046 | broker-correct labels | the position's own path from T+1m to T+5m |
| `disp0` = c0 − mkt_r0 | +0.2033 | broker-correct labels | the confirm minute's displacement on an already-filled position |
| `c4` | +0.1828 | broker-correct labels | same |

And the economic answer for the two survivors, which is what matters: the best exit-rule cell
anywhere in the post-fill set is worth **+0.00223 R/opportunity** (`mom5`, `d5_04_actionable.py`),
and **exiting an adverse fill at the confirm close is worse than holding in every band**
(`d5_05_exit.py`: the hold beats the immediate exit in all four adverse bands; the best exit cell
over eleven thresholds is **−0.00015 R**). There is no exit action in the confirm minute either.

---

## 6. Agreement with x4 on x4's own object, then the reconciliation

`d5_06_pool_repro.py` → `D5_06_POOL_REPRO.json`; `d5_14_pool_anchor.py` → `D5_14_POOL_ANCHOR.json`.

Before disagreeing with x4, reproduce it. On the 27,658-row January counterfactual pool, joining
x4's own intra-bar file:

| | x4 published | d5 measured |
|---|--:|--:|
| refused set `c0 ≤ −0.15`, honest R | −0.66506 | **−0.66522** |
| kept set | −0.05327 | −0.05050 |

**Then the reconciliation.** The pool and the roster differ in exactly the way the mechanism
predicts:

| | roster | counterfactual pool |
|---|--:|--:|
| share of rows whose entry the market had already left (`mkt_r0 < 0`) | **3.09 %** | **17.38 %** |
| share born past stop | 2.08 % | 12.75 % |
| share of the refused cohort that is `mkt_r0 < 0` | 48.2 % | 52.8 % |
| share of the refused cohort born past stop | 36.4 % | 42.4 % |
| share of the population's total negative R from `mkt_r0 < 0` rows | **99.88 %** | **59.9 %** |
| the population's honest R on `mkt_r0 ≥ 0` rows only | — | −0.1139 |

The pool is enriched **5.6×** in unreachable rows, which is why x4's effect measured larger there.
The engine even carries a field for this that no prior lane used:
`limit_marketable_at_decision`, `True` on 3,172 pool rows and **never `False` on a row the tape
says is unreachable** (0 of 915).

---

## 7. What this settles, and what would have to be true

**SIGNAL.** At the broker-correct fill contract the broad family's gross expectancy is **+0.00106
R/trade** — win rate 38.70 % against a 38.65 % breakeven, a **+0.05 pp** gap — and it is zero
*separately* at all three order geometries (+0.00034 / −0.00254 / +0.01042 per opportunity). There
is nothing to repair, nothing to invert, and no sub-population hiding it. This **confirms and
sharpens f1**: "the signal is ZERO, not negative" is right, and the residual −0.57 pp f1 measured
on its clean roster is itself the fill convention rather than the setups. It also sits exactly
where f2 put it — f2's paired-signal estimate was +0.0032 ± 0.0103 R/trade with a detection floor
near 0.010, and this lane's independent construction lands inside that band.

**USAGE.** The published negativity is an accounting artifact carried by 3.09 % of rows. The
downstream stack is not destroying a good signal (f1 measured that it *adds*); the walk was
charging a loss to a fill that never existed. That is a **measurement** defect, and correcting it
removes 99.88 % of the roster's negative R without touching a single trading decision.

**What would have to be true for the confirm-minute rule to be worth anything.** The fill would
have to lag the observable. It does not, and the reason is structural rather than incidental: for a
resting limit, "price ran against the entry" and "the limit was hit" are *the same event*. The only
way to buy the ordering is to stop resting the order at T — arm A3 — which costs 1.40 % of fills
worth +1.70 R each and is still beaten by a rule available at T with no delay at all. **A faster
poll does not help either**: x4 §9 measured 76–98 % of M15 boundaries already moving within one
second of the close, so acting earlier moves the fill earlier too, in the same direction.

**What would have to be true for the family to be viable at all.** Unchanged by this lane and worth
restating in its numbers: gross **+0.00106** per fill against a toll of **0.27752** per fill. The
gap is **0.2765 R/trade**, or **9.22 pp** of win rate — **184×** the +0.05 pp the setups actually
deliver, and **28×** f2's detection floor. Every arm measured here moves net by at most +0.069, and
every arm that moves it does so by **trading less**, never by choosing better.

---

## 8. Limits, stated

1. **The three regenerated rosters reproduce the originals to the row** — January 153,598 = 153,598,
   February 129,287 vs 129,231 (+0.04 %), March 130,051 = 130,051 — and every derived row count
   matches the pre-existing feature table exactly (145,554 / 122,490 / 124,222). The other five
   windows use the rosters f1 generated. All eight windows carry every table in this receipt.
2. **`no_prev_close` drops 4.34 %–11.80 % of emissions** per window (median 6.1 %; the 11.80 % is
   December 2025) — rows whose M1 bar at `T−1m` is absent, concentrated at session opens. They have
   no `mkt_r0` and no `c0` by construction, so no lane using either can score them.
3. The **2-hour path cap** bounds every walk here as it does every other wave-19 lane. The 0.3033
   broker-correct fill rate on stop-entry rows is a rate *within 120 minutes*; a longer cap would
   raise it and could move that segment's gross either way.
4. The **toll is the frozen h1 broker-true basis**, charged once per fill in price units over the
   arm's own risk distance. f1 §6's oil-CFD caveat applies unchanged.
5. **The broker-correct fill side is inferred from the market's position at T, not read from an
   order-type field.** The generator does not emit one; `limit_marketable_at_decision` exists in the
   pool but is null on 84.8 % of rows. The inference is the only construction consistent with a real
   broker, and it is falsifiable: if the generator intends these as marketable limits, the correct
   fill is the *market* price (arm A6 on that segment, +0.01996) — which is also positive, so the
   sign of the conclusion does not depend on the choice.
6. **No multiplicity correction is applied.** This is a discovery lane; the headline is a null plus
   a mechanical identity with zero violations, and under-reporting a null is not what multiplicity
   guards against.
7. **The sealed three (Jun/Aug/Sep 2025) were not opened, read, joined or scored at any point.**

---

## 9. Artifacts

All under `phase19/receipts/discovery/`.

The two row-level tables are **not committed** — 8 windows × ~17 MB each, regenerable in ~25 s per
window from the scripts below plus a roster directory. They were held at `/tmp/d5/out/` for this
lane. Regenerate a roster with
`pbg_run.py --month <YYYYMM> --min-rr 1.5 --workers 3 --out <dir>` (use ≤ 3 workers: at 5 the pool
died silently mid-month twice, leaving zero-byte day files that read as a short month), then
`python3 d5_build.py <window>` and `python3 d5_09_delayed.py <window>`.

| file | what |
|---|---|
| `d5_build.py` → `D5_<window>.npz` (8, uncommitted) | the confirm-minute feature table on the roster, 29 columns |
| `d5_09_delayed.py` → `D9_<window>.npz` (8, uncommitted) | the achievable-fill walks: delayed placement, market at T and at T+1m, broker-correct fill side |
| `d5_01_survive.py` → `D5_01_SURVIVE.json` | item 2: does d survive, per window, with the fill-state split |
| `d5_02_fill.py` → `D5_02_FILL.json` | the fill-state and order-type census of the refused cohort |
| `d5_02b_arms.py` → `D5_02B_ARMS.json` | first arm pass and the PRE/CONFIRM overlap |
| `d5_03_hunt.py` → `D5_03_HUNT.json` | items 4 and 5: 20 features × 8 controls × 3 populations |
| `d5_04_actionable.py` → `D5_04_ACTIONABLE.json` | the ranking restricted to populations that can act |
| `d5_05_exit.py` → `D5_05_EXIT.json` | the exit-at-the-confirm-close action, by `c0` band |
| `d5_06_pool_repro.py` → `D5_06_POOL_REPRO.json` | reproduction of x4 on x4's own object |
| `d5_07_pre.py` → `D5_07_PRE.json` | the PRE-only repair, priced per window |
| `d5_08_verify.py` → `D5_08_VERIFY.json` | the mechanical identity; 0 violations |
| `d5_10_arms.py` → `D5_10_ARMS.json` | the achievable-fill arms table |
| `d5_11_residual.py` → `D5_11_RESIDUAL.json` | the residual on physically reachable limits only |
| `d5_12_hunt2.py` → `D5_12_HUNT2.json` | every observable re-ranked on broker-correct labels |
| `d5_13_final.py` → `D5_13_FINAL.json` | the pooled and per-window receipt tables |
| `d5_14_pool_anchor.py` → `D5_14_POOL_ANCHOR.json` | the pool/roster reconciliation |
| `d5_lib.py`, `d5_ci_check.py` → `D5_CI_CHECK.json` | shared statistics; the day-clustered interval validated against a 2,000-draw block bootstrap (agrees to 3 decimals on three cohorts) |
