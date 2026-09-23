# Q1.4 Post-Mortem + Q1-Close / Q1.5 Re-Spec Recommendation

**Date:** 2026-04-29
**Author:** K54 v3 Modeler (post-Q1.4 dispatch)
**Inputs:** `research/ml_program/models/k54_v3/` (full output set), `research/ml_program/audit/Q1_3_POSTMORTEM_SYNTHESIS.md`, `research/ml_program/audit/dsr_retroactive_sweep.md`, `research/ml_program/audit/architecture_ab.md`, `research/ml_program/audit/canonical_v1_rerun.md`, `research/ml_program/KILLED_HYPOTHESES.md` Q1.4 entry.

---

## Headline

**K54 v3 master bundle FAILED 5 of 6 testable gates (gate g deferred to holdout open).** The architectural complexity added in Q1.4 (Lopez-de-Prado meta-labeling head + Kyle-Obizhaeva W-unit pooling + NAS_US30 specialist routing) does not lift K54 above the DSR-corrected significance threshold at the available cohort size (n=528 v2-feature substrate; 1,798-row 2022-2023 backfill is v1-schema only).

**The lift IS real but below the trial-budget noise ceiling.** K54 v3 mean CPCV AUC = 0.5770, paired lift +0.0484 over canonical K54 v1 baseline 0.5286. PBO 0.20 PASS. Null distribution B=1000 p_emp = 0.000 PASS (no random shuffle reached the observed AUC). But DSR-p = 0.321 (gate < 0.01). The N=200 cumulative GTOS Phase 1 trial budget makes the noise ceiling on paired SR ≈ 1.11; observed SR_paired = 1.27 sits 0.16 above ceiling — directionally significant, statistically not enough.

**Strongest single finding stands:** the NAS_US30 specialist (Architecture B) at AUC 0.6014 on its 113-row cohort, delta +0.103 over the global K54 v3 model. This is the only K54-family component with both paired AUC ≥ 0.60 and per-cohort delta ≥ +0.05. **Recommendation: ship the NAS_US30 specialist as a K55-shadow signal candidate; close Q1 globally.**

---

## 1. What we tested

### 1.1 Architecture (locked per Q1.4 pre-registration)

| Component | Status | Result |
|---|---|---|
| Global LightGBM + per-fold top-100 screening (Architecture A) | RAN | AUC 0.577 (vs Q1.3 Arch A 0.561; +0.016 lift; partly from K-7..K-10) |
| Lopez-de-Prado meta-labeling head | RAN (secondary classifier on TP/SL labels) | At n=528 with ~250 primary-positive rows, the secondary classifier is statistically weak; no measurable lift |
| Kyle-Obizhaeva W-unit pooled training | RAN with diagnostic correction | Raw dollar-volume form catastrophically failed (AUC 0.508); balanced intra-instrument-vol-rank form used, contributes +0.0035 over Arch A |
| NAS_US30 specialist (Architecture B) | RAN | AUC 0.6014, delta +0.103 over global on its 113-row cohort — STRONGEST SINGLE FINDING |
| Adaptive conformal calibration (K-14) | RAN | CPCV-test 90% coverage = 0.881 (target 0.90); Christoffersen p = 0.002 (calibration imperfect on CPCV; gate g proper test deferred to holdout) |
| K-7 Osler stop-cluster proxy | RAN | Marginal contribution; not in top-50 across paths |
| K-8 power-law OB-age weighting | RAN | Marginal contribution; not in top-50 across paths |
| K-9 regime × round × side interaction | RAN | Below noise floor |
| K-10 above-up below-down round-aligned direction | RAN | Marginal — `kw__k10_round_dist_min_atr` appears in some path top-100s |
| K-1' tick-count-time bars | NOT RUN | Closed-form requires per-row tick aggregation across full cohort 2024-2026; deferred |
| K-4 Stoikov micro-price | DROPPED | KILLED 2026-04-29 per `KILLED_HYPOTHESES.md` |

### 1.2 Methodology gates

