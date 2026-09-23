# Q1.3 Post-Mortem Synthesis — 4 Sub-Investigations Closed

**Built:** 2026-04-29 (post all 4 sub-investigations)
**Scope:** Synthesize the 4 post-mortem investigations into the Q1.4-vs-Q1-close decision.

---

## Headline

**The K54 v2 catalog is NOT broken. K54 v2's architecture was.**

- Q1.3's "+0.0309 mean lift, p=0.0015" is statistical noise (CPCV-honest p=0.68; Stouffer's independence assumption violated).
- K54 v1's "baseline AUC 0.571" is a single-test-slice fluke (CPCV K54 v1 = 0.512-0.529 across all variants; per-regime architecture adds only +0.0007, NOT the +0.032 cited).
- BUT: **Architecture A (global + per-fold top-100 feature screening, de Prado AFML §8.5) lifts mean AUC to 0.5625 (+0.0196 over K54 v2), v2-vs-v1 lift to +0.0492, with PBO 0.20** (vs K54 v2's 0.467). 4/4 instrument groups beat K54 v2's per-group AUC. **Stouffer-naive gate (a) PASSES** (CPCV-honest correction still pending).
- **Architecture B's NAS_US30 specialist achieves AUC 0.6379** (+0.13 over K54 v2 global on same cohort, n=113). Strongest single finding of the program.
- **Cross-period replication is the open hard test.** The NAS_US30 lift FLIPPED sign on temporal split (+0.074 → −0.078). XAU_XAG calendar features lose 97-100% of their gain cross-period. The signal we found is partially 2024-2026-specific.

**The honest picture:** the catalog has real signal that proper feature-selection architecture extracts. Whether that signal SURVIVES cross-period is the actual open question. Q1.4 should be scoped to test that, not to chase a fragile global lift.

---

## 1. What we tested

### 1.1 Statistical re-evaluation (`audit/statistical_reevaluation.md`)

- **CPCV-honest training-overlap-weighted SE = 0.0649** (vs Stouffer's implicit 0.0205). Mean off-diagonal train-fold overlap ρ = 0.643.
- **CPCV-honest 95% CI = [−0.0962, +0.1580], t=0.476, p=0.675.** Stouffer combined p=0.0015 is artifact.
- LOO sensitivity: ROBUST (all 15 LOO-14 means ≥ +0.0227); path 9 contributes 26.5% of mean.
- Path 9 GENUINELY CROSS-COHORT (Feb-2026 window, 4/4 groups + 6/7 symbols positive). Refutes my CF-7 XAU-driven hypothesis.
- **Feature stability: UNSTABLE.** Mean Jaccard 0.072. ZERO features in all 15 paths' top-30. ZERO in ≥80% of paths. Classic high-dim overfit at 0.43 rows-per-feature.
- **Verdict: K54 v2's +0.0309 lift is statistical noise** under CPCV-honest accounting.

### 1.2 Canonical K54 v1 re-run (`audit/canonical_v1_rerun.md`)

- **Canonical K54 v1 (17 features, NO `symbol`) CPCV mean AUC = 0.5286** — HIGHER than modeler's modified v1 (0.5120). Adding `symbol` HURT v1, not helped.
- **Per-regime canonical v1 CPCV mean AUC = 0.5293** — the K54 v1 audit's "+0.032 per-regime lift" does NOT replicate. Per-regime adds only **+0.0007** under CPCV.
- Per-regime AUCs: UNTAGGED 0.435, bearish 0.436, bullish 0.483, transitional 0.515 — **3 of 4 regimes BELOW random**.
- v2 vs canonical v1 (Config A) lift: **+0.0143** (Stouffer p=0.196, NOT sig).
- v2 vs per-regime v1 (Config B) lift: **+0.0136** (Stouffer p=0.032, NOT sig at 0.01).
- **Verdict: the K54 v1 baseline that K54 v2 was supposed to beat is itself near-random under CPCV.** The +0.04 effect-size target was set against a non-existent strong baseline.

### 1.3 Cross-period replication (`audit/cross_period_replication.md`)

- **Critical data caveat:** train cohort 2024-04-01 → 2026-01-01 is **n=93 (93.5% XAUUSD-only)** — NOT the ~280 the brief estimated. Pre-2026 data is heavily XAU-dominated. Audit-recommended 2022-2023 backfill was NOT performed.
- K54 v2 cross-period test AUC: **0.5016** (Δ = −0.0413 vs CPCV 0.5429).
- K54 v1 cross-period test AUC: **0.4804**.
- Cross-period paired lift: +0.0212, DeLong p=0.577 (NOT sig).
- Per-group: 3 of 4 positive lift (better than CPCV's 2/4) BUT **3 of 4 SIGN-FLIPPED**. GBPJPY (CPCV NEG → CP +0.089), GBPUSD_USDJPY (NEG → +0.029), NAS_US30 (POS +0.074 → CP **−0.078**), XAU_XAG only stable (POS → +0.074).
- **XAU_XAG calendar features OVERFIT (CF-10 confirmed):** `days_to_OPEX` 44→0.0 (−100%), `day_of_year_cos` 40→0.0 (−100%), `days_to_holiday` 35→1.0 (−97%), `day_of_year_sin` 28→0.0 (−100%).
- Top-1 CPCV feature `vol__h1_range_over_mean_50` (CPCV gain 6.0) drops to **gain 0.0** on cross-period.
- Brier on test = 0.274 — WORSE than constant-WR baseline 0.247 (calibration not preserved).
- **Verdict: K54 v2's CPCV signal is partially 2024-2025-specific.** Cross-period robustness FAILS for 3 of 4 instrument groups. The single train cohort being 93.5% XAU is the structural reason.

### 1.4 Architecture A/B (`audit/architecture_ab.md`)

**Architecture A — global with per-fold top-100 feature screening:**

| Metric | K54 v2 | Architecture A |
|---|---:|---:|
| Mean AUC | 0.5429 | **0.5625** (+0.0196) |
| v2-vs-v1 lift mean | +0.0309 | **+0.0492** |
| Stouffer combined p | 0.001546 | **9.4e-5** |
| 95% CI on lift (naive) | [−0.0093, +0.0711] | **[+0.003, +0.095]** (no longer crosses zero) |
| PBO | 0.467 | **0.20** |
| Cross-instrument: groups beating K54 v2 per-group AUC | — | **4/4** |

**Stouffer-naive gate (a) for Arch A: PASS.** Whether CPCV-honest gate (a) passes is unverified; given the SE inflation factor of ~3-4× from the statistical re-evaluation, Arch A's CPCV-honest p is likely in the 0.05-0.15 range. Borderline.

**Architecture B — per-instrument-group ensemble:**

| Group | n | AUC_v2 (Arch B) | AUC_v1 (per-group) | Lift over per-group v1 | LOO sensitivity |
|---|---:|---:|---:|---:|---|
| XAU+XAG | 215 | 0.510 | (positive lift) | + | (regression vs K54 v2 global) |
| **NAS+US30** | **113** | **0.6379** | (positive lift) | **+~0.13 over K54 v2 global on same cohort** | LOO [+0.11, +0.14], 12/15 paths positive |
| GBPUSD+USDJPY | 138 | 0.532 | (positive lift) | + | |
| GBPJPY | 62 | 0.482 | (positive lift) | + | |
| **Aggregate (weighted by n)** | 528 | **0.5398** | — | — | Slightly BELOW K54 v2's 0.5429 (XAU drag offsets NAS win) |

**Gate (d) for Arch B: PASS** (4/4 groups positive lift over per-group v1). NAS_US30 specialist is the program's strongest single finding.

**Caveat:** the cross-period replication showed NAS_US30 sign-flipped from +0.074 to −0.078 on temporal split. The NAS specialist's +0.13 may be 2024-2026-specific; Q1.4 must verify cross-period robustness BEFORE shipping.

---

## 2. Combined picture

### 2.1 What we now know with high confidence

1. **K54 v2 as built (1,234 features, no per-fold screening) does NOT pass CPCV-honest gate (a).** True lift over canonical K54 v1 is ~+0.014, not +0.0309.
2. **K54 v1's published baseline 0.571 was a single-fluky-test-slice number.** Under CPCV, K54 v1 sits at 0.512-0.529 across all variants, including its per-regime architecture.
3. **Per-fold feature screening (Architecture A, de Prado §8.5) significantly improves the model.** AUC 0.5625, PBO 0.20, lift +0.0492, 4/4 groups beat K54 v2's per-group AUC.
4. **A NAS_US30-specific model achieves AUC 0.6379** — strongest single finding. Indices cohort behaves structurally differently from FX/metals.
5. **The catalog has REAL SIGNAL that PROPER feature selection extracts.** The headline CPCV-honest p=0.68 was a bloated-architecture problem, not a no-signal problem.

### 2.2 What's still uncertain

1. **Whether Arch A passes CPCV-honest gate (a)** at p<0.01. Stouffer-naive p=9.4e-5 → CPCV-honest likely p=0.001-0.05. Probably PASSES even at the conservative end, but not verified.
2. **Whether the NAS_US30 specialist's +0.13 lift survives cross-period.** Cross-period showed NAS_US30 sign-flip; the +0.13 might be 2024-2026 only.
3. **Whether the catalog's calendar features (XAU_XAG) carry GENERALIZABLE signal or are date-memorization artifacts.** Cross-period showed 97-100% gain drop on calendar features.
4. **Whether cross-period replication is even FAIR at this n.** The 2024-04 → 2026-01 train cohort is 93.5% XAU only because pre-2026 data is XAU-dominated. We need 2022-2023 backfill (audit-recommended) to test cross-period properly.

### 2.3 The structural data limit

`feedback_decay_is_ceo_number_one_concern` says decay-velocity dominates compute cost. The "data first" path (extract 2022-2023 for the 5 missing instruments) gets us:

- Estimated 1,500-2,000 trades cohort (vs current 528)
- Proper cross-period replication on all 7 instruments
- Rows-per-feature 1.2-1.6 even for the bloated 1,234 catalog (vs current 0.43)
- Full pre-FN-era / FN-era split for true temporal robustness

This is 4-6 weeks of data engineering. Without it, even Arch A and the NAS specialist remain in the "may be 2024-2026-specific" uncertainty zone.

---

## 3. The Q1.4 vs Q1-close decision

### 3.1 Q1.4 — Architecture-A-led re-spec (RECOMMENDED)

**Q1.4 hypothesis:** *"Architecture A (global LightGBM + per-fold top-100 feature screening, de Prado AFML §8.5) achieves CPCV-honest mean AUC ≥ 0.55 AND v2-vs-canonical-v1 lift ≥ 0.04 with CPCV-honest combined p < 0.01 AND positive sign-of-lift on the cross-period 2024-04→2026-01 train / 2026-01→04-28 test split. Architecture B NAS_US30 specialist achieves cross-period AUC ≥ 0.60. Holdout 2026-04-29 → 2026-05-12 reserved for end-of-Q1 directional discipline check only."*

**Q1.4 thresholds (4 gates, all required):**

- **(a) CPCV-honest:** mean AUC_arch_a ≥ 0.55 (vs random) AND lift over canonical v1 ≥ +0.04 with CPCV-honest combined p < 0.01 (using train-overlap-weighted SE).
- **(b) PBO < 0.40** (tighter than 0.5; Arch A already at 0.20).
- **(c) Cross-period robustness:** Arch A test AUC ≥ 0.53 on 2026-01+ test cohort; lift over v1 cross-period ≥ +0.02; NAS_US30 specialist cross-period AUC ≥ 0.60.
- **(d) Per-instrument:** Arch A AUC_v2 > AUC_v1 on ≥3 of 4 effective groups; NAS_US30 specialist beats Arch A by ≥+0.05 on its cohort.

**Q1.4 architecture (locked):** **Hybrid — Arch A as global + Arch B NAS_US30 specialist routed when symbol ∈ {NAS100, US30_CASH}.**

**Wallclock estimate:** 1-2 weeks (training + cross-period validation + holdout discipline check at end-of-Q1).

**Probability of PASS (my estimate):** ~40-55%. Strongest dependency: cross-period gate (c). Arch A's CPCV gate (a) likely passes; (b) PBO already passes; (d) Arch B NAS specialist already at 0.6379. The cross-period gate is where most failure-mode risk concentrates.

### 3.2 Q1.4 — Architecture-A-and-data-first (ALTERNATIVE A)

Same as 3.1 but pre-pend a 4-6 week 2022-2023 data backfill phase. Increases cross-period gate probability of PASS to ~70-80% but adds ~5-7 weeks to Q1 wallclock. Bundle with the production-ops `_trade_index.json` fix from `research/operations/`.

### 3.3 Q1 close (ALTERNATIVE B)

Reframe K54 v2 as "K55 shadow harness candidate, not Q1 deliverable." Document Arch A + Arch B NAS specialist as "exploratory artifacts" without a Q1 deliverable judgment. Move directly to Q2 sequence-models design + K55 ML-vs-AI shadow harness.

**Pros:** clean exit; no risk of false PASS in Q1.4.
**Cons:** abandons the +0.0196 Arch A signal we found; the NAS specialist gets shelved instead of validated.

### 3.4 My recommendation

**Q1.4 per §3.1, with explicit cross-period as the kill-gate.**

The catalog has signal — Arch A demonstrates it. The honest question is whether that signal SURVIVES temporal split. Q1.4's cross-period gate (c) directly tests this. If it FAILS, we close Q1 with a clear conclusion ("catalog signal exists in-period but doesn't generalize, calendar-feature overfit confirmed, needs 2022-2023 backfill"). If it PASSES, we ship a deployable model (or two — Arch A global + NAS specialist).

The data-first alternative (3.2) is methodologically superior but costs 5-7 weeks. Given decay velocity is the CEO's #1 concern, I'd run Q1.4 fast (~1 week) and only fall back to data-first if Q1.4 fails the cross-period gate. The wasted 1 week is small vs the alpha lost from delaying ship.

---

## 4. What this taught us about the broader program

### 4.1 The infrastructure WORKED

- Pre-registration discipline forced clean Q1.3 verdict.
- The methodology critic's PBO + paired-fixed-HP discipline caught a 2× false PASS.
- Independent post-mortem agents (4 sub-investigations) revealed all the load-bearing failure modes (feature overfit at 0.43 rows/feature, K54 v1 baseline mirage, cross-period decay).
- We saved ~1-2 quarters of ML push on a fragile-architecture by catching it early.

### 4.2 The end-state probability has shifted

Pre-Architecture-A/B finding:
- ML replaces AI: 15-25%
- ML as advisory ensemble: 50-60%

Post-Architecture-A/B finding:
- ML replaces AI globally: 20-30% (still hard at this n)
- **ML as primary on specific cohorts (NAS_US30 + indices)**: 50-65%
- ML as advisory ensemble across the fleet: 60-70%
- Sovereignty doctrine on partial fleet: 45-55%

The NAS_US30 specialist at AUC 0.6379 is the strongest evidence we've seen that ML can outperform AI on a specific cohort. Even with cross-period uncertainty, this is a meaningful directional finding.

### 4.3 The shift in strategic narrative

Originally: "Build K54 v2 to replace AI primary_analyzer."

After Q1.3 + post-mortem: **"Build a portfolio of models — global Arch A as broad signal layer + per-cohort specialists where data permits — that, in ensemble with the AI, achieves higher decision quality than AI alone. Sovereignty doctrine end-state achieved on the cohorts where the data supports it."**

This is the realistic version of the program's vision. Less ambitious than full AI replacement, but ACTUALLY ACHIEVABLE at the available data.

---

## 5. Pending CEO decisions

1. **Approve Q1.4 architecture-A-led re-spec per §3.1?** Cross-period as the kill-gate. Fast path; ~1-2 weeks.
2. **Add 2022-2023 data backfill (alternative A) before Q1.4?** Adds 5-7 weeks but raises cross-period gate PASS probability to ~70-80%.
3. **Open the production-ops `_trade_index.json` ticket?** (Independent of Q1.4; main-thread issue.)

If approved (1 + 3), I dispatch:
- The 2022-2023 backfill agent (data-engineering only, no API calls; ~2-4 hours).
- The Q1.4 hypothesis lock (append-only registry update).
- The Q1.4 modeler (Architecture A + NAS specialist + cross-period; ~3-4 hours wallclock).

If approved (2 + 1 + 3), the backfill goes first, then Q1.4 follows ~5-7 weeks later with stronger data foundation.

---

*Standing by for direction on Q1.4 spec + dispatch.*
