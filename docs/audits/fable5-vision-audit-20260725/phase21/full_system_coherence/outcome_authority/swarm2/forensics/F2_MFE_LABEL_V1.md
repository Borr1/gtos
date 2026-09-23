# F2 — the label was the bottleneck, and replacing it does not help: MFE measures the stop, not the edge

**Forensic lane 2, 2026-08-12. A BUILD lane.** Commission: *"Every selection experiment in this
programme's history has trained and scored on `terminal_net_r` … that label is censored, discrete and
almost information-free. Maximum favourable excursion is continuous and far less censored. It has never
been used here."*

**The commission's premise is CORRECT and is now measured for the first time. Its consequence is
REFUTED, with a mechanism.** MFE is **6.9× more predictable** than `terminal_net_r` on identical
features, identical folds and an identical estimator — and a model that predicts it ranks the actual
economics **significantly worse than the label it replaces**, because MFE denominated in R is a
measurement of the **stop width the system already chose**, not of the market.

**Scope discipline.** Measurement only. No broker, no VPS, no config, no decision-contract-bound file,
no `git` write, no live path touched. Neither reserve day (2025-10-31, 2025-11-05) and none of the four
never-read 2025 windows (june/august/september/december 2025) is touched by any arm. Computation ran
from the sealed row cache, the true-UTC M1 archive and job scratch.

**Code** `swarm2/forensics/f2_mfe_label/` — 8 scripts, 10 JSON receipts.
**Pre-registration** `f2_mfe_label/PREREG_V1.json`, payload sha256
`8b038d866c95412baba06ddf420267ac2d254bdaffa28cf2de8b2b3b38025ff4`, frozen **before the census was
built and before any outcome was read**. Every arm it declares is reported below, pass or fail.

---

## 0. The answer in eight lines

| # | finding | number |
|---|---|---|
| **1** | **The premise is confirmed, decisively. MFE is 6.9× more predictable than the shipped label** on the exactly matched population — same 84,721 rows, same 100 daily refits, same Ridge. The shipped label's model is *worse than predicting its own mean out of sample*, which is the measured signature of a label dominated by noise. | within-window ρ **0.2391 vs 0.0348**; OOS R² **+0.0800 vs −0.0105**; 81,216 distinct values vs 3 outcome classes |
| **2** | **And it is worthless, because MFE in R units is 1/stop-width.** The MFE model's own prediction correlates **−0.787** with `stop_distance_atr`. Predicted-MFE quintiles order realized MFE monotonically **0.604 → 1.968** — and order realized net R **not at all** (−0.095, −0.127, −0.078, −0.085, −0.080), because MAE scales with it (−0.516 → −0.699). The ratio never moves. | ρ(pred MFE, stop_distance_atr) **−0.7873**; ρ(pred MFE, risk_over_atr) **−0.7826** |
| **3** | **THE KILL. Ranking by predicted MFE ranks the economics WORSE than the label it replaces, significantly.** | transfer to realized net R **−0.0565** vs shipped **+0.0348**; paired **−0.0913 [−0.1085, −0.0741], p 0.000** |
| **4** | **One excursion label does transfer positively — MAE, at 2.8× the shipped label — and a single raw feature already does it.** Ranking by cheapest `cost_r` is statistically indistinguishable from the fitted MAE model, and `cost_r` is *already the funnel's tiebreaker* (`b3_lib.run_windows`: `-meta[i]["cost"]` is sort key 2). | MAE **+0.0964 [+0.0828, +0.1106]**; **mae − (−cost_r) = −0.0127 [−0.0286, +0.0039], p 0.128** |
| **4b** | **Ranking on MFE/&#124;MAE&#124; instead of MFE level is worth +0.024–0.028 (p 0.000) and still does not cross zero.** Both constructions of the ratio remain −0.064 to −0.067 worse than the shipped label. F1's cell-level +0.963 coupling reproduces **only** from its `_full` columns (full-window travel, not the trade's own excursion); on the trainable label the same correlation is **+0.043**. §9 | JOINT-RATIO **−0.0322**, L-RATIO **−0.0289**, shipped **+0.0348** |
| **5** | **THE ADAPTIVE TARGET: real, and not adaptive.** A per-trade target beats the fixed 2R convention by **+0.0382 R/trade (p 0.000)** on 91,843 trades — but does **not** beat the best single CONSTANT target chosen causally from prior days. All of the value is "2R is the wrong number"; none of it is conditioning on a prediction. | P-ADAPT − P-FIX2 **+0.0382 [+0.0258, +0.0511]**; P-ADAPT − P-FIXBEST **−0.0024 [−0.0116, +0.0071], p 0.60**; best constant ≈ **0.5R** |
| **6** | **And the target frontier does not reach break-even at any width.** Achieved hit rate is below the required hit rate at **all 14 ladder levels**. The shipped 2R target sits at the *worst* point of the frontier; the best is 0.5R at −0.0155 R/trade. | 2.0R: **18.64 % achieved vs 20.99 % required (−2.36 pp)**; 0.5R: 61.08 % vs 62.34 % (−1.26 pp) |
| **7** | **No arm produces a better BOOK, at any matched trade count.** Arms that look positive are the ones that structurally refuse to transact (26–28 trades in 100 days). Applied to the trades the funnel actually selects, the winning exit change is worth **−11.16 R**. | E1 vs shipped: every CI contains zero; X-FIXBEST − X-FIX2 **−11.158 R, p 0.326** |
| **8** | **The censoring repair works as an estimator and fails as a decision — B2's law, reproduced on a fourth independent label.** Modelling fill and excursion jointly beats collapsing them, and ranks the economics 0.228 worse than the shipped label, because filling is the adverse event. | hurdle − collapse **+0.0067, p 0.000**; hurdle transfer **−0.1359** vs shipped **+0.0926** |

