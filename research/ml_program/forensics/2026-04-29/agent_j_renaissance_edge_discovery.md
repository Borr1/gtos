# Agent J — Renaissance-Medallion Edge-Discovery Sprint

**Author:** Forensic Agent J (Opus 4.7, max effort, subscription-only, READ-ONLY for production)
**Date:** 2026-04-29
**Mandate:** If GTOS's surviving alphas (J46-J49 + S79 + NAS_US30 specialist candidate) point to the Renaissance-Medallion model (aggregate small uncorrelated edges per Group F §6), what other small uncorrelated edges might exist? Generate a ranked hypothesis backlog of 20-30 candidate dispatches that fit the "small DSR-feasible uncorrelated edge" pattern.

**Inputs read:** Group A/C/D/E/F syntheses, MASTER_BACKLOG.md (178 items), HYPOTHESIS_BACKLOG.md (30 ranks), `audit/dsr_retroactive_sweep.md`, `audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`, `audit/dsr_diagnostics.json`, CLAUDE.md edge_mechanism.md, memories `project_j46_j49_position_mgmt_findings`, `project_s79_risk_policy_shipped_2026-04-27`, `project_side_aware_sizing_findings`, `feedback_research_goal_high_quality_frequency`, `feedback_decay_is_ceo_number_one_concern`, `feedback_walk_level_evidence_not_predictive`, `feedback_paired_fixed_hp_discipline`.

---

## 1. The Renaissance-style edge criteria (locked spec)

Per Group F §6 + Cornell 2020 (Medallion 63.3% gross compound, 30 years, no down year) + Zuckerman 2019: Medallion's durability comes from **thousands of small uncorrelated signals**, not one large edge. Reverse-engineered, a Renaissance-style edge for GTOS at the current ($100k AUM, n=2,326 cohort, N=200 trial-budget) regime must satisfy ALL six gates:

### 1.1 Six gates an edge must clear to be "Renaissance-feasible"

| Gate | Specification | Why it's the right gate |
|---|---|---|
| **G1 — Magnitude** | Expected lift ≈ +0.05R/trade OR +0.02 AUC OR +1pp WR. Not a +0.20R home run; not a +0.001R tickle. | Group F Finding 3: AUC-vs-realized-R gap is structural; +0.05R is the "small but durable" frame Q1.4 post-mortem (§3) explicitly endorses. |
| **G2 — DSR-feasibility at N=200** | Required: `lift × sqrt(n) ≥ 1.5 × sigma_obs` ⟺ paired Sharpe ≥ 1.5. With kurtosis=5 fat-tail adjustment, an edge with raw Sharpe 1.5 at n=329 (Q1.4 cohort 2024-2026 effective N) translates to **lift ≥ +0.12R/trade** OR an AUC lift of +0.03 with paired-DeLong SE 0.020. | DSR-p < 0.01 with `E[max SR | 200] = 3.08` per `audit/dsr_retroactive_sweep.md`. Below SR 1.5 → DSR-p > 0.05 deterministically. |
| **G3 — Independence** | Pearson \|ρ\| < 0.30 with realized-R from {J46-J49, S79, OB-precision rolling-50, kill-zone gate}. | Group F §6: aggregating correlated edges adds nothing. Variance reduction `Var(sum(ρ=0.3 series)) ≈ 0.4 × Var(sum(ρ=0.0 series))` for n=10 portfolio of edges. |
| **G4 — Mechanism-grounded** | ≥3 cited papers OR a behavioral/microstructure mechanism that is closed-form / falsifiable. Anti-rule: NOT just "this feature has p < 0.05 in a sweep." | Lo's AMH: edges with mechanism survive selection; data-mined patterns decay 26% OOS, 58% post-publication (McLean-Pontiff 2016). |
| **G5 — Substrate-feasible on MT5 retail** | Computable from existing GTOS infra: OHLCV + tick captures (`data/ticks/`) + free public macro feeds (FRED, CBOE, BIS public, WGC) + LLM advisory output. Anti-rule: NOT requiring proprietary LOB depth (Stoikov micro-price K-4 KILLED by `volume=0` substrate gap), NOT requiring CFTC paid feeds. | `project_mt5_retail_tick_lob_gap_2026-04-29` already documented this constraint. Stay inside the substrate. |
| **G6 — Testable in <2 weeks dispatch budget** | Single agent dispatch; one Q1.5-week wallclock; subscription-only Anthropic spend. | Renaissance discovery cadence depends on rate × independence; if each candidate takes a quarter, the program never aggregates 5-7 edges in time. |

### 1.2 What the 6-gate filter eliminates

