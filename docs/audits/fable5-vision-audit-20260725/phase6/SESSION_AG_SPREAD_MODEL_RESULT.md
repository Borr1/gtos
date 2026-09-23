# Session AG — the era term, measured

**Branch `phase6/spread-model`. Blocks B700–B749. Not merged.**

---

## 0. Headline

The programme's largest disclosed bias is no longer a disclosure. MT5's bar `spread`
column records a spread **per bar back to 2000**, so the era term is measurable rather than
assumed, and `spread_model_v1` measures it for **73 symbols across 2,653 quarters**
(46 FTMO, 27 redacted_account; 63 anchored on tick truth, 10 on bars alone).

**The measurement corrects the premise it was built to size.** The standing disclosure —
W's `_cost_window_note`, quoted into every gate result — says *"retail CFD/FX spreads
compressed materially over that period, so historical trades are systematically UNDER-costed
and every pooled OOS mean is optimistic."* Measured:

| symbol | 2002Q2 | 2007Q2 | 2013Q2 | 2019Q2 | 2022Q2 | 2025Q2 |
|---|---|---|---|---|---|---|
| `EURUSD` | **50.00** [41.7, 60.0] | 20.00 [16.7, 24.0] | 1.79 [1.49, 2.15] | 5.66 [5.58, 5.73] | 2.00 [1.67, 2.40] | 2.01 [1.83, 2.20] |
| `USDJPY` | **20.25** [16.0, 25.6] | 12.15 [9.61, 15.4] | 1.04 [0.86, 1.25] | 2.72 [1.93, 3.83] | 0.81 [0.64, 1.02] | 2.43 [1.92, 3.07] |
| `GBPJPY` | 10.89 [9.02, 13.2] | 5.08 [4.21, 6.14] | 0.85 [0.70, 1.02] | 2.45 [2.24, 2.68] | 0.22 [0.18, 0.26] | 1.04 [0.90, 1.20] |
| `CADJPY` | – | 10.00 [8.33, 12.0] | 5.72 [3.65, 8.96] | 3.17 [2.50, 4.02] | 0.50 [0.46, 0.55] | 2.00 [1.99, 2.01] |
| `XAUUSD` | – | – | 0.61 [0.38, 0.97] | 0.38 [0.35, 0.42] | **0.18** [0.16, 0.19] | 0.58 [0.57, 0.58] |
| `XAGUSD` | – | – | 0.27 [0.18, 0.40] | 0.40 [0.31, 0.52] | 0.23 [0.21, 0.26] | 0.31 [0.29, 0.33] |
| `XPTUSD` | – | – | – | 0.29 [0.23, 0.38] | 0.73 [0.43, 1.24] | 0.41 [0.30, 0.55] |
| `US30_cash` | – | – | – | – | 0.61 [0.55, 0.69] | 0.98 [0.84, 1.15] |
| `NAS100` | – | – | – | – | 0.40 [0.37, 0.44] | 0.96 [0.60, 1.52] |
| `UKOIL_cash` | – | – | – | – | 0.69 [0.50, 0.95] | 0.34 [0.33, 0.35] |

(Ratios against the 37-day snapshot the estate charges today. `>1` = history was dearer.)

**The disclosure is right about FX and inverted for everything else.** EURUSD in 2002 cost
50× what the snapshot charges. XAUUSD in 2022 cost **0.18×** — today is five times dearer
than the era being evaluated, so a metals result charged the snapshot was **over**-costed,
not under. The same holds for silver, platinum, indices and oil.

That matters more than the average magnitude, because **three of the four armed sleeves
trade metals, energy and crypto.** A bias with no consistent sign cannot be reasoned about
in a footnote; it has to be charged. It now can be.

**Second half: "no measured spread" is no longer a refusal.** `cost_r` hard-raised for 131
of 167 FTMO instruments. Eight of them — `XPTUSD`, `XPDUSD`, `XCUUSD`, `ADAUSD`, `DOTUSD`,
`LTCUSD`, `XRPUSD`, `XTZUSD` — are now priceable with bands, plus two on redacted_account. On
redacted_account the effect is larger than the count suggests: the bar archive holds only **7**
of its symbols against FTMO's 43, so 18 more became priceable from their tick anchor alone.

