# B3 — the selector, rebuilt: R1, R2, R3 measured, and the metric that judged them broken

**Breakthrough Lane 3 — a BUILD lane.** Lane 3's audit established that the shipped ranker is
*significantly worse than random* at the decision point and that **+1.436 R/window** of within-window
separability sits inside the same windows, of which it captures none. This lane built the best selector
the data supports — **23 declared walk-forward arms** across four label structures and four model
families, plus four zero-model controls — and validated them out of sample under a discipline frozen
before looking. **17 arms have completed all 100 scored days**; the remaining six are still refitting and are
named, with their prediction, in §8.

**Everything below is measurement.** No broker, no VPS, no config, no decision-contract-bound file, no
git operation. Computation ran from the sealed row cache and the job scratch.

---

## 0. The answer in eight lines

| # | finding | number |
|---|---|---|
| **1** | **R1 is CLOSED NEGATIVE, and B3 measured it independently before being told.** The composed fill-conditional statistic `P̂(fill)·Ê[net│fill]` cleared **both** of Lane 3's pre-registered reversal bars by >2×, at p < 0.001, on the development months and the confirmation months separately — **and booked −95.93 R against the shipped rule's +0.954 R.** | P(pick winner) **0.1863** vs bar 0.0862; P(pick best) **0.0579** vs bar 0.0264; paired-vs-shipped **−96.89 R, p 0.006** |
| **2** | **The pre-registered metric is structurally broken on this population, and B3's own passing arm is the proof.** A `RESOLVED_NO_FILL` books exactly 0.0 and can never be "positive", so every hit-rate metric mechanically rewards *filling* — and filling is the adverse event. | the book is **monotone in MARKET-top share**: 2.1 % → +2.32 R, 2.8 % → −7.03, 7.1 % → +0.95, 24.4 % → −96.89, 75.2 % → **−605.76** |
| **3** | **THE ADVERSARIAL KILL — and it is this lane's most important result.** The A1 family's positive selection term is **entirely the decision not to transact**, and a **zero-model, single-feature control reproduces it**: ranking by `distance_to_limit_atr` descending scores **+0.0215 R/window**, beating every fitted arm except one and matching an outcome-informed abstention picker (+0.0214). | C2 **+0.02150** vs A1 +0.01299, A10 +0.00687, shipped +0.00066 |
| **4** | **Conditional on actually trading, the selector is significantly WORSE than a random draw from its own window.** This holds for the shipped rule and for most rebuilds. | selection term on FILLED picks: shipped **−0.0828 (p 0.045)**, A0 **−0.0866 (p 0.034)**, A10 **−0.1181 (p 0.041)**, A2 **−0.0553 (p 0.022)** |
| **5** | **THE LAW: the book is a linear function of how often the selector transacts.** Across all 17 completed arms — four label structures, four model families, statistics spanning three orders of magnitude — realized book R against MARKET-top share is **r = −0.9786**. Nothing else in this study explains anything by comparison. | Pearson **r −0.9786, p 1.0e-11**; Spearman −0.7353 (p 7.7e-04); range 2.1 % → +2.32 R down to 75.4 % → **−691.77 R** |
| **6** | **Capacity makes it WORSE, and the learning curve is INVERTED.** Ridge→HGB at an identical label costs −188 R (shipped label) and −93 R (composed); the *monotone-constrained* HGB beats the free one by +68 R. Training on the most recent **25 %** of rows roughly doubles the selection term against training on 100 %. | A0→A3 **−2.36 → −190.49 R**; A2→A5 −96.89 → −189.85; A5→A6 −189.85 → **−121.37**; train fraction 12.5/25/50/100 % → **+0.0205 / +0.0291 / +0.0177 / +0.0130** |
| **7** | **Q3 CONFIRMED independently: 4.94 % of rows carry a label that closes after the day they are absorbed with — and every one of them is exactly one day late.** One embargo day removes 100 % of it. **The estate's one positive selection term survives the embargo.** | 23,790 / 481,098 = **0.049449**, all at +1 day; A1 +0.01299 (p 0.034) → **A1E +0.01255 (p 0.035)** → A1E7 (7-day) +0.01086 (p 0.077) |
| **8** | **T0 — the feature-provenance audit the estate had never run: the frozen 43 basis is causally clean.** Verified at source and confirmed empirically. One artifact found: `expected_slippage_r` is a **constant 0.02** in all 427,232 LIMIT rows. | 15 source + 7 cost/fillability + 14 identity + 7 POI, all classified |

**The one-sentence conclusion.** *Every repair Lane 3 ranked works as an estimator and none of them works as
a book: the selector's only measurable skill is declining to transact, one feature with no model does that
better than all but one of the fitted arms, and conditional on transacting the selector is significantly
worse than chance — so the ceiling is not reachable by ranking this candidate pool at all.*

