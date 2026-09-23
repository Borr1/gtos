# GTOS Research Program — Fresh Session Kickoff

**Created:** 2026-04-26 (session 41 close)
**For:** Session 42 onwards
**Mandate:** "close the gap with engineering work, not waiting for live data" (CEO 2026-04-26)
**Operating principle:** Live sessions are primarily for broker slippage + Anthropic API tail latency under load. Almost everything else is offline-answerable with existing data.

---

## Executive Summary

A program of **81 research/engineering tasks** organized into 4 phases. Most can be executed offline against existing data (367-trade canonical batch + 1,240 live evaluations + 65,201-line structure divergence log + 51MB trade records + 53MB historical OHLCV).

**Cost ceiling (uncapped path):** $2,700-5,700 in API spend across the program.
**Cost ceiling (optimized path):** **$850-3,970** with Batch API + prompt caching + Haiku routing applied = ~65% reduction.

**Phase 1 (THIS IS WHERE TO START):** 35-40 subscription-only tasks. **$0 API.** ~3 weeks of dispatched agent work. Generates massive insight before any spend.

**CEO directive:** Phase 1 first (compute tasks only), then look at API tasks.

---

## Cost Optimization — INTEGRATE BEFORE ANY API TASK

Before spending any API dollars on backtests, build these into the research infrastructure:

### 1. Batch API integration (highest ROI — $1,350-2,850 saved)
- **50% discount** on all input + output tokens for asynchronous workloads
- Fully supports `cache_control: ephemeral` + `effort=max`
- 24h SLA (typical <1h turnaround); fine for offline research
- Batch size: 100,000 requests / 256 MB max (our 7,000 evals fit easily)
- Implementation: wrap existing `messages.create()` calls into batch request objects with `custom_id` for result mapping
- **Verify before committing:** test single batch with `effort=max` to confirm equivalence to synchronous call

### 2. Prompt caching with 1h TTL (additional $380-600 saved)
- **95%+ cache hit rate** on system prompt across backtest runs
- 1h TTL: write cost 2× base, read cost 0.10× base — break-even after 2 reads
- Configure: `cache_control: {type: "ephemeral", ttl: "1h"}` at root of cached blocks
- System prompt + MSO framework sections (~3,500 tokens) cache; per-call market_state varies (~100-200 tokens)
- Verify cache hits via response `usage.cache_read_input_tokens` / `usage.cache_creation_input_tokens`

### 3. Cost tracking wrapper (visibility — $0 savings but enables budgeting)
- Per-call cost calculation from `usage` block in API response
- Aggregate per-backtest run; log to `.jsonl` for audit
- Alert if cumulative spend approaches budget ceiling

### 4. Haiku routing for non-trading tasks (additional $60-120 saved)
- Trading-decision gate (MSO): **stays Sonnet 4.6 effort=max** — non-negotiable per memory `project_opus_vs_sonnet_p2c.md` (CR 38% vs 19%, WR 69.6% vs 60.9%)
- Decay analysis / regime classification / setup metadata extraction: Haiku 4.5 viable
- Pre-validate quality: 50-eval A/B test before routing 20% of evals through Haiku
- Risk: if Haiku underperforms on regime task, rollback (no $ penalty)

### What NOT to optimize
- **`effort=max` stays.** Downgrading saves 30-40% tokens but loses 5-10% WR. Edge-killing tradeoff.
- **Enterprise discount.** Below $10K/month threshold; not worth pursuing.
- **Multi-modal images don't cache** — keep image experiment scoped to ≤500 evals if pursued.

### Integration order (Phase 1 prerequisites)
1. **Day 1:** Batch API wrapper (~6h dev + tests)
2. **Day 2:** Cost tracking wrapper (~3h)
3. **Day 3-4:** 1h-TTL caching layer + cache-hit verification (~8h)
4. **Day 5:** Pilot batch with 50-100 evals; verify savings empirically before scaling

This 1-week infrastructure investment pays back ~$1,700-3,500 across the program.

---

## Phase 1 — Subscription-Only Tasks ($0 API, ~3 weeks)

35-40 tasks that don't require running AI on historical data. Pure data analysis, simulation, code work. **Start here.**

### A. Decay Diagnostic — System vs Regime (HIGHEST PRIORITY)

The dumb-momentum baseline test was run on April 2026 XAUUSD only. Extend it.

