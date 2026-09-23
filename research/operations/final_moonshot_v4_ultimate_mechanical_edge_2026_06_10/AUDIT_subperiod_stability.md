# ADVERSARIAL AUDIT — Sub-period / Regime Stability of the Forward Window

**Auditor posture:** trust-calibration on real money, not idea-killing. Separate STRUCTURAL
pass-rate (no-time-limit challenge math — robust) from EDGE MAGNITUDE (return/speed — fragile).

**Engine:** LOCKED `INTEG_portfolio_build_w2.mc_series` (8% / 5% daily / 10% maxDD / BLOCK=5 / 20k
paths). Daily-R stream reconstructed EXACTLY as `INTEG_W7_final_book.build_final_matrix` + Kelly-lite
handset (no-lookahead, real cost, per-year). Reproduction is byte-equivalent on the load-bearing
constants:

| check | reproduced | locked W7 file | match |
|---|---|---|---|
| sd_book | 0.56859 | 0.56859 | ✓ |
| sd_final | 0.75768 | 0.75768 | ✓ |
| VS_final | 0.7504 | 0.7504 | ✓ |
| mean_all (1679d) | 0.10956 | 0.10956 | ✓ |
| mean_fwd (382d) | 0.33550 | 0.33550 | ✓ |

Script: `AUDIT_subperiod_stability.py` → `AUDIT_subperiod_stability_RESULT.json`.

---

## 1. HEADLINE FINDING (the inflation)

**The headline forward edge magnitude is inflated ~3x vs the all-history blended edge, and ~8x vs the
all-history per-year median.** The forward 2025-26 window is the single hottest regime in the entire
11-year (2015-26) dataset, and the deploy-book "monthly %" headline is anchored to that window.

| daily-R estimate | daily mean (unit-R) | implied monthly % @1.50% eff (0.01126) | $/100k/mo | ratio vs headline |
|---|---|---|---|---|
| **HEADLINE forward mean (2025-26)** | **0.33550** | **7.93%** (mc_forward reports 8.81% via block-bootstrap) | **$7,933** | **1.00x** |
| forward H1 (2025-01 → 2025-09) | 0.22078 | 5.22% | $5,221 | 0.66x |
| forward H2 (2025-09 → 2026-06) | 0.45022 | 10.65% | $10,646 | 1.34x |
| all-history BLENDED mean | 0.10956 | **2.59%** | $2,591 | **0.33x** |
| all-history per-year MEDIAN | 0.04187 | **0.99%** | $990 | **0.12x** |
| 2024 (last pre-forward year) | 0.09181 | 2.17% | $2,171 | 0.27x |
| coldest year (2023) | 0.00790 | 0.19% | $187 | 0.02x |

> The 8.81% forward monthly in `INTEG_W7_FINAL_RESULT.json → mc_forward.final.1.50%` and the 2.59%
> all-history vol-matched monthly are **both true** — they just measure different things. The 8.81%
> is "what the last ~16 months would have paid"; the 2.59% (and the far lower per-year median) is
> "what a randomly-drawn year of this book pays." **The book IS the 2.59% book; the 8.81% is the
> hot-regime number.**

**Quantified inflation of the edge-magnitude headline:**
- Headline forward mean is **+206%** (3.06x) above the all-history blended mean.
- Headline forward mean is **+701%** (8.01x) above the all-history per-year median.
- Even vs the most recent pre-forward year (2024), the headline is **+265%** (3.65x).

---

## 2. ALL-HISTORY PER-YEAR DISPERSION (is the edge a few hot years?)

Per-calendar-year daily-mean and Sharpe on the FINAL Kelly-sized book (eff @1.50%):

| year | n days | daily mean | daily Sharpe | implied mo% @eff | win-day% |
|---|---|---|---|---|---|
| 2015 | 8 | 0.194 | 0.504 | 4.58% | 50.0 |
| 2016 | 14 | **-0.046** | **-0.129** | -1.10% | 28.6 |
| 2017 | 13 | 0.116 | 0.209 | 2.75% | 53.8 |
| 2018 | 19 | 0.155 | 0.287 | 3.66% | 42.1 |
| 2019 | 120 | 0.031 | 0.079 | 0.74% | 50.0 |
| 2020 | 162 | 0.028 | 0.080 | 0.66% | 47.5 |
| 2021 | 236 | 0.052 | 0.140 | 1.24% | 54.7 |
| 2022 | 233 | 0.021 | 0.064 | 0.50% | 51.5 |
| 2023 | 242 | **0.008** | **0.026** | **0.19%** | 48.3 |
| 2024 | 250 | 0.092 | 0.124 | 2.17% | 47.6 |
| **2025** | 263 | **0.287** | **0.225** | **6.78%** | 56.3 |
| **2026** | 119 | **0.443** | **0.313** | **10.48%** | 57.1 |