---

## 1. Discipline, fixed before looking

Four pre-registrations, each hashed and frozen before the outcomes it governs were read. **Nothing was
edited after freezing**; later documents supersede and the superseded text stays readable.

| file | payload sha256 | froze |
|---|---|---|
| `PREREG_V1.json` | `9d53ab7275c2ee475e250a3322afd7fe52fd1d11b1e709421f4c2201730e96ab` | 12 arms, every hyperparameter, the walk-forward protocol, metrics P1/P2/P3, the 0.0862/0.0264 bars, the DEV/CONF arm-selection split, seed 20260812 |
| `PREREG_V1_1.json` | `70c5e8d751484feeed13bc05dda247587458e807bb4b8708a0cf2994344b6167` | temporal tests T0–T3 as **pass conditions**; two known-leaky negative-control arms; the standing rule that **a permutation null may never be cited as evidence of causality** |
| `PREREG_V1_2.json` | `733c821cffcd88f0e7c5eadcca76f99b658a1dd0d0379f889a17793daee2e49d` | the fill×cost ablation, the derived fill-probability controls, and the **matched-trade-count** rule for all cross-arm economics |
| `PREREG_V1_3.json` | `3b3a927ad8f39d997eae267a8b1e10fa9362bd1e247144bda65e9810461f2227` | **the economic gate replacing the invalid hit-rate gate**; primary metric E1 (per-day paired difference vs the shipped rule); the Q3 embargo test |

`PREREG_V1_1` records a fact that mattered: **B3's regime block was already lag-one-day**
(`b3_lib.add_regime_features` reads `day_reg[days[i-1]]`), written before the Lane 6 kill was announced.
B3's regime arms are therefore the *causally clean* variant, and their expected result — nothing — was
recorded in advance.

`PREREG_V1_3` was frozen after B3 had reproduced the hit-rate pathology on its own instrument but
**before any paired economic statistic or embargo result was computed**.

### 1.1 The walk-forward

105 declared sealed trading days, of which **100 carry candidates** (2026-04-03, 04-06, 05-01, 05-04,
05-25 are market holidays with zero eligible rows). On each day every model is **refitted from scratch**
on the bootstrap (Oct/Nov 2025 development + January 2026, hash-verified through
`ReplayCompactEventSink.open_sealed`) plus every strictly prior day, then predicts that day's candidates.
Training grows 98,917 → 481,098 eligible rows. Sample weights are the frozen rule's own
`1/(candidates in the row's decision window)`. Hyperparameters are constants in `b3_lib.py`:
Ridge α = 10.0 `lsqr` (inherited verbatim); HGB `max_iter` 300, `lr` 0.06, `max_leaf_nodes` 31,
`min_samples_leaf` 100, `l2` 1.0, no early stopping. **Zero hyperparameter search.**

**Neither reserve day (2025-10-31, 2025-11-05) and none of the four never-read 2025 windows
(june/august/september/december 2025) is touched by any part of this lane.**

### 1.2 The instrument is validated, not assumed

Replaying Lane 3's sealed daily predictions through **B3's own funnel** reproduces the sealed record:

| quantity | sealed / Lane 3 | B3 funnel |
|---|---|---|
| dispositions | 6,988 / 1,959 / 290 | **6,988 / 1,959 / 290** |
| book actual / worst case | +0.954 / −7.263 | **+0.954364 / −7.263306** |
| P(pick winner) / baseline | 0.07224 / 0.08620 | **0.0722 / 0.0862** |
| P(pick best) / baseline | 0.018446 / 0.026410 | **0.0184 / 0.0264** |
| within-window selection term | +0.00066, p 0.897 | **+0.00066, p 0.917** |
| windows reaching the ranker | 9,237 | **9,237** |
| ceiling table: ORACLE / RANDOM / PICK / RANK2 / ANTI-ORACLE | +1.43648 / −0.03688 / −0.02298 / −0.01904 / −1.03062 | **identical to five decimal places** |
| Feb / Apr / May / Jun / Jul | +14.168 / −7.742 / +5.130 / +3.964 / −14.566 | **identical** |

An independent refit of the shipped ridge (arm **A0**) lands at book −1.41 against +0.954 — one trade
different out of 290, from `lsqr`'s iterative tolerance. That gap bounds the numerical noise on every
number here.

---

## 2. T0 — the feature-provenance audit

**`PREREG_V1_1` made this a pass condition. The estate had never run it.** Receipt:
`b3_selector/T0_FEATURE_PROVENANCE_AUDIT_V1.json`.

