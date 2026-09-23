# Session AH — the entry hour is the lever, member conditioning is not, and the cost model that hid both is repaired

**Branch `phase8/conditioning-entry`. Blocks B1000–B1020. Not merged.**
**42 members × 4 entry arms · 246 member cells re-costed · 30 families conditioned ·
843 ledger rows · 9 repair-queue rows.**
Scoped verification per `WAVE_8_WORKING_AGREEMENT.md` §2 — receipt in §9.

---

## 0. Headline

**The FX D1 cohort fills at broker hour 00 on 20,658 of 20,658 trades.** Not usually, not
mostly — every one, because a D1 bar closes at the daily rollover and the sleeve enters at its
own decision bar's close. That hour is the measured 13×–38× hour of the week. AF found it and
re-*priced* it; this session **moved the entry** and simulated the consequence end to end, which
changes the fill price, the path, the hold and the carry rather than only the charge.

On one intersected population of **16,337 decision bars** (counts equal across arms by
construction), against arm B — the control that holds the entry instant fixed and changes only
the exit resolution:

| | arm B (broker 00) | arm C (broker 04) | Δ |
|---|---:|---:|---:|
| cost, R/trade, model convention | 0.2343 | **0.0777** | **+0.1567** |
| cost, R/trade, 50/50 attribution | 0.1617 | 0.0830 | **+0.0788** |
| gross, R/trade | +0.00872 | −0.00672 | −0.0154 |
| **net** | | | **+0.1412 … +0.0633** |

**Cost dominates gross by 5:1 to 10:1 depending on how the spread bill is attributed across the
two crossings.** 38 of 42 members improve, median **+0.117 R/day**. Four cross zero from clearly
negative — including **`mx_cadjpy`'s own live rule**, AF's named beneficiary and "the estate's
closest miss", from −0.1193 to +0.0022 — and their blocking gate changes from expectancy to
significance or lifetime. Nothing admits.

**Arm A reproduces AF's population 42 of 42 exactly on trade count AND on summed R**, which is
what makes the comparison about the same program rather than about two harnesses.

**Four more things Borhen can decide on.**

1. **`mx_nzdjpy`'s pre-declared regime gate is positive, and the entry hour does all of it.** AF
   measured `PERSISTENCE == trend` at −0.1953 and concluded the pre-declared variable does not
   explain the sleeve. Reproduced bit-for-bit; on the 83 bars every arm shares, AF's baseline is
   **−0.28325** and the shifted entry gives **+0.21895 R/day, p 0.2467, 4 of 5 folds positive**
   — obtainable with AF's own unrepaired cost model, because at hour 04 the two compositions are
   bit-identical. **AF §5.3 was a finding about the entry hour, not about the variable.**
2. **The session's best new cell is a conditioned family and it is blocked only by a number
   nobody has fixed.** `volume_surge_reversal × index × D1` gated on `VOL_REGIME == hi` —
   mechanically the regime a volume-surge reversal should want — is **+0.2248 R/day, 5 of 5 OOS
   folds positive, raw p 0.0127 on n=203**. It is an *enumerated* cell, so it carries its own
   9-cell bill (Bonferroni-within-enumeration p 0.114). It admits under BH α = 0.20 at ≤ 15
   declared looks and Bonferroni α = 0.05 at ≤ 3. **Same owner decision as `mx_btcusd`'s, on the
   same unresolved `declared_family_size`.**
3. **Member conditioning is refuted as a lever, on the honest test.** Choosing the carrier set
   on the first four folds and scoring the fifth helps in **11 of 22** mixture families — a coin
   flip — at a trade-weighted **−0.004525 R/trade**. 0 of 30 families cohere inside a
   pre-declared dial bucket. AF's 23-row majority prescription does not deliver, and the two
   levers that *do* move those families are the ones in this session's other half.
4. **The cost model's era × hour product is repaired, and the repair is worth up to +0.35 R/day
   per member with 0 cells moving the wrong way** — but it changes **no** verdict on its own, and
   its *magnitude* is the least certain thing in this session. `b = 0.4947 ± 0.1003` is rejected
   against v1 at 5.0 σ on the class that pays the premium and **not** rejected on the era axis,
   whose broker-wide component points *above* 1. So every conclusion here is published at both
   `b = 0.4947` and `b = 1`, and §3's headline is *larger* under v1 — it does not depend on the
   exponent. §2.2 is the honest version and §8 is how it got there.

**And one thing that was in the archive all along.** The MT5 bar `spread` column is the
**MINIMUM** spread within the bar — 0.999 median exact-match rate over 30 symbols. A four-hour
minimum cannot see a one-hour rollover spike, which is precisely why the era × hour product
could never have been validated at H4 and went unchecked for a whole wave.

**§8 is longer than usual and that is deliberate.** An adversarial workflow — eight skeptics, then
independent judges over every claimed refutation — was run over this session's headline claims
*before* publishing them. Three survived intact; **five were refuted, every one correctly, and one
of them found a defect in shipped code**. All five corrections are in the numbers above rather than
in a footnote, and two of them made the underlying evidence *better* rather than merely weaker.

---

## 1. What the bar `spread` column actually is, and why it matters

`spread_model_v1` reads that column as a level whose ratios track the era. Nothing had asked
which instant of a bar it describes. Exact integer match against tick truth at M15 inside the
reference window, five candidates, 30 symbols:

| candidate | median exact-match rate |
|---|---:|
| **min** | **0.9992** |
| open | 0.2390 |
| close | 0.2195 |
| median | 0.0562 |
| max | 0.0077 |

Worst symbol on `min` is EURUSD at 0.9844. M15 is used because 900 s is short enough that the
candidates separate; at H4 they do not.

Three consequences, in ascending order of importance:

1. AG's era ratios are ratios of **minima**, and the anchor is a tick **p50**. §6.
2. The column is **structurally blind to the rollover at H4** — a four-hour minimum is the calm
   floor of that window, so the 00:00 H4 bar records the 02:00–04:00 spread. That is why the
   product went unvalidated: the only historical instrument available could not see the thing
   being multiplied.
3. At **M15** it *can*, and the M15 archive reaches back to 2024-01. That is what makes the
   era-axis test in §2 possible at all.

---

## 2. The composition, measured on three axes — and my own first answer was wrong

### 2.1 The first regressions said "no repair needed"

The cross-broker and era-axis fits first returned **b = +1.125 ± 0.407** and **+0.930 ± 0.051**
— i.e. the multiplicative composition AF filed as a defect is fine. Both were contaminated the
same way: fourteen archive instruments do not quote at the rollover at all and crypto quotes
24/7 without widening, so their hour-00 multiplier is exactly 1.00 and `h_level == base` **by
construction**. Such a cell fits the slope at 1.0 whichever composition is true — and BTCUSD
carries a 22.4× level difference between the two accounts, so it set the cross-broker slope by
leverage alone.

This is AG's block-pair failure in a new place (352 of 540 pairs did not move, so selecting on
the pooled median picked the variant best at predicting "no change") and it takes the same fix:
fit only where the premium exists.

**One half of that sentence was itself an over-generalisation**, and an adversarial pass caught
it: three crypto symbols contaminated the **era-axis** fit (BTCUSD, DASHUSD, ETHUSD, 17 → 14
symbols), but the cross-broker fit contained exactly **one** — BTCUSD, which carries 66 % of that
regression's leverage. ETHUSD had already been removed in both runs by a pre-existing
"level did not move" filter. The mechanism holds; the count does not.

### 2.2 What the axes say once they are asked properly — and where they disagree

`log(hour-h level) = a + b·log(calm-hours level)`:

| axis | what varies | b | SE | σ from 1 |
|---|---|---:|---:|---:|
| **B cross-section, `fx`** | **14 cells = 7 instruments × 2 accounts**, leave-one-out | **0.310** | 0.139 | **5.0** |
| B cross-section, `jpy_fx` | same | 0.721 | 0.194 | 1.4 |
| C era axis, M15 bar minima 2024Q1–2026Q3 | 152 within-symbol demeaned points, 14 symbols | 0.669 | **0.219** (symbol-clustered) | **1.5** |
| A cross-broker | same instrument, same instant, two administered levels | 0.825 | 0.935 | 0.2 |

**b = 0.4947 ± 0.1003, envelope [0.310, 0.721]**, by inverse-variance weighting over the axes
that identify it. The protocol is declared in `ah_spread_compose.py` source before any verdict
was computed with it.

**And the era axis — the axis the model extrapolates along — does NOT support the damping.** Two
findings an adversarial pass supplied, both landed:

* the published 2.6 σ was an **i.i.d. SE on doubly-clustered data**. 152 quarterly points come
  from 14 symbols over 11 shared quarters. Symbol-clustered, σ-from-1 is **1.5** — below this
  fit's own declared `REJECT_SIGMA = 2.0` — a symbol block bootstrap gives a 95 % CI of
  **[0.439, 1.251]** that **contains 1**, and **6 of the 14 per-symbol slopes are ≥ 1**;
* splitting the axis into the component a historical era ratio actually *is* — a broker-wide move
  — and the idiosyncratic remainder, the two disagree and the broker-wide one points **above** 1:

| component | isolates | b | SE | n |
|---|---|---:|---:|---:|
| quarter-collapsed | the **broker-wide** era response | **1.463** | 0.684 | 11 |
| within-quarter | one instrument moving alone | **0.879** | 0.044 | 152 |

**So what the repair rests on is narrower than "v1 is refuted where either can be tested", which
is what I first wrote in the module docstring.** It rests on two things:

1. the **affected class's cross-section** — 5.0 σ i.i.d., 5.79 clustered by instrument, 3.8–5.6
   leave-one-out, 3.2 σ collapsed to 7 instruments — where v1's leave-one-out prediction error is
   also **2.2× the damped form's** (0.608 against 0.288);
2. **the a-priori ground AF filed the defect on**: v1 charges **178 % of the risk unit as spread**
   on NZDUSD in the 2000s. That is not a market, and it needs no regression.

The era axis neither confirms nor refutes it. **And the functional form is not uniquely
selected** — on the fx class MAX_PEAK (0.263) and ADD_PRICE (0.278) sit within 0.02 of DAMPED_B
(0.280), all three far ahead of MULT_V1's 0.608. What the evidence supports is *damped, by
roughly half an exponent*; it does not single out this algebra.

**Which is why every conclusion here is published at both `b = 0.4947` and `b = 1`.** §3's
entry-shift result is *larger* under v1, so the session's headline does not depend on the exponent
at all; §2.5's is the one that scales with it, monotonically to zero at b = 1.

