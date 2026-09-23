# F4 — THE ACCURACY CEILING: how accurate can this system get, and what would make it accurate

**Forensic lane 4.** Measurement only. No broker, no VPS, no config, no contract-bound file, no commit.
Pre-registration frozen before any model was fitted: `f4_accuracy/F4_PREREG_V1.json`,
sha256 **`bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054`**, frozen 2026-08-11T20:42:03Z.
All code and receipts under `f4_accuracy/`. Population: the frozen five-month cache,
**632,934 candidate occurrences / 146,745 filled trades**, Feb/Apr/May/Jun/Jul 2026.
The four never-read 2025 windows were not loaded, not scored, and no threshold here is proposed for them.

---

## 0. The four answers, in order

1. **The failure decomposition.** Of 94,998 losing filled trades: **42.1 % never went anywhere**
   (max favourable excursion < 0.3 R), **40.6 % went somewhere and stalled** (0.3–1.0 R), **17.4 % were
   genuinely winning and gave it back** (≥ 1.0 R). **82.7 % of losses never reached even half the target.**
   Cost as a binary killer accounts for **2.3 %** of losers and **0.65 %** of the loss. The clock is a net
   **contributor**, not a killer.
2. **Separability.** Yes — spectacularly, and it is **the wrong kind**. The ≥1.5 R vs <0.3 R populations
   separate at **AUC 0.8385** pooled walk-forward (0.8585 MARKET-only), against **0.5511** for the
   terminal-outcome target every prior experiment used. But the side-flip control shows the same model
   predicts the **opposite side's** excursion at **AUC 0.8371**. The separability is *magnitude*, not
   *direction*. It says how far price will travel, not which way.
3. **Feature poverty is real and it is the biggest single finding.** The 43-feature basis is
   **entirely M15**, its deepest populated price lookback is **12.5 hours**, and its effective dimension
   is **8 principal components**. Nothing reads H4, D1, weekly structure, another instrument, elapsed
   regime time, the opposing side, or whether the required move is physically attainable in the horizon.
   Adding 31 new features moved AUC **0.7262 → 0.8385**, and **one family did all of it**.
4. **The ceiling.** At the shipped 2 R contract the pool hits **16.31 %** against a **38.06 %** break-even.
   A perfect oracle earns **+1.83 R/trade** on 16.31 % of the pool. The best model, run as an actual book
   (one candidate per decision window, MARKET only, walk-forward), earns **+0.117 R/trade at a 32.8 %
   target hit rate** — which **closes the nine points** — and is then **exactly annihilated** by the
   estate's own worst-case censoring convention. Both numbers are below.

---

## 1. Three corrections to the brief, all measured

The frame I was given does not survive contact with the data. None of these changes the direction of the
answer; all three change the arithmetic, so they are stated first.

| brief | measured | where |
|---|---|---|
| "2:1 target" | **correct in R** — median gross at target is exactly **+2.0000**, at stop exactly **−1.0000**. But the two features `target_distance_atr` / `stop_distance_atr` stand in a **constant 1.5 ratio on all 632,934 rows**, contradicting the contract they are supposed to describe. This is the geometry defect repaired on `main` at `2bc0141f5`; the cache predates the repair. | `f4_basis_audit.py`, `F4_BASIS_AUDIT_V1.json` |
| "needs 41 %, achieves 32 %" | **needs 38.06 %, achieves 16.31 %** on all filled trades; **37.98 % vs 10.49 %** MARKET-only. Barrier-resolved (excluding time stops) it is **28.21 % vs ~37 %**, which is F1's 8.73 pp and the owner's "nine points". The "41/32" pair appears in no prior artifact. | `F4_CEILING_V1.json` |
| "every experiment re-ranked a fixed pool and failed" | **confirmed and sharpened.** On the terminal-outcome target the best arm here reaches AUC 0.5511 and its top decile earns **−0.326 R/trade**. Selecting on terminal outcome actively loses money. | `F4_SEPARABILITY_V1.json` → `S1_STATUS` |