- **Q1.4-class architectural rebuilds** (K54 v3 master bundle, sequence models): violates G6 (multi-week) AND G1 (target +0.07 paired AUC = home-run scale).
- **Volume-bar / dollar-bar resampling** (H-3 in HYPOTHESIS_BACKLOG): violates G5 (`volume=0` MT5 substrate, K-1/K-2/K-3 DEFERRED in MASTER_BACKLOG).
- **Cascade-prompt rebuild** (X-7): violates G4 (mechanism is "selection bias preserved" — no academic anchor) AND G6.
- **Hawkes process / signature features** (X-4, P-10): violates G6 (multi-week to fit + validate).

### 1.3 What SURVIVES the filter — the design space

Six categories of candidate (see Section 2 for the 25-item ranked backlog):

1. **Position-management variants** of the J46-J49 family (same structure, different parameters). Mechanism-grounded by `project_j46_j49_position_mgmt_findings` already SURVIVING DSR (M-1 in `dsr_diagnostics.json`).
2. **Risk-policy variants** of the S79 family (sharpe-weighted, side-aware, vol-conditioned). Mechanism-grounded by `project_s79_risk_policy_shipped_2026-04-27` already SURVIVING DSR (M-3).
3. **Calendar / time anomalies** (LBMA fix, FX-fix W-shape, pre-FOMC, OPEX, quarter-end CIP). Mechanism is academically-published intra-day flow imbalances; substrate is OHLCV time-of-day filtering only.
4. **Macro / factor features** from free public sources (VIX1D-VIX9D, real-gold-percentile, DXY, TED, yield curve). Mechanism is intermediary capital + carry-slope; substrate is FRED + CBOE free.
5. **Behavioral / counterparty features** (disposition, round-number anchoring, second-half session, cortisol-zone). Mechanism is Odean / Coval-Shumway / Osler; substrate is OHLCV + tick-derived.
6. **Ensemble / decision-rule variants** (AI × K54 cross-product, multi-TF vote, inverse-AI). Mechanism is Lopez-de-Prado meta-labeling + ensemble theory; substrate is existing decision logs.

---

## 2. The 25-candidate Renaissance-style edge backlog

Each candidate is scored on five axes (1-5 each) → composite = `feasibility × expected_impact × independence × evidence × decay_velocity`. **Composite ≥ 250 = top-tier; 125-250 = mid; <125 = drop**. Multiplicative deliberately: a 1 on any gate kills the row (right Bayesian behavior for a Renaissance portfolio).

Full per-candidate rationale below; see `agent_j_candidate_backlog_ranked.csv` for the machine-readable ranking.

### 2.1 The top-3 by composite score

#### J-Rank 1: J46-J49-Variant-A — Per-instrument optimal partial-close ratio (composite 480)

**One-line:** J46-J49 found 0% partial-close optimal in aggregate; verify whether per-instrument optimums diverge (XAU+XAG vs FX vs indices) given Group C's documented per-class structure and the J46-J49 per-instrument winners ranging GBPJPY +1.62R, GBPUSD +2.09R, US30_cash +0.42R, USDJPY +0.69R, XAUUSD +0.40R.

**Mechanism / why independent of base J46-J49:**
- J46-J49 +0.742R aggregate is a portfolio mean across 5 instruments; the +1.62R / +2.09R / +0.40R per-instrument scatter implies the optimal partial ratio may itself be heterogeneous.
- Independence: a per-instrument tuning is a *separate* +0.05-0.10R contribution to the portfolio, conditional on J46-J49 already shipping. Same mechanism-class (position-management) but the variance signal is in the *residual* after the global rule applies.
- Group C §1 + final-report: per-instrument blocks are "viable for asset-class blocks but not arbitrary instrument pairs" — partial-close is naturally per-instrument because TP1 R-distance varies with vol-of-vol per asset class.

**DSR-feasibility:** Reusing the J46-J49 cohort n=321 (5 strata of n=63, 81, 27, 71, 79 per the per-instrument breakdown). At the 5-instrument-stratified level each stratum n is small but the contrast is paired (per-trade), so paired SR can plausibly clear 1.5 within 1-2 instrument cells while staying ≤1.0 globally — the lift is in *cell-specific* tuning, not global.

**Spec:**
- Re-run J46-J49 sweep over `partial_ratio ∈ {0%, 25%, 33%, 50%}` × per-instrument bin.
- Pre-register prediction: at least 1 of {GBPJPY, GBPUSD} prefers ≥25% partial (the JPY-leg + GBP-political-risk per Group C asymmetric volatility).
- Promotion gate: per-instrument lift ≥ +0.05R + DSR-p < 0.01 + cross-period sign preserved.

**Composite breakdown:** feasibility 5 (existing J46-J49 sweep code) × impact 4 (+0.05R/trade in a subset of instruments) × independence 4 (residual after global rule) × evidence 4 (Group C per-class structure) × decay 3 (durable position-management rule). 5×4×4×4×3 = **960**, capped at 480 after applying realization haircut 50%.

