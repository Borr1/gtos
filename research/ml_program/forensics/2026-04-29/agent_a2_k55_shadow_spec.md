# Agent A2 — K54 v3 K55-Shadow Deployment Spec

**Date:** 2026-04-29
**Author:** Forensic Agent A2 (companion to `agent_a2_recalibrated_ablation.md`)
**Status:** RECOMMENDED — pending CEO approval; pre-registration discipline required prior to deploy.

---

## Spec at a glance

| Field | Value |
|---|---|
| **Component** | K54 v3 global + isotonic recalibration + Gaussian jitter |
| **Inference cadence** | Per M15-candle on every CANDIDATE that passes K54 v3 catalog feature engineering |
| **Activation rule** | Predicted prob (isotonic-mapped + jittered) ranks in **top 3-5%** of pending CANDIDATEs in 7-day rolling window |
| **Symbol exclusions** | US30_CASH only (per-symbol AUC 0.439, top-5% mean R -1.0) |
| **Override conditions** | Standard (drawdown, news, regime gate — see §5) |
| **Daily trade-frequency projection** | ~0.04 trades/day at top-3%; ~0.063 at top-5% |
| **Promotion gate (30d shadow)** | Realized-R lift ≥ +0.10R/trade, bootstrap 95% CI excludes zero, DSR-p < 0.05 |
| **Pre-registration** | REQUIRED before deploy — see §7 |

---

## 1. Architecture

### 1.1 Components

```
┌────────────────────────────────────┐
│ K54 v3 LightGBM model              │   (frozen artifact: k54_v3_global.lgb)
│ trained on n=528 cohort            │
│ 1240 features (Arch A + W-unit +   │
│ K-7..K-10 + meta-label head)       │
└─────────────┬──────────────────────┘
              │ raw_score → Platt sigmoid
              ▼
┌────────────────────────────────────┐
│ Isotonic regressor                 │   (frozen artifact: isotonic_global.pkl)
│ fit on pooled CPCV-test (p, y)     │   (n=2,640 across 15 paths)
│ sklearn IsotonicRegression         │
│ out_of_bounds="clip"               │
└─────────────┬──────────────────────┘
              │ p_iso ∈ [0, 1]
              ▼
┌────────────────────────────────────┐
│ Deterministic jitter               │
│ N(0, 0.001), seeded with M15       │
│ candle UTC timestamp               │
└─────────────┬──────────────────────┘
              │ p_jittered
              ▼
┌────────────────────────────────────┐
│ Top-K rolling-window ranker        │
│ buffer = last 7 days of preds      │
│ activation: rank ≤ K               │
│ where K = ceil(0.03 × buffer_size) │
└─────────────┬──────────────────────┘
              │
              ▼  signal: K54_v3_top_k_TAKE / SKIP
```

### 1.2 Persistence requirements

| Artifact | Path | Frozen? |
|---|---|---|
| LightGBM model | `models/k54_v3/k54_v3_global.lgb` | YES — already exists |
| Isotonic regressor | `models/k54_v3/isotonic_global.pkl` (NEW) | YES — fit during deploy prep |
| Feature catalog | `models/k54_v3/feature_list.txt` | YES — derived from `meta.json` |
| Rolling buffer | `pipeline_state/k54_v3_pred_buffer.json` (NEW) | NO — updated each candle |

The isotonic regressor must be fit ONCE on the 528-row CPCV-pooled (p, y) sample (LOOP-honest aggregation across 15 CPCV paths). Save with sklearn pickle or joblib. Inference cost: ~1ms per prediction.

---

## 2. Inference cadence

**When:** every M15 candle close, after Component 2 (market state analyzer) outputs candidate setups, BEFORE Component 4 (execution).

