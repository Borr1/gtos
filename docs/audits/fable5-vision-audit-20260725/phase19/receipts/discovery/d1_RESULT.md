# d1 — IS IT THE SLEEVES? Signal quality, judged on its own terms

Lane d1, wave 19 broad-forensic. Whole population, eight windows, nothing sampled.

**Verdict in one line.** The broad V4 family's *moment* selection carries a small, real,
month-stable positive on its seven at-market families and nothing on its three POI families;
its *direction* call is worth **less than a coin flip on its own rows** across the whole
population (−0.01747 R/trade, p 0.0018, 1 of 8 months positive); and even the best cohort's
total measured value is **3.9 % of the toll those same rows pay.** The signal is not absent.
It is real, it is small, and it is **13–26× too small for the fee schedule it is spent on.**
No downstream repair reaches that gap, because the gap is on the signal side of the ledger.

---

## 0. What was measured, and against what

**Population.** Session PB's reproduced sealed candidate rosters — the trades the system
actually *emitted*, not the counterfactual missed-opportunity pool. 1,142,785 close-only
emissions over eight windows (2025-10, 2025-11, 2025-12, 2026-01, 2026-02, 2026-03, 2026-04,
2026-05), restricted to each arm's own trading days, deduplicated on the setup key.
333,545 honest fills; **310,983 clean fills** after removing rows born already past their
stop. 163 trading days. 24 instruments. 10 origin families.

`origin_family` is the finest label that survives emission — there is no sub-spec field in
the roster — so "per sleeve spec" is delivered as **family × instrument** (T-breadth),
**family × side** (T12) and **family × risk-distance decile** (T11).

**Contract, identical for the real arm and for every control.**

| | |
|---|---|
| fill (7 at-market families) | market fill at the generator's own emitted entry price `e` |
| fill (3 POI families) | honest resting limit at `e`; buy fills on `low<=e`, sell on `high>=e`, scanned over stamps `i .. i+119`; never touched → 0.0 R, no toll |
| exit | stop −1R, target +2.0R (the downstream contract), else the last close of the forward path; forward path = stamps `i+j+1 .. i+120`; tie inside one M1 bar → the STOP wins |
| toll | h1 four-term broker-true: hour-aware tick spread + broker-true commission + measured price-unit slippage + swap, in price units ÷ the arm's own risk distance |
| secondary geometry | the whole lane is re-run at **1.5R**, which is what `risk.min_rr` actually emits (T9). Every sign and every ordering is unchanged. |

**Harness validation — exact, not approximate.** On January's at-market cohort this lane
reproduces f2's R1 baseline to **every printed digit**: n = 17,722, gross +0.038180, cost
0.335605, net −0.297425. f2's R1 in turn matched Session PB's sealed `close_arm` to every
printed digit. The chain from the sealed arm to this table is closed.

**Why the controls are exact rather than sampled.** The R-frames are *linear in side*: for a
fixed entry and risk distance, the short frame is the exact negation of the long frame with
high and low swapping roles. So walking each row once "as long" and once "as short" gives the
outcome of **any** side assignment by a select. The coin flip's expectation is therefore a
closed form — `(g_long + g_short) / 2` — with **zero sampling error**, and every direction
control (matched-random, two shuffles, anti) is exact. A 200-draw sampled coin flip
reproduces the closed form to 4 decimal places (+0.014437 vs +0.014520) and is used only
where win rate and payoff are needed, because those are not linear.

**Four controls, each removing exactly one thing:**

| control | what it holds fixed | what it removes |
|---|---|---|
| **COIN** | rows, instants, risk distances, fill events, toll | the direction call |
| **ANTI** | as COIN | takes the exact opposite side (diagnostic) |
| **SHUF(w,sym,hour)** | rows + the cell's ambient drift | the family's directional lean *and* its row-level call |
| **SHUF(w,sym,hour,family)** | rows + the family's own long/short mix inside each cell | the row-level call only |
| **MOMENT placebo** | symbol, trading day, relative risk distance | the moment *and* the direction — a random instant on the system's own 96-window grid, 3 draws/row, 99.92 % coverage |

The coin flip is **not** drift-adjusted (a long's direction value is positive whenever the
market rose), which is why the two shuffles exist and why they are the load-bearing test.

---

## 1. Q1 — the family table

See **T1** (economics), **T2** (per month), **T3** (significance), **T10** (what would have
to be true). Headline rows:

| | clean fills | gross R | toll R | months gross+ | sign-test p | gross/toll |
|---|---:|---:|---:|:---:|---:|---:|
| **`structural_distance_extreme`** | 22,629 | **+0.06639** | 0.6334 | **8/8** | 0.0039 | +0.105 |
| `liquidity_sweep_reclaim` | 41,158 | +0.02747 | 0.3005 | 5/8 | 0.3633 | +0.091 |
| `cross_asset_lead_lag` | 20,054 | +0.02417 | 0.4524 | 7/8 | 0.0352 | +0.053 |
| **at-market cohort (7 families)** | 135,860 | **+0.02395** | 0.3128 | **8/8** | 0.0039 | +0.077 |
| `displacement_continuation` | 36,946 | +0.00791 | 0.1484 | 5/8 | 0.3633 | +0.053 |
| `session_open_range_break` | 7,855 | +0.00250 | 0.0891 | 5/8 | 0.3633 | +0.028 |
| **whole clean roster** | 310,983 | −0.00295 | 0.2806 | 4/8 | 0.6367 | −0.011 |
| `regime_transition_break` | 2,216 | −0.00455 | 0.0547 | 3/8 | 0.8555 | −0.083 |
| `current_ob_retest` | 17,551 | −0.00457 | 0.1725 | 3/8 | 0.8555 | −0.026 |
| `current_fvg_fill` | 147,079 | −0.02213 | 0.2666 | 2/8 | 0.9648 | −0.083 |
| **POI cohort (3 families)** | 175,123 | −0.02381 | 0.2556 | 2/8 | 0.9648 | −0.093 |
| `volatility_compression_expansion` | 5,002 | −0.03314 | 0.0842 | 2/8 | 0.9648 | −0.394 |
| `current_breaker_re_entry` | 10,493 | −0.07964 | 0.2409 | 1/8 | 0.9961 | −0.331 |

Three things this table settles.

1. **The estate's "needs 45.94 %, gets 34.68 %" is dead twice over** — wrong object *and*
   wrong target. Recomputed on the roster at the shipped geometry the clean gap is
   **38.32 % against a 38.44 % breakeven = −0.13 pp**, and the at-market cohort is
   **39.98 % against 38.92 % = +1.06 pp POSITIVE.**
2. **The deficit is not the win rate. It is the toll.** T10: to pay its own toll the whole
   clean roster needs **+12.09 pp** of win rate; the at-market cohort **+12.78 pp**; the best
   family, `structural_distance_extreme`, **+19.13 pp** (35.83 % → 54.96 %) because its toll
   is 0.6334 R.
3. **One family is not a signal at all.** `current_breaker_re_entry` is 67.9 % born past its
   own stop before any exclusion; even the 32.1 % that are clean book −0.07964 in 7 of 8
   months. It is a defect, and this lane prices it separately from the family it contaminates.

---

## 2. Q2 — does each family beat its own matched RANDOM baseline?

**T4.** Whole clean roster: real **−0.00295**, coin flip on the identical rows **+0.01452**,
the exact opposite side **+0.03199**.

> **Direction value = −0.01747 R/trade, CI95 [−0.02850, −0.00660], p(≥0) = 0.0018
> (the evidence that it is NEGATIVE), positive in 1 of 8 months.**

The realizable sampled coin flip has a **higher win rate than the system**: 39.05 % against
38.32 %, at an essentially identical payoff (1.6017 vs 1.6012). The system's direction call
costs it **0.73 percentage points of win rate** against a coin.

The split is where the mechanism lives:

| cohort | n | real | coin | direction value | CI95 | p(≤0) | months+ |
|---|---:|---:|---:|---:|---|---:|:---:|
| at-market (7 families) | 135,860 | +0.02395 | +0.01615 | **+0.00780** | [−0.00097, +0.01700] | 0.0405 | 6/8 |
| POI (3 families) | 175,123 | −0.02381 | +0.01326 | **−0.03707** | [−0.05432, −0.01984] | 1.0000 | 1/8 |

*(`p(≤0)` is the bootstrap share of day-block resamples at or below zero — the p-value for
"this is positive". Its complement, `p(≥0)`, is the p-value for "this is negative"; the whole
roster's direction value carries `p(≥0) = 0.0018`.)*

**The three POI families are significantly worse than random on their own fills**, and they
are 56 % of the clean roster. The comparison is fair and tradeable: the control shares the
*fill event*, so both arms are standing at price `e` at the same minute — which side to take
from there is a free choice, and the family takes the wrong one.

Mechanically: a POI limit fills when price comes to it, and **the move that filled it keeps
going.** The retracement thesis is inverted at the population level.

---

## 3. Q3 — the SHUFFLED baseline: moments or direction?

**T5**, and this is the finest cut in the lane.

| cohort | vs SHUF(w,sym,hour) — *the lean* | p(≤0) | vs SHUF(w,sym,hour,family) — *the row* | p(≤0) |
|---|---:|---:|---:|---:|
| whole clean roster | −0.01184 | 0.9885 | −0.01307 | 0.9952 |
| **at-market cohort** | **+0.01139** | **0.0170** | **+0.00076** | **0.4195** |
| POI cohort | −0.02986 | 0.9995 | −0.02380 | 0.9968 |
| `liquidity_sweep_reclaim` | **+0.03040** | **0.0080** | +0.01393 | 0.0948 |
| `structural_distance_extreme` | +0.02127 | 0.0910 | **+0.02191** | **0.0300** |
| `current_breaker_re_entry` | −0.10503 | 0.9998 | −0.02745 (only 10.6 % of labels move) | 0.9958 |
| `current_fvg_fill` | −0.02844 | 0.9978 | −0.02496 | 0.9955 |
| `volatility_compression_expansion` | −0.03076 | 0.9710 | −0.03382 | 0.9992 |

> **The at-market families' directional information is a CELL-LEVEL LEAN, not a per-setup
> call.** Holding each family's own long/short mix fixed inside every (window, symbol, broker
> hour) cell, the at-market cohort's row-level direction selection is worth **+0.00076 R/trade
> at p 0.42 — nothing.** Exactly one family carries genuine per-setup direction information:
> `structural_distance_extreme`, +0.02191 at p 0.030 with 28.9 % of its labels actually moved.

`current_breaker_re_entry` is the reverse: its −0.116 against a coin flip is almost entirely
its *lean* (its labels barely move under the within-family shuffle — 10.6 % — because it is
directionally uniform inside a cell). Its problem is which way it leans, not which instances
it picks.

---

## 4. Q4 — is a family a setup, or is it a schedule?