Axis A's robust statistic is worth reading against its own OLS: the **median pairwise slope is
0.103**, because the OLS is dragged by CHFJPY, where redacted_account runs no rollover premium at all
(1.00 against FTMO's 15.68) — a structural difference, not a scaling law. Among the pairs that do
move: EURGBP is 1.90× wider on redacted_account for a 1.085× higher hour-00 level (b 0.13); USDJPY
2.33× wider for 1.069× (b 0.08).

Axis C validates its instrument before using it: the M15 bar-minimum hour-00 multiplier correlates
**0.891** with the tick-measured one over 17 symbols.

### 2.3 The composition, and what it does

`spread(sym, era, h) = anchor × era_ratio ** b × hour_mult(h)` — v1 exactly at `b = 1`, exact in
the reference window at any `b`, clamped so a rollover is never tighter than its own era's calm
level, and applied only above `PREMIUM_FLOOR = 1.5`.

| cell | era class | era ratio | v1 | **v2** |
|---|---|---:|---:|---:|
| EURUSD 2002Q2 | SCHEDULE | 50.00 | 650× | **93.4×** |
| NZDUSD 2005Q2 | SCHEDULE | 13.01 | 143× | **40.1×** |
| USDJPY 2007Q2 | SCHEDULE | 12.15 | 117× | **33.9×** |
| XAUUSD 2022Q2 | QUANTIZED | 0.178 | 0.18× | **unchanged** |

`v1_multiplicative` stays selectable, `GateSpec` carries it, and the composition changes the
spec seal.

### 2.4 `PREMIUM_FLOOR` exists because two of AG's tests were right

The first implementation guarded only on `mult_ref <= 1`. Metals carry a ~1.14× multiplier at
some hours — session structure, not a rollover spike, and the exponent was never measured on it.
Because XAUUSD's 2022 era ratio is **0.178×**, `era_ratio ** (b−1)` exceeds 1 there, so the
"repair" **raised** the metals charge ~2.3× — on the one class AG had just shown was already
**over**-costed. `test_era_costing_changes_a_verdict_sized_amount` failed at 2.1× against its own
3× floor and was correct to. The floor is the same threshold the fit required for inclusion, so
the repair is now exactly as wide as the defect.

### 2.5 What it moves

AF's own grid, same trades, same bill, same band, once per composition:

| scope | improved | worsened | median Δ | max Δ | verdicts changed |
|---|---:|---:|---:|---:|---:|
| member (246) | **84** | **0** | 0.0000 | **+0.3474** | **0** |
| family (30) | **6** | **0** | 0.0000 | **+0.2054** | **0** |

Zero worsened is a property of the clamp and the floor, not luck. **No admission changes** — the
repair moves magnitude and blocking *reason*. AF's interim (restrict banded pricing to
`era_class == RECORDED`, which drops trades) is retired: banded pricing is available on every era
again.

---

## 3. The H4 re-entry, end to end

Four arms, one **intersected** population. 4,321 decision bars are excluded, almost all Friday
D1 bars whose next H4 close is 52 h away — a session gap, not a later fill.

| arm | entry | exit bars | gross R | cost R | median hold | pre-entry drift |
|---|---|---|---:|---:|---:|---:|
| A | D1 close (broker 00) | D1, 80 | +0.00741 | 0.2357 | 96 h | — |
| **B** control | D1 close | H4, 480 | +0.00872 | 0.2327 | 84 h | — |
| **C** | first H4 close (04) | H4, 480 | −0.00672 | **0.0771** | 80 h | +0.00734 R |
| D | second H4 close (08) | H4, 480 | −0.01542 | 0.0823 | 80 h | +0.01351 R |

**B is the control and it is not decoration**: 480 H4 bars span the same 80 trading days as 80
D1 bars, but a finer bar sees a stop the coarser one steps over. A→B is **+0.0013 R/trade**, and
reporting C against A would sell that as part of the entry shift.

### 3.1 The cost convention is a ceiling, and saying so is the honest version

`cost_r` charges `crossings_charged: 1` (`model.py:403`, `:439`) and evaluates all of it at
`entry_utc`. A round trip crosses the spread twice; the near-universal reading of "one full
spread per round trip" is half at entry and half at exit, and the source does not say which it
means. So moving the **entry** is credited with 100 % of a bill whose exit half the shift does
not move — measured: the arms' exit-hour distributions are near-identical and the exit-instant
spread is 0.0468 R against 0.0456 R.

| attribution | cost B → C | saving | net | cost : gross |
|---|---|---:|---:|---:|
| `model_convention` — what the gate charges | 0.2343 → 0.0777 | **+0.1567** | **+0.1412** | **10.2 : 1** |
| `half_at_each` | 0.1617 → 0.0830 | **+0.0788** | **+0.0633** | **5.1 : 1** |

A direction-aware split is the same number: the model's quoted spread is symmetric about mid.
**Cost dominates gross on either reading**, so the conclusion holds and the magnitude is a range.
Every verdict in `ENTRY_HOUR_FRONTIER_V1.json` is charged the model convention, so §3.3's
zero-crossings sit at the ceiling.

Under `v1_multiplicative` the model-convention saving is 0.4318 R — **AF's ~0.40 R figure,
reproduced, and 63 % of it was the composition defect.** That is why item 2 had to be done first.

### 3.2 The gross loss names its own mechanism

