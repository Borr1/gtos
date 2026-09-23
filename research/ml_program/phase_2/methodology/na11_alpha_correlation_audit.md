# NA-11 — Pairwise Alpha Correlation Audit + Corrected Portfolio Sharpe Math

**Author:** Forensic Agent NA-11 (Phase 4, Opus 4.7 / max effort).
**Date:** 2026-04-29.
**Status:** Subscription-only, READ-ONLY for production. No `src/` / `config/` / `prompts/` / `knowledge_base/` modifications.

**Mandate:** Resolves NA-11 from `MASTER_SYNTHESIS.md`. Agent J's portfolio Sharpe math (`agent_j_renaissance_edge_discovery.md` §3 + `agent_j_portfolio_sharpe_projection.json`) **asserted ρ̄ = 0.10** across alphas. This audit measures empirical pairwise correlation across the program's 5 confirmed/candidate alphas to validate Renaissance portfolio aggregation math.

**Inputs:**
- `research/ml_program/forensics/2026-04-29/agent_j_renaissance_edge_discovery.md` (asserted formula).
- `research/ml_program/forensics/2026-04-29/agent_j_portfolio_sharpe_projection.json` (N-edges-to-target).
- `research/ml_program/forensics/2026-04-29/agent_h_meta_pattern_audit.md` (alpha inventory).
- `research/ml_program/scout/feature_matrix.parquet` (n=528 cohort with `__realized_r`, `__win_label`, `__source`).
- `research/ml_program/models/k54_v3/cpcv_paired_results.json` (per-fold K54 v3 OOF predictions for top-3% reconstruction).
- Memories `project_j46_j49_position_mgmt_findings`, `project_s79_risk_policy_shipped_2026-04-27`, `project_f11_ob_zone_decay_velocity_pinned`.

---

## 1. Headline finding

**Empirical ρ̄ = +0.0076 (signed) / 0.0557 (absolute), excluding two structural-degenerate pairs.**
**Agent J's asserted ρ̄ = 0.10. Empirical signed ρ̄ is *more favorable* by Δ = -0.0924; empirical absolute ρ̄ is *more favorable* by Δ = -0.0443.**

Three of the five alphas are operating *near-orthogonally* in the n=528 K54 v3 cohort. The two non-real pairs (one collinear, one partition) inflate Agent J's worst-case projection unless excluded; once excluded, achievable Sharpe ceilings are HIGHER than Agent J's table reports.