| block | n | verdict |
|---|---:|---|
| M15 source features | 15 | **CLEAN.** Every helper read at source: `_prior_high/_prior_low` slice `bars[start:index]` (exclusive of the decision bar); `_close_position` `bars[start:index+1]`; `_close_to_close_vol` `range(index-lookback+1, index+1)`; `_trend_state` uses `bars[index]` and `bars[index-20]`; `_previous_trend_state` uses `index-1`; `_bars_since_session_open` walks *downward*. **No forward index anywhere** |
| cost + fillability | 7 | **CLEAN, decisively.** All from `source_row` (the predecision cost model) at `candidate_funnel_analysis.py:221-223`, `:164-166`. The decisive evidence: these fields vary continuously *within* the `RESOLVED_NO_FILL` class — **142,403 distinct `cost_r` values across 317,167 LIMIT rows whose orders never executed.** A realized-execution quantity cannot exist for an order that never filled |
| categorical identity | 14 | decision-time state only |
| POI state | 7 | taken as emitted; **not verified at generator level by this lane** — flagged, not claimed |

**Found anyway.** `expected_slippage_r` is a **constant 0.02** across all five months and every outcome
class — one distinct value in 427,232 LIMIT rows: a modelling assumption wearing a measurement's name.
And the audit does **not** clear the label:
`terminal_net_r = terminal_gross_r − (expected_slippage_r + swap_cost_r + commission_r)`, so the
deductible under every economic number in this programme is a **predecision estimate**, 0.02 R of it a
constant.

**Association is not leak.** `distance_to_limit_atr` is 6.05 in NO_FILL against 1.52 in TARGET — that is
the legitimate causal direction. The leak test is whether the value was knowable at decision time; it was.

### 2.1 Q3 — the label-availability leak, confirmed independently

A sibling lane reported that the frozen chain absorbs a day's rows wholesale, so ~5 % of training rows
carry labels that close later. **Measured on B3's own basis: 23,790 of 481,098 rows = 4.9449 %, and every
single one is exactly +1 day late.** One embargo day removes 100 % of it.

`A1E` refits the surviving arm with the embargo (a row may enter training only once its label span closed
strictly before the scored day begins); `A1E7` uses a deliberately over-strict 7-day embargo.

| arm | selection term | CI95 | p | ceiling capture |
|---|---:|---|---:|---:|
| A1 (no embargo) | +0.01299 | [+0.0010, +0.0244] | 0.034 | +0.0186 |
| **A1E (1-day embargo)** | **+0.01255** | [+0.0008, +0.0238] | **0.035** | +0.0183 |
| A1E7 (7-day embargo) | +0.01086 | [−0.0011, +0.0233] | 0.077 | +0.0171 |

**The estate's one positive selection term is not a label-availability artifact.** It survives at −3 % of
its value. The 7-day control weakens it to the edge of significance, which is expected from dropping a
further week of the most recent (and, per §5, most valuable) training rows.

---

## 3. The arms

| id | training population | model | decision statistic |
|---|---|---|---|
| A0 | resolved-eligible, `terminal_net_r` | Ridge | ŷ — **shipped control** |
| A1 | **filled only** | Ridge | Ê[net│fill] — **R1, linear** |
| A2 | filled + fill-LPM | Ridge ×2 | **P̂(fill)·Ê[net│fill]** — R1 composed |
| A3–A7 | resolved / filled / win-label | HGB, HGB-monotone, HGB-clf | capacity, R1, monotone, P̂(win) |
| A8 | **all eligible incl. censored**, 5-class | HGB multiclass | Σ p_k(c_k − cost) — **R3 done properly** |
| A9 | filled, IPC-weighted | HGB ×3 | P̂(fill)·Ê[net│fill] — R3 by IPCW |
| A10 / A11 | filled + regime (**lag-1**) | Ridge / HGB | Lane 6 block, causally clean |
| A10L / A11L | filled + regime (**same-day**) | Ridge / HGB | **known-leaky negative controls** |
| A10P / A10F | filled + regime (past / future half) | Ridge | **T2 past/future split** |
| A12 / A12H | filled, **cost+fillability basis only** | Ridge / HGB | fill×cost ablation |
| A1E / A1E7 | filled, **label-availability embargo** | Ridge | Q3 |
| A1_f0125/f025/f05 | filled, most-recent fraction | Ridge | learning curve (diagnostic) |
| C1 / C2 | — | **none** | abstention oracle / `distance_to_limit_atr` — **zero-model controls** |

---

## 4. Results — the economic gate (PREREG_V1_3 primary)

Day-clustered bootstrap, 4,000 draws, trading day the cluster unit, seed 20260812. E1 is the per-day
paired difference in realized book R against the shipped rule over the same 100 days.

