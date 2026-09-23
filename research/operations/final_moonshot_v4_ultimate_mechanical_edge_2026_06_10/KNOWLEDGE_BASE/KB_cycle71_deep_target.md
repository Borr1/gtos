# KB cycle 71 — the DEEP-TARGET breakthrough (robust) + honest correction of c69's prediction over-claim

## What happened
The c69 verification (tail_v2 Workflow, adversarial) found that c69's celebrated "predict-the-tail + ride"
was OVER-CLAIMED: the ML PREDICTION is within-noise at the 51-trial deflation and OOS-insignificant, and
**ride-ALL-deep with NO predictor beats the selective policy on raw mean-R** — i.e. the DEEP TARGET, not the
prediction, is the driver. CONFIRMED_REAL from that workflow = []. This cycle audits the deep target itself,
paired (same trades, only the target depth changes), to see if it is robust or 2025-regime luck.

## RESULT — deepening the metals target ≥4R is a ROBUST, every-year-positive improvement (the real breakthrough)
Paired per-trade test (structural stop unchanged = same −1R downside; only the target depth changes), with a
paired sign-flip permutation, per year:
| depth | SEALED Δ vs 2R | paired p | OOS Δ | per-year Δ (2022..2026) |
|---|---|---|---|---|
| 3R | +0.018 | 0.40 | +0.037 | within-noise (matches wave5/c67) |
| **4R** | **+0.222** | **0.022** | +0.344 (p .047) | +0.50/+0.59/+0.07/+0.27/+0.15 |
| **5R** | **+0.330** | **0.012** | +0.424 | +0.43/+0.88/+0.08/+0.38/+0.26 |
| **6R** | **+0.371** | **0.013** | +0.629 (p .022) | +0.53/+1.15/+0.30/+0.40/+0.33 |
| **8R** | **+0.593** | **0.002** | +0.813 (p .015) | +0.33/+1.45/+0.64/+0.54/+0.68 |
- **Positive in EVERY year 2022–2026, including the 2022–23 metals BEAR** → NOT regime-concentrated (this is
  what makes it robust where c69's selection was sealed/2025-only). Monotone increasing in depth = a coherent
  structural gradient, not a cherry-picked cell. Survives multiplicity (8R sealed p=0.002, Bonferroni×5=0.01).
- Sealed mean-R: 0.227 (2R) → 0.449 (4R) → 0.598 (6R) → 0.820 (8R).
- **Why it works:** the metals edge is fat-tailed momentum (c66: MFE mean 3.5–4.4R, p90 10–14R). A 2R target
  caps the runners and leaves the tail on the table; a deep target lets the ~25% big winners pay for the lower
  hit-rate (win-rate drops 0.42→0.23 at 8R — by design; the asymmetry, capped −1R vs large upside, wins).
- **Why wave5/c67 missed it:** they tested 2R/3R (within-noise — confirmed here at 3R) and a 3×ATR target in a
  separate-stream comparison; the significant jump is at 4R+ and shows cleanly only in the PAIRED test.
- **Downside-neutral (sizing_revalidation):** same −1R stop → worst day IDENTICAL to fixed-2R at every base,
  0% daily-breach (bases 1.0–2.5%); the deeper target adds variance only on the UPSIDE → it LIFTS the safe
  base from 1.25% to 2.0% (faster passes, not deeper losses).

## HONEST STATUS
- **c69 prediction/selection: RETRACTED as a breakthrough** — within-noise at deflation, OOS-insignificant,
  not the driver. (It retains a minor RISK-ADJUSTED role: keeping ~70% of trades on 2R gives a higher
  Sharpe-like ratio + win-rate than ride-all-deep, and concentrates the ride-benefit 7.5×. A refinement, not
  the edge.)
- **Deep target (≥6R): REAL, robust, deployable (gated) candidate.** Paired-significant, every-year-positive,
  downside-neutral, raises the safe base. The strongest geometry finding in the program.
- **Tradeoff (honest):** lower win-rate (0.23–0.25 at 6–8R) and longer holds (up to maxbars=80 ≈ 13 days) —
  psychologically harder, and a velocity cost per trade, but per-trade EV is far higher and the sizing
  analysis shows FASTER challenge passes (higher EV compounds despite longer individual holds; no FTMO time
  limit). CHECK NEXT: R-per-bar (velocity) across depths; the live W7 sleeve's current target (parity); pick
  6R vs 8R on the risk-adjusted frontier (8R has highest EV but lowest win-rate/longest holds).

## DISPOSITION
Deploy candidate (gated, owner-decides): deepen the metals target to ~6R (verify live sleeve parity first;
sizing already re-validated at base 2.0% / 0% daily-breach / smooth DD-defense). This is the deep-target
core; any predictive selection on top is a separate, not-yet-confirmed refinement.

**Files.** `CYCLE71_deep_target_audit.py`, `KNOWLEDGE_BASE/validation/CYCLE71_DEEP_TARGET_AUDIT.json`;
verification `KNOWLEDGE_BASE/validation/TV2_VERIFY_C69.json`.


---
## CORRECTION (cycle 75 — DEPLOYMENT GATE): this win was a SAME-BASE mean-R artifact.
At vol-matched (iso-ruin) book sizing the deep target does NOT pass faster or earn more — its ~3x higher maxDD
tail forces a size-down -> SLOWER (21 vs 17d), Sharpe only mildly higher on the core (0.103 vs 0.091), LOWER
on the full book (T1). It is a safer-but-slower risk-profile DIAL, not a return/speed breakthrough. See
KB_cycle75_deep_target_DEPLOYMENT_GATE.md. Wrong metric used (mean-R/R-per-bar instead of vol-matched Sharpe).