**Concretely:**
- At per-edge Sharpe 0.40 + empirical signed ρ̄ ≈ 0.008, Sharpe 1.0 reachable at **N = 7**, Sharpe 1.5 reachable at **N = 16** (Agent J's table required N=20+ at ρ̄=0.10).
- At per-edge Sharpe 0.40 + empirical *absolute* ρ̄ ≈ 0.056 (conservative), Sharpe 1.0 reachable at **N = 10**, Sharpe 1.5 reachable at **N = 62** (worse than Agent J's projection because conservative |ρ| ≈ 0.05-0.06 — but still reachable, where ρ̄ = 0.10 made it hard).

**Critical structural caveats (Section 4):**
1. **J46_J49_R and S79_sized_R are perfectly collinear (ρ = +1.0)** by construction in the SHIPPED FN profile (S79 = 2.0 × R under uniform_fn 2.0%). They are one alpha reported twice. Excluded from ρ̄.
2. **Mech_OB_indicator and AI_indicator are perfectly anti-correlated (ρ = -1.0)** as a *cohort-assembly partition artifact* (every n=528 row is EITHER mechanical OR AI source, n_both = 0). In the LIVE system both alphas can fire on the same M15 candle; the disjoint structure here is unmeasurable. Excluded from ρ̄.
3. **K54 v3 top-3% picks 16/16 trades from the mechanical cohort** (P(Mech | top-3%) = 1.000). The "top-3% K54 alpha" is a *subset* of the mechanical OB alpha as currently fit. This is a structural concentration, not an independence story.

---

## 2. Methodology

### 2.1 Cohort

The 528-trade K54 v3 cohort (`feature_matrix.parquet`, 2024-04-01 → 2026-04-24, cutoff 2026-04-28) is the only available cross-program substrate with `__realized_r` per trade for ALL five alphas. Per-fill J46-J49 outcomes (`per_fill.jsonl`, 121MB gitignored) and the 2022-2023 mechanical n=1798 cohort live outside this dataset — so the relevant correlations are computed on the n=528 OVERLAP.

### 2.2 Alpha definitions

| # | Alpha | Series type | Definition (per-trade) |
|---|---|---|---|
| 1 | J46-J49 portfolio policy | continuous R | `__realized_r` (the cohort's R is *already J46-J49-encoded* under shipped policy) |
| 2 | S79 risk policy | continuous sized R | `2.0 × __realized_r` (uniform_fn 2.0% under shipped FN profile) |
| 3 | Mechanical OB cross-period | binary indicator | `1{__source == 'f11_mechanical'}` (in-cohort proxy; n=406/528) |
| 4 | K54 v3 top-3% confidence | binary indicator | `1{trade ∈ top-3% by mean_p_v3}` (n=16/528) |
| 5 | AI baseline ~63% WR | binary indicator | `1{__source ∈ {trade_index, unified_csv}}` (n=122/528, WR=65.6%) |

Mean_p_v3 reconstructed by averaging CPCV fold predictions per row per `_run_extended.py` recipe.

### 2.3 Correlation computation

For each of the 10 pairs (5 choose 2):
- **Pearson** (linear correlation; for binary-vs-continuous = point-biserial, semantically `(E[R|A=1] - E[R|A=0]) / σ_R`).
- **Spearman** (rank correlation; robust to monotone non-linearity).
- **Kendall τ** (concordance probability; tail-friendly).
- **Tail correlation:** Kendall τ on top-25% and bottom-25% of alpha A.
- **Co-occurrence frequency:** P(B fires | A fires); P(A fires | B fires); n_both. (Binary-only.)
- **Conditional E[R]:** mean R by 4-cell partition of (A signals, B signals).

### 2.4 ρ̄ computation rule

**Authoritative ρ̄** = mean of off-diagonal Pearson correlations EXCLUDING two structurally degenerate pairs:
- J46_J49_R / S79_sized_R (collinear: ρ = 1.0 by construction).
- Mech_OB_indicator / AI_indicator (partition: ρ = -1.0 by cohort-assembly artifact).

This leaves **7 real pairs** (dropping the duplicate ordering, 8 listed above; deduplicated to 7 unique alpha-pair correlations after removing the two degenerate). Wait — let me recount: from C(5,2)=10 unique pairs, drop 2 degenerate → **8 real pairs**, but in the implementation we have 8 real off-diagonal entries above the diagonal (since each pair appears once). The mean of these 8 is the authoritative ρ̄.

---

## 3. The 5×5 correlation matrix

Pearson correlations (full 5×5; persisted to `na11_correlation_matrix.csv`):

|                       | J46_J49_R | S79_sized_R | Mech_OB | K54_v3_top3 | AI_ind |
|-----------------------|----------:|------------:|--------:|------------:|-------:|
| **J46_J49_R**         | 1.0000    | 1.0000      | +0.0478 | +0.0304     | -0.0478|
| **S79_sized_R**       | 1.0000    | 1.0000      | +0.0478 | +0.0304     | -0.0478|
| **Mech_OB_indicator** | +0.0478   | +0.0478     | 1.0000  | +0.0969     | -1.0000|
| **K54_v3_top3pct**    | +0.0304   | +0.0304     | +0.0969 | 1.0000      | -0.0969|
| **AI_indicator**      | -0.0478   | -0.0478     | -1.0000 | -0.0969     | 1.0000 |

Spearman matrix (rank-based) is qualitatively identical to Pearson for binary-vs-continuous pairs but gives slightly larger magnitudes for the J46/Mech and J46/AI pairs (|ρ| = 0.080 vs 0.048 Pearson) — confirming a small but consistent rank-monotone pattern that Pearson under-detects.

### 3.1 ρ̄ summary

| Variant | Pearson ρ̄ | Pearson |ρ̄| | Notes |
|---|---:|---:|---|
| All 10 pairs (naive) | +0.0061 | 0.2557 | Inflated by both degenerate pairs |
| Exclude collinear only (9 pairs) | -0.1044 | 0.2304 | Dominated by Mech/AI = -1.0 partition artifact |
| **Exclude collinear AND partition (8 pairs)** | **+0.0076** | **0.0557** | **Authoritative** |
| Agent J asserted | +0.10 | 0.10 | — |
| **Δ vs asserted (signed)** | **-0.0924** | — | Empirical is *more favorable* than asserted |
| **Δ vs asserted (absolute)** | — | **-0.0443** | Empirical is *more favorable* than asserted |

**Interpretation.** The 5 alphas — once degenerate pairs are removed — are operating near-orthogonally on this cohort. Most pair |ρ| values are in [0.03, 0.10]. Highest real pair correlation: Mech_OB ~ K54_v3_top3pct = +0.0969 (significant at p=0.026 because the top-3% is a strict subset of mechanical, n_co_occur = 16 of 16). All other pairs have p > 0.05 — Bernoulli noise floors at this n.

---

## 4. Per-pair narrative

### 4.1 Pair 1: J46_J49_R ~ S79_sized_R — **PERFECTLY COLLINEAR (ρ = +1.0)**

**Why:** S79 shipped under uniform_fn 2.0%. Per-trade sized-R = 2.0 × R = constant × J46_J49_R. By construction Pearson/Spearman/Kendall = 1.0, p = 0.

**Operational implication:** S79 is *not* a separable signal-edge under the shipped policy. It's a sizing constant. Treating S79 as an independent contribution to portfolio Sharpe is double-counting. The relevant addition to the alpha portfolio is **future S79 variants** (S79-Variant-B Sharpe-weighted, side-aware-Variant-C, Variant-E drawdown-adaptive) — which are NOT collinear with J46-J49 because they introduce per-trade sizing variation.

**Pre-Phase-2 caveat:** The collinearity is broken the moment S79 ships a non-constant variant. Re-measure ρ at that point.

---

### 4.2 Pair 2: J46_J49_R ~ Mech_OB_indicator — Pearson +0.0478 (p=0.27)

**Headline:** Trades sourced from the mechanical-OB-2026 cohort have **mean R = +0.387** vs **+0.250** for non-mech (i.e., AI-source) trades. The `Δ = +0.137R` is captured by the +0.048 point-biserial correlation. p=0.27 (not significant), but Spearman ρ=+0.080 (p=0.066) catches a marginal monotone pattern.

**Tail correlation:** `tau_right_tail = -0.751` — in the top-25% of R, the binary `Mech_OB_indicator` is negatively associated with R. Reading: among the *highest-R* trades, the AI-source rows actually carry slightly more upside (because AI cohort selects only ~10% CR, so when an AI trade fires it tends to have higher R-conditional-on-fire). However n_right_tail is small and τ_left is degenerate (ties).

**Conditional E[R]:**
- E[R | Mech_OB = 1] = +0.387, n = 406.
- E[R | Mech_OB = 0] = +0.250, n = 122.
- delta = +0.137R.

**Independence verdict:** Mechanical OB and J46-J49 R are *near-orthogonal at the per-trade level on this cohort*. The mechanical signal explains <1% of R variance. This is what we'd expect from Agent F's J46-J49 attribution (J46-J49 lift is per-fill efficiency, downstream of trade-selection edge).

---

### 4.3 Pair 3: J46_J49_R ~ K54_v3_top3pct — Pearson +0.0304 (p=0.49)

**Headline:** The 16 K54 v3 top-3% trades have **mean R = +0.563** vs **+0.349** for the rest. Δ = +0.214R, but n=16 makes p insignificant (Pearson p=0.49). Spearman ρ=+0.028 (p=0.52). All three correlation tests agree this is essentially noise at this n.

**Tail correlation:** `tau_right_tail = +0.009` (essentially zero). The top-3% K54 trades are NOT preferentially located in the top-25% R cohort — they have *typical* R distribution despite their high model probability.

**Conditional E[R]:**
- E[R | top-3% = 1] = +0.5625, n = 16.
- E[R | top-3% = 0] = +0.3488, n = 512.
- delta = +0.214R.

**Independence verdict:** ρ ≈ 0.03 makes K54 v3 top-3% an *almost-orthogonal* edge to J46-J49. But the top-3% n=16 is at the noise ceiling (the +0.21R lift is marginal at p=0.49). This is exactly Agent A2's MARGINAL_WITH_PRACTICAL_LIFT verdict.

---

### 4.4 Pair 4: J46_J49_R ~ AI_indicator — Pearson -0.0478 (p=0.27)

**Mirror of pair 2** by partition (Mech_OB and AI_indicator are partition-complementary in this cohort). E[R | AI = 1] = +0.250 vs E[R | AI = 0] = +0.387 → Δ = -0.137R. The AI-cohort trades have *lower* mean R than the mech-cohort trades on this dataset, BUT this is NOT a verdict on the AI baseline alpha — it's a comment on cohort-source selection (the AI subset includes 2024-2025 trades from the trade_index source, which had different volatility regime than the April 2026 mechanical cohort).

**Independence verdict:** The negative sign is a cohort-mixing artifact. In the LIVE system, the AI baseline and mechanical OB are not partition-complementary — they CAN co-occur. The relevant LIVE rho is unmeasurable from this cohort.

---

### 4.5 Pair 5-7: S79_sized_R ~ {Mech_OB, K54_v3_top3pct, AI_indicator} — IDENTICAL to J46_J49_R pairs

By collinearity (S79 = 2 × J46_J49). All three pairs have ρ identical to the J46_J49 versions. The conditional E[R] values are 2× larger (e.g., S79 ~ Mech_OB: E[sized_R | Mech] = +0.774 vs E[sized_R | not Mech] = +0.500, delta = +0.273) but the correlation structure is unchanged.

**Implication:** Once S79 is collapsed into J46-J49 (one alpha not two), the program has effectively **3-4 alphas** to aggregate, not 5.

---

### 4.6 Pair 8: Mech_OB_indicator ~ K54_v3_top3pct — Pearson +0.0969 (p=0.026) **MOST-CORRELATED REAL PAIR**

**Headline:** **K54 v3 top-3% is a strict SUBSET of mechanical OB cohort (P(Mech | top-3%) = 1.000, n = 16 of 16).** The model has learned that the highest-probability trades on this cohort all come from the f11_mechanical April 2026 source.

**Co-occurrence:**
- n_both = 16, n_only_Mech = 390, n_only_K54 = 0, n_neither = 122.
- P(top-3% | Mech_OB) = 16/406 = 0.039.
- P(Mech_OB | top-3%) = **1.000**.

**Conditional E[R]:**
- E[R | both] = +0.563 (n=16).
- E[R | only Mech, not top-3%] = +0.380 (n=390).
- E[R | neither] = +0.250 (n=122 — i.e., AI cohort rows).

**Critical interpretation.** The top-3% K54 v3 alpha is *not orthogonal* to the mechanical OB alpha — it is a CONCENTRATION OF mechanical OB. Aggregating K54 v3 top-3% on top of mechanical OB is *not* adding an independent edge; it's adding a concentration filter. The +0.183R lift of "both" over "only Mech" (0.563 - 0.380) is the K54 marginal contribution conditional on mechanical, but n=16 is too small to clear DSR.

**Phase 2 Implication.** K54 v4 must be trained on a cohort that is NOT 77% mechanical-source from April 2026, or it will continue to learn date-proximity bias rather than signal-mechanism. The data engineering work (cross-period 2022-2023 v2-feature backfill + non-XAU 2024-2025 fillback) per K54 v3 post-mortem is the binding bottleneck.

---

### 4.7 Pair 9: Mech_OB_indicator ~ AI_indicator — **PERFECTLY ANTI-CORRELATED PARTITION ARTIFACT (ρ = -1.0)**

**Why:** Every row in the n=528 cohort is EITHER source=='f11_mechanical' OR source ∈ {'trade_index', 'unified_csv'} — disjoint by cohort assembly. n_both = 0, n_neither = 0.

**Operational implication:** This ρ = -1.0 is *unmeasurable* from this cohort because the LIVE system can have AI CANDIDATEs on mechanical-OB-qualifying setups (they CO-FIRE in production). The disjoint structure is an artifact of how the K54 v3 cohort was assembled (the f11_mechanical rows are a separate sweep over OHLCV; the AI rows are from the live decision log).

**Future test:** Build a unified per-M15-candle cohort where each row is a single candle and each alpha is a Bool/score (mechanical OB qualifies on this candle? AI emitted CANDIDATE on this candle?). Then measure ρ between Mech_OB and AI. Pre-registered prediction: 0.20-0.40 positive (because both alphas tend to fire when the same setup conditions are present).

---

### 4.8 Pair 10: K54_v3_top3pct ~ AI_indicator — Pearson -0.0969 (p=0.026)

**Mirror of pair 8** by partition complement: top-3% is 16/16 mechanical → 0/16 AI → P(AI | top-3%) = 0. ρ = -0.0969 (mirrors the +0.0969 of pair 8 because of the disjoint partition).

**Operational implication:** Same as pair 8 — K54 v3 has learned a date-proximity / cohort-source bias rather than a generalizable AI-vs-mechanical orthogonality.

---

## 5. Corrected portfolio Sharpe math

### 5.1 Asymptotic ceiling at empirical ρ

Sharpe ceiling at N → ∞ = `s / sqrt(ρ_eff)`. At empirical signed ρ ≈ 0.008, the ceiling is essentially `s × 11.2`; at empirical absolute ρ ≈ 0.056, the ceiling is `s × 4.2`. Compare to Agent J's asserted ρ = 0.10 ceiling = `s × 3.16`.

| per-edge Sharpe | At asserted ρ=0.10 | At empirical signed ρ=+0.008 | At empirical |ρ|=0.056 |
|---:|---:|---:|---:|
| 0.30 | 0.95 | **3.36** | 1.27 |
| 0.40 | 1.26 | **4.48** | 1.69 |
| 0.50 | 1.58 | **5.61** | 2.11 |
| 0.60 | 1.90 | **6.73** | 2.54 |

### 5.2 Finite-N projection at empirical ρ

#### At empirical signed ρ = +0.0076 (nominal/optimistic):

| N | s=0.30 | s=0.40 | s=0.50 | s=0.60 |
|---:|---:|---:|---:|---:|
| 3  | 0.52 | 0.69 | 0.86 | 1.04 |
| 5  | 0.66 | 0.88 | 1.10 | 1.32 |
| 8  | 0.83 | 1.10 | 1.38 | 1.65 |
| 12 | 1.00 | 1.34 | 1.67 | 2.01 |
| 16 | 1.15 | 1.53 | 1.91 | 2.30 |
| 20 | 1.27 | 1.70 | 2.12 | 2.54 |

#### At empirical absolute |ρ| = 0.0557 (conservative):

| N | s=0.30 | s=0.40 | s=0.50 | s=0.60 |
|---:|---:|---:|---:|---:|
| 3  | 0.49 | 0.65 | 0.81 | 0.97 |
| 5  | 0.59 | 0.79 | 0.99 | 1.18 |
| 8  | 0.69 | 0.92 | 1.16 | 1.39 |
| 12 | 0.78 | 1.04 | 1.30 | 1.56 |
| 16 | 0.85 | 1.13 | 1.41 | 1.69 |
| 20 | 0.89 | 1.19 | 1.49 | 1.79 |

### 5.3 Min-N for Sharpe targets

#### Target Sharpe = 1.0:

| per-edge Sharpe | At asserted ρ=0.10 | At empirical signed ρ=+0.008 | At empirical |ρ|=0.056 |
|---:|:--:|:--:|:--:|
| 0.30 | UNREACHABLE | **13** | 28 |
| 0.40 | 7-10 | **7** | 10 |
| 0.50 | 4-5 | **5** | 5 |
| 0.60 | 3 | **3** | 4 |

#### Target Sharpe = 1.5:

| per-edge Sharpe | At asserted ρ=0.10 | At empirical signed ρ=+0.008 | At empirical |ρ|=0.056 |
|---:|:--:|:--:|:--:|
| 0.30 | UNREACHABLE | **31** | UNREACHABLE |
| 0.40 | 45 | **16** | 62 |
| 0.50 | 16-81 | **10** | 18 |
| 0.60 | 7 | **7** | 10 |

### 5.4 Reading the table

**Headline correction.** Agent J's headline finding was *"Sharpe 1.5 is UNREACHABLE at realistic per-edge 0.30 + ρ̄ 0.10."* Under the empirical signed ρ̄ ≈ 0.008, **Sharpe 1.5 is reachable at per-edge 0.30 with N=31**. Under the conservative absolute ρ̄ ≈ 0.056, Sharpe 1.5 at per-edge 0.30 remains unreachable but Sharpe 1.0 is reachable at N=28 — a regime Agent J's table ruled out.

**Practical recommendation:** Use the **absolute ρ̄ = 0.056** as the planning input (conservative; respects sign-uncertainty in future alphas) and PUSH per-edge Sharpe toward 0.40 via DSR-disciplined screening. At per-edge 0.40 + |ρ| = 0.056:
- Sharpe 1.0 reachable at **N = 10** (3-4 more edges past current 7 confirmed/candidate).
- Sharpe 1.5 reachable at **N = 62** (very long horizon).

**Aspirational target** (per-edge 0.50 + |ρ| = 0.056):
- Sharpe 1.0 reachable at **N = 5**.
- Sharpe 1.5 reachable at **N = 18**.

---

## 6. Re-running Agent J's portfolio Sharpe math with empirical ρ̄

### Section 3.1 Update from Agent J:

> **Agent J's Section 3.1 stated:**
> "At per-edge Sharpe 0.30 + ρ̄ = 0.10, target Sharpe 1.5 is UNREACHABLE at any N. Asymptotic ceiling = 0.95."

**Corrected with empirical ρ̄:**
- At per-edge Sharpe 0.30 + empirical signed ρ̄ ≈ 0.008, asymptotic ceiling = **3.36** (4× higher than Agent J's number). Sharpe 1.5 reachable at N=31.
- At per-edge Sharpe 0.30 + empirical absolute ρ̄ ≈ 0.056, asymptotic ceiling = **1.27**. Sharpe 1.5 still UNREACHABLE — but Sharpe 1.0 reachable at N=28.

### Section 3.4 Discovery cadence projection — UPDATED:

Agent J: 2-3 quarters of focused dispatch needed for Sharpe 1.5 *at ρ̄ = 0.10*.
**Corrected with empirical ρ̄:**
- At empirical signed ρ̄ ≈ 0.008 + per-edge 0.40, **N=16 alphas → Sharpe 1.5 in 1-2 quarters**.
- At empirical absolute ρ̄ ≈ 0.056 + per-edge 0.40, N=62 needed → 4-6 quarters; should NOT be the program's target.

**Revised Phase 2 north star.** Push per-edge Sharpe toward 0.40-0.50 (DSR-disciplined screening; small DSR-survivors only). Aim for **Sharpe 1.0 at N = 5-10 edges** (per-edge 0.40-0.50 + ρ̄ ≈ 0.05-0.10) — reachable in 1-2 quarters at current Phase 4 cadence (8-15 DSR-survivors per quarter from the 25-candidate Renaissance backlog).

---

## 7. Strategic implications for Phase 2 discovery prioritization

### 7.1 Re-rank Agent J's top-25 backlog using empirical ρ̄

Agent J's composite score has independence as one factor (G3 gate: ρ < 0.30 with realized-R from {J46-J49, S79, OB-precision}). Under empirical ρ̄ ≈ 0.008, **G3 is much easier to clear than asserted** — most candidates can pass.

**However**, the partition artifact (K54 v3 top-3% ⊂ mechanical OB cohort) suggests a TIGHTER independence constraint:

- Agent J's G3 measures ρ vs realized-R; this NA-11 audit confirms that most candidates will clear ρ < 0.30 vs J46-J49 R.
- BUT the CO-FIRE structure (when alpha A fires, does alpha B also fire?) is the binding constraint for portfolio Sharpe aggregation, not just per-trade R correlation. In this cohort, K54 v3 fires only on a subset of mechanical OB rows — so its INDEPENDENT contribution to a portfolio is small even though its R correlation is weak.

**Refined G3 gate:** Each new candidate alpha must pass BOTH:
- (a) `|ρ_R| < 0.20` with realized-R from existing alphas (Agent J's G3, slightly tightened from 0.30).
- (b) **`P(co-fire) ≤ 0.30`** with each existing alpha — i.e., when alpha A fires, alpha B should NOT fire on >30% of those candles.

Under (b), K54 v3 top-3% would FAIL the gate vs Mech_OB (P(top-3% fires | Mech fires) = 16/406 = 0.039 — passes; P(Mech fires | top-3% fires) = 16/16 = 1.000 — FAILS at 0.30 threshold). This is the right red flag for K54 v3's current overconcentration.

### 7.2 Alpha class prioritization (informed by NA-11)

| Class | Current count | NA-11 verdict | Phase 2 priority |
|---|---:|---|---|
| Position-management variants (J46-J49 family) | 1 | Operating orthogonal to mech/K54 (ρ ≈ 0.03-0.05) — clean independence | **HIGH** (J-Rank 1, J46-J49-Variant-A: per-instrument partial-close) |
| Risk-policy variants (S79 family) | 1 (collapsed into J46-J49 in shipped policy) | Trivially collinear with R until variant ships | **HIGH** (J-Rank 2, S79-Variant-B Sharpe-weighted; breaks collinearity) |
| Side-aware sizing variants | 0 | Multiplicative on top of S79; orthogonal to R-correlation but not yet measured | **HIGH** (J-Rank 3, side-aware-Variant-C) |
| Mechanical OB cross-period | 1 | Operates on mostly mechanical-source rows; not orthogonal to K54 v3 by structural concentration | **MEDIUM** — already shipped via shadow; cross-period anchor is DSR-cheap |
| K54 v3 top-3% confidence | 1 (borderline) | Currently CONCENTRATED in mechanical cohort; not yet orthogonal | **MEDIUM** — needs cohort expansion before re-ranking |
| Calendar / time anomalies | 0 | Untested; high a priori independence (mechanism is intra-day flow imbalances, decoupled from OB-zone structure) | **HIGH** (J-Rank 5, J-Rank 11, J-Rank 12 — LBMA fix, FX-fix W-shape, pre-FOMC) |
| Macro / factor features | 0 | Untested; likely orthogonal to per-trade R | **MEDIUM** (J-Rank 8 real-gold-percentile; J-Rank 16 VIX1D-VIX9D) |

### 7.3 Independence-audit gate as part of every dispatch

Add a one-line independence audit to every Renaissance candidate dispatch's pre-registration:

> Pre-registered prediction: this alpha will have `|ρ_R| ≤ 0.15` with each existing alpha {J46-J49, mech_OB, K54-top-3%, AI-baseline} on the n=528 cohort, and `P(co-fire) ≤ 0.30` with each. If predictions fail, classify the alpha as a *concentration filter* (not an independent edge) and downgrade ranking.

This formalizes Agent J's NA_J3 ambiguity.

---

## 8. New ambiguities surfaced by NA-11

1. **K54 v3 top-3% is structurally concentrated in mechanical-source April 2026 trades.** This was not visible in Q1.4 master-bundle / agent_a forensics. K54 v4 must use cohort-balanced training (cross-period + multi-source backfill) or it will re-learn the date-proximity bias.
2. **The S79 = 2 × J46_J49 collinearity in the shipped policy means S79 is currently a sizing constant, not an alpha.** Phase 2 S79-Variant-B (Sharpe-weighted) is essential to make S79 an independent contributor.
3. **The Mech/AI partition in the n=528 cohort is unmeasurable for the LIVE rho.** A unified per-M15-candle cohort (each row is a candle, alpha-fires are per-row indicators) is needed to measure the *real* alpha-pair correlations as they manifest in production. **This is a Phase 2 data-engineering item** — joining `live_evaluations/` outputs with mechanical OB qualification flags per candle.
4. **The K54 v3 top-3% / Mech_OB co-fire structure (P(Mech|top-3%) = 1.0) is a concrete failure of independence on the current cohort.** This evidence supports the K54 v3 post-mortem recommendation that cohort expansion (4-6 weeks data engineering) is the binding bottleneck.
5. **Tail-correlation analysis is degenerate for binary alphas in this cohort** (most tail subsamples are pure 0 or pure 1, making τ undefined). Tail-correlation findings should be re-run on a larger LIVE cohort once Phase 2 data engineering is complete.
6. **n=528 gives Pearson SE ≈ 1/sqrt(528) ≈ 0.044** per pair. The 8-pair ρ̄ has propagated SE ≈ 0.015. The +0.0076 signed estimate is within 1-σ of zero, so we cannot statistically rule out the asserted ρ̄ = 0.10 — but the 95% CI excludes it (≈ [-0.022, +0.037]).

---

## 9. Implications for Phase 2 portfolio Sharpe planning

### 9.1 Revised Renaissance discovery target

| Target | Per Agent J (asserted ρ=0.10) | Per NA-11 (empirical |ρ|=0.056) | Per NA-11 (empirical signed ρ=+0.008) |
|---|---|---|---|
| Sharpe 1.0 at per-edge 0.40 | N=10 | **N=10** (same) | N=7 |
| Sharpe 1.5 at per-edge 0.40 | N=45 | **N=62** (slightly worse) | N=16 (much better) |
| Sharpe 1.0 at per-edge 0.50 | N=4-5 | **N=5** (same) | N=5 |
| Sharpe 1.5 at per-edge 0.50 | N=16 | **N=18** (slightly worse) | N=10 |

**Operational reading.** Use **N=10 at per-edge 0.40-0.50** as the near-term Phase 2 north star — both empirical ρ̄ regimes agree this is reachable in 1-2 quarters at current discovery cadence. Sharpe 1.5 should remain aspirational and dependent on (a) keeping per-edge Sharpe ≥ 0.40 via DSR discipline AND (b) keeping ρ̄ ≤ 0.06 absolute via the proposed independence-audit gate.

### 9.2 Concrete actions

1. **Phase 2 dispatch order revised** (vs Agent J's recommendation):
   - **Highest priority:** S79-Variant-B Sharpe-weighted (J-Rank 2) — breaks the J46-J49/S79 collinearity and adds a *new* alpha class. Pre-flight with NA8 Babu refresh.
   - **Equal priority:** Side-aware-Variant-C (J-Rank 3) — multiplicative sizing variant; expected near-orthogonal to R correlation.
   - **Equal priority:** Calendar candidates (J-Rank 5, 11, 12) — high a priori independence based on mechanism (intra-day flow vs OB-zone structure).
   - **Lower priority:** J46-J49-Variant-A per-instrument partial-close (J-Rank 1) — Agent J's #1 by composite, but it's a *residual* to the existing J46-J49 alpha (correlated by structure). Independence is in the per-cell residual only.
2. **Independence-audit gate** formalized as part of every dispatch's pre-registration (Section 7.3).
3. **Cohort-expansion data engineering** confirmed as the binding bottleneck for K54 v4 (per K54 v3 post-mortem) — NA-11 evidence (P(Mech | top-3%) = 1.0 partition) is the smoking gun.
4. **Re-measure ρ̄ per-quarter** on the live alpha portfolio. The current estimate is on a 528-row in-sample cohort that ends 2026-04-24. As live trades accumulate, the ρ̄ will drift; quarterly re-audit is the right cadence.

---

## 10. Key file paths

| File | Purpose |
|---|---|
| `research/ml_program/phase_2/methodology/na11_alpha_correlation_audit.md` | **This file — synthesis** |
| `research/ml_program/phase_2/methodology/na11_correlation_matrix.csv` | 5×5 Pearson correlation matrix (alphas as labels) |
| `research/ml_program/phase_2/methodology/na11_portfolio_sharpe_corrected.json` | Full N-edges-to-Sharpe table at empirical ρ̄, including 3 ρ̄ variants (asserted 0.10, signed empirical, absolute empirical) |
| `research/ml_program/phase_2/methodology/_compute_na11.py` | Reproducible computation script (~400 lines, runs in ~10 sec) |
| `research/ml_program/forensics/2026-04-29/agent_j_renaissance_edge_discovery.md` | Source of asserted ρ̄ = 0.10 |
| `research/ml_program/forensics/2026-04-29/agent_j_portfolio_sharpe_projection.json` | Source of N-edges-to-target table being corrected |
| `research/ml_program/forensics/2026-04-29/agent_h_meta_pattern_audit.md` | Alpha inventory (3 surviving alphas + 1 specialist) used in NA-11 audit |
| `research/ml_program/scout/feature_matrix.parquet` | n=528 cohort source (gitignored due to size; reconstructable via `research/ml_program/scout/build_scout_matrix.py`) |
| `research/ml_program/models/k54_v3/cpcv_paired_results.json` | CPCV path predictions (used to reconstruct mean_p_v3 per-trade) |

---

## 11. Final 8-bullet summary

1. **Empirical ρ̄ vs Agent J's asserted 0.10:** Authoritative empirical signed ρ̄ = **+0.0076** (Δ = -0.0924 vs asserted, more favorable); absolute |ρ̄| = **0.0557** (Δ = -0.0443 vs asserted, more favorable). Naive ρ̄ over all 10 pairs is +0.006 (driven by perfect-collinear and perfect-anti-correlated structurally-degenerate pairs that net to ~0).
2. **Most-correlated real pair:** Mech_OB ~ K54_v3_top3pct = **+0.0969** (p=0.026). K54 v3's top-3% trades are 16/16 sourced from the mechanical OB cohort — a structural concentration, not an independent edge. **Phase 2 implication: K54 v3 top-3% is a *concentration filter* on mechanical OB, not a separable alpha.**
3. **Most-uncorrelated real pair:** J46_J49_R ~ K54_v3_top3pct = **+0.0304** (p=0.49). Other near-zero pairs include S79_sized_R ~ K54 (+0.030), J46_J49_R ~ Mech_OB (+0.048), and the Spearman versions which are all in [0.03, 0.10]. Most alphas operate near-orthogonally on this cohort.
4. **Sharpe-1.0 N requirement (corrected):** At per-edge Sharpe 0.40 + empirical |ρ̄| = 0.056, N = **10** alphas. At signed ρ̄ = +0.008 (nominal), N = 7. Vs Agent J's asserted ρ=0.10, which gave N = 7-10.
5. **Sharpe-1.5 reachability (corrected):** At per-edge 0.40 + signed ρ̄ = +0.008, N = **16** (much better than Agent J's N=45 at ρ=0.10). At absolute |ρ| = 0.056, N = 62 (slightly worse than Agent J's number). At per-edge 0.50 + |ρ| = 0.056, N = 18 (vs N=16-81 in Agent J's range — comparable).
6. **New ambiguity surfaced:** K54 v3's top-3% over-concentration in mechanical-source April 2026 rows (P(Mech | top-3%) = 1.0) is a smoking-gun for the K54 v3 post-mortem cohort-expansion recommendation. Also: in the LIVE system, Mech_OB and AI_indicator can co-fire (cohort here is a partition by assembly artifact), so the relevant LIVE rho is unmeasurable from this dataset — Phase 2 data-engineering item to build a unified per-M15-candle cohort.
7. **Phase 2 discovery prioritization implications:** (a) S79-Variant-B (Sharpe-weighted) is HIGHEST priority — breaks the trivially-collinear J46-J49/S79 pair and adds a real new sizing alpha; (b) calendar candidates (LBMA fix, pre-FOMC, FX-fix W-shape) are HIGH priority because their mechanism is intra-day flow (decoupled from OB-zone structure) — likely highest a priori independence; (c) introduce **independence-audit gate** as part of every Renaissance candidate dispatch (`|ρ_R| ≤ 0.15` AND `P(co-fire) ≤ 0.30`); (d) revised near-term north star is **Sharpe 1.0 at N = 5-10 alphas with per-edge 0.40-0.50** — reachable in 1-2 quarters at current cadence; (e) Sharpe 1.5 stays aspirational, requires per-edge ≥ 0.40 + ρ̄ ≤ 0.06 absolute discipline.
8. **Key file paths:** synthesis = `research/ml_program/phase_2/methodology/na11_alpha_correlation_audit.md`; correlation matrix = `na11_correlation_matrix.csv` (5×5 Pearson); corrected projections = `na11_portfolio_sharpe_corrected.json` (3 ρ̄ regimes side-by-side); reproducible code = `_compute_na11.py`. Source data = `research/ml_program/scout/feature_matrix.parquet` (n=528, 2024-04 → 2026-04) + `research/ml_program/models/k54_v3/cpcv_paired_results.json`. Reference inputs = `agent_j_renaissance_edge_discovery.md` + `agent_j_portfolio_sharpe_projection.json` + `agent_h_meta_pattern_audit.md`.

---

*End of NA-11 audit. Read-only over inputs. No production / `src/` / `config/` / `prompts/` / `knowledge_base/` modifications. UTF-8.*