> **Corrected at the end of the session, and the correction costs me a headline.** The
> counts above were 137 and *eleven* for most of this session. `BROKER_TRUE_COSTS_V1.json`
> was **regenerated at 17:03 UTC while I was working** — the export my own prompt said was
> in progress — taking FTMO's tick-measured symbols **30 → 36**. `CADJPY`, `DASHUSD`,
> `NATGAS.cash`, `EU50.cash`, `SPN35.cash` and `AUS200.cash` are now measured directly, so
> they are no longer mine to claim. See §9; the same event took three of my own tests red
> on premises the data had overtaken, and exposed a real defect in the band path.

**And the honest limit, unsoftened, because Fable wrote it and it is right:**

> **Bands narrow the look-ahead; they do not eliminate it. Only capture does.**

The era instrument is validated at ratios of **0.78–1.30** and at one out-of-sample point.
**Nothing validates it at the 20×–50× the pre-2010 FX eras imply.** Those eras are class
`SCHEDULE` — a backfilled constant, the broker's own statement about the era rather than a
per-bar observation — and they carry the widest bands for that reason.

---

## 0b. The armed book, and who actually fixed it

`FOURTH_REVIEW.md:273` records that **the armed book cannot currently be gate-scored at all
on coverage**. Measured against the model, and against the artifact as it stands now:

| sleeve | blocker | snapshot | with the model | who closed it |
|---|---|---|---|---|
| **`crypto`** (armed, real money) | `DASHUSD` | 2 of 2 | 2 of 2 | **the tick export, not me** |
| `sub_xvol_pullback` (armed) | `EU50.cash` | 1 of 1 | 1 of 1 | **the tick export, not me** |
| `metals_core` (armed) | four metal crosses | 6 of 6 | 6 of 6 | the earlier tick export |
| `structural_retest` (crypto arm) | XRP/XTZ/DOT/ADA/LTC | 3 of 8 | **8 of 8** | this model |

**I am not claiming `crypto`.** For most of this session it was the headline — its surface is
exactly `("BTCUSD", "DASHUSD")` (`sleeves/crypto.py:24`), one missing tick file put it at
47.9 % coverage and `NOT_EVALUABLE`, and the model priced DASHUSD from bars. Then the tick
export landed and made it MEASURED outright. The model **would** have made `crypto`
scoreable, and it is worth recording that it independently reached the same answer from a
different input path — but the credit belongs to the capture, and a session that quietly
kept the headline would be reporting a race it lost.

What the model still contributes on its own: the five crypto minors `structural_retest`
needs, the 18 redacted_account symbols with ticks and no bars, and — for every one of these
sleeves — **the era term**, which no amount of forward tick capture supplies.

### Cross-broker validation, unprompted

`src/costs/model.py:472` states BTCUSD's quoted spread "differs 22x between" the two
accounts. Built from a different input path (bar eras × per-account tick anchors), the model
returns FTMO 1.00 against redacted_account 22.56 at the same instant — **22.56×**. Nothing in it
was fitted to that number.

---

## 1. The find, and how it was checked before it was believed

`vps-bars-20260727/*.csv.gz` carry columns
`time,open,high,low,close,tick_volume,spread,real_volume`. The `spread` column is populated
back to 2000 for FX and 2010 for metals. That is a **direct historical spread series** that
nothing in this estate had used.

The working agreement's §4 item 2 says: when your probe says something surprising, suspect
the probe. It was suspected four ways.

**1.1 The column is three populations, not one.** Mechanically classified per quarter:

* `RECORDED` — dispersed per-bar values. A real measurement.
* `SCHEDULE` — one constant held across a multi-year block. EURUSD 2000–2003 is exactly
  50 points at p10 **and** p99. That is the broker's history-server backfill: still the
  broker's own statement about the era, but MODELLED, not observed.
* `FLOORED` — a large mass at 1 point beside a plausible upper tail (GBPJPY 2018: p25=1,
  p75=18, p90=26). 0.1 pip is not a GBPJPY spread; a p50 over those bars is meaningless.
* `QUANTIZED` — ≤3 distinct values.

**1.2 It is used for ratios, never levels.** The bar-recorded level and the tick-median
level differ — measured at **1.00×–1.73× across 22 symbols** that have both. Any constant
multiplicative bias divides out of a ratio, so what has to be true is only that the column
*tracks* spread changes.

**1.3 Does it track? 188 held-out era ratios say yes, modestly.** The 37-day tick window was
cut into weekly blocks; for every symbol and ordered block pair, tick truth gives a real
spread ratio and the bar column gives a predicted one — 540 pairs, 27 symbols.

**Two things had to be fixed in the scoring before it meant anything**, and both are worth
recording because both would have picked the wrong estimator:

* **352 of the 540 pairs do not move at all.** Quoted spread is quantised to the point, so
  the tick median is the *same integer* week to week for most symbols. Model and baseline
  both score exactly 0 there. Selecting on the pooled median picks the variant best at
  predicting "no change". Selection runs on the **moved subset** (188 pairs).
* **A low error is not skill.** Against a "predict no change" baseline, the leading variants
  score **0.33–0.35** — a third of the error removed, not a ground truth.

Skill rises with the data per era: **0.333 at 7-day blocks → 0.370 at 14 → 0.582 at 21**,
which is the signature of estimation noise rather than bias, and it is why quarterly eras
are better estimated than this test's own resolution.

**1.4 H4, not D1, and that was measured too.** Over the same 188 pairs, **H4 skill 0.334
against D1's 0.007** — D1 records one spread reading per day, so an era estimated from it is
six times thinner. The gold window agrees out of sample: **−0.45 % at H4, −6.97 % at D1.**
D1 is kept only where H4 is absent, and its disagreement with H4 widens the band rather than
voting in it.

**1.5 The out-of-sample point named by the prompt.**
`ULTIMATE_TICK_SPREAD_GOLD.json` measures XAUUSD over 2025-10..2026-04 at median **0.37**
price on 1,288,483 ticks; the archive window measures **0.46** on 690,463. True era ratio
**0.8043**. The bar column at H4 predicts **0.8007** — **−0.45 %**.

**Stated because it matters: this is n = 1, and it is no longer out-of-sample for the
winning variant**, because the variant family was written after this window was inspected.
The block holdout is the selection instrument; the gold window is corroboration.

**1.6 Price-proportional scaling, and a correction to my own first verdict.** Regressing
log(spread ratio) on log(price ratio) over 1,076 consecutive `RECORDED` quarter pairs on 43
symbols: **β = 0.823 ± 0.144, R² = 0.0295.**

An earlier draft of this result string said *"price-proportional scaling REFUTED: β is 1.2
standard errors from 1.0"*. **That was an overclaim and it is withdrawn.** 1.2 SE is not a
rejection of the slope. What *is* rejected is price as a **model**: it explains **2.9 %** of
the variance in era spread changes. Knowing how the price moved between two eras tells you
almost nothing about how the spread moved. N §8.5's counterexample is not an exception, it
is typical.

---

## 2. The bands, and what makes them honest

`low`/`mid`/`high` come from a per-era half-width in log space. Every term is measured:

| term | what it is |
|---|---|
| cross-instrument dispersion | 9 estimator variants applied to the same bars |
| split-half sampling noise | interleaved halves of the era — two independent draws |
| D1-vs-H4 disagreement | the second timeframe's opinion, when comparable |
| era-class floor | the **measured** median quarter-to-quarter move of `RECORDED` eras (0.0911 log, n=959), doubled for `SCHEDULE`/`FLOORED`, quadrupled for `ABSENT` |

The class floor exists because of a real failure: a backfilled constant makes every
estimator agree and the split-half noise is exactly zero, so **DASHUSD 2026Q1 came out of
the first build as `mid=1.000` with a half-width of `0.000`** — maximum confidence on the
era where the data is least trustworthy. Perfect agreement on a placeholder is not certainty.

**A band too wide to decide anything is published as a capture requirement, not a band.**
**9.3 %** of FTMO eras and 14.4 % of redacted_account's exceed the threshold and carry a
`capture_requirement` string naming what would close them. That is the prompt's own rule and
it is enforced by test.

---

## 3. Four defects in my own model, found and fixed

Recorded because each one shipped a plausible-looking wrong number first.

| # | what broke | how it showed | fix |
|---|---|---|---|
| 1 | **EURUSD silently absent** from build 1 — the most-traded symbol in the archive | 100 % of its H4 bars inside the 37-day reference window record spread `0`, which means "not stored", not "no spread". Empty reference → no ratios → symbol dropped without a message | reference window widens backwards until it has something to measure, and records by how much |
| 2 | **USDJPY 2021 published as `mid=20.25`, band [0.47, 867]** | the floor filter discarded the 64 bars reading 1 point and kept the rare legacy 50s | floor filter disabled where >50 % of the data sits at the floor — a variant that discards most of the data is not measuring the same quantity |
| 3 | **all 27 EURUSD eras undecidable**, half-width ln(2) | the guard for #2 keyed on the variant *name*; every `trimmed_mean_*` also drops the floor (`_trimmed_mean(drop_floor=True)`), so they stayed in and returned the rare 2s against the mean's 1.05 | guard keys on a behaviour set, `FLOOR_DROPPING` |
| 4 | **a manufactured ln(2) "timeframe disagreement"** on EURUSD | H4's reference widened 90 days and D1's 730, so the two ratios answered different questions | disagreement term only when both references are comparable |

