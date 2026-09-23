# GEOMETRY_DEFECT_AND_ATR_SCALING_V1

**Two corrections to instruments, not searches for edge.** Part 1 repairs a
feature/label contradiction in the wave-21 outcome model and prices what the defect cost.
Part 2 quantifies, on the sleeve estate, the ATR-stop mis-scaling Lane I measured, and
prices the correction as a proposal for the owner.

Built 2026-08-11. Part 1's repair is on branch `swarm/geometry-defect-atr-scaling`
(tip recorded in §4). **Nothing live was touched: no armed sleeve's geometry moved, no
config byte moved, no VPS access, and Part 2 applies nothing.**

Every figure below carries a sample size and an interval, or is stated as an exact count.

---

## 1. Part 1 — the traced path

### 1.1 What was claimed, and what is actually true

The swarm's finding was that across 632,934 candidate occurrences the model's feature frame
encodes `target/stop = 1.5` while the labeler resolves the order at `2.0`. **Both halves
reproduce exactly**, measured here independently from the caches:

| quantity | value | rows | source |
|---|---|---|---|
| feature frame `target_distance_atr / stop_distance_atr` | **1.5**, no dispersion | **632,934 / 632,934** | `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` via `laneG-walk/pool_table.npz` |
| submitted order `\|take_profit_1 − entry\| / \|entry − stop\|` | **2.0** (min = max = 2.000000000) | **81,968 / 81,968** | `/private/tmp/laneG-walk/lg_{feb,apr,may,jun,jul}.pkl.gz` |
| `risk_reward_ratio` field | **2.0** | 81,968 / 81,968 | same |
| `dynamic_geometry_policy` | `momentum_exhaustion` | 81,968 / 81,968 | same |
| `raw_target_r`, `policy_target_r` | **2.0** where present | 37,377 present, `None` on the rest | same |

Per-month order geometry, all five months, min = max = 2.000000000:
feb n=16,322 · apr n=16,587 · may n=14,546 · jun n=18,268 · jul n=16,245.

### 1.2 The mechanism, file by file

1. `config/agent_config.yaml:39` — `risk.min_rr: 1.5`, whose own comment reads *"vNext
   sanity floor only; dynamic policy sets live targets."* It is a risk sanity floor and it
   says so.
2. `src/components/broader_origin_generators.py:3687-3697` — `_target_rr(config)` returns a
   `TargetRRPolicy` equal to `risk.min_rr` for every numeric purpose. `:465` passes it into
   generation as `target_rr`.
3. `_candidate(...)` writes `take_profit_1 = entry ± target_rr × risk` and
   `risk_reward_ratio = target_rr`. Pinned by
   `tests/test_broad_origin_target_policy.py::test_default_path_preserves_legacy_geometry`.
4. **`src/components/broader_origin_generators.py:3833-3834`** — the predecision feature
   block is computed from that same generation-time target:
   ```python
   features["stop_distance_atr"]   = _safe_ratio(abs(entry - stop),   atr14)
   features["target_distance_atr"] = _safe_ratio(abs(entry - target), atr14)
   ```
   so `target_distance_atr / stop_distance_atr ≡ target_rr ≡ min_rr`, identically, by
   construction.
5. **Downstream**, the replay's execution-policy router selects `momentum_exhaustion`
   (`src/research_infra/v4_timewarp_simulated_live_research_loop.py:62405+` →
   `src/research/dynamic_execution_policy.py:167-186`, `final_target_r: float = 2.0`) and
   the order's take-profit is rewritten to 2.0 R. **The predecision feature block is never
   recomputed after that rewrite.**
6. It is then carried verbatim into the model frame —
   `src/research_infra/wave21_forward_shadow/feature_contract.py:244` at `origin/main`
   (`:375` after the repair in §2):
   `**{key: number(source_features.get(key)) for key in _PREDECISION_NUMERIC_KEYS}`.
7. The labeler follows the **order**:
   `outcome_authority/candidate_funnel_analysis.py:141` `target = float(source_row["take_profit_1"])`,
   passed to `resolve_post_submission_m1_lifecycle(..., approved_target_price=target)`.

**In one line: the feature tracks the risk dial; the order tracks the execution policy.**

### 1.3 Why it survived five months of reads — and the scope correction