Against arm B: **38 of 42 improve, median +0.1170 R/day**, four worsen — `atr_mean_reversion` ×
cadjpy (−0.0226), eurusd (−0.0330), usdjpy (−0.0284), plus `volume_surge_reversal` × usdjpy
(−0.0038). Three of the four are the reversion mechanism and they carry the largest pre-entry
drift in the cohort (cadjpy **+0.096 R**, usdjpy +0.068, eurusd +0.035).

**A reversion has already happened four hours after the close; a breakout has not.** So the
prescription splits: the cohort takes the shift, `atr_mean_reversion` needs its own shorter shift
measured. That is the "real finding about the mechanism" item 1 asked for, and it is a repair
rather than a rejection.

### 3.3 Four members cross zero, and their blocker changes

| member | B | C | p_raw at C | folds+ | blocking gate at C |
|---|---:|---:|---:|---|---|
| `donchian × nzdjpy` | −0.1190 | **+0.0831** | 0.196 | 0.4 → 0.6 | **lifetime** (−0.0197 R/trade) |
| `donchian × cadjpy` | −0.0940 | **+0.0611** | 0.282 | 0.2 → 0.6 | **lifetime** (−0.0495) |
| `donchian × audjpy` | −0.1705 | **+0.0442** | 0.299 | 0.0 → 0.6 | **lifetime** (−0.0090) |
| **`mx_cadjpy`'s live rule** | −0.1193 | **+0.0022** | 0.491 | 0.4 → 0.6 | **significance** |

The three donchian JPY crosses reject on *lifetime* — their scored window is positive and their
pre-2010 history is not, which is a sample/era question and a different repair. `mx_cadjpy` moves
to significance, the blocker AD found at all 25 best exit cells and the one `mx_btcusd` waits on.
No family admits; the best is `fam_donchian_20_breakout_fx_d1` at −0.0683, p 0.980.

### 3.4 The saving survives where nothing is extrapolated

| cell | n | saving R | Δnet R | median era ratio | eff/ref hour mult |
|---|---:|---:|---:|---:|---:|
| **era ratio ∈ [0.9, 1.1]** | 358 | **0.1129** | **+0.1133** | **1.000** | **1.000** |
| **2020s** | 1,568 | **0.1043** | **+0.0816** | **1.000** | **1.000** |
| era_class RECORDED | 2,369 | 0.1496 | +0.1205 | 2.125 | 0.683 |
| era_class SCHEDULE | 2,047 | 0.1884 | +0.1849 | 10.000 | 0.312 |
| 2000s | 1,705 | 0.2142 | +0.2258 | 12.152 | 0.283 |

The era-neutral cell settles it: on the 358 trades whose own era ratio is inside [0.9, 1.1] the
effective hour multiplier is *exactly* the tick-measured one and nothing is extrapolated at all.
See §8 for what I first claimed here and why it was wrong.

---

## 4. Member conditioning: answered, and it does not deliver

### 4.1 Carrier stability, against a chance baseline the script computes

Per family the pooled series is cut into five chronological quintiles and the carrier set
(members with positive mean gross R, ≥5 trades there) measured in each. Overlap between
consecutive quintiles runs **0.000–0.635** against a chance baseline of **0.083–0.540**;
**9 of 23 fall BELOW their own chance baseline**, and only **3 of 23** clear both clauses
(overlap > chance AND holdout sign agreement ≥ 0.6), with margins of 0.04–0.07 on a statistic
whose own spread is larger than that.

### 4.2 The honest carrier trade, on two weightings that disagree by 8×

Choose the carriers on quintiles 0–3, score quintile 4 alone. One look per family, the rule
fixed before any quintile-4 number was read, compared against the same quintile-4 trades
unselected. All **gross** R.

* **helps in 11 of 22 scoreable mixtures — a coin flip.** The 23rd chose zero carriers, so
  selection would have skipped a family whose quintile-4 mean was +0.100.
* equal-weight per family: median **+0.00326**, mean **−0.0355**, range −0.554 to +0.141;
* **trade-weighted over 16,248 selected against 24,603 holdout trades: −0.004525 R/trade.**

The equal-weight mean is hostage to two 20- and 32-trade holdouts — drop them and it is +0.0114.
Both are published. On every weighting: **member selection inside these families is worth nothing
out of sample**, and the residual construction biases all run in the direction that would
*flatter* selection.

**Therefore — the prescription, not the rejection.** What moves these families is cost geometry:
§2's composition repair is worth up to +0.35 R/day per member and §3's entry shift another +0.14
on the FX cohort, plus AD's exit surface. The 23 route to those.

### 4.3 The pre-declared dial: 0 of 30

One bucket per mechanism, declared in source before any result in that file was computed, chosen
from what the mechanism IS plus a production precedent where one exists (`crypto.py:25` gates its
own donchian on `autocorr(60) >= 0.15`). Inside the bucket, AF's two-clause coherence test passes
**0 of 30**. The pre-declaration is what makes that worth reporting — AF §8 item 2 is the case
where an `n >= 100` floor excluded the mechanistically right bucket by six trades.

### 4.4 The crypto donchian split: the carrier is the CELL

| test | H4 | D1 |
|---|---|---|
| permutation null on cross-member SD (shuffled labels) | **p 0.0015** | p 0.382 |
| split-half sign agreement within each member's own history | **8 of 9** | 4 of 9 |
| vintage (history years vs mean R) | r +0.623, t 2.11 | r +0.649, t 2.26 |
| liquidity (log median tick volume) | r −0.228 | r +0.472 |