A fifth, in the validation rather than the model: **`refute_price_proportional` collected
zero pairs** because it read an estimator key `scan-bars` never writes. It crashed on the
division rather than reporting a fabricated β — but a statistic assembled from an empty set
is exactly the failure mode this review exists about, so it now recomputes from the bars.

---

## 4. What ships

| artifact | what it is |
|---|---|
| `src/costs/spread_model.py` | the production API: `spread_price(symbol, account, at_utc, band=…)` → banded estimate with coverage class and provenance |
| `src/costs/model.py` | `cost_r(..., spread_band=…)` — **opt-in**; with `None` every existing caller is byte-identical, including the refusal path |
| `src/research_infra/walkforward/spec.py` | `GateSpec.spread_band` |
| `src/research_infra/walkforward/gate.py` | `_cost_window_note` now publishes the measurement and **corrects its own direction claim** |
| `scripts/build_spread_model.py` | `scan-ticks` / `scan-bars` / `validate` / `fit` / `entry-timing` |
| `SPREAD_MODEL_V1.json` | 73 symbols, 2,653 priced eras, bands, capture requirements |
| `SPREAD_MODEL_VALIDATION_RESULT.json` | block holdout, gold window, price-proportionality |
| `ENTRY_TIMING_V1.json` | §5.5 — hour-of-week cost curve per symbol |
| `SPREAD_PRICEABILITY_V1.json` | who became priceable, who still is not, and what capture closes it |
| `ARMED_SLEEVE_COVERAGE_V1.json` | §0b — per armed sleeve, what the snapshot refuses and what the model prices |
| `tests/test_spread_model.py` | 24 behavioural tests |

---

## 5. Entry timing — the second thing the ticks buy (§5.5)

Measured on the broker wall clock, where hour 0 of a weekday **is the daily rollover** and
**is where a D1 bar closes**:

| symbol | spread at broker hour 00 | base p50 | best hour |
|---|---|---|---|
| `GBPUSD` | **38×** | 3e-05 | 02 (1.00×) |
| `EURUSD` | **32×** | 1e-05 | 02 (1.00×) |
| `USDJPY` | **19.3×** | 0.003 | 02 (1.00×) |
| `USDCAD` | 17.6× | 5e-05 | 05 (0.80×) |
| `CHFJPY` | 16.2× | 0.019 | 01 (0.84×) |
| `EURGBP` | 14.0× | 5e-05 | 02 (1.00×) |
| `GBPJPY` | 13.7× | 0.019 | 05 (0.89×) |

**It is an FX/JPY-family effect.** Fourteen symbols — every metal, index and oil CFD —
**do not quote at all** at the rollover, so they cannot pay it. XAUUSD's own worst hour is
1.14×.

The prescription is one hour of patience: by broker 01:00 the multiplier is back to
1.3–2.0×. This is published as a measurement; **entry convention is sleeve geometry and
belongs to wave 7's cost-geometry lane.**

---

## 5b. The banded re-stamp of W's mx pilot — the era term changes verdicts

W's twelve live `mx_*` sleeves, **his own trades** (generated once by
`w_mx_pilot.build_trades`, not re-implemented; **trade counts byte-identical to the
committed `W_MX_PILOT.json`**), through the same gate at four cost configurations. Re-run
after the artifact update, so these are the current numbers.

### `mx_btcusd_d1_donchian_20_breakout` — BAND-UNSTABLE

| | snapshot | low | mid | **high** |
|---|---|---|---|---|
| verdict (`C_exploratory`) | ADMIT | ADMIT | ADMIT | **REJECT** |
| pooled OOS mean R | 0.2446 | 0.2396 | 0.2382 | **0.1452** |

This is **the only sleeve that passes any standard in W's whole pilot.** It passes on the
flat snapshot and at low and mid, and **fails at the high band** — a 41 % fall in pooled OOS
mean. Under the old regime it would have passed with a footnote.