- **A1. Full historical dumb-baseline replay.** Run mechanical 80%-retrace pullback on every CAND across full historical × 7 instruments. Quantify per-month per-instrument AI-vs-mechanical gap. **If gap closed in some periods → decay is regime. If gap is constant 30-40pp → decay is AI-side persistent.** Critical strategic answer.
- **A2. Per-month per-instrument WR/ExpR rolling 50-trade windows.** Decay velocity per instrument.
- **A3. Per-month per-session per-regime stratification.** Identify exact regime change points.
- **A5. Regime-stratified WR matrix.** Use existing structure_detector_divergences.jsonl (65,201 lines, 80 days H4) to tag every CAND with regime. Compute WR per regime per instrument.
- **A6. Component decay attribution.** Bayesian decomposition: how much WR loss attributes to OB-zone advantage vs displacement vs FVG vs touch-count vs framework vs session?

**Data sources:** `knowledge_base/trade_records/{INSTRUMENT}/*.json` (150 fills), `knowledge_base/live_evaluations/` (1,240 evaluations), `shadow_logs/structure_detector_divergences.jsonl` (65k rows), `data/historical_2026/*.csv` (53MB).

**Expected output:** Definitive decay diagnosis. Memory update: replace current speculation about 60/40 system/regime split with empirically-grounded ratio.

### B. AI Behavior Characterization (subscription-only subset)

- **B7. Hallucination rate systematic measurement.** Programmatic comparison of AI-stated price levels vs MSO raw_data on every historical evaluation. Per-instrument, per-regime, per-framework hallucination rate. (No AI re-run; analyze existing outputs.)
- **B12. Confidence scorer deep autopsy.** Spearman correlation of confidence vs realized R, stratified by instrument/framework/regime/session/setup_grade/time-of-day. **Find ANY conditional under which confidence is predictive.** (Pure stat analysis on existing data.)
- **B14. Walk-level vs realized-R systematic study.** For every walk-level signal we have (touch count, distance-to-OB, displacement quality, etc.), compute realized R per stratum. Find any walk-level signal that IS predictive (counter to current memory).

### C. Shipped-Fix Validation (subset, no AI re-run)

- **C15. ADR-006 tolerance gate counterfactual on full history.** Replay every historical sl_beyond_ob L2 rejection through new tolerance gate logic (no AI rerun needed — just gate-decision replay). Per-instrument acceptance rate change. For setups now-passing, what's their realized R from forward_resolution data?
- **C16. Per-instrument tight-FX override sensitivity.** Sweep ATR multipliers (0.25, 0.30, 0.40, 0.50, 0.60) and min_ticks (3, 5, 8, 12) on EURUSD/GBPUSD/USDJPY rejection cohort. Find Pareto frontier of acceptance × realized R. (Gate logic replay only.)

### D. Multi-Framework Analysis (subset)

- **D20. POI co-occurrence matrix.** Cross-tabulate (ob_retest POI present) × (fvg_fill POI present) × (breaker_re_entry POI present) across full 9,069-row pre-AI data. Determines OPTIONALITY vs REDUNDANCY vs DIVERSIFICATION.
- **D23. Framework-class fit study.** Per-class per-framework realized R decomposition from existing trade records.

### E. Synthetic Tick Reconstruction

- **E24. Synthetic tick reconstruction from M1.** `XAUUSD_M1.csv` (5.4MB) + similar M1 for other instruments. Within each M15 bar, simulate tick sequence from M1 OHLC. Compute Lee-Ready proxy from directional candles. NOT broker-real but DIRECTIONALLY useful for D.1 partial unlock.
- **E26. Microstructure-WR correlation study.** Compute synthetic cumulative_delta + footprint imbalance + micro_reversal_count from M1. Correlate with realized R per setup. Identifies which microstructure features are predictive vs noise.

### H. Regime Classifier Activation (subset, no AI re-run)

- **H36. Regime classifier on full historical structure data.** 65,201 lines exist. Cross-reference with historical trade outcomes. Compute realized R per regime per instrument per session.
- **H37. Regime stability analysis.** How often does regime flip mid-trade? How often does regime predict outcome? Persistence measurement.
- **H38. Regime-aware sizing simulator.** Test: 0.25% in chop, 0.5% in trending, 1.0% in reversal. Vs static sizing. Measure DD distribution + total R.

### I. Cross-Instrument Correlation Gate Calibration

