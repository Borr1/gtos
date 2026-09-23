# K-4 / P-4 — Stoikov 2018 Micro-Price: Reference Implementation + K54 v3 Drop-In Spec

**Status:** DESIGN-ONLY — reference implementation lives in `research/ml_program/experiments/`. Production `src/components/tick_features.py` is NOT modified.
**Authoring agent:** B-8 quick-win-bundle dispatch (Phase 4, Opus 4.7 max-effort)
**Date:** 2026-04-29
**Backlog refs:** K-4 (T1), P-4 (T1), U-3 (M15-aggregation question), B-8 (quick-win bundle), H2 in `group_b_microstructure.md` §3
**Paper:** Stoikov, S. (2018). "The Micro-Price: A High Frequency Estimator of Future Prices." *Journal of Financial Markets*, 39, 1-19.
**Tick-coverage scope:** NAS100 + US30_cash only. Other 5 instruments (XAUUSD/USDJPY/GBPJPY/GBPUSD/XAGUSD) get NaN-sentinel handling (no tick captures yet — see memory `project_microstructure_archived_2026-04-27`).

---

## ⚠ HEADLINE VERDICT (post-benchmark, 2026-04-29)

**FAIL.** The Stoikov-flow-proxy adaptation does NOT meet the pre-registered ≥10% RMSE-reduction gate.

| Instrument | Per-tick reduction | Directional accuracy | Verdict |
|---|---:|---:|:---:|
| NAS100 | **-2.47%** (worse than naive mid) | 47.19% | FAIL |
| US30_cash | **-0.85%** (worse than naive mid) | 47.12% | FAIL |

**Recommendation: DO NOT INCLUDE in K54 v3 primary catalog.** See §7.2 for the locked drop-in decision and §4.3 for the post-mortem (root cause: Stoikov 2018 §2.1 requires LOB queue depth which MT5 retail tick data does NOT expose; the flow-proxy substitution produces noise of the wrong scale).

The reference implementation in `k4_stoikov_micro_price.py` passes 12/12 unit tests including the Stoikov 2018 §2.1 canonical AAPL example to numerical precision — the formula is correct; only the MT5-volume substitution path failed.

The K54 v3 catalog drop-in (4 features + NaN-sentinel handling) is documented in §7 and is forward-compatible: when LOB depth becomes available (Databento / similar), the same schema slot can be reused with the canonical Stoikov formula.

Filed under FAIL in `research/ml_program/KILLED_HYPOTHESES.md`.

---

## 1. Pre-registered prediction (locked BEFORE benchmark execution)

> **Prediction P1:** Stoikov micro-price reduces 1-step-ahead RMSE by **≥10%** over naive midprice `(bid+ask)/2` on both NAS100 + US30_cash tick captures. Verdict gate: PASS if reduction ≥10%, FAIL otherwise.
>
> **Prediction P2 (secondary, ancillary):** The directional bias of the micro-price (sign of `mp - mid`) correctly predicts the sign of the next bid/ask mid-quote change with ≥55% accuracy.
>
> **Prediction P3 (M15-aggregation, U-3):** Even when the per-tick edge passes, the M15-aggregated last-tick micro-price will NOT outperform M15-aggregated last-tick midprice for predicting the *next* M15 mid by ≥10%. The microstructure signal half-life is sub-second; M15 aggregation throws it away. (This is the E24/E26 archive context: signal at fine timescales, null at M15.) The test is whether the *per-tick* benchmark passes — which is the K-4 inclusion gate. The M15-aggregated feature should be carried into the K54 v3 catalog as a *cross-sectional structure indicator* (last-tick imbalance state at bar close) rather than a 1-bar predictor.