**One sentence.** *The commission's diagnosis of the label was right and its prescription is refuted by
its own instrument: maximum favourable excursion is six times more predictable than terminal R because
it is a normalised measurement of the stop distance the system already chose, so every model that
learns it learns the geometry rather than the market — and the one genuine lever the census exposes,
that the 2R take-profit is the worst point on a frontier whose best point is 0.5R, is worth +0.04 R per
trade on the pool, needs no model at all, and is worth nothing on the book the funnel actually trades.*

---

## 1. What was built, and its fidelity receipts

### 1.1 The excursion census — the object the estate has never had

`f2_walk.py` walks the true-UTC M1 archive
(`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805`, 661 MB, 24 symbols) for every candidate
occurrence in the five sealed months **and the frozen bootstrap**. Its fill logic is copied **verbatim**
from `swarm2/lane2_receipts/walk.py`, which Lane 2 validated reproduces the sealed
`resolve_post_submission_m1_lifecycle` label at the 1× horizon. Only the post-fill scan is new: Lane 2
walked to the first of {stop, target}; F2 walks to the first of {stop, horizon} with **no take-profit
barrier**, so favourable excursion is not truncated at 2R.

Per filled trade it emits: `mfe` / `mfe_incl_stop` (running max, excl./incl. the stop bar),
`mae`, `t_mfe` (minutes from fill to the running-max bar), `mark_h1`/`mark_h2`, `stop_min`,
`stop_gross`, `mfe_capped_h1`, and **first-passage minutes for a 14-level ladder**
(0.25 … 6.0 R) with an intrabar-ordering ambiguity flag per level.

**Three fidelity checks, all exact** (`receipts/V1_CENSUS_FIDELITY.json`):

| check | result |
|---|---|
| **V1** dispositions vs Lane 2's walk | **identical in all five months** — FILLED 162,266, NO_FILL 493,688, and every censoring class to the row |
| **V2** target-capped MFE vs Lane 2's `h1.mfe` | **max abs diff 0.0 on all 162,266 filled trades**; 0 rows exceeding 1e-9 |
| **V3** sealed label reconstructible from the census | STOP **78,207 / 78,207**; `gross − deductible_cost_r == terminal_net_r` to **max abs diff 0.0** on every stop and every time-stop |

The one apparent residual is fully explained and is not an error. 1,598 of 30,737 sealed `TARGET` rows
do not clear the ladder's 2.0 level. **The take-profit is 2.0000 R from the ENTRY price for 100 % of
candidates in every month** (measured: one distinct value in 31,967 February rows) — but the ladder is
measured from the **fill** price, and a favourable fill puts the target nearer than 2R in fill-relative
terms. All 1,598 have an effective fill-relative target **strictly below 2.0**, max **1.9957**
(`receipts/`, `tgtresid` check). The census is exact; the two quantities are simply different.

### 1.2 The censoring gain, quantified

`F` (walker-filled) is **not** a subset of `R` (sealed-resolved). Across all seven month-groups the
walker fills **19,865 rows on which the shipped label does not exist at all** — 13,230 sealed
`CENSORED_ORDERING_AMBIGUITY` and 6,635 sealed `CENSORED_SOURCE_INTERVAL_GAP` — and **zero** rows go
the other way. Those rows have never entered any ridge the estate has fitted, because
`resolved_eligible` drops them.

That is a real gain and it is stated with its limit: for the 13,230 ordering-ambiguity rows the
intrabar order of the limit fill and the barrier is **genuinely unknown**, and the walker resolves it by
assumption. Every headline below is therefore reported on population **`B` = R ∩ F** — the exactly
matched set, 84,721 scored rows — so that no comparison is contaminated by rows only one label can see.

### 1.3 The estimator, and its receipt

F2 fits ~27 targets per scored day where B3 fit one. Ridge at a fixed α admits an exact shortcut:
targets sharing a training mask share one Cholesky factor, and an **expanding** training window makes
the sufficient statistics `X'WX, X'Wy, X'W1, X'1` additive, so each day adds its own rows to an
accumulator instead of re-reading the corpus. The full 100-day walk-forward over 27 targets runs in
**8 seconds**.

`f2_selftest.py` asserts this is the *same estimator*, not an approximation, against
`sklearn.linear_model.Ridge` on the same sparse one-hot + scaled-numeric layout, including the
different-mask grouping path: **max abs prediction difference 1.3e-10** across six cases
(`receipts/V2_ESTIMATOR_FIDELITY.json`).

**One declared deviation from B3.** B3 refits sklearn's `StandardScaler` on the expanding window each
day; F2 fixes it on the **frozen bootstrap** instead. Reason (1): the raw numeric columns span ~6 orders
of magnitude (`poi_age_hours` against `risk_fraction_of_entry`) and the centred Gram is not positive
definite in float64 at that spread. Reason (2): a bootstrap-only scaler is **strictly prior to every
scored day**, so it is causally cleaner than the thing it replaces. B6 measured the expanding-window
scaler leak at exactly **0.0000**, so nothing is given up.

### 1.4 Protocol