**Instrument validation.** The excursion census reproduces the sealed corpus **bit-exactly**: 146,745 of
146,745 labels match by exit reason, maximum absolute gross-R deviation **4.44 × 10⁻¹⁶**. Every number
below sits on an instrument that reproduces the record it is auditing.

---

## 2. The three-way failure decomposition

**Nobody had separated these, and they have completely different repairs.** MFE/MAE come from Lane 2's
M1 horizon walk at the sealed horizon; MFE is the maximum favourable excursion reached *before* the trade
terminated, so "MFE ≥ k" is exactly "this trade would have hit a target at +kR before its stop".

### 2.1 Path modes — disjoint, over 94,998 losing filled trades

| mode | definition | n | share of losers | net R | median MFE | median MAE |
|---|---|---:|---:|---:|---:|---:|
| **M1 wrong direction from the start** | MFE < 0.3 R | 39,962 | **42.1 %** | −41,730 | +0.086 | −1.086 |
| **M5 went somewhere, stalled** | 0.3 ≤ MFE < 1.0 R | 38,533 | **40.6 %** | −39,474 | +0.564 | −1.114 |
| **M2 right, then reversed** | MFE ≥ 1.0 R | 16,503 | **17.4 %** | −17,473 | +1.346 | −1.164 |

Per-trade these are **−1.044 / −1.024 / −1.059 R**, i.e. **−$522 / −$512 / −$530** at a representative
0.5 % of a $100,000 account ($500 per 1 R). *The R sums are per-trade-if-taken across a 146,745-trade
census and are not a book; no book takes 146,745 trades. Read the per-trade column.*

The split is stable across all five months (M1 share 41.0–43.3 %, M2 share 16.6–18.1 %).

### 2.2 The cost and clock re-cuts — both are much smaller than assumed

| re-cut | n | share of losers | net R |
|---|---:|---:|---:|
| **killed by cost** — gross > 0 but net ≤ 0 | 2,170 | **2.3 %** | **−274.4 R** (0.65 % of the total loss) |
| **cut by the clock while gross-positive** | 23,180 | — | **+11,986 R** (these are *winners*) |
| cut by the clock while already ≥ 1 R up | 13,687 | — | +8,299 R |

**The clock is not killing this system; it is the only thing harvesting it.** Time stops resolve
25.8 % of fills at a mean gross of **+0.238 R**. F1's independent measurement closes the door from the
other side: a **12× longer clock buys 9.66 pp of hit rate and raises break-even by 9.48 pp — net
0.18 pp.** Hit rate and break-even are locked together by barrier geometry.

**And cost is not the disease, exactly as the owner said.** A cost model that charged nothing at all
would rescue 2,170 of 94,998 losing trades.

> **What this decomposition prescribes.** The three modes have three different repairs and only one of
> them is large. Fixing M2 (a wider stop, a trail, an earlier partial) addresses **17.4 %** of losses —
> and it is the repair the owner has rejected as "protecting the thing that wasn't strong in the first
> place". Fixing M1+M5 — **82.7 %** — is not an exit problem at all. It is a statement that four out of
> five losing trades were **entered into a move that never happened**. That is a generation and
> perception problem, which is where §3 and §4 go.

---

## 3. Feature poverty — the perceptual apparatus, audited

**This is the part of the lane the owner's reframing made primary, and it delivered the biggest measured
movement of anything here.**

### 3.1 What the 43 features can see

Receipt: `F4_BASIS_AUDIT_V1.json`.

| | |
|---|---|
| timeframe census | **M15 × 19, static cost tables × 5, POI state × 7** |
| features reading H4, D1, or weekly structure | **0** |
| features reading any other instrument | **0** |
| features encoding time since a regime change | **0** (one 1-bar boolean, `trend_transition_flag`) |
| features encoding the opposing side | **0** |
| features encoding whether the required move is attainable in the horizon | **0** |
| deepest price lookback declared | 96 M15 bars = **24 h** (`session_open_range_width_atr`, **99.24 % missing**) |
| deepest lookback actually populated | 50 M15 bars = **12.5 h** (`atr14_over_atr50`) |