So the H4 split is real and the D1 one is not; liquidity flips sign across timeframes and is
refuted; vintage correlates and **DASHUSD refutes it as the mechanism** — 1.7 years of history
and the best H4 member in the family.

**And the statistic the brief did not ask for, which settles it.** The same nine symbols rank
differently at the two timeframes: **Spearman 0.20**, sign agreement **5 of 9**. DASHUSD is
−0.210 at D1 and **+0.883** at H4; XRPUSD +0.147 and −0.604. The carrier is the
**(symbol × timeframe) cell**, so it cannot have a symbol-level cause — maturity and liquidity
are properties of the same instrument in both. Do not price a crypto cluster on member selection.

---

## 5. `mx_nzdjpy` and the index volume-surge family

### 5.1 The pre-declared gate goes positive, and one lever does all of it

AF's −0.1953 reproduces **bit-for-bit** (−0.19526803768383966, p 0.9011098890110989, n=94) on an
independently regenerated population. On the **83 bars every arm shares** — the 11 dropped are
Friday D1 closes whose next H4 close is 51–53 h away, and their gross mean is *higher*, so the
94-trade cell flatters the middle step:

| step | composition | pooled OOS R/day | p_raw | folds+ |
|---|---|---:|---:|---|
| AF's baseline, broker 00 | v1 | **−0.28325** | 0.9332 | 0.0 |
| + composition repair, broker 00 | v2 | **−0.05487** | 0.6329 | 0.6 |
| + entry shift to broker 04 | v1 | **+0.21895** | 0.2467 | **0.8** |
| + entry shift to broker 04 | v2 | **+0.21895** | 0.2467 | **0.8** |

**The two repairs are not additive.** At broker hour 04 NZDJPY's hour multiplier is 0.92–1.05,
below `PREMIUM_FLOOR`, so the compositions are **bit-identical** there — the composition repair
is worth exactly **0.000** at the shifted entry, and the shift alone reaches +0.21895 under AF's
own unrepaired model. One defect, a rollover premium times a 10× era ratio, reached two ways.
Still REJECT on significance.

### 5.2 The post-hoc bucket holds in 2 of 5 eras

`VOL_REGIME == hi`, which AF offered explicitly as a map entry rather than a claim, is positive
in **2 of 5** eras (boundaries fixed in advance at five-year marks). The pre-declared
`PERSISTENCE == trend` is positive in **4 of 5**. AF was right not to promote it, and the era
test establishes that rather than assuming it.

### 5.3 The index volume-surge family — the session's best new cell

The gate reproduces AF's published fold means **exactly** — [0.3937, −0.1313, −0.0185, −0.0903,
0.3460].

| cell | n | pooled OOS R/day | p_raw | OOS folds+ |
|---|---:|---:|---:|---:|
| ungated | 610 | +0.0999 | 0.1204 | 0.4 |
| **pre-declared** `PERSISTENCE == revert` | 174 | **−0.0324** | 0.5952 | 0.6 |
| **enumerated best** `VOL_REGIME == hi` | 203 | **+0.2248** | **0.0127** | **1.00** |

The pre-declared bucket lifts fold stability and kills the mean, so **the pre-declared dial does
not explain the middle folds**. The enumerated cell does — 5 of 5 OOS folds positive, failing
only significance. Its 9-cell enumeration bill is carried (Bonferroni-within-enumeration
p 0.114). **It admits under BH α = 0.20 at ≤ 15 declared looks and Bonferroni α = 0.05 at ≤ 3.**

### 5.4 `idxrev`: dead in all four cells

Re-simulated, not sign-flipped — its `target_dist / sl_distance_price` is **0.7500** over all
5,597 trades, so negating a stored R would describe an instrument that does not exist. **Forward
parity 5,597 of 5,597 exact on `r_gross`** against AA.

| arm | n | pooled OOS R/day | folds+ |
|---|---:|---:|---:|
| forward | 5,597 | −0.0229 | 0.6 |
| inverse | 5,597 | −0.0866 | 0.0 |
| forward + pre-declared `PERSISTENCE == revert` | 1,720 | −0.0427 | 0.2 |
| inverse + `PERSISTENCE == revert` | 1,720 | −0.0918 | 0.0 |

Direction is not the problem and the regime an index-reversion sleeve was designed for is not the
rescue — it makes both directions worse. With AD's 1,631 exit cells (best +0.0004) that is exit
geometry, direction and regime all exhausted; the entry-hour lever does not apply because index
CFDs carry no quote at the rollover. **What is left is a different trigger definition, which is a
new sleeve rather than a repair of this one** — and that is the row, not a kill.

---

## 6. A bias I sized and did not repair

`era_ratio` is a ratio of bar **minima** (§1) while the anchor is a tick **p50**. For a
SCHEDULE-class era the recorded series is a *constant*, so its min IS its median and the ratio is
inflated by the reference window's own min-to-median factor: **fx 1.500×, jpy_fx 1.333×, metals
1.272×, index 1.103×, energy 1.018×, crypto 1.000×.**

AG measured the same quantity from the other direction (`tick_over_bar_factor`, 1.00×–1.73×) and
applies it **only** to modelled anchors, never to the era ratio. Not repaired here because it is
a defect in the era **term** — closing it means re-deriving `SPREAD_MODEL_V1.json`'s era table on
a min-consistent anchor. It runs the **same direction** as §2's repair, so every number this
session publishes is conservative with respect to it.