| Gate | Threshold | Realized | Verdict |
|---|---|---:|:---:|
| (a) | mean K54 v3 AUC ≥ 0.55 | 0.5770 | **PASS** |
| (b) | lift ≥ +0.04 vs anchor 0.5286 + DSR-p < 0.01 + PBO < 0.4 + null p ≥ 0.99 | lift +0.0484 ✓, PBO 0.20 ✓, null p 1.00 ✓, **DSR-p 0.321 ✗** | **FAIL on DSR-p** |
| (c.i) | Train 2022-2023 v1-schema → Test 2024-2026: lift sign + magnitude ±50% | lift +0.0481, 4/4 groups positive | **PASS (v1-schema sanity)** |
| (c.ii) | Train <2026-01-01 → Test 2026-01-01+ on v3 features: lift sign + ≥3/4 groups positive | lift -0.022, 1/4 groups positive | **FAIL** |
| (d) | All 4 groups AUC ≥ 0.50 + NAS specialist delta ≥ +0.05 | 2/4 groups (NAS+GBPJPY <0.50); specialist delta +0.103 | **FAIL on global; PASS on specialist** |
| (e) | Realized-R lift ≥ +0.05R/trade with bootstrap p < 0.01 | -0.108R, p = 0.999 | **FAIL** |
| (f) | ≥30 features in top-50 across ≥80% paths AND Jaccard ≥ 0.6 | 2 stable features, Jaccard 0.169 | **FAIL** |
| (g) | Christoffersen interval-coverage on holdout 2026-04-29→2026-05-12 | DEFERRED to 2026-05-13+ | DEFERRED |

**Final verdict: 1 of 6 testable gates PASS. FAIL.**

---

## 2. Why each gate failed

### Gate (b) — DSR-p = 0.321 (gate < 0.01)

The lift IS real. Three independent lines of evidence agree on this:

- Paired DeLong DeLong combined Stouffer p = 0.024 (significant at α = 0.05, not at α = 0.01).
- B=1000 null shuffle distribution: observed AUC 0.5770 exceeded by 0/1000 random shuffles. p99 of null = 0.5246; observed is 0.052 above p99.
- PBO via CSCV = 0.20 (well below 0.4 gate); IS-best HP rarely becomes OOS below-median.

**But DSR with N=200 trial budget kills it.** SR_paired = 1.27, sigma_SR = 0.36, expected max-SR at N=200 = 0.36 × 3.08 = 1.11. Observed SR sits 0.16 above the noise ceiling — DSR-p = 0.32. This is the **same fate as K54 v2** (DSR row M-2: dsr_p = 0.965). K54 v3 is closer to the ceiling but does not survive.

**The DSR penalty is the binding constraint at N=200.** Any architecture whose paired SR < 1.5 cannot pass DSR-p < 0.01. Translation to AUC: K54 v3 would need ~+0.07 paired AUC lift (vs realized +0.048) to clear the gate. **No K54 family architecture has produced +0.07+ paired AUC at this n on this catalog.**

### Gate (c.ii) — within 2024-2026 split FAIL

Train n=93 (pre-2026-01-01, 17.6% of cohort) / Test n=435 (2026-01-01+, 82.4%). K54 v3 AUC test = 0.504 vs K54 v1 AUC test = 0.526 (lift -0.022). Per-group: only GBPUSD_USDJPY positive (lift +0.048); NAS_US30 (-0.076), GBPJPY (-0.020), XAU_XAG (-0.046) all negative.

The pre-2026 n=93 training cohort is too small + too XAU-dominated (per `audit/cross_period_replication.md` Section 3.1). The model has not seen enough non-XAU pre-2026 trades to learn temporally-stable structure for FX/indices. This is the **structural data limit** that the audit-recommended 2022-2023 backfill exists to fix — but the backfill is v1-schema-only, so cannot test gate (c.ii) on v3 features.

### Gate (d) — global per-instrument floor FAIL

NAS_US30 global AUC 0.498, GBPJPY global AUC 0.464 — both below the 0.50 floor. Same pattern as Q1.3 K54 v2 (CF-5 in `AMBIGUITIES_AND_OPEN_QUESTIONS.md`): the global model averages over real per-cohort heterogeneity. The K54 v3 features (K-7..K-10) target XAU + indices mechanics (round-number stops, OB-age power law) but do not lift the FX cohorts. This is consistent with Group B / Group D literature: stop-cluster mechanism is FX-only effective; OB-age decay is universal; round-number direction is XAU-specific.

The NAS_US30 specialist PASSES gate (d.specialist) at delta +0.103 — **the only stable per-cohort lift the program has demonstrated**.

