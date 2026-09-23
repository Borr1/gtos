# LANE 8 — WHERE THE LIVE EDGE COMES FROM, AND HOW TO SCALE IT

**Wave 21 swarm 2, 2026-08-11.** Receipts: `swarm2/lane8_receipts/`.

**Measurement only.** No broker call, no VPS touch, no config byte, no `src/` byte, no git write.
Everything below is a re-walk of the three armed generators' own signal functions over the same bar
archive `AQ_ESTATE_TRADES_V2` used (`/Users/borr/GTOSActive/vps-bars-20260727`), labelled through the
sanctioned path replay `src/research_infra/walkforward/exits.py:292` under the published contract, and
priced by the only cost authority (`src/costs/cost_r`). Confers no arming, sizing or activation
authority.

---

## 0. HEADLINE

> **The one thing in this estate that should be scaled is the `crypto` sleeve, and the way to scale
> it is one symbol: `ETHUSD`.**
>
> The crypto rule is *Donchian-20 H4 breakout gated on 60-bar return autocorrelation ≥ 0.15*. Run on
> the two symbols it is armed on today (BTCUSD + DASHUSD) it earns **+0.5422 R/trade gross on n = 186**
> — but at broker-true cost, on the day-block bootstrap, and **outside the `d.year >= 2025` window
> that selected the book, that cell does not exclude zero (net +0.2268 R/trade, CI95
> [−0.1614, +0.6200], p(≤0) = 0.130)**, and 19 % of it (all 36 DASHUSD trades) is `NOT_EVALUABLE`
> under the ratified cost standard.
>
> Add ETHUSD and the same rule, unchanged, becomes:
> **n = 331, net +0.4482 R/trade at 100 % cost coverage, day-block CI95 [+0.1674, +0.7309],
> p(≤0) = 0.00070 — and out of the selection window, n = 248, net +0.4270, CI95 [+0.1192, +0.7363],
> p(≤0) = 0.00270.** Nine of ten calendar years positive (the tenth is one trade). Both directions
> positive (LONG +0.772, SHORT +0.328), so it is not secular crypto drift; the measured placebo null
> for that cell is **+0.1615** and the rule beats the null's 97.5th percentile.
>
> **At the book level, under the live one-unit-per-cluster-per-day cap, adding ETHUSD raises the
> three-sleeve book's frequency by 27.1 % (2.358 → 2.997 signal days/month) AND its R per book-day by
> 7.7 % (+0.6499 → +0.6998), for +36.9 % total R/month (+1.532 → +2.097 gross R/month).** It is the
> only change measured in this lane that moves both terms in the same direction.
>
> **ETHUSD was excluded by a data defect, not an economic finding**, and the defect no longer exists.
> `crypto.py:9-12` says so in its own words: *"ETHUSD H4 via w1.load is broken (only 134 bars from
> 2026-05) … ETH was therefore excluded"*, and the same docstring names adding it as the documented
> next step. The archive now carries **18,442 ETHUSD H4 bars from 2017-02-20** — one month shy of
> BTCUSD's own start. ETHUSD is declared in **both** live profiles
> (`config/profiles/operator_profile.yaml`, `config/profiles/redacted_account.yaml`), where DASHUSD is
> FTMO-only and is `BROKER_DOES_NOT_LIST_IT` on redacted_account — so this is also the only measured way to
> give redacted_account a crypto sleeve wider than one symbol.

Five further results, each measured here:

1. **The sleeve edge is real but it is three different objects, not one.** `crypto` is positive in
   9 of 9 archive years with a day-block CI excluding zero; `sub_xvol_pullback` has a large edge on
   **39 entry days in 20 years**, 71 % of them in 2020 + 2025–26; `energy_agri`'s day-block CI95
   **includes zero** ([−0.0576, +1.7453]) and it is 4.8× better in the selection window than out of it.
2. **`energy_agri`'s live exit contract costs it −0.2883 R/trade**, paired on identical entries,
   CI95 [−0.5207, −0.0414], t = −2.385, n = 72. Independent third confirmation of AD §6.2 and AU.
   Deleting `partial_be_runner` and running the plain 4R is the second-best change available and it
   is free.
3. **Scaling by adding symbols works only inside the sleeve's own asset family.** Both rules are
   family-specific to a decisive degree: the crypto rule on the 32 non-crypto archive symbols earns
   **−0.0115 R/trade on n = 8,588** (null +0.0093); the energy FVG rule off energy earns **+0.0470 on
   n = 2,337** against a null of +0.0201 and fails its own null band. `sub_xvol_pullback` off its
   declared surface is **−0.1015 on n = 280**.
4. **More symbols is not automatically better under the cluster cap — it can be worse.** The 9-symbol
   crypto family produces 3.248 signal days/month against BTC+DASH+ETH's 1.905, but **less** capped
   gross R/month (+0.991 vs +1.119), because four of the nine (ADAUSD, DOTUSD, LTCUSD, XRPUSD) are
   jointly **−0.3128 R/trade on n = 164, CI95 [−0.587, −0.009]** and consume cap slots.
5. **The unarmed set has one candidate that deserves a fresh look and it is `vol_compression`:**
   n = 391, corrected R +0.3301, t = 3.48, target rate 0.325 against a driftless null of 0.250,
   **pre-2025 +0.2975 (n = 290) and 2025+ +0.4237 (n = 101)** — the only unarmed sleeve in the estate
   that is materially positive on *both* sides of the selection window. Its multiplicity bill and the
   reasons to be careful are in §6.

---

## 1. (A) MECHANICAL DOSSIERS — what the three armed sleeves actually trade

All three decide on the **latest CLOSED H4 bar**, emit a `TradeIntent` or `None`, and are pure
(`src/components/ultimate_book/primitives.py` only — stdlib, no broker, no IO). None of them looks at
any learned model, any ranking, or any other candidate. The engine calls each once per symbol per H4
close (`book_engine._generate_intents`).

### 1.1 `crypto` — *"the trend has memory, and price just left the box"*

| | |
|---|---|
| file | `src/components/ultimate_book/sleeves/crypto.py:31-66` |
| what it detects | a **20-bar Donchian channel breakout that happens while the market has positive short-horizon momentum memory** |
| entry trigger | on closed H4 bar `i`: `close > max(high[i-20:i])` → LONG (`:42-43`); `close < min(low[i-20:i])` → SHORT (`:44-45`); then the gate `autocorr(bars, i, 60) >= 0.15` (`:48-50`), else no trade |
| the gate, in plain terms | the lag-1 autocorrelation of the last 60 H4 returns. Above 0.15 means "recent moves have been followed by moves in the same direction" — a **persistence/trend-regime filter**. It is the whole difference between this sleeve and a naive Donchian breakout, and §4 shows a naive Donchian breakout does not pay |
| timeframe | H4. Warm-up 60 bars (`:36`) |
| stop | `2.0 × ATR14` (`:27`, `:51`) — a pure volatility stop, no structure |
| target | `4.0 × stop` (`:28`, `:66`) — 4R |
| exit policy | `time_stop`, broker TP at 4R, `time_stop_bars = 1280` M15 bars = 80 H4 bars = 320 h (`execution_packets.py:80`) |
| session gate | **none** — crypto is 24/7 and the generator says so (`:57`) |
| symbols | `("BTCUSD", "DASHUSD")` (`:24`). DASHUSD is FTMO-only |
| firing frequency | **1.213 signal days/month** measured over 2017-02 … 2026-07 (186 trades on 135 days) |
| realised shape | 60.8 % stop / 18.8 % target / 20.4 % maxbars; median hold **70–72 h** |

**The market phenomenon**: momentum continuation in a trending crypto regime. The autocorrelation
gate is a regime detector, not a signal — it says *don't take breakouts in a chop regime*.

### 1.2 `energy_agri` — *"oil gapped, came back to fill it, and the gap held"*