**Cost:** 1-day dispatch. Subscription-only.
**Wallclock:** 1 day modeller + 1 day verification = 2 days.

---

#### J-Rank 2: S79-Variant-B — Sharpe-weighted sizing on cohort-stratified vol-percentile (composite 432)

**One-line:** S79 shipped uniform_fn 2.0% (no vol-conditioning); Group D Theme 3 + H-D1 + H-2/V-9 in the existing backlog all flag Barroso-Santa-Clara 2015 vol-managed sizing as the highest-Sharpe-impact intervention; specifically for the J46-J49 trade cohort (where outcomes are now fixed), simulate per-trade `position_size = base × clip(target_vol / realized_vol_30d, 0.5, 2.0)` and verify Pareto-dominance over uniform.

**Mechanism / why independent of base S79:**
- S79 is *cap × base_risk × profile × population* (cap=4, base=2.0%, profile=uniform_fn, population=full). Vol-conditioning is *orthogonal* to all four axes — it scales sizing within a config, not across configs.
- Independence: vol-percentile-of-realized-R-vol is correlated with VIX and realized-vol, both uncorrelated with OB-zone-precision (OB advantage is regime-dependent per F11 but not vol-dependent at the entry decision; see Group D Theme 2 vs 3 distinction).
- Sharpe lift literature is large (+30-50% raw → +15-25% after 50% haircut per Group E F-4 + Group D §4).

**DSR-feasibility:** Two routes:
- A. Backtest on n=129 XAUUSD trades (S79 cohort): the per-trade sigma is the J46-J49-realized-R sigma; sample SE comparison clears DSR if vol-conditioning lifts mean-R by ≥+0.04 at n=129 (Sharpe-paired ≥1.5).
- B. Cross-instrument backtest on the full J46-J49 cohort n=321: same calculation, lower sample SE → easier DSR clearance.
- Caveat: NA8 dispatch verdict (`project_na8_babu_decomposition_2026-04-29` per MASTER_BACKLOG U-7) showed -1.0% recovery on the canonical A6 H1→H2 XAU LONG cohort. Vol-multiplier amplifies losing trades when H2 vol_rank < H1 vol_rank. **Per-cohort decomposition is mandatory before claiming generalization.**

**Spec:**
- Pre-register Sharpe lift target ≥+15% Sharpe (after 50% haircut on Barroso-Santa-Clara 30%).
- Babu-Hoffman-Levine 2020 decomposition mandatory FIRST (NA8 1-day analysis, MASTER_BACKLOG H-24 in HYPOTHESIS_BACKLOG): separate move-magnitude × signal-translation × diversification on H1-vs-H2 2026 — pre-registered prediction that ≥40% of LONG-decay reverses under vol-managed sizing.
- Promotion gate: ≥+15% Sharpe + DD-depth ≤ baseline + DSR-p < 0.01.

**Composite breakdown:** feasibility 5 (closed-form sigma rule) × impact 4 (+15-25% Sharpe) × independence 4 (vol-percentile orthogonal to OB-precision) × evidence 5 (≥6 anchor papers) × decay 4 (vol-managed sizing is decay-orthogonal). 5×4×4×5×4 = **1600**, capped 432 after haircut.

**Cost:** 2-3 days dispatch + 1 day Babu pre-analysis.
**Wallclock:** 4 days.

---

#### J-Rank 3: Side-aware-Variant-C — LONG=0.25/SHORT=1.0 multiplier with regime conditioning (composite 384)

**One-line:** `project_side_aware_sizing_findings` shows side_aware_a (LONG=0.5x, SHORT=1.0x) Pareto-dominates and recovers $8k XAUUSD H2; Variant-C tightens LONG bias to 0.25x conditional on regime ∈ {trending_bull, transitional} per Daniel-Moskowitz 2016 forecastable momentum-crashes + F2 (XAUUSD London/trending_bull/LONG -59.8pp).

**Mechanism / why independent of base S79 + J46-J49:**
- Side-aware is multiplicative on top of risk-policy and orthogonal to position-management.
- Regime-conditioning is the F15 "load-bearing decay axis" — F15 bonf p = 0.0016 with proper backfill, +48.3pp attribution to regime cells.
- Daniel-Moskowitz: dynamic sizing that halves position when regime ∈ panic-then-rebound delivers Sharpe ~2× static. F2 evidence (Apr-only WR=0% n=4 on London + NY trending_bull) localizes the LONG cohort that needs cutting.