**T7** (η² against each factor's own permutation null) and **T8** (concentration).

**No family is a schedule, and the margin is not close.** Excess variance explained, over the
permutation null:

| factor | range across the ten families |
|---|---|
| symbol | −0.0002 … **+0.0126** |
| broker hour | −0.0002 … **+0.0335** |
| day of week | −0.0004 … +0.0036 |
| realised-vol regime tertile | −0.0001 … +0.0016 |
| side | −0.0000 … +0.0009 |
| symbol × hour (1,222–4,538 cells) | −0.0719 … +0.3997 — and this column is degrees of freedom, not structure: for `regime_transition_break` and `displacement_continuation` the observed η² is *below* its own null |

The largest single schedule effect anywhere is `volatility_compression_expansion`'s broker
hour at **+0.0335 of variance** — on a family that is significantly *negative*. For the one
8/8 family, `structural_distance_extreme`, the excesses are symbol +0.0014, hour +0.0048.

Concentration says the same thing from the other side (**T8**): the top symbol holds
4.7–12.3 % of a family's rows, the top broker hour 5.5–21.2 %, and the **top three
(symbol, hour) cells hold 0.1–1.2 % of the family's absolute gross.** And the ambient-adjusted
mean — each row's gross minus the leave-one-family-out mean gross of every other family in
the same (window, symbol, hour) cell — moves the family levels by less than 0.02 R and never
changes a sign for the positives (`structural_distance_extreme` +0.06639 → +0.07112,
`liquidity_sweep_reclaim` +0.02747 → +0.02494, `cross_asset_lead_lag` +0.02417 → +0.02549).

**These families are dispersed bets, not disguised schedules.** Whatever is wrong with them
is wrong per trade.

The MOMENT placebo (**T6**) prices the schedule question economically rather than
statistically, by paying the family for choosing *when* and nothing else:

| cohort | MOMENT value | p(≤0) | months+ | DIRECTION value | p(≤0) | months+ | TOTAL | p(≤0) | TOTAL/toll |
|---|---:|---:|:---:|---:|---:|:---:|---:|---:|---:|
| whole clean roster | −0.00434 | 0.9810 | 4/8 | −0.01740 | 0.9982 | 1/8 | **−0.02174** | 1.0000 | −0.077 |
| **at-market cohort** | **+0.00428** | **0.0105** | 6/8 | **+0.00790** | **0.0372** | 6/8 | **+0.01218** | **0.0075** | **+0.039** |
| POI cohort | −0.01103 | 0.9990 | 1/8 | −0.03703 | 1.0000 | 1/8 | −0.04806 | 1.0000 | −0.188 |
| `current_breaker_re_entry` | **+0.02718** | **0.0077** | 6/8 | **−0.11630** | 1.0000 | 1/8 | −0.08911 | 0.9998 | −0.370 |
| `displacement_continuation` | **+0.00777** | **0.0027** | 7/8 | −0.00143 | 0.5613 | 4/8 | +0.00634 | 0.2865 | +0.043 |
| `structural_distance_extreme` | +0.00637 | 0.1212 | 5/8 | +0.02041 | 0.0897 | 5/8 | +0.02679 | 0.0505 | +0.042 |
| `liquidity_sweep_reclaim` | +0.00181 | 0.3030 | 7/8 | +0.01775 | 0.0690 | 5/8 | +0.01956 | 0.0600 | +0.065 |

> **`current_breaker_re_entry` picks its moments significantly BETTER than random
> (+0.02718 R/trade, p 0.0077, 6 of 8 months) and then takes the wrong side by −0.11630.**
> It is the only family in the estate that is simultaneously a real detector and an inverted
> one. Its ANTI arm books +0.15304 gross — against a 0.2409 R toll, so inverting it does not
> make it pay; this is a **signal-repair candidate, not an economic one.**

The families do **not** select cheap moments: real toll / random-moment toll runs 0.83–1.31
with the cohort at 1.00. The "select on affordability" channel that killed this week's second
headline is simply absent here, measured from the other direction.

---

## 5. Q5 — is ANY family reliably gross-positive across months?

**Yes — one. `structural_distance_extreme`: gross-positive in 8 of 8 windows.**

+0.05362, +0.01108, +0.11754, +0.11623, +0.02740, +0.08526, +0.08166, +0.03880 → pooled
**+0.06639 R/trade** on 22,629 clean fills, day-block CI95 [+0.03354, +0.10002], p(≤0) 0.0000,
sign-test p 0.0039. It is 8/8 at **both** target geometries (+0.04333 at 1.5R). It is the only
family carrying significant *per-setup* direction information (§3). It is positive on 13 of 24
instruments.

**And it pays 10.5 % of its own toll.** Its median risk distance is 3.17 bps against a ~3.0 bps
broker toll — it is the tightest-stopped family in the book, which is precisely why its gross
in R is the largest and its toll in R is the largest (0.6334). To pay for itself its win rate
must move from 35.83 % to 54.96 %.

The closest runners-up: `cross_asset_lead_lag` 7/8 (sign-test p 0.0352) at +0.02417 against a
0.4524 toll — **5.3 %**; `liquidity_sweep_reclaim` 5/8 at +0.02747 against 0.3005 — **9.1 %**,
and it is the one family whose *lean* significantly beats a drift-matched shuffle (+0.03040,
p 0.0080). The at-market cohort as a whole is **8/8 gross-positive** (sign-test p 0.0039).

**No risk-distance slice rescues any of them (T11).** For the at-market cohort the gross falls
6.8× from the tightest decile to the widest (+0.11317 → +0.01673) while the toll falls 11.7×
(1.0000 → 0.0856); the gross/toll ratio moves only 0.113 → 0.195 and the net converges toward
zero **from below**, best cell −0.0689. Widening the stop divides the edge and the toll by the
same number, because both are fixed price-distances expressed in R. **There is no stop width
at which this book pays**, and that is a structural fact about the units, not an empirical
accident.

---

## 6. Multiplicity, honestly

This lane declares **30 looks** (10 families × {moment, direction, total}). At Benjamini–Hochberg
α = 0.10 on two-sided day-block bootstrap p-values, **9 admit — 7 of them NEGATIVE**:

| rank | family | metric | value | p₂ | BH bar | sign |
|---:|---|---|---:|---:|---:|---|
| 1 | `current_breaker_re_entry` | direction | −0.11630 | 0.0000 | 0.0033 | NEGATIVE |
| 2 | `current_fvg_fill` | direction | −0.03410 | 0.0000 | 0.0067 | NEGATIVE |
| 3 | `current_fvg_fill` | total | −0.04961 | 0.0000 | 0.0100 | NEGATIVE |
| 4 | `current_breaker_re_entry` | total | −0.08911 | 0.0005 | 0.0133 | NEGATIVE |
| 5 | `current_fvg_fill` | moment | −0.01550 | 0.0005 | 0.0167 | NEGATIVE |
| 6 | `volatility_compression_expansion` | direction | −0.03409 | 0.0130 | 0.0200 | NEGATIVE |
| 7 | **`current_breaker_re_entry`** | **moment** | **+0.02718** | 0.0135 | 0.0233 | **POSITIVE** |
| 8 | **`displacement_continuation`** | **moment** | **+0.00777** | 0.0140 | 0.0267 | **POSITIVE** |
| 9 | `volatility_compression_expansion` | total | −0.03225 | 0.0215 | 0.0300 | NEGATIVE |
| 10 | `regime_transition_break` | moment | +0.00561 | 0.0965 | 0.0333 | reject |
| 11 | `structural_distance_extreme` | total | +0.02679 | 0.1080 | 0.0367 | reject |
| 12 | `liquidity_sweep_reclaim` | total | +0.01956 | 0.1250 | 0.0400 | reject |

> **Both admitted positives are MOMENT-selection findings. Not one direction-selection
> positive survives the lane's own multiplicity bill.** At the family level the only things
> the evidence will carry are: three defects, and the fact that two families know *when*.

Cohort-level robustness of the one surviving positive (the at-market total value, +0.01218,
p 0.0097): split-half **+0.01340** (Oct-25…Jan-26) and **+0.01090** (Feb-26…May-26) — sign
stable, the second half's CI includes zero; leave-one-family-out keeps the sign in all seven
drops (range +0.00897 … +0.01436) with p ≤ 0.08; instrument breadth **19 of 24 positive**
(POI: 3 of 24; `current_fvg_fill`: **0 of 12**).

---

## 7. Answering the owner's question directly

**Is it the sleeves, or the way we use them? On this lane's evidence: the sleeves — and here
is the mechanism.**

1. The setups **do** carry information. It is not zero and it is not noise: the at-market
   cohort beats a random moment plus a random side by +0.01218 R/trade (p 0.0075), in 6 of
   8 months, on 19 of 24 instruments, at both target geometries, in both halves of the sample.
2. **What they carry is almost entirely a moment and a lean, not a per-setup direction call.**
   Row-level direction selection inside a family's own symbol-hour cell is worth +0.00076
   (p 0.42). Only `structural_distance_extreme` clears it.
3. **The information is 13–26× smaller than the toll it is spent on.** At-market total value
   +0.01218 against a 0.3128 R toll; best family +0.02679 against 0.6334. A toll of ~3.0
   price-bps per round trip is charged on an edge worth ~0.12 price-bps.
4. **Three of the ten families are net destroyers of their own information.** The POI cohort
   is 56 % of the clean roster and is significantly worse than random on both axes.
   `current_breaker_re_entry` is a *good detector wired backwards*.
5. Therefore **no usage change reaches this.** The usage layer was already measured to ADD
   (f1 §5: +0.067 matched), the cost gate is the largest real non-oracle improvement in the
   estate (f2: +0.226 R/trade), and oracle exits, oracle ordering and oracle entry instants
   are 98–105 % reproduced by a coin flip (f2). The binding constraint is that the underlying
   directional content is ~0.12 bps against a ~3.0 bps fee schedule.

**What would have to be true for the broad family to work**, stated so it can be tested:

| | requirement | measured today | factor |
|---|---|---|---|
| A | at-market cohort total value ≥ its toll | +0.01218 vs 0.3128 | **25.7×** |
| B | best family gross ≥ its toll | +0.06639 vs 0.6334 | **9.5×** |
| C | win rate that pays the toll (whole clean roster) | 38.32 % → 50.41 % | **+12.09 pp** |
| D | win rate that pays the toll (best family) | 35.83 % → 54.96 % | **+19.13 pp** |
| E | a stop width at which the ratio crosses 1 | ratio 0.113 → 0.195 across the whole decile range | **none exists** |
| F | a family whose *per-setup* direction call is worth measuring | 1 of 10 (`structural_distance_extreme`, +0.02191, p 0.030) | — |

The only routes this lane leaves open are routes that change **A–D by an order of magnitude**:
a toll an order of magnitude smaller (a different instrument set or a different broker class,
not a different threshold — thresholding was already refuted), or a direction call that is
actually a direction call. **`current_breaker_re_entry`'s inversion (row 7 above) is the single
concrete signal-side repair the evidence names**, and it is worth measuring precisely because
its moment-selection is significantly positive while its side is significantly wrong.

---

## 8. Limits of this lane

- The POI direction test conditions on the real arm's fill event, by design (it is the only way
  to isolate direction at a resting limit). It is therefore a statement about *which side to
  take once you are filled at `e`*, which is realizable — a sell-stop at `e` instead of a buy
  limit at `e` — but it is **not** a statement about POI candidates that never fill.
- The MOMENT placebo draws instants uniformly on the 96-window grid, so it includes thin and
  closed minutes; per-draw coverage is ~95 %, and averaging three draws gives 99.92 % row
  coverage. Rows are compared on whatever draws resolved.
- The 2025-05 window's tape ends with the month, so a small tail of its rows carries a
  truncated forward path. This is the estate's standing convention (f1 and f2 share it).
- Everything here is FTMO-basis cost. The h1 four-term model is the lane standard; f1 §6 row 9
  records that the sealed arms' own cost model diverges from it on oil CFDs.
- η² is reported against its own permutation null precisely because high-cardinality factors
  explain variance by construction; the raw η² column must not be read on its own.
- **Nothing in this lane touched the three sealed 2025 windows** (June, August, September).
## T1 — family economics, CLEAN fills (born-past-stop excluded), 8 windows, 2R/-1R/120 M1 bars