B3's, unchanged. 100 scored days in the frozen chain order; training on day *D* = the frozen bootstrap
(Oct/Nov 2025 dev + January 2026, **171,685 candidate rows re-extracted from the sealed sinks by
`f2_geom_bootstrap.py` so that F2's arms are not handicapped against their own control**) plus every
strictly prior day; sample weights are the frozen `1/(candidates in the row's decision window)` computed
inside each target's own training population; Ridge α = 10.0; **zero hyperparameter search**.

---

## 2. Stage L — the label information comparison

Two statistics, both out of sample, on the matched population `B`:

* **SELF** — within-decision-window Spearman between a label's prediction and its own truth.
  *Is MFE more predictable than terminal R?*
* **TRANSFER** — within-decision-window Spearman between the same prediction and **realized
  `terminal_net_r`**. *Does a model of MFE rank the economics better than a model of the economics?*

Within-window is the decision-relevant form: the funnel ranks **inside** a window, so a pooled
correlation credits between-window variation the selector can never act on. Pooled figures are reported
anyway.

| label | distinct values | pooled ρ | **OOS R²** | **SELF** ρ | **TRANSFER** ρ |
|---|---:|---:|---:|---:|---:|
| **`terminal_net_r`** (shipped) | 59,033 | 0.0225 | **−0.0105** | **0.0348** | **+0.0348** |
| **MFE** | 81,216 | 0.3001 | **+0.0800** | **0.2391** | **−0.0565** |
| MAE | 79,314 | 0.2464 | +0.0904 | 0.2154 | **+0.0964** |
| MFE/(&#124;MAE&#124;+0.05) | 81,740 | 0.1276 | +0.0053 | 0.1147 | −0.0289 |
| time-to-MFE | 119 | 0.3681 | **+0.1240** | **0.2643** | +0.0131 |
| MFE, target-capped | 81,061 | 0.3125 | +0.0942 | 0.2506 | −0.0461 |
| P(fill) | 2 | 0.6450 | +0.5227 | **0.5944** | **−0.1455** |

Receipt: `receipts/L1_LABEL_INFORMATION_base.json`.

**The premise is confirmed and the number is large.** MFE's within-window self-predictability is
**6.9× the shipped label's**, and the shipped label's out-of-sample R² is **negative** — its model does
worse than predicting the training mean. That is exactly the "label dominated by noise" signature the
commission described, and this is the first time the estate has measured it against an alternative on
identical folds.

**Paired head-to-head, transfer to realized net R** (day-clustered bootstrap, 4,000 draws, seed
20260812):

| challenger − `terminal_net_r` | Δ | CI95 | p |
|---|---:|---|---:|
| **MFE** | **−0.0913** | [−0.1085, −0.0741] | **0.000** |
| **MAE** | **+0.0616** | [+0.0430, +0.0801] | **0.000** |
| ratio | −0.0638 | [−0.0778, −0.0496] | 0.000 |
| time-to-MFE | −0.0217 | [−0.0464, +0.0027] | 0.087 |
| MFE, target-capped | −0.0809 | [−0.0970, −0.0647] | 0.000 |

**G1 as declared is PASSED on self-predictability and FAILED on the thing that matters.** MFE is
unambiguously the more predictable label; the model that predicts it is unambiguously the worse ranker.

### 2.1 Why — the mechanism, measured

MFE is denominated in R, i.e. **price move divided by the stop distance**. A tight stop mechanically
produces a large MFE. The fitted model discovers exactly that and essentially nothing else:

| | ρ with predicted MFE | ρ with predicted MAE |
|---|---:|---:|
| `stop_distance_atr` | **−0.7873** | +0.7030 |
| `risk_over_atr` | **−0.7826** | +0.7051 |
| `spread_r` | +0.4995 | −0.6239 |
| `cost_r` | +0.3012 | −0.4628 |
| `atr14_over_atr50` | +0.1498 | −0.0746 |
| `close_to_close_vol_8_over_48` | +0.0248 | −0.0306 |

Note the last two rows: the model is **not** finding volatility regime. It is finding the denominator.

And the quintile table settles it (`receipts/L4_MECHANISM.json`):

| predicted-MFE quintile | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| realized **MFE** | 0.604 | 0.895 | 1.186 | 1.490 | **1.968** |
| realized **MAE** | −0.516 | −0.646 | −0.678 | −0.710 | **−0.699** |
| realized **net R** | −0.095 | −0.127 | −0.078 | −0.085 | −0.080 |

The model orders MFE beautifully and monotonically over a 3.3× range. It orders MAE the same way. It
orders the economics **not at all**. Both excursions scale together with 1/stop-width; the ratio between
them — the only thing a fixed-geometry trade can monetise — never moves.

This is the whole result, and it is why "more information per sample" did not become "more edge": the
extra information is about the contract, not the market.

### 2.2 The MAE result, and its kill

MAE is the one excursion label that transfers **positively**, at **2.8× the shipped label**. Before
calling that a finding I ran B3's own most important test — the zero-model control — because B3 found a
single raw feature beat every arm it fitted.

Single features as ranking statistics, within-window transfer to realized net R
(`receipts/L2_CONTROLS_base.json`):

| ranker | ρ | CI95 |
|---|---:|---|
| `−swap_cost_r` | **+0.1407** | [+0.1085, +0.1737] |
| `poi_distance_to_midpoint_atr` | **+0.1380** | [+0.1162, +0.1600] |
| `poi_age_hours` | +0.1147 | [+0.0888, +0.1401] |
| **`−cost_r`** | **+0.1091** | [+0.0943, +0.1247] |
| **fitted MAE model** | +0.0964 | [+0.0828, +0.1106] |
| `distance_to_limit_atr` | +0.0650 | [+0.0495, +0.0809] |
| **fitted shipped model** | +0.0348 | [+0.0207, +0.0497] |

Paired on the identical windows (`receipts/L3_ZERO_MODEL_PAIRED.json`):

| comparison | Δ | CI95 | p | windows |
|---|---:|---|---:|---:|
| **MAE model − (−`cost_r`)** | **−0.0127** | [−0.0286, +0.0039] | **0.128** | 6,398 |
| shipped − (−`cost_r`) | **−0.0743** | [−0.0950, −0.0534] | 0.000 | 6,398 |
| MAE model − (−`spread_r`) | +0.0328 | [+0.0200, +0.0460] | 0.000 | 6,398 |
| MAE model − `stop_distance_atr` | +0.0322 | [+0.0182, +0.0472] | 0.000 | 6,398 |
| MAE model − `risk_over_atr` | +0.0342 | [+0.0203, +0.0489] | 0.000 | 6,398 |

**The fitted MAE model is statistically indistinguishable from ranking by cheapest cost, and worse on
the point estimate.** The mechanism confirms it from the other side: predicted-MAE quintiles map
monotonically onto mean `cost_r` (0.1407 → 0.1223 → 0.1092 → 0.0979 → **0.0814**).

And `cost_r` is not a new idea — it is **already the funnel's second sort key**
(`b3_lib.run_windows`: `available = [(p, -meta[i]["cost"], ...)]`) and already gate G1. The excursion
label rediscovered a control the estate has been running since before this lane existed.

The shipped model, by contrast, **loses to the same single feature by −0.0743 at p 0.000** — which is a
finding about the shipped rule, not about MFE.

---

## 3. Mandatory controls

| control | what it does | result |
|---|---|---|
| **T3 shuffle** | labels permuted **within each decision window**, models refit | MFE self ρ **0.2391 → 0.0410** (−83 %); MAE **0.2154 → −0.0776**; shipped **0.0348 → −0.0309**. **PASSES** — the self-predictability is real |
| **T5 embargo** | a row may enter training only once its label span closed strictly before the scored day (B3: 4.9449 % of rows are exactly +1 day late) | **nothing moves.** MFE 0.2391 → **0.2389**; MAE 0.2154 → 0.2136; every paired head-to-head within 0.003 of base. **PASSES** |
| **T4 permutation** | day-block label permutation, 200 draws | MAE observed +0.0964 vs null mean +0.0094 (sd 0.0045), p 0.000; MFE −0.0565 vs −0.0044, p 0.000. **Declared in advance as necessary and NOT sufficient** — a permutation null cannot see a leak present in every permutation |
| **T1 lag-one-day** | every feature vector replaced by the same symbol's most recent strictly prior scored-day vector | **NOT DIAGNOSTIC, and it says so itself: the control dies too.** Shipped self ρ **0.0348 → 0.0005**, MFE 0.2391 → 0.1354, MAE 0.2154 → 0.0442. A test that destroys the benchmark cannot discriminate. The reason is structural: the frozen 43 are **per-candidate predecision** quantities (B3's T0 audit traced each to bars strictly before the decision bar), not day-level aggregates. Lagging them substitutes a different candidate from a different day |
| **T2 intraday past/future split** | B6's decisive test | **has no analogue on this feature basis, and that is a positive statement, not an excuse.** B6's leak was a *same-day aggregate* (`trendshare` over all of a day's candidates, including ones generated hours later). **No feature in the frozen 43 is a same-day aggregate.** The applicable remnant — skill in the first vs second half of each day — is **stable**: MAE +0.1047 early / +0.0864 late; shipped +0.0288 / +0.0390; MFE −0.0789 / −0.0337. No concentration in the late half |
| **T3 leak audit (structural)** | prove no MFE-derived quantity is on the feature side | the feature set is asserted equal to `CAT0 + NUM0`; the walker writes labels to a **separate keyed artifact** joined only at fit time; no path-derived column exists in the design matrix by construction. Confirmed empirically by the shuffle above |
| **T6 reachability** | no adaptive-target claim at a level the clock cannot deliver | reported in full in §4 |
| **by order type** | B2's law: a ranker that merely sorts order types will look skilled | MAE +0.0724 on MARKET (n 41,147) and +0.0992 on LIMIT (n 43,574) — **present in both**, so it is not an order-type sort |

---

## 4. Stage P — the adaptive take-profit

`realized_R(i, k)` is **deterministic from the census** — no model touches the outcome, only the choice
of *k*. If level *k* is first-passed strictly before the stop bar and at or before the sealed 120-minute
horizon the trade books `+k`; else if the stop is hit inside the horizon it books the stop price
actually walked; else it marks to the last complete bar's close. Net = gross − `deductible_cost_r`.

**Policies, on all 91,843 filled-and-scored trades** (`receipts/P1_ADAPTIVE_TARGET_base.json`):

| policy | net R/trade | CI95 | hit rate | mean *k* | total R |
|---|---:|---|---:|---:|---:|
| **P-FIX2** — the shipped convention | **−0.0586** | [−0.0761, −0.0400] | 0.1864 | 2.00 | −5,381.5 |
| **P-FIXBEST** — best CONSTANT, re-chosen daily on prior data | **−0.0180** | [−0.0279, −0.0086] | 0.6451 | **0.46** | −1,654.7 |
| **P-ADAPT** — per-trade `argmax_k Ê[R(i,k)]` | −0.0204 | [−0.0333, −0.0065] | 0.4150 | 1.88 | −1,875.0 |
| P-MFEMAP — *k* nearest `Ê[MFE]` | −0.0547 | [−0.0731, −0.0349] | 0.3444 | 1.30 | −5,026.4 |
| *P-ORACLE (upper bound, never a claim)* | *+0.8648* | *[+0.8328, +0.8992]* | *0.7198* | *1.15* | *+79,430.3* |

**Paired, day-clustered:**

| comparison | Δ R/trade | CI95 | p |
|---|---:|---|---:|
| **P-ADAPT − P-FIX2** | **+0.0382** | [+0.0258, +0.0511] | **0.000** |
| **P-FIXBEST − P-FIX2** | **+0.0406** | [+0.0248, +0.0562] | **0.000** |
| **P-ADAPT − P-FIXBEST** | **−0.0024** | [−0.0116, +0.0071] | **0.60** |
| P-MFEMAP − P-FIXBEST | −0.0367 | [−0.0529, −0.0210] | 0.000 |

**G4 as declared is PASSED against the stated control and FAILED against the honest one.** The
adaptive target beats the fixed 2R convention by +0.0382 R/trade at p 0.000 — and beats a single
causally-chosen constant by **−0.0024, p 0.60**. An argmax over 14 noisy estimates is biased upward, so
"beats fixed 2R" was never the test; P-FIXBEST was, and it was declared in the prereg as such.

**The whole of the effect is that 2R is the wrong constant.** Under embargo (T5) the picture is
identical: P-ADAPT − P-FIX2 **+0.0390**, P-ADAPT − P-FIXBEST **−0.0016 (p 0.73)**.

### 4.1 The target frontier, and where the hit rate lands

| *k* | net R/trade | hit rate achieved | hit rate **required** | achieved − required |
|---:|---:|---:|---:|---:|
| 0.25 | −0.0201 | 0.7748 | 0.7944 | −0.0196 |
| **0.5** | **−0.0155** | 0.6108 | 0.6234 | **−0.0126** |
| 0.75 | −0.0217 | 0.4860 | 0.5012 | −0.0152 |
| 1.0 | −0.0302 | 0.3919 | 0.4104 | −0.0185 |
| 1.5 | −0.0441 | 0.2653 | 0.2868 | −0.0215 |
| **2.0 (shipped)** | **−0.0586** | **0.1864** | **0.2099** | **−0.0236** |
| 3.0 | −0.0731 | 0.1022 | 0.1238 | −0.0216 |
| 4.0 | −0.0782 | 0.0633 | 0.0814 | −0.0181 |
| 6.0 | −0.0895 | 0.0273 | 0.0417 | −0.0144 |

**The gap is negative at all fourteen levels.** There is no take-profit width at which this candidate
pool breaks even, and the shipped 2R target sits at the **worst** point of the frontier (−2.36 pp),
against a best of −1.26 pp at 0.5R.

This is the exit-side twin of Lane 2's stop-side result. Lane 2 measured the **stop** frontier and found
its limit ≈ 0.036 R/trade short of break-even; F2 measures the **target** frontier and finds its best
point −0.0155 R/trade. Two orthogonal geometry levers, both measured to their limit, neither reaching
zero.

### 4.2 The hit-rate question, answered precisely

The commission asks where this lands against "needs 41 %, achieves 32 %". Both numbers are recovered
and they turn out to be two different geometries (`receipts/P2_HIT_RATE_RECONCILIATION.json`, on all
162,266 fills):

* **32 %** is the 2R hit rate **ignoring the horizon** — F2 measures **32.11 %**, against Lane 2's
  independently-derived 31.88 %.
* **41 %** is the break-even for a ~1R geometry — F2 measures the required rate at *k* = 1.0 as
  **41.04 %**, achieved **41.19 %** with the horizon and 49.17 % without it.
* **At the contract the book actually runs** — a 2R target inside a 120-minute clock — the pool
  **needs 20.99 % and delivers 18.64 %.**

The honest statement is therefore *not* "we need 41 and get 32". It is: **at every target width the
achieved rate is 1.3–2.4 percentage points below the required rate, and the shipped width is the worst
one.** Closing 2.36 pp is what a positive book on this pool would cost.

### 4.3 A new fact about this pool

**The favourable excursion happens almost immediately: median time-to-MFE is 8 minutes** (p90 87 min)
inside a 120-minute contract. Mean MFE 1.4205 R, median 0.7442; mean MAE −0.7691.

That single number explains two prior results at once. It is why Lane 2 found a 128× range of exit
horizons worth at most +0.0034 R/trade — there is nothing left to collect after the first few minutes.
And it is why the target frontier peaks at 0.5R rather than 2R: what the pool reliably delivers is a
short, shallow favourable move, and the contract is written to demand a long deep one.

---

## 5. Stage E — does a better label produce a better book?

**No, and the mechanism is B2's law.** Ranking statistics through the frozen funnel
(`b3_lib.run_windows`, unmodified), booking the sealed `terminal_net_r`
(`receipts/E1_ECONOMICS_base.json`):

| arm | trades | book R | MARKET-top % | E1 /day | CI95 | p |
|---|---:|---:|---:|---:|---|---:|
| E-SHIP-F2 (control) | 181 | −6.73 | 5.34 | — | — | — |
| E-MFE-RAW | 27 | +1.40 | 0.30 | +0.0813 | [−0.2150, +0.3687] | 0.59 |
| E-MFE-EV | 13 | +2.49 | 0.30 | +0.0922 | [−0.1783, +0.3588] | 0.50 |
| E-MAE | 14 | −0.00 | 8.09 | +0.0673 | [−0.2074, +0.3402] | 0.64 |
| E-HURDLE-EV | 2,650 | −93.62 | 32.40 | −0.8689 | [−2.3271, +0.5844] | 0.24 |
| E-NEGCOST (ungated) | 1,389 | −59.71 | 15.08 | −0.5298 | [−1.2279, +0.2320] | 0.16 |

**G2 FAILS for every arm: not one CI excludes zero.** And the apparently positive arms are positive for
the reason B3 identified — they refuse to transact. E-MFE-EV's +2.49 R is **13 trades in 100 days**. Its
MARKET-top share is 0.30 % against the shipped rule's 5.34 %, and the `market_top_abstain` policy
therefore discards essentially every window. That is abstention, not skill, and its trade count makes
the book statistically meaningless.

At **matched trade counts** (PREREG_V1_2's rule, because the 0.10 floor is not scale-invariant):

| arm | N=50 | N=100 | N=181 (shipped) | N=300 | N=600 |
|---|---:|---:|---:|---:|---:|
| E-SHIP-F2 | −3.05 | −7.34 | −12.43 | −32.31 | −67.87 |
| E-MFE-RAW | +1.40 | +1.40 | +1.40 | +1.40 | +1.40 |
| E-MFE-EV | +3.66 | +3.66 | +3.66 | +3.66 | +3.66 |
| E-MAE | −2.96 | −4.54 | −9.18 | −13.34 | −18.95 |
| E-HURDLE-EV | +3.74 | +15.21 | +4.25 | −22.74 | −37.55 |
| E-NEGCOST | −1.40 | −2.11 | −9.22 | −9.99 | −29.74 |

The MFE arms are **flat across N** — they cannot produce more than 26–28 trades because their statistic
almost never puts a MARKET candidate on top. There is no N at which they are comparable to the shipped
rule, which is itself the answer.

### 5.1 The exit overlay — the only channel by which Stage P could reach a book

Keep the shipped ranker, change only the exit, on the 174 filled selections it makes:

| exit | trades | book R | +days / −days |
|---|---:|---:|---:|
| X-FIX2 (2R) | 174 | −10.905 | 29 / 41 |
| X-FIXBEST (causal best constant) | 174 | **−22.063** | 35 / 35 |
| X-ADAPT (per-trade) | 174 | **−23.943** | 28 / 42 |

| comparison | total R | per day | CI95 | p |
|---|---:|---:|---|---:|
| X-FIXBEST − X-FIX2 | **−11.158** | −0.1116 | [−0.3462, +0.1143] | 0.33 |
| X-ADAPT − X-FIX2 | −13.038 | −0.1304 | [−0.3183, +0.0539] | 0.16 |

**The change worth +0.0406 R/trade across 91,843 pool trades is worth −11.16 R on the 174 the funnel
selects, and the sign flips.** It is not statistically significant in either direction, which is itself
the point: 174 trades cannot resolve a 0.04 R/trade effect. **A better label that does not produce a
better book is a negative result, and this is one.**

The mechanism is not mysterious. The funnel's `market_top_abstain` gate admits only MARKET-top windows,
so the selected book is a tiny and deliberately unrepresentative slice of the pool the frontier was
measured on. Two of the three sleeves of evidence — pool-level frontier and book-level realisation —
simply do not meet.

---

## 6. Stage C — the censoring repair

No-fills are coded 0.0 and are the overwhelming majority of the shipped rule's argmaxes. The prereg
declared four arms modelling fill and excursion jointly rather than collapsing them
(`receipts/C1_CENSORING_REPAIR.json`, all 336,430 resolved scored rows):

| arm | self ρ | transfer to realized net R | CI95 |
|---|---:|---:|---|
| C-COLLAPSE — one regressor, no-fill → 0.0 | +0.4887 | **−0.1426** | [−0.1515, −0.1337] |
| C-HURDLE — `P̂(fill) × Ê[MFE│fill]` | +0.4549 | **−0.1359** | [−0.1444, −0.1271] |
| C-FILLONLY — `P̂(fill)` alone | — | **−0.1459** | [−0.1550, −0.1365] |
| shipped `terminal_net_r` | +0.0926 | **+0.0926** | [+0.0841, +0.1011] |

| paired | Δ | CI95 | p |
|---|---:|---|---:|
| **hurdle − collapse** | **+0.0067** | [+0.0047, +0.0088] | **0.000** |
| **hurdle − shipped** | **−0.2284** | [−0.2436, −0.2128] | 0.000 |

**G5 FAILS, and the two halves fail in opposite directions.** The hurdle *is* the better estimator — it
beats the collapse significantly, exactly as the censoring argument predicts. And it is a far worse
decision rule, because **every statistic that models fill correctly ranks fillable candidates highly,
and filling is the adverse event.**

This is B2's law reproduced on a fourth, independent label, by a lane that set out to overturn it: the
collapsed label transfers at −0.1426, the hurdle at −0.1359, `P̂(fill)` alone at −0.1459 — a 0.007 spread
across three structurally different estimators, all strongly negative, against the shipped label's
+0.0926. The estate's ranking problem is not an estimator-structure problem.

---

## 7. What this lane refutes, what it leaves standing, and the nearest unrefuted variant

**Refuted, with numbers.**

1. **"MFE is a better training target."** It is a better *target* and a worse *ranker*, because in R
   units it measures the stop distance (ρ −0.787) rather than the market. −0.0913 against the shipped
   label, p 0.000.
2. **"The target should be chosen per trade."** The per-trade choice adds −0.0024 (p 0.60) over a single
   constant chosen causally.
3. **"Modelling fill and excursion jointly repairs the censoring."** It repairs the estimator
   (+0.0067, p 0.000) and degrades the decision (−0.2284).
4. **"MAE ranking is a new edge."** Indistinguishable from `−cost_r` (p 0.128), which is already the
   funnel's tiebreaker.

**Left standing, and worth carrying forward.**

1. **The 2R take-profit is the worst point on a 14-level frontier** whose best is ≈ 0.5R, worth
   +0.0406 R/trade on 91,843 pool trades at p 0.000, **needing no model**. It does not survive contact
   with the 174-trade selected book, but it is a property of the *pool*, and any future rule that trades
   the pool more broadly inherits it. This is the single most actionable thing in the lane.
2. **Median time-to-MFE is 8 minutes.** This is new, it explains Lane 2's null horizon result and the
   0.5R frontier peak, and it is a hard constraint on any future exit design.
3. **19,865 filled trades carry an excursion label where the shipped label does not exist at all.**
   Any future outcome model can use them; the shipped ridge structurally cannot.
4. **The shipped ridge loses to `−cost_r` by −0.0743 at p 0.000.** That is a finding about the rule now
   in the record, produced incidentally here and consistent with Lane 3's G3 anti-selectivity.

**The nearest variant this lane did NOT refute, stated precisely so it is not over-read.**

Every excursion label F2 tested is denominated in **R** — divided by the stop distance — and §2.1 shows
that is precisely why they carry geometry rather than edge. **The un-normalised excursion, denominated
in ATR or in price, has not been measured by anyone.** It is a different quantity: MFE/ATR asks "how far
does this instrument move after this signal", with the system's own stop choice divided out. That is the
question the commission was reaching for, and the census already on disk contains the inputs to answer
it — `f2_walk.py` emits `risk` per trade, so `mfe_atr = mfe × risk / atr` is a join away, requiring no
new walk.

It is filed, not claimed. Its prior should be poor: Lane 2 measured this pool's directional edge at
+0.0282 R/trade against 0.2659 R/trade of cost, and no re-denomination of a label changes a 9.4:1 ratio.
But it is the one arm the mechanism in §2.1 does not already kill, and it is cheap.

---

## 8. Declared arms, and their disposition

| arm | declared in | status |
|---|---|---|
| L-TNR, L-MFE, L-MAE, L-RATIO, L-TMFE, L-MFEC | §stage_L | all six completed, §2 |
| P-FIX2, P-FIXK (×14), P-FIXBEST, P-ADAPT, P-MFEMAP, P-ORACLE | §stage_P | all completed, §4 |
| P-ADAPT-M (monotone-constrained) | §stage_P | **NOT RUN.** P-ADAPT already failed against P-FIXBEST at p 0.60; a constrained variant of a refuted arm cannot rescue it. Declared here as not run rather than quietly dropped |
| E-SHIP, E-MFE-EV, E-MFE-RAW, E-MFE-RANK | §stage_E | completed as E-SHIP-F2 / E-MFE-EV / E-MFE-RAW and the `ungated` column, §5 |
| C-COLLAPSE, C-HURDLE, C-HURDLE-EV, C-FILLONLY | §stage_C | all four completed, §5–6 |
| T1, T2, T3, T4, T5, T6 | §mandatory_controls | all six reported, §3; T1 and T2 reported as **non-diagnostic on this feature basis with the reason stated** |
| HGB secondary (all stage-L labels) | §stage_L | **NOT RUN.** The incremental-sufficient-statistics shortcut that makes 27 daily-refit targets affordable does not exist for a boosted tree; 200 HGB fits on up to 480k rows was not affordable in this lane. B3 measured HGB strictly worse than Ridge at every label it tried (−188 R shipped label, −93 R composed), so the expected direction is known. Declared as not run |

**Multiplicity.** 6 label arms × 2 populations, 6 policy arms + 14 constants, 6 economic arms × 2 gates
× 5 matched counts, 4 censoring arms, 29 zero-model controls, 4 walk-forward variants. **Zero
hyperparameter searches; zero estimator specifications tuned.** No arm is admitted, so no multiplicity
correction is load-bearing — but the count is recorded because a lane that admitted something on this
surface would owe one.

---

## 9. Addendum — the F1 reconciliation and the ratio arm

Commissioned mid-flight after F1 landed. Amendment `f2_mfe_label/PREREG_V1_1.json`, payload sha256
`b5f23aa4e9d20104e8baede4d280273d7774ba33077a56eb423a403547932e3f`, which records that **L-RATIO was
already frozen in `PREREG_V1`** and that only the *joint* construction is new. Receipts:
`receipts/R1_F1_RECONCILIATION_AND_RATIO_ARM.json`, `receipts/R2_F1_COLUMN_IDENTIFICATION.json`.

### 9.1 F1's headline reproduces exactly — from the `_full` columns, not the trade's own excursion

Recomputed from F1's own parquet, cells = (family × symbol) with n ≥ 150:

| column pair | pooled ratio | cells | corr(MFE, &#124;MAE&#124;) | corr(MFE, net R) | corr(ratio, net R) | share ratio>1 |
|---|---:|---:|---:|---:|---:|---:|
| **`mfe_full_r` / `mae_full_r`** | **0.9044** | **164** | **+0.9632** | **−0.6135** | **+0.4591** | **0.1951** |
| `mfe_r` / `mae_r` (the trade's own excursion) | 1.0124 | 164 | **+0.0429** | **+0.2527** | +0.7640 | 0.4939 |
| `mfe_pre_exit_r` / `mae_pre_exit_r` | 1.2380 | 162 | −0.3061 | +0.3390 | +0.6200 | 0.6910 |

All five of F1's reported figures match `mfe_full_r`/`mae_full_r` to three decimals. **The finding is
real and it is about a different quantity than the one a trained model would target.** `mfe_full_r`
means favourable travel over the **whole 120-minute window regardless of when the trade exited**
(mean +2.088 R against the in-trade +0.936). Total up-travel and total down-travel over a fixed window
are nearly the same variable by construction — both are approximately volatility × √time — which is why
r = +0.963 and why cells with more of it earn less after a fixed cost.

**On the excursion the trade actually experiences, the premise does not hold: r = +0.0429, not +0.963,
and corr(mean MFE, mean net R) is +0.2527, not −0.613.** So the stated mechanism — "a model that
predicts MFE will select high-|MAE| along with it, *because the two are r = 0.963*" — is not the
mechanism operating on the trainable label.

This lane found the same conclusion by a different and independent route, and §2.1 is the version that
survives: the MFE model does select high-|MAE| along with high-MFE, but the coupling is **not** in the
outcome — realized MFE and realized |MAE| correlate **−0.41** at trade level. It is in the *predictions*
(ρ +0.7825), because both are dominated by the same predecision feature: **1/stop-width**
(ρ −0.787 with `stop_distance_atr`). The trap is real; it is a geometry trap, not a volatility trap.

### 9.2 The correlations F1 reports cannot answer the selection question, and F2's do

Every F1 correlation cited is **realized-versus-realized**. On a barrier trade `corr(realized MFE,
realized net R) = +0.628` is close to tautological: a trade that reaches the target *has* MFE ≥ 2R and
net R ≈ +2R — the same event is being measured twice. Aggregation level does not repair this; it only
changes the sign, which is why the three levels disagree:

| | corr(MFE, &#124;MAE&#124;) | corr(MFE, net R) | corr(ratio, net R) |
|---|---:|---:|---:|
| cell-level, 164 cells (`mfe_r`) | +0.043 | +0.253 | +0.764 |
| trade-level, 146,736 trades | **−0.415** | +0.628 | +0.741 |
| within-cell, mean over 164 cells | −0.483 | +0.673 | +0.754 |

The admissible test is out-of-sample **prediction** against outcome. That is Stage L, and it was already
run on the ratio.

### 9.3 The ratio arm — both constructions, same folds (R2)

Within-window transfer to realized net R, matched population, 84,721 rows:

| ranker | ρ | CI95 | p |
|---|---:|---|---:|
| shipped `Ê[net R]` | **+0.0348** | [+0.0207, +0.0497] | 0.000 |
| `Ê[MAE]` | +0.0964 | [+0.0828, +0.1106] | 0.000 |
| **L-RATIO** `Ê[MFE/&#124;MAE&#124;]` (pre-registered) | **−0.0289** | [−0.0435, −0.0144] | 0.000 |
| **JOINT-RATIO** `Ê[MFE]/&#124;Ê[MAE]&#124;` (new) | **−0.0322** | [−0.0494, −0.0151] | 0.000 |
| `Ê[MFE]` | −0.0565 | [−0.0733, −0.0399] | 0.000 |

| paired | Δ | CI95 | p |
|---|---:|---|---:|
| **JOINT-RATIO − `Ê[MFE]`** | **+0.0242** | [+0.0190, +0.0297] | **0.000** |
| **L-RATIO − `Ê[MFE]`** | **+0.0276** | [+0.0177, +0.0374] | **0.000** |
| JOINT-RATIO − shipped | **−0.0671** | [−0.0829, −0.0512] | 0.000 |
| L-RATIO − shipped | **−0.0638** | [−0.0778, −0.0496] | 0.000 |

**The commission's direction is right and its magnitude is insufficient.** Ranking on the ratio rather
than the level is worth **+0.024 to +0.028** at p 0.000 — it recovers roughly 40 % of the gap between
`Ê[MFE]` and the shipped label — and it **still does not cross zero**, remaining −0.064 to −0.067 worse
than the label it was meant to replace. Identical under the one-day embargo (+0.0223 / +0.0272).

The two constructions are statistically indistinguishable from each other, which is itself informative:
predicting the ratio and taking the ratio of predictions give the same answer, so nothing is being lost
to estimator structure.

### 9.4 Priced in R per trade, against 0.2868 (R3)

No rank correlation is reported here without the economics it implies. Realized net R per trade on each
ranker's **own top decile per decision window**, already net of `deductible_cost_r`:

| ranker | net R/trade | CI95 | n | still needs |
|---|---:|---|---:|---:|
| **JOINT-RATIO** | **−0.0068** | [−0.0780, +0.0661] | 4,771 | **+0.0068** |
| L-RATIO | −0.0306 | [−0.0853, +0.0255] | 4,771 | +0.0306 |
| `Ê[MAE]` | −0.0427 | [−0.0728, −0.0104] | 4,771 | +0.0427 |
| `Ê[MFE]` | −0.0462 | [−0.1146, +0.0210] | 4,771 | +0.0462 |
| shipped `Ê[net R]` | −0.0566 | [−0.1071, −0.0042] | 4,771 | +0.0566 |

**The joint-ratio top decile at −0.0068 R/trade is the closest any arm in this lane comes to break-even,
and its CI contains zero — so the honest statement is "indistinguishable from break-even", not
"positive".** It is also the one arm whose confidence interval is wide enough to contain the shipped
rule, so it does not beat it either. Note the tension with §9.3 and read both: the ratio arm has *worse*
average within-window rank skill and a *better* tail, which is what a statistic that concentrates cheap
high-ratio trades into its top decile looks like.

Against F1's frame: the pool's barrier-free directional edge is **+0.0301 R/trade** against an all-in
cost of **0.2868 R**, a ratio of **9.5:1**. Nothing in this lane closes that. The best selected
subpopulation F2 can construct is −0.0068 R/trade net, i.e. it needs **+0.0068 R/trade** more to break
even — which is small in absolute terms only because the top-decile selection has already recovered most
of the pool's −0.0586 R/trade deficit through cost selection, not through excursion prediction.

### 9.5 Not done

`AA_ESTATE_TRADES.json.gz`'s 22,324 per-trade MFE/MAE rows were **not** mined as a second corpus. They
are a different population (the armed sleeve estate, not the funnel candidate pool), so they cannot
cross-check these folds — they would be a separate replication on a separate question, and this lane's
result does not turn on sample size. Filed as available and untouched.

---

## 10. Receipts

| file | contents |
|---|---|
| `f2_mfe_label/PREREG_V1.json` (+`.sha256`) | the frozen pre-registration, `8b038d86…` |
| `receipts/V1_CENSUS_FIDELITY.json` | dispositions vs Lane 2, MFE reproduction, sealed-label reconstruction |
| `receipts/V2_ESTIMATOR_FIDELITY.json` | MultiRidge ≡ sklearn Ridge, max diff 1.3e-10 |
| `receipts/L1_LABEL_INFORMATION_{base,emb1,lag1,shuf}.json` | Stage L, all four walk-forward variants |
| `receipts/L2_CONTROLS_base.json` | 29 zero-model rankers, permutation null, intraday split, order-type split |
| `receipts/L3_ZERO_MODEL_PAIRED.json` | paired fitted-vs-single-feature comparisons |
| `receipts/L4_MECHANISM.json` | the 1/stop-width mechanism and the quintile tables |
| `receipts/P1_ADAPTIVE_TARGET_{base,emb1}.json` | the target frontier and every policy |
| `receipts/P2_HIT_RATE_RECONCILIATION.json` | hit rates with and without the horizon, excursion distributions |
| `receipts/C1_CENSORING_REPAIR.json` | the hurdle arms |
| `receipts/E1_ECONOMICS_base.json` | the funnel books, E1, matched-N, exit overlay |
| `f2_mfe_label/PREREG_V1_1.json` (+`.sha256`) | the mid-flight amendment, `b5f23aa4…` |
| `receipts/R1_F1_RECONCILIATION_AND_RATIO_ARM.json` | three aggregation levels, both ratio arms, top-decile economics |
| `receipts/R2_F1_COLUMN_IDENTIFICATION.json` | which F1 columns reproduce its headline |

Code: `f2_walk.py` (census), `f2_geom_bootstrap.py` (bootstrap geometry), `f2_validate.py`,
`f2_selftest.py`, `f2_lib.py`, `f2_walkforward.py`, `f2_stageL.py`, `f2_controls.py`, `f2_stageP.py`,
`f2_stageE.py`, `f2_ratio_arm.py`. Census artifacts (~70 MB) are in job scratch at
`/Users/borr/.claude/jobs/adb9e69b/tmp/f2/`, not committed.
