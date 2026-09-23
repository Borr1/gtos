# ADVERSARIAL AUDIT — Multiple-Testing / Overfitting Inflation on the 2025-26 Holdout

Auditor pass: how much did 7 waves of selection against the same 2025-26 forward window inflate the
GTOS final deploy-book projections? Quantified, no-lookahead, real-cost, LOCKED engine
(`INTEG_portfolio_build_w2.mc_series`, N=20000, 8% target / 5% daily / 10% maxDD / block-5).

**Bottom line:** The **structural pass-rate is largely real**; the **edge magnitude (return/speed) is
heavily inflated** — and the inflation is concentrated in the *forward-only* numbers, which the
go-live dossier quotes most prominently (5–14%/month, ~22 days-to-pass). The forward window is not a
holdout: ~100 separate evaluations scored against it, and it happens to be the **two best-return
years in the entire 12-year history**. The all-history vol-matched headline survives a multiple-
testing haircut far better than the forward headline.

---

## 1. How contaminated is the "holdout"?

- **101 of 126 `*RESULT.json`** evaluations in the route reference the 2025/2026 forward window. The
  forward window was the **scoring/selection surface**, repeatedly, across ~105 distinct
  strategy/sleeve/variant families and 7 waves. This is repeated selection against the same data,
  i.e. a semi-contaminated holdout — by construction, not a clean out-of-sample test.
- **The forward window is the most benign regime ever observed.** Per-year daily mean of the deploy
  book (clean_3 base, conf-weighted unit-R):

  | year | n | daily mean | rank |
  |---|---|---|---|
  | **2026** | 119 | **0.358** | **#1 of 12** (FORWARD) |
  | **2025** | 263 | **0.244** | **#2 of 12** (FORWARD) |
  | 2024 | 250 | 0.066 | #3 |
  | 2021 | 236 | 0.049 | #4 |
  | 2019–2023 | ~990 | 0.004–0.030 | typical |

  The two forward years are the **#1 and #2 best years**, ~4–5x the 2019–2024 baseline. Selecting
  the window AND selecting strategies that score well on it stacks regime luck on top of selection
  luck.
- **Forward daily mean = 3.06x all-history** (0.280 vs 0.091). Forward daily Sharpe 0.277 vs
  all-history 0.152 (1.82x). The forward outperformance is the multiple-testing + benign-regime
  fingerprint.

## 2. Effective number of trials and the deflated-Sharpe haircut

Trial-count range (from the RESULT inventory): N=11 (deployed sleeves) → 40 (sleeve × major variant
clusters) → 80 (distinct scored configs) → 130 (all evaluations) → 300 (incl. param sweeps).

Deflated Sharpe Ratio (Bailey & López de Prado 2014), trial-SR dispersion from per-sleeve daily
forward Sharpes (sd≈0.065), using forward skew 2.13 / kurt 8.40:

| trials N | SR0 (expected max daily SR) | DSR (forward) | DSR (all-history) |
|---|---|---|---|
| 11 | 0.106 / 0.071 | 1.000 | 1.000 |
| 80 | 0.160 / 0.107 | 0.999 | 0.993 |
| 130 | 0.171 / 0.114 | 0.997 | 0.980 |
| 300 | 0.189 / 0.126 | 0.990 | 0.919 |

**Interpretation (important nuance):** DSR answers *"is Sharpe > 0 after correcting for N trials?"*
With n=1679 (all) / 382 (fwd) daily observations, the answer is **yes even at N=300** (DSR > 0.92).
So the book is **not a pure overfit artifact — a positive-Sharpe portfolio genuinely survives
multiple-testing deflation.** This is the STRUCTURAL good news. DSR is the wrong tool for the
magnitude question, which is where the real inflation lives (Section 3).

## 3. CSCV / PBO on the sleeve/config set

CSCV (Bailey-Borwein-LdP-Zhu 2017), 12 blocks, IS criterion = daily Sharpe, config universe = full
book + 11 leave-one-out + 11 single-sleeve + 40 random reweightings (63 configs), 924 IS/OOS splits:

- **PBO = 13.5%** — probability the in-sample-best config is below the OOS median. Moderate, well
  under the 50% overfit threshold. The book's *internal* sleeve/weight selection is fairly robust.
- IS-best config OOS Sharpe haircut = **10.7%** (mean IS daily SR 0.165 → OOS 0.147). This is the
  honest "selection of which sleeves/weights" haircut — small.

PBO captures *config selection* overfitting (low here). It does **not** capture the *window + regime*
contamination, which is the dominant effect (Section 4).

## 4. The magnitude haircut — re-run through the LOCKED engine

The forward EV is the selection window. The unbiased estimate of the next-period mean shrinks toward
all-history. Inverse-variance blend of forward (SE 0.052) and all-history (SE 0.015) ⇒ honest daily
mean **0.105 = 1.15x all-history**, i.e. the forward 3.06x is **almost entirely selection/regime
luck** (only ~15% of the lift is statistically defensible).