- **I41. Threshold sensitivity sweep.** Test 0.3, 0.4, 0.5, 0.6 on every historical multi-position cluster. Per-threshold: cluster catch rate × realized R impact.
- **I42. Window-size sensitivity.** Test 1mo, 3mo, 6mo, 12mo correlation windows.
- **I43. USD-weakness regime detection.** Identify all historical USD-weakness days. On those days, did 4-way LONG cluster trigger correctly?
- **I44. Per-cluster realized-R counterfactual.** Replay every historical cluster ≥3 with gate ON vs OFF.

### J. Position Management Optimization

- **J45. Trailing stop policy sweep.** Test 5+ trail rules (fixed-pip, ATR-multiple, structural, parabolic, time-decay) on every historical fill's full price path.
- **J46. Partial close ratio optimization.** Currently 100% close at TP1. Test 25/50/75/100% with trail policies.
- **J47. Breakeven trigger optimization.** Test alternatives to current "BE on KZ end if profitable."
- **J48. Time-stop policy.** How many losers would have closed earlier with time-based exit? Win-rate-survival curves.
- **J49. TP1 distance sweep.** Sweep 1.0R, 1.5R, 2.0R, 2.5R, 3.0R per instrument.

### K. Edge Decomposition

- **K50. Causal edge attribution.** SHAP/Bayesian decomposition: how much R from OB-zone advantage vs displacement vs FVG vs touch-count vs framework vs session?
- **K51. Decayed-component identification.** Same decomposition over time. Which components have lost edge magnitude?
- **K52. Bonferroni-survival re-test.** Re-run statistical tests on the 5 surviving findings against current 2-year data.
- **K53. Loser anti-pattern classifier.** Cluster 150+ losers by feature vectors. Build "smell test" classifier.
- **K54. ML classifier training pipeline (algorithmic-gate migration step 1).** Train XGBoost/LightGBM on labeled CAND outcome data using Phase 1 feature outputs (K50-53 SHAP features + B12 confidence conditionals + B14 walk-level survivors + H36-38 regime tags + Q72 spread context). Walk-forward validation. Per-regime ensemble. Calibrated probability output. Hold-out test set drawn from forward time slices to measure regime-non-stationarity sensitivity. **Strategic motivation:** AI gate is the only AI-dependent stage in the pipeline (everything else — POI detection, SL/TP geometry, execution, position management — is already pure algorithmic). If ML can match AI gate quality, the system becomes deterministic + cheap + Anthropic-outage-immune. Memory `project_dumb_momentum_baseline_findings` quantifies the AI-vs-mechanical gap; this task builds the ML alternative to AI for that gap. Subscription compute, $0 API.
- **K55. ML-vs-AI shadow comparison harness (algorithmic-gate migration step 2).** Wire K54 output as a parallel shadow predictor alongside live AI gate. Log both predictions per evaluation. Compute realized-R per quadrant: (AI=trade, ML=trade), (AI=trade, ML=skip), (AI=skip, ML=trade), (AI=skip, ML=skip). After 30-60d shadow data, evaluate promotion criteria: ML hits ≥AI realized-R with statistical significance AND ML-disagreement quadrant is <20% of decisions. If criteria met → migrate primary gate to ML; AI becomes second-opinion / edge-case escalation. If criteria not met → diagnose ML failure modes, iterate features, retrain. Build only ($0); shadow data accumulates from live system once K54 is wired in.

### L. Backtest Infrastructure (code work, $0)

- **L54. Parallel T7 sim.** Currently 30-60 min for 1 instrument × 4 months. Parallelize to 8-16 weekly slices. <10 min wall clock.
- **L55. Incremental backtest engine.** Only re-evaluate diverged candles when prompt changes. 90% time savings.
- **L56. Prompt A/B harness.** Systematic comparator with pre-registered metrics.
- **L57. Edge-component ablation framework.** Drop one feature/section/gate at a time, automated.
- **L58. F3-replay infrastructure (D.3 prerequisite).**

### N. Bull/Bear/Judge Debate Shadow Wire (build only, $0)

- **N62. Wire debate in shadow mode.** Code work. Component 3B PAUSED → shadow-mode runs alongside primary. 3× tokens but subscription compute = $0 incremental for shadow runs.

### O. Knowledge Base / Vector Search Activation

- **O65. LanceDB historical CAND index.** vectordb directory empty per audit. Index every historical CAND with embedding (MSO features → vector). Pure code work.

### Q. Slippage Modeling from Existing Fills (no API)