| | |
|---|---|
| file | `src/components/ultimate_book/sleeves/energy_agri.py:47-63`, entry shared from `metals.fvg_signal` (`metals.py:63-90`) |
| what it detects | a **fair-value-gap retest**: a 3-bar imbalance (an unfilled gap between bar `k-2`'s high and bar `k`'s low) that price returns into and rejects, taken in the direction of the H4 trend |
| entry trigger | volatility-expansion gate first — `atr14(i) >= 1.2 × SMA100(atr14)` (`metals.py:73-75`); then `htf_trend(i, 30)` must be ±1 (close vs close 30 bars ago beyond 1 ATR, `metals.py:52-61`); then scan back 2–8 bars for a gap ≥ `0.10 × ATR`, and require the current bar to **wick into it and close back out** on the right side with a body in the trade's direction (`metals.py:78-90`) |
| the state gate | `energy_gate(vr, slope)` = `vr >= 2.0` **OR** `abs(slope30) < 0.05` (`energy_agri.py:42-44`), where `vr` is ATR14 over its own 100-bar mean and `slope30` is the linear-regression slope of the last 30 closes divided by ATR (`:24-39`). In plain terms: **take it either in a supply-shock volatility ignition, or in a flat, early-continuation tape** — and nothing in between. Its docstring records that the `ac60` persistence gate that powers `metals` *"does NOT help energy"* |
| timeframe | H4. Warm-up 100 bars |
| stop | **structural**, not ATR: `(close − min(low, gap_bottom)) + 0.10 × ATR`, floored (`metals.py:86`). This is the one armed sleeve whose stop is not an ATR multiple — measured stop-to-ATR CV 0.49 |
| target | `4.0 × stop` (`energy_agri.py:63`) |
| exit policy | **`partial_be_runner`**: 50 % off at +2.0 R, stop to breakeven on the remainder, 4R final, `time_stop_bars = 1280` (`execution_packets.py:93-94`). §7 measures what this costs |
| symbols | `("USOIL_cash", "UKOIL_cash")` (`:20`). The agri legs (CORN_c, COTTON_c) and the dropped energy legs (HEATOIL_c, NATGAS_cash) are off-surface — the docstring records CORN/COTTON were over a "0.20 R untradeable wall" on spread |
| firing frequency | **0.653 signal days/month** (72 trades on 40 days, 2021-02 … 2026-07) |
| realised shape | 58.3 % stop / 34.7 % target / 6.9 % maxbars; median hold **62 h** |

**The market phenomenon**: imbalance-fill continuation in crude. The gap is where price moved too fast
for two-sided trade; the retest is the market re-auctioning that level; the trade is that the
imbalance holds.

### 1.3 `sub_xvol_pullback` — *"a four-condition volatility-shock cell, always long"*

| | |
|---|---|
| file | `src/components/ultimate_book/sleeves/substrate.py:114-155`, state machine `substrate_engine.py` |
| what it detects | a **mined conjunctive state cell**, not a chart pattern. It fires when four independent state buckets line up on the same closed H4 bar |
| the cell | `g1.0_3.0\|dir=1\|depth4\|vol=xhi\|persist=rand\|trend=up\|mtf=conflict` (`substrate.py:69`) |
| condition 1 | `vol = xhi` → `vr >= 1.6`, i.e. ATR14 at ≥ 1.6× its own 100-bar mean — **a volatility shock** (`substrate_engine._bucket_vr`) |
| condition 2 | `trend = up` → `slope50 > 1.5` ATR/bar — a **strong up-trend** on the 50-bar regression |
| condition 3 | `mtf = conflict` → `mtf_align = -1`: the multi-timeframe slopes **disagree** — i.e. a pullback against an up-trend |
| condition 4 | `persist = rand` → `-0.10 < ac60 < 0.10` — **no momentum memory**, the opposite of `crypto`'s gate |
| in plain terms | *buy a pullback inside a strong uptrend, but only during a volatility shock, and only when the tape has no directional persistence* |
| direction | **FIXED +1 — long only** (`:71`, `:145`). It never shorts |
| timeframe | H4. Warm-up **210 bars** (`substrate_engine.WARMUP`), fail-closed below it |
| stop | `1.0 × ATR14` (`:70`) |
| target | `3.0 × stop` = 3R (`:70`) |
| exit policy | `time_stop`, broker TP 3R, `time_stop_bars = 1280` (`execution_packets.py:84`) |
| session gate | **none** — depth-4 cell, ignores `bar_time` (`:152`). Its sibling `sub_mid_dn_revert` is depth-7 and needs the server hour |
| symbols | 18 after the dropped-energy filter (`:62`): the six metals crosses, the two oils, CORN/COTTON, and eight indices. 13 of those exist in the H4 archive |
| firing frequency | **0.164 signal days/month** — 94 trades on **39 distinct days in 20 years** |
| realised shape | 53.2 % target / 42.0 % stop / 4.5 % maxbars; median hold **112 h** |

**The market phenomenon**: a volatility-shock dip-buy. It is the estate's highest per-trade edge and
its rarest signal, and §5.3 shows both facts have the same cause.

---

## 2. (B) WHAT IS STRUCTURALLY DIFFERENT — sleeve stack vs funnel stack

The two stacks are not variants of one design. Every axis differs, and the differences are not
cosmetic. (Funnel column sourced from `broader_origin_generators.py`,
`v4_timewarp_simulated_live_research_loop.py`, `w21_score_*.py`, and the wave-21 sealed results.)

| axis | ARMED SLEEVE STACK | RESEARCH FUNNEL STACK |
|---|---|---|
| **generation** | 3 fixed mechanical rules × 22 symbol slots, evaluated on H4 closes. **~1–3 candidates per WEEK** | ~10 families × 24 symbols × ~96 M15 windows = **≈ 6,000 candidate occurrences per DAY** (`FEBRUARY_…_R2.json → population`: 121,302 in 20 days) |
| **selection** | **none.** Every intent that fires is sized and sent (subject to cluster cap + governor). The rule *is* the selection | a **prequential ridge** (`alpha=10`, 43 features) ranks the window's ~40 resolved candidates and takes the top one if predicted net R ≥ 0.10; abstains if the top is LIMIT |
| **feature basis** | 4–6 hand-specified state variables per sleeve, all price-derived, all thresholded | 14 categorical + 29 numeric features, OneHot + StandardScaler, learned weights, **no calibration** |
| **order type** | MARKET only. All 296 captured live orders are `TRADE_ACTION_DEAL` | MARKET for 7 families, LIMIT for 3; LIMIT fills **modelled**, never broker-true |
| **stop geometry** | ATR-multiple (crypto 2.0×, xvol 1.0×) or **structural** (energy: gap depth + 0.10 ATR) | ATR buffer off the trigger bar (0.25–1.0 ATR) |
| **target geometry** | **4R / 4R / 3R**, per-sleeve, chosen | **2.0R on 81,968/81,968 sealed rows**, and the declared table is `UNCHOSEN` on every family — it is `risk.min_rr`, a "sanity floor", overwritten to 2.0 by the momentum-exhaustion policy |
| **timeframe** | H4 decision grid | M15 decision grid |
| **holding period** | **median 62–112 h; horizon 320 h** | **hard 120-minute expiry**; p25 = p50 = p75 = 120 min for time-stopped trades |
| **exit management** | per-sleeve contract: time-stop / partial-BE-runner / trailing runner, broker SL+TP set at entry | barrier + hard time stop only in the scored path; the replay's `partial_be_runner=True` is **not** what the scorer prices |
| **cost treatment** | 4 terms via `src/costs/cost_r`, per-symbol broker-true, **fails closed** when a term is unmeasured | spread charged geometrically inside the M1 walk; **slippage a flat 0.02 R constant on all 24 symbols**; swap at maximum horizon |
| **sizing** | Kelly-lite half-Kelly conviction bins, per-sleeve confidence weight (0.45–0.85), governor, cluster cap | **flat 1R**, no allocator, no exposure budget — 69 % of July's book was one symbol×family |
| **multiplicity** | ratified `CANDIDATE_BOOK_V1` family, sealed α = 0.10, 59 declared members | 12 prereg versions, 3 policies × 3 bars, **BAR-3 written after two reads**, family scoped to LSR after four months |

### 2.1 Which difference plausibly explains positive vs zero — ranked

**Rank 1 — HOLDING PERIOD, and it is not close.** The funnel's contract is 2 hours; the sleeve
contract is 320. Lane I measured the cost drag directly: at H4/4 h it is **12.28 % of one forward
standard deviation**; at H4/120 h it is **2.12 %**. A 2-hour barrier system must find an edge six
times larger, per unit of risk taken, to clear the same friction. Independently, the funnel's own
realised cost is 0.047–0.049 R against family deficits of 0.10–0.57 R — so cost is not *all* of it —
but the funnel's gross is also ≈ 0, which brings us to rank 2.
**How to test**: run the funnel's own ten families at the sleeve contract (H4 grid, 80-bar horizon,
3–4R target) on the same symbols. Lane I's blind-entry ladder says the *unconditional* answer is
still negative; the open question is whether any family's conditional gross survives the re-contract.
**Cost**: one walk, no new data.

