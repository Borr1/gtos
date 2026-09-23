# Agent F — Position-Management Adjacent Hypothesis Backlog

**Author:** Forensic Agent F (J46-J49 + S79 mechanism decomposition)
**Date:** 2026-04-29
**Source data:** Mechanism analysis in `agent_f_j46_s79_mechanism.md` + literature synthesis groups D + E + F.

## Executive summary

J46-J49 + S79 are GTOS's two DSR-validated alphas, both at the **position-management layer** (not signal-detection). The mechanism analysis shows:
- **J46-J49 mechanism:** "Don't truncate the upside; protect the downside via BE-pull at 3R." Each component (J46 partial=0%, J47 immediate-on-TP1, J49 TP1=3.0R) contributes ~+0.24R independently. J48 time-stop contributes ~+0.01R. Sum = +0.742R.
- **S79 mechanism:** "Double the position size on the same Sharpe; let Kelly do the work." cap raise (2->4) ACTUALLY DETRACTS by 2.4pp; the entire +25.8pp lift is base_risk_pct doubling.
- **Independence verdict:** S79 and J46-J49 are orthogonal (S79 = position-size scalar; J46-J49 = per-trade R-distribution transform). They compound multiplicatively in expected value.

**The portfolio-of-edges question:** if 2 DSR-validated alphas already exist at position-management layer, and AI selectivity at signal-detection layer is decaying (F11 + F15), Phase 2 effort should be biased toward FINDING MORE position-management alphas (high-yield, edge-decay-immune) rather than rebuilding signal-detection.

---

## Hypothesis taxonomy (top 20 ranked)

Each hypothesis scored on:
- **Magnitude prior:** expected lift in R/trade (literature + GTOS prior).
- **DSR feasibility:** can it be tested at current cohort size with proper trial-budget accounting?
- **Independence:** orthogonal to J46-J49 + S79?
- **Cost:** approximate test cost (engineering days; NOT API).
- **Combined score:** mag × independence × DSR-feasibility / cost.

---

### Tier 1 — HIGHEST EV, lowest implementation cost (rank 1-5)

#### 1. **H-PM01 Vol-conditional position sizing (Barroso-Santa-Clara port, Phase 2 sharpe_weighted)**
- **Description:** `position_size_R = base_R × clip(target_vol / realized_R_vol_30d, 0.5, 2.0)` per-instrument.
- **Magnitude prior:** +30-50% Sharpe vs uniform_fn 2.0% (Barroso-Santa-Clara 2015 magnitude). Translates to ~+0.10-0.25R/trade.
- **Independence:** ORTHOGONAL to J46-J49 (changes risk-per-trade scalar); PARTIAL OVERLAP with S79 (same scalar axis but conditional on vol regime). Replaces uniform_fn.
- **DSR feasibility:** HIGH. n=129 in S79 MC + 1798 mechanical cohort = comfortable n. Trial budget N=200-500; expected DSR z = 5-7.
- **Cost:** 1-2 days engineering + 1 day MC re-run.
- **Score:** 9/10. **HIGHEST PRIORITY.** Already endorsed by Phase 2 + S79 caveat #3 + Group D Theme 3.
- **Pre-registered prediction:** P(pass FN) jumps from 0.844 to 0.92-0.95 at same MTM-DD ceiling.

#### 2. **H-PM02 EVT-CDaR sizing under FN MTM-DD constraint (Strub 2014/2018 port)**
- **Description:** Replace fixed 2.0% with EVT-fitted CDaR-constrained sizing: `f_t = argmax E[log W_T] s.t. P(MTM-DD >= 4%) <= 0.02`.
- **Magnitude prior:** 10-20% higher growth at same MTM-DD (Strub 2018 magnitude). Translates to ~+0.05-0.15R/trade.
- **Independence:** Replaces S79 base_risk_pct as the sizing rule. NOT independent of S79 — it IS the next-generation S79.
- **DSR feasibility:** HIGH. EVT-fit on n=129 has acceptable variance via bootstrap.
- **Cost:** 2-3 days engineering (EVT machinery + GPD fitting + constraint solver).
- **Score:** 8/10.
- **Pre-registered prediction:** Sharpe per dollar deployed +12-18% over uniform_fn 2.0%.