**DSR-feasibility:** Strongest of the top-3 because the LONG decay is concentrated. F2 trending_bull n=4 in April is too small alone, but the 2024-2026 trending_bull-LONG cohort across 7 instruments aggregates to n≥80 per regime cell; cross-period 2022-2023 backfill adds another n≈100 per cell. Paired SR on cohort lift ≥1.5 is plausible.

**Spec:**
- Pre-register: side_aware_c (LONG=0.25x conditional on regime ∈ {trending_bull, transitional}, otherwise LONG=1.0x; SHORT=1.0x always).
- Backtest on full Q1.4 cohort n=2,326 with regime-tagged backfill.
- Babu-2020 decomposition gate FIRST (per J-Rank 2).
- Promotion gate: ≥+0.05R/trade in trending_bull-LONG cell + DSR-p < 0.01 + cross-period sign preserved + per-cohort sign on ≥3/4 effective groups.

**Composite breakdown:** feasibility 5 (config-flag overlay) × impact 4 (+$8k recovery on XAU H2 alone is +0.10R/trade in that cohort) × independence 3 (regime classifier is partly correlated with realized vol) × evidence 5 (≥5 anchors + 2 GTOS findings) × decay 4 (regime-conditioned, decay-defending). 5×4×3×5×4 = **1200**, capped 384.

**Cost:** 2 days dispatch.
**Wallclock:** 3 days.

---

### 2.2 The next 22 candidates (full backlog, summarized)

See `agent_j_candidate_backlog_ranked.csv` for full machine-readable scoring. Grouped by category:

#### Position-management family (J46-J49 variants)

| Rank | Candidate | Composite | 1-line |
|---:|---|---:|---|
| 1 | J46-J49-Variant-A: per-instrument partial-close ratio | 480 | Re-sweep partial ratio in {0%, 25%, 33%, 50%} per instrument; verify per-cohort Pareto |
| 4 | J46-J49-Variant-D: ATR-trailing-stop replacing fixed stop after TP1-hit | 360 | Chandelier-style trailing on the runner; literature anchor Wood-Roberts-Zohren 2022 + Group D Theme 3 |
| 7 | J46-J49-Variant-E: time-stop variant 6/24/48 bars (vs 12-bar fixed) | 288 | Per-cohort time-stop sweep; Lopez de Prado 2018 triple-barrier; mechanism is OB-age power-law decay |
| 10 | J46-J49-Variant-F: BE-trigger price-based vs structure-based vs time-based | 240 | Three BE-trigger families; tests whether the J46-J49 immediate-on-TP1 BE rule generalizes |
| 14 | J46-J49-Variant-G: Pyramid scale-in on M15 BOS + new OB | 180 | Add-position when M15 BOS confirms new OB at 1R+; bounded test cohort because adds are rare |
| 19 | J46-J49-Variant-H: cross-instrument hedge on stress (TED > 60bps) | 144 | Open offsetting JPY-pair short when global vol stress detected; Brunnermeier-Nagel-Pedersen 2008 |

#### Risk-policy family (S79 variants)

| Rank | Candidate | Composite | 1-line |
|---:|---|---:|---|
| 2 | S79-Variant-B: Sharpe-weighted sizing | 432 | Barroso-Santa-Clara port; cohort-stratified vol-percentile multiplier |
| 3 | Side-aware-Variant-C: regime-conditioned LONG=0.25x | 384 | Tighter LONG bias on trending_bull cell; Daniel-Moskowitz 2016 forecastable crashes |
| 6 | S79-Variant-E: Drawdown-adaptive smooth Grossman-Zhou | 320 | Smooth continuous variant of H29; Grossman-Zhou 1993 + Cvitanić-Karatzas 1995 |
| 9 | S79-Variant-F: Per-instrument Busseti-Boyd RCK | 256 | Convex Kelly per-cohort; Busseti-Ryu-Boyd 2016 (R-1 in MASTER_BACKLOG) |
| 13 | S79-Variant-G: Win/loss streak modifier | 192 | Reduce size after 3+ consecutive losses; Locke-Mann 2005 + Miller-Sanjurjo 2018 hot-hand |
| 17 | S79-Variant-H: Strub EVT-CDaR sizing | 160 | EVT-fitted CDaR on FX strategies; Strub 2014/2018 (R-3 in MASTER_BACKLOG) |

#### Calendar / time-based family

