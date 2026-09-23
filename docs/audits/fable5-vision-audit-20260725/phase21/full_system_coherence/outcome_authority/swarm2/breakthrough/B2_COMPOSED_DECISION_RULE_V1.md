# B2 — the composed decision rule: `P(fill) × E[net | fill]`, built, walked, and measured

**The commission.** Lane 3 measured that the shipped ridge regresses `terminal_net_r` on a population
where **84.8 % of resolved LIMIT rows are exactly 0.0 R because they never filled**, so a high score
means *"this order will fill"* and filling is the adverse event. Three lanes converged on one repair:
**decide on `P(fill) × E[net | fill]` instead of on one score that conflates them.** This lane built it.

**The result, first line.** The composed rule's five-month pooled book is **−76.14 R on 1,151 trades**
against the shipped rule's **+0.954 R on 290**. Per-day paired difference **−0.771 R, CI95
[−1.373, −0.121], p 0.016** — significantly worse, and worse in **all five months individually**.
The repair is **REFUTED as a ranker**, and the reason is not that it failed to price non-fill. It is
that **pricing non-fill correctly is what breaks it**: non-fill was the shipped rule's de-facto risk
control, and composition removes it.

**Scope.** Measurement only. No broker, no VPS, no live config, no decision-contract-bound file, no
git commit. The four never-funnel-read 2025 windows (june/august/september/december 2025) and the two
reserve days were **not touched**. Nothing here is an admission, a promotion, or an arming proposal.

---

## 0. The answer in eight lines

| # | finding | number |
|---|---|---|
| **1** | **The composed rule loses, significantly, and in every month.** | −76.14 R vs shipped +0.954 R; per-day diff **−0.771 R** CI95 [−1.373, −0.121] **p 0.016**, 100 trading days; worse in 5/5 months |
| **2** | **The mechanism: composition triples the MARKET-top share and halves the no-fill share.** Multiplying a LIMIT candidate by `P(fill)` (median **0.099**) shrinks it 10× while MARKET keeps its full magnitude (`P(fill) ≡ 1`), so the argmax migrates to MARKET — Lane 3's *worst* population. | MARKET-top share **7.06 % → 22.66 %**; no-fill share of the pick **81.4 % → 44.6 %**; trades **290 → 1,151** |
| **3** | **Non-fill is the shipped rule's risk control, and nobody knew.** 81.4 % of its argmaxes never fill and book exactly 0.0, so its selection noise is never expressed. Pricing non-fill explicitly *executes* that noise. | shipped +0.954 R on 290 trades; the same ranker with the fill discount removed (A7, rank by `P(fill)` alone) books **−447.06 R** |
| **4** | **THE CRUX — the MARKET-top-abstain rule does NOT reverse. Measured three independent ways.** | `E[net \| LIMIT top fills]` moves −0.2352 (p **0.031**) → **−0.0230** (p **0.747**): the adverse selection is **90.2 % removed but does not cross zero**. Composition-selected un-abstention costs **−14.07 R on 125 rescued trades**. Whole-policy un-abstain arms: **−13.11 R** and **−22.35 R** |
| **5** | **Lane 3's pre-registered reversal test is not a valid proxy for economic value, and this lane can prove it.** The composed ranker **clears both baselines by 2.5–2.8×** and still loses money; the arm that maximises them is the worst economic arm in the study. | composed pick+ **0.2121** vs uniform 0.0862 (**+0.126, p 0.000**), pick-best **0.0747** vs 0.0264 (**+0.047, p 0.000**) — while booking −76 R. `P(fill)`-only scores **0.3568 / 0.1538** (the best hit-rates measured) and books **−447 R** |
| **6** | **Ceiling capture is nil.** Against the +1.436 R/window oracle the composed ranker's within-window selection term is **−0.0204 R/window** (p 0.096) — *below* a uniform random draw. | oracle +1.41233 R/window; composed −0.02044 CI95 [−0.04330, +0.00301]; shipped +0.00066 (p 0.898) |
| **7** | **The one measured positive is a confound in the other direction, and it is reported as such.** `E[net\|fill]` alone beats a uniform draw by **+0.01235 R/window** — the first significantly positive within-window selection term in the estate, and it **survives all three temporal-leak controls** — but it achieves it by picking rows that **never fill** (90.65 % no-fill). Forced to trade, it books **−30.51 R**. | +0.01235 CI95 [+0.00066, +0.02412] p 0.041 = **0.86 % of the ceiling**; embargo-1 +0.01353 p 0.027; strict availability +0.01328 p 0.024; as a policy, −30.51 R on 115 trades |
| **8** | **The refutation is not a lookahead artifact — it is confirmed by removing lookahead.** The basis contains no same-day aggregate of any kind (§7.1); the frozen chain's one real weakness (5.0 % of training rows carry a label ending on a later day, horizon capped at exactly 1.0 day) is removed completely by two independent controls, and the composed rule gets **worse** under both. | A1 −76.14 → **−102.48** (embargo-1) / **−81.63** (strict label availability); past/future split shows the **inverted** signature — the composed statistic is worse in the late half, the positive is stronger in the early half |