### Gate (e) — realized-R lift NEGATIVE

K54 v3 (threshold p > 0.5) trades produce mean R = +0.247 / trade; uniform always-trade produces mean R = +0.355 / trade. **Lift = -0.108R per attempted trade.** The model's threshold removes winning trades on average.

This is NOT an AUC-vs-realized-R disconnect (memory `feedback_walk_level_evidence_not_predictive`). It is the model picking the wrong half of its score distribution to trade. The cohort's win-rate (0.580) is close to the 0.50 threshold, so the model's discriminating boundary is in the high-density region of P(p > 0.5). The 0.500 threshold is wrong; gating at e.g. p ≥ 0.65 might recover positive lift. But the gate (e) test as written uses 0.50 — the standard binary classification threshold — and at that threshold, K54 v3 is harmful.

**Forward methodology note:** future gate (e) tests should sweep the threshold across `[0.50, 0.55, 0.60, 0.65, 0.70]` and report realized-R lift at each, not just at 0.50.

### Gate (f) — feature stability FAIL

Mean pairwise Jaccard on top-50 features across 15 CPCV paths = 0.169 (target ≥ 0.6). Only 2 features in top-50 across ≥80% of paths: `liq__liq_round_50p0_dist_above_ticks` (14/15) and `vol__h1_range_over_mean_200` (12/15). Same overfit signature as Q1.3 K54 v2 (Jaccard 0.072, zero stable-core features).

The per-fold top-100 screening identifies a different "best" set on every fold. With 528 rows × 1,234 features = 0.43 rows-per-feature pre-screening, the per-fold screening's 100-feature output is dominated by which features happen to fit each fold's specific time slice. K54 v3's screening identifies a slightly more stable core (2 features ≥80%) than K54 v2 (0 features ≥80%), but the gate threshold of 30 stable features cannot be satisfied at this n / catalog ratio.

---

## 3. The decisive root cause: cohort-scale ceiling × DSR trial budget

Q1.4 cannot satisfy gate (b) DSR-p < 0.01 at N=200 trial budget for any model whose paired SR < 1.5. To produce paired SR > 1.5 on n=15 CPCV paths requires:

```
sigma_diff_per_path * 1.5 / sqrt(15-1) < diff_mean  
→ diff_mean > sigma_diff * 0.4  
```

With per-path SD of paired diff ≈ 0.07 (this run), the required diff_mean for DSR survival is ≥ 0.028 — which is below K54 v3's 0.048. So why did DSR fail?

The actual DSR computation uses `sigma_SR = sqrt((1 + 0.5 * SR_paired^2) / (T-1))` per AFML eq 11.5, which is per-trial-distribution-aware. With SR_paired = 1.27 and T = 15, sigma_SR = 0.36. Expected max-SR at N=200 = 1.11. Observed SR is 0.16 above the noise ceiling (z = 0.46, one-sided p = 0.32). The deflation comes not from the measurement uncertainty but from the **multiple-comparison penalty: across 200 cumulative GTOS trials, the expected max SR under null is 1.11**, and our observed 1.27 is well within the upper tail of "what null can produce."

**Two paths to escape the DSR penalty:**

1. **Reduce N (the cumulative trial budget).** Not feasible — the program already ran ~200 trials (per Group A audit). Pretending it ran fewer would be deception.
2. **Increase the lift magnitude.** Requires either bigger features (which K54 v3 attempted via K-7..K-10 — failed below noise) OR more rows. The 4× cohort expansion via 2022-2023 v2-feature backfill would shift `n_train` per fold from 274 to ~1,200, dropping noise SD per path by ~`sqrt(274/1200) = 0.48`, lifting effective SR to ~`1.27 / 0.48 ≈ 2.65`, well above the DSR ceiling 1.11.

**The Q1.3 audit explicitly recommended the cohort-expansion path** (`audit/Q1_3_POSTMORTEM_SYNTHESIS.md` §3.2 Alternative A). This dispatch confirms it is the only feasible path forward.

---

## 4. What survives Q1.4

### 4.1 Strongest single finding: NAS_US30 specialist