The defect is **not** universal across the estate, and the swarm's framing ("one population,
two contradictory geometries") is right for the five-month cache but wrong as a statement
about every window. Measured on the frozen training corpus
(`forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz`, 284,652 rows), the feature ratio splits
**perfectly by generation window**:

| window | feature `target/stop` | rows | order `\|tp1−entry\|/\|entry−stop\|` | coherent? |
|---|---|---:|---|---|
| 2025-10, 2025-11 | **2.0** | 32,249 | 2.0 | **yes** |
| 2026-01 | **2.0** | 52,653 | 2.0 | **yes** |
| 2026-02, 2026-04, 2026-05 | **1.5** | 199,750 | 2.0 | **no** |

The order-side figures for Oct/Nov/Jan are measured directly: I opened the sealed compact
ledgers for `2025-10-27` (n=6,563), `2025-11-07` (n=6,269) and `2026-01-05` (n=6,488) —
19,320 rows — and `|tp1−entry|/|entry−stop|` is **2.0 on 100 % of every one**, with
`dynamic_geometry_policy = momentum_exhaustion` on 100 %.

So the frame and the order agreed on Oct/Nov/Jan **only because the sealed replay set
`min_rr = 2.0`** (`phase19/receipts/pbg/pbg_run.py:89-90`) — the same number
`momentum_exhaustion` hardcodes. That coincidence is why five months of reads never tripped
over it: the two earliest, most-scrutinised windows were the coherent ones.

### 1.4 A correction to the committed record (Lane G)

`LANE_G_INDEPENDENT_VERIFICATION_V1.md` §3a attributes the 1.5 to
`src/research_infra/current_ob_retest_geometry_candidate.py:23,181` (`TARGET_DISTANCE_D = 1.5`).
**That attribution is wrong**, and it matters because it points a repair at the wrong file.
That module is a default-off research transform: `DEFAULT_ENABLED = False`,
`ENABLE_SURFACE = "explicit_research_argument_only"`, and its own docstring says *"The
transform is intentionally unreachable from runtime candidate generation."* It is also
scoped to a single origin family (`ORIGIN_FAMILY = "current_ob_retest"`), so it cannot
produce 632,934 rows across eleven families. The 1.5 is `risk.min_rr`, via the path in §1.2.

Lane G's *measurements* in §3a all reproduce; only the attribution sentence is struck.

---

## 2. Part 1 — the repair

Committed on `swarm/geometry-defect-atr-scaling` as one commit touching two files:
`src/research_infra/wave21_forward_shadow/feature_contract.py` (+136) and a new
`tests/research_infra/test_wave21_target_geometry_coherence.py` (12 tests).

**The repair is basis-aware rather than in-place, deliberately.**
`SHADOW_RIDGE_MODEL_V1.json` was *fit* on the as-generated frame, and its consumers include
the default-off shadow runner. Silently re-pointing the feature underneath a model whose
coefficients were fit on the other basis would replace a stale feature with a **train/serve
skew**, which is strictly worse than the defect. So:

* `TARGET_GEOMETRY_AS_GENERATED` (default) — the generator's value, **bit-identical** to
  the frozen frame, so every sealed read still reproduces and the fitted artifact keeps
  seeing exactly what it was fit on. Pinned by
  `test_default_basis_is_bit_identical_to_the_frozen_frame`.
* `TARGET_GEOMETRY_AS_TRADED` — `traded_rr × stop_distance_atr`, where
  `traded_rr = |take_profit_1 − entry_price| / |entry_price − stop_loss|`. This is the frame
  that describes the contract the labeler resolves.
* `target_geometry_coherence(raw)` — returns both RRs and a verdict
  (`COHERENT` / `INCOHERENT_ORDER_TARGET_WIDER_THAN_FRAME` /
  `INCOHERENT_ORDER_TARGET_TIGHTER_THAN_FRAME` / `NOT_EVALUABLE`). Absence never reads as
  agreement — a silent default is how the 1.5 got here in the first place.

Two implementation choices worth stating because they are load-bearing:

* The repaired feature is expressed as `traded_rr × stop_distance_atr`, **not**
  `|take_profit_1 − entry| / atr14`. It must keep the *same* `atr14` denominator the
  generator used for `stop_distance_atr`, and that is not the `atr14` the shadow has to hand:
  measured, `stop_distance_atr` and `risk_over_atr` (which uses
  `predecision_limit_fillability.atr14`) agree on only **21,212 of 284,652** corpus rows,
  max |diff| 13.64. Expressing the repair as a ratio times the existing column changes the
  target geometry and nothing else — pinned by
  `test_default_basis_leaves_every_other_feature_alone`, which asserts exactly one column
  moves.
