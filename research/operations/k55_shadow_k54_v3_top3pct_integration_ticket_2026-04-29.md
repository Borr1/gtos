# K55-Shadow K54 v3 Top-3% Integration Ticket

**Filed:** 2026-04-29 (Phase 2 dispatch sequence — CEO-approved as decision #3)
**Source:** `research/ml_program/forensics/2026-04-29/agent_a2_k55_shadow_spec.md` (Agent A2 deployment spec) + `agent_a2_pre_registered_hypothesis_draft.md` (Q1.5 hypothesis)
**Status:** AWAITING MAIN-THREAD INTEGRATION (after Phase 2 forensic K1-FU3 architecture verdict + apples-to-apples confirmation)
**CEO approval:** 2026-04-29 (Phase 2 dispatch sequence sync)
**Owner:** Main-thread engineer

## TL;DR

Deploy K54 v3 as a **shadow signal** (read-only, no production decision impact) at top-3% confidence threshold using the K54 v3 model from `research/ml_program/models/k54_v3/`. **EXCLUDE US30_CASH** (per-symbol AUC 0.439, top-5% mean R -1.0). Post-pred isotonic regression + Gaussian jitter recalibration is required (Platt clusters break threshold gating; Agent A2 verified).

## ⚠️ Phase 2 update — TARGET MODEL UPGRADE PENDING

**Per K1-FU3 (2026-04-29):** the K54 v4 modeler dispatch is APPROVED. Winning architecture = **Hybrid 5** (K54 v3 master + T7-style NAS specialist) at n=3,132 + T=25 + N=11 ONC → DSR-p=0.0061 SURVIVES. **Once K54 v4 dispatch returns (~6-8 hr), THIS TICKET'S TARGET MODEL UPGRADES to K54 v4 Hybrid 5** (or K54 v3 master FALLBACK 1). Top-3% deployment frame transfers cleanly.

## ⚠️ Per NA-11 — concentration filter caveat

**K54 v3 top-3% trades are 16/16 sourced from mechanical-OB cohort (P(Mech_OB | top-3%) = 1.000).** K54 v3 top-3% deployment is functionally a **concentration filter** on the mechanical OB alpha, NOT an independent K55-shadow signal. The +0.550R top-3% lift IS real (Agent A2 verified) — it represents K54 v3 identifying which mechanical OB setups are best. But for portfolio aggregation purposes, K54 v3 top-3% is a refinement of the mechanical OB cross-period alpha, not a 5th independent dimension. Verify K55-shadow deploy adds value beyond pure mechanical OB cohort routing during 30d shadow window.

## Why this is the right ship target

- **K54 v3 lift +0.0484 SURVIVES apples-to-apples** under K1 verification (paired t p=0.0082, 12/15 paths positive).
- **Top-3% (n=16) under isotonic+jitter delivers realized-R lift +0.550R/trade**, bootstrap 95% CI [+0.703, +1.100], CPCV-honest p=0.011 (Agent A2 verified).
- DSR-p still FAILS at every defensible eff_N — but Agent B's two-tier K55-shadow gate (`DSR-p<0.10 OR CPCV-honest p<0.10`) PASSES via CPCV-honest p=0.011.
- This is a research-grade shadow deploy, NOT a production-grade live A/B. Promotion gate is 30-day shadow data + DSR-p<0.05.

## Shadow deployment spec (locked)

### Activation rule
- Top-3% confidence on rolling 7-day window of K54 v3 isotonic+jitter ranked predictions.
- p ≥ 0.55 floor (defensive).

### Excluded instruments
- **US30_CASH** — per-symbol AUC 0.439, top-5% mean R -1.0. Confirmed harmful at this cohort.
- Possibly XAGUSD/GBPJPY (top-5% lift +0.25, borderline; sample too small). Defer decision per per-symbol shadow data.

### Included instruments (per top-5% per-symbol lift)
| Instrument | Top-5% mean R | Status |
|---|---:|---|
| XAUUSD | +0.918 | INCLUDE |
| GBPUSD | +1.5 | INCLUDE |
| NAS100 | +1.5 | INCLUDE |
| USDJPY | +1.0 | INCLUDE |
| GBPJPY | +0.25 | DEFER (borderline; let shadow accumulate first) |
| XAGUSD | +0.25 | DEFER (borderline) |
| US30_CASH | -1.0 | **EXCLUDE** |

### Inference cadence
- Per-M15-candle on all CANDIDATE decisions for included symbols.
- Daily trade-frequency projection: ~0.04 trades/day at top-3%.

### Override conditions
- DD ≥ 8% (existing H29) — disables shadow (no signal write to log).
- News filter active — disables shadow.
- Heartbeat-flatten active — disables shadow.

## Implementation requirements (main-thread engineering)

### 1. K55-shadow scaffold module
- New: `src/components/k55_shadow.py` — wraps K54 v3 model + isotonic+jitter recalibrator + top-K confidence gate.
- API: `predict_top_k(mso: dict, symbol: str, k_pct: float = 0.03) -> Optional[K55ShadowSignal]`
- Returns `K55ShadowSignal { confidence_pct: float, decision: 'TRADE' | 'NO', features: dict }` or `None` if symbol excluded.
- Reads K54 v3 artifacts from `research/ml_program/models/k55_shadow/k54_v3_global.lgb` (copied from `models/k54_v3/`).
- Reads recalibrator from `research/ml_program/models/k55_shadow/isotonic_jitter_calibrator.pkl` (built from Agent A2 spec).

### 2. Shadow logger
- New: `src/components/k55_shadow_logger.py` — JSONL writes per inference (regardless of decision).
- Schema: `{timestamp, symbol, candle_time, raw_p, recalibrated_p, top_k_pct_value, decision, features_hash, ai_decision, k55_decision_agreement}`
- File: `shadow_logs/k55_shadow_decisions.jsonl`

### 3. Orchestrator hook
- Modify `src/components/orchestrator.py` to invoke `k55_shadow.predict_top_k()` parallel to AI primary (no impact on AI decision flow).
- ~10 LOC additive.
- Feature flag: `config.k55_shadow.enabled: false` (default OFF — flip to true after smoke test).

### 4. Config additions
```yaml
k55_shadow:
  enabled: false
  k_pct: 0.03
  min_confidence: 0.55
  excluded_symbols: [US30_cash]
  deferred_symbols: [GBPJPY, XAGUSD]
  rolling_window_days: 7
  promotion_gate:
    min_n_events: 50
    min_realized_r_lift: 0.10
    max_dsr_p: 0.05
    min_shadow_days: 30
```

### 5. Daily monitor script
- New: `scripts/k55_shadow_monitor.py` — daily evaluation of shadow data.
- Outputs: `shadow_logs/k55_shadow_daily_summary.csv`.
- Watchdog hook: alert if rolling-30d realized-R lift < +0.05R (degradation signal).

## Promotion gate to live A/B

- **n ≥ 50 K55-shadow trade events** (at ~0.04/day = ~5 weeks).
- **Realized-R lift ≥ +0.10R/trade** vs no-K55 baseline (uniform AI decisions on same period).
- **DSR-corrected p < 0.05** at observed N + observed eff_N.
- **CI excludes zero** (stationary block bootstrap, B=1000).
- **Per-symbol verification:** ≥3 of 4 included symbols (XAUUSD/GBPUSD/NAS100/USDJPY) show positive lift.
- **No degradation signal** (rolling-30d not below baseline).

## Pre-registration (Q1.5 hypothesis)

Per Agent A2's draft at `research/ml_program/forensics/2026-04-29/agent_a2_pre_registered_hypothesis_draft.md`:

> **Q1.5 hypothesis (pre-registered).** K54 v3 deployed at top-3% confidence (per recalibrated isotonic+jitter predictions, excluding US30_CASH) achieves realized-R lift ≥ +0.10R/trade on 30-day shadow data with DSR-p<0.05.

To be appended to `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` post-K1-FU3 architecture verdict (in case the spec changes per K54 v4 selection).

## CEO-approval status
- 2026-04-29: CEO approved K55-shadow deploy as part of Phase 2 dispatch sequence (decision #3).
- Per WF-1 discipline: production code modification requires CEO approval; this ticket IS that approval recorded.

## Recommended order of operations
1. **PRE-REQUISITE: Wait for K1-FU3 architecture verdict** (~3-4 hr) to confirm K54 v3 master bundle is the architecture (vs Arch A pure or T7 per-cohort). If K1-FU3 says T7 is the winner, this ticket re-spec'd to T7 model.
2. **PRE-REQUISITE: K1-FU2 baseline-mismatch sweep** (~1-2 hr) to confirm K54 v3 lift survives canonical baseline at the component level.
3. **L-6 + L-7-extension integration** (existing ticket; ~2-3 days) — observability infrastructure prerequisite for K55-shadow analytics.
4. **Implementation:** K55-shadow scaffold + logger + orchestrator hook + config (~3-5 days engineering).
5. **Smoke test:** trigger one K55-shadow inference in DRY-RUN mode; verify shadow log row appears with correct schema.
6. **Activation:** flip `config.k55_shadow.enabled: true`. Begin 30-day shadow data accumulation.
7. **Promotion evaluation:** at day-30 + n≥50, run promotion gate evaluation. Live A/B GO/NO-GO.

## Reproducibility

K54 v3 artifacts (read-only):
- `research/ml_program/models/k54_v3/k54_v3_global.lgb` (LightGBM global model)
- `research/ml_program/models/k54_v3/k54_v3_meta_label.lgb` (meta-label classifier)

Recalibrator construction (per Agent A2 spec):
- Input: K54 v3 raw OOS predictions on 528-row Q1.3 cohort.
- Step 1: IsotonicRegression fit (sklearn).
- Step 2: Add Gaussian jitter sd=0.001 on output.
- Persist to `research/ml_program/models/k55_shadow/isotonic_jitter_calibrator.pkl`.
- Verify: `len(set(round(predictions, 4))) >= 200` (228 unique values per Agent A2).

---

*Ticket end. Main thread: claim when K1-FU3 + K1-FU2 verdicts return; close by linking the integration commit + smoke-test verification + day-30 promotion evaluation.*
