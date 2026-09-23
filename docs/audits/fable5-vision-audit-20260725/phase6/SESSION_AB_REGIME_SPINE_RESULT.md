# Session AB — the armed book's frequency ramp, attributed

**Wave 6.** Branch `phase6/regime-spine`, worktree `worktrees/wave6-regime-spine-20260729`.
Blocks **B650–B699**. Not merged to `main`.

---

## 0. The answer, in one page

The armed four's out-of-window record is **mostly a measurement of when their instruments
existed**, and where it is not, it is one sleeve whose regime is episodic rather than
decayed. Neither reading is "the book is bad", and the brief was right that nobody had
separated them.

Measured on the whole H4 archive, per (symbol, bar) the live engine would have evaluated,
on a **strict symbol panel** — only symbols with bars in *every* year of both eras, so the
2021 surface expansion cannot fake a rate change:

| sleeve | strict panel | fires/1k slots 2015–2019 | 2025+ | ratio |
|---|---|---:|---:|---:|
| `metals_core` | XAUUSD, XAGUSD | 4.163 | 4.139 | **0.99** |
| `metals_softband` | XAUUSD, XAGUSD | 1.821 | 2.070 | 1.14 |
| `crypto` | BTCUSD | 6.800 | 8.608 | 1.27 |
| `energy_agri` | — | *no oil bars before 2020-12-28* | 8.275 | **(a) entirely** |
| `sub_xvol_pullback` | XAUUSD, XAGUSD | 0.065 | 1.656 | **25.4** |

`metals_core` — the conf-1.0 anchor of the armed book — **has no frequency ramp at all**.
Three of the four are flat to mildly up. The book-level ramp is the *number of sleeves and
symbols that exist*, plus `sub_xvol_pullback`.

And `sub_xvol_pullback`'s 25× decomposes cleanly, on counts large enough to trust:

| era | slots | → vol≥1.6 | → slope50>1.5 | → **mtf conflict** | → persist rand | fires |
|---|---:|---:|---:|---:|---:|---:|
| 2015–2019 | 15,373 | 298 (1.94 %) | 161 (54.0 %) | **1 (0.62 %)** | 1 | 1 |
| 2025+ | 4,832 | 237 (4.90 %) | 119 (50.2 %) | **15 (12.6 %)** | 8 (53.3 %) | 8 |

The whole ramp is one conditional: **how often the 20-bar and 100-bar trends disagree,
given high volatility and a 50-bar uptrend.** Its *unconditional* rate is flat over 22
years (0.271 → 0.254 on the same panel), so this is not a threshold drifting — it is the
market's joint structure. That is cause (c), and it names its own dial.

**Held to one book over the era that book existed, the picture is cleaner than either
number in circulation.** Same four sleeves, all four with a tradeable instrument from
2021-02-17, split at the selection boundary:

| window | trades | book-days/month | %/month |
|---|---:|---:|---:|
| **2021-02 → 2024, outside the selection window** | 298 | 2.894 | **+0.117** |
| 2025+, the selection window | 137 | 2.947 | +2.212 |

