# Group A Synthesis — Foundations + Methodology

**Synthesis agent:** Phase 2 Group A — Foundations + Methodology
**Date:** 2026-04-28
**Inputs consumed:** Domains 01 (Math Foundations), 02 (Statistical Methodology), 03 (Distributional Characteristics), 04 (Multitimeframe/Fractal/Wavelets), 05 (Change-Point/Regime-Switching)
**Method:** Read all 5 domain `papers.md` files in full; cross-reference paper IDs and the Section 6 / 7 summaries; identify cross-cutting findings and contradictions; rank GTOS hypotheses by impact x feasibility.

---

## Section 1 — Group A scope + paper totals

| Domain | Papers cataloged | Worker top-1 surprise |
|--------|------------------|----------------------|
| 01 Math Foundations | 42 | Ane-Geman 2000 transaction-count time recovers Gaussianity (challenges M15 wallclock triggers) |
| 02 Statistical Methodology | 70 | Diebold 2015 retrospective: pseudo-OOS is NOT inherently superior to IS — full-sample with proper SE often beats it |
| 03 Distributional Characteristics | 50 | MITRE 2023 finds 3/11 Cont stylized facts weakened in modern HFT-era markets (resolution-dependence) |
| 04 Multitimeframe / Fractal / Wavelets | 38 | Mensi et al. 2025 — gold has SHORT memory while equities/oil have long memory (contrary to gold-as-hedge framing) |
| 05 Change-Point / Regime-Switching | 75 | Kirby 2023 — observed bull/bear MS parameters may be statistical artifacts of fat-tailed mixtures, NOT evidence of regimes |
| **Group A total** | **275 papers** | |

**Coverage note.** Group A is the methodology-rich group: it owns the inferential machinery (multiple-testing, CV, sequential testing, structural-break inference), the distributional null models (Levy, jump-diffusion, EVT, GARCH, multifractal, rough vol), the time-scale decomposition tools (wavelets, HAR-RV, MIDAS, fractional differentiation), and the regime-detection / change-point methods (CUSUM, BOCPD, sticky-HDP-HMM, Bai-Perron). Heavy overlap with K54/K55 architecture decisions and the Phase-1 unresolved item #4 (regime-conditioned LONG-side decay).

---

## Section 2 — Cross-cutting findings (where >=2 domains converge)

The following 12 findings appear in at least 2 of the 5 domains and form the load-bearing synthesis hypotheses. Each is annotated with the domains it surfaced in.

