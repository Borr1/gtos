# GTOS ML Research Program — 4-Quarter Roadmap

**Mission:** Stand up a locally-served deterministic ML system that becomes either:

- **(a)** the primary decision layer of GTOS, replacing the live Anthropic-API-dependent AI, or
- **(b)** a high-quality advisory ensemble member if the AI proves un-replaceable.

The decision is data-driven. We don't pick the outcome; the program does.

**Sovereignty doctrine:** Production runs locally. No Anthropic dependency in the live path. Inference cost per candle effectively zero. Frozen, deterministic, auditable models. Anthropic API is used ONLY for offline research.

---

## Billing model (program-wide)

- **Claude Code subscription** pays for all agent dispatches (audit, feature engineering, modeling, stats, adversarial, productionization). No per-task variable cost.
- **Anthropic API ($50/mo cap, auto-reload disabled)** is hit only by prompt-replay research (K55 ML-vs-AI, HALLUC-style A/Bs).
- Phases are bounded by **wallclock + dispatch shape + quality discipline**, not dollar budgets.

See `COMPUTE_LEDGER.md` for per-dispatch tracking.

---

## Q1 — Foundation: data + features + K54 v2

**Primary hypothesis (pre-registered):** Expanded 2K-feature catalog (4× K54 v1) lifts per-regime LightGBM OOS AUC by ≥0.04, from K54 v1 baseline 0.571 → ≥0.61, on held-out 2026-H2 window with strict CPCV + purge gaps.

**Threshold:** AUC ≥ 0.61 on 30% holdout, opened ONCE.

**Sub-tasks:**

1. K54 v1 audit (Week 1) — feature set, holdout, AUC reproduction, gap analysis.
2. Feature catalog v2 (Week 2-3) — six families: structure, microstructure, volatility, time/session, liquidity, regime.
3. K54 v2 training (Week 4) — per-regime LightGBM, hyperparameter search (Optuna), CPCV with 6 splits + 1-week purge gaps.
4. Cross-instrument replication (Week 4) — train on XAUUSD, test on the other 6.
5. Cross-period replication (Week 4) — train on 2022-2025, test on 2026.
6. Statistical validation (Week 5-6) — Bonferroni, white-noise null, BH-FDR for exploratory.
7. Adversarial audit (Week 5-6) — leakage hunt, survivorship-bias check, robustness probe.
8. End-of-Q1 verdict + Q2 spec.

**Wallclock:** 4-6 weeks.
**Dispatch shape:** ~10-15 subscription-bounded agents (1 auditor, 6 feature-family agents, 1 modeler, 1 statistician, 1 adversarial validator, 1-3 replication runs).
**Anthropic API forecast:** $0 (no prompt replays in this phase).

---

## Q2 — Per-regime + sequence + ensemble

**Primary hypothesis:** Stacked ensemble {regime-conditional LightGBM (K54 v2), M5 LSTM sequence model on 64-bar windows} achieves OOS Sharpe ≥1.3 with n≥200 setups on 2026-H2 holdout, per-instrument averaged across 7 production instruments.

**Threshold:** Sharpe ≥1.3 AND n≥200 AND positive Sharpe on ≥4 of 7 instruments.

**Sub-tasks:**

1. Sequence-model architecture spec (LSTM vs lightweight Transformer; 64- and 128-bar windows on M5 + M15).
2. Per-instrument fine-tune cycles.
3. Stacking architecture (meta-learner on probabilities + regime label).
4. ONNX export pipeline (validate inference matches Python training output bit-exact).
5. Decay velocity benchmarking on each model class.
6. (Optional, API-billed) K55 ML-vs-AI head-to-head replay on a held-out CANDIDATE cohort.

**Wallclock:** 6-8 weeks.
**Dispatch shape:** ~8-12 subscription-bounded agents (sequence-model spec + per-instrument fine-tuners + stacking + ONNX validator + decay analyst).
**Anthropic API forecast:** TBD — K55 design dependent. ~$0.10/setup × 200 setups ≈ $20 if a head-to-head replay is included.

---

## Q3 — Tick microstructure + cross-instrument replication

**Primary hypothesis:** Tick-level features (cumulative delta, footprint imbalance, large-trade clusters, micro-reversal counts) add ≥0.03 OOS AUC to the Q2 ensemble AND replicate (positive marginal AUC) across ≥4 of 7 instruments.

**Threshold:** Both conditions hold simultaneously.

**Sub-tasks:**