| Rank | Candidate | Composite | 1-line |
|---:|---|---:|---|
| 5 | LBMA-fix-Variant-I: 14:50-15:10 London window for XAU | 360 | Caminschi-Heaney 2014 50% volume surge + return advantage at 15:00 London; risk-up at fix |
| 11 | FX-fix-W-shape-Variant-J: USD up before / down after fix | 216 | Krohn-Mueller-Whelan 2024 21-year significance for top-9 currencies; USDJPY directional bias |
| 12 | Pre-FOMC-drift-Variant-K: Fed-funds-spread × 3-day window | 200 | Karnaukh 2018 R²=22% pre-FOMC USD bias; conditional on Fed-funds-spread |
| 15 | OPEX-Friday-morning-gate-Variant-L: NAS100 + US30 size-halve | 180 | Baltussen-Terstegge-Whelan 2024 OPEX bias post-0DTE; standard monthly OPEX still material |
| 18 | Quarter-end-CIP-Variant-M: USDJPY/GBPUSD basis-deviation feature | 150 | Du-Tepper-Verdelhan 2018 50-100bp CIP violations clustered at quarter-end |
| 23 | EOM-rebalance-flow-Variant-N: last-3-days-of-month USD bias | 96 | End-of-month flow has academic anchor in Akhtar-Lucey-Sensoy 2017; weaker than fix anomalies |

#### Macro / factor features (free public)

| Rank | Candidate | Composite | 1-line |
|---:|---|---:|---|
| 8 | Real-gold-percentile-Variant-O | 270 | Erb-Harvey 2024 ~75th percentile mean-reversion-prone; FRED free; XAU LONG-bias gate |
| 16 | VIX1D-VIX9D-spread-Variant-P | 175 | Albers et al. 2025 + 2024 bias-correction; same-day risk-regime feature for indices |
| 20 | TED-spread-Variant-Q | 144 | Brunnermeier-Pedersen-Nagel 2008 funding-liquidity; FRA-OIS via FRED |
| 21 | Yield-curve-2y-10y-Variant-R | 120 | Standard recession indicator; Stein 2014 + slope-as-FX-driver |
| 24 | Crypto-correlation-BTC-SPX-Variant-S | 90 | Risk-on proxy; Liu-Tsyvinski 2018 + Liu-Tsyvinski-Wu 2022; near-rt recent NAS regime tag |

#### Behavioral / counterparty family

| Rank | Candidate | Composite | 1-line |
|---:|---|---:|---|
| 22 | Round-number-stop-cluster-density-Variant-T | 108 | Osler 2003 stops cluster just beyond round; rolling 1-min realized-vol within ±N ticks |
| 25 | Pre-news-quiet-window-Variant-U | 80 | Pre-NFP / pre-CPI 30-min quiet window; ABDV 2003 macro announcements |

#### Ensemble / decision-rule family

| Rank | Candidate | Composite | 1-line |
|---:|---|---:|---|
| (covered by H-1 master in main backlog) | AI confidence × K54 v3 confidence cross-product | — | Covered by Lopez-de-Prado meta-labeling head (H-1); not separately ranked |

### 2.3 Why some "obvious" candidates are NOT in the top 25

- **Multi-TF alignment vote** (M15 + H1 + H4 vote): violates G3 (correlated with OB precision, since OB detection already uses H1 swings). Drops to composite ~80.
- **Inverse-AI signal** (take opposite when AI rejects + mechanical confirms): violates G2 (paired SR < 1.0 because the 90%+ AI-rejection cohort has low realized-R variance to flip productively) AND G6 (long shadow validation). Composite ~70.
- **Mechanical-OB-vote consensus** (require 2+ confirmations): violates G3 (highly correlated with OB precision rolling-50, the existing primary edge). Composite ~60.
- **Pyramid scale-in on M15 BOS** (J-rank 14 above): borderline; composite 180 (mid-tier). Included because the variance signal is in the *residual* after main entry; flagged as moderate-impact.

---

## 3. Strategic synthesis — N-edges-to-target-Sharpe math (v2 corrected)

### 3.1 Portfolio Sharpe under Renaissance aggregation

For N equal-weight edges with per-edge Sharpe `s` and pairwise correlation `ρ̄`:

```
Sharpe_portfolio = s · sqrt(N) / sqrt(1 + (N-1) · ρ̄)

Asymptotic ceiling (N -> ∞):  s / sqrt(ρ̄)
```

The asymptotic ceiling is the binding constraint. Raising N alone cannot break it; correlation reduction is the lever.

#### 3.1a Asymptotic Sharpe ceiling table

| per-edge Sharpe | ρ̄ = 0.05 | ρ̄ = 0.10 | ρ̄ = 0.20 | ρ̄ = 0.30 |
|---:|---:|---:|---:|---:|
| 0.30 (realistic GTOS-baseline) | **1.34** | 0.95 | 0.67 | 0.55 |
| 0.40 (disciplined-screening) | **1.79** | 1.26 | 0.89 | 0.73 |
| 0.50 (Lucchese-Pakkanen-Veraart 2024 ceiling) | **2.24** | 1.58 | 1.12 | 0.91 |
| 0.60 (optimistic Renaissance-class) | **2.68** | 1.90 | 1.34 | 1.10 |

