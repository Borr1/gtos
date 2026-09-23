# ADVERSARIAL AUDIT VERDICT — GTOS Final Deploy-Book Projections

Date: 2026-06-15
Auditor posture: adversarial, source-bound, calibrate-trust-on-real-money (NOT idea-kill).
Locked engine (verified): `INTEG_portfolio_build.py:298` → `TARGET=0.08; MAXDD=0.10; DAILY=0.05; BLOCK=5; N=20000; PATHCAP=2000`, called as `INTEG_portfolio_build_w2.mc_series`. No-lookahead, real cost, per-year, 20k block-5 paths.
Book reproduced byte-consistent by all four sub-audits: `sd_book=0.56859`, `VS_final=0.7504`, `mean_all=0.10956`, `mean_fwd=0.33550`, `fwd/all=3.06x`, 1679 all-history days / 382 forward days, 11 sleeves.

---

## 0. ONE-LINE VERDICT

**REAL but the headline you would quote is the wrong one.** The *structural* "we pass FTMO" claim is sound and survives every stress (overfit deflation, total crypto death, sub-period splits, 2x execution). The *magnitude* story — and especially the **FORWARD table the go-live dossier leads with (5–14%/mo, 15–22-day pass, ~100% P(pass))** — is inflated ~3–4x and must be discarded for sizing. Deploy on the all-history vol-matched basis with a ~15% magnitude haircut. Expect **~1.8–2.2%/mo and ~2.5–4 months to first pass on a normal regime, NOT ~9%/mo in ~18 days.**

---

## 1. HONEST-ADJUSTED PROJECTION

Basis = **all-history vol-matched, "final" (Kelly-sized)** book — the basis all four audits independently endorse as the reliable one. Headline (verified vs `INTEG_W7_FINAL_RESULT.json /mc_volmatched_all/final`):
`1.25% → P(pass) 99.36%, 2.158%/mo, 79d` · `1.50% → P(pass) 98.59%, 2.590%/mo, 66d`.

Haircuts stacked (NOT naively multiplied — overfit/crypto/exec partially overlap on the crypto sleeve):
- Multiple-testing / overfit: PBO=13.5%, IS→OOS Sharpe haircut 10.7% (band 10–25% on EV).
- Crypto-dependence on the all-history monthly: ~10–11% magnitude (but only −1.6pp pass at 1.25%).
- 2x execution realism (mostly the un-costed crypto sleeve): −10 to −20% magnitude, −1 to −5pp pass.
- Sub-period/regime: the all-history blend IS already the regime-robust estimate; no *further* magnitude cut on this basis (the 3x cut applies to the forward table we are discarding). Cold-year floor noted separately.

| Scenario | Dial | P(pass) | Monthly % | $/100k/mo | Days to 1st pass |
|---|---|---|---|---|---|
| **Optimistic** (mag −8% / pass −1pp) | 1.25% | **~99%** | **~2.0%** | ~$1,985 | **~86d** |
| | 1.50% | ~98.5% | ~2.4% | ~$2,383 | ~72d |
| **Central** (mag −15% / pass −3pp) | 1.25% | **~96–99%** | **~1.8%** | ~$1,834 | **~90–95d** |
| | 1.50% | ~95–98% | ~2.2% | ~$2,200 | ~78d |
| **Pessimistic** (mag −30% / pass −7pp, crypto-fade + bad fills) | 1.25% | **~93–96%** | **~1.5%** | ~$1,511 | **~110–115d** |
| | 1.50% | ~92–95% | ~1.8% | ~$1,813 | ~94d |

Cold-regime floor (if the 2024–26 crypto/metals trend fully reverts to 2019–2023 baseline): per-year all-history monthly@eff was 2023=0.19%, 2022=0.50%, 2020=0.66%, 2019=0.74% → **~0.2–0.7%/mo, first pass could take 5–9+ months at 1.25%.** This is the genuine left tail, not the headline.

### The inflated artifact (FORWARD table) — quantified, DO NOT SIZE TO IT
| Forward headline | As shipped | Honest (shrink to all-hist) | Inflation |
|---|---|---|---|
| Monthly % @1.25% | 8.81% | ~2.4–2.8% | **~3.1–4.1x** |
| Days to pass @1.25% | 18 | ~30 (honest fwd) / ~80–90 (all-hist) | **~1.7x–4.4x** |
| P(pass) @1.25% | 97.9% | ~74–78% (on honest fwd EV) | 99.8%→~76% |
| Daily-R mean | 0.3355 | 0.10956 (all-hist) | **3.06x** |

---

## 2. TOO-GOOD-TO-BE-TRUE vs REAL — SPLIT BY RELIABILITY CLASS

