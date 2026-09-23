# Q1.5 Pre-Registered Hypothesis Draft — K54 v3 Top-K Recalibrated Shadow

**Status:** DRAFT — not yet appended to `research/ml_program/PRE_REGISTERED_HYPOTHESES.md`. Pending CEO approval + holdout-discipline verification.

**Author:** Forensic Agent A2, 2026-04-29
**Companion docs:** `agent_a2_recalibrated_ablation.md` (forensic), `agent_a2_k55_shadow_spec.md` (deployment).

---

## Q1.5 — K54 v3 Top-K Recalibrated Shadow Deployment (PRIMARY, contingent on K55-shadow ship)

- **Date pre-registered:** TBD — AT MOMENT OF SPEC LOCK (must be appended to `PRE_REGISTERED_HYPOTHESES.md` BEFORE production code touches the K54 v3 predictor).
- **Pre-registered by:** ML Program Orchestrator (post-Agent-A2 forensic; CEO-approved for K55-shadow ship).
- **Phase:** Q1 close → Q1.5 — K55-shadow operationalization.

---

### Hypothesis text (LOCKED)

> *"K54 v3 deployed in K55-shadow mode at top-3% confidence (per recalibrated isotonic-mapped + Gaussian-jittered predictions, where the isotonic regressor is fit ONCE on the pooled-CPCV-test (p, y) sample from the n=528 Q1.3 cohort using LOOP-honest aggregation, and the jitter is N(0, 0.001) seeded by the M15 candle UTC timestamp), excluding the US30_CASH symbol from activation, achieves realized-R lift ≥ +0.10R/trade with bootstrap 95% CI excluding zero AND CPCV-honest single-test p < 0.05 across the union of:
>
> (a) the 14-day prospective holdout 2026-04-29 → 2026-05-12 (locked at Q1.2 holdout-lock 2026-04-28 20:00 UTC, never opened, never peeked), and
>
> (b) a 30-day forward shadow window 2026-05-13 → 2026-06-11 collected via the K55-shadow logger.
>
> Top-5% deployment is logged in parallel as a secondary observation. The 7-day rolling-window top-K activation rule (rank ≥ 0.97 of last 7 days of CANDIDATE predictions) is the activation primitive; absolute prediction thresholds (e.g., p≥0.6126) are NOT used."*

---

### Thresholds (ALL required for PASS)

#### (a) Realized-R lift on take-trades

**Threshold:** mean realized R on K55-shadow TAKE trades ≥ +0.10R/trade.

**Reference baseline:** uniform mean R across all CANDIDATEs in the same window (≈+0.355R per Q1.3 cohort baseline; will be re-measured during the test window for direction-discipline check).

**Statistical test:** stationary block bootstrap (Politis-Romano, n_boot=2000, block_size=20) on the realized-R series. Bootstrap 95% CI lower bound > 0.

**Single-test p:** CPCV-honest paired t-test (per `statistical_reevaluation.md` methodology) of realized R vs uniform — single-sided p < 0.05.

#### (b) Sample-size floor