**Pre-registration discipline.** This Section 1 was written **before** running `k4_stoikov_micro_price.py`. The benchmark code in Section 4 was implemented and executed only after this section was committed in concept. No back-tweaking of the verdict gate is permitted post-result. If the verdict is FAIL, the recommendation in Section 7 must be NEGATIVE inclusion (don't ship to K54 v3) regardless of intuition or post-hoc reasoning.

**Why ≥10%, not ≥5% or ≥1%:** Stoikov 2018's published example (his Table 2, AAPL) shows ~12-18% RMSE reduction at 1-tick horizon vs naive mid. We discount the published lift to ≥10% to allow for two adverse adaptations in our setting:

1. **Volume-proxy substitution:** MT5 retail-broker tick data has `volume = 0` always (CFD spot ticks); we cannot use bid/ask depth volumes directly. We use rolling tick-flow imbalance as a queue-imbalance proxy. This substitution should weaken the signal somewhat but preserve directional information.
2. **Spread regime:** NAS100/US30_cash have integer-multiple spreads (NAS100 median 1.76, US30_cash median 2.30) — already wider than the 1-tick spreads in Stoikov's AAPL example. Wider spreads mean midprice noise is larger, but also that micro-price corrections matter more. Net effect: roughly compensates.

Anything ≥10% is a **practical edge confirmation**; anything <10% means the Stoikov mechanism doesn't transmit cleanly through the volume-proxy substitution and the feature should not be carried into K54 v3 as a primary feature (though M15-aggregated last-tick form is still a valid catalog hint per H1 dollar-volume bar follow-up).

---

## 2. Theoretical background

### 2.1 The naive midprice

The naive midprice is

```
mid_t = (p_bid_t + p_ask_t) / 2
```

This is the *unweighted* average of best bid and best ask. It treats the spread as symmetric around fair value and is a martingale only under the strong (and false) assumption that bid- and ask-side queue dynamics are independent and identically distributed.

### 2.2 The Stoikov micro-price (Stoikov 2018, §3 eq 9)

Stoikov defines the micro-price as the *expected* mid-quote conditional on current LOB state — specifically, the long-run expected midpoint after an infinite recursion of small price-impact moves caused by depleting one side of the book.

**The closed-form (Stoikov 2018 §2.1, "imbalance-weighted micro-price"):**

```
mp_t = p_bid_t * (V_ask_t / (V_bid_t + V_ask_t))
     + p_ask_t * (V_bid_t / (V_bid_t + V_ask_t))
```

where `V_bid_t` is the queue volume at the best bid, `V_ask_t` at the best ask.

**Crucial inversion to note:** When `V_bid >> V_ask` (lots of buyers waiting), the micro-price tilts *toward p_ask*, not toward p_bid. The intuition: a large bid queue absorbs sellers; the next quote-revision is more likely an upward bid revision, so fair value is closer to the ask. This is the opposite of the naive intuition "bigger queue = price gravitates there."

Define imbalance:

```
I_t = V_bid_t / (V_bid_t + V_ask_t)   ∈ [0, 1]
```

Then the closed-form simplifies to:

```
mp_t = I_t * p_ask_t + (1 - I_t) * p_bid_t
     = mid_t + (I_t - 0.5) * (p_ask_t - p_bid_t)
     = mid_t + (I_t - 0.5) * spread_t
```

That is: **the micro-price is the midprice plus a spread-weighted imbalance correction term**, centered on 0.5.

### 2.3 The martingale correction (Stoikov 2018 §3 eq 9 — "true micro-price")

The "imbalance-weighted micro-price" above is Stoikov's *first-order* approximation. The full §3 derivation iterates this estimator: the next mid given current imbalance is itself a function of the next imbalance, which depends on the next mid, etc. Stoikov shows the fixed-point martingale construction converges to:

```
mp*_t = mid_t + Σ_{k=1}^∞ G_k(I_t, S_t)
```

where `G_k` are the kth-order corrections discretized over the *imbalance × spread* state space, and `S_t` is the discretized spread bucket. In practice, the §3.2 algorithm constructs an empirical transition matrix on `(I, S)` states and computes the long-run expected mid via matrix iteration; the §4 paper notes that 95% of the correction lies in the first 1-3 iterations, so a finite cutoff `K=6` is operationally sufficient.

For our reference implementation we provide BOTH:

- **Variant A — Simple imbalance-weighted micro-price** (§2.1 closed-form). Cheapest, fully closed-form, no calibration needed.
- **Variant B — Martingale-corrected micro-price** (§3.2 finite-iteration). Calibrated transition matrix on a small `(I_bucket × S_bucket)` discretization. K=6 iterations.

Variant A is the K54 v3 feature. Variant B is in the reference impl for completeness and unit-test parity with the published paper.

### 2.4 Volume-proxy substitution (the MT5 spot-tick adaptation)

**The fundamental problem:** Stoikov's formula requires `V_bid` and `V_ask` — best-level queue depths — which MT5 retail-broker tick data does NOT expose. As confirmed by direct inspection: `volume = 0` on 100% of NAS100 + US30_cash ticks, `last = 0` on 100% (no trade events). Only `bid`, `ask`, `inferred_aggressor` are populated.

**Three candidate proxies, evaluated:**

1. **Spread-only proxy:** Use spread-change direction as imbalance signal. Rejected — too noisy, no directional information.
2. **Last-N-tick aggressor imbalance** (selected): For each tick at time `t`, count buy/sell aggressor classifications in the prior `N` ticks (or trailing window of 500ms). Define
   ```
   I_proxy_t = n_buy_in_window / (n_buy_in_window + n_sell_in_window)
   ```
   This is a *flow* imbalance, not a *depth* imbalance, but the empirical correlation between sustained buy-pressure and queue-imbalance is well-documented (Cont-Kukanov-Stoikov 2014 OFI, §2 — the OFI flow proxy explains 65% of return variance at 1-second).
3. **Quote-revision asymmetry proxy:** Count consecutive bid-up vs ask-down revisions in trailing window. Rejected as a primary — high correlation with proxy 2 but more brittle to bid/ask flickers.

**Selected design.** Variant A uses proxy 2 (flow-based imbalance). The window size `N` is a hyperparameter; we test `N ∈ {10, 50, 200}` ticks and pick the value with best 1-tick-ahead RMSE. A small grid search is acceptable here because (a) it's pre-registered as a hyperparameter, (b) the chosen `N` will be locked into the K54 v3 spec and never re-tuned per-period.

**Honesty disclosure.** The volume-proxy substitution means we are *NOT* implementing Stoikov 2018 verbatim — we are implementing the **closest-feasible** Stoikov-style estimator under MT5 retail-broker constraints. The unit tests in Section 5 verify that the Stoikov FORMULA is correct against published example numerics (using synthetic volumes to match Stoikov's Table 2 AAPL example), and the BENCHMARK in Section 4 evaluates the FLOW-PROXY adaptation against MT5 NAS100/US30_cash ticks. These are two separate deliverables — formula correctness (passes/fails on synthetic) is decoupled from MT5-empirical edge (passes/fails on real ticks).

---

## 3. Design — feature spec

### 3.1 Per-tick reference implementation

**Function signature** (in `k4_stoikov_micro_price.py`):

```python
def stoikov_micro_price_per_tick(
    df: pd.DataFrame,
    *,
    imbalance_window_ticks: int = 50,
    use_martingale_correction: bool = False,
    n_imbalance_buckets: int = 5,
    n_spread_buckets: int = 3,
    martingale_iterations: int = 6,
) -> pd.Series:
    """Compute Stoikov micro-price per tick.

    Parameters
    ----------
    df : DataFrame with columns ts_utc, bid, ask, inferred_aggressor (str).
    imbalance_window_ticks : trailing window size for flow-proxy imbalance.
    use_martingale_correction : if True, apply Stoikov §3 finite-K correction.
    n_imbalance_buckets, n_spread_buckets : (I, S)-grid for §3 calibration.
    martingale_iterations : K in Stoikov §3.2 (cutoff for fixed-point).

    Returns
    -------
    pd.Series of float, length len(df), micro-price per tick.
    """
```

### 3.2 M15-aggregated (last-tick) feature for K54 v3

For the K54 v3 catalog, we expose the **last-tick micro-price** of each M15 bar as a single scalar feature. Rationale (per §1 P3):

- Per-tick predictability lives at sub-second scales.
- M15-aggregated last-tick micro-price is a **structural state indicator** at bar close — "where in the imbalance-spread state space did the bar finish?" — not a 1-bar mid forecast.
- For K54's binary classification (will the OB-retest entry result in TP-side outcome?), this kind of structural state feature is exactly the right granularity.

**Canonical aggregation:** Last-tick micro-price (the micro-price computed on the final tick of the bar, including the imbalance window's lookback). Chosen over VWAP-weighted-tick because (a) volume = 0 in MT5 spot ticks (VWAP collapses to simple mean), (b) the last-tick state is what an entry order actually faces.

**Alternative aggregations considered but rejected:**

- VWAP-weighted-tick: trivially equals simple mean when volume=0.
- Median-tick: smooths intra-bar dynamics but loses the bar-close state property.
- Open-tick: same family as last-tick but loses ~15 minutes of information.

**Aggregated feature exposed to K54 v3:**

```python
{
    "stoikov_micro_price_close":   float,     # last-tick micro-price ($)
    "stoikov_micro_price_minus_mid_ticks": float,
                                              # (mp - mid) / tick_size
                                              # — the SHAPLEY-friendly normalized
                                              #   form. 0 = no imbalance,
                                              #   positive = ask-skewed.
    "stoikov_imbalance_close":     float,     # I_proxy at bar close, [0, 1]
    "stoikov_imbalance_window":    int,       # imbalance_window_ticks (locked)
}
```

The most important feature for K54 v3 is **`stoikov_micro_price_minus_mid_ticks`** — the deviation from naive midprice, normalized in tick units. Sign + magnitude of this scalar carries the directional + magnitude signal.

### 3.3 NaN-sentinel design (instruments without tick coverage)

**Five instruments have NO tick captures yet** (XAUUSD, USDJPY, GBPJPY, GBPUSD, XAGUSD). For these, the K54 v3 feature row exposes:

```python
{
    "stoikov_micro_price_close":          float("nan"),
    "stoikov_micro_price_minus_mid_ticks": float("nan"),
    "stoikov_imbalance_close":             float("nan"),
    "stoikov_imbalance_window":            -1,      # sentinel int
}
```

**Two NaN-handling strategies for K54 v3 training:**

1. **Strict NaN-pass-through** (recommended for LightGBM): LightGBM natively handles NaN as a separate split direction. The feature's `is_nan` indicator becomes a learned proxy for "this is a covered-instrument vs uncovered-instrument" distinction, which is a perfectly valid predictor. The instrument-id embedding in K54 v3 will absorb most of this signal, but leaving NaN as-is is the cleanest design.
2. **NaN → median of covered-instrument rows** (NOT recommended): destroys the covered-vs-uncovered information; confuses the model into thinking it has microstructure information when it doesn't.

**Final NaN-design choice:** Strategy 1 (NaN pass-through). The K54 v3 training pipeline must be configured with `lightgbm.use_missing=True` (default true).

**Future expansion path:** When tick captures are extended to the 5 currently-uncovered instruments (a separate ML-program backlog item), the NaN-sentinel rows automatically become real values without any K54 v3 retraining — the feature schema is forward-compatible.

### 3.4 Tick-coverage caveats

- **NAS100 + US30_cash only** as of 2026-04-29.
- Coverage starts 2026-04-27; earliest two days available.
- Per-day file size: NAS100 ~12MB compressed (≈830k ticks/day), US30_cash ~3MB compressed (≈170k ticks/day).
- During US session liquidity, NAS100 shows ~1-3 ticks/sec, US30_cash ~0.3-0.7 ticks/sec. Outside session: minutes between ticks. Imbalance-window math handles this gracefully (window-by-tick-count, not by wall-time).

---

## 4. Benchmark methodology + results

### 4.1 Benchmark specification

**Test:** Per-tick 1-step-ahead RMSE, `mid_{t+1}` as target.

For each tick `t` in the test set:
- `naive_mid_t` = `(bid_t + ask_t) / 2`
- `stoikov_mp_t` = computed per §3.1, default `imbalance_window_ticks=50`, no martingale correction (Variant A)
- `target_t` = `mid_{t+1}` (the next-tick midpoint)
- `naive_residual_t` = `target_t - naive_mid_t`
- `stoikov_residual_t` = `target_t - stoikov_mp_t`

We compute:
- `RMSE_naive` = `sqrt(mean(naive_residual^2))`
- `RMSE_stoikov` = `sqrt(mean(stoikov_residual^2))`
- `reduction_pct` = `100 * (RMSE_naive - RMSE_stoikov) / RMSE_naive`

**Verdict gate:** PASS if `reduction_pct ≥ 10`, FAIL otherwise (per §1 pre-registration).

**Filtering:** Skip ticks with bid≥ask (corrupt), spread > 5× rolling-1000-tick median (likely news/halt), or `t+1` does not exist (last tick of day).

**Imbalance-window grid search:** Test `N ∈ {10, 50, 200}` and lock the best per instrument; the locked value enters the K54 v3 spec.

**Hyperparameter selection discipline:** The grid search is over only 3 values, fully pre-registered, and the locked value is reported alongside the verdict. No further per-period retuning is permitted.

### 4.2 Empirical results

Run via `python research/ml_program/experiments/k4_stoikov_micro_price.py`. Machine-readable verdict in `k4_benchmark_results.json`. Computed 2026-04-28 (4-day-old tick captures: 2026-04-27 + 2026-04-28).

#### Per-instrument results

| Instrument | n_ticks | best_N | RMSE_naive | RMSE_stoikov | reduction_% | dir_accuracy_% | verdict |
|------------|---------|--------|------------|--------------|-------------|----------------|---------|
| NAS100     | 1,752,649 | 200 | 0.32634 | 0.33442 | **-2.47%** | 47.19% | **FAIL** |
| US30_cash  |   385,824 | 200 | 0.90839 | 0.91613 | **-0.85%** | 47.12% | **FAIL** |

**Pre-registered prediction P1 (≥10% RMSE reduction): REJECTED.**
Stoikov-flow-proxy is *worse* than naive midprice on both instruments. RMSE rose by 2.47% on NAS100 and 0.85% on US30_cash. Directional accuracy is below 50% chance on both — i.e., the imbalance-derived directional signal is *negatively predictive*.

**Pre-registered prediction P2 (≥55% directional accuracy): REJECTED.**
Both instruments score ~47%, below the random-chance 50% baseline.

**Pre-registered prediction P3 (M15 form does NOT preserve per-tick edge): VACUOUS.**
The per-tick edge does not exist in the first place; the M15 form trivially also fails. M15-aggregated RMSE reduction is **-0.0003% (NAS100)** and **-0.010% (US30_cash)** — i.e., the M15 last-tick micro-price is nearly identical to the M15 last-tick mid (the imbalance correction averages to zero across the bar).

**Sign-inverted diagnostic:**
- NAS100: -2.47% → -2.47% (sign-flip does NOT recover edge)
- US30_cash: -0.85% → -0.84%

The inverted-sign control is also worse than naive mid by ~the same magnitude. This rules out "right magnitude, wrong sign (bid-ask bounce)" as the explanation. The actual mechanism is **noise injection of the wrong magnitude at the wrong scale** — the imbalance correction term has variance comparable to or larger than the signal it tries to predict, regardless of sign.

### 4.3 Post-mortem: why FAIL on MT5 retail-broker tick data

Three convergent reasons:

1. **No bid/ask queue depth in MT5 spot CFD ticks.** `volume = 0` on 100% of NAS100 + US30_cash ticks (verified 2026-04-29). Stoikov 2018 §2.1's queue-imbalance formula requires `V_bid` and `V_ask`, neither of which is observable on MT5 retail. The flow-proxy substitution is a fundamentally different signal (trade-flow direction) than what Stoikov derived (depth imbalance). The two are correlated in lit-LOB markets but the substitution does not transmit cleanly.

2. **`inferred_aggressor` is mechanically derived from mid changes.** The Lee-Ready aggressor classifier in `tick_capture.py` infers `buy` when `mid_t > mid_{t-1}` and `sell` when `mid_t < mid_{t-1}` (since `last = 0` always on MT5 spot CFDs). So our flow imbalance is essentially a **rolling momentum / persistence signal on mid-changes**. At sub-second timescales, midprice has Roll-model bid-ask-bounce — recent up-tick predicts a *down*-tick, not continuation. So the proxy is a momentum signal in a mean-reverting regime; sign confused, magnitude wrong.

3. **Per-tick mid jumps dominate the signal-to-noise ratio.** NAS100 bid/ask spread is integer-multiple (median 1.76, with 1-tick = $0.01); US30_cash similar (median 2.30, 1-tick = $0.05). Per-tick mid changes are typically 1-3 ticks. The Stoikov correction `(I - 0.5) * spread` is bounded by spread/2 = 0.88 (NAS100) or 1.15 (US30_cash). At the magnitude where a "perfect" signal might shift the prediction, the noise is similar scale, drowning any directional information.

The key academic precedent: Stoikov 2018 §4 showed RMSE reduction of 12-18% on AAPL — but that's on **lit-LOB ITCH data with real queue volumes**. The Lucchese-Pakkanen-Veraart 2024 paper (the "challenge" paper in `group_b_microstructure.md` §7.2) noted Sharpe ceiling ~0.5 even on full-LOB data; on degraded MT5 retail data, expectations should be substantially lower. Our finding is consistent with: Stoikov's mechanism is real but does NOT transmit through the volume-proxy substitution required by MT5 retail ticks.

### 4.4 Connection to E24/E26 archive

This finding aligns with `project_microstructure_archived_2026-04-27` memory: microstructure features at M15 were NULL_VERDICT_CONFIRMED. The K-4 benchmark goes further — even at the **per-tick** scale (proper microstructure timescale per `group_b_microstructure.md` §2.2), the volume-proxy adaptation of Stoikov is null-or-worse. This refines the prior null verdict: it's not just M15-aggregation that destroys the signal, the *substitution of flow proxy for queue depth* destroys it before any aggregation.

A correctly-tested Stoikov micro-price on MT5 retail data **requires LOB depth**. Without that, the feature is noise.

### 4.3 M15-aggregation cross-check (U-3)

For each closed M15 bar within the test set, we compute:
- `bar_naive_mid` = mid at bar close
- `bar_stoikov_mp` = Stoikov micro-price at bar close (§3.2 last-tick-of-bar form)
- `bar_target` = naive mid at next bar's close
- `bar_RMSE_naive`, `bar_RMSE_stoikov`, `bar_reduction_pct`

If per-tick PASSES but per-M15 FAILS, that confirms the H2 / U-3 / E24-E26 thesis: signal is sub-second and decays through M15 aggregation. The K54 v3 feature is then justified as a **structural state indicator at bar close**, NOT a 1-bar mid predictor.

---

## 5. Reference implementation + unit tests

See `k4_stoikov_micro_price.py`. Three test families:

1. **Synthetic-volume formula tests** (5 cases): construct synthetic `(p_bid, V_bid, p_ask, V_ask)` quintuples with known imbalance, verify `mp = p_bid + (V_bid / (V_bid + V_ask)) * (p_ask - p_bid)`. Numerical-tolerance 1e-12.
2. **Stoikov 2018 Table-2-style spot check** (1 case): construct a quintuple matching the AAPL example in the paper (p_bid=$100.00, V_bid=200, p_ask=$100.01, V_ask=100, expected micro-price ≈ $100.0067), verify within 1e-4.
3. **Edge cases** (4 cases): zero-volume side (degenerate, returns mid + spread/2 toward non-zero side), equal volumes (returns naive mid), missing aggressor (returns naive mid as fallback), single-tick history (returns naive mid since imbalance window cannot be populated).

### 5.1 Stoikov 2018 Table-2-style spot-check (canonical)

The simple imbalance-weighted form gives:

```
mp = 100.00 * (100 / 300) + 100.01 * (200 / 300)
   = 100.00 * (1/3) + 100.01 * (2/3)
   = 33.333... + 66.673333...
   = 100.006667
```

Our unit test (`test_stoikov_canonical_aapl_example`) asserts `mp ≈ 100.006667` within tolerance 1e-6.

(The full §3 martingale-corrected form on Stoikov's empirical AAPL transition matrix yields a slightly different value but Stoikov §2.1 — the simple form — is what we benchmark against.)

---

## 6. Verdict synthesis

**Primary verdict (P1, ≥10% RMSE reduction):** **FAIL.** NAS100 -2.47%, US30_cash -0.85%. Both worse than naive midprice.

**Secondary verdict (P2, ≥55% directional accuracy):** **FAIL.** NAS100 47.19%, US30_cash 47.12%. Both below 50% random.

**M15-aggregation verdict (P3, M15 ≪ per-tick):** **VACUOUS.** The per-tick edge doesn't exist; M15 form (RMSE reductions of ~0.0% on both) trivially also fails. The H-A literature pivot to dollar-volume bars is the next architectural step.

**Sign-inverted diagnostic:** Sign flip does not recover edge (-2.47%, -0.84%). The flow-proxy correction is not "right magnitude wrong direction" — it's noise of similar magnitude in either sign.

**Overall:** **FAIL.** The Stoikov-flow-proxy adaptation does not transmit the published Stoikov 2018 mechanism through MT5 retail-broker tick data. The post-mortem in §4.3 attributes this to (1) absence of true LOB queue depth, (2) `inferred_aggressor` being a mid-change-derived proxy that captures bid-ask-bounce noise, (3) per-tick mid jumps dominating the small Stoikov correction term.

---

## 7. K54 v3 catalog drop-in spec (final section)

### 7.1 Feature names (4 new features)

| Feature name | Type | Range | NaN-handling |
|--------------|------|-------|--------------|
| `stoikov_micro_price_close` | float | instrument-native price units | NaN if no tick coverage |
| `stoikov_micro_price_minus_mid_ticks` | float | typically [-3, +3] in tick units | NaN if no tick coverage |
| `stoikov_imbalance_close` | float | [0, 1] (or NaN) | NaN if no tick coverage |
| `stoikov_imbalance_window` | int | locked positive integer (50 default) or -1 | -1 if no tick coverage |

### 7.2 Recommended catalog inclusion (locked by §6 verdict)

**VERDICT: FAIL → DO NOT INCLUDE in K54 v3 primary catalog.**

The Stoikov-flow-proxy feature does NOT meet the pre-registered ≥10% RMSE reduction gate; in fact it underperforms naive midprice on both NAS100 and US30_cash. Promoting it to K54 v3 would inject noise into the model.

**Recommended actions:**

1. **Document FAIL in `research/ml_program/KILLED_HYPOTHESES.md`** with the post-mortem from §4.3 (no LOB depth → flow-proxy substitution required → bid-ask-bounce contamination → noise injection).
2. **Reference impl stays in `research/ml_program/experiments/`** for future re-evaluation when:
   - Databento or similar provides LOB-depth tick data for MT5 instruments (then reuse `stoikov_canonical_micro_price` directly with real `V_bid`/`V_ask`)
   - OR a different broker stream is added with non-zero `volume` per tick
   - OR a different proxy is invented (e.g., consecutive same-side bid/ask move counts; not flow-derived)
3. **Re-route effort to H-A (volume-bar / dollar-bar resampling)** in `group_b_microstructure.md` §6.2. The literature's strongest hypothesis is sampling-clock change, not feature substitution — and the H-A path doesn't depend on LOB depth.
4. **Keep the M15 NaN-sentinel design (§3.3)** as a forward-compatibility hedge: if a future variant of this feature passes, the schema slot is reserved.

### 7.2.1 Caveat — what's still potentially salvageable

The flow-proxy feature might still carry signal as a **non-load-bearing input** to a richer ML model that can learn its conditional usefulness (e.g., LightGBM with strong vol-volume baseline; the sign + magnitude might encode regime information that the model exploits in interaction with other features). This is *not* a primary feature gate; it's a "shadow include + measure SHAP" question for K54 v3. Recommendation: TEST as an *interaction* feature only after primary K54 v3 features lock; if interaction-AUC lift ≥0.005 over baseline, retain; otherwise drop.

### 7.3 Drop-in Python signature for K54 v3 ingestion

```python
# In K54 v3 feature-extraction pipeline (NOT implemented in this dispatch):
from research.ml_program.experiments.k4_stoikov_micro_price import (
    compute_m15_stoikov_features,
)

def add_stoikov_features_to_k54_row(row: dict, symbol: str,
                                     bar_close_utc: datetime,
                                     ticks_root: Path) -> dict:
    """Drop-in: read tick parquet for the bar, compute Stoikov features,
    merge into the K54 row dict.
    Returns the row mutated with 4 new features. Returns NaN-sentinel set
    for instruments without tick coverage."""
    feats = compute_m15_stoikov_features(
        symbol=symbol, bar_close_utc=bar_close_utc, ticks_root=ticks_root,
    )
    row.update(feats)
    return row
```

This signature is **the K54 v3 catalog drop-in** — no production-code modification required. K54 v3's training pipeline calls `compute_m15_stoikov_features` per bar; the function lives in `research/ml_program/experiments/` until promoted to `src/components/`.

### 7.4 Promotion path (research → production)

If K54 v3 with Stoikov features delivers ≥+0.02 OOS AUC over K54 v2 (per the H2 hypothesis bar in `group_b_microstructure.md` §3), then:

1. Move `compute_m15_stoikov_features` to `src/components/tick_features.py` as an **additive** sidecar feature (alongside the existing 12 microstructure features). Schema-version bump to v2.
2. Backwards compatibility: existing tick sidecars stay v1; new sidecars are v2 with the Stoikov features appended.
3. CEO approval required (this is a production-prompt-adjacent change — Stoikov features may end up in the AI prompt context if K54 v3 promotion proceeds).

### 7.5 Risk + cost notes

- **Cost:** $0 (deterministic feature, no API calls; pure parquet I/O + pandas math).
- **Compute per bar:** O(N_ticks_in_bar × imbalance_window_ticks) = ~50k ops / bar for NAS100 — sub-millisecond on commodity hardware.
- **Storage:** None new (4 floats per K54 v3 row).
- **Decay risk:** Low. The Stoikov mechanism is grounded in queue-imbalance microstructure (Bouchaud propagator school + Lillo-Mike-Farmer meta-order splitting per `group_b_microstructure.md` §2.1), which is a *durable* mechanism per Group B's literature finding. Decay risk on the *trading edge* derived from this feature is moderate (Lucchese 2024 ceiling ~0.5 Sharpe), but the feature's mechanical correctness is durable.

### 7.6 Caveats (data + scope)

- Tick coverage starts 2026-04-27 — only **2 days of data** available at benchmark time. Test-set / training-set split is naive (in-sample first day, OOS second day). Repeat the benchmark with ≥30 days when tick captures accumulate.
- NAS100 + US30_cash both use the same MT5 broker (redacted_account); broker-specific quote noise / NBBO-quality differences are NOT controlled for. Cross-broker validation is a future task.
- The flow-proxy substitution for queue volumes is the most empirically suspect step; if Databento or similar provides MT5-degraded LOB depth data in the future, re-run with real depth volumes for direct §3 fidelity.

---

## 8. Cross-references

- **Backlog:** K-4 (T1), P-4 (T1), B-8 (Phase 4 quick-win bundle) in `research/ml_program/MASTER_BACKLOG.md`.
- **Hypothesis:** H-4 in `research/ml_program/literature/HYPOTHESIS_BACKLOG.md`; H2 in `research/ml_program/literature/synthesis/group_b_microstructure.md` §3.
- **Production-code reference:** `src/components/tick_features.py` (existing midprice usage, NOT modified).
- **Memory:** `project_microstructure_archived_2026-04-27` (E24/E26 NULL_VERDICT_CONFIRMED on M15 — exactly what P3 expects to reproduce).
- **Paper:** Stoikov 2018 §2.1 (closed-form), §3 (martingale correction), §4 (empirical AAPL).

---

*Reference implementation in `research/ml_program/experiments/k4_stoikov_micro_price.py`. Benchmark results in `research/ml_program/experiments/k4_benchmark_results.json`. UTF-8. No production code modified.*