**The system decides two-hour trades using a twelve-and-a-half-hour window of one timeframe, and nothing
else.** A discretionary trader who could see only that would be considered blind. This was confirmed
independently against the generator source: `_predecision_features`
(`src/components/broader_origin_generators.py:3805`) is called once, at `:3112`, on a single M15
`BarSeries` — while its own helpers `_trend_state` (`:3733`) and `_close_position` (`:3723`) are
timeframe-agnostic and have simply never been handed an H4 or D1 series.

### 3.2 What the 43 features actually are

- **`expected_slippage_r` is a constant** — one distinct value (0.02) across all 632,934 rows. A dead feature.
- **`poi_touch_count` and `poi_overlap_bar_count` are bit-identical.** A duplicate.
- **`cost_r` is exactly the sum of the other four cost terms** (max deviation 0.0). Redundant.
- **`target_distance_atr` = 1.5 × `stop_distance_atr` exactly, always.** Redundant *and* wrong (§1).
- `sweep_depth_atr` 96.05 % missing; `session_open_range_width_atr` 99.24 % missing.
- **Effective dimension: 18 non-dead numerics → 8 principal components carry 90 % of variance**,
  14 carry 99 %, condition number **1.23 × 10¹⁴** (numerically singular).

**43 declared features are ~8 real dimensions of one timeframe.**

### 3.3 The three families built, and what they moved

Ranked before building, by expected information gain × computability. All are strictly point-in-time: a
bar stamped at open `t` of duration `D` is usable only when `t + D ≤ label_span_start_utc`, asserted per
row — **0 violations over 146,745 rows**. Coverage **1.0000** on every new feature.

| family | n | what it adds | pooled AUC when added alone to the frozen 43 |
|---|---:|---|---:|
| baseline — frozen 43 | 43 | — | 0.7262 |
| **N2 horizon feasibility + vol term structure** | 8 | required move in M15 ATR; required move per bar; **trailing empirical P(reach 2R / 1R in this span)**; D1/M15 and H4/M15 ATR ratios | **0.8378** |
| N1 higher-timeframe context | 13 | D1/H4 trend in own ATR, position in 20-day and 20-bar range, room to the D1 extreme in R, prior-day and **prior-week** levels in R, D1 ATR percentile | 0.7263 |
| N3 decision-window pool state | 8 | window density, same-symbol count, **opposite-side count**, directional agreement | 0.7260 |
| N1b regime age | 2 | **bars since the M15 trend state last changed** | 0.7261 |
| **all four together** | 31 | | **0.8385** |

**One family did all of the work and the other three did none.** N2 alone reaches 0.8378 of the 0.8385
total. Higher-timeframe context — the thing whose absence is the most conspicuous hole in the basis —
**moved the metric by 0.0001**.

> **That is a result, not a null.** It says the missing information that matters is not *context* but
> *physics*: whether the required move is attainable in the time allowed. The system was never blind to
> the daily chart in a way that mattered for this label; it was blind to its own feasibility.
>
> **The honest qualification, and it is severe:** §4.2 shows the N2 family predicts the *opposite side's*
> excursion nearly as well as the real one. N2 is a magnitude instrument. Its 0.11 of AUC is real
> information about how far, and almost none about which way. Higher-timeframe context scoring 0.0001
> on a *magnitude* label is weak evidence that it is useless on a *directional* one — it was never given
> a directional label to predict, because on this pool no directional label separates (§4).

**A note on the guard that fired.** The C3 leak assertion rejected my own feature
`feas_median_span_excursion_r` on its name. The quantity is computed only from windows strictly before
the decision bar and is not a leak — but the guard was right that the name is outcome-shaped, and it was
renamed rather than the guard weakened. Recorded because the repo has a matching production guard
(`learned_edge_dataset_builder.py:203` `FORBIDDEN_FEATURE_TOKENS`) that **counts** violations rather than
raising, so a mis-named feature there silently shrinks the training set.

---

## 4. Separability — the crux, and the control that decides what it means

### 4.1 The two targets are not close

Walk-forward, expanding window, fit on months strictly prior, evaluated on Apr / May / Jun / Jul.
Group disjointness on `decision_window_id` asserted (C6). Receipt: `F4_SEPARABILITY_V1.json`.