| family | emissions | fills | fill rate | gross R | toll R | net R | win rate | payoff | breakeven | gap | months gross+ | past-stop share of fills |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| `structural_distance_extreme` | 22,629 | 22,629 | 1.000 | +0.06639 | 0.6334 | -0.56704 | 0.3583 | 1.9770 | 0.3359 | +0.0224 | **8/8** | 0.000 |
| `liquidity_sweep_reclaim` | 41,158 | 41,158 | 1.000 | +0.02747 | 0.3005 | -0.27307 | 0.3907 | 1.6348 | 0.3795 | +0.0112 | **5/8** | 0.000 |
| `cross_asset_lead_lag` | 20,054 | 20,054 | 1.000 | +0.02417 | 0.4524 | -0.42823 | 0.3606 | 1.8423 | 0.3518 | +0.0087 | **7/8** | 0.000 |
| `displacement_continuation` | 36,946 | 36,946 | 1.000 | +0.00791 | 0.1484 | -0.14054 | 0.4325 | 1.3353 | 0.4282 | +0.0042 | **5/8** | 0.000 |
| `session_open_range_break` | 7,855 | 7,855 | 1.000 | +0.00250 | 0.0891 | -0.08657 | 0.4553 | 1.2042 | 0.4537 | +0.0016 | **5/8** | 0.000 |
| `regime_transition_break` | 2,216 | 2,216 | 1.000 | -0.00455 | 0.0547 | -0.05922 | 0.4797 | 1.0630 | 0.4847 | -0.0050 | **3/8** | 0.000 |
| `current_ob_retest` | 249,436 | 17,551 | 0.070 | -0.00457 | 0.1725 | -0.17705 | 0.4339 | 1.2917 | 0.4364 | -0.0024 | **3/8** | 0.019 |
| `current_fvg_fill` | 645,318 | 147,079 | 0.228 | -0.02213 | 0.2666 | -0.28868 | 0.3624 | 1.6937 | 0.3712 | -0.0088 | **2/8** | 0.000 |
| `volatility_compression_expansion` | 5,002 | 5,002 | 1.000 | -0.03314 | 0.0842 | -0.11734 | 0.4546 | 1.0241 | 0.4940 | -0.0394 | **2/8** | 0.000 |
| `current_breaker_re_entry` | 88,346 | 10,493 | 0.119 | -0.07964 | 0.2409 | -0.32050 | 0.3746 | 1.4320 | 0.4112 | -0.0365 | **1/8** | 0.679 |
| **__ALL__** | — | 310,983 | — | -0.00295 | 0.2806 | -0.28355 | — | — | — | — | **4/8** | 0 |
| **__ATMARKET__** | — | 135,860 | — | +0.02395 | 0.3128 | -0.28889 | — | — | — | — | **8/8** | 0 |
| **__POI__** | — | 175,123 | — | -0.02381 | 0.2556 | -0.27940 | — | — | — | — | **2/8** | 0 |

## T2 — gross R/trade by month, clean fills

| family | 25-10 | 25-11 | 25-12 | 26-01 | 26-02 | 26-03 | 26-04 | 26-05 | months+ | sign-test p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| `structural_distance_extreme` | +0.0536 | +0.0111 | +0.1175 | +0.1162 | +0.0274 | +0.0853 | +0.0817 | +0.0388 | **8/8** | 0.0039 |
| `cross_asset_lead_lag` | +0.0113 | +0.0404 | -0.0600 | +0.0614 | +0.0091 | +0.0454 | +0.0396 | +0.0372 | **7/8** | 0.0352 |
| `displacement_continuation` | +0.0167 | +0.0043 | -0.0140 | -0.0176 | +0.0473 | +0.0337 | +0.0062 | -0.0172 | **5/8** | 0.3633 |
| `liquidity_sweep_reclaim` | +0.0372 | +0.0638 | -0.0158 | +0.0643 | -0.0100 | -0.0138 | +0.0406 | +0.0587 | **5/8** | 0.3633 |
| `session_open_range_break` | +0.0624 | +0.0463 | +0.0297 | -0.0524 | +0.1128 | -0.1431 | +0.0137 | -0.0442 | **5/8** | 0.3633 |
| `current_ob_retest` | -0.0024 | -0.0691 | +0.0412 | +0.0228 | -0.0120 | -0.0574 | -0.0017 | +0.0476 | **3/8** | 0.8555 |
| `regime_transition_break` | -0.0002 | -0.0402 | +0.0011 | +0.0253 | +0.0357 | -0.0227 | -0.0324 | -0.0035 | **3/8** | 0.8555 |
| `current_fvg_fill` | -0.0477 | -0.0577 | +0.0098 | -0.0157 | -0.0225 | -0.0492 | +0.0341 | -0.0138 | **2/8** | 0.9648 |
| `volatility_compression_expansion` | -0.0194 | -0.0611 | -0.0205 | -0.0551 | -0.0326 | +0.0033 | -0.0900 | +0.0104 | **2/8** | 0.9648 |
| `current_breaker_re_entry` | -0.0638 | -0.0341 | -0.1595 | -0.1258 | -0.0332 | +0.0366 | -0.1435 | -0.0946 | **1/8** | 0.9961 |
| **__ALL__** | -0.0111 | -0.0200 | +0.0020 | +0.0061 | -0.0031 | -0.0197 | +0.0243 | +0.0017 | **4/8** | 0.6367 |
| **__ATMARKET__** | +0.0292 | +0.0281 | +0.0022 | +0.0382 | +0.0212 | +0.0172 | +0.0305 | +0.0226 | **8/8** | 0.0039 |
| **__POI__** | -0.0435 | -0.0575 | +0.0018 | -0.0186 | -0.0221 | -0.0460 | +0.0195 | -0.0130 | **2/8** | 0.9648 |

## T3 — significance of gross (day-block bootstrap, 4000 draws, 163 trading days)

| cohort | n | gross R | CI95 | p(<=0) | net R | toll R | gross/toll | median risk dist (bps) |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `structural_distance_extreme` | 22,629 | +0.06639 | [+0.03354, +0.10002] | 0.0000 | -0.56704 | 0.6334 | +0.105 | 3.17 |
| `liquidity_sweep_reclaim` | 41,158 | +0.02747 | [+0.00410, +0.05085] | 0.0115 | -0.27307 | 0.3005 | +0.091 | 7.94 |
| `cross_asset_lead_lag` | 20,054 | +0.02417 | [-0.00225, +0.04972] | 0.0362 | -0.42823 | 0.4524 | +0.053 | 6.22 |
| **__ATMARKET__** | 135,860 | +0.02395 | [+0.01410, +0.03403] | 0.0000 | -0.28889 | 0.3128 | +0.077 | 9.93 |
| `displacement_continuation` | 36,946 | +0.00791 | [-0.01440, +0.03181] | 0.2515 | -0.14054 | 0.1484 | +0.053 | 16.79 |
| `session_open_range_break` | 7,855 | +0.00250 | [-0.03287, +0.03944] | 0.4355 | -0.08657 | 0.0891 | +0.028 | 18.13 |
| **__ALL__** | 310,983 | -0.00295 | [-0.01283, +0.00720] | 0.7198 | -0.28355 | 0.2806 | -0.011 | 9.26 |
| `regime_transition_break` | 2,216 | -0.00455 | [-0.03682, +0.02851] | 0.5970 | -0.05922 | 0.0547 | -0.083 | 44.33 |
| `current_ob_retest` | 17,551 | -0.00457 | [-0.04903, +0.03906] | 0.5837 | -0.17705 | 0.1725 | -0.026 | 10.63 |
| `current_fvg_fill` | 147,079 | -0.02213 | [-0.04074, -0.00372] | 0.9900 | -0.28868 | 0.2666 | -0.083 | 8.67 |
| **__POI__** | 175,123 | -0.02381 | [-0.04071, -0.00676] | 0.9965 | -0.27940 | 0.2556 | -0.093 | 8.89 |
| `volatility_compression_expansion` | 5,002 | -0.03314 | [-0.06156, -0.00350] | 0.9845 | -0.11734 | 0.0842 | -0.394 | 34.52 |
| `current_breaker_re_entry` | 10,493 | -0.07964 | [-0.13084, -0.02586] | 0.9990 | -0.32050 | 0.2409 | -0.331 | 8.82 |