---

## 7. What is in the brief that I am correcting

1. **"Validate it on AG's own held-out pairs" cannot identify the composition.** Both sides of
   every block pair are all-hours medians, so the hour term is identically 1 in both and the
   product is unidentified. The brief's instinct is right — the fix has to be selected on
   held-out data — but the holdout has to vary the *interaction*, which is why §2 builds three
   axes instead.
2. **"`mx_cadjpy` is the named beneficiary; its whole cohort rides along" is half right.** The
   cohort does ride along on net, but the *mechanisms* separate: breakouts keep their edge four
   hours later and `atr_mean_reversion` does not, and `mx_cadjpy`'s own mechanism
   (`volume_surge_reversal`) is the marginal case. A single cohort-wide entry convention would
   take a measured loss on the reversion members.
3. **The named crypto split is the H4 family's, and the D1 family's is a different split that is
   indistinguishable from noise** (permutation p 0.382). The brief quotes one and the question
   "is that maturity, liquidity, or noise?" has different answers at the two timeframes — which
   is itself the answer (§4.4).
4. **`AF_REPAIRS_V1.json` → `R3_regime_conditioning.conditional_map` is gross R, not net.** The
   brief calls it the conditioning substrate, and it is — but a bucket that looks positive there
   can be negative once cost is charged, which is exactly what happened to `PERSISTENCE == trend`
   on `mx_nzdjpy` (gross +0.245, net −0.1953 at hour 00). Every cell in
   `CONDITIONING_MAP_V1.json` states its units for that reason.

---

## 8. What I got wrong

**An adversarial workflow of eight skeptics plus independent judges over every claimed refutation
was run before publication.** Three survived (the bar-min semantics, `PREMIUM_FLOOR`'s necessity,
the volume-surge cell). Five were refuted, every one correctly, and the judges upheld all five.

1. **My own first composition regressions said "v1 is fine".** b = +1.125 and +0.930, on samples
   whose informative content was three crypto symbols that pay no rollover premium and therefore
   force slope 1 by construction. One commit from shipping "no repair needed" on a real defect.
   §2.1.
2. **`PREMIUM_FLOOR` did not exist in the first implementation**, and two of AG's tests went red
   for a good reason: the repair was *raising* the metals charge 2.3× because XAUUSD's era ratio
   is below 1. §2.4.
3. **I cited the wrong cell as era-free.** "Survives on RECORDED eras and in the 2020s, where the
   era ratio is ≈1" is true of the 2020s leg and **false** of the RECORDED leg — `RECORDED`
   classifies the era's *series* as a dispersed per-bar measurement, not its ratio, and that
   cell's median era ratio is **2.125** with an effective/reference hour multiplier of 0.688.
   Fixed by measuring the cut that actually answers it (era ratio ∈ [0.9, 1.1], n=358), which is
   *better* evidence than what I had. §3.4.
4. **My chance baseline for carrier overlap drew from the wrong universe** — every member with
   ≥1 lifetime trade rather than the members scored in that fold, a universe that grows 2→9
   across folds in six families — and used `E|A∩B|/E|A∪B|` instead of `E[|A∩B|/|A∪B|]`. Both
   flattered. Corrected by exact enumeration: baseline 0.083–0.540 not 0.070–0.448, overlap beats
   chance in 13 of 23 not 16, below it in 9 not 6. §4.1.
5. **I mixed baselines in my own headline, breaking a rule my own generator states in its
   docstring.** The economics were arm B→C and the member counts were arm A→C. Against the
   control it is 38 of 42 improving, not 39, and the fourth worsener is not an
   `atr_mean_reversion` member. §3.2.
6. **I took the cost convention for physics.** `cost_r` anchors the whole spread bill at
   `entry_utc`, so moving the entry is credited with the exit leg's share. The 10.2:1 ratio is
   the ceiling; a 50/50 split gives 5.2:1 and a net +0.0633 rather than +0.1412. Cost still
   dominates, but the magnitude is a range. §3.1.
7. **My nzdjpy decomposition implied two additive repairs.** At the shifted entry the two
   compositions are bit-identical, so the composition repair contributes exactly 0.000 there and
   the entry shift alone reaches the same number under AF's unrepaired model. The corrected story
   is one lever, which is cleaner than the one I first wrote. §5.1.
8. **The equal-weight carrier-selection mean was carried by two thin holdouts.** −0.0355 becomes
   +0.0114 without them; the trade-weighted −0.004525 is the number that cannot be moved that
   way, and both are now published. §4.2.
9. **I claimed b = 1 was rejected on the era axis at 2.6 σ. It is not rejected there at all.**
   That SE was i.i.d. on 152 points drawn from 14 symbols over 11 shared quarters; clustered it is
   1.5 σ, below my own declared `REJECT_SIGMA`, with b = 1 inside the bootstrap CI. And the axis's
   broker-wide component — the thing a historical era ratio actually is — points **above** 1
   (1.463 ± 0.684). This was the justification I had put in shipped source, so it was a defect in
   `spread_model.py`'s docstring, not only in a report. The repair still stands, on a narrower and
   correctly-stated basis. §2.2.