### CC1 — Volatility is rough (H ~ 0.1) at intraday scales, with microstructural Hawkes-process foundations
**Domains:** 01 (Gatheral-Jaisson-Rosenbaum 2018, Bayer-Friz-Gatheral 2016, El Euch-Rosenbaum 2019), 03 (03-022 Bayer-Friz-Gatheral, 03-023 El Euch-Fukasawa-Rosenbaum), 04 (#19 Pricing under rough volatility), 16 (cross-link).

Log-realized-variance is *rougher* than Brownian motion (H ~ 0.1) at SPX, FX, commodity scales. Microstructurally, this is the scaling limit of nearly-unstable Hawkes processes (El Euch-Rosenbaum 2019), implying tick-arrival self-excitation IS the empirical mechanism behind rough vol. **GTOS implication:** the H25 session-volatility shadow logger and any forward-vol-aware kill-zone gating must use rough-fBM-aware forecasts at H ~ 0.1, not classical SV (Heston / Bergomi) half-lives. Anti-persistence at fine scales means session-vol mean-reverts faster than ATR-based heuristics anticipate.

### CC2 — Trading-time / transaction-count time is the operational clock; wallclock M15 is fighting the operational clock
**Domains:** 01 (Clark 1973 mixture-of-distributions; Ane-Geman 2000 transaction-count time recovers near-Gaussianity), 03 (subordination references), 04 (#37 Glattfelder-Dupuis-Olsen 12 empirical scaling laws — event-based/directional-change clocks; #16 Mandelbrot-Calvet-Fisher multifractal time), 06 (cross-link).

Subordination (Clark 1973) and the Ane-Geman 2000 finding that *transaction-count time* recovers Gaussianity — confirmed at FX scales by Glattfelder-Dupuis-Olsen 2011 — together imply that GTOS's M15 wallclock candle is implicitly fighting the operational clock. The currently NULL E24/E26 microstructure verdict (memory `project_microstructure_archived_2026-04-27`) is consistent with measurement happening in the wrong time. **GTOS implication:** trade-count-bar triggers (e.g., 200 ticks/bar instead of 15 minutes/bar) is the principled, literature-supported alternative — directly testable.

### CC3 — Regime-conditioning is a load-bearing axis; "regimes" must be statistically tested before assumed
**Domains:** 02 (Giacomini-White 2006 conditional predictive ability; Stock-Watson 1996 structural instability), 03 (03-037 TV-Hurst, 03-049 conditional skewness, 03-021 stylized facts shift over time), 04 (Vogl 2023 rolling Hurst; Mensi 2025 asset-class-specific multifractality; #22 random walks Hurst regime-conditional), 05 (Hamilton 1989, sticky HDP-HMM, Kirby 2023 contrarian).

F15 (regime-conditioned LONG-side selectivity collapse, +48.3pp attribution) is corroborated across all four post-01 domains: regimes are real, time-varying, and dominate cross-section. BUT — Kirby 2023 (05-64) provides the methodological brake: 2-state MS fits on heavy-tailed returns can produce "regime parameters" even with no true regime structure. **GTOS implication:** regime-aware K54 v2 is the right direction, but every regime-classifier must pass a fat-tailed-mixture null-test before promotion. Current memory `project_f3_k53_source_stratified_indistinguishable_random` shows K53 already failed this — discipline is non-optional.

### CC4 — Fat-tailed return distributions are universal at GTOS-relevant intraday timeframes
**Domains:** 01 (Mandelbrot 1963; Cont 2001; Embrechts-Klüppelberg-Mikosch 1997 EVT), 03 (Hill / GPD / power-law family; 03-018 Gabaix cubic law; 03-027 Kelly-Jiang tail risk; 03-046 Sornette dragon kings), 04 (multifractal moment scaling), 05 (within-regime fat tails; switching-df Student-t; Maheu-McCurdy 2009).

Tail index alpha ~ 3 (cubic law, Gabaix 2009) is universal across markets, sizes, periods. Memory `project_distributional_findings` (xi=0.35 for gold) sits at the heavy end. **GTOS implication:** SL-buffer multipliers, heartbeat thresholds, drawdown manager (H29) all calibrated under Brownian/Gaussian implicit nulls are systematically mis-specified. The McNeil-Frey 2000 GARCH-EVT pipeline (03-015) is the direct prescription. Sornette's dragon kings (03-046) further warn that the *largest* events may exceed power-law extrapolation — pure-EVT is necessary but not sufficient.

### CC5 — Long memory in volatility (NOT in returns) is robust; long memory in returns is contested
**Domains:** 03 (Ding-Granger-Engle 1993 |r|^d ACF; ABDL 2003 ARFIMA on log-RV; Bonato 2015 gold FIGARCH; Cont 2001), 04 (Lo 1991 modified R/S — returns no LM, vol yes; HAR-RV cascade Corsi 2009; #34 Lopez de Prado fractional differentiation; 24/2025 Mensi gold short-memory), 05 (long memory vs spurious memory; Diebold-Inoue 2001).

Lo 1991 modified R/S removes apparent long memory in returns, but volatility long memory survives. Diebold-Inoue 2001 + Mensi 2025 + 04 multifractal lit caution that "long memory in returns" can be regime-switching artifact. **GTOS implication:** K54 features should be Hurst-on-absolute-returns or Hurst-on-RV (both volatility quantities), NOT Hurst-on-signed-returns. Lopez de Prado fractional differentiation (04-#34) is the principled stationarity-preserving feature transform.

### CC6 — CPCV + triple-barrier + meta-labeling is the canonical ML pipeline for finance
**Domains:** 02 (AFML Ch. 7-12; CPCV; triple-barrier; meta-labeling; Arian-Norouzi-Seco 2024 ML backtest comparison; Joubert et al. 2024 three types of backtests), 19 (cross-link primary).

CPCV produces lowest PBO + highest DSR across all tested ML strategies (Arian 2024). Triple-barrier labels MAP DIRECTLY to GTOS's existing TP/SL/time-out outcomes. Meta-labeling layers a binary skill classifier on top of a primary signal. **GTOS implication:** K54 v2 should be wired as a meta-labeler over Component 3A (filter signals, don't replace them), trained on triple-barrier labels, validated under CPCV. The Q1.3 K54 v2 architecture-A (per-fold top-100 feature screening) attempts a CPCV-honest discipline — this synthesis confirms the direction is correct.

### CC7 — Multiple-testing discipline is the single largest threat to "lift" claims; cumulative trial count must be tracked
**Domains:** 02 (White Reality Check; Hansen SPA; Romano-Wolf StepM; Harvey-Liu-Zhu 2016 t > 3.0; Bailey-Lopez de Prado deflated SR; PBO; False Strategy Theorem; Lucky Factors), 13 (factor zoo cross-link), 22 (cross-link McLean-Pontiff post-pub decay).

E[max IS-Sharpe over N noise trials] ~ sqrt(2 ln N) (Lopez de Prado-Bailey 2018 false-strategy theorem). With cumulative GTOS trial count ~200 (prompt cascades + K-series + canary fixtures), the noise ceiling is sqrt(2 ln 200) ~ 3.27. Anything below this in IS is statistically attributable to chance. **GTOS implication:** every "lift" headline (J46-J49 +0.742R, S79 +25.8pp, K54 +0.164R) must report N and compute DSR before promotion. Currently in CLAUDE.md none of these report N alongside the lift.

### CC8 — Multi-scale heterogeneity (HAR cascade) replaces the single-scale assumption
**Domains:** 01 (Karatzas-Shreve excursion theory; subordination), 03 (ABDL 2003; HAR/MIDAS class), 04 (Corsi 2009 HAR-RV — three-cascade D/W/M; Souropanis-Vivian 2023 wavelet+HAR; #36 multifractal HAR; #38 Dacorogna et al. heterogeneous-market-hypothesis), 16 (cross-link).

Heterogeneous-market-hypothesis (HMH): different participant types operate at different time scales. HAR-RV's three-cascade structure (daily/weekly/monthly) is *isomorphic* to GTOS's M15 -> H1 -> H4 hierarchy. **GTOS implication:** K54 v2 should adopt HAR-RV-style additive cascade features (M15-aggregated 1-bar, 5-bar, 22-bar realized-vol), instead of single-scale features. Direct hypothesis: AUC lift >= 0.02 vs current K54 baseline 0.571.

### CC9 — Online change-point detection should use BOCPD-AR/score-driven, not vanilla iid-within-regime
**Domains:** 02 (Page CUSUM; Wang 2024 CPD review; e-detectors), 05 (Adams-MacKay 2007 BOCPD; Tsaknaki-Lillo-Mazzarisi 2024 BOCPD-AR-score-driven; Aue-Kirch 2024 self-normalized CUSUM; sticky HDP-HMM 2008-11).

Vanilla BOCPD assumes iid within regime — empirically false for financial returns (volatility clustering, momentum). The Tsaknaki et al. 2024 BOCPD-AR-score-driven extension fixes this and improves on real LOB data. Aue-Kirch 2024 + e-detectors (Wang-Ramdas 2025) extend CUSUM to anytime-valid streaming use. **GTOS implication:** S1 monthly-decay shadow monitor should ship BOCPD-AR-score-driven (lower false-alarm), and the CUSUM-candidate-rate-daily monitor should adopt self-normalized variants. Both upgrades are zero-new-ML-infra and align with the heartbeat/decay observability story.

### CC10 — Signature methods + path-dependent features are the principled feature-engineering alternative
**Domains:** 01 (Lyons 1998; Hambly-Lyons 2010; Chevyrev-Kormilitzin 2016; Lyons-McLeod 2022 signature methods; Cuchiero-Möller 2024 signature portfolios), 04 (wavelet decomposition; fractional differentiation), 19 (cross-link primary).

Signature features linearize nonlinear functionals on path space (universal approximation), with formal injectivity at sufficient depth. Cuchiero-Möller 2024 operationalizes this for portfolio sizing. **GTOS implication:** depth-3 truncated signatures of (price, ATR, volume) over the last 10 H1 candles is a principled K54 v2 feature replacement. Ito-Lyons continuity provides robustness to noisy tick data — an underappreciated property for production deployment.

### CC11 — Forecast comparison must be conditional (regime-aware), not unconditional
**Domains:** 02 (Giacomini-White 2006 conditional predictive ability; Patton 2020 misspecified forecast comparison; Diebold 2015 retrospective), 05 (regime-conditional Sharpe Guidolin-Timmermann; Maheu-McCurdy bull/bear).

Patton 2020 proves that under misspecification, forecast ranking depends on chosen loss function. Walk-AUC and realized-R can rank K54 differently (memory `feedback_walk_level_evidence_not_predictive`). Giacomini-White 2006 says conditional comparison can detect time-varying superiority that unconditional misses. **GTOS implication:** K54 vs Sonnet 4.6 comparison must be regime-conditional + use realized-R loss (not just walk-AUC). The current K54 MARGINAL_WITH_PRACTICAL_LIFT verdict (memory `project_k54_ml_classifier_baseline_2026-04-27`) likely understates the conditional advantage in regimes where Sonnet underperforms.

### CC12 — Spurious-regime / lucky-factor / data-snooping risk is empirically large
**Domains:** 02 (Lucky Factors Harvey-Liu 2021; False/Missed Discoveries Harvey-Liu 2020; Detection of false strategies via unsupervised learning Lopez de Prado-Lewis 2018; effective-N from clustering; Hou-Xue-Zhang 2020 65% anomalies fail), 05 (Kirby 2023 spurious bull/bear; Levi 2024 practitioner spurious-regime warning).

Naive Bonferroni over-deflates correlated tests; correlation-aware Lucky Factors reveals ~30% of "significant" features are lucky. ONC clustering reveals effective N is typically 0.3-0.5 x literal N. Kirby 2023 separately warns that 2-state MS parameters can be artifacts of fat-tail mixtures. **GTOS implication:** K54 v2 promotion gate must include (i) BCa-bootstrap CI on lift, (ii) DSR with correlation-adjusted effective N, (iii) regime-classifier null-test on simulated fat-tailed mixture data. K53 already failed (i)+(iii) per memory `project_f3_k53_source_stratified_indistinguishable_random`.

---

## Section 3 — Top 15 GTOS-actionable hypotheses (ranked by expected impact x feasibility)

Each hypothesis is annotated with: **(I)** expected impact, **(F)** feasibility, **(P)** primary GTOS subsystem addressed, and **(C)** cross-cutting finding it draws from. Score = I + F (informal, 1-5 each).

### Rank 1 — H-Rough-Vol-Aware Heartbeat (I=5, F=4, score=9)
**Hypothesis.** Replacing the GTOS heartbeat threshold from a Gaussian/ATR-implied null to a McNeil-Frey GARCH-EVT (03-015) pipeline with rough-fBM (H~0.1) forward-vol forecasts will reduce false-trigger rate by >=30% while improving 99%-ES coverage by >=20%, *especially* during high-vol regimes.
- **(P)** `src/safety/heartbeat_monitor.py`, `src/components/drawdown_manager.py`, H29 8% DD trigger.
- **(C)** CC1 (rough vol), CC4 (fat tails), CC5 (vol long memory).
- **Why high I:** the 4% portfolio-DD hard rule is implicitly Gaussian under heavy-tailed reality (Group A consensus); single calibration fix improves three production gates.
- **Why high F:** zero new ML infra; statsmodels already has GARCH; arch package supports EVT-GPD; closed-form 1-day ES.

### Rank 2 — H-Meta-Label-K54 (I=5, F=4, score=9)
**Hypothesis.** Wire K54 as a meta-labeler over Component 3A (Sonnet 4.6 primary signal) using triple-barrier labels under CPCV — preserving AI's directional signal while filtering decay-regime LONG bias. Expected: +0.10R/trade vs current state at >=30% precision boost on filtered cohort.
- **(P)** K54 v2 architecture (Phase 2 rank 1 in CLAUDE.md).
- **(C)** CC6 (CPCV+meta-labeling), CC11 (regime-conditional forecast comparison).
- **Why high I:** memory `project_k54_ml_classifier_baseline_2026-04-27` MARGINAL_WITH_PRACTICAL_LIFT verdict + memory `feedback_walk_level_evidence_not_predictive` together imply meta-labeling is exactly the pattern needed: K54 as a skill filter, not a signal replacement.
- **Why high F:** Q1.3 K54 v2 already failed under CPCV-honest discipline; meta-labeling reformulation is a reframe + retest, not a new architecture.

### Rank 3 — H-Sticky-HDP-HMM-Regime-Classifier (I=5, F=3, score=8)
**Hypothesis.** A sticky HDP-HMM (Fox et al. 2008-11; 05-31) on XAU H4 returns + RV + RV-skew + DXY change selects K=3-5 regimes data-drivenly with realistic state persistence; produces regime labels with OOS realized-R AUC >=0.05 better than v1 swing classifier on H1->H2 OOS test.
- **(P)** `src/components/regime_classifier.py` upgrade.
- **(C)** CC3 (regime-conditioning), CC9 (HDP nonparametric), CC12 (spurious-regime risk).
- **Why high I:** Phase 2 rank-1 task (K54 regime-aware ML) depends on the regime label. Current v1 is observational only; sticky-HDP-HMM gives probabilistic confidence + auto-K + realistic dwell time.
- **Why moderate F:** sticky-HDP-HMM is computationally non-trivial; PyMC or pyhsmm has implementations but the Bayesian inference layer is heavier than LightGBM.
- **Mandatory:** must pass Kirby 2023 fat-tailed-mixture null-test before production.

### Rank 4 — H-Trade-Count-Time-Triggers (I=4, F=4, score=8)
**Hypothesis.** Switching from M15-wallclock triggers to instrument-specific 200-trade-count bars (Ane-Geman 2000 + Glattfelder-Dupuis-Olsen 2011) lifts OB-WR by >=3pp on H2-2026 holdout, controlled for total trade frequency. Reopens the E24/E26-archived microstructure track.
- **(P)** Component 1 data ingestion; entire candle-aggregation logic.
- **(C)** CC2 (operational clock).
- **Why high I:** if Group A's "M15 wallclock fights operational clock" hypothesis is correct, this is a foundational architecture fix that affects every downstream signal. Memory `project_microstructure_archived_2026-04-27` may be measurement-artifact-driven NULL.
- **Why high F:** tick daemon already captures ticks; trade-count aggregation is a simple groupby-cumsum on existing data. Backtestable on 2024-2026 history.

### Rank 5 — H-Signature-Feature-K54-v2 (I=4, F=4, score=8)
**Hypothesis.** Replacing K54's engineered features with depth-3 truncated-signature features (Lyons-McLeod 2022 + Cuchiero-Möller 2024) over the last 10 H1 candles improves H2-2026 holdout AUC by >=0.02, controlled for total feature dimension.
- **(P)** K54 v2 feature engineering.
- **(C)** CC10 (signature methods).
- **Why high I:** Q1.3 architecture-A used per-fold top-100 feature screening with marginal lift; signature features replace the screening problem with a principled universal-approximator. Hambly-Lyons 2010 injectivity provides theoretical guarantee.
- **Why high F:** signatory or iisignature Python packages compute signatures cheaply at depth 3.

### Rank 6 — H-Multivariate-Self-Normalized-CUSUM (I=4, F=4, score=8)
**Hypothesis.** Self-normalized multivariate CUSUM on (XAU, US30, USDJPY) joint daily WR/CR/OB-continuation vector reduces S1 false-alarm rate by >=30% at matched detection delay, vs single-statistic baseline.
- **(P)** S1 monthly-decay shadow monitor; CUSUM-candidate-rate-daily monitor; `scripts/ob_continuation_monitor.py`.
- **(C)** CC9 (BOCPD-AR / self-norm CUSUM), CC3 (cross-instrument regime).
- **Why high I:** zero-new-ML-infra upgrade; cross-instrument contagion is exactly the missed regime signal in current per-instrument CUSUM design.
- **Why high F:** Aue-Kirch 2024 (05-43) gives the formula directly; ruptures Python package or simple implementation.

### Rank 7 — H-Jump-Aware-CGMY-SL-Buffer (I=4, F=3, score=7)
**Hypothesis.** Recalibrating XAUUSD / NAS100 / US30 SL-buffer ATR-multiples under a CGMY null (Carr-Geman-Madan-Yor 2002) or Kou (2002) double-exponential first-passage formula with parameters fitted from 2026 tick data shifts optimal buffer by >=0.2 ATR vs current Brownian-implied calibration; back-tested R/trade improves >=0.05 on H2-2026.
- **(P)** `risk.sl_buffer_atr_multiplier` (ADR-006), per-instrument profiles.
- **(C)** CC4 (fat tails), CC1 (rough vol), CC6 (jump processes).
- **Why high I:** memory `project_eurusd_sl_root_cause` and HALLUC-1 reframe show SL-buffer mis-calibration is the live decay class. Jump-aware first-passage gives the principled answer.
- **Why moderate F:** CGMY calibration via FFT is in scipy/specialized packages but requires care; Kou is closed-form first-passage.

### Rank 8 — H-Wavelet-Coherence-Correlation-Gate (I=3, F=4, score=7)
**Hypothesis.** Replacing the cross-instrument correlation gate's Pearson-30-bar with wavelet coherence at scale 6 (~1d-equivalent) plus partial wavelet coherence controlling for DXY removes spurious USD-driven correlation; reduces correlated-pair detection lag by >=1 bar.
- **(P)** `src/components/cross_instrument_correlation_gate.py`.
- **(C)** CC8 (multi-scale heterogeneity), Aguiar-Conraria-Soares 2014 + Tiwari et al. 2016.
- **Why moderate I:** correlation gate is a downstream additive HALVE/REJECT gate; modest lift but improves clarity.
- **Why high F:** PyWavelets supports CWT; partial wavelet coherence is small extension.

### Rank 9 — H-Fractional-Differentiation-Features (I=4, F=4, score=8)
**Hypothesis.** Replace return-based features in K54 with fixed-width fractional differentiation (Lopez de Prado AFML Ch. 5; 04-#34) at optimal d* (binary search for ADF rejection). Resulting features preserve memory while being stationary; expected lift >=0.02 AUC.
- **(P)** K54 v2 feature engineering.
- **(C)** CC5 (vol long memory), CC10 (path-dependent features).
- **Why high I:** complementary to signature features; addresses the "returns destroy info" problem directly.
- **Why high F:** trivial Python implementation; pre-computed weights via Newton's binomial.

### Rank 10 — H-HAR-RV-Cascade-K54-Features (I=4, F=4, score=8)
**Hypothesis.** Adding HAR-RV-style three-cascade RV features (1-bar / 5-bar / 22-bar M15-aggregated realized variance) plus seasonality-corrected intraday RV (Kim et al. 2023) to K54 lifts AUC by >=0.02 vs raw single-scale RV.
- **(P)** K54 v2 feature engineering.
- **(C)** CC8 (multi-scale heterogeneity), CC1 (rough vol via realized).
- **Why high I:** HAR-RV is the canonical multi-scale vol forecast; isomorphic to GTOS M15->H1->H4 hierarchy.
- **Why high F:** Tick daemon already computes M1; aggregation to RV is trivial; pyflux/statsmodels HAR templates exist.

### Rank 11 — H-DSR-Promotion-Gate (I=5, F=5, score=10) [METHODOLOGY — see Section 4]
*Listed in Section 4 as a methodology improvement, not a research hypothesis.*

### Rank 12 — H-Bayesian-Online-CPD-AR-Score-Driven (I=4, F=3, score=7)
**Hypothesis.** A BOCPD-AR(p)-score-driven detector (Tsaknaki-Lillo-Mazzarisi 2024; 05-41) on XAUUSD M15 returns + RV + RV-skew + tick microstructure features will detect the F15-style regime change with detection delay <=7 trading days at FPR <=5% — replacing the rolling-50 + threshold heuristic with a principled streaming detector.
- **(P)** `scripts/ob_continuation_monitor.py`, S1 monthly-decay shadow monitor.
- **(C)** CC9 (BOCPD-AR), CC3 (regime-conditioning).
- **Why moderate-high I:** real-time regime alarm with calibrated FPR; feeds K54 + cross-instrument gate.
- **Why moderate F:** BOCPD-AR-score-driven implementation is non-trivial but published; the 2024 reference paper has open-source code in some forks.

### Rank 13 — H-Conditional-Predictive-Comparison-K54 (I=4, F=4, score=8)
**Hypothesis.** Reframing K54-vs-Sonnet 4.6 comparison as a *conditional* Giacomini-White test (using current regime as conditioner) and computing realized-R loss differential will detect K54-superiority within H2 trending_bull regime even where unconditional DM is null — directly informing K54 production-gate design.
- **(P)** K54 evaluation pipeline.
- **(C)** CC11 (conditional forecast comparison), CC3 (regime-conditioning).
- **Why high I:** memory `project_f2_long_decay_pinpointed_trending_bull_2026-04-27` shows decay is regime-cell-localized; current K54 verdict averages across regimes and underestimates conditional value.
- **Why high F:** statsmodels has DM test; conditioning is regression-based.

### Rank 14 — H-Dragon-King-Monitor-Augmenting-EVT (I=3, F=4, score=7)
**Hypothesis.** A super-exponential-bubble detector (Sornette 2003 LPPL diagnostic mode; 03-046 dragon kings) added as a flag (not gate) alongside EVT-GPD heartbeat monitor identifies the largest-loss precursor patterns missed by power-law extrapolation. Validated diagnostic vs predictive use only.
- **(P)** Heartbeat monitor / decay observability.
- **(C)** CC4 (fat tails), CC12 (data-snooping caveat).
- **Why moderate I:** flag-not-gate; informational.
- **Why high F:** Sornette's framework has open-source implementations; LPPL fit on rolling windows.

### Rank 15 — H-Hawkes-Dynamic-Correlation-Threshold (I=3, F=2, score=5)
**Hypothesis.** Replacing the static |corr| >= 0.4 cross-instrument correlation threshold with a Hawkes-kernel-implied dynamic threshold (Bacry-Mastromatteo-Muzy 2015; Laub et al. 2024) reduces correlated-loss days by >=10%, controlled for total trade frequency.
- **(P)** Cross-instrument correlation gate.
- **(C)** CC1 (rough vol microstructure), CC9 (CPD).
- **Why moderate I:** specific threshold tuning; modest expected lift.
- **Why low-moderate F:** multivariate Hawkes inference is non-trivial; tick package + Bacry et al. tutorials.

---

## Section 4 — Methodology improvements GTOS should adopt

Group A is the methodology-rich group. The following are **single, immediately-actionable methodology upgrades** — most cost less than 1 engineering day and prevent classes of overclaiming that have already cost GTOS in K-series.

### M1 — DSR + PBO + effective-N adoption for every "lift" headline (HIGHEST PRIORITY)
**Source:** 02-#10 Bailey-Lopez de Prado 2014 deflated SR; 02-#12 PBO; 02-#54 false strategy theorem; 02-#55 Lopez de Prado-Lewis 2018 detection via unsupervised learning (effective N via ONC).

**Adopt:** every "+0.X R/trade" or "+Y AUC" claim in the unresolved list (J46-J49 +0.742R, K54 +0.164R, S79 +25.8pp, A2 v2-active backtest pending) must report (i) cumulative trial count N, (ii) DSR-corrected p-value, (iii) PBO from CSCV, (iv) effective-N via ONC clustering of trial population. Without these, "lift" headlines are mathematically suspect (Bailey-Lopez de Prado 2014: 1000 trials -> noise-only Sharpe ~ 3.7). Cross-references CLAUDE.md `What is unresolved` items #4, #5 and `feedback_walk_level_evidence_not_predictive`.

**One-line change to research workflow:** every artifact in `research/` that includes a Sharpe / R-multiple / AUC headline must include a `dsr_diagnostics.json` with the four numbers above.

### M2 — CPCV mandatory for K54 v2; report walk-forward + CPCV + Monte-Carlo simultaneously
**Source:** 02-#9 AFML; 02-#23 Joubert et al. 2024 three types of backtests; 02-#25 Arian-Norouzi-Seco 2024.

**Adopt:** Q1.3 K54 v2 already used CPCV honestly and surfaced p=0.68. Continue. Additionally, require Monte-Carlo regime-stress evaluation (simulate H1->H2 30%-shift scenarios) per Joubert et al. 2024. Single-class backtest (CPCV only) is insufficient; multi-class reveals robustness profile.

### M3 — Conditional Giacomini-White test for forecast comparison instead of unconditional Diebold-Mariano
**Source:** 02-#17 Giacomini-White 2006; 02-#33 Patton 2020 misspecified forecasts.

**Adopt:** any K54 vs Component 3A comparison must condition on regime and use realized-R loss (not walk-AUC). Patton 2020 proves the ranking can flip across loss functions under misspecification. Memory `feedback_walk_level_evidence_not_predictive` already shows this empirically.

### M4 — Romano-Wolf StepM for the 47 instrument-side-regime cell tests
**Source:** 02-#16 Romano-Wolf 2005; 02-#56 Lucky Factors Harvey-Liu 2021.

**Adopt:** any "F-series finding pinpoints cell X" claim (e.g., F2 trending_bull LONG -59.8pp) must apply Romano-Wolf StepM at alpha=0.05 over the 47 cells before being treated as production-decision-grade. Lucky Factors gives a stronger correlation-aware variant.

### M5 — Stationary bootstrap (Politis-Romano) instead of iid bootstrap for trade PnL CIs
**Source:** 02-#19 Politis-Romano 1994; 02-#48 Cavaliere 2015 dependent bootstrap review.

**Adopt:** every Sharpe / hit-rate / R-multiple confidence interval must use stationary bootstrap (geometric block lengths). Trade-by-trade PnL is autocorrelated; iid bootstrap underestimates CI width. The J46-J49 +0.742R/trade headline (n=321, p=3.3e-20) likely uses iid; stationary bootstrap will widen CI by ~30%.

### M6 — Fat-tailed-mixture null-test for any regime classifier before production
**Source:** 05-64 Kirby 2023 spurious bull/bear evidence; 05-65 Levi 2024 spurious regimes whitepaper.

**Adopt:** before promoting *any* regime classifier (sticky HDP-HMM, MS-AR, BOCPD-AR-score-driven), simulate returns from a stationary fat-tailed mixture (no regime structure) calibrated to GTOS data, run the classifier on simulated data, check whether parameter estimates / regime labels look qualitatively similar to live data. If yes, regime interpretation is unsafe.

### M7 — McNeil-Frey GARCH-EVT for all VaR / heartbeat / DD threshold calibration
**Source:** 03-015 McNeil-Frey 2000; 03-031 covariate-GPD; 03-016 Acerbi-Tasche coherent ES.

**Adopt:** replace any GTOS heartbeat / DD trigger that implicitly uses Gaussian or rolling-stdev with the GARCH-EVT pipeline at 99%-ES (not VaR). Coherent ES dominates VaR for portfolio aggregation. Closed-form once GARCH and GPD are fitted.

### M8 — Reality Check + SPA / MCS for all multi-prompt / multi-fixture comparisons
**Source:** 02-#2 White 2000 Reality Check; 02-#3 Hansen SPA; 02-#27 Hansen-Lunde-Nason 2011 MCS; 02-#29 Stepwise SPA.

**Adopt:** any "v3 cascade is best" or "K54 hyperparameter X wins" claim should report Reality-Check / SPA / MCS p-value over the candidate population — not single-best p. Per memory `project_haiku_cache_minimum_tokens` and `project_batch_discount_denominator_misleading`, multi-variant testing is a recurring GTOS pattern; MCS specifically accommodates the case where data cannot resolve a single winner (output is a SET of viable candidates).

### M9 — Operational checklist before any backtest finding is "promotion-grade"
**Source:** 02-#22 Lopez de Prado 2013 "What to look for in a backtest"; 02-#23 three types of backtests.

**Adopt:** integrate the Lopez de Prado backtest-sins checklist (10 items: survivorship bias, look-ahead, data-mining, transaction-cost realism, pseudo-stationarity, ...) into the research/ directory's promotion gate. Audit J46-J49 specifically — likely look-ahead in TP1 immediate-BE rule per the memory implication.

---

## Section 5 — Contradictions / debates flagged

### D1 — IS vs OOS testing: Inoue-Kilian (2005) vs Lopez de Prado AFML doctrine
**Inoue-Kilian 2005 (02-#30):** the conventional "OOS is more reliable" wisdom is wrong; IS tests have higher power and the OOS-IS gap can be explained by data-mining bias correction *of OOS itself*, not unique-OOS-virtue. Diebold 2015 (02-#26) reflective retrospective concurs: "belief that pseudo-OOS guards against IS-overfit is largely false."

**Vs.**

**Lopez de Prado AFML doctrine (02-#9, 02-#10, 02-#15, etc.):** OOS-honest CPCV is the gold standard; AUC reported on holdout is the only legitimate metric.

**Surface to CEO:** **TOP 1 contradiction worth surfacing.** The two camps disagree on whether GTOS should re-run OOS-style retests (current default) or adopt full-sample IS tests with proper SE + multiple-testing correction. Resolution likely instrument-specific: full-sample IS + Romano-Wolf may give MORE power for already-decided regime-cells (e.g., F2 trending_bull LONG); OOS-CPCV remains right for new feature exploration. This affects Q1.4 design choice.

### D2 — Long memory in returns: real (Mandelbrot framework) vs spurious (Lo 1991, Diebold-Inoue 2001)
**Mandelbrot 1963 + multifractal lit (01, 03, 04):** prices are heavy-tailed and self-similar across timescales; long memory is real and structural.

**Vs.**

**Lo 1991 modified R/S (04-#3):** stock returns have NO statistically significant long memory after short-range adjustment. Diebold-Inoue 2001 + Mensi 2025 (04-#24): "long memory" can be regime-switching artifact.

**Resolution status:** literature converges that long memory in *volatility* is real, but long memory in *signed returns* is contested. K54 should use Hurst-on-|r| or Hurst-on-RV, not Hurst-on-r.

### D3 — Multifractality: empirical fact (Mandelbrot, MMAR, MFDFA) vs methodology artifact (Frontiers 2026)
**Mandelbrot-Calvet-Fisher 1997 (04-#16); Kantelhardt et al. 2002 (04-#15):** multifractal moment scaling is universal in financial returns.

**Vs.**

**Frontiers in Physics 2026 (cited in 04 caveat #1):** "multifractality should be viewed not as an established empirical fact, but rather as a working hypothesis whose validity largely depends on methodology, data quality, and observation scale."

**Resolution status:** sample-size-conditional. For series < 1000 bars, multifractal claims are unreliable. K54 features derived from MFDFA / multifractal spectra should be windowed conservatively.

### D4 — Discrete regime models (Hamilton MS, sticky HDP-HMM) vs continuous-drift TVP (Primiceri 2005)
**Hamilton 1989, Krolzig 1997, Fox sticky HDP-HMM (05):** discrete regimes capture business cycles, bull/bear, vol-state.

**Vs.**

**Primiceri 2005, Cogley-Sargent 2005 (05-#59, #60):** continuous-drift TVP-VAR captures gradual evolution; STAR (05-#16) gives smooth transitions.

**Resolution status:** time-scale-conditional. Slow continuous drift (multi-year) and discrete regime shifts (multi-month) coexist. K54 v2 should support both — sticky HDP-HMM for discrete labels + a TVP-VAR layer for slow parameter drift.

### D5 — VaR vs ES: practitioner default (VaR) vs coherent measure (ES)
**Acerbi-Tasche 2002 (03-016):** VaR fails subadditivity; portfolio diversification can INCREASE VaR. ES is coherent.

**Vs.**

**Industry default + GTOS current state:** GTOS's "single trade > 1.5R" rule is implicitly VaR-style; portfolio rule on VaR is unsafe.

**Resolution status:** ES dominates for portfolio aggregation. Heartbeat threshold should migrate to 99%-ES at 1d horizon.

---

## Section 6 — Build-this-next recommendations for K54 v2 / Q1.4 spec

The following is a **prioritized engineering plan** for K54 v2 architecture revision and Q1.4 spec, grounded entirely in Group A literature.

### Priority 1 — K54 v2 as meta-labeler with CPCV + triple-barrier + DSR gate (CC6 + M1, M2)
- **Architecture:** Component 3A (Sonnet 4.6) emits primary signal; K54 v2 is a binary skill classifier on top, trained on triple-barrier outcomes (TP/SL/time-out). Output: keep / filter the primary signal.
- **Validation:** CPCV with k=2 over N=12 monthly blocks; report walk-forward + CPCV + Monte-Carlo regime-stress (Joubert et al. 2024). DSR + PBO + effective-N as promotion gate.
- **Loss function:** realized-R, not walk-AUC. Conditional Giacomini-White test against unfiltered baseline.
- **Why first:** addresses Q1.3 K54 v2 failure (p=0.68) by reframing the question — K54 doesn't need to beat AI head-to-head; it needs to add value as a filter where AI underperforms (decay regimes).

### Priority 2 — Sticky HDP-HMM regime-classifier upgrade with Kirby null-test (Rank 3 + M6)
- **Architecture:** sticky HDP-HMM on XAU H4 returns + RV + RV-skew + DXY change. Output: per-bar regime probability vector (K=3-5).
- **Validation:** null-test on simulated fat-tailed mixture (Kirby 2023). If parameter estimates look qualitatively similar to live data, REJECT regime interpretation.
- **Integration:** regime probability vector feeds K54 v2 features (CC3 + Rank 13 conditional comparison).
- **Why second:** K54 v2's regime-aware advantage depends on a trustworthy regime label. v1 swing classifier is observational; sticky HDP-HMM gives the label with confidence.

### Priority 3 — Feature engineering refresh: signatures + fractional differentiation + HAR-RV cascade (Ranks 5, 9, 10)
- **Add:** depth-3 truncated signatures of (price, ATR, volume) over last 10 H1 candles (CC10).
- **Add:** fixed-width fractional-differentiated price at optimal d* (binary search ADF rejection; CC5).
- **Add:** HAR-RV three-cascade (1-bar / 5-bar / 22-bar M15 RV) plus Kim et al. 2023 seasonality-corrected intraday RV (CC1, CC8).
- **Drop:** raw return features (per Lo 1991 — return long-memory is spurious; per Lopez de Prado AFML — returns destroy info).
- **Keep:** OB-touch features (per F11 — OB-zone advantage degraded but not gone, +4.6pp H2-2026).

### Priority 4 — McNeil-Frey GARCH-EVT pipeline for risk gates (Rank 1 + M7)
- **Apply:** to heartbeat threshold + H29 8% DD trigger + S79 risk-policy.
- **Output:** 99%-ES at 1d horizon, vol-conditioned per instrument.
- **Why this priority:** addresses memory `project_distributional_findings` xi=0.35 and the implicit-Gaussian-null-under-heavy-tailed-reality systematic bias.

### Priority 5 — Multivariate self-normalized CUSUM + BOCPD-AR-score-driven (Ranks 6, 12)
- **Add:** self-normalized CUSUM on (XAU, US30, USDJPY) joint daily WR/CR/OB-continuation vector (Aue-Kirch 2024).
- **Add:** BOCPD-AR-score-driven on XAU M15 returns + RV + RV-skew + tick microstructure features (Tsaknaki et al. 2024).
- **Replace:** rolling-50 OB-continuation alarm + threshold heuristic.
- **Why this priority:** zero-new-ML-infra; immediate operational improvement; aligns with S1 monthly-decay shadow monitor.

### Priority 6 — Trade-count-time triggers (Rank 4 + CC2)
- **Pilot:** 200-trade-count bars per instrument; backtest on 2024-2026 history.
- **Decision criterion:** if OB-WR lift >= 3pp on H2-2026 holdout, escalate to M15-equivalent-trade-count features, then Component 1 trigger replacement.
- **Why this priority:** bigger architectural intervention; should follow the smaller-changes wins (Priorities 1-5) to avoid parallel-debugging chaos.

### Priority 7 — Q1.4 spec must require:
1. **Pre-registration** of hypotheses (per CLAUDE.md anti-fabrication rule + Group A multiple-testing discipline).
2. **DSR + PBO + effective-N** in every "lift" claim (M1).
3. **CPCV + walk-forward + Monte-Carlo regime-stress** triple-class backtest (M2 + Priority 1).
4. **Conditional Giacomini-White** for any K54-vs-AI comparison (M3 + Rank 13).
5. **Romano-Wolf StepM** for any cell-pinpointed claim (M4).
6. **Stationary bootstrap** for all CIs (M5).
7. **Kirby null-test** for any regime classifier (M6 + Rank 3).
8. **Lopez de Prado backtest-sins checklist** as promotion gate (M9).

---

## Final report (synthesis-only summary)

**Total papers read across 5 domains:** 275 (42+70+50+38+75).

**Top 5 cross-cutting findings (>=2 domains):**
1. Volatility is rough (H ~ 0.1) at intraday scales with Hawkes-process micro-foundation (CC1, domains 01+03+04+16).
2. Trading-time / transaction-count-time is the operational clock; M15 wallclock fights it (CC2, domains 01+03+04+06).
3. Regime-conditioning is load-bearing but spurious-regime risk is real (CC3+CC12, domains 02+03+04+05).
4. Fat tails universal at intraday scales; Brownian-implied SL/heartbeat thresholds systematically mis-specified (CC4, domains 01+03+04+05).
5. CPCV + triple-barrier + meta-labeling + DSR + multiple-testing discipline are the canonical ML-finance methodology stack (CC6+CC7+CC11+CC12, domain 02 primary).

**Top 5 actionable hypotheses (with GTOS subsystem):**
1. Rough-vol-aware GARCH-EVT heartbeat (heartbeat_monitor.py + drawdown_manager.py).
2. K54 v2 as meta-labeler over Component 3A under CPCV + triple-barrier (K54 architecture).
3. Sticky HDP-HMM regime-classifier with Kirby null-test (regime_classifier.py).
4. Trade-count-time triggers (Component 1 data ingestion + tick daemon).
5. Signature features + fractional differentiation + HAR-RV cascade (K54 v2 features).

**Top 1 contradiction worth surfacing to CEO:**
Inoue-Kilian 2005 + Diebold 2015 (02-#30, 02-#26) argue that **IS tests with proper SE + multiple-testing correction often beat OOS tests** — directly contradicting the Lopez de Prado AFML CPCV-honest doctrine that GTOS currently follows. Resolution likely instrument-specific (full-sample IS for already-decided cells; CPCV-OOS for new features). Affects Q1.4 design choice.

**Top 1 methodology improvement to adopt now (before Q1.4):**
**M1 — DSR + PBO + effective-N for every "lift" headline.** With cumulative GTOS trial count ~200, false-strategy-theorem noise ceiling is sqrt(2 ln 200) ~ 3.27 IS Sharpe. None of the unresolved-list lifts (J46-J49 +0.742R, K54 +0.164R, S79 +25.8pp) currently report DSR-corrected p with effective-N. This is the single discipline that prevents most overclaiming and is implementable in less than 1 engineering day.

---

*End of Group A synthesis. Cross-references: domain papers.md files (paths above), CLAUDE.md unresolved items #4, #5, #11; memories `project_f15_synthesis_regime_is_load_bearing`, `project_k54_ml_classifier_baseline_2026-04-27`, `feedback_walk_level_evidence_not_predictive`.*