**Repair, not verdict.** The cause is identifiable: FTMO restructured crypto pricing (the
broker-truth artifact carries a *measured* 6.49 bp notional commission on crypto, and
BTCUSD's era ratios run 9× in 2022 and 32× in 2025 against a 2026 anchor of 1.00). The
sleeve's deep history is being charged spreads from a pricing regime that no longer exists.
Repair paths in cost order: **(1)** re-evaluate on the current pricing regime only (2026Q1+,
era ratio ≈1 and `RECORDED`) — cheap, costs sample depth; **(2)** split the panel by *broker*
pricing regime and require the edge in each, the §5.2 conditioning treatment with a broker
regime rather than a market one; **(3)** forward tick capture on BTCUSD, which settles it.

### The two sleeves the era term moves most — both JPY, both by ~0.33 R

| sleeve | snapshot | low | mid | high | mid − snap |
|---|---|---|---|---|---|
| `mx_nzdjpy_d1_donchian_20_breakout` | **+0.0800** | −0.1816 | **−0.2595** | −0.3922 | **−0.340** |
| `mx_cadjpy_d1_volume_surge_reversal` | **−0.0024** | −0.2568 | **−0.3252** | −0.4249 | **−0.323** |

`mx_nzdjpy` reads mildly profitable flat and is clearly negative once the JPY era ratios
(3×–10× through the 2000s and 2010s) are charged. `mx_cadjpy` reads **exactly break-even**
flat — the kind of number that earns a sleeve another look — and is **−0.33 R** charged its
own eras. Verdicts were REJECT either way; what changes is that the reason moves from
marginal to decisive, which is what a repair list needs to be built on.

**Repair levers, in order of what the measurements support:** both are FX sleeves, so both
are the entry-timing customers of §5 (`NZDJPY` pays **13.7×** and `CADJPY`'s class pays
14–17× at the rollover their D1 bar closes on); cost in R scales inversely with stop
distance, so the §5.1 stop-width surface is the second lever; and restricting to the
post-2015 era, where their ratios approach 1, is the third.

### The rest

`EU50.cash` and `FRA40.cash` stay `NOT_EVALUABLE` at every band — `FRA40.cash` is absent
from both archives, and `EU50.cash` gained a tick file but still has no bars, so the *sleeve*
remains ungeneratable. Four sleeves move *up* (`jp225` +0.0069, `us500` +0.0035, `us30`
+0.0013, `us100` +0.0010): the over-charging direction, indices being dearer today than in
their history.

**Family totals: 0 ADMIT under `A_strict` and `B_balanced` at every band**, as in W's run.
The era term did not rescue this family and did not need to — what it did was replace one
silent pass and two indistinguishable-from-zero rejects with a diagnosis each.

> **Corrected against the first run of this receipt.** Before the artifact update `CADJPY`
> had no measured spread, so `mx_cadjpy` was `NOT_EVALUABLE` at the snapshot and the model
> was what gave it a verdict at all. It is now tick-measured, so the snapshot judges it too
> — and the comparison it enables (−0.0024 flat against −0.3252 era-charged) is *more*
> informative than the one I originally claimed. `mx_btcusd`'s band instability and
> `mx_nzdjpy`'s sign flip are unchanged by the update.

---

## 6. What I did not deliver as specified, and why

**The volatility dimension is measurably flat, and I am reporting that rather than a fitted
curve.** §4.6 asks for spread as a function of hour-of-week **× volatility state**. The
hour-of-week term is strong and shipped. The volatility term, at the median, is **1.000 for
every class except metals** (0.963 → 1.013 across quintiles). FTMO's quoted spread on these
instruments is close to administered; the variation lives in the tail and in the hour, not
in the daily volatility state. Both a look-ahead-free trailing state and a contemporaneous
one were measured so the two could be compared — neither moves the median.

The model ships the term (it is in the artifact and applied multiplicatively), but a reader
should know it is doing almost nothing, and why, rather than discovering a 1.000 later and
wondering whether it was wired up.

---

## 7. The trial ledger, and a correction I made to my own count

Per agreement §3 every variant is logged; `SPREAD_MODEL_TRIAL_LEDGER.jsonl` has 135 rows and
`build_trial_budget_ledger` ran over the route — **its first run anywhere in this repo.**

Its first answer was `recommended_n_trials_for_dsr = 10,930`, 85× `gate.py`'s floor of 128.
**That was wrong in the dangerous direction and I withdrew it.** 10,764 of those rows are
`era_series`: one spread level measured per symbol per quarter per estimator. Measuring one
fixed quantity 10,764 times is not a search over 10,764 hypotheses, and none of it touched a
sleeve's returns — the ledger's own docstring draws exactly this line. The honest search
count is **63** (the estimator family compared on held-out block pairs at two timeframes,
plus 3 block widths and the price-proportionality regression), rising only because the
validation was re-run after the artifact update, and it is small because the model was chosen on a
validation criterion rather than by trying things until a sleeve passed.

Separately: any admission that cites a banded verdict carries **12** evaluations of that
sleeve (4 cost configurations × 3 admission options) in its own trial count.

---

## 9. The artifact moved under me, and it was the most useful hour of the session

`BROKER_TRUE_COSTS_V1.json` was regenerated at **2026-07-29T17:03 UTC**, mid-session, taking
FTMO's tick-measured symbols **30 → 36**. My prompt had said, in so many words, *"re-read
`BROKER_TRUE_COSTS_V1.json` rather than assuming any symbol is unpriced."* I read it once at
the start and built on that read. Three things followed.

**1. A real defect in the band path, in the embarrassing direction.** Three of the six new
tick files — `EU50.cash`, `SPN35.cash`, `AUS200.cash` — have **no bar file at all**. The era
loop iterates the *bar* archive, so it skipped them entirely, while `cost_r` prices them
happily from the flat snapshot. **Passing `spread_band=` would have turned a priceable
symbol into a refusal.** Asking for more information must never yield less. Fixed: a symbol
with ticks and no bars gets a MEASURED anchor, an era ratio of 1.0, and — away from the
reference quarter — the widest honest band there is, the observed spread of era ratios
across its instrument class, flagged undecidable with a named capture requirement. It is
guarded by `test_a_band_is_never_worse_than_no_band`, which walks **every** tick-measured
FTMO symbol rather than a hand-picked one.

That fix also closed the redacted_account gap below: **18 redacted_account symbols** have ticks and no
bars and are now priceable, where the bar-driven loop had reached only 7.

**2. Three of my own tests went red on premises the data had overtaken.** They named
`CADJPY` and `EU50.cash` because those were unpriced when I wrote them. Both gained tick
files an hour later. The tests were not wrong about behaviour — they were wrong to hardcode
a coverage fact from a file that demonstrably changes under a running session. They now
derive their fixtures from the artifact at runtime (`_a_symbol_the_snapshot_refuses`,
`_commission_resolves`), which is the same lesson the prompt was teaching.

**3. It cost me the session's best headline, and that is the right outcome.** See §0b.

The general point is worth more than any of the three: **this estate's inputs change while
sessions run.** A claim of the form "X is unpriced" has a timestamp on it whether or not the
author wrote one. Every coverage number in this document now carries the artifact's
`generated_utc` beside it.

---

## 9b. The A/B

**665 bad → 665 bad by failure set, 0 stably regressed, 1 fixed, +24 net new passing tests**
(10,883 → 10,907, exactly the 24 new test functions). `7b0f4f276` → `1901328f1`, both
captures embedded in `phase6/receipts/SESSION_AG_AB.md`.

The fixed one is `test_unpriceable_symbol_is_recorded_not_assumed_zero` — broken at *both*
ends by the tick export, repaired here. The one flagged regression,
`test_high_load_integration`, is a load flake: 3/3 in isolation at HEAD, 10/10 in its own
file, and it **passed in the BEFORE capture and in an earlier capture of this same branch**,
failing only in the final one while three full suites ran concurrently on this machine. Both
captures saw the same cost artifact, which is what makes the comparison about the code.

---

## 10. What is still open

1. **Forward tick capture.** The only thing that closes the residual look-ahead. The bands
   are validated at 0.78–1.30 and corroborated at one 7-month point; the 20×–50× FX eras are
   `SCHEDULE`-class and unvalidatable from what exists.
2. **A broker history re-pull** for the 195 FTMO eras published as `capture_required` —
   cheaper than tick capture and it would close most of them.
3. **123 FTMO symbols remain unpriceable** — equities and exotic FX with neither ticks nor
   bars. None is in any live registry.
5. **The redacted_account bar export stops at ETHUSD.** The archive carries **43 FTMO symbols and
   7 redacted_account** (`ADAUSD, AUDJPY, AUDUSD, BTCUSD, CADJPY, CHFJPY, ETHUSD` — alphabetical,
   then nothing), so redacted_account has no *era* term beyond those seven, only a tick anchor. It
   reads as complete because `BARS_MANIFEST.json` carries an `FTMO_COVERAGE_GAPS` key and
   **no redacted_account equivalent** — the manifest audits one broker's coverage and not the
   other's. Completing it is a bar pull, not a tick capture: the cheapest item on this list.
4. **Entry-timing repair** is measured, not applied. Wave 7.