10. **The per-cell premium filter was applied to the class median, not per cell**, so a
    redacted_account CHFJPY cell with a multiplier of exactly 1.00 — the very contamination
    `MIN_EFFECT_MULT` exists to remove — sat inside the `jpy_fx` fit. Honouring it moves that
    axis from 0.510 ± 0.416 to 0.721 ± 0.194 and the shipped exponent from 0.5041 to **0.4947**,
    which is the constant now in source; every downstream artifact was regenerated at it.
11. **I said "61 instruments" for the fx cross-section row.** The B axis is 33 cells across all
    classes at hour 0; the `fx` row is **14 cells = 7 instruments × 2 accounts**. Collapsed to 7
    instruments it still rejects b = 1, at 3.2 σ rather than 5.0.
12. **"Contamination by three crypto symbols" is true of the era axis and false of the
    cross-broker one**, which had exactly one (BTCUSD, carrying 66 % of the leverage). The
    mechanism holds; the count did not.
13. **My first C5 was about to compare two different partitions of two different quantities** —
   equal-count chronological quintiles of the *gross* series against the gate's walk-forward OOS
   folds *net* of cost. The verdict question is now answered by the gate; the quintiles are
   published with the caveat attached. §5.3.

**A scope cap, stated because the agreement forbids silent ones.** The H4 FX families' hour-00
subset was not run. One sixth of an H4 FX trade's fills land at broker 00 (from the bar stamped
20:00), so the same shift applies to them, and comparing it against the D1 result would separate
"cost effect" from "D1 mechanism effect" more sharply than §3.2 does. It was not run because it
is a fresh grid of hypotheses on every symbol at once and §3.2's per-mechanism split already
answers the question the work list asked. It is the first item in §11.

---

## 9. Scoped verification

**Blast radius.** Five production files, all verified **unbound** by the R2 decision contract
before editing:

* `src/costs/spread_model.py` — `damped_intraweek_mult`, `COMPOSITIONS`, `DEFAULT_COMPOSITION`,
  `ERA_HOUR_EXPONENT`, `ERA_HOUR_EXPONENT_ENVELOPE`, `PREMIUM_FLOOR`, `composition` /
  `era_exponent` on `estimate` and `spread_price`, `SpreadEstimate.composition`
* `src/costs/model.py` — `cost_r(spread_composition=, spread_era_exponent=)`, threaded to the
  model; the snapshot path is untouched and a test asserts it
* `src/research_infra/walkforward/spec.py` — `GateSpec.spread_composition`, `spread_era_exponent`
* `src/research_infra/walkforward/panel.py` — one call site
* `src/research_infra/walkforward/gate.py` — `_cost_window_note` publishes the composition, its
  exponent and its envelope
* `tests/test_spread_model.py` — one AG assertion loosened from an exact provenance string to
  the model path plus a behavioural quantity, because Session AH renamed the label

**Scope named mechanically** by `python3 scripts/pytest_failset.py scope --base 12b59d03f
--include-worktree` → 15 files:

```
tests/research_infra/test_trainer_folds.py tests/research_infra/test_trainer_partitions.py
tests/research_infra/test_vig_trial_ledger_prospective.py
tests/research_infra/test_walkforward_book_replay.py tests/research_infra/test_walkforward_family.py
tests/research_infra/test_walkforward_gate.py tests/research_infra/test_wf_diagnostics.py
tests/research_infra/test_wf_exits_parity.py tests/test_costs_layer.py
tests/test_spread_composition.py tests/test_spread_model.py tests/test_w7_recost.py
tests/ultimate_book/test_learning_actuator_cost_true.py tests/ultimate_book/test_live_evidence.py
tests/ultimate_book/test_live_evidence_calibration_v2.py
```

### 9.1 Receipt

```
........................................................................ [ 84%]
..........................................s.........                     [100%]
347 passed, 1 skipped, 1 warning in 9.12s
```

Green, so no base comparison was needed — §2 item 2 asks for one only to explain a failure. The
one skip is a precondition skip, not a repair. `tests/test_implementation_state_block_citations.py`
is inside the scope above and green after B1000–B1020 landed; the ceiling rose to B1020 and no sibling
citation went dangling.

**19 new behavioural tests** in `tests/test_spread_composition.py`. They assert *properties* —
that `b = 1` is v1 exactly, that the reference window is reproduced, that the multiplier is
monotone in the era ratio, that it never falls below 1, that an hour without a material premium
is untouched in both directions, that nothing moves where no rollover exists, that the envelope
is ordered, that the composition changes the spec seal — so re-measuring `b` on better data
changes one constant and not this file.

**The H1 contract check** reports the same **2 un-hydrated LFS pointers** at session end as at
session start (`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`,
`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`) and nothing else. No bound path drifted.

**Not run:** the full suite. `WAVE_8_WORKING_AGREEMENT.md` §2 makes it the orchestrator's, once
per merge train, diffed against the committed `FAILSET_BASELINE_MAIN.json`.

**Parity, which is the load-bearing verification here rather than the suite.** Three independent
reproductions of prior sessions' populations, each on two statistics:

| against | statistic | result |
|---|---|---|
| `AF_FAMILY_TRADES.json.gz` | trade count per member | **42 / 42 exact** |
| same | summed `r_gross` per member | **42 / 42 exact** |
| `AA_ESTATE_TRADES.json.gz` (`idxrev`) | per-trade `r_gross` | **5,597 / 5,597 exact** |
| AF `R5_nzdjpy_break` gated re-walk | pooled OOS mean, p, n, fold fraction | **bit-for-bit** |
| AF `FAMILY_ADMISSION_V1.json` | index volume-surge fold means | **exact to 4 dp** |