| Metric | Value |
|---|---:|
| Cohort | n = 113 |
| Specialist AUC (Arch B replicated under K54 v3 features + balanced W-unit) | **0.6014** |
| Global K54 v3 AUC on same 113-row cohort | 0.4984 |
| Specialist delta over global | **+0.103** |
| PBO (Q1.3 Arch B) | 0.53 (yellow flag — HP-fragile within group) |

The NAS_US30 specialist is **the only K54-family component with statistically-defensible per-cohort lift**. It replicates the Q1.3 finding under the K54 v3 feature catalog + corrected W-unit. The PBO 0.53 caveat from Q1.3 still applies — within-group HP is unstable, suggesting +0.103 may shrink under truly-blind out-of-sample.

**Ship recommendation:** deploy as **K55-shadow signal candidate** with low-confidence floor (p ≥ 0.55) on NAS100 + US30_cash only. Run in shadow mode for 30+ days; promote to live A/B if shadow data confirms lift.

### 4.2 V1-schema cross-period model passes gate (c.i)

Train on 2022-2023 backfill (n=1,798, 17 features) → Test on 2024-2026 (n=528, same 17 features). AUC test = 0.577, lift over anchor 0.5286 = +0.048. **Per-group: 4/4 positive.**

This is a **cross-period generalization signal** for the v1-schema features — but it does not test K54 v3 (1,234 v2 features). It is a side-finding that confirms: **the v1-schema features carry generalizable signal across the 2022-2024 break.**

This validates Operational Filter #1 (drop `framework`) and the canonical 14-feature K54 v1 set. It does NOT validate K54 v3 architecture.

### 4.3 Architecture A's Q1.3 finding survives K54 v3 retest

Diagnostic ablation: K54 v3 features + W-unit OFF (i.e. Arch A reproduction with K-7..K-10 added) → AUC 0.5640. Q1.3 Arch A original → AUC 0.5605. **The K-7..K-10 additions contribute +0.0035 AUC.** This is below noise (per-path SD ≈ 0.07).

**Forward methodology:** K-7..K-10 should NOT be carried into Q1.5 K54 v4 unless cohort expansion lifts the rows-per-feature ratio to where their marginal contribution becomes detectable. At n=2,326 + 1,234 features → 1.88 rows-per-feature, still high-dim. Need n ≥ 5,000 to drop to 4 rows-per-feature.

---

## 5. Q1-close vs Q1.5 re-spec — recommended path

### 5.1 Recommended: Q1 CLOSE with K55-shadow ship of NAS specialist

**Rationale:**

1. The K54 v3 master bundle architecture is empirically unable to clear DSR at N=200 trial budget on this cohort. No further architectural refinement at n=528 will move DSR-p below 0.01.
2. The NAS_US30 specialist is the program's only deployable component. Ship it now in K55-shadow.
3. The cohort-expansion path (4-6 weeks of 2022-2023 v2-feature engineering) is the only methodologically defensible Q1.5 substrate. Closing Q1 first lets that work proceed without Q1.5 wallclock pressure.
4. CLAUDE.md item #11 explicitly approves Q1 close path: "Phase 2 rank #1 = K54 regime-aware ML classifier" — the K54 v3 result reframes that as "K55-shadow with NAS specialist + cohort expansion before next architecture iteration."

### 5.2 Q1.5 re-spec template (if cohort expansion completes)

If a future agent dispatch produces 1,798 rows of full v2-catalog features for the 2022-2023 backfill (audit-recommended; 4-6 weeks of OHLCV-driven feature computation), the Q1.5 hypothesis would be:

> *"K54 v4 trained on the unified n=2,326 cohort (528 + 1,798 v2-feature) with Architecture A (per-fold top-100 screening) + NAS_US30 specialist routing achieves CPCV-honest mean AUC ≥ 0.58 with paired SR ≥ 1.6 (DSR-p < 0.01 at N=200) on the 4-axis 2022-2026 timeline. Lift ≥ +0.05 over canonical K54 v1 baseline 0.5286 with PBO < 0.4 + null p ≥ 0.99. Cross-period gate: (c.i) train 2022-2023 → test 2024-2026 lift ≥ +0.04 with 4/4 groups positive AUC ≥ 0.55; (c.ii) train ≤2025-12-31 → test 2026-01-01+ lift ≥ +0.04 with 3/4 groups positive."*

**Drop from Q1.5 scope:**