| target | positive class | n pos / n neg | best pooled AUC | top-decile precision | top-decile realized net R |
|---|---|---:|---:|---:|---:|
| **S2 excursion** (this lane's) | MFE ≥ 1.5 R vs MFE < 0.3 R | 39,284 / 41,084 | **0.8385** | 0.9004 | **+0.7222** |
| **S1 terminal** (every prior attempt) | TARGET vs STOP | 30,737 / 78,207 | 0.6302 | 0.4320 | **−0.0980** |
| S1 on the frozen 43 alone | | | 0.5511 | 0.3430 | **−0.3258** |
| incumbent frozen ridge, as a score | | | 0.5396 / 0.5011 | | +0.2605 / −0.2632 |

**Posing the question on the path rather than on the terminal value is worth 0.29 of AUC.** That is the
single largest metric movement in the lane and it required no new data at all — only a different label.

**The capacity ladder inverts again**, on both targets and independently of B3's finding:
0.7262 (100 iters / 15 leaves) → 0.7217 → 0.7135 → **0.7076** (1200 / 63). Plain L2 logistic regression
(0.7321) beats every boosted arm. Four folds, monotone. This is now a **third** independent
instrument reporting that more capacity on this surface is worse.

### 4.2 The side-flip control — and it kills the headline

For every filled trade I recomputed the excursion the **opposite side** would have seen, from the
**identical fill price** over the **identical window**. Symbol, instant, horizon, risk, volatility state
and every feature except the sign of `side` are held exactly constant.

| arm | AUC predicting the REAL side's excursion | AUC predicting the FLIPPED side's excursion |
|---|---:|---:|
| frozen 43 | 0.7262 | **0.8210** |
| frozen 43 + all 31 new | 0.8385 | **0.8371** |
| N2 family only | 0.8056 | 0.7892 |
| geometry only (`risk_over_atr`, `cost_r`, `spread_r`) | 0.7064 | 0.7701 |
| `risk_over_atr` alone | 0.6474 | — |

**The model predicts the excursion of a trade pointed the wrong way as well as it predicts the real one.**
On the frozen 43 it predicts the wrong-way trade *better*. AUC 0.84 is arithmetic about how far this
instrument travels in two hours relative to this stop. It contains, on its own, no opinion about direction.

**This is my own headline result, refuted by my own control, and it is the most useful thing in the lane.**
Any future selector reporting a large AUC on an excursion-shaped label must publish its side-flip number
or the AUC means nothing.

### 4.3 But the generator's direction is not zero — it is real, small, and dies before the target

Same instrument, read as an economic quantity rather than a model input. Blind-entry control matched on
symbol, side, month, hour-of-day, horizon and risk, with the blind arm **charged the candidate's own
spread** (which cuts against the finding). Receipts: `F4_SIDEFLIP_V1.json`, `F4_BLIND_CONTROL_V1.json`.

**MARKET orders (74,249 fills), real vs the identical trade pointed the other way:**

| threshold | real P(MFE ≥ k) | flipped P(MFE ≥ k) | directional lift |
|---|---:|---:|---:|
| 0.5 R | 0.5218 | 0.7120 | **−0.1901** |
| 1.0 R | 0.3433 | 0.4136 | **−0.0703** |
| 1.5 R | 0.2261 | 0.1537 | **+0.0724** |
| **2.0 R** | 0.1049 | 0.0622 | **+0.0427** [CI +0.0386, +0.0467], p(>0) = 1.000 |

Against a matched blind entry rather than the flipped side, the MARKET lift at 2 R is
**+0.0066** [CI +0.0002, +0.0131], p = 0.98, positive in all five months.

**LIMIT orders are directionally inverted**: real P(MFE ≥ 2 R) 0.2227 against flipped **0.3516**, lift
**−0.1288** [CI −0.145, −0.112]. A filled LIMIT is a level the market came to *and kept going through*.
The fill is itself an adverse selection, and it is 49 % of all fills.

> **The mechanism this exposes, and it is new.** The LIMIT families' barrier-free drift measured from
> their own fill is **positive** (+0.146 / +0.088 / +0.087 R on the three largest cells) while their
> realized outcome is **−0.191 R**. They take a large adverse excursion first and then revert. They are
> mean-reversion entries wearing a trend-following stop. The stop is converting a positive drift into a
> negative outcome on half the book.
>
> The obvious repair is a wider stop, which the owner has rejected on principle and which §2 shows only
> addresses 17.4 % of losses anyway. **The reading that survives his objection is that the entry is
> mistimed, not that the stop is too tight** — the LIMIT is filled at the start of the adverse leg rather
> than at its end. That is a generation repair, and it is testable: re-time the LIMIT to the *reclaim* of
> the level rather than the touch, and re-measure the flipped lift. Nothing in this lane tested it.

---

## 5. The ceiling table

Because MFE is the excursion reached before termination, the outcome under any target `k ≤ 2` is an
**exact re-simulation**: `R(k) = +k if MFE ≥ k, else terminal gross R`. Costs held at the row's own
deductible. Receipt: `F4_CEILING_V1.json`. All filled trades, n = 146,745; MARKET-only in brackets.

| target k | pool hit rate | break-even needed | gap | take-everything net R | **(a) perfect oracle** | **(b) rank oracle, top 10 %** | **(c) shipped ridge, top 10 %** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5 R | 60.18 % [52.18] | 76.11 % | −15.9 pp | −0.174 [−0.291] | **+0.352** on 60.2 % of pool | +0.480 | +0.016 [−0.094] |
| 1.0 R | 39.48 % [34.33] | 57.08 % | −17.6 pp | −0.198 [−0.283] | **+0.845** on 39.5 % | +0.980 | −0.016 [−0.083] |
| 1.5 R | 26.77 % [22.61] | 45.67 % | −18.9 pp | −0.214 [−0.272] | **+1.339** on 26.8 % | +1.480 | −0.042 [−0.081] |
| **2.0 R (shipped)** | **16.31 %** [10.49] | **38.06 %** | **−21.8 pp** | **−0.228** [−0.264] | **+1.831** on 16.3 % | **+1.972** | **−0.066** [−0.079] |

**Read the two gaps the brief asked for, plainly.**

- **(a) oracle +1.831 vs (b) best model.** The oracle is not a model — it is the whole available
  information. The gap between it and anything fittable is essentially the entire distance, because
  §4.2 establishes the fittable part is magnitude and magnitude is symmetric in direction. **The
  modelling is failing to use almost all of the available information, and the reason is that the
  information is not in the feature side — it is in the direction of the next two hours, which nothing
  in the basis or in my 31 additions predicts.**
- **(c) the shipped rule ranks better than random and still loses.** Its top decile earns −0.066 R
  against a pool mean of −0.228, so it *is* ranking; it ranks within a pool whose every decile is negative.
- **The gap between (b) and break-even is the whole question**, and §6 is the one place it closes.

**A structural fact worth recording:** only **84,721 of 146,745** filled trades (57.7 %) were ever scored
by the shipped ridge at all — the rest fail its `cost_r ≤ 0.20` gate before scoring. Two-fifths of the
trades this system actually takes are invisible to the model that is supposed to be choosing them.

---

## 6. The gap: can the ~10× between drift and cost be closed from either end?

Receipt: `F4_GAP_V1.json`. Barrier-free directional drift measured from the actual quote-adjusted fill
over the label span, from M1 closes.

### 6.0 Reconciliation with F1 — the two lanes agree, and the sharper statement is mine

F1 measures pool drift **+0.0301 R/trade** on the raw archive basis. I measure **−0.0360 R/trade**
[CI −0.0489, −0.0224], p(>0) = 0.000, from the **quote-adjusted fill**. The difference is F1's own
entry-leg quote transform, **0.0579 R**: +0.0301 − 0.0579 = −0.0278, inside my confidence interval.

> **Once the entry quote transform is charged — before commission, swap, slippage or the exit leg —
> the pool's directional drift is already negative.** F1's "cost is 9.5× the edge" is generous. On the
> price a trade actually pays to get in, there is no edge left to be 9.5× of.

### 6.1 The cost end — the floor is real, and it is empty

| keep | cost threshold | n (per day) | mean all-in cost | drift | **net (drift − cost)** |
|---|---:|---:|---:|---:|---:|
| cheapest 5 % | 0.0477 R | 7,338 (73) | **0.0386 R** | −0.0359 | **−0.0745** [−0.097, −0.052] |
| cheapest 10 % | 0.0612 R | 14,675 (147) | 0.0467 R | −0.0011 | −0.0478 [−0.067, −0.029] |
| cheapest 25 % | 0.0982 R | 36,687 (367) | 0.0666 R | −0.0110 | −0.0777 |
| cheapest 50 % | 0.1688 R | 73,373 (734) | 0.0989 R | +0.0035 | −0.0954 |
| **whole pool** | — | 146,745 | **0.2630 R** | −0.0360 | −0.2990 |

**The cost floor reachable by selection alone is ≈ 0.039–0.047 R — a 6–7× reduction, with no contract
change.** That is a genuine and previously unstated headroom, and it answers the coordinator's question:
0.2868 R is a pool mean, not a floor.

**And it buys nothing, because the drift is not there.** Every quantile is net-negative and the
confidence intervals exclude zero.

**Why cost falls is mechanical, not a discovery.** Cost in R is `cost_price / risk_price`, so it is
governed by the stop denominator:

| `risk_over_atr` quintile | mean risk/ATR | all-in cost | drift | net |
|---|---:|---:|---:|---:|
| 1 (tightest) | 0.33 | **0.4444 R** | −0.0268 | −0.4712 |
| 3 | 0.75 | 0.2473 R | −0.0239 | −0.2712 |
| 5 (widest) | 2.71 | **0.1187 R** | −0.0364 | −0.1551 |

Cost falls **3.7×** from tightest to widest stop while drift is **flat and negative throughout**. This is
the magnitude program's "widening the stop is worth +0.03 to +0.07 R" re-derived on a different
instrument, and it is exactly the move the owner rejected: it improves the ratio by shrinking the
denominator, not by making the trade better. **Confirmed: not the answer.**

**What is left on the cost side.** Spread is the largest term (0.1213 R pool-wide) and is instrument- and
hour-selectable; F1's finding that the **exit** leg (0.0872 R) exceeds the **entry** leg (0.0579 R) is not
a symmetry I can explain from this lane's data and I flag it as an unexplained asymmetry worth isolating —
a same-instrument round trip should not cost more to leave than to enter unless exits are systematically
timed into wider-spread moments, which would be a schedulable defect rather than physics.

### 6.2 The edge end — hard structural conditioning

Cells of order type × family × volatility-term-structure state, minimum 400 trades. **0 of 26 cells is
net-positive.** Best: `LIMIT | current_breaker_re_entry | LO`, n = 1,554, drift **+0.1457**,
cost 0.2354, **net −0.0897** [CI −0.180, +0.009], p(>0) = 0.036. The three best-drift cells are all LIMIT,
i.e. all fill-conditioned and all directionally inverted by §4.3 — their drift is the reversion after an
adverse leg, not an edge.

**The gap at the best structural cell is 0.09 R/trade, or −$45 per trade at $500/R.**

### 6.3 The trailing MFE/|MAE| ratio test — it works, and it is not enough

Pre-registered as asked: cell = symbol × family × order type; rank by **trailing** mean(MFE)/|mean(MAE)|
on strictly prior months; trade only cells above 1.0; measure the forward month.

| | net R/trade (drift − cost) | n |
|---|---:|---:|
| cells selected by trailing ratio > 1 | **−0.2424** [−0.264, −0.220] | 70,665 |
| all cells | −0.3175 [−0.333, −0.303] | 107,697 |
| **delta** | **+0.0752** | |

**The rule adds +0.0752 R/trade out of sample and the selected subpopulation is still −0.2424 R/trade.**
It is a real conditioning signal that closes about a quarter of the gap. It is a measurement, not a
candidate. **Gap remaining at the best cell: 0.24 R/trade = −$121 per trade at $500/R.**

---

## 7. The one place the gap closes — and the control that annihilates it

Everything above says no. This does not, and it gets the most adversarial treatment in the lane.

**The construction.** Train the winning arm on the S2 excursion label, MARKET only, walk-forward. Then run
it as an actual book: **one candidate per decision window**, top-N% by score, and measure **realized
terminal net R** on the sealed labels. Receipt: `F4_CONTROLS_V1.json`.

| cut | trades | per day | net R/trade | total net R | 95 % CI | p(total > 0) | **target hit rate** | pos/neg days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| top 9 % | 3,043 | 38.0 | **+0.1171** | **+356.4** | [+208, +521] | 1.000 | **32.83 %** | 53 / 27 |
| top 5 % | 1,878 | 23.5 | +0.1196 | +224.6 | [+104, +353] | 1.000 | 32.32 % | 53 / 27 |
| top 1 % | 520 | 6.5 | **+0.1644** | +85.5 | [+23, +143] | 0.997 | 30.96 % | 51 / 29 |

**32.83 % against a 20.95 % pool rate and a ~27–28 % barrier-resolved break-even. The nine points close.**
At $500 per 1 R that is **+$59 per trade** and **+$178,000** over 100 trading days at top-9 % — which is
precisely why it must be attacked rather than reported.

### 7.1 The pre-registered leak controls — it passes both

- **C1, one-day lag.** Replacing every feature with the same feature from the prior trading day collapses
  AUC **0.8585 → 0.5447**. Under the interpretation declared in the prereg this is the good outcome: the
  signal is genuinely timely, and it is not slow-moving symbol or regime identity.
- **C5, random split vs time split on identical rows** — the control that can see a leak permutation
  cannot. Random **0.8638**, time **0.8434**, gap **+0.0205**, inside the pre-registered 0.03 bar. No
  material within-window information sharing.
- **C6**, group disjointness on `decision_window_id`, asserted on every fold.
- **C3**, the outcome-key whitelist, enforced in-process; it fired once, correctly (§3.3).

### 7.2 The control that kills it

**The book is measured on resolved MARKET fills only. 9.42 % of MARKET candidates are CENSORED**
(4.88 % source-interval gap, 3.66 % gap-through SL/TP, 0.85 % geometry). The estate's own worst-case
convention charges a censored row **−1 − deductible = −1.1394 R**.

| cut | booked (censored excluded) | censored siblings at the pool rate | worst-case charge | **worst-case book** |
|---|---:|---:|---:|---:|
| top 9 % | +356.4 R | ~316 | −360.5 R | **−4.1 R** |
| top 5 % | +224.6 R | ~195 | −222.5 R | **+2.1 R** |
| top 1 % | +85.5 R | ~54 | −61.6 R | **+23.9 R** |

**At the loose cut the result is annihilated to within 1 % of zero.** The truth lies between the two
columns — "exclude" is optimistic and "−1.1394 R each" is deliberately punitive — but the honest
statement is that **this book's sign is decided by a censoring convention, not by its edge**, at every
cut except the tightest, where it survives at 6.5 trades/day and +23.9 R over 100 days.

**Two further reasons for scepticism, both stated against my own result:**

1. **The law.** B3 measured realized book R against MARKET-top share across 17 arms at
   **r = −0.9786 (p = 1.0 × 10⁻¹¹)**: every arm that traded more MARKET lost more, down to −690 R at
   75 % MARKET share. This book is **100 % MARKET**. It sits at the far end of the strongest empirical
   regularity the estate has, on the wrong side. The distinguishing feature is the label — every arm in
   that regression trained on terminal net R or P(win); this one trains on excursion magnitude — but a
   single arm contradicting a 17-point regression is a hypothesis, not a refutation.
2. **The label is close to the payoff.** "MFE ≥ 1.5 R" and "hit the +2 R target" are nearly the same
   event, so a top decile with 92 % precision on that label *mechanically* books high net R. Top-decile
   net R is substantially a restatement of the AUC, not an independent economic confirmation. The
   independent confirmation is the **32.83 % target hit rate under a one-per-window constraint**, which
   is a real book statistic — and that is what §7.2's censoring column then puts in doubt.

### 7.3 The exact measurement that resolves it

**Score the 7,719 censored MARKET rows with the same model and measure the selected set's *actual* censor
rate rather than assuming the pool rate; then resolve them with Lane 2's TOLERANT M1 walk, which already
exists at `walk2_{month}.pkl.gz` and treats an M1 gap as unobserved time instead of censoring.** All
inputs are on disk; this is hours, not days. My selection favours high-feasibility (volatile relative to
stop) instants, and gap-through censoring is more likely there, so **I expect the selected censor rate to
be above 9.42 %, which would push the worst-case book further negative.** That is the prediction to
falsify, and stating it is the point.

---

## 8. What would make a candidate accurate — the answer

1. **Not exits, not cost, not the clock.** 82.7 % of losing trades never reached half the target; cost
   binary-kills 2.3 % of them; the clock is a net contributor; and a 12× longer clock closes the gap by
   0.18 pp.
2. **Not higher-timeframe context, on the evidence here.** The most conspicuous hole in the basis moved
   the metric by 0.0001 — with the caveat in §3.3 that it was tested against a magnitude label.
3. **Feasibility is genuinely missing and genuinely large.** "Can this instrument travel the required
   distance in the time allowed" was worth 0.11 of AUC and is absent from all 43 features. **But it is a
   magnitude instrument** (§4.2) and it cannot, alone, make money.
4. **The binding scarcity is direction, and it is scarce but not zero.** The MARKET arm has a real,
   five-month-stable directional lift (+0.0427 vs its own flipped side at 2 R). The LIMIT arm — half of
   all fills — is directionally **inverted**, and its positive barrier-free drift is post-adverse-leg
   reversion, not edge.
5. **So the shape of a strong candidate is now specified:** a **MARKET** entry, in an instant where the
   trailing feasibility says the required move is attainable, in a family whose flipped lift is positive.
   That combination measures **+0.117 R/trade at a 32.8 % hit rate** and closes the nine points — and its
   sign then rests on a censoring convention, which is the next thing to measure, not to argue about.

### The one direction this lane did not test and would prioritise

**Re-time the LIMIT fill from the touch of the level to the reclaim of it, and re-measure the flipped
lift.** Half of all fills are directionally inverted, their drift after the fill is positive, and the
adverse leg they take first is what the stop is catching. That is a generation repair rather than an exit
repair, it is exactly "make a strong thing in the first place", and everything needed to measure it —
M1 bars, the walker, the flipped-lift instrument built here — is on disk.

---

## 9. Ledger

**Arms declared and run:** 6 separability arms × 2 targets, 4 single-family ablations × 2 targets,
2 MARKET-only replications × 2 targets, 3 geometry controls (**failed to execute — import-by-value bug;
the intended question is answered instead by the side-flip in §4.2 and by `risk_over_atr`-only
AUC 0.6474**), 9 side-flip arms, 4 cost-floor quantiles, 5 stop-width quintiles, 26 structural cells,
1 trailing-ratio test, 2 leak controls, 3 book cuts. **No arm outside the prereg is reported as a
result.** The book cuts (§7) and the side-flip (§4.2) were **not** in the frozen prereg — the side-flip
was added as an adversarial control on a positive result, and the book cuts as an economic realism test;
both are declared here as **post-hoc controls on my own findings**, which is the direction that can only
weaken a claim.

**Nulls and negative results, stated as such:** N1/N1b/N3 feature families (~0 AUC movement);
higher capacity (monotone inversion, 4 cells); structural cell conditioning (0 of 26 net-positive);
cost-floor selection (4 of 4 quantiles net-negative); every target level in the ceiling table.

**Not touched:** june/august/september/december 2025; no threshold proposed for them. No live path, no
config, no contract-bound file, no commit.

**Receipts:** `f4_accuracy/receipts/` — `F4_DECOMPOSITION_V1.json`, `F4_BASIS_AUDIT_V1.json`,
`F4_NEW_FEATURES_V1.json`, `F4_SEPARABILITY_V1.json`, `F4_SIDEFLIP_V1.json`, `F4_BLIND_CONTROL_V1.json`,
`F4_CEILING_V1.json`, `F4_GAP_V1.json`, `F4_CONTROLS_V1.json`, plus run logs and
`F4_PREREG_V1.sha256`.