* Three tests **fail against the pre-repair implementation** by construction
  (`test_as_traded_basis_restates_the_target`, `test_incoherent_row_is_detected`,
  `test_unknown_basis_fails_loud`). A test that passes against the old code proves the
  change is different, not that it is a fix.

---

## 3. Part 1 — what the defect cost: the refit

**Answer: nothing measurable, and the reason is structural rather than empirical.**

### 3.1 The structural result

On any population generated at a single `min_rr`, `target_distance_atr` is an **exact
positive scalar multiple** of `stop_distance_atr`. `StandardScaler` maps `x₂ = c·x₁` (c > 0)
to the *identical* standardised column, so the feature carries **exactly zero incremental
information — under both bases**. Measured on the homogeneous 199,750-row sub-corpus:

| basis | `max |z(target_distance_atr) − z(stop_distance_atr)|` |
|---|---|
| as-is (1.5×) | 3.126 × 10⁻¹³ |
| repaired (2.0×) | **0.000 × 10⁰** |

Repairing the feature therefore *cannot* move a prediction on a single-basis population.
This is a property of the design matrix, not a claim about markets, so it is pinned by a
test (`test_target_is_an_exact_multiple_of_stop_under_both_bases`) rather than argued.

### 3.2 The empirical refit

Refit with the frozen rule's exact pipeline (`daily_refit.make_rule_pipeline`: constant-0
impute + missingness indicator → `StandardScaler` → `OneHotEncoder` → `Ridge(alpha=10,
solver="lsqr")`) and the rule's `1/window` sample weights, time-ordered train/test split.
Arms: **as-is** vs **repaired** (`target_distance_atr := 2.0 × stop_distance_atr`).

**(a) Homogeneous population** — Feb/Apr/May 2026, frame at 1.5, order at 2.0.
n = 199,750 (train 136,850 / test 62,900, test from 2026-05-05). The repair changes
199,750 of 199,750 rows' feature values.

| | as-is | repaired |
|---|---:|---:|
| OOS R² | −0.005422 | −0.005424 |
| OOS RMSE | 0.559389 | 0.559389 |
| top-1-per-window mean net R (n = 1,559) | **−0.02503 ± 0.02090** | **−0.02503 ± 0.02090** |

**Top-1 selections are identical in 1,559 / 1,559 windows (100.00 %).** The repair does not
change a single decision. Residual prediction difference is solver tolerance
(max |Δ| 2.29 × 10⁻⁴, Pearson r = 0.99999997), not a real effect.

**(b) Full mixed-basis corpus** — n = 284,652 (train 199,878 / test 84,774, test from
2026-04-22). Here the repair does something real but small: it removes the
**generation-epoch marker** (ratio 1.5 vs 2.0 is a proxy for which run produced the row).

| | as-is | repaired |
|---|---:|---:|
| OOS R² | −0.003306 | −0.003236 |
| OOS RMSE | 0.560966 | 0.560946 |
| top-1-per-window mean net R (n = 2,159) | −0.020677 ± 0.017669 | −0.020010 ± 0.017726 |

Selections differ in **76 of 2,159** windows (3.5 %). Paired delta
**+0.000667 R/trade, 95 % CI [−0.003398, +0.004130]** (10,000-resample paired bootstrap,
seed 20260811). Zero is comfortably inside; the point estimate is **0.18 ×** the CI
half-width.

### 3.3 What this means — it strengthens Lane I

**OOS R² is negative in all four fits.** Both arms, both populations, the model is worse
out of sample than predicting the test-set mean. The defect was real, the repair is real,
and the model's predictive performance is unchanged because *there was no predictive
performance to change*.

This is the honest reading, and it is the one the caller asked for in advance: it
**strengthens** Lane I rather than weakening it. Lane I's claim was that the 43 recorded
predecision features carry no out-of-sample directional information. A live objection to
that claim was that one of those features was demonstrably wrong — so perhaps the emptiness
was an artifact of the defect. It is not. With the frame restated onto the contract the
labeler actually resolves, the result is the same to three decimal places, and one of the
43 features turns out to have been carrying **exactly zero** information all along in any
case, because it was a rescaled copy of another feature.