**Threshold:** ≥ 5 realized samples in the union of (a) holdout + (b) shadow window. (At top-3% activation rate ~0.04/day × 44 days = ~1.7 samples expected; we require ≥5 to compute meaningful CI. If <5, hypothesis is INVALIDATED_PRE_TEST and re-spec'd to top-5%.)

#### (c) Per-symbol cross-replication

**Threshold:** at least 4 of the 6 deployable symbols (XAUUSD, XAGUSD, NAS100, USDJPY, GBPJPY, GBPUSD) have positive realized R on their K55-shadow TAKE trades. (US30_CASH is excluded from activation, so excluded from this count.)

#### (d) DSR-corrected p (research-grade)

**Threshold:** DSR-p < 0.05 at effective N = 200 + (number of distinct deployment variants tested in this Q1.5 spec) ≈ 202.

**Note:** N=200 is the CEO-conservative anchor (Agent B §1.3). Under the empirically-defensible eff_N=11 (ONC), the threshold becomes more permissive but the DSR-p requirement still applies.

#### (e) No per-symbol regression (live-deploy gate only)

**Threshold (LIVE-DEPLOY GATE only — NOT for K55-shadow PASS):** no symbol's K55-shadow TAKE trades have realized mean R < -0.5 (strictly worse than holding cash with friction).

This gate fires only at the LIVE A/B promotion step, not at K55-shadow PASS. K55-shadow PASS allows for some per-symbol weakness if cohort lift clears.

---

### Holdout discipline

**Holdout date range:** 2026-04-29 00:00 UTC → 2026-05-12 23:59 UTC (14 calendar days). [INHERITED from Q1.2 lock.]

**Holdout LOCKED:** YES — locked 2026-04-28 20:00 UTC at Q1.2 lock.

**Holdout opened:** NO — must remain NO until end of Q1.5 evaluation window.

**Single-pass evaluation rule:**

1. Holdout (a) data is captured via K55-shadow logger over 2026-04-29 → 2026-05-12.
2. NO HUMAN reads `shadow_logs/k54_v3_predictions.jsonl` between 2026-04-29 and 2026-05-12.
3. Shadow window (b) accumulates 2026-05-13 → 2026-06-11.
4. At 2026-06-12, ONE-PASS evaluation:
   - Compute realized-R lift on union (a) + (b).
   - Compute bootstrap 95% CI.
   - Compute CPCV-honest paired-t p.
   - Compute DSR-corrected p.
   - Compute per-symbol cross-replication (≥4 of 6 positive).
5. Record PASS / FAIL / INVALIDATED_PRE_TEST with full why-passed-or-failed memo.

**No interim peeks. No partial evaluations. No re-specs based on observed data.**

---

### Validation discipline (every primary hypothesis must satisfy ALL)

Per `PRE_REGISTERED_HYPOTHESES.md` validation discipline checklist:

1. **Pre-registration BEFORE data work:** This entry. (Q1.5 deploy MUST follow this entry.)
2. **CPCV with explicit purge gaps:** Yes — Q1.3 cohort (n=528) used K=6, N=2, purge_days=7, embargo_days=1. Isotonic refit uses pooled CPCV-test labels (LOOP-honest).
3. **30% OOS holdout opened ONCE:** Yes — 14-day prospective window 2026-04-29 → 2026-05-12.
4. **White-noise null test:** SHADOW-DEFERRED — applies at K54 v3 cohort training (Q1.4); for K55-shadow, the per-trade signal is the test of interest, not a null shuffle.
5. **Multiple-comparison correction:** Bonferroni — single-test p < 0.05; DSR at eff_N ≥ 200 captures program-level multiple comparison.
6. **Cross-instrument replication:** ≥4 of 6 deployable symbols positive (gate (c)).
7. **Cross-period replication:** ASSUMED via CPCV (Q1.4 cross-period gates c.i / c.ii FAILED but Q1.4 cohort training data covers 2024-02 → 2026-04).
8. **Independent adversarial validator:** Agent A2's forensic + Agent B's DSR rigor + Agent C's NAS-specialist analogue serve as the adversarial validators; all three are READ-ONLY external auditors of the same K54 v3 architecture.
9. **Decay velocity benchmark:** Re-measure top-3% lift at 7d, 14d, 30d shadow milestones; compute decay slope. Flag for re-evaluation if decay velocity exceeds -0.05R/trade per 7d.
10. **Replication on a different model class:** SHADOW-DEFERRED — not blocking for K55-shadow ship; Q1.5+ work item.

---

### Result fields (editable post-registration ONLY for these)

- **Holdout LOCKED:** YES → (no change post-registration)
- **Holdout opened:** NO → YES on 2026-06-12 (single flip)
- **Result:** PENDING → PASS | FAIL | INVALIDATED_PRE_TEST
- **Result date:** TBD
- **Why it passed/failed:** TBD
- **Audit trail link:** `research/ml_program/forensics/2026-04-29/agent_a2_recalibrated_ablation.md`

---

### Differences from prior Q1.x hypotheses

| Field | Q1.3 / Q1.4 (master bundle) | Q1.5 (this draft) |
|---|---|---|
| Architecture | K54 v3 master bundle (5-gate) | Top-3% slice of K54 v3 only |
| Activation | Threshold p ≥ 0.50 (binary) | 7-day rolling top-3% (rank-based) |
| Calibration | LightGBM Platt sigmoid | Isotonic on pooled CPCV-test |
| Symbol scope | All 7 | Excludes US30_CASH (n=6) |
| Test cohort | Cross-period CPCV (n=528) | 14d holdout + 30d shadow forward (n≥5) |
| Failure mode | -0.108R / DSR-p 0.32 | Recalibration + per-symbol exclusion + top-K |

---

### Risks / known limitations

1. **Top-3% activation rate may be too sparse** — at n≥5 floor, may take >30 days to accumulate signal. Top-5% parallel logging mitigates.

2. **n=16 underlying signal could be sample-dependent** — the +0.55R top-3% lift in Q1.3 cohort relies on n=16. Cross-period generalization to 14d holdout + 30d shadow is the test.

3. **K54 v3 features may not be available at runtime in production** — feature engineering work is the engineering prerequisite. Spec-locked but engineering-pending.

4. **Isotonic regressor may not generalize** — fit on Q1.3 cohort (2024-02 → 2026-04); production data 2026-04-29+ may have different prediction distributions. 7-day rolling-window mitigates but doesn't eliminate distribution-drift risk.

5. **DSR-p at N=200 anchor is conservative** — may yield FAIL even with strong realized-R signal. Two-tier gate (Agent B §7.2) provides relaxation for K55-shadow research-grade.

---

### Pre-registration commit checklist (when ready to deploy)

- [ ] Append this entry to `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` (between Q1.4 and any new entry).
- [ ] Commit with message: `pre-register Q1.5 — K54 v3 top-3% recalibrated K55-shadow (CEO-approved spec lock)`.
- [ ] Verify `Holdout LOCKED: YES` and `Holdout opened: NO` in the registered text.
- [ ] Tag commit `q1.5-pre-registered`.
- [ ] WAIT 24h.
- [ ] Then deploy K55-shadow code per `agent_a2_k55_shadow_spec.md`.

---

*End of Q1.5 pre-registration draft. To be appended to `PRE_REGISTERED_HYPOTHESES.md` post-CEO-approval and pre-deploy.*
