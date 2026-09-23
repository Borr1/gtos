# Agent D — Substrate-Immune Research Directions (Ranked)

**Date:** 2026-04-29
**Companion to:** `agent_d_substrate_audit.md`
**Scope:** Identify substrate-immune research directions ranked by `program_value × current_under_exploration`. These are the directions that REQUIRE NEITHER LOB depth NOR real trade volume — they work today, on MT5 retail, at $0/mo subscription.

---

## Method

- **Program value (1-5):** composite of expected lift (R/trade or Sharpe), DSR-survival probability, and connection to CEO's #1 concern (decay).
- **Under-exploration (1-5):** 1 = heavy ongoing investment; 5 = little or no current dispatch.
- **Score = product** (1-25 range).

Substrate-immunity criteria applied per row (must satisfy all):
1. No `volume`, `last`, or LOB depth required.
2. No paid LOB feed required (Databento, ICE, IEX paid tier).
3. Free public macro feeds (FRED, CFTC COT, WGC, BIS public, CBOE-free dashboards) acceptable.
4. Existing tick stream `bid/ask/inferred_aggressor` allowed for QUOTE-derived features only (Roll-bounce regime caveat applies).

---

## Top 8 Substrate-Immune Directions

### Rank 1 — Risk-policy bundle (H-5 / R-1..R-9 / B-3) — Score 20

**Direction.** Replace S79 uniform_fn 2.0% with literature-grounded multi-component risk policy: Busseti-Boyd Risk-Constrained Kelly under FN constraint × Strub EVT-CDaR sizing × side-aware multiplier × smooth Grossman-Zhou variant of H29.

**Substrate-immunity:** 100%. Inputs: trade history + FN constraint ε. No microstructure, no LOB, no paid macro.

