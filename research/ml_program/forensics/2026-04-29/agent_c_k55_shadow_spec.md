# K55-Shadow Operational Specification — NAS_US30 Specialist (proposed)

**Date:** 2026-04-29
**Status:** PROPOSAL ONLY — depends on CEO decision per `agent_c_nas_us30_specialist_forensic.md` §8
**Forensic context:** the production case for this deploy (specialist +0.103 delta) is invalid (see forensic §5; apples-apples paired delta = -0.007, t-p 0.93). This spec is the operational form of the deploy IF the CEO decides to ship as cheap insurance / shadow telemetry.

---

## 1. Decision summary

**Forensic recommendation: DO NOT SHIP K55-shadow on the strength of the production +0.103 evidence.** The production case is built on a pool-aggregation artifact. If shipped anyway, the spec below makes the deploy methodologically defensible (pre-registered, fixed-window, auto-expiring) at zero API cost.

Two CEO paths:

**Path A — defer K55-shadow:** drop the specialist from program scope; reallocate to 2022-2023 v2-feature backfill (4-6 weeks data engineering) + K54 v4 dispatch. This is the methodologically sound default per `Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` §6.2.

**Path B — ship K55-shadow as cheap insurance:** with the spec below + pre-registered promotion gate. Cost: ~zero (log-only). Value: operational telemetry that may catch a real signal the apples-apples test was underpowered to detect.

If CEO chooses Path B, what follows is the operational spec.

---

## 2. Operational scope

| Parameter | Value |
|---|---|
| Instruments | NAS100 + US30_CASH only (other 5 instruments: K55-shadow not active) |
| Score threshold | p_specialist ≥ 0.55 (floor; per Q1.4 postmortem §4.1) |
| Mode | Read-only shadow log; NO trading-decision impact |
| Output | `shadow_logs/k55_specialist_decisions.jsonl` |
| Promotion gate | pre-registered (see §6) |
| Window | 90 days (30 days too low-power per forensic §9) |
| Auto-expire | After 90 days OR n ≥ 50 events, whichever first |
| Re-evaluation | Hard stop at expiry; no rolling window without explicit CEO go-ahead |

---

## 3. Inference pipeline

Per CANDIDATE evaluation on NAS100 or US30_CASH:

1. **Already done by orchestrator:** Component 2 emits MSO; Component 3A (Sonnet 4.6 effort=max) emits CANDIDATE/REJECT.
2. **K55-shadow hook (NEW):** if symbol ∈ {NAS100, US30_CASH} AND Component 3A emitted CANDIDATE:
   - Compute v3 feature row using the same feature-extraction code as K54 v3 modeler (deterministic).
   - Predict via `k54_v3_nas_us30_specialist.lgb` (saved booster).
   - Predict via `k54_v3_global.lgb` (saved booster).
   - Calibrate both via the K54 v3 logistic calibrator artifacts (NOT YET SAVED — see §7 deficiency).
   - Compute `p_specialist`, `p_global`.
3. **Log-only emit** (no decision impact):
   - One row per CANDIDATE to `shadow_logs/k55_specialist_decisions.jsonl`.
   - Schema:
     ```json
     {
       "ts_close": "2026-05-15T13:30:00Z",
       "symbol": "NAS100",
       "framework": "ob_retest",
       "ai_decision": "CANDIDATE",
       "ai_confidence": 80,
       "p_global_v3": 0.612,
       "p_specialist_nas_us30": 0.671,
       "p_combined_avg": 0.6415,
       "specialist_above_threshold": true,
       "global_above_threshold": true,
       "trade_id_if_executed": "NAS100|2026-05-15T133000Z",
       "ai_executed": true,
       "realized_r_at_close": null,
       "realized_r_attached_at": null
     }
     ```
4. **Trade close hook:** when the orchestrator records realized R for any trade with a corresponding K55-shadow log row, append `realized_r_at_close` and `realized_r_attached_at` to that row (in-place via line-replace; not append).

---

## 4. Feature engineering note (PRECONDITION for production deploy)

The K54 v3 features include 6 closed-form additions (`kw__k7..k10`). These are computed in `add_k54_v3_features()` in `train_k54_v3.py`. Production deploy requires:

- Move `add_k54_v3_features()` into a stable production module (`src/components/k54_features.py` or equivalent).
- Verify the feature list is identical on (a) the offline scout matrix, (b) the live MSO input. The scout matrix was built via `build_scout_matrix.py`; production has no equivalent feature-extraction pipeline.
- This is a non-trivial engineering task (~3-5 days) and is the **largest operational hidden cost** in the K55-shadow deploy.

**Risk:** if any feature in the K54 v3 catalog cannot be replicated live (e.g., a feature requires offline OHLCV history not in the live MT5 stream), the specialist's predictions will be silently distorted. Pre-deploy validation: shadow-replay the last 30 days of CANDIDATEs through both offline and live feature extractors and verify per-feature-row equality.

---

## 5. Existing infra integration points

- Hook into `src/components/orchestrator.py` post-Component-3A, pre-execution (additive, log-only).
- New file: `src/components/k55_specialist_shadow.py` — handles inference + log emit.
- New config flag: `k55_shadow.enabled: false` (default) → flip to `true` when ship-approved.
- Watchdog: extend `scripts/watchdog.ps1` to monitor `shadow_logs/k55_specialist_decisions.jsonl` for n ≥ 50 milestone OR 90-day expiry.

