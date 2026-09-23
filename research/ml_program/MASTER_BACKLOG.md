# GTOS ML Research Program — MASTER BACKLOG

**Last updated:** 2026-05-01
**Status:** living document; every item has a status (PENDING / IN_FLIGHT / DONE / FAILED / BLOCKED).
**How to use:** CEO names an item ID (e.g. `M-12`); orchestrator dispatches the appropriate agent(s) on Opus 4.7 + max effort; result returns to this backlog with status update + outcome notes.

This is the **comprehensive pool** capturing everything the research surfaced. Phase 3 hypothesis-generation will produce a more polished ranked subset (`HYPOTHESIS_BACKLOG.md`); this doc ensures nothing is lost between the polished view and the raw evidence.

**Discipline gates** (apply across all items):

- Pre-registration in `PRE_REGISTERED_HYPOTHESES.md` for primary hypotheses.
- Paired-fixed-HP CPCV + DSR + effective-N + B=1000 null + cross-period robustness gate.
- CPCV-honest training-overlap-weighted SE (NOT Stouffer naive).
- Treat literature-derived predictions as upper bounds (50% realization in production is the planning baseline).
- Failure protocol: pass → ship; fail → KILLED memo + re-spec or close.

**Tier convention:**
- **T1** = cheap, high-EV, do this week
- **T2** = Q1.4 candidate (~1-2 weeks)
- **T3** = Q2-Q3 (~1-2 months)
- **T4** = Q4+ or research-only (deferred / pre-conditional)

---

## Section M — METHODOLOGY corrections (apply retroactively)