**The one-sentence conclusion.** `E[net] = P(fill)·E[net|fill]` is an *identity*, not a repair — the
composed statistic targets exactly the same estimand the shipped ridge already targets — and factoring
it makes the estimate *better* and the book *worse*, because on a pool with no positive cell the
decision-relevant quantity is not "which candidate has the highest EV" but "how often do I avoid
transacting at all."

---

## 1. Instrument — validated twice before any composed number was computed

The frozen spec (`b2_composed_rule/B2_SPEC_V1.json`, sha256
`6d4ebdea10fd1b8249e9d94c62504d2e2ff80ff5eee98efe041d908dae82e62e`) was written and hashed **before**
the first composed score existed, and it committed to reproducing the sealed reads first.

**(a) The funnel reproduces all five sealed months exactly** (`instrument_validation.json`):

| month | sealed dispositions (`below0.10` / `abstain` / `trade`) | reproduced | sealed actual R | reproduced |
|---|---|---|---:|---:|
| February | 1,164 / 601 / 106 | **identical** | +14.168399 | **+14.168399** |
| April | 1,447 / 344 / 50 | **identical** | −7.742114 | **−7.742114** |
| May | 1,265 / 374 / 17 | **identical** | +5.130257 | **+5.130257** |
| June | 1,575 / 414 / 49 | **identical** | +3.963843 | **+3.963843** |
| July | 1,537 / 226 / 68 | **identical** | −14.566020 | **−14.566020** |

**(b) The ranking instrument reproduces Lane 3's published pick-rate test to 4 dp.** Shipped ranker,
policy occupancy basis: pick-positive **0.0722** vs uniform **0.0862**, diff −0.0140 CI95
[−0.0232, −0.0038]; pick-best **0.0184** vs **0.0264**, diff −0.0080 CI95 [−0.0117, −0.0041];
within-window selection **+0.00066** CI95 [−0.01528, +0.01594] p 0.898. Lane 3 published
−0.0140 [−0.0228, −0.0040], −0.0080 [−0.0117, −0.0041], +0.00066 [−0.01483, +0.01577] p 0.897.

The funnel is adapted from `lane3_receipts/funnel_lib.py`; the **only** change is that the score is
supplied from an external `{occurrence_key: value}` map, so every arm runs through byte-identical
gates G0–G5.

### 1.1 What was built

Two models, walked forward day by day over `feb → apr → may → jun → jul` (100 trading days), each fit
on the dev+January bootstrap (**84,902 rows**) plus every day **strictly before** the test day —
identical protocol to the sealed chain (`b2_walk.py`):

| stage | target | training population | estimator |
|---|---|---|---|
| **A — fill** | `1` if state ∈ {TARGET, STOP, TIME_STOP}, `0` if NO_FILL | resolved-eligible **LIMIT** rows (grew to 368,078) | `LogisticRegression(C=0.1)` |
| **B — net given fill** | `terminal_net_r` | resolved-eligible **FILLED** rows (grew to 103,395) | `Ridge(alpha=10.0, solver='lsqr')` — byte-identical to shipped |

`P(fill) ≡ 1.0` exactly for MARKET, by contract (`geometry_bound_outcome_model.py:1027-1034`).
Feature basis, preprocessing and the `1/count(decision_window_id)` sample-weight rule are **identical**
to the frozen rule (`w21_predecision_ridge.py:49-67`, `:257-281`). `C = 1/alpha = 0.1` mirrors the
estate's own L2 strength — **no hyperparameter search was run**. 382,181 scores emitted, matching the
eligible-occurrence count exactly.

**The identity was disclosed in the spec before the run**, and it governs the interpretation:

> `E[net] = P(fill)·E[net|fill] + P(no_fill)·0 = P(fill)·E[net|fill]` **exactly**, because a
> `RESOLVED_NO_FILL` row books exactly 0.0 R (Lane 3 §4.2, verified over 388,912 rows). The composed
> statistic therefore targets the **same estimand** as the shipped ridge. This is a change of
> *estimator structure*, not of *target*. Any claim that composition "prices non-fill for the first
> time" would be false — the shipped ridge already prices it, badly.

Score distributions (382,181 rows): `P(fill)` mean 0.2648, median 0.0991; `E[net|fill]` mean **−0.0490**,
median −0.0473; composed mean −0.0203, median −0.0005. **143,008 rows (37.4 %) carry a positive
`E[net|fill]`** — and `composed > 0 ⟺ E[net|fill] > 0` exactly, which is the product structure
asserting itself.

---

## 2. (2) The five-month re-score — every arm, per month and pooled