- **Q71. Historical slippage from existing fills.** 150 trade_records have requested_price + fill_price. Compute distribution per instrument per session.
- **Q72. Spread-spike detection from M1 wick analysis.** Identify high-spread periods historically.
- **Q73. News-event-overlay.** Historical economic_calendar.csv exists. Does AI behavior degrade post-news? Causal study.

### R. Continuous Learning Architecture (build only, $0)

- **R74. Online prompt-revision loop.** Build infrastructure (no API spend yet).
- **R75. Weekly research auto-dispatch.** Cron-fired comprehensive review.

### S. Counterfactual / Twin-Sim Studies

- **S77. What-if-different-broker simulation.** Apply different broker spread/slippage profiles to existing OHLCV. How edge-sensitive are we to broker choice?
- **S78. What-if-different-fleet.** Edge analysis on subsets: 3-best, 5-without-XAUUSD, etc.
- **S79. What-if-different-risk-policy.** Cap=2/3/4, risk=0.5%/1%/2%. Optimal Phase 1 profile.

---

## Phase 2 — Selective API Tasks (~$500-1,000 OPTIMIZED, ~$1,500-3,000 BASELINE)

The highest-ROI API spenders. Run AFTER Phase 1 results inform priorities. AFTER batch + caching infrastructure is built.

### A. Decay Diagnostic API tasks
- **A4. AI-on-historical-CANDs replay with current prompt.** Run V3 + ADR-006 + B.1 + parallel dispatch retroactively on every historical CAND. Compare to actual AI decisions of the time. Did our shipped fixes recover the decay or not?
  - **Cost optimized:** $40-90 with batch + caching (vs $80-180 baseline)

### B. AI Behavior API tasks
- **B8. Self-consistency stress test.** Same MSO through Sonnet 4.6 effort=max N=200 times. Variance.
- **B9. Adversarial prompts.** Edge-case MSOs.
- **B10. Prompt ablation matrix.** Remove each prompt section systematically. Quantify load-bearing contribution. (~$25-50 optimized)
- **B11. Model comparison ladder.** Sonnet 4.6 max vs high vs Opus 4.6 vs Sonnet 4.5. (~$100-200 optimized — EXPENSIVE)
- **B13. Cross-instrument calibration.** Identical setup, different instrument labels. (~$3-5 optimized)

### C. Fix Validation API tasks
- **C17. Parallel-evaluation framework dispatch full BT.** AI's actual framework selection on full 2-year. (~$40-90 optimized)
- **C18. B.1 |corr| gate impact.** With vs without correlation gate active. (~$25-50 optimized)
- **C19. v2 detector full 2-year BT.** SHORT signal recovery magnitude. (~$40-80 optimized)

### D. Multi-Framework API tasks
- **D21. Per-framework expectancy.** Force AI to use only one framework, measure per-framework realized R. (~$100-150 optimized)
- **D22. Tiebreaker policy ablation.** (~$25-50 optimized)

### E. Synthetic Tick API task
- **E25. Synthetic tick features in prompt experiment.** AI re-run with tick context injected. (~$25-50 optimized)

### F. AI Feedback Loop (HIGH LEVERAGE)
- **F27. Backward outcome injection prototype.** ($25-50 optimized)
- **F28. Feedback granularity sweep.** ($100-200 optimized)
- **F29. Adaptive prompt revision A/B framework.** ($50-150 optimized)
- **F30. Memory-augmented evaluation.** ($50-100 optimized)

**Total Phase 2 optimized: ~$500-1,200** (pre-batch+cache: $1,500-3,000)

---

## Phase 3 — Long-Horizon (~$300-1,500 OPTIMIZED)

After Phase 2 informs strategic direction.

- **G31-35. Tool-use grounding D.3 Phase 1.** Tool A complete, Tool B+C scaffolding, F3-replay A/B. (~$50-125 optimized)
- **M59-61. Multi-modal chart input experiment.** Image generation + multi-modal calls. **Note: images don't cache.** Limit to 500-1,000 evals to control cost. (~$150-350 optimized)
- **N63-64. Bull/Bear/Judge debate active study.** Disagreement analysis + confidence ensembling. (~$100-250 optimized)
- **O66-67. Retrieval-augmented evaluation.** Similar-setup retrieval + loser-similarity warning. (~$75-150 optimized)
- **P68-70. Prompt resurrection program.** V4/LIRA/cascade re-run on full 2-year + V5 systematic generation + cascade reconstruction. (~$325-650 optimized — most expensive Phase 3 cluster)