**What this does *not* license.** It does not say the geometry defect is harmless in
general — only that it is harmless *to this ridge on this corpus*. Any consumer that reads
`target_distance_atr` as a **level** (an economic quantity, a cost model, an EV calculation,
a filter threshold) rather than as a standardised regressor was reading a number 33 % too
small on 632,934 rows, and this measurement says nothing about those. The coherence
detector now makes such a consumer's exposure visible.

---

## 4. Part 1 — branch and suite A/B

**Branch `swarm/geometry-defect-atr-scaling`, tip `6578d5275`**, one commit off
`origin/main` at `b0fe2daf0`. Pushed, **not merged**.

Full-suite failure-set A/B, both sides captured with
`scripts/pytest_failset.py capture` (`--continue-on-collection-errors`, whole `tests/`):

```
before b0fe2daf0 ('Lane G corrections applied to the committed record: …'): 53 bad
after  6578d5275 ("Geometry defect repaired: the model frame's take-profit is now the order's"): 53 bad
unchanged: 53   fixed: 0   REGRESSED: 0
No regressions.   DIFF_EXIT=0
```

| | before (`b0fe2daf0`) | after (`6578d5275`) |
|---|---:|---:|
| failed | 52 | 52 |
| errored | 1 | 1 |
| passed | 13,865 | **13,877** |
| skipped | 123 | 123 |
| xfailed | 32 | 32 |

**The failure sets are identical by identity** — 53 unchanged, 0 fixed, 0 regressed — and
the change adds **+12 net new passing tests**, which is exactly the new
`tests/research_infra/test_wave21_target_geometry_coherence.py`. The 53 standing failures are
the estate's pre-existing baseline and are untouched by this branch.

---

## 5. Part 2 — the ATR stop mis-scaling on the sleeve estate

**Headline: the relationship is real, large and monotone — and correcting the estate's stops
for it does not pay. The recommendation is DO NOT DEPLOY, and the reason is not "the effect
is small"; it is that a placebo reproduces most of the result.**

Measured on the sleeve corpus only (`phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz`,
22,354 trades) and the estate's own bar archive `/Users/borr/GTOSActive/vps-bars-20260727`,
via the estate's own walker
(`phase20/receipts/r1/r1_frontier_surface_sweep.py:105 walk(...)`). Per Lane C, **no funnel
evidence is cross-credited** — nothing from the candidate caches enters this section.
Full artifact: `/private/tmp/atr-scaling-20260811/ATR_SCALING_ESTATE_V1.json`.

### 5.1 The relationship (Step A — bars only, no trade outcomes)

`y = travel / ATR14` regressed on `v = ATR14 / ATR50`, `log(y) = b₀ + β·log(v)`, 80-bar
forward window, 3,531,865 bar-rows over 123 (symbol, timeframe) series. Standard errors are
symbol-block bootstrap (2,000 draws) and CR1 clustered on symbol — never naive OLS, because
bars are autocorrelated.

| timeframe | n rows | β | 95 % CI (block bootstrap) | R² | Q0/Q4 mean y |
|---|---:|---:|---|---:|---:|
| M15 | 2,570,553 | **−0.9336** | [−0.9532, −0.9117] | 0.305 | 2.323 |
| H4 | 826,115 | **−0.7541** | [−0.7806, −0.7210] | 0.097 | 1.441 |
| D1 | 135,197 | **−0.6136** | [−0.6607, −0.5595] | 0.059 | 1.329 |

The published Q0/Q4 magnitudes reproduce **on the H4 tape**: 1.227 at a 4 h horizon and
1.389 at 5 d, against the claimed 1.26× and 1.42×. They do not reproduce as a
series-independent constant (M15 gives 1.466 at 4 h and 2.201 at 5 d), so "1.26–1.42×" is an
H4 statement and should be cited as one.

**The caveat that governs everything downstream.** Replace the contemporaneous `ATR14` in
the denominator with a *disjoint past* `ATR14` (window [i−27, i−14]) and **the sign flips
positive at every timeframe and horizon** (β_lag +0.13 to +0.81). Raw travel actually
*rises* with the vol ratio at short horizons (γ +0.22 to +0.61). So travel-per-ATR14 falls
with `ATR14/ATR50` because **ATR14 itself mean-reverts** — it is a property of the estimator
in the denominator, not a property of the volatility regime. That still licenses rescaling a
stop pegged to the *contemporaneous* ATR14, which is what most of these sleeves use, but the
finding must be described as an estimator property or it will be over-read.