LOCKED-engine MC on the clean_3 base series, EV deflated, deploy dials 1.25%/1.50% nominal:

### 4a. FORWARD headline (the contaminated numbers the dossier quotes)
| forward-EV scenario | risk | P(pass) | P(failDD) | med days | monthly% |
|---|---|---|---|---|---|
| forward as-is (HEADLINE) | 1.25% | 99.80% | 0.20% | 22 | **7.34%** |
| forward as-is (HEADLINE) | 1.50% | 99.32% | 0.68% | 19 | **8.81%** |
| inverse-var blend (honest) | 1.25% | 77.88% | 22.12% | 31 | 2.76% |
| inverse-var blend (honest) | 1.50% | 73.84% | 26.16% | 23 | 3.32% |
| all-history mean (luck removed) | 1.25% | **73.69%** | 26.31% | 30 | **2.40%** |
| all-history mean (luck removed) | 1.50% | 70.08% | 29.93% | 23 | 2.88% |

### 4b. ALL-HISTORY vol-matched basis (the more reliable headline)
| all-hist EV scenario | risk | P(pass) | P(failDD) | med days | monthly% |
|---|---|---|---|---|---|
| all-history as-is | 1.25% | 99.31% | 0.69% | 68 | 2.40% |
| −10.7% (PBO OOS haircut) | 1.25% | 98.27% | 1.73% | 73 | 2.14% |
| −25% (moderate MT haircut) | 1.25% | 95.17% | 4.83% | 80 | 1.80% |
| −40% (aggressive MT haircut) | 1.25% | 88.82% | 11.18% | 84 | 1.44% |
| −25% (moderate MT haircut) | 1.50% | 92.00% | 8.00% | 64 | 2.16% |

## 5. Verdict — split structural vs magnitude

**STRUCTURAL pass-rate (RELIABLE):**
- Daily-breach = 0% is **mean-shift invariant**: deflating EV cannot manufacture a −5% day. Worst
  single day stays ~−2.5%/−3.0%/−4.0% at 1.25/1.50/2.00% nominal in BOTH windows. The "structurally
  cannot single-day −5%" claim is genuine.
- The all-history vol-matched P(pass) holds ≥95% even after a 25% multiple-testing EV haircut at
  1.25%. The book being a real positive-Sharpe, low-corr (avg off-diag +0.003, 10.85 of 11 effective
  independent sleeves) portfolio survives DSR deflation to N=300.

**EDGE MAGNITUDE (HEAVILY INFLATED):**
- **Forward monthly% inflated ~3.0x.** The 7.3%/month @1.25% and 8.8%/month @1.50% forward headlines
  deflate to ~2.4–2.9%/month on the all-history-consistent mean. **The all-history vol-matched
  numbers (2.16%/month @1.25%) were already telling the honest story; the forward table is the
  inflated one.**
- **Forward P(pass) inflated.** 99.8% forward @1.25% → ~74–78% once EV is shrunk to honest. (The
  all-history vol-matched 99.4% is far more defensible — it deflates only to ~95% at a 25% haircut.)
- **Days-to-pass is the LEAST inflated dimension.** Forward 22d → ~30d honest; all-history basis is
  ~68–80d. The "~1.5–1.8x faster than 0.75%" *relative* speed claim survives; the *absolute* ~22-day
  forward figure does not — expect ~2.5–4 months to first pass on a normal regime.

## 6. Recommended honest deploy numbers (after correction)

Use the **all-history vol-matched basis with a 10–25% multiple-testing EV haircut**, NOT the forward
table:

| dial | P(pass) | P(maxDD) | monthly% | med days | note |
|---|---|---|---|---|---|
| 1.25% honest | **95–98%** | 1.7–4.8% | **~1.8–2.1%** | **73–80** | first cycle |
| 1.50% honest | **92–96%** | 3.5–8.0% | **~2.2–2.6%** | 60–64 | step-up |

**Discard / heavily discount:** the `mc_forward` table (5.3–14.1%/month, 11–37 day med, 90–100%
P(pass)). It is the single most inflated artifact — built on the two best regime-years ever, used
~100x as a selection surface. The owner should treat forward numbers as a best-case ceiling, not a
projection.

## 7. Caveats on this audit
- Trial count N is an estimate; the true effective N is between the cluster count (~40) and the full
  evaluation count (~130). DSR is insensitive to N in this range because n (sample size) is large.
- The magnitude haircut uses inverse-variance shrinkage and a regime argument; if 2025-26 represents
  a genuine structural regime shift (e.g. persistent crypto/metals trend), the true forward mean is
  higher than all-history — but betting deploy size on that is exactly the bet the audit warns
  against.
- The structural (daily-breach, low-corr, positive-Sharpe-survives-DSR) findings are robust; the
  magnitude correction is a central estimate with a wide band (the table spans the band).