**Rank 2 — SELECTION vs SPECIFICATION.** The funnel's rule is *"generate everything, then learn which
one"*; the sleeve's rule is *"specify one thing precisely, then take every instance"*. The funnel's
own measurement says the learned layer contributes nothing out of sample (`gbm_oos` capture
−0.033…+0.002; `ridge_oos_frozen` within-window lift +0.00298 R/trade, se 0.00488, positive in 2 of 5
months — beaten by *"pick the cheapest candidate"* at +0.00650). **This lane's §4 shows the sleeve
stack's specificity is exactly what carries its edge**: relax `sub_xvol_pullback`'s four-condition
conjunction by one clause and the per-trade excess over null falls from **+1.0188 to +0.0445 …
+0.2787**, monotonically in every direction tested.
**How to test**: already tested here — see §5.3. The generalisation is that a conjunctive
specification is a *cost filter*, and a ranked pool has no cost filter at all.

**Rank 3 — ASSET-FAMILY SPECIFICITY.** Each sleeve rule is tuned to a market whose behaviour it
matches, and §4 shows every one of them collapses to zero off its own family. The funnel runs ten
generic families across all 24 symbols with no family×symbol restriction, so it is structurally
averaging over exactly the surfaces where each rule does not work.
**How to test**: fit the funnel's per-(family × symbol) cells and check whether the surviving cells
are family-coherent. Partly done and negative — 366 conditioned cells, 1 survivor against ≈11
expected by chance — but that scan was at the 2-hour contract; redo at rank 1's contract.

**Rank 4 — TARGET GEOMETRY WAS CHOSEN vs INHERITED.** The sleeves carry 3R and 4R targets that were
selected per sleeve; the funnel carries 2.0R that nobody chose (`FAMILY_TARGET_RR` is `UNCHOSEN` on
every row). §7 measures that this matters: on `energy_agri`, 2R earns **−0.4272 R/trade** against its
own 4R (CI95 [−0.755, −0.062]), and 3R **−0.2214**. If the funnel's families have the same convexity,
its published economics understate them by a comparable amount.
**How to test**: re-label the sealed funnel rows at 3R/4R/6R with the same 80-bar horizon. Cheap —
the M1 lifecycle walker already exists.

**Rank 5 — SIZING AND EXPOSURE.** Half-Kelly with per-sleeve confidence and a one-unit-per-cluster
cap, against flat 1R with no exposure budget and measured 8 re-entries/day on one cell. This changes
the *book* result, not the per-trade edge, so it cannot turn a zero into a positive — but it is why a
+0.33 R/book-day sleeve book and a −0.02 R/trade funnel are not directly comparable.
**How to test**: not needed; it is arithmetic.

**Rank 6 — ORDER TYPE / FILL REALISM.** The sleeve stack is MARKET-only and has 296 broker-true
captured orders; the funnel's LIMIT families are modelled. G3's XAUUSD × `current_fvg_fill` cell died
precisely here (a magnet artifact worth ≈ 0.179 R/trade, larger than the +0.15 it claimed). Low rank
because the funnel's MARKET-only top-choice policy also measures zero.

**Ranked NOT plausible**: cost model differences (the funnel's flat 0.02 R slippage is generous, not
punitive — repairing it makes the funnel worse); and the debate/probability layer, which is banned
from the scored path by the frozen rule and so cannot be the cause of anything.

---

## 3. (C) IS THE EDGE REAL, AND WHERE DOES IT COME FROM

### 3.0 The null, computed rather than assumed

A barrier system with a 1R stop and a kR target has, under a driftless price process,
**E[R] = 0 exactly** — optional stopping on a bounded stopping time — and P(target) = 1/(1+k). So the
"geometry fair value" of an asymmetric R:R is **zero before costs and negative after them**; there is
no free expectancy in the shape.

Real price series are not driftless, so the honest null is measured. `placebo_null`
(`lane8_receipts/lane8_expansion.py`) draws entry bars uniformly from the **same (symbol, year) cells
the sleeve's own entries occupy**, with the same direction mix and the same ATR-scaled stop
distribution, and replays them through the same labeller. That null carries the data's real drift,
fat tails and volatility clustering. Anything above it is the rule.

| sleeve, live surface | n | analytic driftless E[R] | **measured placebo null** | sleeve gross R | **excess** | beats null p97.5 |
|---|---:|---:|---:|---:|---:|---|
| `crypto` (BTC+DASH) | 186 | 0.0000 | **+0.0906** | +0.5422 | **+0.4516** | **yes** |
| `energy_agri` (2 oils) | 72 | 0.0000 | **+0.0350** | +0.8640 | **+0.8289** | **yes** |
| `sub_xvol_pullback` (13 sym) | 94 | 0.0000 | **+0.2326** | +1.2514 | **+1.0188** | **yes** |

The nulls are positive and non-trivially so — **+0.0906 R/trade of `crypto`'s gross is what a random
entry with the same geometry on the same symbols in the same years would have earned.** That is 16.7 %
of the sleeve's gross, and it is the secular-drift component. For `sub_xvol_pullback` it is 18.6 %.
For `energy_agri`, 4.1 %.

Target-rate corroboration on the same axis: `sub_xvol_pullback` hits its 3R target on **53.2 %** of
trades against a driftless 25.0 %; `energy_agri` hits 4R on **32.8 %** against 20.0 %; `crypto` hits
4R on **20.4 %** against 20.0 % — and earns its edge from the **maxbars tail instead** (20.4 % of
trades exit at the 80-bar ceiling at a mean of **+1.42 R**, contributing +0.2902 of its +0.4339
corrected R). That is a materially different edge shape and it is worth knowing: `crypto` is a
**runner** whose published 4R target is not where the money is.

### 3.1 The decomposition of the live book's +0.3298 R/book-day

`THREE_SLEEVE_BOOK_RESTATEMENT_V1.md` §3.2: FTMO, three sleeves, `CURRENT_SURFACE`, **196 trades over
69 book-days, +0.3298 R/book-day, sd 1.1785, CI95 [+0.0517, +0.6079], t = 2.325.** That is the number
to decompose. Components below are measured on the archive population and transferred to the
book-day unit by the frequency ratio; each carries its own basis, and they are **not** additive to
five decimal places — they are a magnitude attribution.

| component | magnitude | interval | basis |
|---|---:|---|---|
| **A. Geometry / fair value of the barrier** | **0.0000 R/trade** | exact | optional stopping; a 1R:kR barrier is a martingale stop |
| **B. Drift the geometry harvests for free** (placebo null, R/trade, trade-weighted over the armed three) | **+0.114** | crypto [−0.190, +0.375]; xvol [—]; energy [—] | measured, `LANE8_EXPANSION_V1.json → arms[*].null` |
| **C. Rule excess over B, gross** | **+0.452 / +0.829 / +1.019** per sleeve | all three exceed the null's 97.5th pct | same |
| **D. Cost** | **−0.157** (crypto, 100 % coverage); **−0.055 + unmeasured slippage** (energy); **−0.13 to −0.5** (xvol, 28 % coverage) | — | `src/costs/cost_r`; §3.3 |
| **E. Selection-window survivorship** | **÷1.84 on R per book-day, ÷7.83 on frequency** | — | `W7_INSTRUMENT_RESTATEMENT_V1.md` §4, reproduced independently here in the pre/post splits below |
| **F. Sizing / compounding** | **0 in R units**; it scales the %/month conversion only | — | the +0.3298 is already per-R |
| **G. Luck** | t = 2.325 on 69 book-days; joint 95 % band on the monthly rate **[−0.005, +4.236]** — lower edge zero | — | `THREE_SLEEVE_BOOK_RESTATEMENT_V1.md` §3.2 |

**E is the component this lane can sharpen, and it splits the three sleeves apart.** Same walk, same
labeller, split on the `d.year >= 2025` predicate that `build_survivor_book.py:74` and
`KB7_growth_kelly_sizing.py:130` share:

| sleeve | pre-2025 n | pre-2025 gross R | 2025+ n | 2025+ gross R | in/out ratio |
|---|---:|---:|---:|---:|---:|
| **`crypto` (BTC+DASH)** | 126 | **+0.4099** | 60 | +0.8199 | **2.00×** |
| **`crypto` (BTC+DASH+ETH)** | **248** | **+0.6023** | 83 | +0.7338 | **1.22×** |
| `energy_agri` | 32 | **+0.2782** | 40 | +1.3326 | **4.79×** |
| `sub_xvol_pullback` | 47 | **+0.6942** | 47 | +1.8085 | **2.61×** |

**`crypto` with ETHUSD added is the only cell in the armed estate whose in-window inflation is under
1.25×.** Everything else — including both of the other armed sleeves — is 2.6× to 4.8× better inside
the window that chose it.

### 3.2 Robustness of each sleeve, adversarially

Day-block bootstrap over **(symbol, entry-day)** blocks — the clustering unit — 8,000–20,000
resamples, on the sleeve's own live surface, GROSS:

| sleeve | span | n | blocks | mean R | day-block CI95 | p(mean ≤ 0) | years positive |
|---|---|---:|---:|---:|---|---:|---|
| **`crypto`** | 2017-02 … 2026-07 | 186 | 136 | +0.5422 | **[+0.194, +0.903]** | **0.00065** | **9 / 9** |
| `energy_agri` | 2021-02 … 2026-07 | 72 | 40 | +0.8640 | **[−0.058, +1.745]** | 0.0338 | 4 / 6 |
| `sub_xvol_pullback` | 2006-05 … 2026-07 | 94 | 39 | +1.2514 | **[+0.551, +1.859]** | 0.0000 | **7 / 14** |

**`energy_agri`'s interval includes zero.** `sub_xvol_pullback` excludes zero decisively but is
positive in only half its years and lives on 39 days in twenty years, 67 of its 94 trades falling in
2020, 2025 and 2026. `crypto` is the only one of the three positive in every year of its record —
including 2022, the crypto bear market, at +0.077 on n = 54 (BTC+ETH basis).

### 3.3 Cost coverage — a live-money finding

`src/costs/cost_r` fails closed on an unmeasured term rather than back-filling. Charging it per trade
on each sleeve's own walked population:

| sleeve, live surface | n walked | **priced** | coverage | gross | cost | net | blocker |
|---|---:|---:|---:|---:|---:|---:|---|
| `crypto` (BTC+DASH) | 186 | 150 | **0.81** | +0.4600 | 0.1518 | +0.3083 | `DASHUSD`: no reconciled price-domain slippage sample |
| **`crypto` (BTC+DASH+ETH)** | 331 | **295** | **0.89** (100 % of the evaluable pair) | +0.6049 | 0.1568 | **+0.4482** | same, DASHUSD only |
| **`energy_agri`** | 72 | **0** | **0.00** | +0.8640 | — | — | **`USOIL_cash` AND `UKOIL_cash`: no reconciled price-domain slippage sample** |
| `sub_xvol_pullback` | 94 | 26 | **0.28** | +1.1538 (priced subset) | 0.1305 | +1.0233 | all six metals crosses + both oils unpriceable |

**Three findings the owner should have:**

1. **`energy_agri` — armed and trading real money on both accounts — has ZERO cost-priceable
   evidence on FTMO.** The prior lane recorded 0.0 % priceability on redacted_account; it is 0.0 % on FTMO
   too. Its published economics are gross-only under the ratified authority.
2. **`sub_xvol_pullback`'s 28 % coverage is adversely selected.** The 26 priceable trades are
   JP225.cash (+2.43), US30.cash (+3.00), US500.cash (+3.00), XAUUSD (+0.54), GER40.cash (−1.00) —
   the index legs, whose holds are shorter. The 68 unpriced trades sit on XAGUSD (120 h median),
   UKOIL.cash (166 h), USOIL.cash (262 h), XAGAUD (136 h) — precisely the long-carry rows where cost
   is largest. **The +1.0233 net is an optimistic bound, not an estimate.** For scale: XAUUSD at a
   1×ATR stop and a 100 h hold costs **0.519 R**, of which 0.463 is swap.
3. **The single repair that unlocks all three is the CS slippage capture** already on the
   `CLAUDE.md` next-queue. Six symbols would move `crypto` to 100 %, `energy_agri` from 0 % to 100 %,
   and `sub_xvol_pullback` from 28 % toward 100 %.

### 3.4 Verdict on (C)

**The edge is real, it is not geometry, and it is not one thing.**
- Not geometry: the barrier's fair value is exactly zero and the measured placebo null accounts for
  4–19 % of each sleeve's gross.
- Not sizing: the +0.3298 is already in R.
- Partly survivorship: 1.22× to 4.79× in-window inflation depending on the sleeve.
- **`crypto` is the component that survives every control**: 9/9 years, both directions positive,
  day-block p 0.00065, in-window inflation 1.22× once ETH is included, 100 % cost coverage on the
  evaluable pair.
- **`sub_xvol_pullback` is real but is a regime instrument**, not a steady earner; §8 gives the
  owner recommendation.
- **`energy_agri` is the weakest of the three on evidence** — CI includes zero, 4.8× in-window
  inflation, zero cost coverage — and simultaneously carries the largest *free* improvement
  available anywhere in the book (§7).

---

## 4. (D) CAN IT BE SCALED — the lane's centre of gravity

### 4.1 Why the book fires ~4 days a month: it is the generator's rate, not a throttle

Measured signal days per month on the archive, each rule on its own live surface:

| sleeve | trades | signal days | **days/month** | share of book clock |
|---|---:|---:|---:|---|
| `crypto` | 186 | 135 | **1.213** | the clock |
| `energy_agri` | 72 | 40 | **0.653** | the clock |
| `sub_xvol_pullback` | 94 | 39 | **0.164** | ~7 % |

The three together, under the live one-unit-per-cluster-per-day cap, over the window where all three
surfaces exist (2021-02 … 2026-07, 5.48 y): **2.358 book-days/month, +0.6499 gross R/book-day,
+1.532 gross R/month.** That is close to the 3.833/month the W7 cache gives for FTMO's current
surface and confirms the order of magnitude on an independent population.

**It is the generators' natural rate.** The throttles that exist — the cluster cap and `--tags` — cost
frequency but the cap only binds on 32.86 % of `(cluster, day)` buckets and 95.6 % of what it blocks
is a repeat of a symbol already on. The binding constraint is upstream: **`crypto` scans 2 symbols;
`energy_agri` scans 2; `sub_xvol_pullback` needs four independent state conditions to coincide.**

### 4.2 `crypto` — expansion works, and one symbol does most of it

Same rule, byte-identical, symbol set varied. GROSS, whole archive:

| arm | symbols | n | gross R | placebo null | **excess** | beats null p97.5 | days/mo |
|---|---:|---:|---:|---:|---:|---|---:|
| **A0 LIVE** | 2 (BTC, DASH) | 186 | +0.5422 | +0.0906 | +0.4516 | yes | 1.213 |
| **A1 +ETH** | 3 | **331** | **+0.6353** | +0.1531 | **+0.4822** | yes | **1.905** |
| A2 family-9 | 9 | 704 | +0.3556 | +0.0755 | +0.2801 | yes | 3.248 |
| **A3 all archive** | 41 | 9,292 | **+0.0163** | +0.0184 | **−0.0021** | **no** | 9.813 |
| **A4 non-crypto only** | 32 | 8,588 | **−0.0115** | +0.0093 | **−0.0208** | **no** | 9.226 |

**A3/A4 are the decisive negative and they are what makes A1 credible.** The Donchian-20 + ac60 rule
has *no edge whatsoever* outside crypto: on 8,588 trades across 32 non-crypto symbols it earns
−0.0115 R/trade against a null of +0.0093. This is the same verdict MAGNITUDE §2's 576-cell breakout
scan reached for generic Donchian, reproduced here — and it locates where the exception is.

Per symbol, whole archive, gross:

| symbol | archive from | n | gross R | target rate | days | years positive |
|---|---|---:|---:|---:|---:|---|
| **ETHUSD** | 2017-03-03 | **145** | **+0.7548** | 0.269 | 104 | **7 / 10** |
| BTCUSD | 2017-02-24 | 150 | +0.4600 | 0.180 | 110 | **9 / 9** |
| XTZUSD | 2019-11-06 | 106 | +0.5346 | 0.217 | 70 | 4 / 8 |
| DASHUSD | 2024-12-02 | 36 | +0.8844 | 0.306 | 26 | 3 / 3 |
| AVAUSD | 2021-01-09 | 103 | +0.3365 | 0.233 | 77 | 4 / 6 |
| ADAUSD | 2024-11-10 | 47 | +0.0115 | 0.106 | 27 | 2 / 3 |
| DOTUSD | 2024-11-10 | 46 | **−0.2552** | 0.130 | 31 | **0 / 3** |
| LTCUSD | 2024-11-29 | 22 | **−0.4768** | 0.091 | 15 | 1 / 3 |
| XRPUSD | 2024-12-02 | 49 | **−0.6043** | 0.041 | 42 | **0 / 3** |

Five of nine have **less than two years of archive** and all four negatives are among them.
**ETHUSD is the only crypto symbol with BTCUSD-length history**, and its record is better than
BTCUSD's on comparable n.

Cost-charged, day-block bootstrap over (symbol, day) blocks, 20,000 resamples:

| cell | n | cov | gross | cost | **NET** | **day-block CI95 (net)** | **p(≤0)** |
|---|---:|---:|---:|---:|---:|---|---:|
| **BTC+DASH — LIVE, all** | 186 | 0.81 | +0.4600 | 0.1518 | **+0.3083** | **[−0.052, +0.672]** | **0.0484** |
| **BTC+DASH — LIVE, pre-2025** | 126 | 0.96 | +0.3618 | 0.1351 | **+0.2268** | **[−0.161, +0.620]** | **0.1303** |
| **BTC+ETH — all** | 295 | **1.00** | +0.6049 | 0.1568 | **+0.4482** | **[+0.167, +0.731]** | **0.00070** |
| **BTC+ETH — pre-2025** | 243 | **1.00** | +0.5824 | 0.1554 | **+0.4270** | **[+0.119, +0.736]** | **0.00270** |
| BTC+ETH — 2025+ | 52 | 1.00 | +0.7104 | 0.1632 | +0.5471 | [−0.115, +1.239] | 0.0529 |
| BTC alone — all | 150 | 1.00 | +0.4600 | 0.1518 | +0.3083 | [−0.052, +0.672] | 0.0484 |
| ETH alone — all | 145 | 1.00 | +0.7548 | 0.1619 | **+0.5929** | [+0.160, +1.016] | 0.00325 |
| **ADDED-4 (ADA,DOT,LTC,XRP)** | 164 | — | **−0.3128** | — | — | **[−0.587, −0.009]** gross | **0.978** |

Two things to read off this table:
- **The currently armed pair does not clear zero out of window** (p 0.130) and barely clears it in
  sample (p 0.048). Its published strength rests substantially on 36 DASHUSD trades from a
  1.7-year window inside the selection period, which the cost authority refuses to price at all.
- **BTC+ETH clears zero out of window at p 0.0027 with full cost coverage.** Cost is 0.157 R/trade,
  of which **72 % is swap** at a 80 h median hold.

Direction split (the drift control): BTC+ETH LONG n = 184, +0.7719; **SHORT n = 111, +0.3281**;
pre-2025 SHORT +0.1904. **Both sides positive on both sides of the window** — the edge is not a long
crypto beta.

Per year, BTC+ETH gross: 2017 +0.942 (n 59), 2018 −1.000 (n 1), 2019 +0.222, 2020 +0.417,
2021 +0.308, 2022 **+0.077** (n 54), 2023 +0.756, 2024 +0.960, 2025 +0.728, 2026 +0.625.