Dispersion (years with n≥20, i.e. 2019-2026):
- per-year daily-Sharpe: mean **0.131**, std **0.089**, range **0.026 → 0.313** (CV = **0.675**).
- per-year daily-mean: range **0.008 → 0.443** — a **56x** spread coldest-to-hottest year.
- per-year daily-mean **median = 0.042** (≈ one-eighth of the forward headline).
- 0 of 8 years are net-negative-Sharpe in the n≥20 set (2016 is negative but n=14, pre-depth),
  so the **direction of the edge is stable; only the magnitude is wildly regime-dependent.**

**Read:** the book made almost nothing in 2019-2023 (0.19%–1.24% mo equivalent) and then 5x-10x'd in
2025-26. The edge magnitude does **rest on the two most recent years.** This is partly real (crypto/
metals depth + the 2024-26 trend regime + tick-true execution were not in the early thin years) and
partly the well-known forward-window selection: every sleeve was tuned/validated with these years
visible as the holdout, and crypto (38.8% of book EV) had its biggest trending regime ever in 2024-26.

---

## 3. WITHIN-FORWARD STABILITY (does the recent edge itself hold flat?)

The forward window is NOT flat — it is **accelerating** (the opposite of a settled steady state):

| sub-period | dates | n | daily mean | Sharpe | worst day (unit-R) | win% | mo% @eff |
|---|---|---|---|---|---|---|---|
| H1 | 2025-01 → 2025-09 | 191 | 0.2208 | 0.182 | -3.23 | 54.5 | 5.22% |
| H2 | 2025-09 → 2026-06 | 191 | 0.4502 | 0.319 | -2.34 | 58.6 | 10.64% |
| Q1 | 2025-01 → 2025-05 | 96 | 0.2466 | 0.215 | -1.44 | 50.0 | 5.83% |
| Q2 | 2025-05 → 2025-09 | 95 | 0.1947 | 0.153 | -3.23 | 58.9 | 4.60% |
| Q3 | 2025-09 → 2026-02 | 95 | 0.5268 | 0.321 | -2.34 | 58.9 | 12.45% |
| Q4 | 2026-02 → 2026-06 | 96 | 0.3744 | 0.328 | -1.72 | 58.3 | 8.85% |

- H2 daily-mean (0.450) is **2.04x** H1 (0.221). The hot half is the **recent** half.
- Quarter daily-mean ranges 0.195 → 0.527 (**2.7x** spread inside a 17-month window).
- The single worst forward day is **-3.23 unit-R = -3.63% @1.50% eff** (in 2025 Q2) — still inside the
  5% daily wall, confirming the STRUCTURAL daily-breach claim, but it shows the tail is real.

**Hot-month concentration (forward window, 18 months):**
- Top 1 month = **13.5%** of forward total R; top 2 = **26.4%**; top 3 = **39.2%**.
- 16 of 18 months positive, 2 negative (2025-01: -2.6%, 2026-04: -2.7%). So it is **not** one or two
  lucky months carrying everything — breadth across months is genuinely good. The concentration is at
  the **YEAR/regime** level (2025-26 vs 2019-23), not the month level.

---

## 4. HONEST STEADY-STATE DAILY-R ESTIMATE

Two different "steady-state" questions, two different answers — both reported honestly:

**(a) Robust estimator WITHIN the forward window** (median/trimmed across forward sub-periods):
- median-of-months = 0.338, median-of-quarters = 0.311, 20%-trimmed-month-mean = 0.347.
- These land **on top of the 0.336 headline** → *within the recent regime, the edge is not driven by a
  couple of outlier months; trimming barely moves it (-7% at most).*
- **BUT this does NOT correct regime risk** — every forward sub-period is drawn from the same hot
  window, so an intra-forward median cannot detect that the whole window is hot.

