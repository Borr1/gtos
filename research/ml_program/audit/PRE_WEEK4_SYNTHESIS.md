# Pre-Week-4 Synthesis — K54 v2 Q1 Ambiguity Audits

**Built:** 2026-04-28 (5 Opus 4.7 + max-effort audits closed)
**Scope:** Resolve all open ambiguities flagged in the post-Week-3 reflection so the Week-4 modeler dispatches with full operational + statistical clarity.

---

## TL;DR

- 5 of 5 audits done; all subscription-only; total wallclock ~16 min (parallel).
- **Catalog has signal.** Joint-model scout: test AUC = 0.6544 on burned ballpark (n=88), z=4.29σ vs white-noise null. AUC ≥0.61 already exceeded by tiny global LightGBM with defaults.
- **4 program-level adjustments recommended before Week 4 modeler dispatch.**
- **3 CEO decisions pending** (Q1.3 re-spec; modeler dispatch authorization; production-ops `_trade_index.json` ticket).

---

## Section 0 — Operational context from main thread (integrate)

Five facts surfaced by the main session that materially affect Q1 training-data filters. **Don't auto-investigate; bake into Week-4 modeler brief.**

| # | Fact | K54 v2 implication |
|---|---|---|
| 1 | **A4 verdict on XAUUSD trending_bull = GREEN.** n=11 M1 sim: mean realized R +0.818R, WR 72.7%, sum +9.00R after FA-2 prompt fix. The "regime-conditioned LONG-side selectivity collapse" framing (F2/F15) was *substantially* a pre-FA-2 SL buffer bug masquerading as selectivity drift. | **Refines the program's strategic framing.** AI's setup selection on the XAUUSD trending_bull cohort is fine — ML competes with an already-recovering baseline on this cell. **Cross-period (2022-2025) replication is the actual open test**, not the trending_bull cell. |
| 2 | **F27 prompt-injection feedback: NULL on decisions, CHANNEL_PARTIAL on confidence.** Confidence aggregator asymmetric — positive telemetry dead, negative telemetry deflates by ~4 points (caps at 72). Per memory `project_b12_confidence_autopsy_2026-04-26`, 98% live CANDs emit confidence=80 (rubber stamp). | **If `ai_confidence` enters K54 v2 via cross-source training, treat as bimodal categorical, not fine-grained continuous.** Our 6-family catalog does NOT include `ai_confidence` (catalog is pure market state); this caveat applies if Week-4 modeler joins K54 v1's 17 features for ablation. |
| 3 | **Multi-framework dispatch suppression bug — FIXED** (commit < 41b4a59). Pre-fix, AI was prompt-biased into `framework=ob_retest` even when `frameworks_evaluated.fvg_fill.qualified=true`. | **`analysis.framework` (wrapper-level) is unreliable on ALL pre-2026-04-28 ~05:00 UTC data.** For training, prefer `analysis.frameworks_evaluated.<X>.qualified` flags + `analysis.reasoning.h1_setup.poi_type`. K54 v1's `framework` feature had ZERO importance, so dropping it costs nothing; dropping it from any v2 derivative is mandatory. |
| 4 | **sl_beyond_ob precision class — FULLY CLOSED** (5-site fix, commit `70d93d8`, 2026-04-28). Pre-fix, 6 of 7 instruments had `market.tick_size` missing → L2 floor was 1e-5. | **L2 PASS/FAIL outcome on pre-fix data has a deterministic-bug-class component.** Records with `sl_buffer_applied=0.0` are bug-rejections, not setup-quality rejections. Q1 K54 v2 catalog uses realized R (not L2 outcome) as label, so unaffected. **Becomes load-bearing at K54 v3 if AI-side L2-derived features are introduced.** |
| 5 | **Broker offset bug — FIXED** (commit `5c66ee8`, 2026-04-28). FN-Server-2 is UTC+3; pre-fix tick.time was off +10800s, treated as future-dated, rejected. Tick capture daemons died every 15 min since FN switch (2026-04-27). | **Historical tick parquet data 2026-04-27 → 2026-04-28 ~05:16 UTC is missing.** Pre-FN switch tick parquets (FTMO UTC+0) are clean. Reinforces audit Microstructure caveat — 24 tick-required features remain `stability_n=0` for 5 of 7 instruments; treat as secondary at K54 v2 (re-evaluate at K54 v3). |

---

## Section 1 — Per-audit summary

### 1.1 Catalog Health (`audit/catalog_health_audit.md`)