## T4 — the three matched controls (clean fills, 2R). Every arm shares the SAME rows,
instants, risk distances and fill events; only the side changes.

| cohort | n | REAL gross | COIN gross | ANTI gross | direction value | CI95 | p(>=0) = evidence it is NEGATIVE | months dirval+ |
|---|---:|---:|---:|---:|---:|---|---:|:---:|
| **__ALL__** | 310,983 | -0.00295 | +0.01452 | +0.03199 | **-0.01747** | [-0.02850, -0.00660] | 0.0018 | 1/8 |
| **__ATMARKET__** | 135,860 | +0.02395 | +0.01615 | +0.00835 | **+0.00780** | [-0.00097, +0.01700] | 0.9595 | 6/8 |
| **__POI__** | 175,123 | -0.02381 | +0.01326 | +0.05032 | **-0.03707** | [-0.05432, -0.01984] | 0.0000 | 1/8 |
| `cross_asset_lead_lag` | 20,054 | +0.02417 | +0.01954 | +0.01490 | **+0.00464** | [-0.01661, +0.02656] | 0.6567 | 5/8 |
| `current_breaker_re_entry` | 10,493 | -0.07964 | +0.03670 | +0.15304 | **-0.11634** | [-0.16911, -0.06372] | 0.0000 | 1/8 |
| `current_fvg_fill` | 147,079 | -0.02213 | +0.01205 | +0.04622 | **-0.03417** | [-0.05263, -0.01567] | 0.0005 | 1/8 |
| `current_ob_retest` | 17,551 | -0.00457 | +0.00936 | +0.02329 | **-0.01393** | [-0.05662, +0.02815] | 0.2550 | 3/8 |
| `displacement_continuation` | 36,946 | +0.00791 | +0.00931 | +0.01072 | **-0.00141** | [-0.01914, +0.01729] | 0.4410 | 4/8 |
| `liquidity_sweep_reclaim` | 41,158 | +0.02747 | +0.00987 | -0.00772 | **+0.01759** | [-0.00536, +0.04107] | 0.9305 | 5/8 |
| `regime_transition_break` | 2,216 | -0.00455 | +0.00390 | +0.01235 | **-0.00845** | [-0.03910, +0.02325] | 0.3085 | 3/8 |
| `session_open_range_break` | 7,855 | +0.00250 | -0.00084 | -0.00418 | **+0.00334** | [-0.02917, +0.03676] | 0.5887 | 5/8 |
| `structural_distance_extreme` | 22,629 | +0.06639 | +0.04605 | +0.02572 | **+0.02034** | [-0.00901, +0.05092] | 0.9095 | 5/8 |
| `volatility_compression_expansion` | 5,002 | -0.03314 | +0.00152 | +0.03618 | **-0.03466** | [-0.06239, -0.00644] | 0.0078 | 1/8 |

## T5 — shuffled-direction controls (side labels permuted inside cells; ambient drift preserved)

| cohort | n | vs SHUF(w,sym,hour) | CI95 | p(<=0) | labels changed | vs SHUF(w,sym,hour,family) | CI95 | p(<=0) | labels changed |
|---|---:|---:|---|---:|---:|---:|---|---:|---:|
| **__ALL__** | 310,983 | -0.01184 | [-0.02205, -0.00213] | 0.9885 | 0.479 | -0.01307 | [-0.02241, -0.00374] | 0.9952 | 0.403 |
| **__ATMARKET__** | 135,860 | +0.01139 | [+0.00066, +0.02231] | 0.0170 | 0.481 | +0.00076 | [-0.00782, +0.00930] | 0.4195 | 0.383 |
| **__POI__** | 175,123 | -0.02986 | [-0.04639, -0.01353] | 0.9995 | 0.477 | -0.02380 | [-0.03888, -0.00873] | 0.9968 | 0.418 |
| `cross_asset_lead_lag` | 20,054 | +0.00492 | [-0.02433, +0.03498] | 0.3710 | 0.491 | -0.00638 | [-0.03030, +0.01710] | 0.7080 | 0.401 |
| `current_breaker_re_entry` | 10,493 | -0.10503 | [-0.15826, -0.05244] | 0.9998 | 0.448 | -0.02745 | [-0.04681, -0.00718] | 0.9958 | 0.106 |
| `current_fvg_fill` | 147,079 | -0.02844 | [-0.04630, -0.01097] | 0.9978 | 0.480 | -0.02496 | [-0.04262, -0.00758] | 0.9955 | 0.466 |
| `current_ob_retest` | 17,551 | +0.00322 | [-0.04085, +0.04621] | 0.4425 | 0.472 | -0.01194 | [-0.03535, +0.01188] | 0.8377 | 0.199 |
| `displacement_continuation` | 36,946 | -0.00336 | [-0.02348, +0.01808] | 0.6198 | 0.487 | -0.01972 | [-0.03887, +0.00044] | 0.9732 | 0.431 |
| `liquidity_sweep_reclaim` | 41,158 | +0.03040 | [+0.00591, +0.05480] | 0.0080 | 0.477 | +0.01393 | [-0.00716, +0.03443] | 0.0948 | 0.402 |
| `regime_transition_break` | 2,216 | -0.01341 | [-0.05394, +0.02764] | 0.7288 | 0.485 | +0.01745 | [-0.00984, +0.04605] | 0.1082 | 0.162 |
| `session_open_range_break` | 7,855 | +0.00306 | [-0.03637, +0.04163] | 0.4375 | 0.486 | +0.00270 | [-0.03343, +0.03756] | 0.4283 | 0.413 |
| `structural_distance_extreme` | 22,629 | +0.02127 | [-0.00959, +0.05317] | 0.0910 | 0.460 | +0.02191 | [-0.00083, +0.04504] | 0.0300 | 0.289 |
| `volatility_compression_expansion` | 5,002 | -0.03076 | [-0.06150, +0.00053] | 0.9710 | 0.500 | -0.03382 | [-0.05477, -0.01153] | 0.9992 | 0.277 |

## T6 — MOMENT vs DIRECTION decomposition against a random moment on the same symbol+day