**(b) Regime-robust steady-state** (across the full 11-year sample — the honest go-live prior):
- all-history blended mean = **0.110 unit-R/day → ~2.59% mo @1.50% eff (~$2,590/100k/mo)**.
- all-history per-year median = **0.042 unit-R/day → ~0.99% mo (~$990/100k/mo)** — the most
  pessimistic, treats each year as one draw.
- A defensible **steady-state band for go-live: ~0.10 to ~0.13 unit-R/day → ~2.4%–3.0% monthly per
  account @1.50%**, with a realistic downside of ~1% monthly in a cold year (2019-2023 type) and the
  observed forward upside of ~8% monthly only if the 2024-26 regime persists.

**Recommended planning number: assume the all-history ~2.6% monthly @1.50% (not the 8% forward
number), treat the 8% as best-case regime upside, and budget for ~1% monthly cold-year stretches.**

---

## 5. STRUCTURAL vs EDGE-MAGNITUDE — the critical split

This is the part the auditor wants to be *fair* about: the two reliability classes are very different.

### STRUCTURAL (challenge-pass / no-time-limit) — ROBUST across sub-periods
Running the LOCKED `mc_series` on each forward HALF independently, vol-matched to its own std:

| dial (nominal) | H1 vol-matched P(pass) | H2 vol-matched P(pass) | full-fwd P(pass) | all-history P(pass) |
|---|---|---|---|---|
| 0.75% | 99.99% | 100.0% | 99.87% | 99.99% |
| 1.25% | 99.82% | 100.0% | 97.92%* | 99.36% |
| 1.50% | 99.38% | 100.0% | 96.25%* | 98.59% |
| 2.00% | 97.88% | 99.90% | 90.42%* | 95.73% |

(*forward "full" at NOMINAL, not vol-matched — that's the regime-juiced framing; the all-history
column is the honest vol-matched one.)

**P(pass) is high in BOTH halves and across all-history.** The structural claim — "this book passes
the FTMO no-time-limit challenge with very high probability at ≤1.5%" — does **not** depend on the hot
regime. Even the coldest sub-period (H1 2025) still passes 99.4% vol-matched at 1.50%. The 0%
daily-breach claim is also structural (worst forward day -3.63% @1.50%, inside the 5% wall).
**Trust the pass-rate.**

### EDGE MAGNITUDE (monthly % / speed-to-pass) — FRAGILE, REGIME-DEPENDENT
- Headline 8.8% forward monthly is **3x** the all-history 2.59% and **8x** the per-year median.
- Median-days-to-pass at 1.50%: H2 vol-matched = 30 days, H1 = 47, all-history = 66, but a 2023-type
  cold year would be vastly slower (daily-mean 0.008 → effectively near-flat growth that cycle).
- **Do NOT trust the speed/return headline at face value.** The 66-day all-history median is the
  honest "typical" speed; the ~15-30 day forward speed is the hot-regime best case.

---

## 6. VERDICT

| dimension | reliability | honest number | headline number | inflation |
|---|---|---|---|---|
| Challenge PASS-rate @1.50% | HIGH (regime-robust) | 98.6% (all-hist vm); 99.4%+ each fwd half | 96–99% | none material |
| 0% daily-breach | HIGH (structural) | confirmed (worst day -3.63%) | 0% | none |
| Monthly % / $ throughput @1.50% | LOW (regime-dependent) | ~2.6% all-hist / ~1% cold-year | 8.8% forward | **~3x (best case); ~8x vs per-year median** |
| Speed-to-pass | LOW-MED | ~66d all-hist median | ~15-30d forward | ~2-4x |

**Bottom line:** the deploy book's *survivability* projection is honest and robust — it really does
pass the challenge with high probability and cannot single-day-breach at the deploy sizes, in every
sub-period including the coldest forward half. But the *return/speed* projection is anchored to the
hottest 16-month regime in the 11-year history and is inflated roughly **3x vs the blended-history
expectation and ~8x vs the per-year-median expectation.** Crypto (38.8% of book EV) carried its
strongest trending regime ever in 2024-26, and the whole forward window post-dates sleeve tuning.

For real-money planning: **size to the pass-rate (it's real), but budget returns to ~2.6% monthly
per account @1.50% as the central case, ~1% in a cold year, and treat 8%/mo as upside that only
materializes if the 2024-26 regime persists.** The book's own caveat #1 ("forward window is short,
distrust single-fwd-year positives") is correct and, per this audit, materially under-stated in the
headline monthly/$ figures.