The book is **positive out of window**, and **the frequency term is flat** — book-days/month
move ×1.018 while the per-day edge moves ×18.6. `SESSION_V` §7 attributes the multiple to
both terms (*"the edge per book-day is 5.3× higher and the firing frequency is 7.1×
higher"*); on a like-for-like book only one of them moves. **V's frequency term was the
surface arriving, not the market speeding up.** What remains to explain is the per-day edge
— a smaller and cleaner question than the one the estate has been carrying.

**Three prescriptions come out of it, and all three are cheap:**

1. **`metals_core` is a cost-geometry case, not an edge case.** Gross **+0.174 R/trade**
   over 385 trades and 21 years; cost **0.259 R**, of which **0.126 is spread**; net
   **−0.085**. Cost in R is a price drag divided by the stop, so the stop is the lever.
   Swept: at **stop × 3.0** it is **+0.098 R/trade** and **+0.023 R/day**, positive in the
   pre-2024 era on n=297. §4.
2. **`sub_xvol_pullback`'s selection-artefact doubt does not survive its neighborhood.**
   **125 of 125** adjacent threshold cells are net-positive; the production cell ranks
   **49th of 125** with the neighborhood median at 85 % of it. Geometry: 25 of 25 positive.
   An edge that survives every cell around it was not manufactured by the cell that was
   chosen. §5.
3. **A live-generation defect worth 1.3–6.8 % of every H4 sleeve's trades**, found by the
   fidelity check rather than looked for: the last closed bar before every session gap is
   unreachable. The fix is written and tested; wiring it is one line and Borhen's call. §7.

**None of this is evidence the book is bad.** Two of the four sleeves could not be measured
before 2021 for want of data, one has no ramp, and one has a regime that switches on and
off. Where a number is negative — `metals_core` at production geometry — the finding is a
named repair with a measured frontier.

---

## 1. What was built

`src/research_infra/regime_spine/` — the condition-series engine. It answers the question
`GenerationPort` cannot: not *"did the sleeve fire?"* but *"which gate stopped the other
bars, and did that gate's pass rate move?"*

| module | what |
|---|---|
| `state.py` | one pass over a bar series → every statistic any armed gate tests |
| `conditions.py` | the sleeves' gate chains, each gate tagged `availability` / `threshold` / `structure` |
| `ramp.py` | the exact funnel decomposition, the panel controls, the joint-lift discriminator |
| `normalize.py` | fixed cut → trailing-percentile cut, fitted pre-2024 |
| `sweep.py` | one variant end to end: fires → fill → broker-true cost → per-era statistics |
| `dials.py` | the five named regime variables + the feature/label row schema |
| `archive.py` | bars in, frames out, through `CsvBarSource` so the timebase seam is never bypassed |
| `trials.py` | the trial-budget appender (§8) |

**Fidelity is checked twice, both behaviourally.** `test_regime_spine_state.py` asserts the
frame equals `primitives.atr14/autocorr/vol_ratio`, `metals.htf_trend/fvg_signal`,
`substrate_engine.compute_state` and `crypto.crypto_signal` **exactly** — no `approx`,
because the frame deliberately sums the same slices the production functions sum rather
than using a rolling accumulator, so exactness is achievable and a tolerance would only
hide drift. `test_regime_spine_conditions.py` asserts the fire set against
`X_ESTATE_TRADES.json.gz`, which Session X generated by driving the production
`UltimateBookLiveEngine._generate_intents`. Result: **`only_port = 0` and
`geometry_mismatches = 0` on all five H4 sleeves** — this package never misses a bar the
live engine fires on and never disagrees about direction or stop.

42 new tests, all green.

---

## 2. The ramp, attributed

`AB_RAMP_ATTRIBUTION_V1.json`. The identity is exact, not a model:

```
fires = eval_slots × Π_g (passed_g / reached_g)          residual measured at ~1e-16
```

so `log(fires_B/fires_A)` splits into an **opportunity** term (cause (a)) and one term per
gate, with no remainder.

### (a) — surface availability, and it dominates

First evaluable bar per sleeve, regenerated from the archive:

| sleeve | surface opens | note |
|---|---|---|
| `metals_core` | **2004-07-30** | XAUUSD only until 2008 (XAGUSD), 2 of 6 symbols until 2021-01 |
| `sub_xvol_pullback` | **2004-08-02** | 1–3 of 18 symbols until 2021; 5 never in the archive |
| `crypto` | **2017-02-21** | BTCUSD; DASHUSD only from 2024-10 |
| `energy_agri` | **2021-02-17** | FTMO holds **no oil bars before 2020-12-28** |

Five of `sub_xvol_pullback`'s 18 registered symbols — `CORN_c`, `COTTON_c`, `FRA40_cash`,
`EU50_cash`, `US2000_cash` — are **absent from the bar archive entirely**. That is a named
data hole, not a sleeve property.

Book-day density, regenerated (a book-day = any armed sleeve fired anywhere):

| year | book-days | density | sleeves with a surface | density **per open sleeve** |
|---|---:|---:|---:|---:|
| 2015 | 5 | 1.92 % | 2 | 0.96 % |
| 2017 | 20 | 7.69 % | 3 | 2.56 % |
| 2021 | 27 | 10.35 % | 4 | 2.59 % |
| 2025 | 53 | 20.31 % | 4 | 5.08 % |

Session V's cache-based figures were **0.4 % (2015) → 28.7 % (2025)**, a 72× ramp. On the
regenerated stream it is **1.92 % → 20.3 %** (10.6×), and per open sleeve **0.96 % →
5.08 %** (5.3×). The difference is the validation cache's own coverage:

| sleeve | rows in `load_book_rows()` | years covered | years the bars support |
|---|---:|---|---|
| `crypto` | 104 | **2024–2026** | 2017–2026 |
| `energy_agri` | 162 | 2021–2026 | 2021–2026 |
| `metals_core` | 131 | 2015–2026 | **2005–2026** |
| `sub_xvol_pullback` | 90 | 2016–2026 | **2006–2026** |

So a large share of the headline ramp is neither the edges nor the instruments: it is what
the cache happened to contain.

### (b) — fixed thresholds crossing more often: **a small term here**

For every threshold gate, where its fixed cut sits in each year's own distribution of the
statistic it cuts. If the cut were drifting relative to the data, this rank would slide.

| gate | cut | percentile rank, 2004 → 2026 |
|---|---|---|
| `metals_core` vol_expansion | vr ≥ 1.2 | 0.76 – 0.89, no trend |
| `metals_core` persistence | ac60 ≥ 0.10 | 0.75 – 0.93, no trend |
| `sub_xvol` vol_xhi | vr ≥ 1.6 | 0.95 – 0.995, mild recent softening |
| `sub_xvol` trend_up | slope50 > 1.5 | 0.36 – 0.72, no trend |
| `energy_agri` energy_state | vr ≥ 2.0 | 0.95 – 1.00 |

**These cuts are already scale-free in practice.** The one real marginal shift is
`sub_xvol`'s `vr ≥ 1.6` on the strict panel: 0.0194 → 0.0490, a 2.5× change concentrated in
the far tail where a small rank move is a large rate move. Everything else is flat.

### (c) — genuine structural change: one sleeve, one variable

Joint lift = observed fires ÷ fires the gates' own marginals would predict if independent.
On the strict panel, `sub_xvol_pullback`: marginals move ×3.3 in total, joint lift moves
**0.06 → 0.46 (×7.7)**. On a log scale that is ~37 % (b) and ~63 % (c). And the (c) half is
not a small-sample artefact: the conditional it rests on is **1/161 vs 15/119**.

---

## 3. The out-of-window economics, restated

`AB_OUT_OF_WINDOW_RESTATED_V1.json`. Regenerated from bars, priced by `src.costs.cost_r`
through `walkforward.panel.price_trades`, combined by **V's own `armed_set_mc.comb_from`**
with the half-Kelly bins and `DIAL`, so the arithmetic is the arithmetic V used. The cost
*layer* is not V's — the cached rows carry cost columns a regenerated stream does not — so
levels are not bit-comparable to V's table and **era-to-era ratios inside this table are**.

Each sleeve alone, over its own available era:

| sleeve | n | book-days | bd/month | R/book-day | %/month | net R/trade | gross R/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| `crypto` | 150 | 110 | 0.965 | +0.119 | **+0.230** | +0.295 | +0.460 |
| `sub_xvol_pullback` | 84 | 37 | 0.140 | +0.288 | **+0.081** | **+1.192** | +1.329 |
| `energy_agri` | 57 | 34 | 0.515 | −0.046 | −0.047 | +0.172 | +0.346 |
| `metals_core` | 385 | 188 | 0.709 | −0.160 | **−0.226** | −0.085 | +0.174 |

**The negative out-of-window number is one sleeve.** `crypto` and `sub_xvol_pullback` are
positive across their whole available history; `energy_agri` is positive per trade and
slightly negative per day (its two symbols fire together, so day-pooling charges the
correlation, which is the honest admission metric); `metals_core` carries the whole deficit.

`energy_agri`'s contribution to V's 2015–2019 cell is **exactly zero information** — the
instrument does not exist in the archive before 2021.

**Where these numbers differ from the brief's, it is the pipeline, not a contradiction.**
The brief cites `sub_xvol_pullback` at **+1.071 R/trade on n=88**; this measures **+1.192 on
n=84 priced** (94 fires, 10 of them inside the reserved March-2026 blackout and therefore
recorded rather than priced). Different generation runs, the same rule, the same cost
authority, and the same conclusion — the sleeve is the strongest per-trade earner in the
estate by a wide margin.

---

### 3a. The like-for-like cell — and it refines Session V's decomposition

Every table above compares books of different sizes. This one does not: the **same four
sleeves**, over the era in which all four had a tradeable instrument (`energy_agri` opens
last, **2021-02-17**), split at the selection boundary.

| window | trades | book-days | bd/month | density | R/book-day | %/month |
|---|---:|---:|---:|---:|---:|---:|
| **2021-02 → 2024 — outside the selection window** | 298 | 136 | **2.894** | 13.47 % | +0.0201 | **+0.117** |
| 2025+ — the selection window | 137 | 56 | **2.947** | 13.73 % | +0.3753 | +2.212 |
| 2021-02 → 2026 | 435 | 192 | 2.909 | 13.54 % | +0.1237 | +0.720 |

Two things follow, and the second is the important one.

**The four-sleeve book is positive outside the window that selected it** — +0.117 %/month
on 298 trades over 3.9 years. Small, and positive. That is a different fact from V's
−0.220 %/month, which is a two-sleeve book measured over an era in which two of the four
did not exist.

**And the frequency term is flat.** `SESSION_V` §7 attributes the selection-window multiple
to *both* terms — *"the edge per book-day is 5.3× higher and the firing frequency is 7.1×
higher"*. Held to one book over the era that book existed, **book-days/month move ×1.018
and the per-day edge moves ×18.6.** V's frequency term was the surface arriving, not the
market speeding up.

That sharpens the residual doubt rather than dissolving it: what is left to explain is the
**edge per book-day**, on 56 book-days of selection window against 136 outside it. It is a
smaller, cleaner question than the one the estate has been carrying, and it is the one
Session AI's composition work should be pointed at.

The three-sleeve config-runnable canary (`metals_core`, `crypto`, `energy_agri` — what
`include_clean3: false` actually permits) reads the same way: **+0.099 %/month** outside the
window, +1.351 %/month inside it, on 2.77 vs 2.58 book-days/month.

---

### 3b. The three live sleeves' gate states are two data gaps and a multiplicity bar, plainly

The brief asks for this said plainly, and it is worth saying because the orchestrator has
repeatedly reported this class of thing as if it were a verdict:

- **`crypto` NOT_EVALUABLE at 47.9 % cost coverage** is a missing DASHUSD tick file. It is
  not a statement about the rule. Measured here on the same broker-truth layer at the
  gate's `restrict_to_priced` policy, coverage is **80.65 %** — 36 DASHUSD trades unpriced,
  150 BTCUSD trades priced — and on the priced subset the sleeve is **+0.295 R net per
  trade** across 2017–2026.
- **`sub_xvol_pullback` at 93.9 %** was `EU50.cash` blocking its universe. Measured here on
  the 13 archive-available symbols, coverage is **100 %** and the sleeve is **+1.192 R net
  per trade**. Its rejection is on *significance* — a family-size bar at n=88 — and §5
  shows the neighborhood is uniformly positive and contains an n=420 variant.
- **`energy_agri`'s q 0.33** is a multiplicity bar on a positive edge, which §5.4 of the
  fourth review calls a **breadth** repair. Coverage here is **100 %**; +0.172 R net per
  trade. Its registry-vs-generator surface mismatch is re-confirmed through the production
  resolvers rather than cited: `walkforward.registry.live_registry()` returns
  `('USOIL_cash', 'UKOIL_cash', 'CORN_c', 'COTTON_c')` while `energy_agri.ON_SURFACE` is
  `('USOIL_cash', 'UKOIL_cash')` — CORN and COTTON are sized-for and can never fire.

None of the three is evidence against the book. Two are data and one is arithmetic about
the size of the family they were judged in.

**One drop class is deliberate and is not a gap:** 29 trades (5 `metals_core`, 14
`energy_agri`, 10 `sub_xvol_pullback`) fall inside the gate's `reserved_blackout`
(2026-03-01…2026-03-31) and are recorded, not priced. March 2026 stays outcome-unread; that
is W's sealed blackout doing its job.

---

## 4. `metals_core`: a cost-geometry prescription, and a measured frontier

The diagnosis is `FOURTH_REVIEW.md` §2.2's own row — *expectancy fails with gross > 0 →
cost-geometry repair* — and the cost split says which lever:

| term | R/trade |
|---|---:|
| gross | **+0.1738** |
| spread | 0.1258 |
| swap | 0.1218 |
| slippage | 0.0097 |
| commission | 0.0019 |
| **net** | **−0.0853** |

**That gross is not era-stable, and saying "+0.174 over 21 years" without this would be
misleading.** Split at the archive's own surface expansion: **≤2015 gross is −0.155 on
n=95** (XAUUSD + XAGUSD only), **>2015 it is +0.287 on n=295**. So the *gross-positive*
premise of the cost-geometry diagnosis holds firmly on the recent two-thirds of the record
and not on the early third. What survives that qualifier is the sweep result below, which is
measured on the **pre-2024 era including the weak early years** and is positive there
(+0.128 R/trade at stop ×3.0, n=297). The prescription rests on the sweep, not on the
21-year average.

Median stop is 1.11 × ATR, p10 0.58 × ATR. Cost in R is a price drag divided by the stop,
so widening the stop divides every term — while the R-geometry moves with the *path*,
because a wider stop is hit less often and a target at the same R multiple is further away
in price. Those run in opposite directions and only a re-simulation says which wins.

Swept over the archive (28 cells, target held at its R multiple so only stop *width* moves):

| stop × | n | gross | cost | **net** | R/day | median hold | pos% |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1.00 (production) | 390 | 0.179 | 0.222 | **−0.042** | −0.166 | 36 h | 29.7 % |
| 1.50 | 390 | 0.218 | 0.194 | **+0.024** | −0.151 | 80 h | 34.9 % |
| 2.00 | 390 | 0.196 | 0.185 | +0.011 | −0.088 | 144 h | 37.7 % |
| 2.50 | 390 | 0.249 | 0.175 | +0.075 | −0.061 | 234 h | 42.8 % |
| **3.00** | 390 | **0.262** | **0.164** | **+0.098** | **+0.023** | 320 h | 45.9 % |

Both terms move the right way: gross **rises** (a wider stop is hit less often) and cost
**falls**. Pre-2024 era at 3.0×: **+0.128 R/trade on n=297** (and 2024+ is only +0.003 on n=93 — the repair is measured out of the selection window, not in it).

**Three honest limits, and they are why this is a repair direction rather than a delivered
repair.**

- At 3.0× the **median hold is 320 h — the maxbars horizon.** The median trade is no longer
  a stop/target trade, it is a two-week hold. That is a joint stop **and exit** change, and
  the live sleeve's exit is `exit_state_d`'s scale-out, not a hard horizon.
- **`R/day` is negative at every scale except 3.0×.** Per-trade and per-day disagree because
  `metals_core` clusters. The admission-relevant metric is per-day (`panel.py`), so the
  frontier crosses zero only at the cell that also changes the sleeve's character most.
- A 320-hour median hold means positions occupy the **4 % gross open-risk cap** far longer,
  which the per-trade R does not price. That is a book-level cost, and Session AI's lane.

The `ac_thr` × `gate_k` neighborhood is **10 % positive** with production at rank 6/30 — so
the thresholds are *not* the lever, and that negative is worth as much as the positive.

**Prescription:** hand `metals_core` to the exit-repair lane (AD, §5.3) as a **joint
stop-width × exit-horizon** sweep, not a stop sweep. The frontier above is its starting grid.

---

## 5. `sub_xvol_pullback`: a plateau, and a breadth variant

`AB_NEIGHBORHOOD_V1.json`. The brief's question was whether the substrate cell's edge is a
spike (artefact) or a plateau (real).

| neighborhood | cells | net-positive | median | production | rank | median ÷ production |
|---|---:|---:|---:|---:|---:|---:|
| thresholds (vr × slope × ac band) | 125 | **100 %** | +0.973 | +1.149 | **49 / 125** | 0.85 |
| geometry (stop × target) | 25 | **100 %** | +1.069 | +1.149 | 9 / 25 | 0.93 |
| mtf sign threshold | 5 | 100 % | +1.114 | +1.149 | 2 / 5 | 0.97 |

**Every one of 155 adjacent cells is net-positive, and the production cell is in the middle
of the field rather than at its peak.** On the day-pooled metric the picture is identical
(100 % positive, rank 51/125).

**The cells are nested, and 155/155 is not 155 independent tests — measured, not assumed.**
Relaxing a cut adds trades and tightening removes them, so neighbours overlap heavily:
`vr_xhi 1.4` contains **100 %** of the production trades (Jaccard 39 %), `slope_up 1.0`
100 % (Jaccard 75 %), `ac_band 0.15` 100 % (Jaccard 62 %); the tightening directions
(`vr_xhi 1.8`, `ac_band 0.05`) are strict subsets. So the correct reading is *"the edge
survives every relaxation and every tightening tested"* — which is exactly the plateau
signature §5.1 asks for, because a spike collapses the moment you step off its cell — and
**not** 155 confirmations. It is also why the trial-budget deflation is the right instrument
for it: 261 measured, heavily-overlapping trials, recorded rather than assumed.

Read that way it still says the selection bought about 15 % of the level and none of the
sign.

**And the neighborhood contains a breadth repair for the significance failure.** The brief
names `q 0.264 at n = 88` as a sample-size problem. Relaxing the vol bucket to `vr ≥ 1.4`:

| variant | n | net R/trade | R/day | pre-2024 (n) | 2024+ (n) |
|---|---:|---:|---:|---|---|
| production (vr 1.6, slope 1.5, ac 0.10) | 94 | +1.149 | +0.837 | +0.578 (46) | +1.695 (48) |
| vr 1.4, slope 1.25, ac 0.15 | **420** | +0.325 | +0.352 | **+0.079 (230)** | +0.623 (190) |
| vr 1.4, slope 1.5, ac 0.15 | 368 | +0.326 | +0.360 | +0.108 (197) | +0.578 (171) |
| vr 1.4, slope 1.0, ac 0.10 | 309 | +0.427 | +0.378 | +0.225 (152) | +0.622 (157) |

**n = 88 → 420, positive in both eras, with 230 trades outside the selection window.** The
per-trade edge is ~3.5× smaller and the sample ~4.5× larger, which is the trade a
significance bar exists to make. It is a *different sleeve* and belongs in front of Borhen
as a variant with its trial cost attached, not as a silent widening.

`crypto`'s neighborhood is also a plateau: 20 cells, **85 % positive**, production rank
9/20, median +0.284 against production +0.305.

---

## 6. The normalization: mostly no repair, and that is the result

`AB_NORMALIZATION_V1.json`. Each flagged cut re-expressed as a **trailing percentile within
its own symbol**, leak-free (the current bar is excluded from its own reference window),
with `p` fitted on **pre-2024 bars only** to match production's own pre-2024 pass rate —
deliberately *not* fitted on returns, because a return-fitted percentile is the same defect
one level up.

| gate | n → n | pre-2024 net R/trade → | reading |
|---|---|---|---|
| `sub_xvol` vol_xhi | 94 → 94 | +0.578 → **+0.066** | **no repair** — the fixed cut is doing real work |
| `sub_xvol` trend_up | 94 → 61 | +0.578 → +0.890 | better but 35 % thinner |
| `metals_core` vol_expansion | 390 → 341 | −0.217 → −0.164 | better, still negative |
| `metals_core` persistence | 390 → 407 | −0.217 → −0.102 | better, still negative |
| `crypto` persistence | 150 → 148 | +0.226 → **+0.349** | see below |
| `energy_agri` vol_expansion | 71 → 52 | −0.279 → +0.740 on **n = 11** | not a measurement |

**The one place it does what it was supposed to is `crypto`.** Production fires
25/0/8/16/7/31/19 over 2017–2023; the percentile variant fires 5/14/19/17/24/22/10 — **2018
goes from zero fires to 14**, the fires-per-year CV drops 0.647 → 0.554, and the pre-2024
economics improve. A fixed `ac60 ≥ 0.15` on a persistence measure whose distribution moves
with the crypto vol regime produces whole silent years; the scale-free form fills them.

Everywhere else, **cause (b) is not the mechanism** — which is exactly what the stable
percentile ranks in §2 predicted. Three independent measurements agree, and the repair
failing is the evidence.

---

## 7. A live-generation defect, found by the fidelity check

`AB_PORT_PARITY_V1.json`. This package fires on **29 bars the live engine does not**, and
**29 of 29** sit immediately before a data gap of ≥ 2 intervals.

The mechanism, read off production: `bar_provider.candles_to_bars:54-58` does
`rows = candles[:-1]` **unconditionally**. At a session close there is no forming bar, so
the last candle **is** the freshly-closed decision bar and it is discarded; by the time the
next session's bar starts forming, that bar's close is more than two intervals old and
`book_engine.py:512` refuses it as stale. **The last closed bar before every weekend and
holiday is unreachable.**

| sleeve | fires | unreachable | % |
|---|---:|---:|---:|
| `sub_xvol_pullback` | 94 | 6 | **6.4 %** |
| `energy_agri` | 71 | 4 | 5.6 % |
| `metals_softband` | 246 | 9 | 3.7 % |
| `crypto` | 186 | 5 | 2.7 % |
| `metals_core` | 390 | 5 | 1.3 % |

The sleeve it costs most is the one whose gate failure is significance at n = 88.

**`[MEASURED]`** on the archive replay, which reproduces the convention exactly.
**`[UNVERIFIED]`** on the live MT5 feed — whether the terminal returns a forming candle at a
session close cannot be checked from this machine.

**Fix, written and tested** (8 tests, `tests/ultimate_book/test_bar_provider_pre_gap_bar.py`):
`candles_to_bars(..., now=..., interval_minutes=...)` keeps a last candle it can prove is
closed (`time + interval <= now`). Without both arguments the behaviour is byte-identical,
so every existing caller and test is unaffected — the first test asserts exactly that.

**It is not wired into `book_engine`, deliberately, and this is the one place I declined.**
Wiring it changes which bars an armed book trades on a funded account, and I cannot gate it
behind a config key because `config/agent_config.yaml` is bound to the live activation
token. The wiring is one line at the single call site:

```python
bar_cache[key] = get_closed_bars(self._mt5, broker_sym, spec.timeframe, primary_count,
                                 now=now, interval_minutes=_TF_MINUTES.get(spec.timeframe))
```

That is an owner decision with a measured price, not a session's.

---

## 8. The trial budget

`validation_integrity/trial_budget_ledger.py` is a **retrospective scanner**: it infers a
trial count from `*RESULT*.json` files that already exist. It cannot see a variant a live
session evaluates and never writes down — which is most of them. So this session added the
**write** half (`regime_spine/trials.py`) rather than editing that module, because Session
AA owns it this wave and two sessions editing one instrument is a failure this programme
has already paid for.

**261 trials logged**, one row per variant with the metric it could have been selected on:

| family | trials | | family | trials |
|---|---:|---|---|---:|
| `xvol_thresholds` | 125 | | `crypto_neighborhood` | 20 |
| `metals_thresholds` | 30 | | `normalization` | 18 |
| `metals_stop_geometry` | 28 | | `ramp_attribution` | 5 |
| `xvol_geometry` | 25 | | `xvol_mtf` | 5 |
| `restatement` | 4 | | `dials` | 1 |

The existing scanner reads the summary without modification:

```
recommended_n_trials_for_dsr: 261     (was: the assumed floor of 128,
                                       which gate.py:47-48 calls "a number nobody measured")
```

`test_regime_spine_trials.py` asserts the connection end to end — a logging mechanism no
deflation reads is decoration.

---

## 9. For Session AJ (command center) and Session AH (stores)

`AB_REGIME_DIALS_V1.json` — five named variables, each computable live from bars the book
already fetches, each with its **measured** distribution per year so "high" means something:

| dial | gates | reads as |
|---|---|---|
| **SURFACE_OPEN** | all | 0 means the sleeve cannot fire for want of bars, not for want of a setup. Check this first when the book is quiet — this session's central finding is that it explains most of the silence. |
| **VOL_REGIME** | 4 of 5 sleeves | ATR / SMA100(ATR). Below 1.2 most of the armed book structurally cannot fire. |
| **PERSISTENCE** | metals ×2, crypto | ac60. Negative = mean-reverting tape; the trend-continuation half stands down by design. |
| **HORIZON_CONFLICT** | sub_xvol_pullback | −1 = 20-bar and 100-bar trends disagree. **Conditional on the sleeve's own vol and trend gates this is the sleeve's regime.** |
| **TREND_STATE** | substrate sleeves | slope50 in ATR. |

Operator note carried in the artifact: *the armed four fire on 6.9 % of weekday sessions
across 2000–2026; 1.9 % in 2015 and 20.3 % in 2025, and the difference is mostly how many of
the four had a tradeable instrument at all.* A quiet book is the normal state.

`AB_FEATURE_SCHEMA_V1.json` + `AB_LABEL_STORE_V1.jsonl.gz` — 741 typed, leak-free rows, one
per generated trade, with decision-time features and the realized outcome in **separate
blocks** so a store built from them cannot train on its own answer. The full 176,552-row
per-bar feature series is regenerable in seconds and is written outside the repo
(`CLAUDE.md` §8: the tracked tree is already 97 % generated evidence).

---

## 10. What I got wrong, and withdrew

1. **I read HORIZON_CONFLICT as trending. It is episodic, and the per-year table refutes the
   first reading.** The aggregate numbers are right (0.62 % over 2015–2019, 12.6 % over
   2025+) but year by year the conditional runs 0.273 (2006), 0.321 (2008), 0.429 (2009),
   0.429 (2012), ~0.000 through most of 2014–2019 **and in 2024**, 0.205 (2020), 0.148
   (2025). 2015–2019 is a long quiet stretch of a recurrent regime, not the base of a ramp.
   The corrected reading is *better* for the book: a trend would make the sleeve's edge new
   and possibly transient; episodicity makes its 2013–2019 silence the regime being absent.
   Corrected in `dials.py` and in the artifact's `correction` field.

2. **My first archive index keyed on the broker symbol and silently lost 12 of 20 symbols.**
   The archive's filenames carry the *canonical* name (`USOIL_cash`), not the broker one
   (`USOIL.cash`); `BARS_MANIFEST.json` says so. It returned 8 frames instead of 20 — the
   whole index, energy and US30 surface — and would have produced a confident,
   wrong attribution. Caught by the working agreement's own rule: the probe said something
   surprising, so I suspected the probe. Fixed, and the reason is a comment in
   `archive.py:archive_index`.

3. **My first cost decomposition read all four terms as zero.** `PricedTrade.cost_r` is the
   scalar total, not a breakdown, so `getattr(b, "spread_r")` returned `None` and every term
   printed 0.0000 — with a plausible-looking "no cost repair required" verdict attached to
   `metals_core`. The fix asks the cost layer for the breakdown directly and **asserts the
   totals agree** with what `price_trades` charged, so the two can never silently diverge
   again.

4. **A test I wrote asserted an era split on a fixture too short to contain one** (1,400 H4
   bars ≈ 233 days, all inside 2015, so both eras returned 1,191). The assertion caught it;
   the fixture now starts mid-2014 and asserts it crosses a year boundary before testing
   anything.

**One thing in the brief I did not confirm.** It names the (b) case — fixed absolute
thresholds that recent volatility crosses more often — as *"the high-value case"*. Measured,
it is the **smallest** of the three for the armed four: every threshold's percentile rank is
stable across 22 years, and the scale-free re-expression delivers for one gate out of six.
That is not a criticism of the brief — it was the right hypothesis to test first, it was
cheap to test, and testing it is what makes the (a)-dominant conclusion credible.

---

## 11. What is next, and what this does not do

**Immediately actionable, all measured, none of them mine to decide:**

| # | item | owner |
|---|---|---|
| 1 | `metals_core` joint stop-width × exit-horizon sweep — the §4 frontier is the starting grid | AD (exit-repair lane) |
| 2 | `sub_xvol_pullback` at `vr ≥ 1.4` — n 88 → 420, positive both eras — as an owner packet with its trial cost | Borhen, via AI |
| 3 | Wire the pre-gap bar (§7), one line | Borhen |
| 4 | `crypto`'s percentile persistence gate — fills 2018 entirely | AF / AK |
| 5 | The five archive holes (`CORN_c`, `COTTON_c`, `FRA40_cash`, `EU50_cash`, `US2000_cash`) — `sub_xvol_pullback` runs on 13 of its 18 registered symbols | §9 tick/bar capture |

**What this does not do.** It does not re-run V's Monte Carlo on the regenerated stream —
the cost layers differ and reconciling them is a session in itself. It does not touch the
M15 sleeves or `idxrev`. It does not change what the live book trades: no config edited, no
wiring landed, `bar_provider`'s default byte-identical. And it does not settle OD-3.

**What it does do is shrink the question.** The objection to the armed four was that their
record outside the selection window was evidence against them. Most of that record was the
calendar: two of four sleeves had no instrument, `metals_core` had two symbols of six, and
the validation cache saw less than the bars do. Held to one book over the era that book
existed, it is **positive out of window** and its **firing frequency is flat** across the
boundary. What is left is a single, well-posed question — the **edge per book-day**, 18.6×
higher on 56 selection-window days than on 136 outside them — and that is a much better
thing to be uncertain about than the one the estate started with.

---

**Receipts.** `phase6/receipts/`: `AB_RAMP_ATTRIBUTION_V1.json`,
`AB_OUT_OF_WINDOW_RESTATED_V1.json`, `AB_NEIGHBORHOOD_V1.json`, `AB_NORMALIZATION_V1.json`,
`AB_REGIME_DIALS_V1.json`, `AB_FEATURE_SCHEMA_V1.json`, `AB_LABEL_STORE_V1.jsonl.gz`,
`AB_PORT_PARITY_V1.json`, `AB_TRIAL_LEDGER.jsonl` (261 rows),
`AB_TRIAL_BUDGET_SUMMARY.json`, `SESSION_AB_FULL_SUITE_AB.md`. Every driver is beside its
artifact and re-runs in under ten seconds against the bar archive.

**H1.** Checked at start and end: **0 drifted**, 2 unhydrated-LFS (the documented pointer
case, unchanged from base). No decision-contract-bound file was edited.

**A/B.** `7b0f4f276` → `136dcb9e8`, full suite, by failure set, both trees clean:
**665 bad → 665 bad, 0 regressed, 0 fixed, passing 10,883 → 10,925** — exactly the 42 new
test functions, so nothing was silently gained or lost elsewhere. Captures embedded in
`SESSION_AB_FULL_SUITE_AB.md`.

It took three capture cycles and the two extra ones earned their keep. The second flagged a
real regression that was mine (**B672**): writing B650–B671 raised the citation guard's
ceiling past Session AA's declared-but-unwritten `B600–B649`, so `B600` stopped being a
forward reference and became a dangling one in two documents I never touched. The guard's
own docstring names that failure mode for parallel waves and its `IN_FLIGHT_WAVE_RANGES` is
the designed remedy.

The third found something the first two had been hiding (**B673**):
`BROKER_TRUE_COSTS_V1.json` and `TICK_SPREAD_MEASUREMENT.json` were **regenerated inside this
worktree at 00:03:48 local, mid-capture**, adding measured spreads for previously-unpriceable
instruments including `EU50.cash` — priceability work, which is the spread-model lane's scope
and not this session's. No AB code path writes there (`load_broker_true_costs` is a pure
cached reader, `src/costs/model.py:144-145`); `git add -A` swept them into a follow-up commit.
It surfaced as `test_unpriceable_symbol_is_recorded_not_assumed_zero` failing at HEAD and
passing at base — the test asserts EU50.cash prices 0 of 40 and the rewritten layer priced 40
of 40. Both files are reverted to base bytes and `git diff <base> -- research/` is empty.

**No number in this report is affected.** Every receipt was written by 23:50:20, thirteen
minutes before the rewrite, so every cost-bearing figure used the base broker-truth layer the
branch now carries. The generalisable lesson, which cost two capture cycles: **stage by path,
not `git add -A`, when other sessions are live on the machine.**
