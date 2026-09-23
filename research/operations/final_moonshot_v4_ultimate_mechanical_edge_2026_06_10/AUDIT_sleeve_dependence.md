# ADVERSARIAL AUDIT — Crypto & single-sleeve dependence (concentration risk)

**Auditor posture:** trust-calibration on real money, not idea-killing. Quantify, don't hand-wave.
**Engine:** LOCKED `INTEG_portfolio_build_w2.mc_series` (N=20000, 8% target / 5% daily / 10% maxDD /
block-5), reproduced **byte-exact** against `INTEG_W7_FINAL_RESULT.json` before any scenario was run
(baseline 1.25%: p_pass=0.99355, mo=2.158%, 79 days; 1.50%: 0.98590, 2.590%, 66 days; stress15 1.25%
=0.79125, 1.50%=0.73490 — all matched to 5 dp).
**Harness:** `AUDIT_sleeve_dependence_run.py` → `AUDIT_sleeve_dependence_RESULT.json`.
**Method (faithful to the locked build):** start from `INTEG_W7_final_book.build_final_matrix()`
(tick-restated, HEATOIL+NATGAS dropped), zero/halve the target sleeve **column**, **recompute the
leak-free conviction `n_active`** on the reduced matrix, re-apply the **same Kelly-lite handset**, then
report two conventions:
- **REVOLMATCH** — re-vol-match the surviving book to the fixed risk anchor `sd_book` (=0.56859, the
  8-sleeve W3 book std the engine always matches to). This is the deployment-realistic question:
  *"same risk budget, fewer edges — re-size to fill it."*
- **KEEP_VS** — keep the baseline VS (0.7504), no re-sizing. Isolates pure EV/vol loss.
- Plus **FORWARD** (2025-26, nominal sizing) — the regime where crypto data actually lives.

---

## HEADLINE FINDING (the honest split)

**Structural pass-rate (no-time-limit challenge math) barely depends on crypto. Edge MAGNITUDE
(speed + monthly%) depends on it heavily, and forward monthly% depends on it MOST.**

The two have very different reliability and must not be quoted as one number.

### The single most load-bearing fact about crypto