**Frequency and book effect, under the live cluster cap** (one unit per cluster per day, first bar of
the day, the cap's own rule), restricted to 2021-02 … 2026-07 where all three armed surfaces exist:

| book | crypto units | book-days | **book-days/month** | **gross R/book-day** | **gross R/month** |
|---|---:|---:|---:|---:|---:|
| **LIVE (crypto = BTC+DASH)** | 102 | 155 | **2.358** | **+0.6499** | **+1.532** |
| **+ETH (crypto = BTC+DASH+ETH)** | 147 | 197 | **2.997 (+27.1 %)** | **+0.6998 (+7.7 %)** | **+2.097 (+36.9 %)** |
| swap DASH→ETH (BTC+ETH) | 124 | 174 | 2.647 (+12.2 %) | +0.6868 (+5.7 %) | +1.818 (+18.7 %) |
| crypto = family-9 | — | — | 3.248 *(crypto cluster alone)* | — | **+0.991 capped R/mo vs +1.119 for BTC+DASH+ETH** |

**Adding ETHUSD is the only change in this lane that raises frequency and per-day edge at the same
time.** Going all the way to the 9-symbol family raises frequency further and lowers total capped R,
because the four negative alts consume cap slots — which is the sharpest available demonstration that
under a cluster cap, symbol *quality* dominates symbol *count*.

### 4.3 `energy_agri` — expansion does NOT work

| arm | symbols | n | gross R | null | excess | beats null | days/mo |
|---|---:|---:|---:|---:|---:|---|---:|
| **B0 LIVE** | 2 oils | 72 | +0.8640 | +0.0350 | +0.8289 | **yes** | 0.653 |
| B1 +NATGAS | 2 (see note) | 72 | — | — | — | — | — |
| **B2 all archive** | 41 | 2,409 | +0.0715 | +0.0193 | +0.0522 | **no** | 3.592 |
| **B3 non-energy only** | 39 | 2,337 | +0.0470 | +0.0201 | +0.0270 | **no** | 3.564 |

The FVG-retest + energy-gate rule does not transfer. B2/B3 are also **negative in the forward window**
(−0.1996 and −0.3509), so they are not even an in-window artifact — they are simply not an edge.
**Note on B1**: `NATGAS_cash` produced zero rows because the archive carries only **2,751 H4 bars from
2024-10-13** for it and the FVG rule needs 100 bars of warm-up plus a vol-expansion gate; the harness
also resolved the name inconsistently. Either way NATGAS is untestable on this archive and is not a
scaling route. **The four off-surface symbols the sleeve's published economics rest on — CORN_c,
COTTON_c, HEATOIL_c, NATGAS_cash — are absent from the H4 archive entirely, so 63.6 % of that sleeve's
published population cannot be re-measured here at all.**

**The scaling route for `energy_agri` is not more symbols — it is the exit contract (§7), and it is
worth +0.2883 R/trade.**

### 4.4 `sub_xvol_pullback` — expansion does not work, and loosening does not either

**More symbols:**

| arm | symbols | n | gross R | null | excess | days/mo |
|---|---:|---:|---:|---:|---:|---:|
| **C0 LIVE** | 13 in archive | 94 | +1.2514 | +0.2326 | **+1.0188** | 0.164 |
| C1 all archive | 37 | 374 | +0.2385 | +0.1063 | +0.1322 | 0.514 |
| **C2 off-surface only** | 25 | 280 | **−0.1015** | +0.0707 | **−0.1722** | 0.412 |

**Looser but same-shaped trigger** — drop one clause of the depth-4 conjunction at a time, live
surface held fixed:

| variant | n | gross R | null | **excess** | days/mo | **capped R/mo** | pre-2025 | 2025+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **D0 full depth-4 (LIVE)** | 94 | +1.2514 | +0.2333 | **+1.0181** | 0.164 | **+0.1579** | +0.6942 | +1.8085 |
| drop `vol=xhi` | **7,874** | +0.1441 | +0.0996 | **+0.0445** | 6.278 | +0.8386 | +0.1353 | +0.1730 |
| drop `persist=rand` | 200 | +0.4781 | +0.1995 | +0.2787 | 0.264 | +0.2196 | +0.0679 | +1.1918 |
| drop `trend=up` | 478 | +0.3830 | +0.1740 | +0.2091 | 0.539 | +0.0475 | +0.1394 | +0.7900 |
| drop `mtf=conflict` | 1,041 | +0.2905 | +0.2090 | +0.0815 | 0.841 | +0.2651 | +0.1297 | +0.6249 |

**The conjunction is load-bearing, and every relaxation is monotonically worse per trade.** The
`drop_vol` arm looks tempting — 38× the frequency and **+0.8386 capped gross R/month against the live
cell's +0.1579** — until cost is charged. This sleeve's trades sit on metals and oil at a **112 h
median hold**, where the measured cost is 0.18 R (XAUUSD at 36 h) to **0.52 R** (XAUUSD at 100 h). At
0.30 R/trade the `drop_vol` arm's +0.134 capped mean is **net negative**, while the live cell's +0.963
survives with room. **`vol=xhi` is not a signal filter, it is a cost filter** — it is what keeps the
per-trade edge above the carry bill. This is the single most transferable lesson in the lane and it is
the mechanism behind rank 2 in §2.1.

**So `sub_xvol_pullback` cannot be scaled by symbols or by loosening.** Its one untested route is the
six declared symbols absent from the archive (CORN_c, COTTON_c, HEATOIL_c, FRA40_cash, EU50_cash,
US2000_cash) — a data fetch, not a research question, and the first three are already known to fail a
spread wall.

### 4.5 What (D) answers

**The book fires rarely because two of its three sleeves scan two symbols each and the third needs a
four-way state coincidence. Only one of those is fixable without changing a mechanism, and the fix is
ETHUSD: +27.1 % book frequency, +7.7 % R/book-day, +36.9 % R/month, at 100 % cost coverage, on the one
cell in the estate with sub-1.25× selection-window inflation.** Everything else tested — more crypto
symbols beyond ETH, the energy rule off oil, the substrate rule off its surface, and every relaxation
of the substrate conjunction — either fails its own null or fails once carry is charged.

---

## 5. (E) THE REST OF THE ESTATE — 29 sleeves under the corrected standard

Source: `R1_ESTATE_ROWS_V1.json.gz` (22,354 rows, the wave-20 quote-side-corrected walk), `r_new_mid`,
with the driftless target-rate null 1/(1+k) from each sleeve's own `SLEEVE_EXIT_PROFILES` entry.
Sleeves with `final_from_intent` targets have no single k and are marked `—`. **These are GROSS of
broker cost**; the estate's median measured cost is 0.10–0.30 R/trade depending on hold, so a sleeve
needs roughly **+0.15 R/trade gross** to be worth arming and **+0.30** to be worth arming with
conviction.

| sleeve | armed | n | R corrected | t | target rate | driftless null | **excess** | pre-2025 | 2025+ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `sub_xvol_pullback` | **A** | 88 | **+1.2676** | 6.07 | 0.534 | 0.250 | **+0.284** | +0.693 | +1.927 |
| `energy_agri` | **A** | 67 | **+0.7785** | 2.71 | 0.328 | 0.200 | **+0.128** | −0.108 | +1.455 |
| `crypto` | **A** | 181 | **+0.4339** | 2.89 | 0.188 | 0.200 | −0.012 | +0.372 | +0.563 |
| **`metals_softband`** | | 237 | **+0.4091** | 3.28 | 0.287 | — | — | **+0.465** | +0.127 |
| **`mx_btcusd_d1_donchian_20`** | | 318 | **+0.3491** | 4.16 | 0.450 | 0.333 | **+0.116** | +0.385 | +0.190 |
| **`vol_compression`** | | 391 | **+0.3301** | **3.48** | 0.325 | 0.250 | **+0.075** | **+0.298** | **+0.424** |
| `mx_jp225_cash_d1_vsr` | | 110 | +0.2818 | 1.98 | 0.427 | 0.333 | +0.094 | +0.292 | +0.263 |
| **`mx_ethusd_d1_donchian_20`** | | 311 | **+0.2116** | 2.54 | 0.402 | 0.333 | **+0.069** | **+0.186** | **+0.336** |
| `sub_mid_dn_revert` | (pulled) | 533 | +0.1932 | 2.44 | 0.298 | 0.250 | +0.048 | +0.134 | +0.625 |
| `metals_core` | | 385 | +0.1521 | 1.60 | 0.218 | — | — | +0.047 | +0.853 |
| `mx_us30_cash_d1_vsr` | | 121 | +0.1405 | 1.06 | 0.380 | 0.333 | +0.047 | +0.074 | +0.385 |
| `asian_fade` | | 1,319 | +0.1012 | 2.64 | trail | — | — | **+0.102** | **+0.101** |
| `mx_avausd_d1_donchian_20` | | 189 | +0.0925 | 0.88 | 0.360 | 0.333 | +0.026 | +0.113 | +0.039 |
| `mx_ger40_cash_d1_vsr` | | 110 | +0.0909 | 0.66 | 0.364 | 0.333 | +0.030 | +0.040 | +0.200 |
| `idxrev` | | 5,597 | −0.0138 | −1.19 | 0.564 | 0.571 | −0.008 | −0.037 | +0.046 |
| `orb_crypto_london` | | 858 | −0.0150 | −0.31 | 0.317 | 0.333 | −0.016 | +0.040 | −0.053 |
| `fx_jpy_ny` | | 1,620 | −0.0200 | −0.51 | 0.278 | 0.286 | −0.007 | −0.091 | +0.040 |
| `fx_jpy` | | 3,984 | −0.0473 | −1.92 | 0.271 | 0.286 | −0.015 | +0.032 | −0.098 |
| `metal_session_reversion` | | 837 | −0.0440 | −1.18 | trail | — | — | −0.093 | −0.008 |
| `vss_fxcross_london_up_low` | | 308 | −0.0552 | −0.69 | 0.315 | 0.333 | −0.018 | −0.349 | +0.053 |
| `mx_cadjpy_d1_vsr` | | 286 | −0.0559 | −0.68 | 0.315 | 0.333 | −0.019 | −0.039 | −0.200 |
| `mx_nzdjpy_d1_donchian_20` | | 503 | −0.1178 | −1.93 | 0.292 | 0.333 | −0.041 | −0.073 | −0.682 |
| `ny_crypto_momentum` | | 559 | −0.1250 | −1.64 | none | — | — | −0.200 | −0.077 |
| `mx_us500_cash_d1_atr_mr` | | 67 | −0.1493 | −0.90 | 0.284 | 0.333 | −0.050 | −0.200 | −0.046 |
| `metals_ob_micro` | | 34 | −0.2192 | −0.77 | 0.147 | — | — | −0.115 | −1.000 |
| `mx_us100_cash_d1_atr_mr` | | 71 | −0.2394 | −1.53 | 0.254 | 0.333 | −0.080 | −0.204 | −0.318 |
| `kz_london_crypto_low` | | 286 | −0.3085 | −2.82 | none | — | — | −0.426 | −0.241 |
| `asia_pdl_fade` | | 2,827 | −0.3289 | −11.85 | 0.160 | 0.250 | −0.090 | −0.361 | −0.313 |
| `liq_asia_up_low_metal` | | 157 | −0.4650 | −4.27 | 0.134 | 0.250 | −0.116 | −0.200 | −0.608 |

### 5.1 The one candidate that deserves a fresh look: `vol_compression`

**Why it qualifies under the mandate's test** — a sleeve rejected under a standard that has since been
corrected:

- Its `time_stop_bars` was **already correct** (`7680` = 80 D1 bars) while the fourteen `mx_*` sleeves
  next to it in the same dict carried `96`, the conversion *ratio*, and were re-measured. `CLAUDE.md`
  H-section records this explicitly: *"`vol_compression`, declared four lines earlier in the same
  dict, had the identical D1 horizon right all along."* Its neighbours got a repair and a re-read; it
  got neither, because nothing was broken about it.
- It is the **only unarmed sleeve in the estate materially positive on both sides of the selection
  window**: pre-2025 **+0.2975 on n = 290**, 2025+ **+0.4237 on n = 101**. In-window inflation
  **1.42×** — better than every armed sleeve except crypto-with-ETH.
- Its target rate **0.325 against a driftless 0.250** is a +0.075 excess with a clean shape: 66.0 %
  stop / 32.5 % target at 3R / 1.5 % maxbars. No trail, no partial, no truncation artifact.
- The quote-side correction barely touches it: **+0.3646 → +0.3301, −9.5 %**, i.e. it is not a
  spread-domain illusion.

**The honest multiplicity bill.** The ratified rule is `CANDIDATE_BOOK_V1` at the sealed **α = 0.10**,
family tip **V27, 59 declared members**. Adding one look makes 60; the BH rank-1 bar is
**0.10 / 60 = 0.001667**. `vol_compression`'s naive t = 3.48 on n = 391 is a raw p ≈ 0.00027 — but
that is an iid p on clustered data and this lane did **not** run its day-block or permutation null.
**It therefore does not have an admission-grade p-value and must not be armed on this document.**
What it has is the strongest prima facie case in the unarmed set for spending one gate run.

**Adversarial notes on my own candidate**: (i) it is a **D1** sleeve, so its live time stop is
7,680 M15 bars and `CLAUDE.md`'s B1452 hazard applies — an open D1 position asks the terminal for
7,744 M15 bars per tick, and if the terminal returns fewer than 7,680 the time stop **never fires**;
measure `copy_rates`' ceiling before arming anything in that cohort. (ii) its cost profile is
unmeasured here and D1 holds are long, so carry could be 0.3–1.0 R/trade — that alone could erase
+0.33. (iii) it is not in either account's `--tags`, so this is a genuine new arming decision, not an
expansion.

### 5.2 The near-misses, and why each is not the recommendation

- **`mx_ethusd_d1_donchian_20_breakout`** (n = 311, +0.2116, t 2.54, target 0.402 vs 0.333, pre-2025
  +0.186 / 2025+ +0.336 — one of only three sleeves that *improve* out of window). Interesting for
  the same reason as §4.2: **ETH carries a Donchian breakout edge on D1 as well as H4.** It is not the
  recommendation because the H4 route (adding ETH to `crypto`) reaches the same phenomenon inside an
  already-armed sleeve, at an already-priced contract, with no new arming decision and no new
  multiplicity look on an unarmed sleeve.
- **`mx_btcusd_d1_donchian_20_breakout`** (+0.3491, t 4.16). Already litigated: ADMIT → REJECT under
  A1b's corrected permutation null (q 0.129–0.135), **disarmed on FTMO 2026-08-05 by owner
  instruction**, and AN measured 7.6× chronological decay (folds 1–3 +1.504 → folds 4–5 +0.198). The
  pre/post split here reproduces the decay: +0.385 → +0.190. **Do not reopen.**
- **`metals_softband`** (+0.4091, t 3.28) **decays hard**: pre-2025 +0.465 on n = 198, 2025+ **+0.127**
  on n = 39. It is also a `partial_be_runner` sleeve walked at the plain contract, so its published
  economics describe a contract the book does not run — the same defect §7 measures on `energy_agri`.
- **`asian_fade`** (+0.1012, t 2.64) is the estate's most *stable* number — pre-2025 +0.1016, 2025+
  +0.1009, on n = 1,319 — but +0.10 R/trade gross is inside the cost band for an M15 sleeve, and
  AD's honest intrabar trail bound costs it 0.3365 R/day. Its stability is a genuine curiosity worth
  one properly-costed look; it is not an arming candidate at this magnitude.
- **`metals_core`** was armed for 90 minutes on 2026-07-29 and pulled. AE's cost-true lane inverted it
  to DOWN_WEIGHT ×0.50 on a 232-trade OOS at −0.205 R. Its pre-2025 is +0.047 on n = 335. The pull
  was right.

**Nothing else in the unarmed 28 is close.** The bottom half of the table is not marginal — it is
−0.12 to −0.47 R/trade on four-figure samples, with target rates *below* the driftless null. That is
what a sleeve with no edge looks like, and 15 of the 29 look like it.

---

## 6. (F) THE TWO OPEN OWNER ITEMS

### 6.1 `sub_xvol_pullback` — **KEEP, at current weight, and do not touch its exits**

**The number that drives it**: on its own live surface the sleeve is **+1.2514 R/trade gross on
n = 94, day-block CI95 [+0.551, +1.859], p(mean ≤ 0) = 0.0000**, with a target-hit rate of **53.2 %
against a driftless 25.0 %** — the largest target-rate excess in the estate by a factor of two.

**On the train-negative/test-positive sign inversion**: that inversion is a property of
**`sub_xvol_pullback @ target_4R`** — AK's *proposed exit change* — not of the armed sleeve. AU
measured that cell at the ratified rule and it **REJECTS at all four bands, p 0.0080 against a
0.002083 rank-1 bar**, with train −0.190/−0.278 and test +1.02/+1.37. AS handoff 3's standing
instruction is *"do not propose it."* This lane agrees and adds a second, independent reason:
`config/live_armed_set.json` declares `frontier_exits: []`, so the sleeve runs its committed 3R
contract, and §5.1 of that file records that flipping it would change armed-money behaviour the
moment the VPS carried the code. **The sign inversion is a reason not to change the exit. It is not a
reason to pull the sleeve.**

**On the 13 firing days in 18 months**: confirmed and worse than stated — **39 firing days in 20
years, and 67 of the 94 trades fall in 2020, 2025 and 2026**. The cause is mechanical and now
measured: `vol=xhi` requires ATR14 ≥ 1.6× its own 100-bar mean, so the sleeve fires **only in
volatility shocks**. §4.4 shows that removing that clause multiplies frequency 38× and collapses the
per-trade excess from +1.018 to +0.045 — below any plausible carry bill at a 112 h hold.

**Recommendation: KEEP, unchanged, at registry confidence 0.45.** It is a volatility-shock insurance
leg, not an earner: it will be silent for months and then contribute a large fraction of a good
quarter. Size it for that, do not expect a cadence from it, and **do not** attempt to raise its
frequency — the measurement says every route to more trades costs more than it earns.

**The one repair it needs**: its cost coverage is **28 %, adversely selected toward its cheapest
trades** (§3.3). Until the six-symbol slippage capture lands, every net number for this sleeve —
including this lane's — is an optimistic bound.

### 6.2 `energy_agri` — **MODIFY: delete `partial_be_runner`, run the plain 4R**

**The number that drives it**: paired on identical entries, identical bars, identical labeller
(`lane8_receipts/energy_agri_exit_contract_ab`, n = 72, USOIL.cash + UKOIL.cash, H4 archive):

| exit contract | mean R | t | total R | exits | median hold |
|---|---:|---:|---:|---|---:|
| **PLAIN published** — stop / 4R target / 80 bars | **+0.8640** | +3.08 | +62.2 | 25 target, 42 stop, 5 maxbars | 62 h |
| **LIVE `partial_be_runner`** — 50 % off at 2R, BE stop, 4R final | **+0.5757** | +2.76 | +41.5 | 22 target, **48 stop**, 2 maxbars | 62 h |
| variant: partial WITHOUT the BE stop | +0.6504 | +2.98 | +46.8 | 25 target, 42 stop, 5 maxbars | 62 h |
| variant: 2R target, no partial | +0.4368 | +2.48 | +31.4 | 34 target, 36 stop | 40 h |
| variant: 3R target, no partial | +0.6426 | +2.79 | +46.3 | 29 target, 40 stop | 48 h |
| variant: 6R target, no partial | +0.9022 | +2.81 | +65.0 | 19 target, 45 stop, 8 maxbars | 107 h |

**Paired deltas against the published plain contract:**

| change | Δ R/trade | **CI95** | t | n |
|---|---:|---|---:|---:|
| **the LIVE contract** | **−0.2883** | **[−0.5207, −0.0414]** | **−2.385** | 72 |
| partial without BE | −0.2136 | [−0.3775, −0.0312] | −2.511 | 72 |
| 2R target | −0.4272 | [−0.7550, −0.0624] | −2.511 | 72 |
| 3R target | −0.2214 | [−0.4028, +0.0011] | −2.116 | 72 |
| 6R target | +0.0382 | [−0.2638, +0.2917] | +0.265 | 72 |

**This is the third independent instrument to land on the same answer.** AD §6.2 measured
−0.308 R/day; AU measured a +0.2302 R/day restamp error at every band; this measures
**−0.2883 R/trade with an interval that excludes zero.** They agree in sign, in magnitude and in
mechanism — and the mechanism is now visible: the live contract converts **six winners into stops**
(42 → 48 stop exits) by moving the stop to breakeven on the remainder, and takes half the position off
at 2R in a sleeve whose winners run to 4R and beyond. Splitting the two components shows the partial
costs −0.214 and the **BE stop costs a further −0.075**.

**And 4R is not the problem**: 2R and 3R are both materially worse, 6R is statistically
indistinguishable from 4R. The target the route chose is right; the scale-out bolted onto it is not.

**Recommendation: MODIFY.** Change `energy_agri`'s entry in `SLEEVE_EXIT_PROFILES`
(`execution_packets.py:93-94`) from
`policy="partial_be_runner", trigger_r=2.0, partial_close_ratio=0.5` to
`policy="time_stop", final_target_r=4.0`, keeping `time_stop_bars=1280` unchanged. Expected value
**+0.2883 R per energy trade** at ~0.65 energy signal-days/month = **+0.19 gross R/month**, which is
12 % of the whole book's measured +1.53 gross R/month, for zero added risk — the change strictly
*reduces* the number of stop-outs.

**Two things that must be said with it.** (1) `energy_agri` is the **weakest of the three armed
sleeves on evidence**: day-block CI95 [−0.058, +1.745] includes zero, in-window inflation 4.79×, and
**0 % cost priceability on both accounts**. This modification improves a sleeve whose edge is not
established. (2) It is a **live-money behaviour change on an armed sleeve**, so it needs the same
ceremony discipline as an arming: it does not touch the R2 seal (`execution_packets.py` is unbound)
but it does change what the book does with an open position, and the owner should decide it
deliberately rather than as a side effect of a merge. **It is not urgent** — energy fires under once
a month.

---

## 7. (G) THE CONSTRUCTIVE CONCLUSION — one change, stated as an executable proposal

### PROPOSAL: add `ETHUSD` to the `crypto` sleeve's `ON_SURFACE`.

**The change, in full:**

```
src/components/ultimate_book/sleeves/crypto.py:24
-  ON_SURFACE = ("BTCUSD", "DASHUSD")
+  ON_SURFACE = ("BTCUSD", "DASHUSD", "ETHUSD")
```

One tuple. No rule change, no threshold change, no geometry change, no exit change, no config change,
no `--tags` change, no token re-mint (`crypto.py` is not in the activation-token digest, which hashes
`config/agent_config.yaml` plus the active profile bytes only). ETHUSD is already declared in both
live profiles. `registry.py:50` picks up `crypto.ON_SURFACE` by reference, so the registry needs no
edit. The docstring's own exclusion note (`:9-15`) must be rewritten to record why the exclusion is
being lifted.

**The scoring, as the mandate asks:**

| term | value | basis |
|---|---|---|
| **expected R gain** | **+0.565 gross R/month** on the whole three-sleeve book (+1.532 → +2.097, **+36.9 %**), from +27.1 % frequency and +7.7 % R/book-day | archive, one-unit-per-cluster-per-day, 2021-02 … 2026-07, `LANE8_MEASUREMENTS_V1.json → crypto_frequency_capped` |
| **probability it is real** | **high.** Out-of-selection-window, cost-charged, day-block bootstrapped: **n = 243, net +0.4270 R/trade, CI95 [+0.119, +0.736], p(≤0) = 0.00270**. Nine of ten years positive. Both directions positive out of window (LONG +0.817, SHORT +0.190). Beats its own measured placebo null's 97.5th percentile. 100 % cost coverage | §4.2 |
| **risk added** | **the lowest of any expansion available.** It does not add a cluster (crypto already exists), so under the one-unit-per-cluster-per-day cap **total daily risk is unchanged** — the unit splits across more symbols, it does not stack. It does not raise per-trade size, does not change the governor, does not change the dial. The only new exposure is BTC↔ETH correlation *within* an already-capped cluster, and the cap forecloses it by construction | `LIVE_BOOK_INTEGRITY_V1.md` §2, `admission.py` |
| **multiplicity bill** | **honest statement**: this is one new look. Family tip V27 = 59 declared, +1 = 60, BH rank-1 bar at the ratified α = 0.10 is **0.10/60 = 0.001667**. The **all-record** day-block p is **0.00070 — clears rank-1 by 2.4×**. The **out-of-window** day-block p is **0.00270 — does NOT clear rank-1**; it would clear at rank 2 (0.10 × 2/60 = 0.00333) but only if some other family member ranks below it, which is not established here, so **treat rank-1 as the binding bar and the out-of-window cell as NOT clearing it**. Do not overclaim: the correct sentence is *"clears the ratified bar on the full record; on the out-of-window subset alone it is 1.6× short of it"* |
| **what would reverse it** | ETHUSD's out-of-window cell going negative on a properly *permutation* null (this lane ran a day-block bootstrap, not the permutation null the ratified rule uses); or the CS slippage capture revealing an ETHUSD slippage term above ~0.28 R/trade, which is 1.8× the whole measured cost |

**Why this and not the `energy_agri` exit repair.** The exit repair is worth +0.19 gross R/month for
zero risk and is genuinely free, and it should also be done. It ranks second because it improves a
sleeve whose own edge interval includes zero and whose cost coverage is 0 %, whereas ETHUSD adds
sample and out-of-window support to the *only* cell in the estate that survives every control this
lane could construct. **Do both; do ETHUSD first because it is the one that makes the book's evidence
better as well as its return higher.**

**The pre-conditions, stated plainly:**

1. **One `symbols_get` check on the redacted_account terminal for `ETHUSD`.** It is declared in
   `config/profiles/redacted_account.yaml` and BTCUSD sits in that broker's `Cryptocurrencies\` folder, but
   the 2026-08-11 live probe covered only the 25 armed slots and did not include it. If it exists,
   this change **doubles redacted_account's crypto surface from one symbol to two** — that account currently
   has no DASHUSD (`BROKER_DOES_NOT_LIST_IT`) and so runs a one-symbol crypto sleeve.
2. **Run the ratified gate**, not this lane's bootstrap: the permutation null at `CANDIDATE_BOOK_V1`,
   RECORDED era population, banded, with `declared_family_size` incremented by one and recorded in
   `CANDIDATE_FAMILY_V*.json`. This lane's numbers are the case for spending that run; they are not a
   substitute for it.
3. **Arm at a decision-day boundary**, or delete the namespace's `firing_sleeves.json` first — the
   `RunningConvictionLedger` takes `na = max(na, override)` within a day and a mid-day change to the
   firing set is a size event (B365).
4. **Do not add ADAUSD, DOTUSD, LTCUSD or XRPUSD.** Jointly −0.3128 R/trade on n = 164, CI95
   [−0.587, −0.009]; all four have under two years of archive; they would consume cap slots from a
   positive symbol. AVAUSD (+0.337, n = 103) and XTZUSD (+0.535, n = 106) are positive but neither is
   cost-priceable on FTMO, so both are `NOT_EVALUABLE` and should wait for the slippage capture.

---

## 8. WHAT THIS LANE DID NOT SETTLE

- **The permutation null was not run.** Every p-value here is a moving-block/day-block bootstrap over
  (symbol, entry-day) blocks. The ratified admission rule uses a permutation null and a BH ladder at a
  declared family. Nothing here is an admission.
- **`energy_agri` and `sub_xvol_pullback` have no cost-true net anywhere**, because six symbols
  (USOIL_cash, UKOIL_cash, XAGUSD, XAGEUR, XAGAUD, XAUEUR/XAUAUD) lack reconciled price-domain
  slippage samples. Every net figure for them in this document and in the prior lanes is gross or an
  optimistic-subset bound. **The CS slippage capture is the highest-value unblocking measurement in
  the estate and it is a capture, not a research question.**
- **63.6 % of `energy_agri`'s published population cannot be re-measured** — CORN_c, COTTON_c,
  HEATOIL_c and NATGAS_cash are absent from the H4 archive. The same is true of six of
  `sub_xvol_pullback`'s twenty declared symbols.
- **This lane's walk is a strict superset of AQ's** by 5–6 grid-edge rows per sleeve (crypto 186 vs
  181, energy 72 vs 67, sub_xvol 94 vs 88); on every overlapping row the R is **identical to
  machine precision, zero mismatches**. The extras arise because AA/AQ generate on a union stamp grid
  and this harness walks each series directly. All comparisons here are within-harness, so the
  superset is a labelling note, not a confound.
- **`vol_compression` was not gated.** §5.1 makes a prima facie case and explicitly refuses to make
  an admission claim. Its cost profile is unmeasured and the D1 `copy_rates` ceiling hazard (B1452)
  applies to its whole cohort.
- **The book-level numbers in §4.2 are on the ARCHIVE population at the correlated-unit scale**, not
  the W7 cache at the book-day scale. They are the right population for a symbol-set question (the
  cache has no bar index) and the wrong one for a `p_pass`. Do not transfer them into a `p_pass`.
- **Record discrepancy, reported not resolved**: `config/live_armed_set.json` in this worktree
  (and in the wave-21 restatement worktree) still declares **four** armed sleeves including
  `sub_mid_dn_revert`, and `src.safety.armed_set.armed_sleeves()` returns that four. The
  2026-08-11 restatement records the host pull to three. This lane analyses the three; **the
  declaration file and the host may be out of sync, which is exactly the failure mode that file
  exists to prevent.** One `Select-String` on the launcher settles it.

---

## 9. RECEIPTS

| file | what |
|---|---|
| `lane8_receipts/lane8_walk.py` → `LANE8_CONTROL_WALK.json.gz` | the control: three armed generators on their own live surfaces, R-identical to `AQ_ESTATE_TRADES_V2` on every overlapping row |
| `lane8_receipts/lane8_expansion.py` → `LANE8_EXPANSION_V1.json{,.gz}` | §4 — 12 symbol-set arms + 5 substrate clause ablations, each with a 60–400-replicate measured placebo null, bootstrap CI, era split, frequency |
| `lane8_receipts/lane8_cost.py` → `LANE8_COST_CHARGED_V1.json` | §3.3 — every arm charged through `src/costs/cost_r`, with per-symbol coverage and the unpriced reason |
| `lane8_receipts/LANE8_MEASUREMENTS_V1.json` | §4.2 day-block cells; §4.2 cost-charged crypto; §4.2 capped frequency; §6.2 the `energy_agri` exit A/B; §5 the 29-sleeve corrected-walk table |
| `lane8_receipts/LANE8_CRYPTO_FAMILY_ROWS_V1.json.gz` | 704 per-trade rows, 9 crypto symbols, so §4.2 can be re-derived from raw |

Inputs bound: `/Users/borr/GTOSActive/vps-bars-20260727` (304 files, FTMO H4/M15/D1);
`docs/audits/…/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz` (control);
`docs/audits/…/phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz` (22,354 corrected rows);
`BROKER_TRUE_COSTS_V1.json`; `swarm/live_book_integrity_receipts/SYMBOL_UNIVERSE_V1.json`.
Machinery imported unchanged: `src/components/ultimate_book/sleeves/{crypto,energy_agri,metals,substrate,substrate_engine}.py`,
`src/components/ultimate_book/primitives.py`, `src/research_infra/walkforward/exits.py`,
`src/research_infra/replay_policy/generation.py`, `src/costs/`, `src/safety/armed_set.py`.
No sealed route touched, no `src/` byte changed, no git write, no broker or VPS contact.