### 5.2 The correction, and the controls that decide it

Per-trade `stop_mult = v^β` (β matched to the trade's timeframe), then **normalised per
sleeve so the geometric mean is exactly 1.0**. That normalisation is essential: it isolates
the *cross-sectional* re-scaling — which is the actual finding — from a global stop
widening, which is a different intervention already on AD's grid. Post-winsorisation to
[0.5, 2.0] (binding on 86 of 22,205 trades, 0.39 %) the per-sleeve geomean stays
1.0000 ± 0.0007.

Controls proven before any result was read:

* the per-trade walker copy is faithful — with every multiplier set to 1.0 it reproduces
  `walk(..., stop_mult=1.0)` on 16 cells × 5,733 values, **0 differing, max abs difference
  0.0**, identical exit-reason counts and identical by-day buckets;
* the uncorrected arm reproduces the estate's published `r_gross` on **22,343 / 22,343 rows,
  max abs error 0.0**;
* vectorised ATR matches scalar `atr_n`, which matches `primitives.atr14`, to < 1.6 × 10⁻¹².

### 5.3 Per-sleeve results — armed sleeves called out

Band = mid, `corrected=True` (repaired quote convention), each sleeve's native target
convention. Δ = CORRECTED − CONTROL, paired by trade, 10,000-resample bootstrap.

**ARMED — and the armed set changed underneath this measurement.** The walk was designed
against the four-sleeve armed set. At **2026-08-11T11:47:56Z**, mid-measurement,
`sub_mid_dn_revert` was **DISARMED on both accounts** by owner decision (`ed4d071f1`, host
commit `47d0960e6`, on `W7_INSTRUMENT_RESTATEMENT_V1.md`'s corrected-instrument evidence —
unrelated to this work). `config/live_armed_set.json` at `origin/main` now reads
**`crypto, energy_agri, sub_xvol_pullback`** on both accounts, `frontier_exits: []`. The
table below marks the current three as ARMED and `sub_mid_dn_revert` as **just-disarmed**;
§5.4 reports both subtotals, because the four-sleeve one is what was measured and the
three-sleeve one is what is live.

| sleeve | n | CONTROL R/trade (95 % CI) | CORRECTED R/trade (95 % CI) | Δ paired (95 % CI) | CI≠0 | stop-rate C→N | maxDD R C→N |
|---|---:|---|---|---|:-:|---|---|
| **crypto** (ARMED) | 181 | +0.4339 [+0.151, +0.728] | +0.3888 [+0.104, +0.688] | −0.0451 [−0.255, +0.166] | – | 0.608→0.624 | 10.8→13.4 |
| **energy_agri** (ARMED) | 67 | +0.7785 [+0.234, +1.338] | +0.4928 [−0.030, +1.022] | **−0.2857 [−0.575, −0.061]** | **YES** | 0.597→0.642 | 16.6→16.5 |
| **sub_xvol_pullback** (ARMED) | 88 | +1.2676 [+0.860, +1.671] | +1.3636 [+0.955, +1.768] | **+0.0959 [+0.003, +0.233]** | **YES** | 0.420→0.398 | 6.0→6.0 |
| `sub_mid_dn_revert` (disarmed 2026-08-11) | 524 | +0.2061 [+0.046, +0.366] | +0.1374 [−0.015, +0.290] | **−0.0687 [−0.130, −0.008]** | **YES** | 0.698→0.716 | 81.0→81.0 |

**Rest of the estate** (23 sleeves; only those whose paired CI excludes zero are called out —
the full 27-row table is in the JSON):

| sleeve | n | CONTROL R/trade (95 % CI) | Δ paired (95 % CI) | CI≠0 |
|---|---:|---|---|:-:|
| fx_jpy | 3,984 | −0.0473 [−0.095, +0.002] | **−0.0212 [−0.042, −0.001]** | **YES** |
| mx_nzdjpy_d1_donchian | 503 | −0.1178 [−0.233, +0.004] | **−0.0299 [−0.060, −0.000]** | **YES** |
| mx_avausd_d1_donchian | 189 | +0.0925 [−0.110, +0.302] | −0.0983 [−0.209, +0.003] (low band −0.1103, excludes 0) | partial |
| asia_pdl_fade | 2,827 | −0.3289 [−0.383, −0.273] | +0.0038 [−0.027, +0.035] | – |
| idxrev | 5,597 | −0.0138 [−0.036, +0.009] | −0.0016 [−0.012, +0.009] | – |
| metals_core | 384 | +0.1551 [−0.031, +0.341] | +0.0118 [−0.065, +0.089] | – |
| mx_btcusd_d1_donchian | 318 | +0.3491 [+0.189, +0.509] | +0.0189 [−0.057, +0.104] | – |
| vol_compression | 391 | +0.3301 [+0.151, +0.518] | −0.0574 [−0.127, +0.007] | – |

**EXCLUDED, control arm only** — the entry signal reads the risk distance
(`market_expansion_d1.py:211`, `ad_exit_sweep.py:143 STOP_DEPENDENT_SIGNAL`), so rescaling
the stop changes *which trades exist* and a re-walk of the recorded trades would measure a
different candidate set: `mx_us100_cash_d1_atr_mean_reversion` (n=71, CONTROL −0.2394
[−0.535, +0.056]) and `mx_us500_cash_d1_atr_mean_reversion` (n=67, CONTROL −0.1493
[−0.463, +0.209]).

### 5.4 Totals

| | n | CONTROL (95 % CI) | CORRECTED (95 % CI) | Δ paired (95 % CI) | stop-rate C→N (Wilson) | maxDD R C→N (Δ CI) |
|---|---:|---|---|---|---|---|
| **ESTATE (27 sleeves)** | 22,205 | −0.0264 [−0.045, −0.008] | −0.0379 [−0.056, −0.020] | **−0.0115 [−0.0196, −0.0035]** | 0.6313 [0.6250, 0.6377] → 0.6350 [0.6287, 0.6413] | 893.3 → 1030.5 (Δ CI [−9.5, +304.7]) |
| **ARMED FOUR** (the set at measurement time) | 860 | +0.4073 [+0.280, +0.539] | +0.3435 [+0.215, +0.472] | **−0.0638 [−0.1267, −0.0011]** | 0.6430 [0.6104, 0.6743] → 0.6581 [0.6258, 0.6891] | 63.0 → 73.6 (Δ CI [−10.6, +26.9]) |
| **ARMED THREE** (live now, after the 08-11 disarm) | 336 | +0.7210 [+0.4991, +0.9428] | +0.6648 [+0.4469, +0.8828] | **−0.0561 [−0.1847, +0.0725]** | – | – | – |

The armed-three row is recomputed by n-weighting the three per-sleeve paired deltas and
combining their standard errors across sleeves as independent — **not** a pooled paired
bootstrap, and labelled as such. It matters that it changes the verdict's shape: with
`sub_mid_dn_revert` removed, the armed-set delta's interval **includes zero**
(−0.0561 [−0.1847, +0.0725], n = 336). So the correct statement about the live book today is
not "the correction loses on armed money" but **"on the live armed set the measurement is
inconclusive, and on the estate it loses."** The recommendation in §6.1 is unchanged, but it
rests on the estate result and the placebo control, not on an armed-set effect.

Sign is stable across cost bands — estate low −0.0148 [−0.023, −0.006], high −0.0108
[−0.019, −0.003]; armed-four low −0.0978 [−0.156, −0.040], high −0.0656 [−0.127, −0.006]. All
six exclude zero, all negative.

### 5.5 The control that kills it, and the honest reading

**A placebo reproduces most of the loss.** Permuting the *same* multipliers at random within
each sleeve (20 draws) costs **−0.0077 R/trade** (sd 0.0027, range [−0.0117, −0.0022])
against the real assignment's −0.0115. The real value sits **inside** the placebo range,
z = −1.39. The **anti-correction** (β sign flipped) costs −0.0070, statistically
indistinguishable from the placebo. So *neither direction* of the vol-ratio tilt pays:
per-trade stop jitter at geomean 1.0 is intrinsically costly on this population, and the
ATR14/ATR50 assignment adds only about −0.004 R/trade of its own on top.

On the **armed four as measured** the real assignment (−0.0638) *is* outside the placebo
range [−0.0625, +0.0228], one-sided p ≈ 1/21 = 0.048 — weak evidence that the signal
actively hurts there, at a resolution floor of 1/21 with four sleeves tested. That evidence
is carried mostly by `sub_mid_dn_revert`, which is no longer armed (§5.3); on the live three
the interval includes zero, so this line does **not** transfer to the current book.

**Why a real β can fail to pay.** β prices *forward travel per unit of stop*. Realised R is
not travel — it is a race between a stop and a target that **both move with the rescale**,
resolved bar by bar under the pessimistic same-bar tie rule. A stop exit is exactly −1 R and
a target exit exactly +k R *in units of the same stop that was just rescaled*, so only
**3,741 of 22,205** trades change R at all and 1,034 change exit reason. Pooled stop-out rate
rises 0.6313 → 0.6350 while mean R falls.

**The premise does not hold uniformly, and it fails worst where it costs most.** Measured
`sl_distance_price / ATR14` at the decision bar: 18 sleeves are exactly ATR14-pegged
(CV = 0.00 — crypto ×2.000, sub_mid_dn_revert ×1.000, every `mx_*` ×1.000), but
`energy_agri` (CV 0.49), the three metals sleeves (0.55–0.70), `asia_pdl_fade` (0.69) and
`liq_asia_up_low_metal` (0.56) set stops **structurally**. `energy_agri` — the single biggest
casualty at −0.2857, and armed — is one of them. Applying an ATR14-derived rescale there was
the least-justified case in the set, so its loss should not be read as evidence about the
correction's merit.

**How thin the one improvement is.** `sub_xvol_pullback`'s +0.0959 rests on **six**
materially-changed trades out of 88, two of them exit-reason flips. Its placebo z is +2.48
with 0/20 placebos matching — but 27 sleeves were tested against a permutation floor of
p = 1/21, so ≈1.3 false positives per tail are expected and three sleeves reached p = 0.00 on
the positive side. **Treat it as a hypothesis worth a dedicated test, not a result.**

**Out of scope, stated so it is not inherited.** The four `partial_be_runner` sleeves
(`metals_core`, `metals_softband`, `metals_ob_micro`, and the armed `energy_agri`) are walked
at AA's plain stop/target/maxbars contract, **not** their live scale-out — so `energy_agri`'s
−0.2857 describes a contract the book does not run. Sizing, portfolio admission and the
governor are all outside this walk; these are gross R with only the quote-side spread anchor
applied.

---

## 6. Part 2 — deployment path, cost, and the multiplicity bill

**This is a proposal for the owner, and the proposal is NO-GO.** Nothing here was applied.
The section states the path and its price anyway, because that is what was asked and because
the price is itself an argument.

### 6.1 Recommendation

**Do not deploy the ATR14/ATR50 stop correction, on any sleeve, including
`sub_xvol_pullback`.** The estate-level and armed-level effects are negative with CIs
excluding zero, and — decisively — a within-sleeve permutation placebo reproduces most of the
estate effect while the sign-flipped anti-correction is statistically indistinguishable from
it. An intervention whose placebo performs as well as the intervention has not been shown to
carry information about the thing it claims to correct.

The one positive cell (`sub_xvol_pullback`, armed, +0.0959 R/trade on 88 trades, six of them
materially changed) does not clear the multiplicity bill in §6.4 and rests on a sample that
cannot support arming.

### 6.2 What would have to change

1. **A per-trade multiplier is not expressible today.**
   `execution_packets.py:530-535` applies `risk_distance = base_risk_distance ×
   stop_distance_multiplier`, and `stop_distance_multiplier` is a **scalar constant** read
   from the sleeve's exit profile (`resolve_exit_profile`, `:409-419`). An ATR-ratio-dependent
   multiplier is a per-decision quantity, so the profile schema would have to carry a
   *callable or parameterised* multiplier evaluated at packet-build time. That is a
   structural change to the live geometry path, not a config value.
2. **A new live input: ATR50.** Measured — **there is no ATR50 anywhere in the live book**
   (`rg` over `src/components/ultimate_book/` returns nothing). Only `primitives.atr14`
   exists. Deployment requires an `atr_n` primitive plus a guaranteed ≥ 50-bar window on each
   sleeve's own timeframe at decision time, with a fail-closed path when it is short —
   otherwise the multiplier silently degrades toward 1.0 and the book runs a geometry nobody
   declared. (The `mx_*` cohort's bar-window hazard at `_trading_m15_bars_since` is a
   separate, already-filed issue that would interact with this.)
3. **Two sleeves cannot take it at all** — `mx_us100_cash_d1_atr_mean_reversion` and
   `mx_us500_cash_d1_atr_mean_reversion`, whose entry signal reads the risk distance. For
   them the change is not a re-scale but a different strategy, and it would need generation
   from scratch rather than a re-walk.
4. **Declaration + launcher invariant.** Any arming change must move
   `config/live_armed_set.json` and `scripts/run_book_supervisor.ps1` in the same commit or
   `tests/safety/test_armed_set_single_source.py` fails.

Seal and token status, measured: `execution_packets.py` is **not** an R2-bound path, so the
change would not break the decision contract; and the activation-token digest hashes
`config/agent_config.yaml` plus the active profile bytes only, so a code-only change does
**not** require a token re-mint. Neither of those is a reason to proceed — they are simply
the two costs that would *not* be incurred.

For the record, current live geometry: the `stop_distance_multiplier = 1.5` entry for
`crypto` sits in `FRONTIER_EXIT_OVERRIDES` and applies only when the sleeve is named in
`--frontier-exits`. `config/live_armed_set.json` declares `frontier_exits: []`, and CM was
rolled back 2026-08-10, so **no armed sleeve currently carries a stop multiplier ≠ 1.0.**

### 6.3 What would have to be re-certified

The 2.0 % dial (`clean3_w7_ceiling_nom2p00`) was certified under an envelope in which each
sleeve's **R unit is its recorded stop distance**. Risk percentage is fixed, so lot size
scales inversely with stop distance: a per-trade stop rescale changes position size on every
trade, and therefore the realised R distribution, the equity path and the drawdown path.
Consequently:

* **`BOOKS_MC_V1` must be re-run** — the armed set's P2 `p_pass` (0.9172 FTMO / 0.9331
  redacted_account) prices the recorded geometry and does not survive the change by assumption.
  Measured here, the armed four's max drawdown moves 63.0 → 73.6 R (Δ CI [−10.6, +26.9]) and
  the stop-out rate rises 0.6430 → 0.6581 — both in the direction that costs `p_pass`. Those
  are the four-sleeve figures; the live three would have to be re-measured, and the MC re-run
  against the post-08-11 armed set regardless.