---

## Phase 4 — Continuous Learning (low ongoing cost)

After foundations from Phase 1-3.

- **R76. Self-improving meta-prompt** (research-track design, low active cost once shipped)
- **D.3 production wiring** (after Phase 1 F3-replay confirms gains)
- **Multi-modal production wiring** (only if Phase 3 experiment shows clear edge)

Steady-state: ~$50-100/month additional API for continuous learning loops.

---

## Truly Live-Data-Blocked Items (~5% of total)

These are the only items that genuinely need Monday onwards live data:

1. **Real broker slippage** on FTMO MT5 fills — observed-vs-requested distributions
2. **Broker partial-fill behavior** under FTMO load
3. **Gap-on-news fills** (Sunday open, NFP open)
4. **Anthropic API tail latency** during NY open volume
5. **MT5 connection stability** under multi-instrument concurrent load
6. **Real broker tick data** (daemon starts Monday automatically)

Everything else: **offline-answerable with existing data**.

---

## Recommended Execution Sequencing

### Week 1 (Phase 0 — Infrastructure, $0 API)
1. Batch API wrapper + tests
2. Cost tracking wrapper
3. 1h-TTL caching layer
4. Pilot batch (50-100 evals) to verify savings empirically
5. L54-58: Backtest infrastructure improvements (parallel T7, A/B harness, ablation framework)

### Week 2-3 (Phase 1A — Decay diagnostic, $0 API)
6. A1-A6: Full decay diagnostic sweep
7. K50-K53: Edge decomposition
8. B7, B12, B14: AI behavior subset
9. **Strategic deliverable:** definitive system-vs-regime decay diagnosis

### Week 3-4 (Phase 1B — Validation + Position Management, $0 API)
10. C15-C16: Shipped-fix validation
11. J45-J49: Position management optimization
12. I41-I44: Correlation gate calibration
13. H36-H40: Regime classifier outcome correlation

### Week 4-5 (Phase 1C — Quick wins + Infrastructure, $0 API)
14. E24, E26: Synthetic tick reconstruction + correlation
15. D20, D23: Multi-framework analysis (subset)
16. Q71-Q73: Slippage modeling
17. S77-S79: Counterfactual sims
18. N62: Bull/Bear/Judge wire shadow (build only)
19. O65: LanceDB index build
20. R74-R75: Continuous learning architecture (build)

### Week 5-6 (Phase 1D — Algorithmic-gate migration setup, $0 API)
21. K54: Train ML classifier on Phase 1 feature outputs (gradient boosting + walk-forward + per-regime ensemble)
22. K55: Wire ML-vs-AI shadow comparison harness (build only; shadow data accumulates from live system)

### Week 6+ (CEO authorizes Phase 2 budget after Phase 1 results inform priorities)

### Estimated Phase 1 total time: ~5-6 weeks of dispatched agent work
- Subscription compute only
- $0 incremental API spend
- Generates definitive answers on decay, edge magnitude, position management ROI, AI behavior characterization

---

## Dependencies & Critical Path

- Phase 0 infrastructure → blocks Phase 2 (need cost optimization in place)
- A1-A6 decay diagnostic → unblocks regime-aware sizing decisions (H38, D.2 promotion)
- B7 hallucination measurement → quantifies tool-use Phase 1 ROI ceiling
- C15-C16 fix validation → confirms ADR-006 actually works as designed (pre-Monday confidence boost)
- K50-K53 edge decomposition → identifies which components are decaying (informs prompt research P68-P70)
- L54-L58 backtest infrastructure → speeds up everything in Phase 2-4
- N62 debate wire → enables N63-64 ensembling study in Phase 3
- K54 ML classifier training → requires K50-53 + B12 + B14 + H36-38 outputs as feature inputs; produces shadow-mode classifier
- K55 ML-vs-AI shadow harness → requires K54 trained model; runs in production parallel to live AI gate; 30-60d shadow data informs algorithmic-gate migration decision

---

## Reference Index