#### 3. **H-PM03 Side-aware sizing with regime conditioning (H-D2 from Group D synthesis)**
- **Description:** `LONG=0.5x in {trending_bull, transitional} AND realized_vol_z > +1; 1.0x otherwise. SHORT=1.0x always.`
- **Magnitude prior:** +20-40% LONG-side realized R/trade (Daniel-Moskowitz 2016 magnitude on momentum crashes). Translates to ~+0.05-0.10R/trade portfolio.
- **Independence:** ORTHOGONAL to S79 + J46-J49.
- **DSR feasibility:** MEDIUM. n=129 with side stratification = 64 LONG / 65 SHORT, marginal for proper trial-budget accounting.
- **Cost:** 1-2 days (regime classifier already exists; sizing modifier is config edit).
- **Score:** 8/10. **F15 + F2 ALREADY pinpoint this cell.**
- **Pre-registered prediction:** XAUUSD H2 P(pass) recovers from 0.515 to 0.60-0.65.

#### 4. **H-PM04 J46-J49 + S79 combined-MC re-run (validation gate)**
- **Description:** Re-run S79 bootstrap MC with J46-J49 winner R-distributions instead of historical-baseline R-multiples.
- **Magnitude prior:** Validation, not new lift. Determines if combined ship requires base_risk_pct backoff.
- **Independence:** NA (it's a verification of independence claim).
- **DSR feasibility:** HIGH (same MC infrastructure).
- **Cost:** 0.5 day to re-run.
- **Score:** 9/10. **MUST run before J46-J49 main-merge.**
- **Pre-registered prediction:** Combined P(pass FN) > 0.90 at base=2.0%; P(bust HARD) <= 0.025.

#### 5. **H-PM05 Continuous-sized OB entries via K54 score (Cartea-Jaimungal port, H-D5)**
- **Description:** Replace binary CANDIDATE -> 2% sizing with continuous K54-score -> [0.5%, 3.0%] sizing.
- **Magnitude prior:** +15-30% portfolio realized R (Cartea-Jaimungal 2016 + Bertram 2010). Translates to ~+0.10-0.25R/trade.
- **Independence:** ORTHOGONAL to J46-J49; CO-DEPENDENT on K54 v3 maturity (which is Phase 2 rank #1).
- **DSR feasibility:** MEDIUM. Depends on K54 OOS Sharpe; current K54 v1/v2 marginal.
- **Cost:** 3-5 days (continuous mapping + canary fixtures + safety gates).
- **Score:** 7/10. Bundles with K54 v3.

---

### Tier 2 — Strong literature backing, mid-cost (rank 6-12)

#### 6. **H-PM06 Trailing stop at ATR-based distance (J45 follow-up)**
- **Description:** GBPUSD `atr-0.5` trailing stop (J45 finding +1.321R/trade n=35 p=0.003) as default-OFF config flag. Applied to remainder leg post-J46 partial close.
- **Magnitude prior:** +1.32R for GBPUSD (n=35); portfolio impact uncertain.
- **Independence:** SEMI-INDEPENDENT of J46-J49 (J46-J49 currently uses fixed BE/SL). Could be added to remainder leg.
- **DSR feasibility:** LOW for portfolio (n=35); HIGH for GBPUSD-specific.
- **Cost:** 1-2 days engineering + canary.
- **Score:** 6/10.

#### 7. **H-PM07 Chandelier exit (high - 3*ATR for LONG)**
- **Description:** Replace J46-J49's higher-target=2*TP1=6.0R with chandelier-exit (3*ATR below recent high).
- **Magnitude prior:** +5-15% Sharpe in trend-following literature (Kestner 1995; LeBeau 1992).
- **Independence:** REPLACES J46-J49's higher-target axis.
- **DSR feasibility:** MEDIUM.
- **Cost:** 1-2 days.
- **Score:** 6/10.

#### 8. **H-PM08 Time-of-day forced close (NY close + KZ-end)**
- **Description:** Force-close all open positions at NY-close (16:00 UTC) regardless of policy. Mitigates overnight gap risk.
- **Magnitude prior:** Eliminates overnight-gap losses (~2-5% of trades). Net effect TBD — may forfeit upside.
- **Independence:** ORTHOGONAL to J46-J49 (overrides time-stop axis at session boundary).
- **DSR feasibility:** HIGH.
- **Cost:** 0.5-1 day.
- **Score:** 5/10.

#### 9. **H-PM09 Multi-level scale-in (50%/50% across 2 entries)**
- **Description:** Split CANDIDATE entry into 2 entries: 50% at OB midpoint, 50% at OB low/high (50% Fib retrace).
- **Magnitude prior:** Improves average entry; reduces SL-hit-on-overshoot frequency. Estimated +0.05-0.15R/trade.
- **Independence:** AT EXECUTION layer (NOT position-management). Orthogonal to J46-J49.
- **DSR feasibility:** MEDIUM. Requires sub-bar OHLCV walking.
- **Cost:** 3-5 days (execution refactor + canary).
- **Score:** 5/10.

#### 10. **H-PM10 Partial-close ratio AT 6R higher-target (not at TP1=3R)**
- **Description:** Variation on J46-J49: still 0% at TP1=3R + immediate BE; ALSO 50% at 6R + trail remainder. Captures fat-tail upside while banking some.
- **Magnitude prior:** +0.05-0.20R/trade depending on instrument fat-tail thickness.
- **Independence:** EXTENDS J46-J49.
- **DSR feasibility:** HIGH. Use existing J46-J49 sweep infra.
- **Cost:** 1-2 days.
- **Score:** 7/10. **Direct J46-J49 extension.**

#### 11. **H-PM11 Cross-instrument basket hedge (XAU+XAG + USDJPY+GBPJPY pairs)**
- **Description:** Open offsetting positions in correlated pairs at 0.5x size each, reducing net exposure by 50% but doubling participation.
- **Magnitude prior:** Reduces variance ~25%; same expected R; +30-50% Sharpe.
- **Independence:** ORTHOGONAL to J46-J49 + S79; touches CONCURRENT_TRACKER + correlation gate.
- **DSR feasibility:** MEDIUM. Requires per-fill correlation modeling.
- **Cost:** 3-5 days.
- **Score:** 6/10.

#### 12. **H-PM12 BE-move at structure (anchor to last swing low/high, not R-multiple)**
- **Description:** Replace J47 R-based BE trigger with structure-based: BE pulls when price breaks last swing low/high in trade direction.
- **Magnitude prior:** Smaller variance in time-to-BE; protects against flat-tail SL-cluster sweeps.
- **Independence:** REPLACES J47 axis.
- **DSR feasibility:** MEDIUM (requires structure detection on M15).
- **Cost:** 2-3 days.
- **Score:** 5/10.

---

### Tier 3 — Speculative, lower priority (rank 13-20)

#### 13. **H-PM13 Pyramid scale-in on continuation (add 25% at +1R, +2R)**
- **Description:** Add to winning positions at MFE=1R, 2R checkpoints. Inverse of partial-close.
- **Magnitude prior:** +0.10-0.30R/trade in extreme winners (Edwards-Magee 1948 trend-following). Compounds with J46-J49 0%-partial.
- **Independence:** ORTHOGONAL to J46-J49 (different operation).
- **DSR feasibility:** MEDIUM.
- **Cost:** 3-5 days (execution + risk-budget tracking).
- **Score:** 6/10.

#### 14. **H-PM14 Mid-trade regime-flip flatten (REJECTED by H37 but worth re-test)**
- **Description:** Force-close on M15 regime classification flip vs entry-regime.
- **Magnitude prior:** H37 found p=0.564 (NOT predictive at n=335). Likely no lift.
- **Independence:** ORTHOGONAL.
- **DSR feasibility:** HIGH but expected to fail.
- **Cost:** 0.5 day re-test.
- **Score:** 3/10. **Likely null but inexpensive to confirm.**

#### 15. **H-PM15 Alternative time-stop bases (M15 ATR-bars vs fixed bars)**
- **Description:** Time-stop = N M15 bars where realized vol is below threshold; longer time-stop in low-vol regimes.
- **Magnitude prior:** +0.02-0.05R/trade.
- **Independence:** REFINES J48 axis.
- **DSR feasibility:** MEDIUM.
- **Cost:** 1-2 days.
- **Score:** 4/10.

#### 16. **H-PM16 Volatility-targeted SL distance (ATR-based, regime-conditional)**
- **Description:** `sl_distance = max(zone_height, k * realized_vol_30d)` where k is regime-conditional.
- **Magnitude prior:** ATR-only is 1980s tech (Group D Theme 3). HAR-RV or rough-vol replacement: +5-15% Sharpe.
- **Independence:** ORTHOGONAL.
- **DSR feasibility:** MEDIUM.
- **Cost:** 2-3 days.
- **Score:** 5/10.

#### 17. **H-PM17 News-event circuit breaker (FED/NFP closes)**
- **Description:** Force-close all positions 5min before FED/NFP/CPI releases.
- **Magnitude prior:** Eliminates news-induced gap losses (~1-2% of trades).
- **Independence:** ORTHOGONAL.
- **DSR feasibility:** HIGH.
- **Cost:** 1-2 days (calendar integration).
- **Score:** 4/10.

#### 18. **H-PM18 KZ-conditional risk-per-trade (NY = 1.5x London)**
- **Description:** Per-KZ risk-pct multiplier; NY shows highest WR (62.8% in mechanical cohort).
- **Magnitude prior:** +5-10% portfolio Sharpe.
- **Independence:** REPLACES uniform_fn ratios.
- **DSR feasibility:** MEDIUM.
- **Cost:** 1 day config.
- **Score:** 5/10.

#### 19. **H-PM19 Round-number-anchored TP (Osler 2005 port)**
- **Description:** Set TP not at fixed R-multiple, but at next round-number anchor in trade direction (e.g. XAUUSD next $50 level).
- **Magnitude prior:** +0.05-0.20R/trade (Osler 2005 evidence on FX). Bundles with K54 round-number feature (H-D-Group-D-domain-9).
- **Independence:** REPLACES J49 axis.
- **DSR feasibility:** MEDIUM.
- **Cost:** 2-3 days (round-number detection + TP re-targeting).
- **Score:** 6/10.

#### 20. **H-PM20 Equity-curve-based position sizing (anti-streak modulation)**
- **Description:** Reduce risk-pct by 0.5x after 3 consecutive losses; restore on first winner. (More aggressive than H29's 8% DD floor.)
- **Magnitude prior:** -DD reduction; mild expected-R reduction. Net P(pass) +2-5pp.
- **Independence:** ORTHOGONAL to J46-J49; PARTIAL overlap with S79 (modifies sizing).
- **DSR feasibility:** HIGH.
- **Cost:** 1-2 days.
- **Score:** 5/10.

---

## Top 3 most-promising adjacent variants (recommended dispatch)

1. **H-PM01 Vol-conditional position sizing (Barroso-Santa-Clara port).** Strongest literature backing (≥6 papers, +30-50% Sharpe magnitude), bundles directly with S79 Phase 2 sharpe_weighted, low engineering cost. **Most promising.**

2. **H-PM10 Partial-close ratio at 6R higher-target.** Direct extension of J46-J49 winner; uses existing J46-J49 sweep infrastructure; tests fat-tail truncation at the 2nd target level. **Easiest to implement (1-2 days).**

3. **H-PM03 Side-aware sizing with regime conditioning.** F15 + F2 already pinpoint XAUUSD London/trending_bull/LONG as the load-bearing decay cell. Direct test of side-aware (LONG=0.5x SHORT=1.0x); uses regime classifier already in shadow mode. **Most-precisely-targeted at known decay.**

## Discovery rate estimate

J46-J49 was found via the H-series exploration program over ~9 months (J45 + J46-J49 + side_aware + S79). 4 DSR-grade candidates examined; 2 SURVIVED DSR (J46-J49, S79). Discovery rate ≈ 0.5 grade-A alphas / quarter / position-management agent.

If 1 dedicated agent runs the top-20 backlog above at 1-3 days per hypothesis: 
- **Top 5 candidates testable in ~10 days.**
- **Top 10 candidates testable in ~20-30 days.**
- **Expected new SURVIVING DSR alphas: 1-2 of top 5; 3-4 of top 10.**

Renaissance Medallion model: 100+ small uncorrelated edges driving Sharpe ~3-4. GTOS at 2 alphas is at the **start** of the curve. Realistic 12-month target: 8-12 SURVIVING DSR alphas, contributing +0.3-0.6 cumulative Sharpe over current.

## Phase 2 program implication

The Phase 2 priority order should weight position-management discovery HEAVILY over signal-detection (K54 v3, prompt overhauls). Reasons:
1. Position-management alphas are **edge-decay-immune** (orthogonal to F11 + F15 erosion). Signal-detection alphas decay with publication.
2. Position-management sweep cycle is **short** (1-3 days per hypothesis vs K54 v3 sweep-cycle 2-3 weeks).
3. Position-management lifts **stack multiplicatively** with each other and with signal-detection.
4. The 2 SURVIVING alphas (J46-J49, S79) ARE the program's currently-best-evidence-based output. Building on this thread is highest-EV.

**Recommendation:** Phase 2 dispatch H-PM01, H-PM10, H-PM03 in parallel (3 sub-agents, ~10 days). Then H-PM04 (validation gate) before any ship.
