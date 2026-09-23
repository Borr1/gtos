# Touch-Count Gate Independent Reviewer Pass — A19

**Reviewer:** Opus 4.7 max-effort, dispatched 2026-04-25 with explicit instruction to perform the analysis FROM SCRATCH before reading A11's report, then compare.

**Audit target:** A11's recommendation to LOOSEN_TO_3 the touch-count gate threshold based on +8.52R/12wk uplift on A1 + A2 backtest data (n=98 combined filled CANDs).

---

## Verdict

**REJECT LOOSEN_TO_3. Confidence: HIGH.**

Recommendation: keep gate at `>= 2 reject` for Monday FTMO deploy. Implement the ADR-005 touch-count shadow logger. Re-evaluate after ≥30 production rejection events / ≥6 weeks live data.

---

## Independent re-analysis (no peek at A11's report until completion)

### Re-derived per-stratum statistics

Direction-aware touch lookup against A1 (75 filled) + A2 (30 filled) backtest data:

| Stratum | Combined n | Wins | WR | Wilson 95% CI | Exp R | totR |
|---:|---:|---:|---:|---|---:|---:|
| 1 | 42 | 18 | 42.9% | [28.7, 58.3] | +0.071 | +3.00 |
| **2** | **33** | **19** | **57.6%** | **[40.8, 72.8]** | **+0.439** | **+14.50** |
| ≥3 | 23 | 10 | 43.5% | [25.6, 63.2] | +0.088 | +2.02 |

### Counterfactual on A1 (gate ACTIVE vs INACTIVE at each threshold)

| Threshold | Kept n | Kept totR | Rejected n | Rejected totR | Δ vs KEEP=2 |
|---|---:|---:|---:|---:|---:|
| KEEP >=2 (current) | 32 | +0.50R | 39 | +8.52R | — |
| LOOSEN_TO_3 | 57 | +8.00R | 14 | +1.02R | **+7.50R** |
| LOOSEN_TO_4 | 65 | +12.52R | 6 | −3.50R | +12.02R |
| REMOVE | 71 | +9.02R | 0 | 0 | +8.52R |

**Key finding #1:** A11's headline "+8.52R/12wk" is the REMOVE−KEEP delta, NOT LOOSEN_TO_3−KEEP. True LOOSEN_TO_3 uplift is **+7.50R on A1** alone, **+12.00R on A1+A2 combined**. A11 conflated the threshold semantics in the headline.

### H1 vs H2 2026 regime split (A11 did not perform this split)

**H1 2026 (Jan+Feb), n=36 filled:**

| Touch | n | WR | ExpR | totR |
|---|---:|---:|---:|---:|
| 1 | 13 | 46.2% | +0.154R | +2.00R |
| **2** | **16** | **75.0%** | **+0.875R** | **+14.00R** |
| ≥3 | 7 | 42.9% | +0.074R | +0.52R |

**H2 2026 (Mar+Apr), n=35 filled:**

| Touch | n | WR | ExpR | totR |
|---|---:|---:|---:|---:|
| 1 | 19 | 36.8% | −0.079R | −1.50R |
| **2** | **9** | **11.1%** | **−0.722R** | **−6.50R** |
| ≥3 | 7 | 42.9% | +0.071R | +0.50R |

**Key finding #2:** Touch=2 stratum REVERSES from +14R in H1 to −6.5R in H2. The pooled +7.50R uplift is regime-confounded — entirely Jan-Feb regime driven. Most recent 2 months show touch=2 decisively losing.

If LOOSEN_TO_3 had been active in H2 only:
- Would have ACCEPTED 28 trades (touch=1: 19, touch=2: 9)
- TotR: −8.00R (touch=1: −1.50, touch=2: −6.50)
- vs KEEP at ≥2 reject would have ACCEPTED 19 touch=1 trades, totR −1.50R
- **Delta H2: −6.50R** — the gate-loosen would have HURT us in the most recent regime

### Statistical power at n=98