**Program value (5):**
- S79 already shipped +25.8pp P(pass FN) at uniform 2% — bundle replaces uniform with per-instrument optimal weights.
- Literature predicts: vol-managed +15-25% Sharpe (Moreira-Muir post-haircut); side-aware +$8k XAUUSD H2 recovery (memory `project_side_aware_sizing_findings`); per-instrument optimal weights non-uniform.
- Combined post-haircut: +20-35% Sharpe + +0.05-0.15R/trade.
- Decay-orthogonal (risk policy doesn't decay).

**Under-exploration (4):**
- S79 sharpe_weighted explicitly Phase 2 follow-up (memory `project_s79_risk_policy_shipped_2026-04-27`).
- J46-J49 + side-aware ready but not bundled.
- Busseti-Boyd RCK / Strub EVT-CDaR / smooth Grossman-Zhou never implemented.

**Score: 5 × 4 = 20.**

**Suggested next action:** Dispatch a Q1.5-or-Q2 risk-policy modeler agent. 2-3 weeks engineering + 1 month shadow A/B vs current S79.

---

### Rank 2 — Vol-conditioning overlay (H-2 / V-1..V-9 / B-2) — Score 20

**Direction.** Insert Component 3C between Component 3A and Component 4: realized-vol-percentile + VRP + regime-persistence → sigma multiplier ∈ [0.5, 2.0] applied to S79 risk_per_trade_pct.

**Substrate-immunity:** 100%. Inputs: existing OHLCV + free CBOE VIX/GVZ for VRP. No microstructure required.

**Program value (5):**
- Group D + Group E F-4: highest-EV / lowest-cost addition; Barroso-Santa-Clara Sharpe 0.53→0.97 in literature; post-haircut +15-25% Sharpe.
- Multiplies with H-1 K54 v3 (sigma is meta-label head sizing input) and H-5 RCK λ.
- Direct AMH-decay defender (Group E F-1: edge magnitude correlates with funding-stress / vol regimes).

**Under-exploration (4):**
- NA8 partial-answered for one cohort (-1.0% recovery on H1→H2 XAU LONG; cohort-specific result).
- No production Component 3C exists.
- Babu-Hoffman-Levine 2020 decomposition (H-24) is a 1-day pre-requisite analysis.

**Score: 5 × 4 = 20.**

**Suggested next action:** 2-3 days rule-based v1 implementation + 2-week shadow A/B. Then ML-trained version slots into K54 v3 (when reopened).

---

### Rank 3 — Calendar / macro features (A-8/A-9/A-10/A-11/A-12/A-13/A-14 / B-4 / H-13/H-14/H-20) — Score 20

**Direction.** Bundle of free-public-feed macro features:
- A-8 Erb-Harvey real-gold-price percentile (WGC + FRED).
- A-9 Gold COT positioning (CFTC).
- A-10 Gold central-bank-flow (WGC).
- A-11 LBMA fix anomaly (LBMA public).
- A-12 Krohn-Mueller-Whelan FX-fix W-shape.
- A-13 Brunnermeier-Nagel-Pedersen funding-liquidity (FRED TED).
- A-14 Aquilina BIS JPY-carry-unwind (BIS public).

**Substrate-immunity:** 100%. All inputs from free public feeds.

**Program value (4):**
- Each per-feature ≤+0.02 AUC; bundled ≥+0.03-0.05 AUC.
- A-1+A-2+A-3 NAS_US30 dealer-gamma cures cross-period sign-flip (most-supported Group C finding).
- Calendar features are decay-resistant (durable structural-flow mechanisms).

**Under-exploration (5):**
- No current dispatch on this bundle.
- LBMA fix never tested.
- Krohn-Mueller-Whelan W-shape never tested.
- BIS JPY-carry-unwind regime classifier not built.

**Score: 4 × 5 = 20.**

**Suggested next action:** **Free-feed integration sprint** — CFTC COT + FRED + WGC + LBMA + CBOE-GEX scrapers (10 engineering days). Then A-1/A-2/A-3 NAS_US30 dealer-gamma feature for 1 week. Then bundle to H-8 specialist routing.

---

### Rank 4 — AI-grounding bundle (H-10 / L-1..L-8 / B-5) — Score 16

**Direction.** Wire QuantMCP/FinAgent-style tool-use grounding for Component 3A (predicted 70-80% HALLUC reduction); activate Bull/Bear/Judge debate (built-but-not-wired N62, default OFF) in shadow mode; add Reflexion-style post-trade reflection loop.

**Substrate-immunity:** 100%. No microstructure or LOB required. All prompt/tool-architecture work.

**Program value (4):**
- Tool-grounding: 70-80% HALLUC-class precision-bug reduction (Group F + memories `project_halluc_1_precision_bug_class_2026-04-27` + `project_eurusd_sl_root_cause`). Direct CR lift.
- Bull/Bear/Judge: TradingAgents 2024 + AlphaAgents 2025 + FinCon 2024 — 5-15% lift in 30d-3mo backtests.
- Reflexion: ≥0.05R expectancy lift at <$5/mo per L-3 spec.

**Under-exploration (4):**
- Component 3B Bull/Bear/Judge wired but default OFF; CEO DELETE/WIRE/LEAVE decision pending (CLAUDE.md unresolved item #10).
- Tool-grounding not wired into Component 3A.
- Reflexion loop not built.

**Score: 4 × 4 = 16.**

**Suggested next action:** L-1 QuantMCP wiring 2 weeks + 4-week shadow A/B; L-4 Bull/Bear/Judge shadow activation parallel; L-3 Reflexion deferred to Q2.

---

### Rank 5 — Decay observability infrastructure (H-9 / Group A Rank 6+12) — Score 15

**Direction.** Replace S1 monthly-decay shadow monitor's rolling-50 + threshold heuristic with two principled streaming detectors:
- Aue-Kirch 2024 self-normalized multivariate CUSUM on (XAU, US30, USDJPY) joint daily WR/CR/OB-continuation vector.
- Tsaknaki-Lillo-Mazzarisi 2024 BOCPD-AR-score-driven on XAU M15 returns + RV.

**Substrate-immunity:** 100%. Inputs: shadow logs + M15 OHLCV.

**Program value (3):**
- Operational improvement; ≥30% reduction in S1 false-alarm rate at matched detection delay.
- Not direct realized-R lift, but is the decay observability infrastructure CEO #1 concern depends on.

**Under-exploration (5):**
- No implementation; S1 watchdog cron hook DISABLED per CLAUDE.md item #6.
- Aue-Kirch 2024 + BOCPD-AR-score-driven not tried.

**Score: 3 × 5 = 15.**

**Suggested next action:** 2-3 week implementation + 30-day shadow A/B vs current rolling-50 baseline. Promotes S1 watchdog to monitoring+enable.

---

### Rank 6 — Asset-class specialists (H-8 / A-1..A-18 / B-4) — Score 16

**Direction.** Replace generic "FX block" K54 specialist with three asset-class-specialist models (JPY-pair / GBP-pair / dollar-pair) via Lustig-Roussanov-Verdelhan 2-factor decomposition + NAS_US30 specialist with dealer-gamma + VIX1D-VIX9D + LETF-flow features.

**Substrate-immunity:** 100% via free public proxies (CBOE GEX dashboards, FRED, BIS public). NO LOB feed required for the free-substrate version.

**Program value (4):**
- Group C central claim: NAS_US30 cross-period sign-flip is dealer-gamma-regime-flip; FX-cohort negative-lift is mis-specified single-FX-block.
- Per-specialist +0.02-0.04 AUC on each cohort.
- NAS_US30 specialist already strongest single Q1.3 finding (AUC 0.601 / +0.103 lift).

**Under-exploration (4):**
- NAS_US30 specialist exists at 0.6014 but not in production / K55 shadow.
- FX-pair specialists never trained.

**Score: 4 × 4 = 16.**

**Suggested next action:** Ship NAS_US30 specialist to K55 shadow in 1 week. Train FX-pair specialists in 4-6 weeks (parallel per-cohort modelers).

---

### Rank 7 — Methodology bundle (H-6 / M-1..M-16 / B-6) — Score 12

**Direction.** Apply DSR + effective-N + PBO + Romano-Wolf StepM retroactively to all "Validated Numbers" in CLAUDE.md; make the same bundle a mandatory promotion gate for every Q1.4+ "lift" claim.

**Substrate-immunity:** 100%. Closed-form formulas on existing trade samples.

**Program value (4):**
- B-8 partial done 2026-04-29 (M-1/M-3 DSR_VALIDATED, M-2/M-4 DSR_FAILED).
- M-7 (CPCV-honest training-overlap-weighted SE) already adopted in K54 v3 modeler.
- Pending: M-12 effective-N tracker, M-1 (J46-J49 retro DSR — DONE), M-13 PBO baked-in, Romano-Wolf StepM over 47 cells.

**Under-exploration (3):**
- B-8 closed 2026-04-29; B-6 partially complete.
- 5-6 Methodology items still PENDING.

**Score: 4 × 3 = 12.**

**Suggested next action:** Complete B-6 tail items in 2-3 days. Make `dsr_diagnostics.json` mandatory in every research/ artifact with a Sharpe/R/AUC headline.

---

### Rank 8 — K54 v3 substrate-immune feature set (K-7..K-15 + H-11 signature + frac-diff + HAR-RV cascade) — Score 12

**Direction.** Substrate-immune feature engineering for K54 v3 (when cohort permits Q1.5 reopen):
- K-7 Osler stop-cluster proxy (rolling RV near round numbers).
- K-8 Power-law-decayed OB-age weighting.
- K-9 Regime × round_aligned × side interaction features.
- K-10 Above-up below-down round-aligned direction.
- K-11 Per-fold top-100 feature screening.
- K-12 Meta-labeling head over Component 3A.
- K-13 Triple-barrier labeling.
- K-14 Adaptive conformal calibration.
- K-15 TreeSHAP-stability pruning gate.
- H-11 Signature features (depth-3 truncated path) + fractional differentiation + HAR-RV three-cascade RV.

**Substrate-immunity:** 100% (closed-form on existing OHLCV / candidate-OB lists).

**Program value (4):**
- Each +0.02 AUC; bundled +0.04-0.06 AUC.
- Mechanism-grounded; less arbitrage-decayed.

**Under-exploration (3):**
- K54 v3 master bundle attempted 2026-04-29 and FAILED (B-1).
- Q1 closed; Q1.5 conditional on cohort expansion to n>5,000 (4-6 weeks data engineering).
- Substrate-immune features bundled inside the FAILED bundle; need re-validation in isolation.

**Score: 4 × 3 = 12.**

**Suggested next action:** Reopen K54 v3 only after cohort expansion (Q1.5+). Meanwhile, test K-7 + K-8 + K-9 + K-10 as standalone additive features in isolation on Q1.4 cohort.

---

## Summary table

| Rank | Direction | Score | Cost | Engineering effort | Phase | Status |
|---|---|---:|---:|---|---|---|
| 1 | Risk-policy bundle | 20 | $0 | 2-3 weeks | Q1.5-Q2 | Sharpe_weighted Phase 2 deferred |
| 2 | Vol-conditioning overlay | 20 | $0 | 2-3 weeks v1 | Q1.5 | NA8 partial-answered |
| 3 | Calendar/macro features | 20 | $0 | 10 days sprint | Q1.5 | No current dispatch |
| 4 | AI-grounding bundle | 16 | $0 | 4-6 weeks | Q2 | CEO decision pending on N62 |
| 5 | Decay observability (BOCPD+CUSUM) | 15 | $0 | 2-3 weeks | Q2 | S1 cron disabled |
| 6 | Asset-class specialists | 16 | $0 | 1 week NAS+US30; 4-6 weeks FX-3 | Q1.5-Q2 | NAS_US30 model exists |
| 7 | Methodology bundle | 12 | $0 | 2-3 days | Q1.5 | B-8 partial; B-6 tail pending |
| 8 | K54 v3 substrate-immune features | 12 | $0 | 2-4 weeks (after cohort expansion) | Q1.6+ | Conditional on cohort >5,000 |

**Aggregate substrate-immune research budget:** ~6-9 months of high-EV work at $0/mo subscription cost. Phase 2 priority should weight directions 1-4 (combined score ≥20 each).

**Critical observation:** None of the top-8 substrate-immune directions overlap with the substrate-blocked items (K-1..K-4 volume-bar, X-1..X-3 microstructure, H-19 multi-level OFI). The substrate gap does NOT remove any rank-1-3 direction from the program. **The Phase 2 plan is fully defensible without paid LOB feeds.**

---

## Decision matrix: free-feed integration sprint vs Databento

| Criterion | Free-feed sprint | Databento CME Standard |
|---|---|---|
| Cost (yearly) | $0 | $2,148 |
| Items unblocked | 19 substrate-immune (a-section + d-section macro) | 6 substrate-blocked (k-section + x-section micro) |
| Engineering effort | 10 days (one-off) | 0 days (subscription) |
| Per-item expected R-lift | $20-40/yr each | $30-50/yr each |
| Total expected R-lift | $400/yr | $200/yr |
| ROI 12-month | INF (zero cost) | -91% |
| CEO #1 concern (decay) attack | DIRECT (calendar/macro decay-resistant) | INDIRECT (substrate fix; mechanism preserved but decay-orthogonal) |
| Risk to existing program | None (additive only) | None (additive only) |
| Decision | **SHIP — high-EV substrate-immune** | **DEFER — re-evaluate at scale-up event** |

The choice between these two is not either/or; both could ship. But the free-feed sprint comes first because (a) zero cost, (b) higher expected R-lift in 12 months, (c) directly attacks decay-resistant macro mechanism, (d) no scale-up trigger required.

---

*Agent D, 2026-04-29. Companion to substrate audit. Read-only.*