- K-7 Osler stop-cluster proxy (FX-only mechanism; below noise on global model)
- K-8 power-law OB-age weighting (below noise)
- K-9 regime × round × side 3-way interaction (below noise)
- Kyle-Obizhaeva W-unit pooling (FAILED in raw form; balanced form contributes nothing; mechanism requires LOB depth not present in MT5 retail data)
- Lopez-de-Prado meta-labeling head (statistically weak at n=528; reintroduce at n>5,000)

**Keep in Q1.5 scope:**

- Architecture A (per-fold top-100 screening) — the Q1.3 audit's strongest finding, robust under K54 v3 retest
- NAS_US30 specialist routing layer (Architecture B) — strongest single finding
- TreeSHAP-stability pruning gate (K-15) — gate (f) anchor
- Adaptive conformal calibration (K-14) — gate (g) enabler
- DSR + CSCV PBO + null shuffle methodology gates (Q1.3 + Q1.4 lessons-learned)

**Add to Q1.5 scope:**

- 2022-2023 v2-feature backfill (data engineering prerequisite)
- Threshold sweep on gate (e) realized-R measurement (`p ≥ {0.50, 0.55, 0.60, 0.65, 0.70}` with bootstrap CI per threshold)
- Per-group ensemble alternative to global+specialist routing (Q1.3 Arch B's NAS specialist won; XAU+XAG, GBPJPY, GBPUSD+USDJPY each get own model with feature subset selection)

### 5.3 Holdout discipline: gate (g) opens at 2026-05-13

The 14-day prospective holdout window 2026-04-29 → 2026-05-12 was NOT touched in this dispatch. Per pre-registration discipline, gate (g) is the only-once Christoffersen interval-coverage test on K54 v3's adaptive conformal predictions over the holdout window. **The Q1 verdict does NOT depend on gate (g)** — the architecture has already failed 5 of 6 testable gates; gate (g) PASS would not lift the verdict.

**Operational note:** if K54 v3 is reframed as K55-shadow signal at the NAS specialist level only, gate (g) on the global K54 v3 is not load-bearing for the shadow-deploy decision. Gate (g) on the NAS specialist's predictions during the holdout would be the relevant operational test.

---

## 6. Forward methodology hardening

### 6.1 DSR is mandatory

Every forward K54 (or any-other) family lift claim must report:

- Raw / Stouffer / DeLong p (already standard)
- **DSR-corrected p** at the cumulative GTOS Phase 1 trial budget (currently N=200; will increase as program proceeds)
- **PBO via CSCV** with n_combos ≥ 14
- **B=1000 null shuffle empirical p**
- **Per-path SR + sigma_SR** (so DSR can be computed from raw paired-trade Sharpe)

The forward gate proposed in `dsr_retroactive_sweep.md` Section 10:

```
def methodology_gate(claim):
    if (claim.dsr_p < 0.01
        and (claim.pbo is None or claim.pbo < 0.4)
        and (claim.effective_N is None or claim.effective_N >= 3)):
        return "SURVIVES"
    if claim.dsr_p >= 0.05 or (claim.pbo is not None and claim.pbo >= 0.5):
        return "FAILS"
    return "BORDERLINE"
```

### 6.2 The audit-recommended cohort expansion is the binding bottleneck

At n=528 + 1,234 features, NO architectural refinement can produce DSR-survival. The next 4-6 weeks of program time should be allocated to:

1. **2022-2023 v2-feature backfill** — full 1,234-feature catalog computed on the 1,798-row 2022-2023 cohort. This is OHLCV-driven feature engineering; deterministic, reproducible.
2. **2024-2025 trade-cohort gap closure** — the 2024-04-01 → 2026-01-01 cohort is 93.5% XAU-only (per `audit/cross_period_replication.md`). If feasible, mine non-XAU fills from `knowledge_base_backtest/` + `trades_unified.csv` to balance the pre-2026 cohort.

After both, the unified Q1.5 cohort is n ≈ 2,326 + non-XAU fillback. At 5+ rows per feature post-screening, the K54 architecture's potential becomes DSR-testable.

### 6.3 The Kyle-Obizhaeva pooling failure is informational

Per `KILLED_HYPOTHESES.md` Q1.4 entry (Top-1 surprise): the literature's W-unit invariance assumption requires LOB depth (Kyle-Obizhaeva 2016 was developed on equity TAQ data). MT5 retail FX/CFD with volume=0 ceiling makes the literal W-unit non-computable; substitution via balanced intra-instrument-vol-rank is methodologically defensible but does not transmit the published mechanism. **Same operational gap that killed K-4 Stoikov.**

Forward implication: **literature transplants from equity-LOB domains to retail FX/CFD must be vetted for substrate compatibility** BEFORE pre-registration. Group B / Group F / Group D anchor papers should be re-audited for "requires LOB depth?" — those that do should be flagged as not-feasible-on-current-data.

---

## 7. Decision request to CEO

**1. Approve Q1 CLOSE per §5.1?** Reframe K54 v3 to K55-shadow (NAS_US30 specialist only); do not open Q1.5 immediately.

**2. Approve audit-recommended cohort expansion as Phase 2 priority?** 4-6 weeks of 2022-2023 v2-feature backfill + non-XAU 2024-2025 fillback before any K54 v4 dispatch.

**3. Approve K55-shadow deploy of NAS_US30 specialist?** Read-only shadow mode (`config.k55_shadow.enabled: true`, hard-coded at p ≥ 0.55 floor, NAS100 + US30_cash only). 30-day shadow data → empirical promotion gate.

**4. Approve forward methodology gate?** All future K54-family lift claims must include DSR-corrected p alongside Stouffer/DeLong, with auto-pass/fail per the `methodology_gate` function above. Add to `dsr_diagnostics.json` audit trail.

**5. Approve the holdout window 2026-04-29 → 2026-05-12 to remain UNOPENED for K54 v3 global gate (g)?** Per pre-registration, the holdout opens only once per phase. Since K54 v3 has already failed 5/6 testable gates, opening gate (g) for the global model is not necessary. The holdout window may instead be applied to the NAS specialist or held in reserve for a Q1.5 K54 v4 evaluation.

If approved (1+2+3+4+5), Phase 2 priorities re-set to:

- **Week 1-2:** open production-ops `_trade_index.json` ticket; deploy K55-shadow NAS specialist; start 2022-2023 v2-feature backfill data engineering.
- **Week 3-4:** non-XAU 2024-2025 fillback from `knowledge_base_backtest/` + `trades_unified.csv`.
- **Week 5-6:** K54 v4 modeler dispatch on unified n ≈ 2,326 + fillback cohort with Architecture A + NAS specialist + DSR-mandatory methodology gate.
- **End of Phase 2:** Q1.5 verdict (PASS → ship K54 v4 + NAS specialist; FAIL → close K54 family, pivot to ensemble / per-cohort-only deploy).

---

## 8. File index

- `research/ml_program/models/k54_v3/report.md` — full K54 v3 modeler report
- `research/ml_program/models/k54_v3/cpcv_paired_results.json` — 15-path detail
- `research/ml_program/models/k54_v3/dsr_per_gate.json` — DSR per gate
- `research/ml_program/models/k54_v3/cross_period_results.json` — gates c.i + c.ii
- `research/ml_program/models/k54_v3/specialist_results.json` — NAS_US30 specialist
- `research/ml_program/models/k54_v3/realized_r_holdout.json` — gate (e)
- `research/ml_program/models/k54_v3/feature_stability.json` — gate (f)
- `research/ml_program/models/k54_v3/conformal_calibration.json` — gate (g) DEFERRED
- `research/ml_program/models/k54_v3/diagnostic_w_unit_ablation.json` — W-unit failure diagnostic
- `research/ml_program/models/k54_v3/k54_v3_global.lgb` — final global LightGBM
- `research/ml_program/models/k54_v3/k54_v3_meta_label.lgb` — meta-label secondary classifier
- `research/ml_program/models/k54_v3/k54_v3_nas_us30_specialist.lgb` — NAS specialist (RECOMMENDED FOR K55-SHADOW)
- `research/ml_program/models/k54_v3/top_features.json` — per-path top-100 + aggregated
- `research/ml_program/audit/dsr_diagnostics.json` — appended K54 v3 row (verdict FAILS)
- `research/ml_program/KILLED_HYPOTHESES.md` — Q1.4 K54 v3 entry (why-it-failed memo)
- `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` — Q1.4 entry status updated to FAIL
- This document: `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`

---

*Standing by for CEO direction on §7 (Q1 close + K55-shadow deploy + cohort expansion priority).*