Crypto contributes **38.8% of all-history book EV** but **only has data from late-2024 onward**:
0 active days 2015-2023, 11 days in 2024, 41 in 2025, 15 in 2026 (67 of 1679 matrix days = 4%).
**77.6% of crypto's all-history EV sits in 2025-26.** It also has the **highest EV/active-day of any
sleeve (0.814 unit-R/day, ~1.5× metals_core's 0.549)**. So the all-history headline is, mechanically,
a 1679-day block-bootstrap whose top contributor is a 67-day, last-28-months, exceptionally-trendy
cluster. In the FORWARD book crypto is **45.8% of EV** — even more concentrated in the live window.

This is the inflation vector: the all-history pass/speed numbers borrow crypto's 2025-26 trend
performance and spread it across 11 years of resampled days that never actually contained crypto.

---

## RESULTS — all-history, REVOLMATCH (deployment-realistic, same risk budget)

| Scenario | size | P(pass) | Δpass | days | Δdays | monthly% | Δmo% | stress15 | Δs15 | stress20 |
|---|---|---|---|---|---|---|---|---|---|---|
| **BASELINE** | 1.25% | 0.9936 | — | 79 | — | 2.16% | — | 0.7913 | — | 0.4398 |
| **BASELINE** | 1.50% | 0.9859 | — | 66 | — | 2.59% | — | 0.7349 | — | 0.4299 |
| remove crypto | 1.25% | 0.9774 | −1.62pp | 78 | −1% | 1.92% | **−10.9%** | 0.6341 | **−15.7pp** | 0.2847 |
| remove crypto | 1.50% | 0.9335 | **−5.24pp** | 62 | −6% | 2.31% | **−11.0%** | 0.6072 | **−12.8pp** | 0.2802 |
| crypto EV halved | 1.25% | 0.9909 | −0.27pp | 71 | −10% | 2.26% | +4.8%* | 0.7509 | −4.0pp | 0.3965 |
| crypto EV halved | 1.50% | 0.9792 | −0.67pp | 58 | −12% | 2.71% | +4.8%* | 0.7181 | −1.7pp | 0.3776 |
| remove metals_core | 1.25% | 0.9825 | −1.11pp | 92 | +17% | 1.79% | −16.8% | 0.6679 | −12.3pp | 0.3261 |
| remove metals_core | 1.50% | 0.9662 | −1.97pp | 76 | +15% | 2.15% | −16.8% | 0.6244 | −11.1pp | 0.3286 |
| remove energy_agri | 1.25% | 0.9887 | −0.49pp | 86 | +9% | 1.97% | −8.8% | 0.7341 | −5.7pp | 0.4015 |
| remove energy_agri | 1.50% | 0.9767 | −0.92pp | 71 | +8% | 2.36% | −8.8% | 0.6806 | −5.4pp | 0.3993 |

\* crypto-halved REVOLMATCH monthly *rises* because halving crypto's variance lets VS lever up to
0.976; the speed cost shows correctly as **days −10..−12%** and the **stress tail still erodes**. Under
KEEP_VS (no re-size) crypto-halved monthly is −19% (1.74% vs 2.16%) — the cleaner magnitude read.

### REMOVE ALL TOP-3 (crypto+metals_core+energy_agri = 75% of EV; only the 8 tail sleeves remain)
EV collapses to **23.9% of baseline**; REVOLMATCH must lever **VS to 1.78** to hit the risk budget, and
even so: 1.25% pass **0.852** (−14pp), 1.50% pass **0.807** (−18pp), **stress15 ≈ 0.31** (was 0.73-0.79).
The maxDD wall binds hard once the surviving edge can't outrun bootstrap drawdowns at that leverage.
The tail sleeves alone are not a deployable book.

## RESULTS — FORWARD (2025-26, nominal) — the cleanest concentration read

| Scenario | size | P(pass) | days | monthly% | fwd daily-mean (R) |
|---|---|---|---|---|---|
| **BASELINE** | 1.25% | 0.9792 | 18 | **8.81%** | 0.3355 |
| **BASELINE** | 1.50% | 0.9625 | 15 | **10.57%** | 0.3355 |
| remove crypto | 1.25% | 0.9899 | **32** | **4.95%** | 0.18847 (56% of base) |
| remove crypto | 1.50% | 0.9804 | **26** | **5.94%** | 0.18847 |
| crypto EV halved | 1.25% | 0.9940 | 23 | 6.95% | 0.26464 (79%) |
| crypto EV halved | 1.50% | 0.9863 | 19 | 8.34% | 0.26464 |
| remove metals_core | 1.25% | 0.9760 | 22 | 7.20% | 0.27425 (82%) |
| remove energy_agri | 1.25% | 0.9732 | 21 | 7.77% | 0.29614 (88%) |

**Removing crypto from the forward book RAISES pass probability (0.979 → 0.990) while nearly DOUBLING
days-to-pass (18 → 32) and HALVING monthly% (8.81% → 4.95%).** This is the whole story in one line:
**crypto buys SPEED and headline return, not pass probability.** Removing the *highest-vol* sleeve
mechanically lowers drawdown risk, so pass-rate goes *up* — the engine just gets there slower.

---

## HOW MUCH THE HEADLINE DEPENDS ON CRYPTO 2025-26 TRENDINESS (quantified)

| Headline metric | Baseline | Crypto removed | Inflation attributable to crypto |
|---|---|---|---|
| **Structural P(pass) 1.25% (all-hist)** | 0.9936 | 0.9774 | **−1.6pp — essentially crypto-independent** |
| **Structural P(pass) 1.50% (all-hist)** | 0.9859 | 0.9335 | −5.2pp (modest; size-dependent) |
| **All-hist monthly% (speed proxy)** | 2.16-2.59% | 1.92-2.31% | **−11%** of the monthly headline |
| **Forward monthly%** | 8.81-10.57% | 4.95-5.94% | **−44% — the headline forward return is ~1.8× inflated by crypto** |
| **Forward days-to-pass** | 18 | 32 | **+78% slower** without crypto (speed claim is ~1.8× crypto-levered) |
| **Stress15 P(pass) 1.25%** | 0.7913 | 0.6341 | **−15.7pp — crypto's tail is propping the stress gate** |
| **Stress15 P(pass) 1.50%** | 0.7349 | 0.6072 | −12.8pp |
| Forward EV (daily-mean R) | 0.3355 | 0.1885 | crypto = **44% of forward EV** |
| All-history EV (daily-mean R) | 0.1096 | 0.0655 | crypto = **40% of all-history EV** |

### Verdict by metric class
- **STRUCTURAL pass-rate (challenge math): RELIABLE / barely crypto-dependent.** Even with crypto
  fully removed and the book re-sized to the same risk budget, the challenge still passes with
  P≈0.93-0.98. The "we pass the FTMO challenge" claim survives a total crypto regime-death. Trust it.
- **EDGE MAGNITUDE (speed + monthly%): MATERIALLY INFLATED by crypto, ~10-11% all-history.** Discount
  the all-history monthly/speed headline ~10% for crypto-fade risk.
- **FORWARD return/speed headline: HEAVILY crypto-dependent — discount ~40-45%.** The 8-10%/month and
  ~15-18-day forward figures are roughly **1.8× what the book delivers without crypto's 2025-26 run**.
  Because 100% of crypto's history is the last 28 months of a strong crypto trend, the forward
  number is the *least* out-of-sample-defensible figure in the book. **If crypto trendiness fades to
  half (the `crypto_EV_halved` regime-fade proxy), forward monthly drops 8.81%→6.95% and days 18→23**;
  if it dies entirely, 8.81%→4.95% and 18→32.
- **STRESS GATE is crypto-supported:** crypto removal cuts the 1.5×-left-tail stress pass by 13-16pp.
  Crypto's right-skewed high-EV days are partly what carries the adversarial stress scenario. This is
  the one place crypto helps *robustness*, not just speed — and it's the one place its loss hurts a
  risk metric, not just a return metric.

---

## SECONDARY CONCENTRATION (the other two top sleeves)
- **metals_core (24.6% EV):** removal is the biggest *speed* hit after crypto — all-hist monthly −17%,
  days +15-17%, stress15 −11-12pp. But it has deep multi-year history (65 active days across 2015-26),
  so it is **far more out-of-sample-trustworthy than crypto**. Its EV is not regime-borrowed.
- **energy_agri (11.6% EV):** smallest top-3 dependence — monthly −9%, stress15 −5-6pp, pass −0.5-0.9pp.

No single non-crypto sleeve breaks the structural pass. Crypto is the only sleeve whose loss both
(a) materially moves a *risk* metric (stress gate) and (b) is concentrated in an un-replayed recent
regime. **Crypto is the concentration risk; metals_core is concentration but not regime-fragile.**

---

## BOTTOM LINE FOR THE OWNER (real money)
1. **The pass/no-pass claim is sound** even if crypto dies. Don't lose sleep over the structural math.
2. **Cut the FORWARD return/speed headline by ~40%** for planning. Plan on **~5-6%/month and ~25-32
   days**, not 9-10%/month and ~15-18 days, unless you are explicitly betting that 2025-26 crypto
   trendiness persists live. The headline forward speed/return is ~1.8× crypto-levered.
3. **Cut the ALL-HISTORY monthly/speed headline ~10%** for crypto-fade.
4. **Watch the stress gate:** without crypto the 1.5×-stress pass falls into the low-0.60s at 1.50%
   nominal. If crypto fades, consider dialing nominal down to 1.25% (stress15 0.63 vs 0.61) to hold
   the tail. Crypto-fade is a *size-down* trigger, not just a return haircut.
5. **Live tripwire:** crypto is 4% of days but ~40-46% of EV. Monitor crypto sleeve EV live; a single
   regime change there moves the book's return profile more than any other sleeve.