* The dial itself would need re-ratification if `p_pass` moves materially, and that is
  Borhen's call, not an implementation detail.
* The measurement supporting any re-certification would have to be redone at the
  `partial_be_runner` sleeves' **live** contract, not AA's plain walk — which is the gap that
  makes `energy_agri`'s number unusable for a live decision today.

### 6.4 The multiplicity bill

The ratified rule is `CANDIDATE_BOOK_V1`, all-declared basis, sealed α = 0.10
(`phase18/receipts/CANDIDATE_FAMILY_V27.json` → `ratified_rule`). The family tip is
**59 declared members**.

A stop-scaling cell is a new declared member per sleeve it is evaluated on:

| scope | new looks | family size | BH rank-1 bar at α = 0.10 |
|---|---:|---:|---:|
| armed sleeves only (3 live today; 4 as measured) | 3–4 | 62–63 | 0.10 / 63 = **0.00159** |
| whole estate (27 walkable sleeves) | 27 | 86 | 0.10 / 86 = **0.00116** |

Every measured effect either fails that bar or is on the wrong side of zero. The single
positive cell, `sub_xvol_pullback`, has a permutation p-value **floored at 1/21 = 0.048** by
its own 20-draw null — an order of magnitude above the rank-1 bar, and unable to reach it
without a much larger permutation budget on a sample of 88 trades with six material changes.
**There is no admission available here at the ratified rule**, which is why §6.1 is a NO-GO
rather than a deferral.

### 6.5 What is worth doing instead

Two cheap, non-deployment follow-ons the measurement earns:

1. **The estimator finding is worth keeping.** β is real, monotone and large, and the
   disjoint-window control identifies it as ATR14 mean-reversion rather than a regime effect.
   That is a fact about the *instrument* every ATR14-pegged sleeve uses, and it belongs in the
   sleeve dossier as a documented property — independent of whether any stop is ever rescaled.
2. **`sub_xvol_pullback` deserves one dedicated, pre-registered test** with a real permutation
   budget (≥ 10,000 draws, not 20) and its live contract, on a declared single-member family —
   which is a ~1-session research task with no live exposure. That is the only cell in the set
   with a positive sign, an armed sleeve, and a mechanism story; it is also the cell most
   likely to be a false positive, and one clean test settles it either way.