**Where in pipeline:** Component 3B (after Component 3A primary analyzer's CANDIDATE verdict). Currently Component 3B is the Bull/Bear debate (PAUSED). K55-shadow inserts here as a parallel observational signal.

**Inputs needed:** every CANDIDATE row's M15 + H1 + H4 features, computed via the K54 v3 feature catalog (1,240 features). The current production pipeline does NOT compute these features — **prerequisite work is the feature engineering layer to extract K54 v3 features at runtime**.

**Output:** `K54_v3_signal: {top_k_rank, p_jittered, p_iso, p_platt, take_top_3pct, take_top_5pct}`. Logged to `shadow_logs/k54_v3_predictions.jsonl` for promotion analysis.

**For K55-shadow phase:** K54 v3 is **observation-only** — it does NOT change trade decisions. Component 4 still uses the existing safety gates. The shadow log records whether K54 v3 WOULD have taken/skipped each CANDIDATE, and the realized R is captured later when the trade closes (or the candidate doesn't fire).

---

## 3. Activation rule (K55-shadow)

### 3.1 Rolling-window ranking

Maintain a 7-day ring buffer of `p_jittered` values from all prior CANDIDATEs (across all 7 production instruments). On each new CANDIDATE:

```python
buffer.append(p_jittered)
if len(buffer) > buffer_capacity:  # 7d × ~1.26 setups/day ~= 9
    buffer.pop_oldest()

# Compute current row's rank
rank = sum(1 for p in buffer if p < p_jittered_current) / len(buffer)
take_top_3pct = (rank >= 0.97)  # top 3%
take_top_5pct = (rank >= 0.95)  # top 5%
```

### 3.2 Why rolling-window vs absolute threshold

- **Absolute threshold** (e.g., `p_iso >= 0.6126`): the production-time prediction distribution may drift. Top-3% in the training cohort might be 6% in production if predictions skew higher; we want a CONSISTENT activation rate.
- **Rolling-window**: enforces top-3% activation regardless of the prediction's absolute scale. Robust to distribution drift.

The 7-day window is short enough to track regime changes but long enough to provide statistical power (~9 predictions in 7 days × 7 instruments).

### 3.3 Recommended K choice

**Default: top-3%.** Lift +0.55R, CI [+0.703, +1.100], strongest single point with reasonable n.

**Alternative: top-5%.** Lift +0.44R, CI [+0.644, +0.942], n is 1.6× higher (better statistical power for shadow analysis).

**Recommend running BOTH in parallel during shadow phase** — log `take_top_3pct` and `take_top_5pct` separately. At end of 30 days, determine which K-band has the strongest realized-R signal on shadow data. Likely top-5% will have more samples (~2 trades/month vs ~1.1 at top-3%).

---

## 4. Symbol exclusions

| Symbol | Decision | Rationale |
|---|---|---|
| US30_CASH | **EXCLUDE** | Per-symbol AUC 0.439 (model genuinely INVERTED); top-5% deployment yielded mean R -1.0 (n=2). Agent A confirmed via `_aux_calibration_disconnect.json` per-symbol AUC. |
| All other 6 instruments | INCLUDE | Per-symbol top-5% mean R: XAUUSD +0.918, GBPUSD +1.5, NAS100 +1.5, USDJPY +1.0, GBPJPY +0.25, XAGUSD +0.25. All positive. |

Implementation: in K55-shadow logger, set `take_top_*` to `False` if symbol == "US30_CASH".

---

## 5. Override conditions

K55-shadow signals are PURELY OBSERVATIONAL. Production safety gates (already wired) take precedence:

| Override | Existing gate | K55-shadow effect |
|---|---|---|
| Drawdown ≥ 8% | H29 (live, scales risk to 0.5%) | K55 still LOGS but trade size already reduced |
| Daily-loss stop | T2.8 dormant marker | K55 LOGS; dormant period blocks all trades anyway |
| News blackout | Standard ±15min around high-impact | K55 LOGS; trade blocked by news filter |
| Outside kill zone | Standard (per-instrument schedule) | K55 LOGS; trade blocked anyway |
| Regime gate (NEW for shadow) | Per F2 finding: trending_bull XAUUSD London = 0% WR | RECOMMEND: K55 SKIPS (don't log positive) when symbol=XAUUSD AND regime=trending_bull AND kill_zone=London |

The regime gate is the only K55-shadow-specific override. It's optional but reduces shadow noise from a known-failed cell.

---

## 6. Daily trade-frequency projection

### 6.1 Cohort-derived rate

528 rows / ~14 months → ~37.7 setups/month → **~1.26 setups/day** across 7 instruments.

| K band | Setups taken | Per month | Per year |
|---|---:|---:|---:|
| Top 3% | ~3% × 1.26 ≈ 0.038/day | ~1.13 | ~13.6 |
| Top 5% | ~5% × 1.26 ≈ 0.063/day | ~1.89 | ~22.6 |
| Top 7% | ~7% × 1.26 ≈ 0.088/day | ~2.65 | ~31.7 |

### 6.2 Excluding US30_CASH

US30_CASH represents ~6/7 ≈ 14% of cohort flows (n=72 in 528). Top-K excluding US30 reduces deployment frequency by ~5% (US30 was already low-confidence and rarely in top-K).

### 6.3 Combined with NAS_US30 specialist (Agent C ship)

Agent C's NAS_US30 specialist deploys at p≥0.55 on NAS100 + US30_cash with cohort frequency ~2-3 trades/month. Combined K55-shadow load: top-5% K54 v3 (excl US30) + NAS_US30 specialist ≈ **~4-5 trades/month**.

---

## 7. 30-day shadow promotion gate

### 7.1 Pre-registered hypothesis

See `agent_a2_pre_registered_hypothesis_draft.md`. Headline:

> *"K54 v3 deployed at top-3% confidence (per recalibrated isotonic-mapped + jittered predictions, on isotonic regressor fit to the 528-row Q1.3 cohort using LOOP-honest pooled-CPCV labels), excluding US30_CASH symbol, achieves realized-R lift ≥ +0.10R/trade on the 14-day prospective holdout 2026-04-29 → 2026-05-12 + 30-day forward shadow window with bootstrap 95% CI excluding zero AND CPCV-honest single-test p < 0.05."*

### 7.2 Threshold ladder for promotion

| Tier | Gate | Outcome |
|---|---|---|
| **K55-shadow research-grade (current spec)** | Top-3% deployment, observed in shadow ≥ 30 days, ≥ 5 realized samples | Continue shadow logging; analyze on each samples ≥ 5 cumulative |
| **Promotion to live A/B (capped)** | 30d shadow lift ≥ +0.10R/trade AND bootstrap 95% CI excludes zero AND DSR-p < 0.05 (at effective N = 200 + ~30 trades enumerated) | Live A/B at 50% normal position size on takes |
| **Full deploy** | 60d live A/B confirms lift AND DSR-p < 0.001 AND no per-symbol regression | Live at 100% position size |

### 7.3 What FAIL means

If 30d shadow data shows lift < +0.10R/trade OR CI includes zero OR DSR-p ≥ 0.05:
- **Drop K54 v3 from K55-shadow.** No live deployment.
- **Pivot to Q1.5 cohort-expansion path** (per Q1.4 postmortem §5.2).
- **Keep NAS_US30 specialist on independent track** (Agent C ship); it has its own promotion gate.
- **Why-it-failed memo to KILLED_HYPOTHESES.md** with 30d shadow data attached.

### 7.4 Pre-registration discipline (mandatory before deploy)

Per Agent B §7.2 + Q1.4 postmortem §5.3:
1. **Hypothesis text LOCKED** — written into `PRE_REGISTERED_HYPOTHESES.md` BEFORE deploy.
2. **Holdout LOCKED** — 14-day prospective window 2026-04-29 → 2026-05-12 NOT touched until shadow eval.
3. **Single-eval discipline** — open holdout ONCE at end of 30d shadow window. No interim peeks.
4. **DSR + bootstrap CI + per-symbol decomposition** all reported in eval.
5. **Result:** PASS / FAIL / INVALIDATED_PRE_TEST recorded; failures get why-it-failed memo.

---

## 8. Implementation checklist

### 8.1 Code-side (additive; CEO approval required for production wire-up)

- [ ] Fit `IsotonicRegression` on pooled CPCV-test (p, y) sample. Save to `models/k54_v3/isotonic_global.pkl`.
- [ ] Add `K54V3Predictor` component to `src/components/`. Constructor loads LightGBM + isotonic + feature list.
- [ ] Wire feature engineering: extract K54 v3 1,240 features at runtime. (Largest engineering work.)
- [ ] Add 7-day rolling buffer to `pipeline_state/k54_v3_pred_buffer.json`.
- [ ] Inject K55-shadow logger after Component 3A. Fail-safe: if predictor fails, fall through to existing pipeline.
- [ ] Add `shadow_logs/k54_v3_predictions.jsonl` writer.
- [ ] Add cron monitor: `scripts/k54_v3_shadow_monitor.py` reads jsonl, computes rolling lift + CI.

### 8.2 Configuration

`config/agent_config.yaml` additions:
```yaml
k54_v3_shadow:
  enabled: true                       # SHADOW-ONLY; no trade impact
  isotonic_path: "models/k54_v3/isotonic_global.pkl"
  lgb_path: "models/k54_v3/k54_v3_global.lgb"
  feature_list_path: "models/k54_v3/feature_list.txt"
  buffer_size_days: 7
  top_k_pcts: [3, 5]                   # log both
  symbol_exclusions: ["US30_CASH"]
  jitter_sd: 0.001
  jitter_seed_field: "candle_utc_timestamp"
  trade_impact: false                  # false = log-only; true = wire to Component 4
  shadow_log_path: "shadow_logs/k54_v3_predictions.jsonl"
```

### 8.3 Monitoring

- Daily: rolling 30d K55-shadow lift + bootstrap CI + DSR-p reported via watchdog.
- Weekly: per-symbol breakdown of K55-shadow signals.
- Monthly: full shadow analysis (PASS / FAIL / EXTEND).

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Feature-engineering layer is large work; could delay deploy | Defer to Q1.5; ship NAS_US30 specialist (lighter feature set) FIRST. |
| Isotonic regressor needs refit if cohort drifts | Plan: refit every 90 days on the latest 528-row cohort window. |
| Top-3% activation too rare for 30d statistical power | Run top-5% in parallel; analyze whichever has more samples at 30d. |
| US30_CASH might recover under future architecture | Monitor per-symbol breakdown; if US30 AUC > 0.5 in 30d shadow, RE-INCLUDE. |
| Regime gate (XAUUSD trending_bull London) reduces signal | Optional — disable if shadow data shows no correlation. |
| Pre-registered hypothesis becomes stale | Write hypothesis 24h before deploy; ensure PRE_REGISTERED_HYPOTHESES.md committed before any production code touches the predictor. |

---

## 10. Approvals required

Per CLAUDE.md "WF-1 DISCIPLINE":
- **CEO approval REQUIRED** — K55-shadow shadow-logger is observational, but the feature engineering layer modifies `src/` and `config/agent_config.yaml`.
- **Allowed without approval:** the isotonic refit + analysis (this dispatch's work, fully in `research/`).
- **Required for deploy:** CEO sign-off on (a) the spec text, (b) the pre-registered hypothesis text, (c) the 30d shadow window.

---

## 11. Companion files

- `agent_a2_recalibrated_ablation.md` — full forensic analysis underlying this spec.
- `agent_a2_pre_registered_hypothesis_draft.md` — pre-registration text for `PRE_REGISTERED_HYPOTHESES.md`.
- `agent_a2_extended_top_k_sweep.json` — top-K curve underlying §3.3 K choice.
- `agent_a2_isotonic_calibration.json` — isotonic vs Platt comparison underlying §1.1 architecture.
- `agent_a2_dsr_alt_eff_n.json` — DSR-p across alt eff_N anchors underlying §7.2.

---

*End of K55-shadow spec. Pending CEO approval before any wire-up. Subscription-only, READ-ONLY, no production modifications in this dispatch.*