1. Tick-capture daemon coverage audit per instrument.
2. Build tick-level feature primitives (stubs in `src/research_infra/microstructure_features.py`).
3. CPCV with tick + OHLCV joint feature space.
4. Orthogonality test — tick features must have correlation <0.3 with OHLCV after Q2 ensemble residualization.
5. Cross-instrument replication explicit (hardest gate).

**Wallclock:** 6-8 weeks.
**Dispatch shape:** ~8-12 subscription-bounded agents (tick-feature engineer per primitive + CPCV runner + replication checker + orthogonality auditor).
**Anthropic API forecast:** $0 (local features; no prompt replays).

---

## Q4 — Production hardening + 30-day shadow + scale

**Primary hypothesis:** 30-day live shadow signal correlation with realized R is ≥1.2× the live AI primary_analyzer's correlation over the same window.

**Threshold:** Correlation ratio ≥1.2 across the 7 instruments.

**Sub-tasks:**

1. ONNX deployment harness in `research/ml_program/shadow/`.
2. Live shadow worker mirrors orchestrator's per-candle calls; logs predictions in parallel. Worker NEVER calls orchestrator, NEVER touches MT5, NEVER influences live decisions.
3. Per-feature distribution drift monitor (KS-test rolling-30-day vs trained, alarm at p<0.01).
4. Per-model AUC drift monitor (rolling-30-day; alarm if drops below promotion threshold).
5. Auto-retrain trigger spec (gradient-boosted only; sequence models manual).
6. Risk overlay (Kelly fractional, vol-targeted) integrated with shadow.
7. 30-day shadow run + realized-R correlation comparison.

**Wallclock:** 4-6 weeks shadow + 2 weeks integration.
**Dispatch shape:** ~6-10 subscription-bounded agents (ONNX harness + shadow worker + 2 drift monitors + retrain spec + risk overlay).
**Anthropic API forecast:** $0 (local ONNX inference; production AI charged to live-trading $-cap, not this program).

---

## End-state decision tree

| Phases hit | Action |
|---|---|
| **4 of 4** | Propose AI-to-ML primary swap to CEO; AI moves to advisory. |
| **3 of 4** | Keep ML as advisory ensemble member; AI stays primary. |
| **2 of 4** | ML is supplementary signal; selectively integrate replicated features. |
| **0-1 of 4** | Price-action-only ML doesn't replace AI; document the boundary and stop. |

A failed primary hypothesis at a phase boundary HALTS forward progression. Re-spec the failed phase with a new hypothesis informed by the why-it-failed memo (`KILLED_HYPOTHESES.md`), or escalate to CEO if 2 attempts on the same phase have burned.

---

## Hard constraints (non-negotiable across all phases)

- **Pure market state only.** MT5-derivable: OHLCV across timeframes + tick. No news, options, macro, positioning, sentiment.
- **Locally-served inference.** Final production model deploys as ONNX or pure-Python (LightGBM, XGBoost, scikit-learn). Sequence models export to ONNX. Sub-millisecond per-decision target.
- **Pre-registration is non-negotiable.** Every primary hypothesis enters `PRE_REGISTERED_HYPOTHESES.md` BEFORE data work begins. Append-only.
- **30% OOS holdout opened ONCE per phase.** Peeked = burned; need fresh data.
- **CPCV + walk-forward with purge gaps** (de Prado, *Advances in Financial Machine Learning*, ch. 7).
- **Multiple-comparison correction.** Bonferroni at α/N for primary hypotheses; BH-FDR for ranked exploratory features.
- **Cross-instrument replication required.** ≤2 of 7 = "instrument-specific" and de-prioritized for ensembling.
- **Cross-period replication required.** Works on ≥2 of {2022-2023, 2024-2025, 2026}.
- **No production state changes.** Read from `data/`, `knowledge_base/`, `shadow_logs/`. NEVER modify `src/`, `config/`, `scripts/canary_fixtures/`, or any `pipeline_state/` file.

---

## Research-plane / production-plane separation

```
RESEARCH PLANE  (this program operates here)
  Claude Code agents drive: data engineering, feature engineering,
  model training, backtest, statistical validation, decay analysis,
  leakage hunting. Subscription cost; no per-trade API.

   ↓  (proven ML models exported as ONNX after passing all gates)

PRODUCTION PLANE  (sacred; we read its data, never modify)
  Local ML inference per M15 candle close. <1ms. No external calls.
  Eventually swaps the Anthropic primary_analyzer for the local ONNX
  model.
```

---

*Maintained by the ML Program Orchestrator. Updated when phase boundaries cross.*
*Last updated: 2026-04-28 (program kickoff; budget framing corrected).*
