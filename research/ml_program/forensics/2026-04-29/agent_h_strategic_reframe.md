# Agent H — 1-Page Strategic Reframe

**Date:** 2026-04-29 | **Author:** Forensic Agent H | **Audience:** CEO / Phase 2 program

---

## The 8 DSR-failed Validated Numbers are not 8 failures. They are 5 over-stratified headlines + 1 reversed feature, all clustering into 2 patterns. The program's true alpha structure is simpler than it looked.

### What we now know

**The program has 3 alphas + 1 specialist, not 8+.**

| # | Alpha | DSR-p | Class | Status |
|---|-------|------:|-------|--------|
| 1 | **J46-J49 portfolio policy** (+0.742R/trade) | 1.23e-7 | Position management | Live A/B 30d, then ship |
| 2 | **S79 risk policy** (uniform_fn 2.0%, +25.8pp P(pass FN)) | <2.22e-16 | Risk-policy sizing | Shipped; refine via Busseti-Boyd RCK |
| 3 | **AI ~63% baseline** (single signal across all instruments) | implicit via XPER | Signal-detection-as-mechanism | Confirmed by cross-period mechanical OB at z=10.5 |
| 3.5 | **NAS_US30 specialist** (+0.103 paired AUC, replicated 2×) | borderline | Per-cohort ML | K55-shadow deploy at p≥0.55 |

### What killed the headline numbers

**Failure Mode A — Signal-Detection-As-Classification on Stratified Small Cohorts.** Per-instrument WR claims (XAUUSD 62%, USDJPY 75.8%, US30 58.5%, GBPJPY 57.1%) are **statistically indistinguishable from a single underlying ~63% baseline** (chi²=3.27, df=3, p>0.35). They are 4 stratifications of one signal, not 4 independent edges. DSR correctly killed them as over-stratified noise.

**Failure Mode B — Headline-Is-Overfit-Baseline-Artifact.** OB-advantage +17pp FAILS DSR but the underlying mechanism (mechanical OB-retest mean-R > 0) **SURVIVES** independently on the 2022-2023 cross-period cohort at z=10.5. The headline number was the overfit; the mechanism is real.

**The 1 truly dead claim:** FVG-in-impulse — direction REVERSED in K52, no mechanistic survivor.

### Why position-management + risk-policy + cross-period-mechanism survive while signal-detection-classification fails

**Different alpha classes operate at different effective N.** J46-J49 tests on filled trades (paired-fill effective n=321). S79 tests on MC P(pass) over 1000 trials per config. XPER tests on 1798-trade out-of-sample cohort. All have effective N >> the per-instrument WR claims (33-131). DSR's noise ceiling is the same for everyone; the survivors clear it because they have more signal density per claim.

### What this means for Phase 2 / Q1.5

| Pursue | De-prioritize |
|--------|---------------|
| Position-management variants (J45 trail, side-aware sizing, J46-J49 ship) | Per-instrument WR re-validation |
| Risk-policy refinements (Busseti-Boyd RCK, Strub EVT-CDaR, Moreira-Muir vol-scaling) | More K54 architecture iteration on n=528 cohort |
| Per-cohort specialists (NAS_US30 deploy + extend to precious metals, JPY crosses) | OB-advantage relative-claim re-tests |
| Cross-period anchors (XPER 2022-2023 as validation-only for K54 v4) | FVG as positive feature |
| **Cohort EXPANSION** (4-6 weeks data eng → n≥5000) | Re-claiming "8 Validated Numbers" |

### Lo's AMH frame on edge decay

GTOS observed decay (73% YoY on OB advantage) **vastly** exceeds McLean-Pontiff industry baseline (5%/yr). BUT F15+A6 attribute the H2-2026 collapse to **regime-conditioned LONG-side selectivity** caused by the v1 detector's 100%-bullish bias trapping the AI in the trending_bull cohort. Once v2 detector is fully active and SHORT-side accumulates n≥30, the long-run decay rate should regress toward McLean-Pontiff baseline. **GTOS decay is not industry-baseline AMH; it is regime-trapped detector failure overlaid on baseline AMH.** The fix (v2 detector + side-aware sizing + K54 v4 regime-aware) is already in motion.

### The DSR-budget discipline forward

**Each architecture iteration on the same cohort burns trial budget for ALL claims tested on that cohort.** K54 v1/v2/v3 have cumulatively burned ~500 trials of DSR budget on the n=528 cohort. The DSR ceiling is now near-unreachable on that cohort. **Phase 2 must STOP iterating architectures on n=528 and START 4-6 weeks data engineering to expand to n≥5000.**

Every new lift claim should be tested at TWO levels: headline (standard DSR) + mechanistic (cross-period out-of-sample). If the headline survives but the mechanism doesn't, the claim is overfit.

### Bottom line

The DSR audit didn't reveal that GTOS has no edge. It revealed that **GTOS has 3-4 real edges concentrated in 3 alpha classes**, and **the "8+ Validated Numbers" framing was over-stratified counting**. The program is healthier than it looked; the strategic priority is to **stop discovering new headlines on the burned cohort and start expanding the cohort + iterating on the surviving alpha classes**.

---

*Source: `research/ml_program/forensics/2026-04-29/agent_h_meta_pattern_audit.md` (full audit, ~14 pages).*