Judged on **the same three pre-registered gates the frozen rule was judged on**
(`MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json` → `validation.pass`): **G1** ≥ 20 resolved trades,
**G2** pooled worst-case strictly positive, **G3** positive active days > negative. Column `G` reads
`G1G2G3`. `wc` = worst case (censored charged −1 − deductible cost).

| arm | trades | actual R | wc R | pos/neg days | G | feb | apr | may | jun | jul |
|---|---:|---:|---:|---:|:--:|---:|---:|---:|---:|---:|
| **C1 shipped `market_top_abstain`** | 290 | **+0.954** | −7.263 | 46/39 | `101` | +14.168 | −7.742 | +5.130 | +3.964 | −14.566 |
| C2 shipped naive-mixed | 959 | −27.299 | −145.204 | 41/51 | `100` | −4.742 | −13.524 | +4.313 | +3.694 | −17.040 |
| C3 shipped market-rerank | 333 | −9.279 | −18.517 | 46/42 | `101` | +4.673 | −9.169 | +6.199 | +2.636 | −13.617 |
| C4 random within eligible (200 seeds) | 9,051 | **−211.55** (p05 −292.3, p95 −124.1) | −1,631.6 | — | — | — | — | — | — | — |
| **A1 PRIMARY composed, floor 0.10, abstain** | **1,151** | **−76.138** | −114.147 | 37/62 | `100` | +8.330 | −8.446 | −25.432 | −18.220 | −32.371 |
| A2 composed, floor 0.00, abstain | 2,047 | −112.164 | −184.257 | 40/60 | `100` | +5.057 | −12.801 | −37.092 | −37.390 | −29.938 |
| A3 composed, floor 0.10, **no abstain** | 1,918 | −91.286 | −340.409 | 39/61 | `100` | +7.081 | −13.744 | −39.367 | −14.244 | −31.013 |
| A4 composed, floor 0.00, **no abstain** | 7,822 | −232.616 | −1,098.825 | 31/69 | `100` | −7.456 | −36.712 | −52.890 | −79.252 | −56.306 |
| A5 `E[net\|fill]` only, floor 0.10, abstain | 115 | −30.505 | −32.603 | 13/28 | `100` | −9.610 | −12.592 | −0.354 | −2.225 | −5.724 |
| A6 Jeffreys-cell fill × `E[net\|fill]` | 1,257 | −80.274 | −122.363 | 38/61 | `100` | −9.646 | −11.903 | −13.536 | −14.419 | −30.771 |
| A7 `P(fill)` only (negative control) | 6,762 | **−447.058** | −974.371 | 27/73 | `100` | −114.026 | −114.963 | −41.343 | −128.846 | −47.880 |

**Not one arm passes the three gates**, and neither does the shipped book on the five-month pooled
basis (its `G2` fails at −7.263; its February PASS was a single-month read). **A1 is worse than the
shipped rule in all five months**, including February.

**Outcome mix** (the win/stop/time-stop split the commission asked for):

| arm | TARGET | STOP | TIME_STOP | CENSORED | target rate |
|---|---:|---:|---:|---:|---:|
| C1 shipped | 53 | 123 | 106 | 8 | 18.8 % |
| **A1 composed** | 167 | 458 | 489 | 37 | **15.0 %** |
| B2 (best constructive) | 23 | 62 | 74 | 3 | 14.5 % |

A1 does not merely trade more — it trades **worse per trade** (−0.0662 R/trade against the shipped
+0.0033), with a lower target rate.

### 2.1 Head-to-head against the shipped book (day-clustered bootstrap, 100 days)

| arm | total Δ vs shipped | per-day Δ | CI95 | p |
|---|---:|---:|---|---:|
| **A1 PRIMARY** | **−77.092** | **−0.77092** | [−1.37346, −0.12058] | **0.016** |
| A2 | −113.118 | −1.13118 | [−2.12084, −0.11367] | 0.034 |
| A3 | −92.241 | −0.92241 | [−1.71617, −0.12885] | 0.026 |
| A4 | −233.571 | −2.33571 | [−3.53638, −1.23356] | 0.000 |
| A5 | −31.460 | −0.31460 | [−0.67723, +0.02133] | 0.072 |
| A6 | −81.228 | −0.81228 | [−1.49675, −0.10304] | 0.024 |
| A7 | −448.012 | −4.48012 | [−6.03085, −2.85150] | 0.000 |
| B1 (post-hoc) | −2.239 | −0.02239 | [−0.18913, +0.13883] | 0.829 |
| **B2 (post-hoc)** | **+0.107** | +0.00107 | [−0.20809, +0.23053] | 0.977 |
| B3 (post-hoc) | −14.068 | −0.14068 | [−0.33079, +0.01417] | 0.097 |
| B4 (post-hoc) | −23.303 | −0.23303 | [−0.54375, +0.05993] | 0.124 |