Power to detect Δ Exp R = 0.20R difference at α=0.05 = **~10%**. Pairwise Fisher tests do NOT survive Bonferroni at α=0.0167 (smallest corrected p=1.000). The point estimate ordering (touch=2 best) is consistent across A1, A2, per-instrument cells, but absolute-significance bar isn't met.

### Per-instrument generalization

Every (instrument × backtest) cell shows touch=2 with highest Exp R. Cross-validates the pooled signal — but every cell suffers the H1/H2 regime confound when split.

---

## Comparison with A11

| Dimension | A11 finding | A19 independent finding | Agreement |
|---|---|---|---|
| Pooled per-stratum ranking | touch=2 best | touch=2 best | YES |
| Headline R uplift | "+8.52R/12wk" | True LOOSEN_TO_3 uplift = +7.50R; A11's number was REMOVE−KEEP | DISAGREE on headline |
| H1 vs H2 split | Not performed | Touch=2 reverses (+14R H1, −6.5R H2) | A19 KEY ADD |
| Bonferroni significance | None survive | None survive (confirmed) | YES |
| Statistical power | Not stated | ~10% at n=98 | A19 KEY ADD |
| Recommendation | LOOSEN_TO_3 | KEEP at >=2 + ADR-005 logger | DISAGREE |

A11's analysis was directionally correct on the pooled data but missed the regime-split that reverses the conclusion. The "+8.52R" headline conflated REMOVE with LOOSEN_TO_3 thresholds.

---

## Why REJECT LOOSEN_TO_3

1. **Regime-confounded uplift.** +14R H1 advantage came from Jan-Feb 2026 trending bull regime. −6.5R H2 cost in Mar-Apr (the most recent regime). Pooled +7.50R is dominated by the early regime which has aged out.

2. **Aligns with documented quarterly decay.** CLAUDE.md unresolved item #9: XAUUSD H1 64.5% WR vs H2 24.0% WR, chi-square p=0.006. Same regime mechanism that's hurting our overall WR is also flipping the touch=2 signal. Cannot be coincidence.

3. **Statistical fragility.** n=98, ~10% power, no pairwise tests survive Bonferroni. The signal is real but the magnitude is not pinned.

4. **Memory `feedback_walk_level_evidence_not_predictive.md`** explicitly warned: "walk-level statistics that don't survive regime split are not predictive." Same pattern as the V4-A nudge that was REJECTED for the same reason.

5. **Per-exact-touch is non-monotone** (touch=3 actually wins in some cells) — overfitting tell.

6. **The mathematical optimum is T=4** (LOOSEN_TO_4 keeps +24.52R) — if we trust the analysis, T=4 should be optimal, but accepting that means accepting an even more extreme hypothesis on n=14 trades. Strong overfitting signal.

---

## Recommended path

**KEEP gate at `>= 2 reject` for Monday.** 

Implement ADR-005 touch-count shadow logger (already drafted, ready to ship). The logger collects PASS+REJECT decisions in production from Monday onward.

After ≥30 production rejection events from a single regime (~6 weeks), re-evaluate with:
- Live data (not backtest)
- Single-regime (eliminates the H1/H2 confound)
- Accept rate vs realized R per stratum

If the data then supports loosening, the config knob (`gate1.touch_count_reject_threshold`) makes the flip a 1-line YAML change.

If we MUST do something Monday, prefer SOFT_FEATURE (move touch-count signal to prompt as a contextual input) over hard-gate loosen. Less regime risk.

---

## Methodological lessons captured

1. Pooled-stratum analyses over multi-regime data hide regime-dependent reversals. ALWAYS split by regime.
2. Headline R-uplift numbers must specify their threshold semantics explicitly. "REMOVE delta" ≠ "LOOSEN delta."
3. n=98 is small. Power calculations should accompany every threshold-change recommendation.
4. The same memory lesson (`feedback_walk_level_evidence_not_predictive.md`) applies recursively — even the post-walk realized-R analysis can hide regime confounds.

---

*A19 reviewer pass. Independent verification of A11's recommendation. CEO and main thread accepted REJECT verdict — ADR-005 logger SHIPPED via commit `fba3875` 2026-04-25.*