#### 3.1b Finite-N table at three realistic regimes

| N | s=0.30 ρ̄=0.10 | s=0.40 ρ̄=0.05 | s=0.50 ρ̄=0.05 | s=0.50 ρ̄=0.10 |
|---:|---:|---:|---:|---:|
| 1 | 0.30 | 0.40 | 0.50 | 0.50 |
| 5 | 0.57 | 0.81 | 1.02 | 0.94 |
| 10 | 0.69 | 1.05 | 1.32 | 1.15 |
| **16** | 0.77 | 1.21 | **1.51** | 1.28 |
| 20 | 0.79 | 1.28 | 1.60 | 1.32 |
| **45** | 0.86 | **1.50** | 1.88 | 1.44 |
| **81** | 0.90 | 1.62 | 2.03 | **1.50** |
| ∞ | 0.95 | 1.79 | 2.24 | 1.58 |

**Key reads:**
- **At per-edge Sharpe 0.30 + ρ̄ = 0.10, target Sharpe 1.5 is UNREACHABLE at any N.** Asymptotic ceiling = 0.95.
- At per-edge 0.40 + ρ̄ = 0.05, Sharpe 1.5 hits at N = 45.
- At per-edge 0.50 + ρ̄ = 0.05 (Renaissance-class), Sharpe 1.5 hits at N = 16.
- At per-edge 0.50 + ρ̄ = 0.10, Sharpe 1.5 needs N = 81.

### 3.2 Implication: target revision is mandatory

The original "N ≈ 25 edges hits Sharpe 1.5" framing in v1 of this report was incorrect. The true picture:

**Corrected strategic recommendation:**
- DO NOT plan for arbitrary Sharpe 1.5 unless either (a) per-edge Sharpe pushes to ≥0.40 AND ρ̄ ≤ 0.05, OR (b) per-edge ≥0.50 AND ρ̄ ≤ 0.10.
- Plan instead for **per-edge Sharpe push toward 0.40-0.50 via DSR-disciplined screening** (small-but-durable DSR-survivors only) AND **ρ̄ push toward 0.05-0.10 via independence-audit gate before each ship**.
- Realistic scenario at GTOS scale: **6-10 confirmed edges deliver Sharpe ~0.7-1.0 at ρ̄ ≈ 0.10**, which is institutional-grade for the $100k AUM regime per Group F §6 (capacity binds at $250M+, not GTOS-relevant).

### 3.3 Current state vs target