---

## 3. Why it fails — measured, not argued

The commission's diagnosis was that the score conflates *will fill* with *will pay*. That is true. The
inference — that separating them must help — does not follow, and the measurement says why.

**Composition is a systematic re-weighting toward MARKET.** For a LIMIT candidate the composed score
is multiplied by `P(fill)`, whose median is **0.0991**; for MARKET it is multiplied by exactly 1. The
window argmax is taken over ~41 candidates, so it lands on a candidate with a *positive* estimated
`E[net|fill]` (37.4 % of the pool qualify), and among those the one with the highest `P(fill)` wins.
That is a MARKET candidate:

| ranker | MARKET-top share | no-fill share of the pick | censor rate of the pick |
|---|---:|---:|---:|
| shipped | **7.06 %** (652/9,237) | **81.41 %** | 18.18 % |
| **composed** | **22.66 %** (2,093/9,237) | **44.62 %** | 20.01 % |
| composed (Jeffreys fill) | 24.69 % | 65.95 % | 15.42 % |
| `E[net\|fill]` only | 1.89 % | 90.65 % | 16.65 % |
| `P(fill)` only | **73.40 %** | 8.25 % | 15.62 % |

Lane 3 §7 had already measured that restricting selection to MARKET is **the worst rule it tested**
(−0.09588 R/window, against a −0.03688 random draw). The composed statistic is a **soft market-rerank**,
and it inherits that defect in proportion to how much MARKET it promotes. Across the
shipped → composed → `P(fill)`-only sequence — the three arms that rank the full pool and differ
essentially in how much weight the fill channel carries — the book is **monotone in MARKET-top share**:
7.06 % → **+0.95 R**, 22.66 % → **−76.1 R**, 73.40 % → **−447.1 R**. (A6, the same composition with the
estate's Jeffreys cell fill model, sits where the pattern predicts: 24.69 % → −80.3 R.)

**So the shipped rule's +0.954 R rests on an accident.** Its argmax is 81.4 % no-fill: four out of five
of its "decisions" are never expressed, because the order it selects never trades. Its selection noise
is therefore mostly *unrealised*, and the abstain gate removes most of what remains. **Non-fill is the
de-facto risk control.** Estimating it correctly and then acting on the corrected estimate removes the
control while leaving the noise — which is exactly what the −76.14 R is.

This also **weakens Lane 3's mechanism claim as literally worded**, and the spec committed in advance
to reporting it. Lane 3 §6: the model "has learned to predict *this order will actually trade*". If
that were the whole story, the shipped ridge would behave like A7 — rank by fill probability — which
books **−447.06 R**. It books +0.954 R. The shipped ridge is a *weak* and *partial* fill detector whose
weakness is load-bearing; the top-decile association Lane 3 measured is real, but it is a tendency
inside the top decile, not the ranker's operating principle.

---

## 4. (3) THE CRUX — does the MARKET-top-abstain rule reverse under composition?

**No.** Lane 3 §4.3 pre-specified the single measurement that would reverse it: *"the mean realized net
of the LIMIT-topped windows' tops, conditional on fill… positive with a day-clustered CI excluding zero
reverses the verdict, and nothing else does."*

| score used to rank | windows abstained | no-fill share of those tops | take-the-LIMIT-top-instead | **`E[net \| LIMIT top fills]`** | n | CI95 | p |
|---|---:|---:|---:|---:|---:|---|---:|
| **shipped** | 1,959 | 81.61 % | **−73.63 R** (−0.04326/win, p 0.038) | **−0.23524** | 313 | [−0.43545, −0.02208] | **0.031** |
| **composed** | 1,424 | 38.16 % | **−14.62 R** (−0.01419/win, p 0.799) | **−0.02295** | 637 | [−0.19386, +0.13317] | **0.747** |
| `E[net\|fill]` only | 8,186 | 92.65 % | −48.37 R (−0.00672/win, p 0.305) | −0.09144 | 529 | [−0.25691, +0.08001] | 0.330 |

**The repair does exactly what it was designed to do, and it is not enough.** Composition cuts the
adverse selection on the LIMIT tops it picks by **90.2 %** — from a significantly negative −0.2352
(p 0.031) to **−0.0230, statistically indistinguishable from zero** (p 0.747). The rule stops being
"declining a lottery whose only paying tickets are losses" and becomes "declining a coin flip." But
the reversal condition requires *positive with a CI excluding zero*, and the point estimate is still
negative with a CI straddling zero. **Not reversed.**

**Two whole-policy confirmations, which are the honest test** because the conditional above is measured
on each score's own (different) abstained set:

| un-abstain arm | rescued trades | R | Δ vs shipped |
|---|---:|---:|---:|
| **B3** shipped rank, take the LIMIT top iff `composed ≥ 0.10` | +125 | **−13.114** | **−14.068 R** (−0.1126 R per rescued trade) |
| **B4** shipped rank, take the LIMIT top iff `E[net\|fill] > 0` | +590 | **−22.348** | −23.303 R |
| A3 composed rank, no abstain | 1,918 | −91.286 | −92.241 R |

**Three independent measurements, one answer: keep abstaining.** The composed statistic identifies a
*less bad* LIMIT population, not a *good* one, and every way of acting on it loses money.

---

## 5. (4) Ceiling capture — and a correction to Lane 3's reversal test

Lane 3 pre-specified: beat **0.0862** (pick is positive) and **0.0264** (pick is the window's best).
Measured on the policy occupancy basis (which reproduces Lane 3's shipped numbers exactly):

| ranker | pick-positive | Δ vs uniform | p | pick-best | Δ vs uniform | p | **mean R vs uniform draw** | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| shipped | 0.0722 | −0.0140 | 0.008 | 0.0184 | −0.0080 | 0.001 | +0.00066 | 0.898 |
| **composed** | **0.2121** | **+0.1260** | **0.000** | **0.0747** | **+0.0472** | **0.000** | **−0.02044** | 0.096 |
| composed (Jeffreys) | 0.1400 | +0.0535 | 0.000 | 0.0368 | +0.0092 | 0.000 | +0.00030 | 0.976 |
| `E[net\|fill]` only | 0.0352 | −0.0508 | 0.000 | 0.0131 | −0.0132 | 0.000 | **+0.01235** | **0.045** |
| `P(fill)` only | **0.3568** | **+0.2689** | 0.000 | **0.1538** | **+0.1181** | 0.000 | **−0.04669** | 0.000 |

**The composed ranker clears both pre-specified baselines by a factor of 2.5–2.8, at p 0.000 — and
books −76 R.** The arm that maximises both metrics (`P(fill)`, 0.3568 / 0.1538) is the worst economic
arm in the entire study (−447 R). **Lane 3's reversal test is therefore not a valid proxy for economic
value on this population, and this lane refutes it with its own instrument.**

The reason is structural: a `RESOLVED_NO_FILL` row books exactly 0.0, which is **never "positive"** and
**never "the window's best"** when any filled winner exists. So *any* hit-rate metric rewards picking
candidates that fill — and filling is the adverse event. The metric and the objective point in
opposite directions by construction.

**Ceiling capture is nil.** Against the +1.41233 R/window oracle, the composed ranker's within-window
selection term is **−0.02044 R/window** — below a uniform random draw. It captures **none** of the
+12,504 R, exactly as the shipped ranker does, and unlike the shipped ranker it also loses the
protection of not trading.

**The one positive, adversarially dismantled.** `E[net|fill]` alone is the first ranker in the estate
with a **significantly positive** within-window selection term: **+0.01235 R/window, CI95
[+0.00043, +0.02456], p 0.045**. That is **0.86 % of the ceiling**. And it is a confound in the
opposite direction: its picks are **90.65 % no-fill**, so it "beats" the negative pool by selecting
rows that book 0.0 rather than by selecting winners. The moment it is required to actually trade
(A5: floor 0.10 + abstain, 115 trades) it books **−30.51 R**. It is not tradeable, and it is reported
here as a measurement artifact rather than an edge. It is, however, **not a lookahead artifact**: it
survives both temporal controls and the past/future split, and strengthens under them (§7).

**The methodological conclusion, which is the lane's most transferable output:** on this population
every window-level metric is confounded by the no-fill mass, in a direction set by whether the metric
rewards transacting. Hit-rate metrics reward filling and are maximised by the worst policies; mean-R
metrics reward not-filling and are maximised by policies that cannot trade. **The only uncontaminated
instrument is the realised book of a complete policy that must actually place orders** — which is
§2's table, and nothing else.

---

## 6. The nearest constructive variants (POST-HOC, IN-SAMPLE)

A1's failure mode is specific — composition promotes MARKET into the argmax — so the constructive
direction is to use the composed statistic as a **veto on the shipped selection**, preserving the
shipped ranker's protective 81.4 % no-fill rate. **These four arms were chosen after seeing A1 fail.
They are in-sample, hypothesis-generating only, and they are counted in the multiplicity bill.**

| arm | trades | actual R | wc R | Δ vs shipped | p |
|---|---:|---:|---:|---:|---:|
| B1 shipped rank + require `E[net\|fill](top) > 0` | 253 | −1.285 | −8.482 | −2.239 | 0.829 |
| **B2 shipped rank + require `composed(top) ≥ 0.10`** | **162** | **+1.061** | **−2.056** | **+0.107** | 0.977 |
| B3 shipped rank, composed LIMIT-rescue ≥ 0.10 | 415 | −13.114 | −56.773 | −14.068 | 0.097 |
| B4 shipped rank, `E[net\|fill] > 0` LIMIT-rescue | 880 | −22.348 | −130.504 | −23.303 | 0.124 |

**B2 is the only arm in this lane that beats the shipped book, and it beats it by +0.107 R over five
months at p 0.977.** That is economically nil and statistically nothing. Its one genuinely interesting
property is that it cuts the **worst case** from −7.263 to **−2.056** by vetoing **146 of the 308 tops
that reach its veto gate** (the shipped rule takes 290 under its own occupancy path; vetoing frees
symbols, so the downstream counts shift) — a **44 % cut in trade count** for +0.107 R. As a *risk*
statement that is mildly interesting; as an *edge* it is not one, it fails gate G2 like everything
else, and its per-month record (+10.17 / −5.07 / +3.72 / −1.92 / −5.84) is negative in three of five
months. Under the embargo-1 control of §7 it rises to **+5.767 R** — which is the honest upper end of a
post-hoc arm on already-opened data, and still not an edge.

**Nothing here is deployable.** Any forward use of B2 is **pre-registration-pending** on data this lane
did not touch, and the four never-funnel-read 2025 windows are the program's validation currency —
they must not be spent on a +0.107 R hypothesis.

---

## 7. Temporal-leak audit — run after a sibling lane killed a finding as lookahead

A sibling lane established that the estate's only OOS-predictive finding was a **lookahead artifact**:
its regime features were medians over *every eligible candidate on the trading day*, including
candidates generated **after** the scored trade. It looked clean — walk-forward, strictly prior
training, daily refit — and it passed four permutation nulls, because **every one of them permutes
labels and a leak present in every permutation is invisible to them.** Only an explicit temporal test
finds it. This lane's build was therefore audited against the same standard.

### 7.1 Structural audit — the specific defect has no target in this basis

The composed statistic uses the frozen rule's own basis and **adds no feature**
(`w21_predecision_ridge.py:49-67`). Every one of the 43 features is an attribute of a *single
candidate* at its own decision instant:

- the 15 source features come from `_predecision_features(series, index, …)`
  (`broader_origin_generators.py:3478-3538`), whose docstring is explicit — *"Pure function of the
  closed-bar series, the candidate geometry… **No outcome fields, no post-asof bars**, no wall-clock
  reads"* — and whose every helper is strictly backward-looking:
  `_prior_high` → `series.bars[start:index]` (`:3391`), `_close_position` → `series.bars[start:index+1]`
  (`:3408`), `_close_to_close_vol` → `range(index-lookback+1, index+1)` (`:3456-3457`),
  `_full_lookback_atr(series, index, N)` (`:3444-3448`), `_bars_since_session_open` walking backward
  (`:3467-3468`);
- the cost, geometry, fillability and POI features come off the candidate's own record
  (`w21_predecision_ridge.py:138-153`).

**There is no median, mean, share, count or normalisation over "the day's candidates" anywhere in the
basis**, and no cross-candidate aggregation of any kind. The sibling's defect cannot be present here by
construction. Fitting is also leak-free by construction: the imputer, scaler and one-hot encoder are
fit on the training frame only and merely transform the test frame (`b2_walk.py`).

### 7.2 The one real temporal weakness in the frozen chain — measured, then removed twice

The frozen chain has a genuine, previously unstated weakness that this lane inherited: `resolved_eligible`
absorbs a day's rows **wholesale** the moment that day is scored, so a trade whose label span ends after
the *next* day has begun sits in training before its outcome could have been known.

**Measured across all 336,430 resolved-eligible rows: 5.0 % (16,794) carry a label ending on a later
calendar day, and the label horizon is capped at exactly 1.000 days.** Because the horizon can never
exceed one day, holding one day back removes the leak **completely** rather than merely reducing it.
Two independent controls were therefore run as full re-walks:

- **embargo-1** — training excludes the immediately prior day entirely (`b2_walk_embargo.py`);
- **strict label availability** — a row is admitted only once its own label span has ended before the
  test day begins (`b2_walk_avail.py`), the discipline `geometry_bound_outcome_model.py:437-460`
  already applies.

| quantity | baseline | **embargo-1** | **strict label availability** | verdict |
|---|---:|---:|---:|---|
| **A1 PRIMARY composed book** | **−76.14 R** | **−102.48 R** | **−81.63 R** | **negative result is NOT a leak artifact — it gets worse** |
| A5 `E[net\|fill]` policy book | −30.51 R | −16.02 R | −32.63 R | negative under all three |
| B2 constructive veto book | +1.061 R | +5.767 R | +1.061 R | survives; still nil-to-small |
| **`E[net\|fill]` within-window selection** | **+0.01235** [+0.00066, +0.02412] p **0.041** | **+0.01353** [+0.00197, +0.02599] p **0.027** | **+0.01328** [+0.00162, +0.02623] p **0.024** | **SURVIVES and strengthens** |

**The headline is immune by direction.** A lookahead leak inflates a fitted model; removing it can only
make the composed rule worse or unchanged. It got **worse** under both controls, so the −76.14 R
refutation is robust, and the leak could never have manufactured it.

### 7.3 The past/future split — the decisive test, and the signature is inverted

The sibling's decisive test was to split the day at hour 12 and check whether the **future** half
carries the signal. Applied to the evaluation here (`leaktest.json → past_future_split`):

| statistic | decision hour < 12 | decision hour ≥ 12 | leak signature? |
|---|---:|---:|---|
| composed | −0.01618 (n 4,170) | −0.02596 (n 3,219) | **no** — the later half is *worse* |
| **`E[net\|fill]`** | **+0.01471 (n 4,278)** | +0.00940 (n 3,421) | **no — inverted.** The signal sits in the **early** half |

A same-day aggregation leak concentrates signal in the **later** windows, which see more of the day.
Both statistics show the **opposite**: the composed statistic is worse late, and the one positive
finding is **stronger early**. Combined with §7.1's structural audit and §7.2's two full re-walks, the
`E[net|fill]` selection term is **not** a lookahead artifact.

### 7.4 What survives, stated at its true size

The coordinator's standing preference — *a composed rule that survives the temporal test at a smaller
number is worth more than a bigger one that does not* — is answered as follows. **What survives all
three temporal controls is a +0.0135 R/window within-window selection term from `E[net|fill]` alone
(p 0.024–0.041), which is 0.94 % of the +1.437 R/window ceiling, and which is NOT TRADEABLE** because
90.65 % of its picks never fill: it beats the pool by declining to transact, and every policy that
forces it to transact books between −16.0 R and −32.6 R. It is a real measurement of a real
(tiny) ordering, not an edge, and it is reported here at that size deliberately.

The sibling lane's related finding is **consistent with this one and was not tested against it**: it
reports that the regime block *subtracts* inside a `P(fill) × E[net|fill]` statistic while fill×cost is
the component that works. This lane added no regime features — the basis is fill-, cost- and
geometry-side throughout — and still finds the composition negative, which locates the defect in the
**composition step itself** (§3), not in the choice of conditioning block.

---

## 8. (5) Multiplicity, declared honestly

| category | count | detail |
|---|---:|---|
| **Pre-declared arms (frozen before any result)** | **7** | A1–A7, in `B2_SPEC_V1.json` |
| **Post-hoc constructive arms** | **4** | B1–B4, chosen after A1 failed — declared in-sample |
| **Total decision rules scored** | **11** | 0 admitted; 0 pass the three gates; best is +0.107 R at p 0.977 |
| Estimator specifications searched | **0** | `C = 1/alpha = 0.1` derived from the shipped `Ridge(alpha=10.0)`; no grid, no tuning |
| Model fits | 200 | 2 per trading day × 100 days — one specification, refit prequentially |
| Comparators (not searched) | 4 | C1–C3 are published Lane 3 policies; C4 is 200 seeded random replicates |
| Reporting bases (not arms) | 2 | `open` / `policy` occupancy for the pick-rate test; both reported |

**Everything measured on already-opened development data** (February VAL-read wave 18; April+May opened
by the 2026-08-11 REJECT; June+July opened by the 2026-08-12 REJECT). **Nothing here has paid a
multiplicity bill against unread data, and no arm is admission-grade.**

---

## 9. Adversarial checks run against this lane's own findings

| claim | check | outcome |
|---|---|---|
| "composition prices non-fill for the first time" | derive `E[net] = P(fill)·E[net|fill]` and check whether the shipped target already equals it | **FALSE, and disclosed in the spec before the run.** It is an identity; the shipped ridge targets the same estimand. The lane's framing was corrected before it produced a number |
| the funnel is faithful | reproduce all five sealed reads on dispositions and R | **exact**, 5/5 months (§1) |
| the pick-rate instrument is faithful | reproduce Lane 3's published 0.0722 / 0.0184 / +0.00066 | **exact to 4 dp** (§1) |
| "the composed rule beats the shipped rule on the pre-specified reversal test, so the ranker is repaired" | check the economics of the same arm; then check the arm that maximises the metric | **REFUTED.** Clears both baselines at p 0.000 and books −76 R; `P(fill)`-only maximises both metrics and books −447 R. **The test itself is invalid on this population** (§5) |
| "`E[net\|fill]` has positive selection skill, p 0.045" | check *how* it earns it; then force it to trade | **CONFOUND.** 90.65 % of its picks never fill; as a policy it books −30.51 R (§5) |
| "B2 beats the shipped book" | day-clustered CI; per-month sign | **NIL.** +0.107 R, p 0.977, negative in 3 of 5 months (§6) |
| Lane 3's mechanism: "the model learned to predict *this order will trade*" | build that model explicitly (A7) and compare | **WEAKENED.** A pure fill detector books −447 R against the shipped +0.954 R. The shipped ridge's *failure* to be a good fill detector is load-bearing (§3) |
| "A1 lost because of one bad month" | per-month sign check | **NO.** Worse than shipped in **5 of 5** months |
| the whole result could be a lookahead artifact (a sibling lane just killed one) | audit every feature for same-day/forward aggregation; read the source helpers | **NO TARGET.** Basis adds no feature and contains no cross-candidate aggregate; every source helper is a backward slice (§7.1) |
| the frozen chain's wholesale day absorption is itself lookahead | measure the label horizon; then re-walk with embargo-1 and with strict label availability | **REAL BUT SMALL, AND REMOVED.** 5.0 % of rows, horizon capped at exactly 1.0 day; A1 goes **−76.14 → −102.48 / −81.63**, i.e. the refutation strengthens (§7.2) |
| the surviving positive is a same-day contamination | split the day at hour 12 and check which half carries it | **INVERTED SIGNATURE.** Signal is in the **early** half (+0.01471 vs +0.00940); a leak puts it in the late half (§7.3) |
| permutation nulls would have caught a leak | — | **NO — and this is the transferable warning.** Permutation nulls permute *labels*; a leak present in every permutation is invisible to all of them. Only the explicit temporal test finds it |
| A1's loss is an artifact of the logistic | substitute the estate's existing hierarchical Jeffreys cell fill model (A6) | **REPRODUCED.** −80.27 R, per-day −0.812, p 0.024. The finding is about composition, not about the fill estimator |

---

## 10. What this lane changes about the program's next move

1. **Retire R1 from Lane 3's repair table.** "Retrain the ranker on `terminal_net_r` conditional on
   FILL, with a separate fill model" was ranked the estate's highest-value repair and described as
   *"unquantified"*. It is now **quantified: −77.09 R against the shipped book, p 0.016**, and its two
   sub-variants (`E[net|fill]`-only ranking, MARKET-restricted ranking) are −31.46 R and −9.28 R. The
   repair is closed.
2. **Retire the pick-rate reversal test.** Any future ranker work on this population must be judged on
   the realised book of a complete policy, never on P(pick positive) or P(pick best) — both are
   maximised by the worst policies measured (§5).
3. **The abstain rule is confirmed for the third time, and now with a mechanism.** It is not
   discarding a cheap half; it is declining a population whose adverse selection composition can
   reduce by 90 % but not eliminate. Keep it, and do not build on it.
4. **The real finding for whoever works this next: the shipped book's +0.954 R is a non-transacting
   result.** 81.4 % of its argmaxes never fill; it places 290 orders across 100 trading days out of
   9,237 decision windows. Its edge is not selection skill (+0.00066 R/window, p 0.898) — it is
   abstention. Any change that makes the funnel trade more will lose money on this pool, and the four
   arms that traded 1,151–7,822 times all did, monotonically in trade count. **The constraint is the
   pool's expectancy, not the estimator**, and Lane 3 §8.1 already established there is no cost band,
   stop-width band or R:R band of this pool with positive expectancy.

---

## 11. Receipts

`b2_composed_rule/` — all JSON machine-written by the three scripts beside it.

| file | what |
|---|---|
| `B2_SPEC_V1.json` | the frozen spec, sha256 `6d4ebdea10fd1b8249e9d94c62504d2e2ff80ff5eee98efe041d908dae82e62e`, written before the first composed score |
| `instrument_validation.json` | the five-month sealed-read reproduction proof |
| `arms.json` | A1–A7 and C1–C4, pooled and per month, with the three judgement gates |
| `pickrate.json` | the ceiling-capture / reversal test, both occupancy bases, 2,000-draw day-clustered bootstrap |
| `abstain_crux.json` | the MARKET-top-abstain re-decision, `E[net \| LIMIT top fills]` per score |
| `constructive.json` | B1–B4, the post-hoc veto and rescue variants |
| `headtohead.json` | per-day paired bootstrap of every arm against the shipped book |
| `leaktest.json` | the temporal-leak controls: embargo-1, strict label availability, and the past/future hour split |
| `b2_bootstrap.py` | materializes the dev+January bootstrap (84,902 rows) once |
| `b2_walk.py` | the prequential two-stage walk, 100 days, 382,181 scores |
| `b2_walk_embargo.py` | the embargo-1 control re-walk |
| `b2_walk_avail.py` | the strict label-availability control re-walk |
| `b2_score.py` | the funnel (adapted from `lane3_receipts/funnel_lib.py`) and all seven scoring steps |

Inputs: `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` (632,934 occurrences);
`w21_predecision_ridge.py` (feature basis, pipeline, weights); Lane 3's exact daily-refit shipped
predictions. Bootstrap seed 20260812, day-clustered, 2,000 draws.