| ID | Tier | Status | Item |
|---|---|---|---|
| M-1 | T1 | DSR_VALIDATED | J46-J49 +0.742R/trade SURVIVES DSR at N=200. DSR-p=1.23e-7 (5.16σ post-deflation). Forward-citable. PBO not computable (per_fill.jsonl 121MB gitignored). Done 2026-04-29 (B-8). See `audit/dsr_retroactive_sweep.md`. |
| M-2 | T1 | DSR_FAILED | K54 v1 AUC 0.571 / +0.164R FAILS DSR at N=200 (DSR-p=0.965, PBO 0.467 borderline). Q1.4 gate (b) anchor revised to **CPCV-honest K54 v1 = 0.5286** per `audit/canonical_v1_rerun.md`. Done 2026-04-29 (B-8). |
| M-3 | T1 | DSR_VALIDATED | S79 +26.5pp P(pass FN) SURVIVES DSR (DSR-p<2.22e-16, machine zero). Forward-citable. PBO not computable on 1000-trial MC (no time axis). Done 2026-04-29 (B-8). |
| M-4 | T1 | DSR_FAILED | All XAUUSD/USDJPY/US30/GBPJPY WR claims, +0.200R expectancy, FVG-impulse, **+17pp OB-advantage relative claim** FAIL DSR. Mechanical OB cross-period 2022-2023 cohort survives SEPARATELY at z=10.5 — mechanism real, headline overfit. CLAUDE.md "Validated Numbers" table updated 2026-04-29. See `audit/dsr_retroactive_sweep.md` Section 7. |
| M-5 | T2 | BLOCKED | Resolve Inoue-Kilian 2005 + Diebold 2015 (IS-can-beat-OOS) vs Lopez de Prado AFML (CPCV-honest doctrine) per-instrument empirically. |
| M-6 | T2 | BLOCKED | Build Romano-Wolf StepM pipeline at α=0.05 over 47 instrument×side×regime cells (vs Bonferroni's ~3 expected rejections). |
| M-7 | T1 | DONE | Training-overlap-weighted SE is now implemented in `src/research_infra/methodology_gate.py` and audited across current primary methodology artifacts by `audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md`. K54 v2 Stouffer-era JSON remains archived and is explicitly blocked as promotion evidence; current/future reporting must use CPCV-honest SE rows. |
| M-8 | T1 | DONE | B=1000 null shuffles in K54 v2 modeler — already adopted post-Q1.3. |
| M-9 | T1 | DONE | PBO check — already in K54 v2 modeler (PBO 0.467 borderline). |
| M-10 | T2 | DONE | Hansen SPA test on K54-class lifts. |
| M-11 | T2 | DONE | Diebold-Mariano per-fold for paired AUC comparison. |
| M-12 | T2 | DONE | Effective-N and cumulative trial-budget helpers are implemented in `src/research_infra/methodology_gate.py`; `audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md` verifies future lift-claim rows must carry `effective_n_status` before promotion p-values are allowed. |
| M-13 | T2 | DONE | PBO guard is implemented as the hardened-claim gate in `src/research_infra/methodology_gate.py` and audited in `audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md`; current primary artifacts have PBO or are marked `not_computable`/blocked with zero promotion p-values allowed. |
| M-14 | T2 | DONE | Christoffersen interval-coverage test for any K54 v3 confidence-band feature. |
| M-15 | T2 | DONE | Bayesian-backtesting alternative methodology track (parallel to frequentist). |
| M-16 | T1 | DONE | Bias-variance bookkeeping closed by `audit/Q13_CPCV_BIAS_VARIANCE_BOOKKEEPING_2026-05-03.md`: Q1.3 fixed-HP CPCV +0.030896 lift is `VARIANCE_DOMINATED_NO_SIGNAL_CLAIM`; squared-mean signal share `13.1%`, path-variance share `86.9%`, CPCV-honest weighted 95% CI `[-0.096223, +0.158016]`. |
| M-17 | T1 | DONE | Phase 3 raw-OHLC PBO validation: CSCV orientation covered by synthetic winner/loser tests; raw follow-up now reports individual-child, family-vs-control, and blocked-control PBO variants. Diagnostic remains same-dataset only. See `research/phase_3_external_feed_validation/RAW_OHLC_PBO_VALIDATION_NOTE_2026-05-01.md`. |

## Section K — K54 v3 ARCHITECTURAL elements

| ID | Tier | Status | Item |
|---|---|---|---|
| K-1 | T2 | DEFERRED | Volume-bar resampling — BLOCKED by MT5 retail `volume=0` substrate. **Substituted by K-1' tick-count-time bars** (Glattfelder-Dupuis-Olsen 2011) in H-1 K54 v3 modeler 2026-04-29. Re-run trigger: paid LOB feed (Databento) OR ≥30d ticks across 7 instruments. See memory `project_mt5_retail_tick_lob_gap_2026-04-29`. |
| K-2 | T2 | DEFERRED | Dollar-bar resampling — same `volume=0` substrate gap as K-1. Same re-run trigger. |
| K-3 | T2 | DEFERRED | Imbalance-bar resampling — same `volume=0` substrate gap. Tick-direction tags via BVC-corrected (Andersen-Bondarenko 2014) require LOB depth GTOS doesn't have. Same re-run trigger. |
| K-4 | T1 | FAILED | Stoikov 2018 micro-price — KILLED 2026-04-29. NAS100 RMSE -2.47% / US30_cash -0.85% vs naive mid (BOTH WORSE). MT5 retail tick stream has `volume=0` and `last=0` on 100% of rows; flow-proxy substitution via `inferred_aggressor` is mechanical mid-momentum on Roll-bid-ask-bounce regime. Re-run only if paid LOB feed (Databento) sourced. Reference impl preserved. See KILLED_HYPOTHESES.md K-4/P-4 entry + memory `project_mt5_retail_tick_lob_gap_2026-04-29`. |
| K-5 | T2 | FAILED | Kyle-Obizhaeva 2016 W-unit normalization for pooled multi-instrument K54. Failed 2026-05-03 triage: W-unit ON AUC 0.510 vs OFF 0.564; MT5 retail/CFD substrate lacks the LOB/trade-volume mechanism. Reopen only with approved LOB/trade-volume substrate or new preregistered pooling transform. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-6 | T2 | FAILED | Pooled multi-instrument K54 training pipeline (uses K-5 normalization). Failed for current cohort: K54 v3 DSR-p 0.321 and K54 v4 all architectures failed. Reopen only after cohort expansion to n>=5000 with source-period flags and missing old labels resolved. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-7 | T2 | FAILED | Osler 2003 stop-cluster feature for FX K54. Failed for current cohort: K-7..K-10 additions contributed only about +0.0035 AUC over Arch A, below noise. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-8 | T2 | FAILED | Power-law-decayed OB-age weighting. Failed for current cohort: combined K-7..K-10 marginal lift was below noise. Reopen only with larger cohort or standalone preregistration. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-9 | T2 | FAILED | Regime x round_aligned x side interaction features. Failed for current cohort: below-noise contribution and global K54 family failed per-cohort floors. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-10 | T2 | FAILED | Above-up / below-down round-aligned OB direction feature (Bhattacharya 2012 / Zhang 2024). Failed for current cohort: marginal top-100 appearances did not produce decision-grade lift. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-11 | T2 | DONE | Per-fold top-100 feature screening (de Prado AFML §8.5; Architecture A from Q1.3 post-mortem). Research component ran in K54 v3/v4; current feature-stability gate failed, but no tooling blocker remains. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-12 | T2 | DEFERRED | **Meta-labeling head over Component 3A AI direction** (Lopez de Prado 2018; Hudson-Thames 2022). Ran in K54 v3 but was statistically weak at n=528 / about 250 primary-positive rows with no measurable lift. Trigger: n>5000 or new label-rich K55 shadow cohort. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-13 | T2 | DONE | Triple-barrier labeling (Lopez de Prado AFML). Research label component ran as the K54 v3 meta-labeling substrate; no tooling blocker remains. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-14 | T2 | DONE | Adaptive conformal calibration on K54 v3 outputs (90%-coverage prediction intervals). CPCV proxy ran: coverage 0.881 vs target 0.900, Christoffersen p 0.00158; true holdout remains a separate validation gate, not a tooling blocker. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-15 | T2 | DONE | TreeSHAP-stability pruning gate (only retain features stable across CPCV folds; addresses Jaccard 0.072 instability). Gate is implemented/reported; current K54 features failed stability (2 stable features, mean Jaccard 0.169), which is a result rather than a tooling blocker. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |
| K-16 | T3 | DEFERRED | Focal loss (γ=2, α=0.25) for trending_bull-LONG cells. Deferred 2026-05-03: no same-cohort K54 architecture iteration remains unblocked after K54 v3/v4 primary failure. Trigger: n>=5000 regime-balanced labels or new label-rich K55 shadow cohort plus preregistered focal-loss comparison. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| K-17 | T3 | DEFERRED | Hierarchical-Bayesian K54 pooling for data-poor instruments. Deferred 2026-05-03: pooled K54 v3/v4 failed global gates and data-poor instruments still need source-period flags plus missing old labels resolved. Trigger: source-balanced expanded cohort. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| K-18 | T2 | FAILED | **K54 v3 master bundle** = K-1 + K-4 + K-5 + K-6 + K-7 + K-8 + K-9 + K-10 + K-11 + K-12 + K-13 + K-14 + K-15. Failed globally: K54 v3 DSR-p 0.321 / feature stability failed, and K54 v4 fallback architectures also failed. NAS_US30 specialist remains K55-shadow discovery only. Reopen only after n>=5000 or alternate broker/provider pre-2024 GBPJPY+US30 coverage plus v2/v3 feature backfill. See `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`. |

## Section V — Component 3C VOL-CONDITIONING OVERLAY

| ID | Tier | Status | Item |
|---|---|---|---|
| V-1 | T1 | DONE | Realized-vol-percentile feature. Research-side vol-rank tooling exists in H-PM01/H-PM03/NA8; portfolio-wide H-PM01 failed, so Component 3C sizing integration remains separate P-1/V-9 work. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| V-2 | T1 | BLOCKED | Variance Risk Premium (VRP) feature. Blocked 2026-05-03: no local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists; VIXCLS/GVZCLS alone do not define VRP. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| V-3 | T1 | DONE | Regime-persistence feature. K54 regime feature family already contains run-length, flip-window, and score-dynamics persistence features; live Component 3C overlay remains separate. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| V-4 | T2 | DONE | Sigma multiplier function `[0.5, 2.0]` mapping. DONE 2026-05-03: H-PM01 implements `bsc_sigma_mult = clip(median_vol / realized_vol_30d, 0.5, 2.0)`. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| V-5 | T2 | FAILED | Backtest of Barroso-Santa-Clara 2015 vol-managed momentum on GTOS data. FAILED 2026-05-03 portfolio-wide in H-PM01: delta mean R=-0.004960547358764833, delta Sharpe=-2.5761764707408985%, DSR-p=0.9999646857030353. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| V-6 | T2 | FAILED | A/B test: vol-managed sizing vs current uniform 2%. FAILED 2026-05-03: H-PM01 is the A/B and rejects portfolio-wide vol-managed sizing vs uniform. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| V-7 | T2 | DONE | Daniel-Moskowitz 2016 LONG-sizing modifier integration with S79. DONE 2026-05-03: side-aware/Long modifier evidence is closed by H-PM03/combined MC; full P(bust HARD)=0.022. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| V-8 | T2 | FAILED | Moreira-Muir vol-scaling integration (15-25% Sharpe lift OOS in literature). FAILED 2026-05-03 as a broad all-symbol policy in H-PM01; NAS100-only remains shadow/deferred. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| V-9 | T2 | DEFERRED | **Component 3C bundle** = V-1+V-2+V-3+V-4+V-5+V-6. Deferred 2026-05-03: V-2 source is blocked, broad V-5/V-6 failed, and live insertion needs approval; only NAS100-only shadow/approval route remains open. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |

## Section A — ASSET-CLASS specialists

| ID | Tier | Status | Item |
|---|---|---|---|
| A-1 | T2 | DEFERRED | Gamma-sign feature for indices (Barbon-Buraschi 2021). Deferred 2026-05-03: local FlashAlpha GEX proxy has 15 rows but only forward/current snapshots; trigger: >=30 trading days of snapshots or legal historical CBOE/GEX data. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-2 | T2 | BLOCKED | VIX1D-VIX9D spread feature (gamma-sign proxy from MT5 + supplement). Blocked 2026-05-03: local external-feed inventory has VIXCLS/GVZCLS but no VIX1D or VIX9D cache/source. See `research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md`. |
| A-3 | T2 | BLOCKED | VRP delta feature (term-structure-based gamma proxy). Blocked 2026-05-03: no local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source. See `research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md`. |
| A-4 | T2 | BLOCKED | NAS_US30 specialist re-train with A-1+A-2+A-3 features. Blocked 2026-05-03: A-1 is forward-only and A-2/A-3 are blocked; same-cohort K54/K55 retraining remains closed until source-quality/cohort triggers. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-5 | T2 | BLOCKED | JPY-pair specialist (USDJPY + GBPJPY-JPY-leg) — Lustig-Roussanov-Verdelhan factor decomp + Aug-2024-carry-unwind features. Blocked 2026-05-03: no local Japan/UK rate-differential, carry-unwind, or BIS/Aquilina source cache. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-6 | T2 | BLOCKED | GBP-pair specialist (GBPUSD + GBPJPY-GBP-leg) — BoE policy + political risk features. Blocked 2026-05-03: no local BoE policy, GBP political-risk, or registered legal proxy feed exists. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-7 | T2 | BLOCKED | Dollar-pair specialist (USDJPY + GBPUSD) — Treasury-basis + Fed-funds + intermediary-capital features. Blocked 2026-05-03: FRED cache is partial but lacks Treasury-basis/intermediary-capital/Fed-funds feature contracts. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-8 | T1 | BLOCKED | Erb-Harvey 2024 real-gold-price percentile feature (anchors XAU H2-2026 LONG decay). Blocked 2026-05-03: local feeds have nominal XAUUSD bars plus FRED real-rate/inflation-expectation proxies, but no CPI/PCE deflator or registered real-gold-price percentile construction. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| A-9 | T2 | DONE | Gold COT positioning feature feed feasibility. DONE 2026-05-03: normalized CFTC XAUUSD COT cache exists with managed-money/commercial-style positioning fields. Alpha validation remains separate. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-10 | T3 | DONE | Gold central-bank-flow feature feed feasibility. DONE 2026-05-03: WGC demand/ETF plumbing exists with latest demand rows=9475 and central-bank-like rows=162; alpha validation remains separate. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| A-11 | T2 | DONE | LBMA fix anomaly feature feasibility. DONE 2026-05-03: normalized LBMA gold/silver fix-calendar cache exists; alpha validation remains separate. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-12 | T2 | BLOCKED | Krohn-Mueller-Whelan 2024 FX-fix W-shape feature (USD up before / down after). Blocked 2026-05-03: no KMW FX-fix source/cache exists locally. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-13 | T2 | BLOCKED | Brunnermeier-Nagel-Pedersen 2008 funding-liquidity (TED, VIX) feature for FX. Blocked 2026-05-03: VIX/yields exist, but TED/funding-liquidity/intermediary-capital source contract is incomplete. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-14 | T2 | BLOCKED | Aquilina et al. 2024 BIS JPY-carry-unwind regime classifier. Blocked 2026-05-03: no BIS JPY carry-unwind source/table/cache exists locally. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-15 | T3 | BLOCKED | He-Kelly-Manela 2017 intermediary-capital SDF as cross-instrument anchor. Blocked 2026-05-03: no H-K-M/intermediary-capital source, status file, normalized cache, or source spec exists locally. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| A-16 | T2 | FILED | Engle DCC / Aielli cDCC / Engle-Kelly Block-DECO replacing current `cross_instrument_correlation_gate.py` model. Filed 2026-05-03: live correlation-gate replacement would alter risk behavior and requires explicit CEO approval; research prototype can be scoped separately. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| A-17 | T3 | DONE | Patton 2006 + Christoffersen 2012 copula tail-dependence feature feasibility. DONE 2026-05-03: tail-dependence diagnostic ran on 13064 aligned M15 returns and 21 pairs; no live risk rule. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| A-18 | T3 | DONE | Forbes-Rigobon 2002 heteroskedasticity-corrected correlation diagnostic. DONE 2026-05-03: adjusted high-vol correlations are included in the Lane 6 tail diagnostic; no live risk rule. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |

## Section R — RISK POLICY upgrades

| ID | Tier | Status | Item |
|---|---|---|---|
| R-1 | T2 | DEFERRED | **Busseti-Boyd 2017 Risk-Constrained Kelly** replacing S79 uniform 2%. Deferred 2026-05-03: replacement needs preregistered simulation over DSR-surviving J46-J49/S79 baselines and CEO approval before risk behavior changes. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| R-2 | T2 | DEFERRED | Lambda-knob auto-calibration to FN constraint `P(MTM-DD ≥ 4%) ≤ 0.02`. Deferred 2026-05-03: depends on R-1 and owner-approved risk replacement path. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| R-3 | T3 | DEFERRED | Strub EVT-CDaR sizing implementation. Deferred 2026-05-03: needs preregistered simulation over DSR-surviving baselines and CEO approval before risk behavior changes. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| R-4 | T3 | DEFERRED | Smooth Grossman-Zhou drawdown control. Deferred 2026-05-03: needs simulation and owner approval; current H29 drawdown reducer remains the live safety path. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| R-5 | T2 | DEFERRED | Per-instrument optimal weights (vs uniform 2%). Deferred 2026-05-03: requires R-1 simulation path and source-flagged all-symbol cohort; do not override S79 uniform profile from current evidence. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| R-6 | T2 | DONE | Side-aware sizing (LONG=0.25 / SHORT=0.5-1.0) bundled with sharpe_weighted. DONE 2026-05-03: closed by H-PM03/combined MC and existing config flip; full P(bust HARD)=0.022. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| R-7 | T2 | FAILED | Vol-scaled sizing across all 7 instruments. FAILED 2026-05-03 portfolio-wide in H-PM01: delta mean R=-0.004960547358764833, DSR-p=0.9999646857030353; NAS100-only remains separate deferred/shadow candidate. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| R-8 | T2 | DONE | Walasek 2025 λ-context-dependence audit. DONE 2026-05-03 at control level: live risk assumptions are fixed-profile S79/side-aware scalars; any lambda-knob replacement is deferred under R-1/R-2. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| R-9 | T2 | DEFERRED | **Risk-policy bundle** = R-1 + R-2 + R-5 + R-6 + R-7 + V-8. Deferred 2026-05-03: depends on deferred R-1/R-2/R-5 and rejected R-7; cannot replace S79/full-stack from current evidence. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |

## Section E — EDGE-MECHANISM validation tests

| ID | Tier | Status | Item |
|---|---|---|---|
| E-1 | T1 | FAILED | Osler 2003 stop-cluster prediction on GTOS XAU+FX data: take-profits cluster AT round numbers (~10% at .00); stops cluster JUST BEYOND (asymmetric). Current K54 v3 Osler/K-7 round-level proxy was below-noise; production trade history records GTOS proposed levels, not counterparty stop clusters. Reopen only with direct stop-cluster/counterparty data or a feature-specific preregistered cohort. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| E-2 | T1 | DEFERRED | Toth-Bouchaud V-shaped latent liquidity test on tick data where coverage exists. Deferred 2026-05-03: current all-symbol MT5 tick coverage is short and quote-only; latent-liquidity shape needs mature tick/depth/order-flow evidence. Trigger: >=30 trading days all-symbol ticks or approved depth/order-flow feed plus preregistered V-shape estimator. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| E-3 | T2 | BLOCKED | Lillo-Mike-Farmer-Sato meta-order long-memory test on hourly aggregates. Blocked 2026-05-03: needs signed order-flow/meta-order aggregates; local OHLCV/H1 bars and MT5 tick volume are not a parent-order-flow substrate. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| E-4 | T1 | BLOCKED | F11 OB-zone decay regression vs retail-flow share over time (operationalizes AMH on existing data). Blocked 2026-05-03: no retail-flow-share proxy, broker client-sentiment cache, Google Trends cache, or social-flow dataset is available locally. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| E-5 | T2 | DONE | OB-precision feature uncorrelated-with-OB-precision discovery inventory. DONE 2026-05-03: current via NA-11 plus queue state; live candidates remain discovery/forward-shadow only. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |

## Section X — Reopened CLOSED tracks

| ID | Tier | Status | Item |
|---|---|---|---|
| X-1 | T2 | BLOCKED | E24/E26 microstructure re-test on volume-bar-sampled data. Blocked 2026-05-03: needs real trade volume or approved tick/depth feed; MT5 retail tick volume is not a volume-bar substrate. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| X-2 | T2 | BLOCKED | E24/E26 re-test on dollar-bar-sampled data. Blocked 2026-05-03: dollar bars need price x real traded volume; current MT5 feed lacks true centralized trade volume. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| X-3 | T2 | BLOCKED | E24/E26 re-test on imbalance-bar-sampled data. Blocked 2026-05-03: imbalance bars need signed trades or aggressor-side proxy; current local data is OHLCV/quote-tick only. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| X-4 | T3 | DEFERRED | Tick-level Hawkes process fitting for kill-zone gating. Deferred 2026-05-03: current tick capture is short and quote-only; trigger is >=30 trading days all-symbol ticks or approved signed order-flow/depth feed. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| X-5 | T2 | DONE | Hurst exponent intraday measurement across 7 instruments. DONE 2026-05-03 as rough-vol proxy diagnostic: median H=0.5050851741228051, range=[0.48422314477656087, 0.6033981383377698] on local M15 data. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| X-6 | T2 | DONE | K54 v1 published 0.571 vs CPCV-honest 0.512-0.529 reconciliation. DONE 2026-05-03: canonical v1 rerun/K1 follow-ups set the promotion anchor to CPCV-honest 0.5286, not the DSR-failing 0.571. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| X-7 | T3 | FILED | Cascade-prompt rebuild post-V4-shelf. Filed 2026-05-03: prompt rebuild would alter trading evaluation behavior and requires explicit CEO approval; recovered template remains archived. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |

## Section C — Cheap A/B TESTS on existing data

| ID | Tier | Status | Item |
|---|---|---|---|
| C-1 | T1 | FAILED | **Coval-Shumway 2005 second-half-of-session OB-retest A/B** — predicts second-half outperforms first-half. **2026-04-29: FAIL.** Aggregate Δ=+0.0605R (passes magnitude gate) but bootstrap p=0.422, DSR-p=1.0 (fails significance gates). Sign-count 3/4 groups positive (XAU+XAG, INDEX, USD_FX) — directional signal real but underpowered. NY KZ Δ=+0.184R p=0.090 borderline-suggestive. See `research/ml_program/experiments/c1_coval_shumway_second_half.md` + KILLED_HYPOTHESES.md. **Do NOT add `is_second_half_of_kz` as binary feature to K54 v3.** Follow-ups remain open: C-1b (NY-only at finer M15/M1 precision); C-1c / V-1 / H-E16 (high-RV-decile-conditioned variant — cleaner stress proxy than time-of-session). |
| C-2 | T1 | BLOCKED | Disposition-effect feature on counterparty stop placements (Odean 1998 + Shefrin-Statman 1985). Blocked 2026-05-03: GTOS does not observe counterparty stop placements, broker client positioning, or IG/OANDA-style client sentiment locally; production trade records contain our proposed levels only. See `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md`. |
| C-3 | T2 | BLOCKED | Walasek λ context-dependence on inverted-TP gate. Blocked 2026-05-03: inverted-TP correction log has 66 rows but lacks symbol/outcome/realized-R linkage. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| C-4 | T2 | DONE | Daniel-Moskowitz LONG-modifier sizing simulation on existing trades. DONE 2026-05-03: closed by H-PM03/combined MC; side_aware_everywhere H2 P(pass)=0.7806666666666666 and full P(bust HARD)=0.022. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| C-5 | T2 | DEFERRED | Lim-Zohren-Roberts Sharpe-objective training on existing K54 cohort. Deferred 2026-05-03: same-cohort K54/K55 training is closed after v3/v4 failures; reopen only with n>=5000 or source-quality/cohort-expansion trigger. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| C-6 | T2 | DEFERRED | Cartea-Jaimungal continuous-sized entries simulation. Deferred 2026-05-03: requires actual broker-R/fill truth, lifecycle telemetry, and live-risk approval. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| C-7 | T1 | DONE | Path-9 Feb-2026 window deep-dive completed 2026-05-03. Verdict: Feb-heavy, cross-cohort temporal-window signal, not a single-symbol artifact; replication scan shows fragility rather than stable all-window lift. See `research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md`. |
| C-8 | T2 | BLOCKED | Per-fold feature stability vs production deployment performance regression. Blocked 2026-05-03: feature-stability artifacts exist, but no K54 production deployment performance series exists because K54 is not deployed. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| C-9 | T1 | BLOCKED | Raw-OHLC architecture ablation and path-scaling exit study is partially complete but full comparison remains blocked. Completed: protocol, V0 base/J46/lock-only, V2 structural selector, V2b rolling status, V3 discovery replay. Blockers: deterministic L2 reconstruction, resolved V2b post-cutoff pairs, pending lifecycle + original POI/pre-fill fields for close-and-reenter accounting, and measured cost/slippage. See `research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md`. |

## Section D — DATA extraction needs

| ID | Tier | Status | Item |
|---|---|---|---|
| D-1 | T2 | DEFERRED | Tick re-bar-sampling infrastructure (volume / dollar / imbalance bars across all 7 instruments). Deferred 2026-05-03: tick capture exists for 7/7 symbols, but local history is only 5 days at best and MT5 retail volume/last fields are not a real volume/dollar substrate. Trigger: >=30 trading days of all-symbol ticks or approved paid LOB/trade feed. See `research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md`. |
| D-2 | T3 | BLOCKED | Pre-2024 tick data extraction (where broker permits). Blocked 2026-05-03: current MT5 tick probes/tick capture do not provide pre-2024 tick history; broker retention only covers recent windows. Trigger: alternate broker/provider/archive or paid historical tick/LOB source with pre-2024 coverage. See `research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md`. |
| D-3 | T2 | DONE | CBOE GEX feed integration (or proxy via VIX term-structure). FlashAlpha Basic single-expiry GEX proxy path is integrated and cached for QQQ/DIA/SPY/GLD/SLV; official CBOE aggregate/historical GEX remains separate blocked validation/source work. See `research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md`. |
| D-4 | T2 | BLOCKED | CFTC COT data fetcher (gold + FX positioning). Blocked 2026-05-03 as full item: CFTC fetcher and XAUUSD gold cache exist, but no local FX COT contract mappings/rows are present. See `research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md`. |
| D-5 | T2 | BLOCKED | LBMA fix + Krohn-Mueller-Whelan FX-fix data sources. Blocked 2026-05-03 as full item: LBMA gold/silver fix calendar exists, but no local KMW FX-fix source/cache is present. See `research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md`. |
| D-6 | T1 | DONE | NDX100 → NAS100 alias documentation across codebase. DONE 2026-05-03 as operations triage: `NAS100` remains canonical, `NDX100` is redacted_account broker alias, and `US100.cash` stays historical/demo extraction context. See `research/operations/weekend_backlog_ops_triage_2026-05-03.md`. Follow-up: centralize extraction alias hygiene only if a future code-change window is approved. |
| D-7 | T3 | BLOCKED | He-Kelly-Manela intermediary-capital SDF index access. Blocked 2026-05-03: no local H-K-M/intermediary-capital SDF source, status file, normalized cache, or registered source spec was found. Trigger: legal source/access path plus no-lookahead publication metadata. See `research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md`. |
| D-8 | T3 | BLOCKED | FRED / BIS macro feature feed (intermediary capital, funding liquidity). Blocked 2026-05-03 as full item: FRED macro cache exists, but no BIS source/cache/spec exists locally. Trigger: BIS source tables/cache/join with publication-time metadata. See `research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md`. |
| D-9 | T3 | BLOCKED | Federal Reserve research feed integration. Blocked 2026-05-03: no distinct Federal Reserve research-feed source contract, parser, status file, or normalized cache exists beyond FRED macro feed. Trigger: define intended source, fields, cadence, publication-time model, and parser/cache. See `research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md`. |
| D-10 | T3 | DONE | World Gold Council central-bank-flow feed. DONE 2026-05-03 as data plumbing: local WGC Gold Demand Trends and ETF imports exist, including central-bank/other-institution rows. Alpha validation and scheduled/operator refresh remain separate work. See `research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md`. |
| D-11 | T1 | DONE | 2022-2023 backfill data quality bias check (mechanical extraction vs live trades). DONE 2026-05-03. Verdict: `USABLE_WITH_DOWNSAMPLING_AND_SOURCE_FLAGS_NOT_LIVE_EQUIVALENT`; old labels are mechanical-discovery rows, not live-equivalent. Missing GBPJPY and US30_cash old labels were regenerated as a versioned supplement (`465` filled rows: GBPJPY `238`, US30_cash `227`) with source-period flags; do not overwrite/merge into canonical five-symbol cohort without explicit source flags. See `research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md` and `research/ml_program/audit/D11_MISSING_OLD_LABELS_REGENERATION_2026-05-03.md`. |
| D-12 | T2 | BLOCKED | Pre-2022 OHLCV extension (where broker has depth). Blocked 2026-05-03: current MT5 history probes show no full 2021 all-symbol M15 coverage; only XAGUSD has a small late-2021 slice. See `research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md`. |

## Section P — ARCHITECTURE / SYSTEM-FLOW additions

| ID | Tier | Status | Item |
|---|---|---|---|
| P-1 | T2 | DEFERRED | Component 3C Vol-Conditioning Overlay implementation (between 3A and Execution). Deferred 2026-05-03: portfolio-wide H-PM01 failed (delta mean R -0.0050, DSR-p ~1.0); NAS100-only subcandidate remains shadow/approval work only (delta R +0.0907, DSR-p 0.0152). Reopen with CEO approval for NAS100-only shadow A/B or a fresh preregistration that clears portfolio-wide gates. See `research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md`. |
| P-2 | T2 | DEFERRED | Component 3D Meta-labeling head module. Deferred 2026-05-03 with K-12: K54 v3 meta-labeling ran but was statistically weak at n=528 / about 250 primary-positive rows. Trigger: n>5000 or new label-rich K55 shadow cohort plus CEO approval for live system-flow wiring. See `research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md`. |
| P-3 | T2 | DEFERRED | Adaptive conformal calibration module (90%-coverage). Deferred 2026-05-03: K54 global candidates failed, conformal has only a CPCV proxy (coverage 0.881 vs 0.900, Christoffersen p 0.00158), and no approved live/holdout candidate is ready for system-flow calibration. See `research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md`. |
| P-4 | T1 | FAILED | Stoikov micro-price in `tick_features.py` — KILLED 2026-04-29 by K-4/P-4 dispatch (B-8). MT5 retail tick has `volume=0` + `last=0` on 100% of rows; flow-proxy substitution failed RMSE benchmark (NAS100 -2.47%, US30 -0.85% vs naive midprice). Reference impl preserved at `research/ml_program/experiments/k4_stoikov_micro_price.py` (paper-faithful, 12/12 unit tests pass). Re-run trigger: paid LOB feed (Databento) OR coverage extends to all 7 instruments. See `KILLED_HYPOTHESES.md` K-4/P-4 + memory `project_mt5_retail_tick_lob_gap_2026-04-29`. |
| P-5 | T2 | FAILED | Pooled multi-instrument training pipeline (uses K-5/K-6). Failed 2026-05-03 by inheritance from K-5/K-6: W-unit pooling failed on current substrate and pooled K54 v3/v4 training failed global gates. Reopen only after usable LOB/trade-volume substrate or n>=5000 source-flagged cohort exists. See `research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md`. |
| P-6 | T2 | DEFERRED | Per-instrument-group routing layer at inference. Deferred 2026-05-03: K54 v4 T7-NAS routing add was negative (-0.0052 per path), gate_h failed, and all K54 v4 architectures failed. Reopen after K55-shadow specialist evidence clears sample, stability, and approval gates. See `research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md`. |
| P-7 | T3 | DEFERRED | Hawkes-process-based heartbeat/drawdown re-thresholds. Deferred 2026-05-03: safety/risk-threshold work needs >=30 trading days of tick/depth data and separate CEO approval before any live threshold change. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| P-8 | T3 | DEFERRED | Sticky HDP-HMM regime classifier (replaces v1+v2 H4-swing) with Kirby null-test. Deferred 2026-05-03: literature prior exists but no local HDP-HMM/Kirby-null harness has passed; runtime replacement requires approval. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| P-9 | T3 | DEFERRED | Trade-count-time triggers in Component 1 data ingestion + tick daemon. Deferred 2026-05-03: depends on D-1 tick-count-time substrate maturity and would alter Component 1/tick-daemon runtime behavior. Trigger: >=30 trading days all-symbol ticks or approved feed, then research-only validation before live hook. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| P-10 | T3 | DEFERRED | Signature features + fractional differentiation + HAR-RV cascade in K54 features. Deferred 2026-05-03: literature-prior feature family, but same-cohort K54 feature iteration is closed after v3/v4 failure. Trigger: source flags/missing old labels fixed and n>=5000 or new label-rich shadow cohort. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |

## Section L — LLM/AI improvements

| ID | Tier | Status | Item |
|---|---|---|---|
| L-1 | T2 | FILED | QuantMCP-style tool-use grounding for Component 3A. Filed 2026-05-03: ai_tools scaffolding/design exist but PrimaryAnalyzer is not wired; live Component 3A behavior changes require CEO approval and shadow-only design refresh. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| L-2 | T2 | FILED | FinAgent-style tool inventory for market-state queries. Filed 2026-05-03: current ai_tools registry exists, but live tool inventory wiring would alter Component 3A behavior and needs approval. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| L-3 | T3 | FILED | Reflexion-style post-trade reflection loop. Filed 2026-05-03: AdaptiveReview exists, but Reflexion-style post-trade feedback would alter AI/adaptation behavior and requires CEO approval plus a shadow-only design. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| L-4 | T2 | FILED | Bull/Bear/Judge debate framework activation. Filed 2026-05-03: debate code/tests exist but orchestrator does not import debate; activation changes AI flow/token spend and needs CEO DELETE/WIRE/LEAVE decision. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| L-5 | T3 | DEFERRED | Y. Li 2023 ICAIF hybrid (LLM + traditional ML) architecture path. Deferred 2026-05-03: depends on a surviving K55/K54 shadow candidate and approval for system-flow changes; current K54 global architectures failed. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| L-6 | T1 | DESIGN_DONE | HALLUC-2 token-usage logger — design + reference impl complete 2026-04-29 (B-8). NOT shipped. ~12 LOC integration in `src/components/primary_analyzer.py`. 12/12 unit tests pass. Integration ticket filed at `research/operations/l6_l7_integration_ticket_2026-04-29.md` for main-thread handoff. |
| L-7 | T1 | SHIPPED + EXT_DESIGN | Q71 slippage logger — entry-side **ALREADY SHIPPED** in production (`src/components/slippage_shadow_logger.py`, commit `6b049ab`, wired at `src/components/execution.py:502`). 1-row jsonl is real (limit-fill rarity in April). Close-side extension design complete 2026-04-29 (B-8) — `record_close_slippage` API + 9 close-side fields + `event` discriminator. ~50-60 LOC integration across slippage_shadow_logger.py + execution.py. 11/11 unit tests pass; backward-compat verified. Integration ticket: `research/operations/l6_l7_integration_ticket_2026-04-29.md`. See memory `project_l7_already_shipped_l6_still_gap_2026-04-29`. |
| L-8 | T2 | DEFERRED | LLM transfer test: does QuantMCP/FinAgent grounding work for Sonnet-class? Deferred 2026-05-03: depends on L-1/L-2 shadow grounding implementation and approval path. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |

## Section S — K55 ML-vs-AI SHADOW HARNESS

| ID | Tier | Status | Item |
|---|---|---|---|
| S-1 | T3 | FILED | K55 shadow harness design (read-only ML inference parallel to AI). Filed 2026-05-03 as design/approval work: existing K55 ticket needs target refresh after K54 v4 failed and implementation would touch orchestrator/config live paths. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| S-2 | T3 | DEFERRED | Per-instrument-group ML routing in shadow mode. Deferred 2026-05-03: K54 v4 T7-NAS routing add was negative; reopen after K55-shadow specialist evidence clears sample, stability, and approval gates. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| S-3 | T3 | DEFERRED | K55 30-day shadow evaluation (Q4 spec). Deferred 2026-05-03: no K55 shadow logger/output exists; trigger after S-1 implementation/smoke test and >=30 days or n>=50 K55-shadow events. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| S-4 | T3 | DEFERRED | Hybrid ML+AI ensemble vs pure-AI baseline measurement. Deferred 2026-05-03: no paired live AI+ML shadow dataset exists; trigger after S-3 produces paired AI decision, K55 decision, and realized-R rows at preregistered sample floors. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |
| S-5 | T4 | DEFERRED | K55 production gate flip (only after shadow correlation ≥1.2× AI per Q4 spec). Deferred 2026-05-03: requires successful S-3/S-4 shadow evaluation, promotion dossier, and explicit CEO approval. See `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md`. |

## Section Q — Q2 SEQUENCE MODEL preparation

| ID | Tier | Status | Item |
|---|---|---|---|
| Q-1 | T2 | DONE-FAIL | **DLinear baseline gate** — must clear K54 v1 ±0.01 AUC before any deeper architecture ships. Occam discipline. **VERDICT FAIL** (2026-04-28; CPCV mean AUC 0.5049 vs anchor 0.5286, Δ=−0.0237; DSR p=1.0, PBO=0.795, B=1000 null p=0.962, cross-period AUC=0.499). Q2 sequence-model exploration (Q-2 — Q-7) NO-GO. K54 v3 (H-1, K-18) only ML path. See `research/ml_program/experiments/q1_dlinear_baseline.md`. |
| Q-2 | T3 | DEFERRED | Time-LLM — SHELVED 2026-04-29 by Q-1 DLinear NO-GO. Re-run trigger: cohort expansion to n≥5,000 with regime-balanced labels (~4-6 quarters out at current cadence). |
| Q-3 | T3 | DEFERRED | Chronos foundation model — SHELVED 2026-04-29 (Q-1 NO-GO). Same re-run trigger. |
| Q-4 | T3 | DEFERRED | iTransformer — SHELVED 2026-04-29 (Q-1 NO-GO). Same trigger. |
| Q-5 | T3 | DEFERRED | PatchTST — SHELVED 2026-04-29 (Q-1 NO-GO). Same trigger. |
| Q-6 | T3 | DEFERRED | TCN — SHELVED 2026-04-29 (Q-1 NO-GO). Same trigger. |
| Q-7 | T3 | DEFERRED | LSTM baseline — SHELVED 2026-04-29 (Q-1 NO-GO). Same trigger. |
| Q-8 | T3 | DEFERRED | Sequence model architecture decision — auto-DEFERRED until Q-1 re-runs cleanly at n≥5,000. |
| Q-9 | T3 | DEFERRED | Chen-Pelger-Zhu 2024 RNN macro-encoder — SHELVED 2026-04-29 (Q-1 NO-GO). Same trigger. See memory `project_q1_dlinear_q2_nogo_2026-04-29`. |

## Section Z — QUANTUM / long-horizon research

| ID | Tier | Status | Item |
|---|---|---|---|
| Z-1 | T4 | DEFERRED | Orus-Mugel-Lizaso 2019 quantum finance deep-dive. Deferred 2026-05-03: no current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| Z-2 | T4 | DEFERRED | Quantum Monte Carlo for derivatives evaluation. Deferred 2026-05-03: no current GTOS derivatives-evaluation bottleneck or quantum runtime path exists. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| Z-3 | T4 | DEFERRED | Quantum RL trading agents review. Deferred 2026-05-03: no current GTOS RL/quantum runtime path exists, and live-learning changes would require separate approval. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| Z-4 | T4 | DEFERRED | IBM Q-finance / Goldman quantum-derivatives literature follow. Deferred 2026-05-03: no current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |

## Section O — OPERATIONAL OPS / production tickets

| ID | Tier | Status | Item |
|---|---|---|---|
| O-1 | T1 | FILED | `_trade_index.json` frozen/stale fix. Original ticket at `research/operations/trade_index_frozen_bug_2026-04-28.md`; refreshed 2026-05-03 triage shows index has 129 batch-session trades with latest trade date `2026-03-13`, while `trade_records` has 263 records through `2026-05-01`. Implementation/verifier still pending; do not use `_trade_index.json` for current live/OOS counts until rebuilt or replaced. See `research/operations/weekend_backlog_ops_triage_2026-05-03.md`. |
| O-2 | T1 | DONE | NDX100 vs NAS100 alias documentation. DONE 2026-05-03 as operations triage; `NAS100` remains canonical and `NDX100` is redacted_account broker alias. Out-of-scope for ML program. See `research/operations/weekend_backlog_ops_triage_2026-05-03.md`. |
| O-3 | T1 | BLOCKED | Heartbeat-flatten kill-switch "Wake the computer" Task Scheduler operator action. Repo-side triage 2026-05-03 confirms this is operator-only: CEO/operator must enable the Windows scheduled-task wake setting and verify the next active kill-zone wake cycle. See `research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md`. |
| O-4 | DONE | DONE | Windows OS canary fanout fix (commit a44f39d session 43). |
| O-5 | T1 | BLOCKED | Disk cleanup + pagefile raise remains operator/admin maintenance outside repo research tooling. CEO/operator must perform or approve Windows disk cleanup/pagefile change and rerun ops checks. See `research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md`. |
| O-6 | T1 | DESIGN_DONE_PENDING_INTEGRATION | HALLUC-2 token-usage logger — design + reference impl complete 2026-04-29 (B-8 L-6 dispatch). Integration ticket: `research/operations/l6_l7_integration_ticket_2026-04-29.md`. ~12 LOC main-thread integration. |
| O-7 | T1 | SHIPPED + EXT_PENDING | Q71 slippage logger — entry-side **ALREADY SHIPPED** (`src/components/slippage_shadow_logger.py`, commit `6b049ab`). Close-side extension design complete 2026-04-29 (B-8 L-7 dispatch); ~50-60 LOC integration. Ticket: `research/operations/l6_l7_integration_ticket_2026-04-29.md`. |
| O-8 | T2 | FILED | live_evaluations + trade_records enrichment gap audit filed 2026-05-03. Current local counts: 89 live-evaluation files / 1647 rows through `2026-05-01`; 263 trade records through `2026-05-01`, all `execution: null`. Lifecycle-aware completeness verifier remains a follow-up; do not backfill actual R from research OHLC path touches. See `research/operations/weekend_backlog_ops_triage_2026-05-03.md`. |

## Section U — Open RESEARCH QUESTIONS (need more agents)

| ID | Tier | Status | Item |
|---|---|---|---|
| U-1 | T2 | BLOCKED | Inoue-Kilian vs CPCV-honest doctrine resolution per-instrument. Blocked 2026-05-03: same blocker as M-5; needs full 2022-2023 v2/v3 feature catalog plus source-flagged supplemental old-label integration. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-2 | T2 | BLOCKED | Gamma-sign feature constructibility from MT5 alone. Blocked 2026-05-03: MT5 alone has no option dealer gamma sign, VIX1D/VIX9D, VRP, or official GEX source; FlashAlpha Basic is only a proxy path. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-3 | T2 | DONE_NULL | Stoikov micro-price benefit at M15 — ANSWERED 2026-04-29: null on retail substrate. M15-aggregated form delta -0.0003% (NAS100) / -0.010% (US30) vs naive midprice; per-tick form -2.47% / -0.85%. The substrate (`volume=0` 100% rows on MT5 retail) prevents the published mechanism from transmitting at any timescale. See K-4/P-4 KILL + memory `project_mt5_retail_tick_lob_gap_2026-04-29`. |
| U-4 | T2 | DONE | Pooled multi-instrument benefit per-instrument sweep. DONE 2026-05-03: K54 v3/v4 triage answers it; global K54 failed and the strongest remaining group is NAS_US30 specialist discovery, not promotion. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-5 | T2 | DONE | DSR retroactive — ANSWERED 2026-04-29 (B-8 M-1+M-2+M-3+M-4 sweep). At N=200 trial budget: only **J46-J49** (DSR-p=1.23e-7) and **S79** (DSR-p<2.22e-16) survive. K54 v1 0.571 / XAUUSD WR 62% / USDJPY 75.8% / US30 58.5% / GBPJPY 57.1% / +0.200R / FVG-impulse / +17pp OB-advantage relative claim — all FAIL DSR. Mechanical OB cross-period 2022-2023 cohort survives SEPARATELY at z=10.5 (mechanism real, headline overfit). CLAUDE.md "Validated Numbers" updated 2026-04-29. See `audit/dsr_retroactive_sweep.md` + memory `project_dsr_retroactive_sweep_2026-04-29`. |
| U-6 | T2 | BLOCKED | Trade-count-time bars feasibility per broker depth. Blocked 2026-05-03: current broker substrate has retail quote ticks, not centralized trade prints or true depth; do not relabel quote-tick count as trade-count time. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-7 | T2 | ANSWERED_BY_NA8 | Component 3C Vol-Conditioning realization — partially ANSWERED 2026-04-29 (NA8 dispatch). On the canonical A6 H1→H2 XAU LONG cohort: vol-managed (Barroso-Santa-Clara) recovery estimate is **-1.0% (point)** with 95% CI [-48.5%, +21.7%] — NEGATIVE because H2 vol_rank 0.67 < H1 0.77 (multiplier amplifies losing trades). Recovery target ≥20% firmly rejected. **H-2 Component 3C deferred to Phase 5** as multiplicative sizing-overlay-on-K54. Generalization to other cohorts may differ (FA-2 caveat: refresh trigger n≥20 post-FA-2). See memory `project_na8_babu_decomposition_2026-04-29`. |
| U-8 | T3 | BLOCKED | He-Kelly-Manela SDF data availability check. Blocked 2026-05-03: no H-K-M/intermediary-capital source, cache, or source contract exists locally. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-9 | T2 | DONE | Walasek context-dependence — which other GTOS gates assume λ=2? DONE 2026-05-03: live config/code scan found 0 literal lambda=2 hits; relevant risk/ratio knobs are config-driven. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-10 | T3 | DEFERRED | LLM tool-use grounding transfer (Claude Sonnet vs GPT-4-class). Deferred 2026-05-03: depends on L-1/L-2 tool-use grounding shadow implementation and approval path. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-11 | T1 | DONE | 2022-2023 backfill data quality bias check (mechanical extraction vs live). ANSWERED 2026-05-03 by D-11 audit: old backfill is usable as mechanical discovery with source flags/downsampling, not live-equivalent; GBPJPY and US30_cash old mechanical labels are missing despite OHLC coverage. See `research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md`. |
| U-12 | T2 | BLOCKED | F2/F15 LONG decay attribution under Erb-Harvey lens. Blocked 2026-05-03: same blocker as A-8; no local CPI/PCE-deflated real-gold-price percentile construction exists. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-13 | T3 | DEFERRED | Per-instrument capacity-decay limits (Naik-Ramadorai-Stromqvist relevance). Deferred 2026-05-03: needs AUM/capacity trigger plus venue-volume or slippage/capacity data by instrument. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-14 | T3 | DEFERRED | McLean-Pontiff publication-decay rate validation on GTOS edge. Deferred 2026-05-03: needs longer live history or a clean publication/crowding proxy panel; current OB-decay monitor is sample-limited. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-15 | T3 | DEFERRED | Renaissance Medallion edge-aggregation mechanism deep-dive (Zuckerman 2019). Deferred 2026-05-03: requires dedicated literature/book synthesis and translation into substrate-immune candidate specs. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-16 | T3 | DEFERRED | Kirby null-test calibration for HDP-HMM regime classifier (P-8). Deferred 2026-05-03: depends on standalone sticky-HDP-HMM plus Kirby fat-tailed-mixture null-test harness; no local harness has passed. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| U-17 | T2 | DONE | Path-9 anomaly investigation: Feb-2026 window's specific market conditions. DONE 2026-05-03: Path-9 is Feb-heavy and cross-cohort, not single-symbol; fold 4 turns negative after the window and cached FRED shows elevated gold volatility. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |

## Section R-Recurring — RECURRING program tasks

| ID | Tier | Status | Item |
|---|---|---|---|
| RR-1 | T2 | DEFERRED | Quarterly literature refresh (last-6-months papers across 22 domains). Deferred 2026-05-03: requires a dedicated current-web literature sweep and source-citation pass outside local evidence triage; existing local corpus remains usable. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| RR-2 | T2 | DONE | Monthly DSR + effective-N tracker update. DONE 2026-05-03: current snapshot has 15 DSR rows, verdict counts, and promotion-p-value allowed count 0. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| RR-3 | T2 | DONE | Weekly McLean-Pontiff baseline alarm (5%/year decay threshold). DONE 2026-05-03 for the current local update: OB continuation latest date 2026-05-01 has 0 alarms, and monthly decay report exists. Recurrence remains process work. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| RR-4 | T2 | DEFERRED | After every experiment FAILS — refresh hypothesis backlog from new literature. Deferred 2026-05-03: requires the same dedicated current-web literature sweep deferred under RR-1. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| RR-5 | T3 | DEFERRED | Capacity-decay band re-evaluation as AUM grows (Naik-Ramadorai-Stromqvist). Deferred 2026-05-03: current live prop-account scale does not trigger capacity analysis; needs AUM/capacity growth or venue-volume participation data. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| RR-6 | T3 | DEFERRED | Hypothesis-portfolio diversification metric (correlation between active edges). Deferred 2026-05-03: needs separately logged live edge return streams before an edge-correlation/diversification metric is meaningful. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |
| RR-7 | T2 | DEFERRED | After every domain paper expires or is retracted, backlog audit. Deferred 2026-05-03: requires a current-web paper status/retraction watcher with source citations. See `research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md`. |

## Section B — ARCHITECTURAL COMPOSITES (multi-hypothesis bundles)

These are pre-bundled deployable units. Each combines multiple individual items into a single dispatch.

| ID | Tier | Status | Bundle |
|---|---|---|---|
| B-1 | T2 | FAILED | **K54 v3 master bundle FAILED 2026-04-29** — 1/6 testable gates PASS. Same DSR-ceiling fate as K54 v2: AUC 0.5770 + lift +0.048 + PBO 0.20 + null p=0 ✓ but DSR-p=0.321 at N=200 (paired SR 1.27 vs ceiling 1.11) ✗. K-7..K-10 contribute +0.0035 (below noise); Kyle-Obizhaeva W-unit pooling failed (LOB-substrate gap). **NAS_US30 specialist (Architecture B) survives**: AUC 0.6014, delta +0.103 — recommended K55-shadow deploy. Cohort expansion (n≥5,000) is the only Q1.5 path. Q1 CLOSE recommended. See `audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` + memory `project_k54_v3_failed_q1_close_2026-04-29`. |
| B-2 | T2 | DEFERRED | **Component 3C Vol-Conditioning bundle** (=V-9). Deferred 2026-05-03: portfolio-wide vol conditioning failed; NAS100-only subcandidate needs shadow/approval trigger before Component 3C work. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| B-3 | T2 | DEFERRED | **Risk-policy bundle** (=R-9). Deferred 2026-05-03: risk-policy replacement must be simulated over DSR-surviving J46-J49/S79 baselines and needs live-risk approval. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| B-4 | T2 | BLOCKED | **Asset-class-specialist bundle** = A-1+A-2+A-3+A-4+A-5+A-6+A-7+A-8+A-11. Blocked 2026-05-03: most constituent specialist features are blocked/deferred; A-9/A-11 are feed-feasibility only. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| B-5 | T3 | FILED | **AI-grounding bundle** = L-1+L-2+L-4+L-6+L-7+L-8. Filed 2026-05-03: constituent Component 3A/3B behavior changes need CEO approval and refreshed shadow-only design. See `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md`. |
| B-6 | T1 | COMPLETED | **Methodology-discipline bundle** — M-1/M-3 DSR_VALIDATED, M-2/M-4 DSR_FAILED, M-8/M-9 DONE, and M-7/M-12/M-13 closed by `src/research_infra/methodology_gate.py` + `audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md`. Current primary methodology artifacts checked: K54 v2 historical archived, K54 v3, K54 v4, Q1 DLinear, and Phase 3 diagnostics. Promotion p-values allowed: 0. Updated 2026-05-03. |
| B-7 | T2 | BLOCKED | **Edge-mechanism validation bundle** = E-1+E-2+E-3+E-4. Blocked 2026-05-03: E-1 failed, E-2 deferred, E-3 blocked, and E-4 blocked; no bundle-level validation can proceed. See `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md`. |
| B-8 | T1 | COMPLETED | **Quick-win bundle dispatched + closed 2026-04-29.** M-1 DSR_VALIDATED + M-3 DSR_VALIDATED, M-2/M-4 DSR_FAILED → CLAUDE.md "Validated Numbers" obsoleted; C-1 KILLED (no `is_second_half_of_kz` feature); K-4/P-4 KILLED (MT5 retail volume=0 substrate gap); Q-1 NO-GO → Q-2..Q-9 SHELVED until cohort n≥5,000; L-6 DESIGN_DONE, L-7 SHIPPED + EXT_DESIGN; NA8 H-1-first verdict. Q1.4 spec locked, H-1 modeler dispatched. See `dispatch_log.md` 2026-04-29 entries + 5 saved memories. |

---

## Item-count summary

| Section | Count |
|---|---:|
| M (Methodology) | 17 |
| K (K54 v3 architecture) | 18 |
| V (Vol-conditioning) | 9 |
| A (Asset specialists) | 18 |
| R (Risk policy) | 9 |
| E (Edge-mechanism) | 5 |
| X (Reopened tracks) | 7 |
| C (Cheap A/B tests) | 9 |
| D (Data extraction) | 12 |
| P (Architecture/system-flow) | 10 |
| L (LLM/AI) | 8 |
| S (K55 shadow harness) | 5 |
| Q (Q2 sequence model) | 9 |
| Z (Quantum) | 4 |
| O (Operational ops) | 8 |
| U (Open research questions) | 17 |
| RR (Recurring) | 7 |
| B (Composite bundles) | 8 |
| **Total** | **180** |

---

## Phase 4 in-flight items (live snapshot, 2026-04-29)

The following items are IN_FLIGHT as part of the **B-8 Quick-Win Bundle** dispatch (Phase 4 Day-1, Opus 4.7 max effort, subscription-only, READ-ONLY):

- **M-1, M-2, M-3, M-4** — DSR retroactive sweep (single agent; bundles methodology audit)
- **C-1** — Coval-Shumway second-half-of-session A/B
- **K-4, P-4** — Stoikov micro-price reference impl + drop-in spec (single agent)
- **Q-1** — DLinear baseline gate before Q2 sequence-model exploration
- **L-6, L-7** — HALLUC-2 + Q71 logger DESIGN (single agent; design-only, no src/ changes)

Plus **NA8** (Babu-Hoffman-Levine 2020 decomposition) — gates Q1.4 priority order between H-1 (K54 v3) and H-2 (Vol-Conditioning); not in original master backlog (surfaces from HYPOTHESIS_BACKLOG.md §7), surface as new methodology task on completion.

These items move to DONE/FAILED via orchestrator follow-up commits as agents return (~3-4 hours wallclock parallel).

---

## Dispatch protocol

When CEO names an ID:

1. Orchestrator looks up the item in this backlog.
2. If item is **single-action** (e.g. M-1 DSR retroactive), dispatch one Opus 4.7 max-effort agent with a focused prompt.
3. If item is a **bundle** (B-1, etc.), dispatch the constituent items in parallel where independent, sequential where dependent.
4. If item is a **research question** (U-N), dispatch a research agent with WebSearch + GTOS-data-read access.
5. Status field updated as items move through PENDING → IN_FLIGHT → DONE / FAILED.
6. Outcome notes appended (per-item) so future sessions can read what was learned.

**Default execution discipline:**

- Subscription-bounded throughout (no Anthropic API spend on research/data).
- Pre-registration in `PRE_REGISTERED_HYPOTHESES.md` for primary hypotheses.
- Paired-fixed-HP CPCV + DSR + effective-N + B=1000 null + cross-period robustness gate per Q1.3 post-mortem methodology.
- CPCV-honest training-overlap-weighted SE.
- Failure protocol: pass → ship; fail → KILLED memo + re-spec or close.

**Phase 3 hypothesis-generation (currently running)** will produce a more polished ranked subset (`HYPOTHESIS_BACKLOG.md`); items there will reference back to this master backlog by ID.

---

*Master backlog maintained by ML Program Orchestrator. All items derived from Phase 2 syntheses + Q1.3 post-mortem + AMBIGUITIES doc + 5 audits + 22 literature domains. Last refreshed: 2026-04-29.*
