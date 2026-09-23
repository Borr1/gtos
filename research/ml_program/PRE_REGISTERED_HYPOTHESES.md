# Pre-Registered Hypotheses

This registry is **append-only**. No retroactive edits to past entries. Editing a past entry (other than the explicitly editable status fields below) invalidates it.

Threshold-or-fail: a hypothesis without a measured outcome on its threshold is incomplete. PASS / FAIL / INVALIDATED_PRE_TEST is the only acceptable terminal status.

**Editable status fields per entry (the ONLY fields that may change post-registration):**

- `Holdout LOCKED` (NO → YES, with date)
- `Holdout opened` (NO → YES, with date — flips ONCE; flipping twice invalidates)
- `Result` (PENDING → PASS | FAIL | INVALIDATED_PRE_TEST)
- `Result date`
- `Why it passed/failed`
- `Audit trail link` (may be added after registration to point at the deciding artifact)

**Status definitions:**

- `PASS` — hypothesis was tested per its discipline and the threshold was met.
- `FAIL` — hypothesis was tested per its discipline and the threshold was NOT met. → write a why-it-failed memo to `KILLED_HYPOTHESES.md`.
- `INVALIDATED_PRE_TEST` — hypothesis cannot be tested as written because of a methodology defect discovered before testing (e.g., the named holdout was burned by prior research). The entry remains for audit trail but is superseded by a re-spec'd entry.

---

## Q1.1 — K54 v2 expanded feature catalog (PRIMARY) — *INVALIDATED_PRE_TEST; superseded by Q1.2*

- **Date pre-registered:** 2026-04-28
- **Pre-registered by:** ML Program Orchestrator (program kickoff)
- **Phase:** Q1 — Foundation: data + features + K54 v2
- **Hypothesis:** *"An expanded 2K-feature catalog (4× the K54 v1 feature set) lifts a per-regime LightGBM's OOS AUC by ≥0.04, from K54 v1's baseline of 0.571 to ≥0.61, on a held-out 2026-H2 window with strict CPCV + purge gaps."*
- **Threshold:** OOS AUC ≥ 0.61 on the 30% holdout, opened ONCE per the discipline below.
- **Holdout date range:** Never locked.
- **Holdout LOCKED:** NO
- **Holdout opened:** NO
- **Result:** INVALIDATED_PRE_TEST
- **Result date:** 2026-04-28
- **Why it passed/failed:** K54 v1's de-facto holdout slice (2026-04-01 → 2026-04-24, n=94) was peeked at by K55 (`dd6a855`), F11 (`605cb74`), F15 (`a0e39de`), F4, A4, A6 per `research/ml_program/k54_v1_audit.md` Section 3. Per de Prado discipline, peeked = burned. The registered text "2026-H2" was further ambiguous — 2026-04 is late-H1. Q1.1 invalidated before any K54 v2 training data was touched. Superseded by Q1.2.
- **Audit trail link:** `research/ml_program/k54_v1_audit.md`

---

## Q1.2 — K54 v2 expanded feature catalog (PRIMARY, supersedes Q1.1)

- **Date pre-registered:** 2026-04-28 20:00 UTC
- **Pre-registered by:** ML Program Orchestrator (post-K54-v1-audit re-spec; CEO-approved Path B)
- **Phase:** Q1 — Foundation: data + features + K54 v2
- **Hypothesis:** *"An expanded 2K-feature catalog (4× the K54 v1 feature set) lifts a per-regime LightGBM's AUC by ≥0.04, from K54 v1's baseline of 0.571 to ≥0.61, when validated via CPCV-with-purge over data from 2024-02-20 (F14 backfill start) → 2026-04-28 (training population) AND on a 14-day prospective live holdout from 2026-04-29 onward, opened ONCE at the end of Q1."*
- **Threshold:** AUC ≥ 0.61 on **BOTH** of:
   - **(a)** CPCV mean across folds, with explicit purge gaps ≥1 week and embargo ≥1 day.
   - **(b)** 14-day prospective live holdout opened ONCE.