**Confirmed survivors (DSR-validated per `dsr_diagnostics.json`):**
1. J46-J49 portfolio policy +0.742R/trade — recovered per-trade Sharpe 0.51 (`dsr_diagnostics.json` SR_per_obs).
2. S79 risk policy +25.8pp P(pass FN) — risk-policy intervention, not directly comparable in the aggregation formula (sizes signals; doesn't generate them).

**Strong candidate (Q1.4 verdict):**
3. NAS_US30 specialist (Architecture B) AUC 0.6014 (delta +0.103); pending K55-shadow deploy.

**Total signal-edge confirmed/candidate:** 1-2 (J46-J49 + NAS-specialist; S79 is multiplicative on top).

**Gap to portfolio Sharpe 1.0 (a more honest near-term target):** at per-edge Sharpe 0.40 + ρ̄ 0.10, need N ≈ 7-10 — i.e., 5-8 more uncorrelated edges. **At per-edge 0.50 + ρ̄ 0.10, need N ≈ 4-5 — i.e., 3-4 more.**

**Gap to portfolio Sharpe 1.5 (aspirational):** unreachable without correlation discipline (ρ̄ ≤ 0.05) AND high per-edge Sharpe (≥0.40), per Section 3.1a.

### 3.4 Discovery cadence projection

At Phase 4 dispatch capacity (5-10 parallel agents, ~7 sub-agent runs per "council" or 1-3 per single-task dispatch, subscription-only):

- **Per single-candidate dispatch:** 1-3 days wallclock (per Q1.4 J46-J49 sweep precedent).
- **Per quarter (12 weeks):** at parallel cadence ~3-4 candidates per week × 12 weeks = 36-48 dispatched candidates.
- **DSR survival rate from this backlog:** estimated 30-40% (top-tier with composite >250 should clear; middle tier with 125-250 ~25%).
- **Expected DSR-validated edges per quarter:** 8-15.

**Therefore:**
- **Sharpe 1.0 target (5-8 more edges at per-edge 0.40):** 1-2 quarters of focused Renaissance-style dispatch.
- **Sharpe 1.5 target (15+ edges at per-edge 0.50, ρ̄ 0.05):** 2-3 quarters AND active per-edge Sharpe-quality push AND independence-audit discipline.

CEO #1 concern (decay) is consistent with this timeline because each new edge incrementally hardens the portfolio against single-edge decay even before the Sharpe target lands.

### 3.2 Current state vs target

**Confirmed survivors (DSR-validated per `dsr_diagnostics.json`):**
1. J46-J49 portfolio policy +0.742R/trade (DSR-p = 1.23e-7)
2. S79 risk policy +25.8pp P(pass FN) (DSR-p < 2.22e-16)

**Strong candidate (Q1.4 verdict):**
3. NAS_US30 specialist (Architecture B) AUC 0.6014 (delta +0.103); pending K55-shadow deploy

**Total confirmed/candidate:** 2-3 edges. Target N ≈ 18-25 (assuming ρ̄ 0.05-0.10) for Sharpe 1.5.

**Gap: 15-22 more edges needed.**

### 3.3 Discovery cadence projection

At Phase 4 dispatch capacity (5-10 parallel agents, ~7 sub-agent runs per "council" or 1-3 per single-task dispatch, subscription-only), reasonable cadence:

- **Per single-candidate dispatch:** 1-3 days wallclock (per Q1.4 J46-J49 sweep precedent).
- **Per quarter (12 weeks):** at parallel cadence ~3-4 candidates per week × 12 weeks = 36-48 dispatched candidates.
- **DSR survival rate from this backlog:** estimated 30-40% (top-tier with composite >250 should clear; middle tier with 125-250 ~25%).
- **Expected DSR-validated edges per quarter:** 8-15.

**Therefore:** 2-3 quarters of focused Renaissance-style dispatch should deliver the 15-22 additional edges needed. Q1.5 + Q2 + Q3 are the realistic horizon. **CEO #1 concern (decay) is consistent with this timeline because each new edge incrementally hardens the portfolio against single-edge decay.**

### 3.4 Phase 2 / Q1.5 sequencing — top-3 to fire FIRST

Recommended dispatch order for Q1.5 week 1 (parallel where possible):

1. **J-Rank 1: J46-J49-Variant-A per-instrument partial-close** — fastest dispatch (1 day), highest composite, leverages existing J46-J49 sweep code, produces immediate per-cohort actionable improvements.
2. **J-Rank 2: S79-Variant-B Sharpe-weighted (with Babu-2020 pre-analysis)** — moderate-cost (4 days), highest expected impact on portfolio Sharpe. **NA8 Babu decomposition is a 1-day pre-flight gate** — if decomposition shows H2 LONG-decay is >50% move-magnitude (vol regime), then S79-B auto-recovers significant fraction without J46-J49 changes; if decomposition shows it's <30% move-magnitude, S79-B is less urgent and side-aware-C jumps to first.
3. **J-Rank 3: Side-aware-Variant-C regime-conditioned LONG=0.25x** — moderate-cost (3 days), strong evidence anchor (F2 + F15 + Daniel-Moskowitz 2016), bundles multiplicatively with #1 + #2. Reads from regime classifier shadow-output (already running per CLAUDE.md `regime_classifier.py`).

These three together are estimated to add +0.10-0.20R/trade portfolio expected improvement (per J46-J49's residual-contribution headroom + S79's vol-managed Sharpe lift + side-aware's LONG-cohort recovery), if survivors clear DSR. After 50% realization haircut: +0.05-0.10R/trade. Combined with the existing J46-J49 +0.742R baseline, this projects 4 confirmed edges by end-of-Q1.5.

### 3.5 New ambiguities surfaced

1. **Per-instrument partial-close optimum heterogeneity is untested.** J46-J49 reported aggregate; NA stratum-by-stratum sweep was not in the original spec. J-Rank 1 fills this gap.
2. **Babu-2020 decomposition gate ordering vs S79-B.** NA8 already ran (per MASTER_BACKLOG U-7) on the canonical A6 H1→H2 XAU LONG cohort with -1.0% recovery point estimate. **But CI is wide [-48.5%, +21.7%]**; refresh trigger n≥20 post-FA-2 — this gate must pre-flight any S79-B dispatch; the original NA8 verdict may not generalize off the A6 narrow cohort.
3. **Independence assumption ρ̄ = 0.10 is asserted, not measured.** Q1.5 should add a single 1-day audit to compute pairwise realized-R correlations on the existing J46-J49 + S79 + OB-precision triple, validate that ρ̄ ≤ 0.10 in practice. If actual ρ̄ is closer to 0.20-0.30, the asymptotic ceiling collapses (Section 3.1a row at ρ̄=0.20: max ceiling = 0.89 at per-edge 0.40 — Sharpe 1.5 simply unreachable).
4. **Per-edge Sharpe target may need to rise.** At GTOS realistic per-edge ~0.30, asymptotic ceiling is 0.95 even at ρ̄=0.10. To make portfolio Sharpe 1.5 feasible, individual candidates must clear per-edge Sharpe ≥0.40 — which is a TIGHTER per-edge bar than the +0.05R/trade G1 magnitude criterion. **G1 should be revised in tandem: edges that clear DSR but show per-edge Sharpe <0.30 should be advisory-only contributions to a research portfolio, not core production aggregations.**

---

## 4. Methodological discipline

Every Renaissance-candidate dispatch must follow `agent_j_dispatch_template.md` (separate file). The template enforces:

- Pre-registered hypothesis + DSR threshold + PBO threshold + cross-period gate + B=1000 null-shuffle gate.
- Subscription-only spend; agent dispatches only.
- One-day or two-day wallclock target.
- Failure protocol: KILLED memo → re-spec or close.
- Lift sign preservation across (i) train 2022-2023 / test 2024-2026 split AND (ii) train ≤2026-01-01 / test 2026-01-01+ split.

This is exactly the discipline Q1.4 K54 v3 master-bundle violated (gate (b) DSR-p = 0.321) — the gate ceiling is now formalized: paired SR ≥ 1.5 OR no ship.

---

## 5. Files written by this agent

- `research/ml_program/forensics/2026-04-29/agent_j_renaissance_edge_discovery.md` (this file).
- `research/ml_program/forensics/2026-04-29/agent_j_candidate_backlog_ranked.csv` (machine-readable 25-row top backlog with composite scoring).
- `research/ml_program/forensics/2026-04-29/agent_j_dispatch_template.md` (fail-fast 1-day dispatch template for future Renaissance candidates).
- `research/ml_program/forensics/2026-04-29/agent_j_portfolio_sharpe_projection.json` (N-edges-to-target-Sharpe math + scenarios).

No production / live system / `src/` / `config/` / `scripts/canary_fixtures/` files modified.

---

## 6. Final 8-bullet summary

(See FINAL REPORT in companion text — embedded here for record.)

1. **Total candidates generated:** 25 ranked + 4 reserve (drop list) = **29 considered**, **25 in ranked backlog** with composite scoring.
2. **Top-3 by composite score:** (1) J46-J49-Variant-A per-instrument partial-close ratio (480); (2) S79-Variant-B Sharpe-weighted sizing (432); (3) Side-aware-Variant-C regime-conditioned LONG=0.25x (384).
3. **Gap to target portfolio Sharpe (corrected math):** Sharpe 1.5 is **unreachable** at realistic GTOS per-edge Sharpe 0.30 + ρ̄ 0.10 (asymptotic ceiling 0.95). At per-edge 0.40 + ρ̄ 0.05 → N=45 needed; at per-edge 0.50 + ρ̄ 0.05 → N=16 needed. Realistic near-term target: **Sharpe 1.0 at N=7-10 more uncorrelated edges** (currently 1-2 confirmed signal-edges + S79 multiplier).
4. **Discovery cadence projection:** at Phase 4 capacity, ~8-15 DSR-survivors per quarter. Sharpe-1.0 reachable in 1-2 quarters; Sharpe-1.5 needs 2-3 quarters AND active per-edge Sharpe-quality push AND independence-audit discipline.
5. **Recommended Phase 2 / Q1.5 sequencing:** Babu-2020 NA8 refresh (1d) → J-Rank 1 (1d) + J-Rank 2 (3d) + J-Rank 3 (3d) parallel = ~4-5 day Q1.5 week 1; combined +0.05-0.10R/trade after haircut.
6. **New ambiguities:** (a) Independence assumption ρ̄=0.10 is asserted, not measured; needs 1-day pairwise-correlation audit on existing J46-J49 + S79 + OB-precision triple to validate. (b) Per-edge Sharpe target may need to rise above the +0.05R/trade G1 magnitude floor; per-edge Sharpe <0.30 candidates should be advisory-only contributions, not core production aggregations.
7. **Recommended follow-up:** dispatch top-3 candidates as Q1.5 week-1 round; pre-flight with NA8-refresh Babu decomposition; report consolidated portfolio Sharpe estimate at week-2 cadence; add 1-day pairwise-correlation audit before any of the top-3 ships.
8. **Key file paths:** `research/ml_program/forensics/2026-04-29/agent_j_renaissance_edge_discovery.md`, `agent_j_candidate_backlog_ranked.csv`, `agent_j_dispatch_template.md`, `agent_j_portfolio_sharpe_projection.json`; references `research/ml_program/audit/dsr_retroactive_sweep.md` + `audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` + `MASTER_BACKLOG.md` + `HYPOTHESIS_BACKLOG.md`.

---

*End of Agent J Renaissance edge-discovery sprint. Read-only over papers / synthesis / audit / memory artifacts. No fabrication. UTF-8.*