| cohort | n | REAL | COIN(real rows) | COIN(random moment) | MOMENT value | p(<=0) | m+ | DIRECTION value | p(<=0) | m+ | TOTAL value | p(<=0) | toll | TOTAL/toll |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|---:|:---:|---:|---:|---:|---:|
| **__ALL__** | 310,734 | -0.00293 | +0.01447 | +0.01881 | -0.00434 | 0.9810 | 4/8 | -0.01740 | 0.9982 | 1/8 | **-0.02174** | 1.0000 | 0.2806 | -0.077 |
| **__ATMARKET__** | 135,759 | +0.02402 | +0.01612 | +0.01184 | +0.00428 | 0.0105 | 6/8 | +0.00790 | 0.0372 | 6/8 | **+0.01218** | 0.0075 | 0.3129 | +0.039 |
| **__POI__** | 174,975 | -0.02384 | +0.01319 | +0.02422 | -0.01103 | 0.9990 | 1/8 | -0.03703 | 1.0000 | 1/8 | **-0.04806** | 1.0000 | 0.2556 | -0.188 |
| `cross_asset_lead_lag` | 20,039 | +0.02422 | +0.01950 | +0.01629 | +0.00321 | 0.2930 | 4/8 | +0.00472 | 0.3397 | 5/8 | **+0.00793** | 0.2780 | 0.4525 | +0.018 |
| `current_breaker_re_entry` | 10,487 | -0.07956 | +0.03674 | +0.00956 | +0.02718 | 0.0077 | 6/8 | -0.11630 | 1.0000 | 1/8 | **-0.08911** | 0.9998 | 0.2409 | -0.370 |
| `current_fvg_fill` | 146,947 | -0.02215 | +0.01195 | +0.02746 | -0.01550 | 1.0000 | 2/8 | -0.03410 | 0.9995 | 1/8 | **-0.04961** | 1.0000 | 0.2666 | -0.186 |
| `current_ob_retest` | 17,541 | -0.00467 | +0.00945 | +0.00591 | +0.00354 | 0.3412 | 5/8 | -0.01412 | 0.7480 | 3/8 | **-0.01058** | 0.6767 | 0.1724 | -0.061 |
| `displacement_continuation` | 36,915 | +0.00784 | +0.00927 | +0.00150 | +0.00777 | 0.0027 | 7/8 | -0.00143 | 0.5613 | 4/8 | **+0.00634** | 0.2865 | 0.1485 | +0.043 |
| `liquidity_sweep_reclaim` | 41,134 | +0.02760 | +0.00985 | +0.00804 | +0.00181 | 0.3030 | 7/8 | +0.01775 | 0.0690 | 5/8 | **+0.01956** | 0.0600 | 0.3006 | +0.065 |
| `regime_transition_break` | 2,212 | -0.00438 | +0.00391 | -0.00170 | +0.00561 | 0.0415 | 7/8 | -0.00829 | 0.6885 | 3/8 | **-0.00269** | 0.5515 | 0.0547 | -0.049 |
| `session_open_range_break` | 7,848 | +0.00274 | -0.00071 | +0.00054 | -0.00125 | 0.6185 | 6/8 | +0.00345 | 0.4100 | 5/8 | **+0.00220** | 0.4442 | 0.0890 | +0.025 |
| `structural_distance_extreme` | 22,614 | +0.06643 | +0.04601 | +0.03964 | +0.00637 | 0.1212 | 5/8 | +0.02041 | 0.0897 | 5/8 | **+0.02679** | 0.0505 | 0.6334 | +0.042 |
| `volatility_compression_expansion` | 4,997 | -0.03265 | +0.00144 | -0.00041 | +0.00185 | 0.2360 | 6/8 | -0.03409 | 0.9912 | 1/8 | **-0.03225** | 0.9848 | 0.0842 | -0.383 |

## T7 — schedule vs setup: eta^2 of gross R against the factor's OWN permutation null (200 perms)

| family | factor | levels | eta2 | null mean | EXCESS | p(null>=obs) |
|---|---|---:|---:|---:|---:|---:|
| `cross_asset_lead_lag` | symbol | 18 | 0.0006 | 0.0009 | -0.00022 | 0.745 |
| `cross_asset_lead_lag` | broker_hour | 24 | 0.0014 | 0.0011 | +0.00023 | 0.215 |
| `cross_asset_lead_lag` | symbol_x_hour | 3,324 | 0.1801 | 0.1656 | +0.01455 | 0.000 |
| `cross_asset_lead_lag` | dow | 5 | 0.0007 | 0.0002 | +0.00053 | 0.005 |
| `cross_asset_lead_lag` | vol_regime | 3 | 0.0000 | 0.0001 | -0.00010 | 0.965 |
| `cross_asset_lead_lag` | side | 2 | 0.0000 | 0.0000 | -0.00004 | 0.785 |
| `current_breaker_re_entry` | symbol | 24 | 0.0148 | 0.0022 | +0.01260 | 0.000 |
| `current_breaker_re_entry` | broker_hour | 24 | 0.0221 | 0.0022 | +0.01989 | 0.000 |
| `current_breaker_re_entry` | symbol_x_hour | 2,170 | 0.6073 | 0.2076 | +0.39968 | 0.000 |
| `current_breaker_re_entry` | dow | 5 | 0.0012 | 0.0003 | +0.00090 | 0.015 |
| `current_breaker_re_entry` | vol_regime | 3 | 0.0016 | 0.0002 | +0.00142 | 0.000 |
| `current_breaker_re_entry` | side | 2 | 0.0009 | 0.0001 | +0.00082 | 0.000 |
| `current_fvg_fill` | symbol | 14 | 0.0004 | 0.0001 | +0.00030 | 0.000 |
| `current_fvg_fill` | broker_hour | 24 | 0.0010 | 0.0002 | +0.00089 | 0.000 |
| `current_fvg_fill` | symbol_x_hour | 2,051 | 0.0370 | 0.0139 | +0.02309 | 0.000 |
| `current_fvg_fill` | dow | 5 | 0.0002 | 0.0000 | +0.00018 | 0.000 |
| `current_fvg_fill` | vol_regime | 3 | 0.0000 | 0.0000 | +0.00002 | 0.060 |
| `current_fvg_fill` | side | 2 | 0.0001 | 0.0000 | +0.00008 | 0.000 |
| `current_ob_retest` | symbol | 24 | 0.0084 | 0.0013 | +0.00707 | 0.000 |
| `current_ob_retest` | broker_hour | 24 | 0.0068 | 0.0013 | +0.00547 | 0.000 |
| `current_ob_retest` | symbol_x_hour | 2,843 | 0.4684 | 0.1621 | +0.30624 | 0.000 |
| `current_ob_retest` | dow | 5 | 0.0004 | 0.0002 | +0.00015 | 0.150 |
| `current_ob_retest` | vol_regime | 3 | 0.0017 | 0.0001 | +0.00154 | 0.000 |
| `current_ob_retest` | side | 2 | 0.0009 | 0.0001 | +0.00087 | 0.000 |
| `displacement_continuation` | symbol | 24 | 0.0010 | 0.0006 | +0.00040 | 0.025 |
| `displacement_continuation` | broker_hour | 24 | 0.0014 | 0.0006 | +0.00081 | 0.005 |
| `displacement_continuation` | symbol_x_hour | 4,289 | 0.1123 | 0.1160 | -0.00377 | 0.970 |
| `displacement_continuation` | dow | 5 | 0.0003 | 0.0001 | +0.00015 | 0.040 |
| `displacement_continuation` | vol_regime | 3 | 0.0002 | 0.0000 | +0.00015 | 0.010 |
| `displacement_continuation` | side | 2 | 0.0001 | 0.0000 | +0.00007 | 0.085 |
| `liquidity_sweep_reclaim` | symbol | 24 | 0.0008 | 0.0005 | +0.00029 | 0.025 |
| `liquidity_sweep_reclaim` | broker_hour | 24 | 0.0026 | 0.0006 | +0.00209 | 0.000 |
| `liquidity_sweep_reclaim` | symbol_x_hour | 4,538 | 0.1322 | 0.1102 | +0.02200 | 0.000 |
| `liquidity_sweep_reclaim` | dow | 5 | 0.0004 | 0.0001 | +0.00029 | 0.005 |
| `liquidity_sweep_reclaim` | vol_regime | 3 | 0.0002 | 0.0001 | +0.00018 | 0.010 |
| `liquidity_sweep_reclaim` | side | 2 | 0.0001 | 0.0000 | +0.00009 | 0.020 |
| `regime_transition_break` | symbol | 24 | 0.0142 | 0.0104 | +0.00379 | 0.105 |
| `regime_transition_break` | broker_hour | 24 | 0.0315 | 0.0103 | +0.02126 | 0.000 |
| `regime_transition_break` | symbol_x_hour | 1,531 | 0.6195 | 0.6914 | -0.07187 | 1.000 |
| `regime_transition_break` | dow | 5 | 0.0013 | 0.0017 | -0.00038 | 0.520 |
| `regime_transition_break` | vol_regime | 3 | 0.0013 | 0.0009 | +0.00043 | 0.205 |
| `regime_transition_break` | side | 2 | 0.0009 | 0.0005 | +0.00044 | 0.190 |
| `session_open_range_break` | symbol | 22 | 0.0027 | 0.0028 | -0.00003 | 0.490 |
| `session_open_range_break` | broker_hour | 17 | 0.0019 | 0.0020 | -0.00019 | 0.575 |
| `session_open_range_break` | symbol_x_hour | 1,222 | 0.1543 | 0.1557 | -0.00143 | 0.585 |
| `session_open_range_break` | dow | 5 | 0.0012 | 0.0005 | +0.00072 | 0.040 |
| `session_open_range_break` | vol_regime | 3 | 0.0004 | 0.0003 | +0.00014 | 0.210 |
| `session_open_range_break` | side | 2 | 0.0005 | 0.0001 | +0.00042 | 0.025 |
| `structural_distance_extreme` | symbol | 24 | 0.0024 | 0.0010 | +0.00138 | 0.000 |
| `structural_distance_extreme` | broker_hour | 24 | 0.0058 | 0.0010 | +0.00479 | 0.000 |
| `structural_distance_extreme` | symbol_x_hour | 4,318 | 0.2230 | 0.1908 | +0.03213 | 0.000 |
| `structural_distance_extreme` | dow | 5 | 0.0002 | 0.0002 | -0.00002 | 0.500 |
| `structural_distance_extreme` | vol_regime | 3 | 0.0005 | 0.0001 | +0.00039 | 0.000 |
| `structural_distance_extreme` | side | 2 | 0.0001 | 0.0000 | +0.00006 | 0.115 |
| `volatility_compression_expansion` | symbol | 24 | 0.0170 | 0.0047 | +0.01229 | 0.000 |
| `volatility_compression_expansion` | broker_hour | 24 | 0.0382 | 0.0047 | +0.03353 | 0.000 |
| `volatility_compression_expansion` | symbol_x_hour | 1,723 | 0.3673 | 0.3446 | +0.02266 | 0.020 |
| `volatility_compression_expansion` | dow | 5 | 0.0044 | 0.0008 | +0.00360 | 0.000 |
| `volatility_compression_expansion` | vol_regime | 3 | 0.0020 | 0.0004 | +0.00160 | 0.010 |
| `volatility_compression_expansion` | side | 2 | 0.0005 | 0.0002 | +0.00029 | 0.125 |