**Memory files (always cross-check before flagging stale code):**
- `feedback_engineer_systemic_not_patches` — engineer not patches
- `feedback_audit_driven_cleanup_pattern` — multi-agent audit pattern
- `feedback_walk_level_evidence_not_predictive` — walk-level not predictive of realized R
- `feedback_decay_is_ceo_number_one_concern` — backtest-shadow > live-shadow when feasible
- `feedback_research_goal_high_quality_frequency` — optimize R/month, not freq vs WR
- `feedback_billing_tracks_distinction` — subscription vs API billing separate
- `project_anthropic_billing_auto_reload_disabled` — $50/mo cap (need to revise for research budget)
- `project_distributional_findings` — fat tail ξ=0.35, GARCH 0.9906 calibration
- `project_eurusd_sl_root_cause` — multi-causal SL bug class
- `project_multi_framework_dispatch_suppression` — Verdict B finding
- `project_live_l2_rejection_per_instrument` — pre-FA-2 baseline rates
- `project_opus_vs_sonnet_p2c` — Sonnet wins for live gate

**ADRs (decision records):**
- ADR-004: market_state v2 promotion (CLOSED-OPTION-C-DE-FACTO)
- ADR-005: touch-count gate decision logger
- ADR-006: SL geometry tolerance + parallel-evaluation dispatch + per-instrument tight-FX

**Audit artifacts (research/audit_2026_04_26/):**
- 26 individual audit reports (01-26)
- SYNTHESIS_TRIAGE.md — categorized findings
- 14 cross-audit confirmations

**Validated Numbers (CLAUDE.md + .context/01_knowledge_base/validated_numbers_caveats.md):**
- XAUUSD WR 62% (n=129 batch) — H1 baseline
- XAUUSD WR 24% (n=25 H2-2026) — chi-square p=0.006 vs H1
- OB zone advantage +17pp (p=0.003)
- 5 Bonferroni-surviving findings

**Current production state:**
- HEAD: `56bc7ca` (after this session's 12 commits)
- v2 detector ACTIVE
- ADR-006 shipped
- B.1 cross_instrument_context |corr|≥0.4 gate ACTIVE
- C.3 SPRT class-aware halt MANUAL mode
- A.1 sl_beyond_ob shadow logger ACTIVE
- A.2 direction-emission audit logger ACTIVE
- E.2 NY-candle window-boundary fixed
- Heartbeat per-symbol architecture
- 7 instruments live
- pytest 2752 passing, canary 75/75

---

## How to Start the Fresh Session

1. **Open new Claude Code session** in `C:\Users\MSI\Documents\ai-trading-agent`
2. **Standard orientation:**
   ```bash
   python scripts/generate_live_state.py
   cat .context/LIVE_STATE.md
   cat CLAUDE.md
   cat .context/02_session_handoffs/41_apr26_session_41_CLOSE_RESEARCH_PROGRAM_HANDOFF.md
   cat .context/02_session_handoffs/RESEARCH_PROGRAM_KICKOFF.md  # this document
   ```
3. **Confirm CEO authorization** for Phase 1 (subscription-only, $0 API)
4. **Start with Week 1 Phase 0:** Build batch API + cost tracking + caching infrastructure BEFORE any API task
5. **Dispatch Phase 1 agents in parallel** per the sequencing above. Each on feature branch. Validation agent at end of each week.
6. **Hold for CEO authorization** before starting Phase 2 (API budget)

---

## Critical Operating Principles for Fresh Session

1. **Engineer systemic, not patch** (memory). Each task gets a proper engineering brief.
2. **Avoid conservative-default deferral** (memory). If data already supports a decision, ship it.
3. **Walk-level evidence ≠ realized R** (memory). Always join with realized-R per stratum.
4. **Audit-driven cleanup pattern** (memory). For "comprehensive review" requests, dispatch ~20+ specialized agents → synthesis → CEO triage → parallel fix on feature branches → validation.
5. **Fresh sessions for major epics.** Don't try to do all 4 phases in one session. Plan for at least Phase 1 (one session), Phase 2 (next session), Phase 3 (third session).

---

## CEO Action Items Pre-Phase-2

Before authorizing Phase 2 (which spends API budget):

1. **Review Phase 1 results.** Especially the decay diagnostic (A1-A6).
2. **Authorize API budget.** Recommended: $1,500-3,000 for Phase 2 (gives headroom over $850 optimized estimate). Re-enable Anthropic auto-reload at higher cap.
3. **Strategic priority confirmation.** Which Phase 2 tasks should run first? My ranking is in this doc; CEO may differ.
4. **Live data accumulation review.** First 30d post-Monday data informs many Phase 2 decisions.

---

*Research program kickoff. Session 41 close 2026-04-26. Total scope ~79 tasks. Optimized cost ceiling $850-3,970. Phase 1 entry point: subscription-only Week 1 infrastructure builds.*