### A. STRUCTURAL PASS-RATE — **REAL. Trust it. ~0–5% inflated.**
This is the "no-time-limit challenge math" and it is robust because it does not depend on the hot regime or on edge magnitude:
- **0% daily-breach is structural**, not fitted. Deflating EV cannot manufacture a −5% day; worst MC day stays ~−2.4/−2.9/−3.6% at 1.25/1.50/1.75% in *both* windows, inside the 5% wall. (Crosses −5% only when 2x-exec is stacked with a 1.5x loss-tail: worst −5.7%, breach 0.06%.)
- **Genuinely diversified**: avg off-diagonal corr +0.003; ~10.85 of 11 effective independent sleeves.
- **Survives overfit deflation**: Deflated-Sharpe DSR > 0.92 all-history even at N=300 trials (n=1679/382 days is large); PBO=13.5%.
- **Survives total crypto death** re-sized to the same risk budget: all-history pass 0.977 (1.25%) / 0.934 (1.50%) — the "we pass" claim holds with crypto fully removed.
- **Survives 2x execution stress**: all-history pass only 99.36/98.59% → 96.59/94.06% (−1 to −5pp).
- **Survives sub-period split**: P(pass)@1.50% = 99.4% (coldest forward half H1) / 100% (H2) / 98.6% (all-history).

### B. EDGE MAGNITUDE (monthly % / $ / speed) — **INFLATED. Halve confidence. ~3x on the forward table, ~10–20% on the all-history basis.**
- **Window contamination is the dominant inflator** (PBO/DSR do NOT catch it): the 2025–26 "holdout" is the #1 and #2 best years in 12 (daily-mean 0.443/0.287 vs 2019–2023 ~0.02–0.07), AND it was the selection surface — 101 of 126 RESULT.json evals scored against this same window. Forward daily-mean is 3.06x all-history; that single ratio is the cleanest inflation measure.
- **Edge is accelerating inside the forward window, not stable**: forward H2 mean = 2.04x H1; quarter means span 2.7x. Trimming within-forward barely helps (−7%) because all forward sub-periods share the same hot regime.
- **Crypto leverages magnitude, not pass**: removing crypto from the forward book *raises* pass (0.979→0.990) while nearly doubling days (18→32) and halving monthly (8.81%→4.95%). Crypto = 38.8% all-hist / 45.8% fwd EV from only **67 days, all post-2024** (zero pre-2024 history) — the least out-of-sample-defensible figure in the book.
- **Profit hyper-concentration**: forward top-10 days = 46% and top-20 = 75% of all forward profit; 43% of active days negative; all-history top-50 days = 96% of total. ~50 outlier days carry the book; MC resamples them into every projection, so monthly%/speed inherit outlier magnitude that real fills erode first.
- **Execution optimism**: the "tick-true" book applies ZERO erosion to crypto (no crypto tick ledger exists) and the metals/JPY erosions it does apply are net *favorable* (XAU +0.019R, JPY +0.018R on thin 14/66-day coverage). Pricing the missing crypto cost cuts all-history monthly ~10–20%.

---

## 3. TOP 3 RISKS TO THE LIVE NUMBERS (ranked)

1. **Regime reversion (the #1 threat to returns and speed).** ~85% of the forward 3x lift is selection/regime luck; the entire crypto sleeve and the bulk of the lift come from a 28-month uptrend. If 2024–26 trendiness fades, monthly collapses toward ~1%/mo and first-pass stretches to 5–9 months. **Mitigation: budget returns to the all-history central case (~1.8–2.2%/mo); treat the forward 8–10%/mo as an upside ceiling, never a base case.**

2. **Crypto concentration as a single-sleeve tripwire.** 40% all-hist / 46% fwd EV, highest EV/active-day, zero pre-2024 history, AND completely un-costed for execution. It props the 1.5x-stress gate too (+13–16pp). It does NOT threaten pass (re-sized pass stays 0.93–0.98) but it owns the magnitude. **Mitigation: monitor live crypto-sleeve EV as the book's single largest regime tripwire; on crypto-fade, size down 1.50%→1.25% rather than expecting the return to hold.**

3. **Execution / outlier fragility under real fills.** ~50 outlier days carry the entire book and the dominant sleeves are charged almost no real friction. Under realistic 2x execution the maxDD-stress failure rate is **~1-in-3, not the headline ~1-in-4** (stress15 P(pass)@1.50% 73.5%→57–64%). **Mitigation: size for the ~1-in-3 stress-fail, fund extra challenge attempts in the budget, and add a real crypto execution cost to the model before the next book revision.**

---

## 4. BOTTOM LINE FOR THE OWNER

- **Believe "we will pass."** The structural pass mechanics (0% daily-breach, low cross-sleeve correlation, positive Sharpe surviving multiple-testing deflation, robustness to crypto death and 2x execution) are sound on real money. Deploy 1.25% first-cycle, step to 1.50% after a clean pass.
- **Do not believe the speed and return headlines.** The mc_forward table (5–14%/mo, 15–22-day pass, ~100% P(pass)) is the single most inflated artifact in the book — in-sample to selection, anchored to the two best years ever, crypto-levered, and outlier-driven. Discard it for sizing.
- **Plan around: ~1.8–2.2%/mo, ~2.5–4 months to first pass on a normal regime; ~1%/mo and 5–9 months in a cold regime; the advertised ~9%/mo & ~18 days only if the 2024–26 regime persists.**

Artifacts cross-checked: `INTEG_W7_FINAL_RESULT.json`, `INTEG_portfolio_build.py` (locked constants L298), `AUDIT_overfit_mt.md`, `AUDIT_sleeve_dependence_RESULT.json`, `AUDIT_subperiod_stability_RESULT.json`, `AUDIT_exec_stress_RESULT.json`, `AUDIT_recent_slice_RESULT.json` (all under `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`).