## T8 — concentration: is a family really one instrument at one hour?

| family | n symbols | top symbol | its row share | n hours | top hour | its row share | top-3 (sym,hour) cells' share of |gross| | raw mean gross | ambient-adjusted mean gross |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `cross_asset_lead_lag` | 18 | USDJPY | 0.082 | 24 | 17 | 0.077 | 0.0020 | +0.02417 | +0.02549 |
| `current_breaker_re_entry` | 24 | SPX500 | 0.055 | 24 | 16 | 0.082 | 0.0072 | -0.07964 | -0.10090 |
| `current_fvg_fill` | 14 | JP225 | 0.123 | 24 | 15 | 0.071 | 0.0014 | -0.02213 | -0.04280 |
| `current_ob_retest` | 24 | USDCAD | 0.052 | 24 | 16 | 0.092 | 0.0041 | -0.00457 | -0.01589 |
| `displacement_continuation` | 24 | USOIL_cash | 0.046 | 24 | 10 | 0.094 | 0.0015 | +0.00791 | -0.00223 |
| `liquidity_sweep_reclaim` | 24 | NAS100 | 0.047 | 24 | 10 | 0.067 | 0.0011 | +0.02747 | +0.02494 |
| `regime_transition_break` | 24 | US30_cash | 0.052 | 24 | 17 | 0.112 | 0.0115 | -0.00455 | -0.00442 |
| `session_open_range_break` | 22 | AUDUSD | 0.061 | 17 | 16 | 0.212 | 0.0060 | +0.00250 | +0.00505 |
| `structural_distance_extreme` | 24 | NAS100 | 0.058 | 24 | 17 | 0.055 | 0.0014 | +0.06639 | +0.07112 |
| `volatility_compression_expansion` | 24 | NAS100 | 0.058 | 24 | 3 | 0.166 | 0.0090 | -0.03314 | -0.04348 |

## T9 — target-geometry robustness: 2.0R (downstream contract) vs 1.5R (`risk.min_rr`, the emitted contract)

| cohort | gross @2R | months+ @2R | gross @1.5R | months+ @1.5R | dirval @2R | dirval @1.5R |
|---|---:|:---:|---:|:---:|---:|---:|
| `structural_distance_extreme` | +0.06639 | 8/8 | +0.04333 | 8/8 | +0.02034 | +0.01793 |
| `liquidity_sweep_reclaim` | +0.02747 | 5/8 | +0.02102 | 5/8 | +0.01759 | +0.01541 |
| `cross_asset_lead_lag` | +0.02417 | 7/8 | +0.01349 | 6/8 | +0.00464 | +0.00279 |
| **__ATMARKET__** | +0.02395 | 8/8 | +0.01500 | 8/8 | +0.00780 | +0.00600 |
| `displacement_continuation` | +0.00791 | 5/8 | +0.00282 | 5/8 | -0.00141 | -0.00277 |
| `session_open_range_break` | +0.00250 | 5/8 | +0.00012 | 5/8 | +0.00334 | +0.00259 |
| **__ALL__** | -0.00295 | 4/8 | -0.00890 | 2/8 | -0.01747 | -0.01537 |
| `regime_transition_break` | -0.00455 | 3/8 | -0.00323 | 3/8 | -0.00845 | -0.00690 |
| `current_ob_retest` | -0.00457 | 3/8 | -0.01101 | 3/8 | -0.01393 | -0.01563 |
| `current_fvg_fill` | -0.02213 | 2/8 | -0.02463 | 2/8 | -0.03417 | -0.02821 |
| **__POI__** | -0.02381 | 2/8 | -0.02744 | 1/8 | -0.03707 | -0.03194 |
| `volatility_compression_expansion` | -0.03314 | 2/8 | -0.03532 | 1/8 | -0.03466 | -0.03664 |
| `current_breaker_re_entry` | -0.07964 | 1/8 | -0.09435 | 0/8 | -0.11634 | -0.11161 |

## T10 — what would have to be true: win rate needed to pay the family's own toll

| cohort | n | gross R | toll R | win rate now | avg win | avg loss | breakeven wr | wr that pays the toll | pp needed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **__ALL__** | 310,983 | -0.00295 | 0.2806 | 0.3832 | 1.4439 | 0.9017 | 0.3844 | 0.5041 | **+12.09** |
| **__ATMARKET__** | 135,860 | +0.02395 | 0.3128 | 0.3998 | 1.3806 | 0.8796 | 0.3892 | 0.5276 | **+12.78** |
| **__POI__** | 175,123 | -0.02381 | 0.2556 | 0.3703 | 1.4969 | 0.9181 | 0.3802 | 0.4860 | **+11.57** |
| `cross_asset_lead_lag` | 20,054 | +0.02417 | 0.4524 | 0.3606 | 1.7908 | 0.9721 | 0.3518 | 0.5156 | **+15.50** |
| `current_breaker_re_entry` | 10,493 | -0.07964 | 0.2409 | 0.3746 | 1.2832 | 0.8961 | 0.4112 | 0.5217 | **+14.71** |
| `current_fvg_fill` | 147,079 | -0.02213 | 0.2666 | 0.3624 | 1.5753 | 0.9301 | 0.3712 | 0.4776 | **+11.52** |
| `current_ob_retest` | 17,551 | -0.00457 | 0.1725 | 0.4339 | 1.0587 | 0.8196 | 0.4364 | 0.5282 | **+9.43** |
| `displacement_continuation` | 36,946 | +0.00791 | 0.1484 | 0.4325 | 1.0636 | 0.7965 | 0.4282 | 0.5080 | **+7.56** |
| `liquidity_sweep_reclaim` | 41,158 | +0.02747 | 0.3005 | 0.3907 | 1.5249 | 0.9328 | 0.3795 | 0.5018 | **+11.11** |
| `regime_transition_break` | 2,216 | -0.00455 | 0.0547 | 0.4797 | 0.4649 | 0.4373 | 0.4847 | 0.5453 | **+6.56** |
| `session_open_range_break` | 7,855 | +0.00250 | 0.0891 | 0.4553 | 0.8658 | 0.7190 | 0.4537 | 0.5099 | **+5.46** |
| `structural_distance_extreme` | 22,629 | +0.06639 | 0.6334 | 0.3583 | 1.9685 | 0.9957 | 0.3359 | 0.5496 | **+19.13** |
| `volatility_compression_expansion` | 5,002 | -0.03314 | 0.0842 | 0.4546 | 0.4252 | 0.4152 | 0.4940 | 0.5942 | **+13.96** |