- **Holdout date range:** **2026-04-29 00:00 UTC → 2026-05-12 23:59 UTC** (14 calendar days). Holdout = all M15 candles + setups on the 7 production instruments in this window. NEVER read by feature engineers, modelers, or statisticians until end-of-Q1 evaluation.
- **Holdout LOCKED:** YES — locked 2026-04-28 20:00 UTC.
- **Holdout opened:** NO
- **Result:** PENDING
- **Result date:** —
- **Why it passed/failed:** —
- **Audit trail link:** `research/ml_program/k54_v1_audit.md`

**Notes:**

- Statistical-power note: 14 calendar days × ~17 trades/month system frequency = ~8 fleet setups; M15-candle-level evaluation gives ~9k candles which is plenty for AUC SE control. Setup-level n is small; CPCV gate (a) carries the primary statistical weight, holdout gate (b) is the leakage-discipline check.
- **All Weeks 2-6 data work must restrict to ≤2026-04-28 timestamps.** This constraint is communicated to all dispatched agents.
- The holdout window is fixed at 2026-04-29 → 2026-05-12 regardless of Q1 wallclock. If Q1 finishes before 2026-05-13, evaluation waits until the holdout window completes. If Q1 finishes later, the holdout is what it is — no extension.
- "Opened ONCE" means a single evaluation pass at end-of-Q1: feed the locked feature catalog + locked trained model on the 14-day data, record AUC on (a) CPCV and (b) holdout, write Result. Subsequent peeks at the holdout invalidate the result.

**Validation discipline (every primary hypothesis must satisfy ALL):**