| arm | trades | book R | **E1 sum** | E1 p | selection term | p | DEV | CONF | capture | MKT-top % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1_f025 ᴰ | 172 | -6.07 | **-7.03** | 0.692 | +0.02906 | 0.000 | +0.03160 | +0.02555 | +0.0297 | 2.84 |
| A1_f0125 ᴰ | 128 | +3.27 | **+2.32** | 0.924 | +0.02054 | 0.000 | +0.02267 | +0.01760 | +0.0242 | 2.10 |
| A1_f05 ᴰ | 176 | -17.95 | **-18.90** | 0.381 | +0.01774 | 0.001 | +0.01380 | +0.02319 | +0.0221 | 2.90 |
| **A4 · HGB fill-cond** | 274 | -45.64 | **-46.60** | 0.093 | +0.01519 | 0.024 | +0.01658 | +0.01325 | +0.0180 | 3.32 |
| **A1 · R1 ridge** | 116 | -28.66 | **-29.62** | 0.112 | +0.01299 | 0.034 | +0.01028 | +0.01680 | +0.0186 | 1.92 |
| A1E · embargo | 116 | -31.87 | **-32.82** | 0.081 | +0.01255 | 0.035 | +0.00896 | +0.01759 | +0.0183 | 1.91 |
| A1E7 · 7-day | 132 | -11.18 | **-12.13** | 0.530 | +0.01086 | 0.077 | +0.00491 | +0.01929 | +0.0171 | 2.27 |
| A10 · regime lag-1 | 177 | -18.05 | **-19.00** | 0.348 | +0.00687 | 0.270 | +0.00299 | +0.01221 | +0.0143 | 2.83 |
| **SHIPPED (sealed)** | 290 | +0.95 | **+0.00** | — ᴿ | +0.00066 | 0.917 | +0.00137 | -0.00035 | +0.0094 | 7.06 |
| A0 · shipped refit | 289 | -1.41 | **-2.36** | 0.511 | -0.00018 | 0.998 | +0.00126 | -0.00218 | +0.0088 | 7.07 |
| A6 · HGB mono | 2214 | -120.42 | **-121.37** | 0.054 | -0.01216 | 0.392 | -0.00278 | -0.02508 | -0.0020 | 26.23 |
| **A2 · R1 composed** | 1230 | -95.93 | **-96.89** | 0.006 | -0.01586 | 0.175 | -0.00115 | -0.03487 | -0.0027 | 24.41 |
| **A3 · HGB shipped label** | 2515 | -189.53 | **-190.49** | 0.003 | -0.01663 | 0.203 | -0.02092 | -0.01070 | -0.0049 | 31.67 |
| A5 · HGB composed | 2292 | -188.90 | **-189.85** | 0.000 | -0.02837 | 0.046 | -0.01666 | -0.04443 | -0.0133 | 27.12 |
| A7 · HGB P(win) | 5722 | -446.69 | **-447.65** | 0.000 | -0.04081 | 0.001 | -0.02188 | -0.06634 | -0.0242 | 62.38 |
| PFILL ridge ᶜ | 6928 | -604.81 | **-605.76** | 0.000 | -0.06527 | 0.000 | -0.06335 | -0.06789 | -0.0427 | 75.21 |
| PFILL hgb ᶜ | 6934 | -690.82 | **-691.77** | 0.000 | -0.07399 | 0.000 | -0.07706 | -0.06973 | -0.0496 | 75.38 |

ᴰ learning-curve **diagnostic** arm — declared as such in `PREREG_V1`, may not carry a verdict.
ᴿ the reference arm: E1 is defined against it, so its own difference is identically zero.
ᶜ derived **control**, not a candidate. Reference arms on the same 9,237 windows: ORACLE **+1.43648**,
RANDOM −0.03688, ANTI-ORACLE −1.03062.

**No arm produces a significantly positive E1. Not one.** The only positive point estimate
(A1_f0125, +2.32 R) has p 0.924 — indistinguishable from the shipped rule. **Four fitted arms and both
fill-probability controls are significantly negative** (A2 p 0.006, A3 p 0.003, A5 p 0.000, A7 p 0.000,
PFILL ×2 p 0.000) — and every one of the six trades between 4× and 24× as often as the shipped rule.

### 4.1 R1 as Lane 3 specified it: closed negative

`E[net] = P(fill)·E[net│fill]` is an **identity**, not a repair. Factoring it improves the estimator and
destroys the book, for a mechanical reason B3 can now show directly: multiplying a LIMIT candidate by
`P̂(fill)` shrinks it toward zero while a MARKET candidate keeps `P(fill) ≡ 1`, so the argmax migrates to
the MARKET population — which Lane 3 measured as the worst rule in its whole ceiling table (−0.096
R/window). The migration is visible in the last column of §4's table — and it is the whole story of the
study.

Across all seventeen completed arms — four label
structures, four model families, decision statistics whose numeric scales span three orders of magnitude —
realized book R is a near-perfect linear function of MARKET-top share:

| MARKET-top % | 2.10 | 2.84 | **7.06** | 24.41 | 26.23 | 27.12 | 31.67 | 62.38 | 75.38 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| arm | A1_f0125 | A1_f025 | **SHIPPED** | A2 | A6 | A5 | A3 | A7 | PFILL-hgb |
| book R | **+3.27** | −6.07 | **+0.95** | −95.93 | −120.42 | −188.90 | −189.53 | −446.69 | **−690.82** |

**Pearson r = −0.9786 (p 1.0e-11), Spearman −0.7353 (p 7.7e-04), n = 17.** No feature, no model family
and no label structure in this study explains anything remotely comparable. **The selector's only
economically material property is how often it transacts on the MARKET population**, and every fitted
refinement is noise on top of that one number.

**Anything that makes this funnel trade more loses money on this pool.** The shipped book's +0.954 R is a
non-transacting result: 290 orders across 9,237 ranked windows, and 81.4 % of its argmaxes never fill.
That non-fill *is* its risk control.

### 4.1b Q1 — does capacity find anything the ridge cannot? Measured: no, it finds harm faster

`PREREG_V1_3` named this as still open. Ridge → HGB at an **identical** label and an identical protocol:

| label | ridge | HGB | selection term | E1 book | MARKET-top share |
|---|---|---|---|---:|---|
| shipped `E[net]` | A0 | **A3** | −0.00018 → **−0.01663** | −2.36 → **−190.49** (p 0.003) | 7.07 % → **31.67 %** |
| composed `P(fill)·E[net│fill]` | A2 | **A5** | −0.01586 → **−0.02837** (p 0.046) | −96.89 → **−189.85** (p 0.000) | 24.41 % → 27.12 % |
| fill-conditional `E[net│fill]` | A1 | **A4** | +0.01299 → +0.01519 (p 0.024) | −29.62 → **−46.60** (p 0.093) | 1.92 % → 3.32 % |

**Capacity is negative at every label.** It costs −188 R at the shipped label and −93 R at the composed
one. The single place it helps at all is the fill-conditional arm's *selection term* (+0.013 → +0.015),
and even there the book gets worse. The direction is the one the leak warning predicted: **higher capacity
finds the fill channel faster and harder**, and the fill channel is the adverse one.

Two corroborations from inside the HGB family:

- **Constraining capacity helps.** The cost-**monotone** HGB (A6) beats the free HGB (A5) by **+68.5 R**
  (−121.37 vs −189.85) and halves the damage to the selection term (−0.0122 vs −0.0284). A sign prior
  imposed by hand outperforms letting the model choose.
- **Optimising the pre-registered metric directly is the worst thing you can do.** A7 predicts
  `P(net > 0)` — literally the P1 event — and lands at **62.4 % MARKET share and −446.69 R**, the second
  worst book of the study. The metric and the money are not merely uncorrelated here; they are opposed.

### 4.2 R2 (the cap) — it works on every arm, and it is abstention in disguise

`PREREG_V1_2` fixed the cap grid on each arm's own quantile scale before it ran. Capping improves the
matched-count book **on every single arm tested**:

| arm | no cap | q0.99 | q0.98 | q0.95 | q0.90 |
|---|---:|---:|---:|---:|---:|
| SHIPPED | −39.10 | −26.38 | −15.91 | −14.21 | **+0.23** |
| A0 | −34.39 | −22.27 | −16.45 | −15.52 | **−6.13** |
| A1 | −7.22 | −7.22 | −2.12 | −6.88 | **+3.71** |
| A2 | −23.70 | −35.50 | −25.65 | −8.49 | **−3.04** |