---

## 6. Pre-registered promotion gate

**Promotion criteria (locked BEFORE shadow window opens):**

The K55-shadow specialist promotes from shadow → live A/B if and only if:

1. **n ≥ 50 NAS100+US30_cash CANDIDATE events** (with ai_executed=true and realized_r_at_close populated).
2. **Per-row paired analysis:** for each event, compute `realized_r_under_specialist_gate(0.55) - realized_r_under_global_gate(0.55)`.
3. **Bootstrap CI:** Politis-Romano stationary block bootstrap, 5,000 resamples, on the per-event paired delta.
4. **Bootstrap p < 0.05** for H1: `mean_paired_delta > 0`.
5. **Bootstrap 95% CI lower bound > 0**.
6. **Mechanism check:** the specialist's emit decisions on the 50 events must show non-degenerate variance (`std(p_specialist) > 0.05` on those 50 events; not all clustered near 0.55 boundary).

**De-promotion criteria (hard fail; auto-disable):**

The K55-shadow auto-disables (config flag flipped back to `false`) if:

1. **n ≥ 20 events with mean realized R < 0** (early hard-stop).
2. **Specialist's p_specialist distribution is degenerate** (`std(p_specialist) < 0.02` over 20+ events) — indicates feature-extraction or calibration failure.
3. **30-day OOS performance < random** (AUC < 0.50 with n ≥ 30 events).

The auto-disable path is operationally important because a feature-extraction silent bug (per §4) would manifest as a degenerate distribution.

---

## 7. Known deficiencies vs current artifact set

**The following must be addressed BEFORE shadow window opens; otherwise spec is incomplete:**

1. **No saved calibrator.** `k54_v3_nas_us30_specialist.lgb` was trained but the per-path logistic calibrator was applied at evaluation, not saved as a permanent artifact. Production specialist predictions need an independent calibration pass on a held-out NAS+US30 subset (e.g., final 20% of cohort by date) saved as a sklearn pickle.
2. **No per-row specialist prediction artifact.** The CPCV-pooled-pred file (`p_v3_te` per path) does not include specialist-only preds. To compute per-row specialist scores ex post for the n=113 cohort (sanity-check input pipeline) requires re-running the agent-c forensic.
3. **Feature replication on live MSO.** The K54 v3 modeler used `feature_matrix.parquet` as input, NOT the live MSO. The 1,247-feature scout matrix was built offline by `build_scout_matrix.py`. Production deploy requires building the same feature row from the live MSO at CANDIDATE time. This is non-trivial; see §4.
4. **No regime-conditioning despite Group C literature recommending it.** The NAS_US30 specialist has no `dealer_gamma_sign` / `vix1d_minus_vix9d` / `mag7_concentration_percentile` / `is_opex_week` feature. The literature-cited mechanisms are explicitly NOT instrumented. If the specialist were shipped and worked, it would not be the literature-claimed mechanism doing the work.
5. **Trade-frequency projection (forensic §9):** ~17 NAS+US30 trades/month at p ≥ 0.55. The pre-registered n ≥ 50 gate would require ~3 months of shadow data. The proposed 90-day window is at the lower bound of feasibility; if frequency comes in lower, the gate cannot trigger before auto-expire.

---

## 8. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Specialist signals are noise (no real lift) | HIGH | LOW (shadow-only) | Pre-registered promotion gate prevents premature promotion |
| Feature-extraction divergence offline-vs-live | MEDIUM | MEDIUM | §4 pre-deploy validation; auto-disable on degenerate distribution |
| Calibrator drift (saved on Q1 cohort, applied to Q3 live) | MEDIUM | LOW | 90-day window auto-expires before drift compounds |
| Operator ignores auto-disable signal | LOW | LOW | Watchdog alerts to Telegram on auto-disable; CEO 24h ack required |
| K55-shadow code path has bug (logs wrong scores) | MEDIUM | LOW | Read-only shadow; verify on 30-day backtest before flipping flag |
| Gate (g) holdout 2026-04-29 → 2026-05-12 contaminated | LOW | LOW | K55-shadow's NAS+US30 events during holdout window are EXCLUDED from any K54 v3 global-model gate (g) test (which is already deferred per §6.2 of postmortem). |

---

## 9. CEO decision request

1. **Path A (defer K55-shadow + Phase 2 cohort expansion priority)** — recommended per forensic §8.
2. **Path B (ship K55-shadow with this spec)** — acceptable; mostly cheap (~5 days engineering); promotion gate is honest; auto-expire prevents drift.
3. **Path C (ship K55-shadow with broader scope)** — NOT recommended. Adding cohorts beyond NAS+US30 would dilute already-marginal evidence.

If Path B chosen, additional pre-deploy work:
- Resolve §7 deficiencies (~1 week)
- Pre-register promotion gate criteria (this document, signed by CEO)
- Update CLAUDE.md "What is unresolved" list with K55-shadow active → expiry milestone (90d or n=50)

If Path A chosen:
- This spec archives; `k54_v3_nas_us30_specialist.lgb` artifact retained for audit-trail
- Phase 2 begins with 2022-2023 v2-feature backfill data engineering

---

*End of K55-shadow spec. Operational decision pending CEO; forensic does not by itself reject the shadow deploy, but does reject the production +0.103 case as invalid evidence.*