## T11 — affordability: risk-distance deciles (clean fills). No slice pays.


**__ATMARKET__**

| decile | d_lo bps | d_hi bps | n | gross R | toll R | net R | gross/toll |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.32 | 2.34 | 13,586 | +0.11317 | 1.0000 | -0.88678 | +0.113 |
| 2 | 2.34 | 3.68 | 13,586 | +0.05137 | 0.4936 | -0.44225 | +0.104 |
| 3 | 3.68 | 5.35 | 13,586 | +0.01503 | 0.3446 | -0.32960 | +0.044 |
| 4 | 5.35 | 7.38 | 13,585 | +0.00563 | 0.2787 | -0.27309 | +0.020 |
| 5 | 7.38 | 9.93 | 13,587 | +0.00257 | 0.2379 | -0.23536 | +0.011 |
| 6 | 9.93 | 13.48 | 13,586 | +0.01036 | 0.2078 | -0.19740 | +0.050 |
| 7 | 13.48 | 18.98 | 13,586 | +0.00231 | 0.1832 | -0.18091 | +0.013 |
| 8 | 18.98 | 29.16 | 13,586 | +0.01353 | 0.1657 | -0.15216 | +0.082 |
| 9 | 29.16 | 53.20 | 13,586 | +0.00875 | 0.1312 | -0.12249 | +0.067 |
| 10 | 53.20 | 1624.22 | 13,586 | +0.01673 | 0.0856 | -0.06890 | +0.195 |

**structural_distance_extreme**

| decile | d_lo bps | d_hi bps | n | gross R | toll R | net R | gross/toll |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.32 | 1.32 | 2,263 | +0.15497 | 1.4434 | -1.28843 | +0.107 |
| 2 | 1.32 | 1.73 | 2,263 | +0.18816 | 0.9428 | -0.75463 | +0.200 |
| 3 | 1.73 | 2.12 | 2,260 | +0.10922 | 0.7115 | -0.60227 | +0.154 |
| 4 | 2.12 | 2.59 | 2,266 | +0.09482 | 0.6044 | -0.50960 | +0.157 |
| 5 | 2.59 | 3.17 | 2,262 | +0.02995 | 0.4989 | -0.46896 | +0.060 |
| 6 | 3.17 | 4.03 | 2,263 | +0.04510 | 0.4187 | -0.37362 | +0.108 |
| 7 | 4.03 | 5.49 | 2,263 | -0.00408 | 0.3747 | -0.37882 | -0.011 |
| 8 | 5.49 | 7.94 | 2,263 | +0.03760 | 0.4127 | -0.37506 | +0.091 |
| 9 | 7.94 | 12.77 | 2,263 | -0.01274 | 0.5050 | -0.51770 | -0.025 |
| 10 | 12.77 | 197.92 | 2,263 | +0.02087 | 0.4223 | -0.40142 | +0.049 |

**liquidity_sweep_reclaim**

| decile | d_lo bps | d_hi bps | n | gross R | toll R | net R | gross/toll |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.59 | 2.71 | 4,116 | +0.11254 | 0.7701 | -0.65754 | +0.146 |
| 2 | 2.71 | 3.77 | 4,116 | +0.07222 | 0.4428 | -0.37056 | +0.163 |
| 3 | 3.77 | 4.88 | 4,116 | +0.00158 | 0.3387 | -0.33716 | +0.005 |
| 4 | 4.88 | 6.22 | 4,115 | +0.01065 | 0.2752 | -0.26451 | +0.039 |
| 5 | 6.22 | 7.94 | 4,116 | +0.02633 | 0.2263 | -0.20002 | +0.116 |
| 6 | 7.94 | 10.47 | 4,116 | +0.01638 | 0.2121 | -0.19572 | +0.077 |
| 7 | 10.47 | 14.56 | 4,115 | +0.00498 | 0.1969 | -0.19195 | +0.025 |
| 8 | 14.56 | 22.06 | 4,116 | +0.02734 | 0.2064 | -0.17911 | +0.132 |
| 9 | 22.06 | 38.16 | 4,116 | +0.01706 | 0.2003 | -0.18329 | +0.085 |
| 10 | 38.16 | 788.35 | 4,116 | -0.01441 | 0.1364 | -0.15084 | -0.106 |

**cross_asset_lead_lag**

| decile | d_lo bps | d_hi bps | n | gross R | toll R | net R | gross/toll |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.38 | 1.97 | 2,006 | +0.02466 | 1.3640 | -1.33933 | +0.018 |
| 2 | 1.97 | 2.83 | 2,005 | +0.00023 | 0.6920 | -0.69175 | +0.000 |
| 3 | 2.83 | 3.72 | 2,005 | +0.04029 | 0.4450 | -0.40471 | +0.091 |
| 4 | 3.72 | 4.83 | 2,006 | +0.01127 | 0.3443 | -0.33307 | +0.033 |
| 5 | 4.83 | 6.22 | 2,005 | +0.05806 | 0.3007 | -0.24259 | +0.193 |
| 6 | 6.22 | 8.30 | 2,005 | +0.00597 | 0.2739 | -0.26788 | +0.022 |
| 7 | 8.30 | 11.75 | 2,006 | +0.02191 | 0.2767 | -0.25480 | +0.079 |
| 8 | 11.75 | 17.80 | 2,005 | +0.03987 | 0.3082 | -0.26832 | +0.129 |
| 9 | 17.80 | 29.34 | 2,005 | +0.01773 | 0.3164 | -0.29867 | +0.056 |
| 10 | 29.34 | 354.71 | 2,006 | +0.02176 | 0.2027 | -0.18093 | +0.107 |

## T12 — family x side (clean fills)

| family | n LONG | gross LONG | coin LONG | dirval LONG | n SHORT | gross SHORT | coin SHORT | dirval SHORT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `cross_asset_lead_lag` | 10,395 | +0.02193 | +0.01389 | +0.00804 | 9,659 | +0.02659 | +0.02562 | +0.00097 |
| `current_breaker_re_entry` | 3,971 | -0.03432 | +0.03931 | -0.07364 | 6,522 | -0.10724 | +0.03510 | -0.14234 |
| `current_fvg_fill` | 74,883 | -0.01070 | +0.01243 | -0.02313 | 72,196 | -0.03398 | +0.01165 | -0.04563 |
| `current_ob_retest` | 9,802 | +0.02474 | +0.01558 | +0.00916 | 7,749 | -0.04164 | +0.00149 | -0.04313 |
| `displacement_continuation` | 18,163 | +0.01886 | +0.00566 | +0.01320 | 18,783 | -0.00269 | +0.01284 | -0.01554 |
| `liquidity_sweep_reclaim` | 18,449 | +0.04228 | +0.01097 | +0.03131 | 22,709 | +0.01543 | +0.00899 | +0.00645 |
| `regime_transition_break` | 1,118 | +0.01376 | +0.00395 | +0.00982 | 1,098 | -0.02319 | +0.00385 | -0.02704 |
| `session_open_range_break` | 4,137 | +0.02345 | -0.00549 | +0.02894 | 3,718 | -0.02081 | +0.00434 | -0.02515 |
| `structural_distance_extreme` | 7,927 | +0.08562 | +0.06494 | +0.02068 | 14,702 | +0.05601 | +0.03586 | +0.02015 |
| `volatility_compression_expansion` | 2,663 | -0.02120 | +0.00150 | -0.02270 | 2,339 | -0.04673 | +0.00154 | -0.04828 |