1. Pre-registration in this file BEFORE data work.
2. CPCV with explicit purge gaps (de Prado, *AFML* ch. 7).
3. 30% OOS holdout opened ONCE per phase (the 14-day prospective holdout fills this role for Q1.2; CPCV is the bulk of the validation).
4. White-noise null test (shuffle labels ×100; result must beat null distribution at p<0.01).
5. Multiple-comparison correction (Bonferroni primary; BH-FDR exploratory).
6. Cross-instrument replication (works on ≥4 of 7 instruments).
7. Cross-period replication (works on ≥2 of {2022-2023, 2024-2025, 2026}).
8. Independent adversarial validator (leakage hunter, robustness probe, survivorship-bias check).
9. Decay velocity benchmark (model's expected useful life, NOT just peak Sharpe).
10. Replication on a different model class (LightGBM → RandomForest sign preservation).

Failing ANY of the above means the hypothesis is exploratory only, not promotable.

---

---

## Q1.3 — K54 v2 expanded feature catalog (PRIMARY, supersedes Q1.2 gate (b) per methodology critique)

- **Date pre-registered:** 2026-04-28 23:30 UTC
- **Pre-registered by:** ML Program Orchestrator (post-methodology-critique re-spec; CEO-approved Path B)
- **Phase:** Q1 — Foundation: data + features + K54 v2
- **Hypothesis:** *"An expanded 1,219-feature catalog (vs K54 v1's 17) lifts a global LightGBM (regime-as-feature) AUC by ≥0.04, from K54 v1's baseline of 0.571 to ≥0.61, when validated via combinatorial-purged CV (K=6, N=2; 15 paths) with explicit purge gaps ≥1 week and embargo ≥1 day, on training data from 2024-02-20 → 2026-04-28. AUC measurement is paired (v2 vs v1 on identical CPCV folds), with PBO < 0.5 to confirm non-overfitting. A 14-day prospective holdout window 2026-04-29 → 2026-05-12 serves as a directional-discipline check (sign of lift, calibration retention, no per-instrument sign-flip), NOT as a numeric AUC gate."*
- **Thresholds (ALL required):**
   - **(a) CPCV paired:** mean(AUC_v2 − AUC_v1) ≥ 0.04 AND DeLong p < 0.01 across 15 CPCV paths.
   - **(b) PBO:** Probability of Backtest Overfitting < 0.5 over hyperparameter selection grid.
   - **(c) Holdout discipline:** Holdout AUC > 0.50 AND Holdout Brier ≤ 1.20× CPCV Brier AND Holdout (AUC_v2 − AUC_v1_paired) > 0.
   - **(d) Cross-instrument:** AUC_v2 > AUC_v1 on at least 3 of 5 effective-independent instrument groups {XAU+XAG, NAS100+US30, GBPJPY, GBPUSD+USDJPY, residual}, with per-group n ≥ 30.
   - **(e) White-noise null:** B=1000 shuffles, observed AUC ≥ permutation p<0.01 boundary with margin.
- **Holdout date range:** 2026-04-29 00:00 UTC → 2026-05-12 23:59 UTC (inherited from Q1.2 lock).
- **Holdout LOCKED:** YES (inherited 2026-04-28 20:00 UTC; Q1.3 lock at 2026-04-28 23:30 UTC does not re-open).
- **Holdout opened:** NO
- **Result:** FAIL
- **Result date:** 2026-04-28 (CPCV+PBO+null+cross-instrument; gate c deferred)
- **Why it passed/failed:** Gate (a) FAIL: mean(AUC_v2-AUC_v1)=+0.0309 (gate >=0.04, fails on effect-size threshold), DeLong combined p=0.001546 (passes <0.01 — lift IS statistically significant, just not large enough). Gate (b) PBO=0.4667 PASS (gate <0.5; borderline). Gate (d) Cross-instrument 2/4 eligible groups (XAU+XAG +0.036, NAS+US30 +0.074) with positive lift; GBPJPY (-0.016) and GBPUSD+USDJPY (-0.028) had negative lift. FAIL (gate >=3 of 5; only 4 effective groups exist for our 7-symbol set since no symbol falls into 'residual'). Gate (e) Null (B=1000) obs=0.5429 (CPCV-honest fixed-HP) vs p99=0.5365, p_emp=0.003 PASS (gate obs>=p99 AND p_emp<0.01). Gate (c) Holdout discipline DEFERRED to end-of-Q1 (Week 6 close, on/after 2026-05-13) per Q1.3 spec; not evaluated in Week 4. Final verdict 2 PASS (b, e) / 2 FAIL (a, d): K54 v2 lift IS detectable above white-noise (p_emp=0.003) but BELOW the pre-registered effect-size threshold (+0.0309 vs >=0.04 required) and inconsistent across instrument groups. Recommend why-it-failed memo to KILLED_HYPOTHESES.md + Q1.4 re-spec, NOT holdout open.
- **Audit trail link:** `research/ml_program/audit/methodology_critique.md` (proposed text §6.2); `research/ml_program/audit/PRE_WEEK4_SYNTHESIS.md` (synthesis + CEO approval).

**Differences from Q1.2:**

1. Architecture changed from per-regime LightGBM ensemble to **global LightGBM with regime-as-feature** (per the joint-model scout finding: per-regime drags AUC −0.075pp at this n; data inventory finding: 22/28 cells fail n≥30).
2. Gate (b) numeric AUC ≥ 0.61 on holdout replaced with directional + calibration discipline check (Q1.2 gate (b) was statistically empty at the available holdout n; methodology critic verdict).
3. CPCV explicitly K=6, N=2 (15 paths), with paired comparison (DeLong) — not naive ensemble.
4. PBO added as gate (b).
5. Cross-instrument re-grouped from "≥4 of 7 instruments AUC ≥ 0.61" to "≥3 of 5 effective-independent groups, sign-of-lift, n≥30 floor".
6. White-noise null B=100 → B=1000 (Phipson & Smyth 2010).

---

---

## Q1.4 — K54 v3 master bundle: Architecture A + meta-labeling head + NAS_US30 specialist + Kyle-Obizhaeva pooled multi-instrument (PRIMARY, post-Q1.3-FAIL re-spec)

- **Date pre-registered:** 2026-04-29 (Phase 4 Day-2; post-B-8 Quick-Win Bundle close)
- **Pre-registered by:** ML Program Orchestrator (CEO-approved post B-8 synthesis, Day-2 spec lock)
- **Phase:** Q1 — Foundation: data + features + K54 v3
- **Hypothesis:** *"A K54 v3 model architected as (i) global LightGBM with per-fold top-100 feature screening (de Prado AFML §8.5; Architecture A from Q1.3 audit), (ii) Lopez-de-Prado meta-labeling secondary classifier on triple-barrier outcome labels (TP/SL/TIMEOUT) feeding sizing in {0, 0.5, 1.0} × `risk_per_trade_pct`, (iii) Kyle-Obizhaeva W-unit pooled training across 7 instruments with one-hot instrument-id, and (iv) NAS_US30 specialist routing layer activated when `symbol ∈ {NAS100, US30_cash}` will achieve, on the post-2022-2023-backfill cohort (n ≈ 2,326), all gates (a-g) below. K-4 Stoikov micro-price is DROPPED from scope (KILLED 2026-04-29 by B-8 dispatch — MT5 retail tick has volume=0 + last=0; no LOB depth). K-1 volume-bar resampling is replaced with K-1' tick-count-time bars (Glattfelder-Dupuis-Olsen 2011) since MT5 retail volume=0."*

- **Thresholds (ALL required):**
   - **(a) CPCV-honest mean AUC:** mean K54 v3 AUC across 15 paths ≥ **0.55** under CPCV-honest training-overlap-weighted SE (Group A M7).
   - **(b) Lift over CPCV-honest K54 v1 baseline 0.5286** (NOT 0.571 — that baseline FAILED DSR per B-8 sweep): **≥ +0.04** with DSR-p < 0.01 (Bailey-Lopez de Prado deflation, N≥200) AND PBO < 0.4 (CSCV) AND B=1000 null p ≥ 0.99.
   - **(c) Cross-period robustness on TWO splits (both required):**
      - (c.i) Train 2022-2023 / test 2024-2026: lift sign preserved AND magnitude within ±50% of CPCV mean.
      - (c.ii) Train ≤ 2026-01-01 / test 2026-01-01+: lift sign preserved AND per-cohort sign positive on ≥3 of 4 effective groups.
   - **(d) Per-instrument-group floor:** K54 v3 AUC ≥ **0.50** on ALL 4 effective groups (XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY); NAS_US30 specialist beats global K54 v3 by **≥ +0.05** on its cohort.
   - **(e) Realized-R lift on J46-J49 holdout:** ≥ **+0.05R/trade** with stationary block bootstrap (Politis-Romano) p < 0.01.
   - **(f) Feature stability:** ≥30 features in top-50 across ≥80% of CPCV paths (Jaccard overlap ≥ 0.6).
   - **(g) Calibration on 2026-04-29 → 2026-05-12 holdout:** Christoffersen interval-coverage test PASS at α=0.05.

- **Holdout date range:** 2026-04-29 00:00 UTC → 2026-05-12 23:59 UTC (inherited from Q1.2/Q1.3 lock; opens ONCE at end-of-Q1).
- **Holdout LOCKED:** YES (inherited 2026-04-28 20:00 UTC; Q1.4 lock 2026-04-29 does not re-open).
- **Holdout opened:** NO
- **Result:** FAIL
- **Result date:** 2026-04-29 (gates a/b/c.i/c.ii/d/e/f evaluated; gate g DEFERRED)
- **Why it passed/failed:** 1/6 testable gates PASS (gate (a) only). Gate (a) PASS: mean AUC=0.5770 ≥ 0.55. Gate (b) FAIL on DSR-p: lift=+0.0484 (≥0.04 ✓), PBO=0.20 (✓), null p_emp=0.000 (✓), but DSR-p=0.321 (gate <0.01 FAIL — same fate as K54 v2 at N=200 trial budget). Gate (c.i) PASS (v1-schema sanity, +0.0481 lift cross-period, 4/4 groups positive); but it tests v1 features only — backfill cohort lacks v2-feature engineering. Gate (c.ii) FAIL: within 2024-2026 lift=-0.022. Gate (d) FAIL: 2/4 groups (NAS_US30 + GBPJPY <0.50); NAS_US30 specialist delta=+0.103 PASS but global floor fails. Gate (e) FAIL: realized-R lift=-0.108R (negative — model removes winning trades). Gate (f) FAIL: 2 stable features, Jaccard 0.169 (overfit signature mirrors Q1.3). Gate (g) DEFERRED to holdout open (2026-05-13+). Diagnostic ablation (`research/ml_program/models/k54_v3/diagnostic_w_unit_ablation.json`) showed raw dollar-volume Kyle-Obizhaeva W-unit catastrophically underperformed (AUC 0.508 vs Arch A 0.561); balanced intra-instrument-vol-rank form recovered to 0.577 but adds essentially nothing over Arch A. Per failure protocol: KILLED memo written + Q1 close recommended; reframe K54 v3 NAS_US30 specialist (AUC 0.601, delta +0.103) as K55-shadow signal candidate.
- **Audit trail link:** `research/ml_program/literature/HYPOTHESIS_BACKLOG.md` §8 (full architectural spec); `research/ml_program/audit/dsr_retroactive_sweep.md` (gate b anchor revision); `research/ml_program/audit/architecture_ab.md` (Architecture A + B Q1.3 foundation); `research/ml_program/experiments/na8_babu_decomposition.md` (H-1-first verdict); `research/ml_program/experiments/q1_dlinear_baseline.md` (Q2 sequence-model NO-GO); `research/ml_program/models/k54_v3/report.md` (K54 v3 modeler report); `research/ml_program/KILLED_HYPOTHESES.md` Q1.4 entry (why-it-failed memo).

**H-1 K54 v3 master bundle scope (revised post-B-8):**

| Element | Status | Source |
|---|---|---|
| K-1' tick-count-time bars (Glattfelder 2011) | NEW substitute for K-1 | MT5 retail volume=0 ceiling |
| ~~K-4 Stoikov micro-price~~ | **DROPPED** | KILLED 2026-04-29 (B-8 dispatch) |
| K-5 + K-6 Kyle-Obizhaeva W-unit pooled training | KEEP | Group B §2.4 |
| K-7 Osler stop-cluster (round-number proxy; no volume needed) | KEEP | Group B §6.1 |
| K-8 power-law-decayed OB-age weighting | KEEP | Group B §6.1 |
| K-9 regime × round_aligned × side interaction | KEEP | Group B + Group D |
| K-10 above-up below-down round-aligned OB direction | KEEP | Bhattacharya 2012 / Zhang 2024 |
| K-11 per-fold top-100 feature screening | KEEP | de Prado AFML §8.5; Q1.3 Architecture A (PBO 0.20) |
| K-12 Lopez-de-Prado meta-labeling secondary head | KEEP | Group F Rank 1; closes AUC-vs-realized-R gap |
| K-13 triple-barrier outcome labels | KEEP | feeds K-12 |
| K-14 adaptive conformal calibration | KEEP | Zaffran 2022; gate (g) prerequisite |
| K-15 TreeSHAP-stability pruning | KEEP | Q1.3 Jaccard 0.072 issue |
| NAS_US30 specialist (Architecture B from Q1.3) | KEEP | AUC 0.6379 in-sample; gate (d) target |

**Differences from Q1.3:**
1. **Architecture extended** — Architecture A is now ONE component of the master bundle, joined by meta-labeling head, K-W-unit pooling, and NAS_US30 specialist routing.
2. **Gate (b) anchor revised** — lift measured against CPCV-honest K54 v1 0.5286, NOT the DSR-failing 0.571 published baseline.
3. **Methodology gate hardened** — DSR-p < 0.01 + PBO < 0.4 + null-p ≥ 0.99 mandatory (was: PBO < 0.5 only at Q1.3).
4. **Cross-period gate (c) split into two** — adds 2022-2023 → 2024-2026 split (newly feasible per data backfill).
5. **Per-instrument-group floor (d) tightened** — was "≥3 of 5 effective groups" with no per-group AUC floor; now "ALL 4 effective groups ≥ 0.50" + NAS_US30 specialist delta gate.
6. **Realized-R gate (e) added** — block bootstrap p<0.01 on ≥+0.05R/trade lift on J46-J49 holdout (J46-J49 baseline survived DSR per B-8 sweep — anchorable).
7. **Feature stability gate (f) added** — top-50 Jaccard ≥ 0.6 (Q1.3 was 0.072 — overfit signature).
8. **K-4 Stoikov dropped from scope** — KILLED by B-8 K-4 dispatch (MT5 retail volume=0 substrate gap).
9. **K-1 replaced with K-1' tick-count-time bars** — Glattfelder 2011 substitute (volume=0 in retail stream blocks volume bars).
10. **Q2 sequence-model phase shelved** — Q-1 DLinear FAIL (B-8 dispatch) shelves Q-2..Q-7 until cohort n≥5,000.

**Validation discipline (must satisfy ALL):**
1. Pre-registration in this file BEFORE data work (this entry).
2. Paired-fixed-HP CPCV with K=6, N=2 + 7-day purge / 1-day embargo (15 paths).
3. CPCV-honest training-overlap-weighted SE (Group A M7); NOT Stouffer-naive.
4. DSR + ONC effective-N + CSCV PBO computed on every primary lift claim.
5. B=1000 null shuffles (Phipson & Smyth 2010).
6. Cross-period replication on TWO splits per gate (c).
7. Per-instrument-group floor per gate (d).
8. Stationary block bootstrap (Politis-Romano) per gate (e).
9. Calibration via Christoffersen interval-coverage test per gate (g).
10. Independent adversarial validator (post-modeler-return audit agent).

---

---

## Q1.5 — K54 v4 Hybrid 5 architecture under canonical v1 baseline + ONC effective_N=11 (PRIMARY, supersedes Q1.4 K54 v3 master bundle re-spec)

- **Date pre-registered:** 2026-04-29 (Phase 2 dispatch sequence — CEO-approved post Phase 2 8-agent forensic close)
- **Pre-registered by:** ML Program Orchestrator (CEO-approved per Phase 2 master synthesis decision #3)
- **Phase:** Q1 — Foundation: data + features + K54 v4 architecture
- **Hypothesis:** *"K54 v4 (Hybrid 5: K54 v3 master bundle on non-NAS_US30 + T7-style per-cohort LightGBM specialist on NAS_US30, identical K=6/N=4 folds, fixed-HP CPCV-honest) trained on Phase 2-A expanded cohort (n ≥ 3,132 = Q1.3 cohort 528 + 2022-2023 v2-feature backfill ~1,798 + GBPJPY+US30 2022-2023 backfill ~806) achieves OOS-AUC paired lift ≥ +0.04 vs canonical K54 v1 (0.5286, NOT modeler-modified `symbol`-augmented v1 0.5133) under K=6/N=4 CPCV (T_paths = 25, purge = 7d, embargo = 1d) with paired-t p < 0.01, Wilcoxon p < 0.05, bootstrap p_one < 0.05, null-perm p < 0.05, PBO < 0.40, AND DSR-p < 0.05 under ONC effective_N = 11. Component-ablation: (a) master bundle's added components (Lopez-de-Prado meta-label + Kyle-Obizhaeva W-units + adaptive conformal) over Arch A pure contribute ≥ +0.02 per-path AUC; (b) T7-NAS-routing over v3-NAS-fall-through contributes ≥ +0.01 per-path AUC. Both component contributions bootstrap p_one < 0.10."*

- **Thresholds (ALL required for PRIMARY PASS — Hybrid 5):**
   - **(a) CPCV-honest mean AUC:** mean K54 v4 AUC across 25 paths ≥ **0.55** under CPCV-honest training-overlap-weighted SE.
   - **(b) Lift over canonical K54 v1 baseline 0.5286:** ≥ **+0.04** with paired-t p < 0.01 + Wilcoxon p < 0.05 + bootstrap p_one < 0.05 + null-perm p < 0.05 + PBO < 0.40 + DSR-p < 0.05 under ONC effective_N = 11.
   - **(c) Cross-period robustness on TWO splits (both required):**
      - (c.i) Train 2022-2023 / test 2024-2026: lift sign preserved AND magnitude within ±50% of CPCV mean.
      - (c.ii) Train ≤ 2026-01-01 / test 2026-01-01+: lift sign preserved AND per-cohort sign positive on ≥3 of 4 effective groups.
   - **(d) Per-instrument-group floor:** K54 v4 AUC ≥ **0.50** on ALL 4 effective groups; NAS_US30 specialist beats global by ≥ +0.01 per-path on its cohort (component-ablation gate b).
   - **(e) Realized-R lift on J46-J49 holdout:** ≥ **+0.05R/trade** on top-K confidence band (sweep p ∈ {0.50, 0.55, 0.60, 0.65, 0.70, top-3%, top-5%, top-10%}) with stationary block bootstrap p < 0.01.
   - **(f) Feature stability:** ≥30 features in top-50 across ≥80% of CPCV paths (Jaccard overlap ≥ 0.6).
   - **(g) Calibration on 2026-04-29 → 2026-05-12 holdout:** Christoffersen interval-coverage test PASS at α=0.05 (per-decile coverage, NOT unconditional, per Agent A2 NA-7 recommendation).
   - **(h) Component ablation (NEW gate):** master-bundle add ≥ +0.02 per-path AUC AND T7-NAS-routing add ≥ +0.01 per-path AUC. Both bootstrap p_one < 0.10.

- **FALLBACK paths (if Hybrid 5 PRIMARY fails any gate):**
   - **FALLBACK 1: K54 v3 master alone** (drops T7 NAS routing). Same gates (a)-(g); skip (h.b). Verified by K1: lift +0.0484, t-p=0.008, PBO=0.20, DSR-p=0.0083 under N=11 ONC.
   - **FALLBACK 2: Hybrid 4** (K54 v3 master + Arch A on NAS routing). 4/5 PASS borderline per K1-FU3.
   - **FALLBACK 3 (if all above fail):** close Q1 with K54 v4 reframed as K55-shadow-only signal at top-3% per Agent A2 spec. KILLED memo + Q1.6 spec.

- **Holdout date range:** 2026-04-29 00:00 UTC → 2026-05-12 23:59 UTC (inherited from Q1.2/Q1.3/Q1.4 lock; opens ONCE at end-of-Q1).
- **Holdout LOCKED:** YES (inherited 2026-04-28 20:00 UTC; Q1.5 lock 2026-04-29 does not re-open).
- **Holdout opened:** NO (gate g moot — K54 v4 PRIMARY all 3 architectures FAILED 3/7 testable gates; FALLBACK 3 ships K55-shadow only)
- **Result:** FAIL
- **Result date:** 2026-04-29 (K54 v4 modeler dispatch verdict; gates a, c.i, e PASS / b, c.ii, d, f, h FAIL across all 3 architectures; gate g deferred-but-moot)
- **Why it passed/failed:** ALL 3 architectures (Hybrid 5 PRIMARY + K54 v3 master FALLBACK 1 + Hybrid 4 FALLBACK 2) FAILED 4 of 7 testable gates. **Phase 2-A cohort backfill INFEASIBLE** — Q1.5 spec called for n≥3,132 = 528 + 1,798 + ~806 (GBPJPY+US30 v2-feature backfill) but FN broker doesn't carry pre-2024 OHLCV for GBPJPY or US30 (per `audit/data_backfill_2022_2023.md` §1; hard data limit). K1-FU3's projected DSR-p=0.0061 was an assumption ("lift held constant 528→3,132"), not data-grounded. Modeler proceeded at empirical n=528 + 1,798 v1-schema cross-period composite. Per-architecture: Hybrid 5 AUC 0.5906, lift +0.0617, paired-t p=0.021 (≥0.01 fails strict gate b); within-2024-2026 lift -0.019 (1/4 groups+, fails c.ii); GBPJPY 0.462<0.50 + per-path NAS specialist negative (fails d); Jaccard 0.165 (fails f); component-ablation master-add +0.016<+0.020 + T7-routing -0.005 (fails h). **Strongest finding: top-3% realized-R lift +0.822R (Hybrid 5, n=16, p=0.000)** — REPLICATES Agent A2's K54 v3 finding. **Verdict per FALLBACK 3: CLOSE Q1 + ship K54 v4 reframed as K55-shadow-only signal at top-3%** per Agent A2 spec. Q1.6 re-spec deferred until pre-2024 GBPJPY+US30 OHLCV obtained from alternative broker.
- **Audit trail link:** `research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md` (Phase 2 verdict); `research/ml_program/models/k54_v4/` (K54 v4 modeler outputs); `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_research.md` (architecture re-search — projection over-optimistic); `research/ml_program/phase_2/k1_followup/k1_fu2_baseline_mismatch_sweep.md` (baseline-mismatch correction); `research/ml_program/forensics/2026-04-29/agent_a2_k55_shadow_spec.md` (top-3% K55-shadow ship spec — applies); memory `project_k54_v4_modeler_FAIL_q1_close_FALLBACK_3_2026-04-29`.

**K54 v4 Hybrid 5 architecture (locked spec):**
1. **Global model on non-NAS_US30 rows:** K54 v3 master bundle (Architecture A per-fold top-100 screening + Lopez-de-Prado meta-labeling secondary classifier + Kyle-Obizhaeva W-unit pooled training balanced form + adaptive conformal calibration + TreeSHAP-stability pruning).
2. **NAS_US30 specialist routing:** T7-style per-cohort LightGBM trained NAS+US30-only on identical 15-path-equivalent K=6/N=4 folds. Activated when `symbol ∈ {NAS100, US30_cash}`.
3. **Cohort:** n ≥ 3,132 (Phase 2-A expanded). Composition: Q1.3 cohort 528 + existing v1-schema 2022-2023 backfill 1,798 + new v2-feature backfill on GBPJPY + US30 ~806.
4. **Feature catalog:** 1,219 base + K-7 Osler stop-cluster (FX-only) + K-8 power-law OB-age + K-9 regime × round × side + K-10 above-up below-down. K-1' tick-count-time bars optional (per K1-FU3 not required for primary architecture).
5. **DROP from scope:** K-4 Stoikov micro-price (KILLED 2026-04-29; substrate gap), Kyle-Obizhaeva W-unit RAW form (KILLED; balanced form used), Lopez-de-Prado meta-label head as required component (kept as ablation candidate per gate h.a).

**Methodology (paired-fixed-HP CPCV per K1 + K1-FU3 protocols):**
1. CPCV K=6, N=4 (T_paths = 25), 7-day purge / 1-day embargo.
2. Paired-fixed-HP discipline (per memory `feedback_paired_fixed_hp_discipline`).
3. CPCV-honest training-overlap-weighted SE (Group A M7).
4. ONC effective_N = 11 (REQUIRED, NOT optional, per Agent B + K1-FU3).
5. DSR + CSCV PBO (n_combinations ≥ 14) + B=1000 null + null-perm.
6. Per-path mean AUC as primary aggregator (NOT pooled per-row, per K1-FU1 lesson).
7. Apples-to-apples paired comparison vs canonical K54 v1 baseline 0.5286.
8. Per-component baseline-mismatch corrected (per K1-FU2 sweep).

**Differences from Q1.4:**
1. **Architecture changed** — Q1.4 was K54 v3 master + meta-label + W-unit + NAS specialist. Q1.5 is **Hybrid 5** (K54 v3 master on non-NAS routes + T7-style NAS specialist on NAS routes; explicit routing layer instead of single-model specialist).
2. **Cohort changed** — Q1.4 was n≈2,326 (528 + 1,798 v1-schema). Q1.5 is **n≥3,132** (added GBPJPY+US30 v2-feature backfill ~806).
3. **CPCV changed** — Q1.4 was K=6/N=2 (T=15 paths). Q1.5 is **K=6/N=4 (T=25 paths)**, single-config-line change unblocks DSR-p<0.01.
4. **DSR anchor changed** — Q1.4 used N=200 conservative anchor. Q1.5 uses **ONC empirical effective_N=11** (per Agent B + K1-FU3).
5. **Aggregator locked** — per-path mean AUC primary (NOT pooled per-row, per K1-FU1 lesson).
6. **Baseline anchor changed** — Q1.4 used K54 v1 0.5286 vs MODELER-modified v1 0.5133. Q1.5 explicitly uses **canonical v1 0.5286 only**; per K1-FU2 baseline-mismatch sweep.
7. **Component-ablation gate (h) ADDED** — master bundle ≥+0.02 + T7-NAS-routing ≥+0.01.
8. **Realized-R gate (e) updated** — top-K confidence sweep instead of binary p>0.5 (per Agent A2 NA-7 + K1-FU1 per-path aggregator lessons).
9. **Holdout calibration (g)** — per-decile coverage instead of unconditional (per Agent A2 NA-7).
10. **3 fallback paths** explicitly defined (vs Q1.4's no-fallback structure).

**Validation discipline (must satisfy ALL):**
1. Pre-registration in this file BEFORE data work (this entry).
2. Phase 2-A cohort backfill complete BEFORE training begins.
3. Paired-fixed-HP CPCV K=6/N=4 (T=25 paths) + 7-day purge / 1-day embargo.
4. CPCV-honest training-overlap-weighted SE; per-path mean as primary aggregator.
5. DSR + ONC effective_N=11 + CSCV PBO computed on every primary lift claim.
6. B=1000 null shuffles + null-perm.
7. Cross-period replication on TWO splits per gate (c).
8. Per-instrument-group floor per gate (d).
9. Stationary block bootstrap (Politis-Romano) per gate (e).
10. Calibration via Christoffersen interval-coverage test (per-decile) per gate (g).
11. Component-ablation gate (h) for both Hybrid 5 component contributions.
12. Independent adversarial validator (post-modeler-return audit agent).

---

*End of registry. Append new hypotheses below this line for future phases.*