- **Composability: PASS.** All 6 modules join on ISO-UTC candle-close. Zero name collisions, zero within-family duplicates. Two caveats: Time/Session is per-instrument-conditional (XAUUSD 126 features; JPY pairs 138 incl. Tokyo) — modeler must use 138-column union schema with NaN sentinel; heterogeneous call signatures (Liquidity needs `current_price`; Microstructure needs M1 frame; Regime needs `RegimeFeatureContext`) → ~30-LOC adapter required.
- **Redundancy: 1,852 cross-family pairs ≥0.7, 52 ≥0.9.** Two genuine cross-family duplications:
  - **(A)** `regime__regime_atr_h4_14` ≡ Volatility ATR/Parkinson/realized-vol cluster (14+ pairs ≥0.94).
  - **(B)** `microstructure__fvg_*_count_h4_lb*` ≡ `structure__H4__fvg_*_count__lb*` (~12 pairs ≥0.94).
  - **Recommended: prune at |ρ|≥0.95 Spearman.** Drop regime-side raw ATR (keep ratio variants), drop microstructure-side H4 FVG counts.
- **Integrity: PASS_WITH_NOTE.** 1,219 rows + 11 canonical columns + 0 dup names. 5 regime rows carry literal `"NA"` in `stability_rho`; one-line fix in `build_catalog_v2.py`.
- **Inference cost: 1,644 ms median total. Volatility 1,134 ms (69%); Microstructure 484 ms (29%) — together 99%.** Production M15-close cadence (28 decisions/hour fleet-wide, 1.25% CPU) is fine. **350k-row training-backfill = 156 hr single-thread; parallelize per-instrument 7-way → ~22 hr.**
- **Top surprise:** Regime family duplicates Volatility's H4 ATR exactly (+0.97 Pearson on raw values). Catalog Section 4.C predicted redundancy; magnitude (≥0.94 across 14+ pairs) means the regime family is silently overweight in any L1-style model.

### 1.2 Data Inventory (`audit/data_inventory_audit.md`)

- **Per-instrument coverage:** All 28 (instrument × TF) cells populated. M15 — XAUUSD/XAGUSD/USDJPY/GBPUSD/NAS100 from 2024 (~50k bars); GBPJPY from 2022-03 (101k); US30_cash from 2022-01 (101k). Gap density ~0.2-0.5% (normal weekend/holiday).
- **Cross-period replication: feasible on 2/7 instruments for true 3-period (only GBPJPY + US30_cash have pre-2024 M15); 7/7 for train-2024-2025/test-2026 only.** **The K54 v1 audit's claim that pre-2024 has only XAUUSD/GBPUSD coverage was wrong-by-sign** — opposite is true.
- **Per-cell n: 22 of 28 (instrument × regime) cells fail n≥30.** Only viable: XAUUSD UNTAGGED 129, XAUUSD bullish 39, USDJPY bullish 38, US30_cash UNTAGGED 66. **Per-(instrument, regime) ensemble is statistically unworkable; pooled cross-instrument with regime-as-feature is the only viable architecture.**
- **D1 MTF rescue: pooled cross-instrument RESCUED; per-XAU STILL-SATURATED.** XAU 2026 D1 = 60/35/5%; XAU 2022-2023 D1 = 36.7/36.7/26.6% — healthy variance. GBPUSD/GBPJPY/USDJPY 2026 cohorts have 33-44% neutral.
- **Top surprise:** **K54 v1 brief's "411 trades" is wrong.** Actual `features.csv` has 582 rows (439 F11 + 33 trade_index + 110 unified_csv). 5 of 7 non-XAU/non-GBPUSD instruments are 100% F11 mechanical (zero AI-graded trades) → K54 v2 cannot test ML-vs-AI on them.

### 1.3 Joint-Model Scout (`scout/joint_model_scout.md`)