---

## 10. Artifacts

| path | what |
|---|---|
| `src/costs/spread_model.py` | the repaired composition, its constants, `damped_intraweek_mult` |
| `src/costs/model.py`, `walkforward/{spec,panel,gate}.py` | the composition carried to any gate run |
| `tests/test_spread_composition.py` | 19 behavioural tests |
| `phase8/receipts/ah_spread_scan.py` | the tick hour cells and the bar-semantics scan |
| `phase8/receipts/ah_spread_compose.py` | the three axes, the declared protocol, the fit |
| `phase8/receipts/ah_entry_shift.py` | the four-arm generator and the AF parity check |
| `phase8/receipts/ah_entry_gate.py` | the intersected population, 16 gate runs, cost split |
| `phase8/receipts/ah_entry_era_robustness.py` | the era-neutral cut |
| `phase8/receipts/ah_entry_attribution.py` | both baselines and both spread attributions |
| `phase8/receipts/ah_verdicts_moved.py` | AF's grid re-run under both compositions |
| `phase8/receipts/ah_conditioning.py` | C1–C5, the pre-declared dials, the conditioning map |
| `phase8/receipts/ah_idxrev_inverse.py` | the re-simulated inverse and the pre-declared gate |
| `phase8/receipts/ah_spread_v2_validation.py`, `ah_repair_rows.py` | the two assembled deliverables |
| **`phase8/receipts/ENTRY_HOUR_FRONTIER_V1.json`** | **deliverable 1** — before/after per member, gate verdicts at measured carry |
| **`phase8/receipts/SPREAD_MODEL_V2_VALIDATION.json`** | **deliverable 2** — the repair, its held-out evidence, the verdicts it moves |
| **`phase8/receipts/CONDITIONING_MAP_V1.json`** | **deliverable 3** — per family, per member, dial × bucket with fold stability and look counts |
| `phase8/receipts/AH_IDXREV_INVERSE_V1.json` | item 5 |
| `phase8/receipts/AH_{BAR_SPREAD_SEMANTICS,TICK_HOUR_CELLS,TICK_HOUR_CELLS_redacted_account,COMPOSITION_TESTS,ENTRY_SHIFT_TRADES,ENTRY_ERA_ROBUSTNESS,ENTRY_ATTRIBUTION,VERDICTS_MOVED}.*` | supporting receipts |
| `phase8/receipts/REPAIR_QUEUE_AH.json` | the 9 rows, also appended to the shared queue |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | **+843 rows**; total 5,628 |
| `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` | 49 → **58** rows; `REPAIR_QUEUE_V1.json` untouched |

---

## 11. Routing

**Borhen — one decision, and it is the same one AF routed.** `declared_family_size` now blocks
**two** candidates, not one. `mx_btcusd` at raw p 0.0064, and this session's
`volume_surge_reversal × index × D1` gated on `VOL_REGIME == hi` at raw p 0.0127 with **5 of 5
OOS folds positive**. The second admits under BH α = 0.20 at ≤ 15 declared looks and under
Bonferroni α = 0.05 at ≤ 3; its own 9-cell enumeration bill puts it at p 0.114 if you charge only
that. This is the same class of decision as the risk dial.

**Borhen — one thing that is a sleeve-geometry decision, not a research one.** The FX D1 cohort's
entry convention. Moving it from the D1 close to the first H4 close is worth **+0.063 to +0.141
R/trade** depending on how the spread bill is attributed, it moves four members across zero
including `mx_cadjpy`'s own live rule, and it costs a measured **−0.015 R/trade of gross**. None
of the affected sleeves is armed, so nothing about the live book changes with it — but the
convention is a contract, and contracts are yours.

**Session AI (challenge book)** — three things. `mx_cadjpy` and the three donchian JPY crosses are
now *positive at mid band* under the shifted entry, which changes what the candidate book can
contain; the `VOL_REGIME == hi` index cell is the strongest new candidate this wave produced; and
`declared_family_size` is the single number that decides both, so the arming package should state
what it assumes.

**Session AK (orphan/candidate sleeves)** — the entry-hour question is not FX-only in *principle*,
only in *this cohort*. Any candidate sleeve that decides on a D1 close and trades an FX symbol
inherits the whole 13×–38× charge. Check the decision hour before pricing anything.

**Wave 9** — four named items, in value order:

1. **The H4 FX hour-00 subset** (§8's scope cap). One sixth of H4 FX fills land at broker 00;
   the same shift applies, and it separates "cost effect" from "D1 mechanism effect".
2. **`atr_mean_reversion`'s own entry shift.** The cohort's 4 h is measurably wrong for it — the
   drift is +0.096 R on cadjpy — so the frontier between 0 h and 4 h is unpriced.
3. **The min-to-median era-ratio bias** (§6). Sized at 1.50× on constant-spread FX eras and not
   repaired; closing it means re-deriving the era table on a min-consistent anchor.
4. **The lifetime-versus-scored split** on the three donchian JPY crosses. They are positive in
   the scored window and negative over their pre-2010 history, which after this session is a
   sample/era question rather than a cost one — and the era term is exactly what §2 just repaired.