The mechanism, measured directly rather than argued (`receipts/DECILE_V1.json` — mean realized R by each
arm's **own** prediction decile, the generalisation of Lane 3 §6 from one ranker to all of them):

| arm | D1 | D5 | **D10** | D10 MARKET share | D10 no-fill share | top decile is worst? |
|---|---:|---:|---:|---:|---:|:--:|
| SHIPPED | −0.0310 | +0.0041 | **−0.0796** | 0.23 | 0.56 | **YES** |
| A0 | −0.0305 | +0.0014 | **−0.0826** | 0.23 | 0.56 | **YES** |
| A2 · ridge composed | −0.0147 | −0.0260 | **−0.1023** | **0.94** | 0.02 | **YES** |
| A3 · HGB shipped label | −0.0270 | −0.0202 | **−0.1382** | 0.62 | 0.19 | **YES** |
| A6 · HGB monotone | −0.0123 | −0.0468 | **−0.1072** | 0.43 | 0.19 | **YES** |
| A7 · HGB P(win) | −0.0649 | −0.0256 | **−0.1358** | **0.93** | 0.02 | **YES** |
| A1 | −0.0135 | −0.0153 | −0.0213 | 0.00 | 0.96 | no |
| A4 · HGB fill-cond | −0.0123 | −0.0101 | −0.0253 | 0.02 | 0.88 | no |
| A1_f025 | −0.0132 | +0.0187 | −0.0078 | 0.00 | 0.99 | no |
| A1E7 | −0.0417 | +0.0151 | **+0.0040** | 0.00 | 0.98 | no |

**"The top decile is the worst decile" is not a generic overfitting artifact — it is exactly and only the
MARKET/fill channel.** All six arms whose top decile is MARKET-heavy have their worst realized mean there;
not one of the arms whose top decile is ~90–99 % no-fill does. The rule holds across both model families
and all four label structures, with no exception in seventeen arms. So R2 "works" because a cap removes high-`P̂(fill)`
candidates: **the cap is an abstention rule wearing a threshold's clothes.** That is a better reason to
test it than the one it was proposed under, and it remains in-sample here — the grid has five cells and
was read after the fact.

### 4.3 The hit-rate metrics, reported as diagnostics only

`PREREG_V1_3` demoted these. They are reported because B3's passing arm is the evidence the metric is broken.

| arm | P1 | bar | Δ | p | P2 | bar | Δ | p | book R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SHIPPED | 0.0722 | 0.0862 | −0.0140 | 0.006 | 0.0184 | 0.0264 | −0.0080 | 0.011 | **+0.95** |
| **A2** | **0.1863** | 0.0862 | **+0.0992** | **0.000** | **0.0579** | 0.0264 | **+0.0304** | **0.000** | **−95.93** |
| A2 DEV | 0.2065 | 0.0876 | +0.1189 | 0.000 | — | — | — | — | — |
| A2 CONF | 0.1601 | 0.0863 | +0.0738 | 0.000 | — | — | — | — | — |
| A1 | 0.0353 | 0.0861 | −0.0507 | 0.000 | 0.0131 | 0.0263 | −0.0132 | 0.000 | −28.66 |

A2 clears both bars by >2×, with day-clustered CIs excluding zero, **separately on the months it was
selected on and the months it was not** — and loses 96.89 R against the shipped rule at p 0.006. A
sibling lane reached 0.2121 / 0.0747 with −76.14 R on the same population by a different route. Two
instruments, same verdict: **on a population where 61.4 % of rows book exactly 0.0, hit rate and R are
close to orthogonal, and the pre-registered bar can be cleared at p < 0.001 by an arm that loses money
faster than random.**

---

## 5. The learning curve — the constraint is non-stationarity, not capacity or data

`PREREG_V1` declared the train-fraction ablation as a diagnostic, most-recent-first, before any of it ran.

| train fraction (most recent) | rows at July | selection term | p | ceiling capture | E1 vs shipped |
|---|---:|---:|---:|---:|---:|
| **12.5 %** | ~13 k | +0.02054 | 0.000 | +0.0242 | **+2.32** |
| **25 %** | ~26 k | **+0.02906** | **0.000** | **+0.0297** | −7.03 |
| 50 % | ~51 k | +0.01774 | 0.001 | +0.0221 | −18.90 |
| **100 % (A1)** | ~103 k | +0.01299 | 0.034 | +0.0186 | −29.62 |

**More data is monotonically worse from 25 % onward**, on the selection term, on ceiling capture, and on
the book. Training on a quarter of the most recent rows more than doubles the selection term against
training on everything since October 2025, and holds on both the development months (+0.0316) and the
confirmation months (+0.0256).

Read this together with §4.1b's capacity axis and the two agree: **neither more model nor more data
helps.** Capacity is negative at every label; data volume is negative beyond a quarter of the recent
window. The binding constraint is **non-stationarity** — the estate's prequential chain accumulates every
row since October 2025 and never forgets, so it is optimising against a distribution that no longer
exists.

The honest caveat is that the fraction grid has four cells and the best was read after the fact; the
*shape* (monotone decline beyond 25 %) is the finding, not the winning cell. And §6 shows even the
winning cell's advantage over a zero-model control is +0.0076 R/window.

---

## 6. Adversarial checks against this lane's own positive

The A1 family's selection term is positive and significant, and its no-fill share tracks it almost
perfectly — exactly what a "skill" that is really abstention would look like. Three controls
(`b3_selector/b6_adversarial.py`, receipt `ADVERSARIAL_V1.json`):

| arm | selection term | share of picks that **never filled** | selection term **on FILLED picks only** | p |
|---|---:|---:|---:|---:|
| A1_f025 ᴰ | +0.02906 | 92.9 % | +0.14401 | 0.077 |
| **C2_FAR_LIMIT** (zero model, one feature) | +0.02150 | 99.4 % | +0.01383 | 0.958 |
| **C1_NOFILL_PICKER** (outcome-informed) | +0.02142 | 99.4 % | -0.02711 | 0.722 |
| A1_f0125 ᴰ | +0.02054 | 92.8 % | +0.01885 | 0.802 |
| A1_f05 ᴰ | +0.01774 | 91.9 % | -0.01563 | 0.799 |
| A4 · HGB fill-cond | +0.01519 | 85.7 % | -0.01803 | 0.710 |
| A1 | +0.01299 | 90.7 % | -0.06475 | 0.282 |
| A1E | +0.01255 | 90.5 % | -0.06704 | 0.260 |
| A1E7 | +0.01086 | 90.4 % | -0.08334 | 0.183 |
| A10 | +0.00687 | 89.9 % | **-0.11812** | **0.041** |
| **SHIPPED** | +0.00066 | 81.4 % | **-0.08282** | **0.044** |
| A0 | -0.00018 | 81.4 % | **-0.08664** | **0.034** |
| A6 · HGB mono | -0.01216 | 36.4 % | -0.02885 | 0.196 |
| A2 | -0.01586 | 52.2 % | **-0.05529** | **0.022** |
| A3 · HGB shipped label | -0.01663 | 42.9 % | -0.04111 | 0.070 |
| A5 · HGB composed | -0.02837 | 35.9 % | **-0.05579** | **0.009** |
| A7 · HGB P(win) | -0.04081 | 12.1 % | **-0.04779** | **0.001** |

**Three things this table settles.**

1. **A single causally clean feature with no model beats every fitted arm except one.** Ranking by
   `distance_to_limit_atr` descending — "pick the limit least likely to fill" — scores **+0.02150**,
   above A1 (+0.01299), A1E, A10 and the shipped ranker (+0.00066), and it lands within 0.0001 of the
   outcome-informed abstention picker C1 (+0.02142), which is allowed to see which candidates will not
   fill. Seventeen fitted arms, 481,098 training rows and 100 daily refits do not beat one feature and a
   sort. *(C1 breaks ties by key among the no-fill candidates, so it is a representative abstention
   picker, not the supremum over them — which is why C2 can edge past it by 0.00008.)*

2. **The skill is abstention, arithmetically.** A no-fill books exactly 0.0 in a pool whose mean is
   −0.037, so picking one is worth (0 − pool mean) with no skill of any kind. That accounting predicts
   +0.0343 for A1 against its observed +0.0130 — **the model gives back 62 % of the free abstention
   value** by occasionally picking a filling loser.

3. **Conditional on transacting, the selector is significantly worse than chance — for six of seventeen
   arms, and negative for fourteen.** On the windows where the pick actually filled: the shipped rule
   **−0.0828 (p 0.044)**, A0 **−0.0866 (p 0.034)**, A10 **−0.1181 (p 0.041)**, A2 **−0.0553 (p 0.022)**,
   A5 **−0.0558 (p 0.009)**, A7 **−0.0478 (p 0.001)**. Only `A1_f025` is meaningfully positive there
   (+0.144) and it clears no multiplicity bar at p 0.077 on 7.1 % of its windows.

4. **The abstention share is the ordering variable here too.** Sort the table by selection term and the
   no-fill share falls monotonically from 99.4 % to 12.1 %; it is the same law as §4.1 seen from the
   other side.

**So the ceiling capture number should be read as follows.** The best figure any arm reaches is **+2.97 %**
of the +1.436 R/window separability (A1_f025), against the shipped ranker's +0.94 % — and **+2.15 %** of it
is available from one feature with no model, and *all* of it is realised by declining to transact. The
fraction of the ceiling reachable **by trading** is, on this evidence, **negative**.

---

## 7. Multiplicity, declared ruthlessly

| category | count | ids |
|---|---:|---|
| declared model arms (total) | **23** | A0–A12, A12H, A10L, A11L, A10P, A10F, A1E, A1E7, A1_f0125/f025/f05 |
| of which **candidate** arms | **15** | A0–A12, A12H, A1E |
| of which complete at time of writing | **12** | A0, A1, A2, A10, A1E, A1E7, A1_f0125/f025/f05 (+ derived PFILL, C1, C2) |
| declared negative controls | 4 | A10L, A11L, A10P, A10F |
| over-strict control | 1 | A1E7 |
| learning-curve diagnostics | 3 | A1_f0125, A1_f025, A1_f05 |
| zero-model / derived controls | 4 | C1, C2, PFILL_RIDGE, PFILL_HGB |
| hyperparameter settings searched | **0** | one fixed setting per family, named in `PREREG_V1` |
| threshold grids | 2 | the R2 cap grid (5 quantile cells) and the top-N grid (5 cells) — both declared **exploratory and in-sample**, neither may carry a verdict |

**On the primary metric E1, no correction is needed because nothing is positive to correct.** On the
selection term, `A1_f025`'s raw p 0.000 clears BH at α = 0.10 over 15 arms (rank-1 bar 0.0067) — but
`A1_f025` is a **learning-curve diagnostic**, not a candidate arm, and promoting it to a finding is
precisely the post-hoc move this ledger exists to expose. It is reported as a *shape*, not a cell.

**What would need pre-registering for a real read.** One arm, one statistic, one floor, one cap, one
policy, one window — named before the window is opened. On this evidence the only proposal worth that
cost is not a selector at all: it is **the abstention rule stated directly** (`distance_to_limit_atr`
above a threshold ⇒ stand down), pre-registered against the shipped rule on a never-read window, with the
per-day paired difference as the sole gate. **This lane makes no arming proposal and no admission claim
under any reading.**

---

## 8. What is closed, what is open

**Closed by measurement.**
- **R1** (retrain conditional on fill, rank on the composed statistic) — closed negative, two independent
  instruments, −95.93 R here (−188.90 R at higher capacity).
- **Q1, capacity** — closed negative. Gradient boosting is worse than the ridge at every label it was
  given; the monotone constraint recovers +68.5 R of the damage; directly optimising the pre-registered
  hit-rate metric produces the second-worst book in the study.
- **The hit-rate reversal test** — closed as structurally invalid on this population.
- **Breadth of ranking skill as a route to the ceiling** — closed: conditional on trading, the selector
  is significantly worse than chance.
- **Lane 6's regime × family interaction** — B3's lag-1 build adds nothing (+0.00687, p 0.270, *below*
  the plain arm it extends), an independent corroboration that the same-day construction was lookahead.
- **The label-availability leak** — confirmed at 4.94 %, all +1 day, and the surviving selection term
  survives its removal.

**Open, and cheap.**
- **R2 (the cap)** — untested as a pre-registered object. Note the mechanism now has a cleaner
  explanation than "adverse selection at the top": a cap removes high-`P̂(fill)` candidates, i.e. it is
  an abstention rule in disguise. That is worth one pre-registered test.
- **R3 (competing risks A8, IPCW A9)**, the fill×cost ablation (A12/A12H) and the leaky negative
  controls (A10L/A11L/A10P/A10F) are **still refitting** — six arms across four stages, queued in that
  order. `refresh_all.sh` folds each in automatically the moment its stage checkpoints all 100 days; no
  table above needs rewriting by hand.

  **Their prediction is already on the record, and it is falsifiable.** §4.1's law
  (r = −0.9786) says each will land on the same line: book R ≈ −9.4 R per point of MARKET-top share.
  A8 is the one arm with a mechanism to depart from it, because it prices the payoff asymmetry
  (`Σ p_k (c_k − cost)` with the class-conditional gross means learned strictly prior) rather than the
  fill probability — if any arm can transact *and* not lose, it is that one. A11L is expected to beat
  A11 substantially, which would be a third independent confirmation that the same-day regime
  construction was lookahead.

---

## 9. Receipts

All under `swarm2/breakthrough/b3_selector/`.

| file | what |
|---|---|
| `PREREG_V1.json` … `PREREG_V1_3.json` | the four frozen pre-registrations with payload hashes |
| `T0_FEATURE_PROVENANCE_AUDIT_V1.json` | the 43-feature provenance audit |
| `b0_bootstrap_cache.py` | sealed-sink bootstrap corpus build (171,685 rows) |
| `b1_dataset.py`, `b1b_leak_features.py` | the master dataset; the deliberately leaky and past/future regime blocks |
| `b2_walkforward.py` | the daily-refit engine, all stages, per-day checkpointed |
| `b3_evaluate.py` | P1/P2/P3 + the sealed-read instrument validation |
| `b4_economics.py` | matched-trade-count books, the cap factorial |
| `b5_paired_economics.py` | **E1/E2/E3 and the Q3 label-availability measurement** |
| `b6_adversarial.py` | **the abstention controls C1/C2 and the conditional-on-filled term** |
| `b7_decile.py` | mean realized R by each arm's own prediction decile |
| `refresh_all.sh` | **one command** that regenerates every table above from whatever stages are complete |
| `receipts/` | the machine-written JSON for every table, with `PROVENANCE.json` sha256s |
| `PROGRESS.json` | step-by-step completion state |

An arm is admitted to any table only when its stage has **all 100 scored days** checkpointed
(`b3_lib.complete_stages`). A row-count guard was rejected because it admits an arm that has seen only
February, which is a different and much easier evaluation window.

Machine-written results in the job scratch (`/Users/borr/.claude/jobs/adb9e69b/tmp/b3/out/`):
`eval_*.json`, `EVAL_V1.json`, `ECONOMICS_V1.json`, `PAIRED_ECONOMICS_V1.json`, `ADVERSARIAL_V1.json`,
`ck_W*.json`, `preds_W*.npz`.

Inputs: `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` (632,934 occurrences, 382,181
eligible); the frozen chain `w21_predecision_ridge.py` → `candidate_funnel_analysis.py`; the sealed
bootstrap sinks via `w21_january_prequential.py`.