- **Effective n after tuple-keyed dedup: 528** (406 F11 + 89 unified_csv + 33 trade_index). Collapsed 54 from K54 v1's 582 — confirms K54 v1 dedup bug.
- **Test AUC = 0.6544** on BURNED ballpark (n=88, 2026-04-01 → 2026-04-28). Holdout 2026-04-29+ never touched (verified: max train date 2026-04-24 18:00 UTC).
- **Null distribution (B=10):** mean 0.495, std 0.037, max 0.549. Real beats null max by +0.106; **z=4.29σ.** (B=1000 should be re-run per methodology critic for tighter null.)
- **Per-regime ensemble DRAGS:** AUC 0.579 (vs global-only 0.654, **−0.075pp**) at smallest=21 train rows. **Confirms "regime-as-feature in global LightGBM" architecture for K54 v2** (matches Data Inventory's "22/28 cells fail n≥30").
- **Top global-gain features:**
  1. `vol__h1_range_over_mean_50` — gain 89, ρ=+0.136
  2. `micro__last_bar_body_ratio_h4` — gain 55, ρ=+0.075
  3. `vol__m15_sq_return_autocorr_lag5_w50` — gain 55, ρ=+0.087
  4. `micro__synthetic_footprint_imb_m1_last_480min` — gain 54, ρ=−0.015 (interaction signal!)
  5. `struct__M15__nearest_fvg_age_bars__lb20` — gain 50, ρ=+0.101
- **Top surprise:** **Catalog's univariate top-1 `H1__impulse_max_displacement_ratio` (ρ=+0.266) did NOT make top-30 global gain** — 51% NaN density penalizes it under tree splits. Same for the XAU-only round-number features. **K54 v2 modeler must NOT feature-prune by univariate ρ.**
- **Verdict:** Catalog has signal (yes); AUC ≥0.61 plausible at Week 4 (yes — already exceeded).

### 1.4 Live OOS + Bug Hunt (`audit/live_oos_and_bug_hunt.md`)

- **OOS holdout n estimate: ~50-100 filled trades** (~7-12 CANDIDATEs/day fleet-wide × ~50% conversion). AUC SE @ n=100 ≈ 0.058 — z=1.03 (p=0.15) for 0.61-vs-0.55 → **still cannot reliably discriminate at the threshold.** Reinforces methodology critic's "drop holdout as numeric gate."
- **Live evaluations NOT usable as training data.** 139 CANDIDATEs in `live_evaluations/` 2026-04-13..28 have full MSO snapshot but NO realized R; trade_records 159/159 (100%) `execution: null` in April. Modeler stuck with K54 v1's pre-extracted 528 rows until OHLCV-replay backfill.
- **Stability-scorer dedup bugs found in 2 modules:**
  - **Volatility:** PARTIAL (`(symbol, ts)` dedup leaves ~29/496 rows ~6% double-weighted from F11↔trade_index/unified collisions).
  - **Time/Session:** FULL (`_compute_stability.py:132` `all_recs = f11 + ti` — no dedup at all).
  - Pure feature-extractor modules CLEAN. Structure/Liquidity/Microstructure scorers F11-only CLEAN.
  - **Fix: tuple-keyed `(date, symbol, round(realized_r, 3))` dedup.**
- **Precision mismatch** affects same 2 modules. F11 ts = bos_time (precise); trade_index/unified ts = `date + KZ_HOUR` (snap to 8/14/1 UTC). 27% of time_session cohort artificially concentrates at KZ-default hours. **Fix: per-source weighting (F11=1.0, trade_index/unified=0.5)** + precision-pure column for hour-sensitive features.
- **Top surprise:** **`knowledge_base/index/_trade_index.json` is FROZEN at 2026-04-04.** `KnowledgeBase.update_trade_index` never fires because live writes to `trade_records/` instead of `trades/`. 24-day-stale snapshot. Operational bug — affects K54 v2 only marginally (training pop = K54 v1's pre-extracted) but is a production-ops issue worth a separate ticket.

### 1.5 Methodology Critic (`audit/methodology_critique.md`)

- **CPCV gate (a) — SOUND with 2 caveats.** Realistic ensemble SE ≈ 0.04-0.05 (not 0.024 — paths share data, not independent). Gate can prove "K54 v2 beats random" at ~85-90% power but **cannot prove "beats K54 v1 by ≥0.04 AUC"** without paired-comparison structure (DeLong / paired bootstrap). Per-fold feature selection mandatory at 1,219 features / 350 rows = 0.3 rows/feature.
- **Holdout gate (b) — DROP as primary numeric gate; KEEP as discipline check.** At n=8 (or n=100), AUC SE = 0.21 (or 0.058); power vs null ~12% (or ~35%); power vs K54 v1 baseline <5% in both cases.
- **Cross-instrument threshold — CHANGE.** Per-instrument n=54-191 means AUC≥0.61 unmeasurable on 6 of 7. Recommend: "AUC_v2 > AUC_v1 sign-of-lift on ≥3 of 5 effective-independent groups {XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY, residual}, n ≥ 30 floor."
- **White-noise null — RE-TUNE** to B=1000 (Phipson & Smyth 2010). B=100 is at α=0.01 boundary with zero margin.
- **Top alternative methodology to add: PBO (Bailey & López de Prado 2014)** — directly tests overfit risk under feature/hyperparam selection. ~30 min CPU. Subscription-bounded. High-leverage at 1,219 features ÷ 350 rows.
- **Q1.3 re-spec — YES** (Path B: Q1.3 supersedes Q1.2 gate (b); preserves pre-registration discipline).

---

## Section 2 — How orientation has changed

| Before audits | After audits |
|---|---|
| Univariate ρ ceiling 0.266 → joint AUC unknown | Joint AUC = 0.654 on burned ballpark; signal exists at z=4.29σ |
| Per-regime LightGBM ensemble (K54 v1 carry-forward) | **Regime-as-feature in global LightGBM** (per-regime drags −0.075pp at this n) |
| Training population = 411 trades | **Training population = 528 trades** (post tuple-keyed dedup; was 582 pre-dedup) |
| Cross-period replication on 7 instruments | **2 of 7 for true 3-period** (GBPJPY + US30_cash only); 7/7 for train-2024-2025/test-2026 |
| OOS holdout SE = 0.18 → toothless | OOS holdout n = 50-100, SE = 0.058 → **still toothless for AUC≥0.61 vs 0.55**; **drop as numeric gate** |
| 14-day prospective gate is statistically empty | Replace with directional + calibration discipline check (Q1.3) |
| Methodology adequate | Add PBO; tune null B=1000; paired-comparison structure (DeLong); cross-instrument threshold change |
| 1,219 features all retained | Catalog is healthy (compose PASS, integrity PASS_WITH_NOTE); **prune ~26 features at |ρ|≥0.95** (regime ATR raw + micro H4 FVG counts) |
| Stability scorer bugs unknown | 2 modules buggy (Volatility partial, Time/Session full); pure feature extractors clean |
| Live data may help | Live data NOT usable for training (no realized R); modeler is stuck with 528 rows |
| Confidence as fine-grained feature | If used (it isn't in Q1 catalog): treat as bimodal (op-context #2) |
| `analysis.framework` reliable | UNRELIABLE pre-2026-04-28 ~05:00 UTC (op-context #3) |
| Inference 1ms target enforced | Production-inline OK at 1.25% CPU; **training-backfill needs 7-way per-instrument parallelization** (156h → 22h) |

---

## Section 3 — Pending CEO decisions

### Decision #1 — Approve Q1.3 re-spec (RECOMMENDED YES)

The Q1.2 numeric AUC ≥0.61 holdout gate is statistically toothless at the available n. Append Q1.3 to the registry per Path B in `methodology_critique.md` §6.3. Q1.2 stays as a historical entry; Q1.3 supersedes its gate (b) and tightens (a, c, d, e). **Proposed text in Section 4 below.**

### Decision #2 — Authorize Week 4 modeler dispatch

Once Q1.3 is locked (or Q1.2 is reconfirmed if you reject Q1.3), I dispatch the Week 4 modeler agent on Opus 4.7 + max effort, with the operational changes from Section 2 baked into the prompt. Subscription-only; no API spend.

### Decision #3 — Production-ops ticket for `_trade_index.json`

`KnowledgeBase.update_trade_index` never fires because live writes to `trade_records/` instead of `trades/`. The trade index has been frozen at 2026-04-04 since FN go-live. Affects all stability scorers + live monitors that read it. **Not a Q1 K54 v2 blocker** (training pop is pre-extracted) but is a production-ops issue. Recommend opening a separate ticket on the main thread; out of scope for the ML program.

---

## Section 4 — Proposed Q1.3 re-spec (verbatim from `methodology_critique.md` §6.2)

> ## Q1.3 — K54 v2 expanded feature catalog (PRIMARY, supersedes Q1.2 gate (b) per methodology critique)
>
> - **Date pre-registered:** [TBD by orchestrator after CEO review]
> - **Pre-registered by:** ML Program Orchestrator (post-methodology-critique re-spec)
> - **Phase:** Q1 — Foundation: data + features + K54 v2
> - **Hypothesis:** *"An expanded 1,219-feature catalog (vs K54 v1's 17) lifts a per-regime LightGBM's AUC by ≥0.04, from K54 v1's baseline of 0.571 to ≥0.61, when validated via combinatorial-purged CV (K=6, N=2; 15 paths) with explicit purge gaps ≥1 week and embargo ≥1 day, on training data from 2024-02-20 → 2026-04-28. AUC measurement is paired (v2 vs v1 on identical CPCV folds), with PBO < 0.5 to confirm non-overfitting. A 14-day prospective holdout window 2026-04-29 → 2026-05-12 serves as a directional-discipline check (sign of lift, calibration retention, no per-instrument sign-flip), NOT as a numeric AUC gate."*
> - **Thresholds (ALL required):**
>   - **(a) CPCV paired:** mean(AUC_v2 − AUC_v1) ≥ 0.04 AND DeLong p < 0.01 across 15 CPCV paths.
>   - **(b) PBO:** Probability of Backtest Overfitting < 0.5 over hyperparameter selection grid.
>   - **(c) Holdout discipline:** Holdout AUC > 0.50 AND Holdout Brier ≤ 1.20× CPCV Brier AND Holdout (AUC_v2 − AUC_v1_paired) > 0.
>   - **(d) Cross-instrument:** AUC_v2 > AUC_v1 on at least 3 of 5 effective-independent instrument groups {XAU+XAG, NAS100+US30, GBPJPY, GBPUSD+USDJPY, residual}, with per-group n ≥ 30.
>   - **(e) White-noise null:** B=1000 shuffles, observed AUC ≥ permutation p<0.01 boundary with margin.
> - **Holdout date range:** 2026-04-29 → 2026-05-12 (inherited from Q1.2 lock).
> - **Holdout LOCKED:** YES (inherited).
> - **Holdout opened:** NO.
> - **Result:** PENDING.
> - **Audit trail link:** `research/ml_program/audit/methodology_critique.md`.
>
> **Differences from Q1.2:** (1) Gate (b) numeric AUC ≥ 0.61 replaced with directional + calibration discipline check. (2) CPCV explicitly N=2 (15 paths). (3) PBO added. (4) Cross-instrument re-grouped to effective-independent. (5) White-noise null B=100 → B=1000.

---

## Section 5 — Recommended Week 4 modeler dispatch brief

If Decisions #1 + #2 are approved, the Week 4 modeler agent should receive:

1. **Architecture: regime-as-feature in global LightGBM.** Per-regime ensemble drags at this n (audit verdict). Optionally raise per-regime min-rows ≥60 before fragmenting; otherwise stay global.
2. **Training population: 528 rows** (post tuple-keyed dedup `(date, symbol, direction, framework, realized_r)`). Use the scout's `feature_matrix.parquet` directly.
3. **Feature set: 1,193 features** (1,219 minus 26 high-redundancy candidates at |ρ|≥0.95: drop regime-side raw ATR, drop microstructure-side H4 FVG counts).
4. **Methodology: per Q1.3** — paired CPCV (DeLong, K=6/N=2/15 paths), per-fold feature selection, PBO, B=1000 null, cross-instrument by 5 effective groups.
5. **Pre-modeler patches required (cheap fixes):**
   - Volatility stability scorer: tuple-keyed dedup (~10 LOC fix).
   - Time/Session stability scorer: tuple-keyed dedup (~10 LOC fix).
   - `build_catalog_v2.py`: convert 5 regime "NA" entries to empty (~3 LOC).
   - Volatility + Time/Session: per-source weighting (F11=1.0, trade_index/unified=0.5).
6. **Training-backfill parallelization:** 7-way per-instrument processing (156h → 22h projected).
7. **Operational filters from Section 0:**
   - Drop `analysis.framework` from any cross-source data; use `frameworks_evaluated.X.qualified` instead.
   - Filter `sl_buffer_applied=0.0` records out of any L2-outcome features (none in Q1 catalog; precaution for K54 v3).
   - Don't expect tick parquet data in 2026-04-27 → ~2026-04-28 05:16 UTC window.
   - If joining K54 v1's 17 features for ablation, treat `ai_confidence` as bimodal categorical.
8. **Output:** `research/ml_program/models/k54_v2/` — `meta.json`, `regime_*.lgb` (or `global.lgb` if pure global), `cpcv_results.json`, `pbo_results.json`, `null_distribution.json`, `cross_instrument_results.json`.
9. **Holdout discipline:** Strictly never read 2026-04-29 → 2026-05-12 data.
10. **Subscription-bounded; no API spend.**

---

## Section 6 — File map

```
research/ml_program/audit/
├── PRE_WEEK4_SYNTHESIS.md           # this document
├── catalog_health_audit.md          # 1.1
├── data_inventory_audit.md          # 1.2
├── live_oos_and_bug_hunt.md         # 1.4
├── methodology_critique.md          # 1.5
└── (auxiliary CSVs + driver scripts per audit)

research/ml_program/scout/
├── joint_model_scout.md             # 1.3
├── feature_matrix.parquet           # 528 × 1,247 (catalog 1,219 + 28 liq round-number variants)
├── feature_matrix_meta.json
├── scout_results.json
├── build_scout_matrix.py
└── scout_model.py

research/ml_program/feature_catalogs/
├── CATALOG_v2.md                    # Week 2-3 close synthesis
├── CATALOG_v2.csv                   # 1,219 unified rows
└── {family}.{md,csv}                # per-family
```

---

*Standing by for Decision #1 (Q1.3 approval) and Decision #2 (Week 4 modeler authorization).*
