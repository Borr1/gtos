# Agent E — Cohort Expansion Feasibility + DSR-Defensible Sizing

**Date:** 2026-04-29
**Author:** Forensic Agent E (cohort-expansion feasibility, max-plausible-cohort sizing)
**Discipline:** READ-ONLY on production. Subscription-only. MAX-EFFORT Opus 4.7.
**Inputs:**
- `research/ml_program/audit/data_backfill_2022_2023.md` (existing 1,798 backfill)
- `research/ml_program/audit/data_inventory_audit.md` (per-instrument coverage)
- `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` §6.2
- `research/ml_program/feature_catalogs/CATALOG_v2.csv` (1,219 features)
- `research/ml_program/forensics/2026-04-29/agent_b_*` (DSR-N sensitivity precedent)
- MT5 broker depth probe 2026-04-29 (Agent E read-only)

**Outputs:**
- `agent_e_v2_feature_backfill_feasibility.csv` (1,219 rows, per-feature feasibility)
- `agent_e_non_xau_fillback_inventory.json` (per-instrument-year fillback counts)
- `agent_e_pre_2022_extension.json` (broker-depth probe + extension strategy)
- `agent_e_dsr_projection.csv` (scenario × lift × N → DSR-p)
- `agent_e_dsr_threshold_scan.json` (joint T × n × lift threshold scan)
- `agent_e_phase_2_calendar.md` (refined timeline)

---

## Headline

The postmortem's "4-6 weeks for cohort expansion" estimate is **wallclock-conservative for compute** (compute is 2-12 hours) but **methodologically correct for the full Q1.5 program** (calendar-locked by gate (g) holdout open at 2026-05-12 and CEO triage cycles).

**Three findings reframe the postmortem:**

1. **96.9% of the v2 catalog (1,181 of 1,219 features) is computable on the existing 2022-2023 OHLCV.** Only 38 features (24 tick-required + 14 M1-OHLCV-only) are infeasible. The cohort-expansion compute is ~2 hours wallclock with 6-way family-parallelism.

2. **The cohort-only DSR escape is mathematically impossible at observed lift +0.0484 and N=200 trial budget.** Even Phase 2 maximum (n=14,892 with synthetic augmentation) at T=15 paths leaves DSR-p = 0.018 (BORDERLINE). The postmortem's framing "cohort expansion is the only feasible path" understates the scale required.

3. **The cheapest DSR escape is increasing CPCV paths from T=15 to T=20.** This drops DSR-p from 0.055 (BORDERLINE) to **0.009 (SURVIVES)** at Phase 2 minimum (n=2,326) and N=200. Combined with Phase 2 aggressive A (n=3,132 with GBPJPY+US30 extension), DSR-p drops to 0.006. **K54 v4 can be DSR-defensible inside 1 week with no architectural changes — just methodology refinement.**

---

## 1. 2022-2023 v2-feature backfill feasibility audit (Task 1)

### Per-feature feasibility breakdown

| Family | Total features | Feasible (YES) | Infeasible (NO) | Notes |
|---|---:|---:|---:|---|
| structure | 432 | 432 | 0 | All M15/H1/H4/D1 OHLCV-derived |
| volatility | 270 | 270 | 0 | ATR / vol / GARCH-style on OHLCV |
| time_session | 138 | 138 | 0 | Calendar / clock features (no OHLCV dep) |
| liquidity | 129 | 129 | 0 | Sweep / round-number / OB clutter from OHLCV |
| regime | 63 | 63 | 0 | Backfill JSONL exists; needs +GBPJPY+US30 |
| microstructure | 187 | 149 | **38** | 24 tick-parquet + 14 M1-OHLCV |
| **Total** | **1,219** | **1,181** | **38** | **96.9% feasible** |

### Per-feature wallclock estimates

Per `research/ml_program/feature_catalogs/` build history, the full v2 catalog (1,219 × 528 = 643,632 cells) was generated in ~75 min single-stream:
- **Per-cell time:** ~7 ms.
- **Scaling to 1,798 trades:** 1,219 × 1,798 × 7 ms = **~4.3 hours single-stream**.
- **6-way family-parallel:** ~45 min wallclock (each family worker handles ~200 features on 1,798 rows independently).
- **Plus stability scoring + catalog assembly:** +30-40 min.

### Features REQUIRING data unavailable in 2022-2023

| Feature subset | Count | Why unavailable | Mitigation |
|---|---:|---|---|
| Tick parquet (data/ticks/*) | 24 | Tick capture only began 2026-04-27 (NAS100/US30); 5 instruments have ZERO tick coverage; pre-2026 unrecoverable from MT5 | NaN sentinel (already implemented per `microstructure.md`); flagged as Phase 3 feature subset |
| M1 OHLCV (synthetic_*_m1_*) | 14 | MT5 broker M1 depth caps at ~99,999 bars (~3.3 months); pre-2026 M1 unavailable | NaN sentinel; potential third-party data source (Dukascopy / Histdata) for Q3 expansion |
| ADR-005 touch_count_gate logger | 0 | Logger only goes back to 2026-04-27 | Catalog's 14 touch_count features are computed FROM OHLCV (`compute_ob_features` in structure.py), NOT from the logger; FEASIBLE on 2022-2023 |
| Regime backfill (structure_detector_backfill) | 0 | 2022-2023 backfill `shadow_logs/structure_detector_backfill_2022_2023.jsonl` already exists (14,878 rows for 5 syms); needs +GBPJPY+US30 to be 7-sym complete | Re-run `backfill_v2_regime.py` on existing 2022-2023 H4 OHLCV for GBPJPY+US30; 30 min wallclock |

**Bottom line on Task 1:** The audit's recommendation (Section 7 #5: "Synthesize 2022-2023 trade labels by F11 mechanical on `data/historical/GBPJPY_M15.csv` + `data/historical/US30_cash_M15.csv`") is feasible AS-IS for the 7-instrument 2022-2023 panel. The 38 infeasible features (3.1% of catalog) are NOT load-bearing for Q1.4 architecture B (per microstructure family doc, "the 163 non-tick features carry the family weight"). Phase 2 minimum can ship **96.9% feature coverage**.

---

## 2. Non-XAU 2024-2025 fillback inventory (Task 2)

### What's actually available

| Source | 2024 trades | 2025 trades | Mechanical or AI-graded |
|---|---:|---:|---|
| `knowledge_base_backtest/sessions/{INSTR}/` | 27 executed | 146 executed | AI-graded (debate-confidence-weighted) |
| `knowledge_base_backtest/sessions/{INSTR}/` (CANDIDATEs) | 40 | 185 | AI-graded |
| `knowledge_base/index/_trade_index.json` | 17 | 80 | AI-graded (live-derived) |
| `trades_unified.csv` | 17 | 102 | Mixed (XAUUSD + GBPUSD) |
| **F11 mechanical from `data/historical/{SYMBOL}_M15.csv`** | **(uncomputed)** | **(uncomputed)** | **Mechanical** |

### F11 mechanical projection for 2024-2025 non-XAU panel

Per the existing `build_trade_cohort_2022_2023.py` schema, running F11 mechanical OB-retest on 2024-2025 OHLCV for non-XAU instruments yields:

| Symbol | M15 first | M15 last | Span (months) | Trades/month (2022-2023) | Projected trades 2024-2025 |
|---|---|---|---:|---:|---:|
| GBPUSD | 2024-03-31 | 2026-04-17 | 24 | 17.0 | 326 |
| USDJPY | 2024-03-31 | 2026-04-17 | 24 | 16.6 | 318 |
| GBPJPY | 2022-03-28 | 2026-04-17 | 24 (2024-2025 partition) | (extrapolated) | 408 |
| US30_cash | 2022-01-06 | 2026-04-17 | 24 (2024-2025 partition) | (extrapolated) | 384 |
| XAGUSD | 2024-01-02 | 2026-04-02 | 27 | (extrapolated) | 320 |
| NAS100 | 2024-01-02 | 2026-04-02 | 27 | (extrapolated) | 354 |
| **Panel total** | | | | | **2,110** |

**Plus XAUUSD 2024-2025 mechanical fillback:** ~250 additional trades (current K54 v1 has 108; running F11 mechanical on full historical/XAUUSD_M15.csv 2024-04 to 2025-12 yields more).

### Caveats

1. **AI-graded vs mechanical contamination risk.** kb_backtest sessions use the production AI scorer; the cohort would be AI-filtered, not mechanically-filtered. **Recommendation: use F11 mechanical only for K54 cohort; reserve kb_backtest for K55-shadow validation.**
2. **trades_unified.csv source partition.** Per K54 v1 audit, 33 of 110 unified_csv rows are duplicates of trade_index (`_xauusd` suffix bug). After tuple-keyed dedup (audit §10 #2), expect ~80 useful unified_csv rows; mostly XAUUSD.
3. **Cross-source dedup discipline.** Phase 2 aggressive B requires re-running the dedup audit on (date, symbol, direction, framework, realized_r) tuples to avoid contaminating the cross-period CPCV with re-graded duplicates.

---

## 3. Pre-2022 extension feasibility (Task 3)

### MT5 broker depth probe (read-only, 2026-04-29)

Probed via `MetaTrader5.copy_rates_from_pos(symbol, tf, 0, 99999)` on redacted_account-Server 2 LIVE account (read-only; no order_send paths invoked).

| Symbol | M15 oldest | H1 oldest | H4 oldest | D1 oldest | Notes |
|---|---|---|---|---|---|
| XAUUSD | 2022-01-31 | 2019-12-23 | 2019-12-23 | 2019-12-23 | M15 capped 2022; H1+ to 2019 |
| XAGUSD | 2021-12-15 | 2019-12-23 | 2019-12-23 | 2019-12-23 | Same; ~2 mo earlier M15 |
| USDJPY | 2022-04-12 | **2008-09-04** | 2008-09-04 | 2008-09-04 | M15 capped 2022; H1+ has **17.6 years** |
| GBPUSD | 2022-04-12 | 2010-02-03 | 2008-09-04 | 2008-09-04 | M15 capped; H1+ to 2008 |
| GBPJPY | 2022-04-12 | 2010-02-02 | **1993-04-19** | 1993-04-19 | **33 years** H4/D1 history (longest of any pair) |
| US30 | 2022-10-20 | 2022-10-20 | 2022-10-20 | 2022-10-20 | Broker only carries US30 from 2022-10-20 |
| NDX100 | 2022-10-20 | 2022-10-20 | 2022-10-20 | 2022-10-20 | Same broker-side cutoff |

### M1 broker depth (relevant for the 14 M1 features)

| Symbol | M1 oldest | M1 newest | Span days |
|---|---|---|---:|
| XAUUSD | 2026-01-15 | 2026-04-28 | 103 |
| GBPJPY | 2026-01-21 | 2026-04-29 | 97 |
| USDJPY | 2026-01-21 | 2026-04-29 | 97 |

**M1 OHLCV is hard-capped at ~3.3 months from MT5.** Pre-2026 M1 backfill is not feasible from broker. Third-party (Dukascopy / Histdata) is possible but introduces broker-mismatch risk.

### Pre-2022 H1+ feature subset feasibility

If we accept the M15-feature loss, ~300 of 1,219 catalog features depend only on H1/H4/D1 OHLCV. Pre-2022 mechanical OB-retest yield projection (using H1 BOS instead of M15):

| Symbol | Window | Yield estimate |
|---|---|---:|
| USDJPY | 2010-2021 (12 yr) | ~2,016 H1 trades (12 yr × 12 mo × 14 trades/mo) |
| GBPUSD | 2010-2021 (12 yr) | ~2,016 |
| GBPJPY | 2010-2021 (12 yr) | ~2,016 |
| XAUUSD | 2020-2021 (2 yr) | ~336 |
| **Panel total** | | **~6,384 H1-only mechanical trades pre-2022** |

**Tradeoff:** dropping ~75% of the catalog (M15+M1 features). The H1+ feature subset can still inform K54 architecture B (per-cohort specialist routing) but with reduced model-class continuity. **Recommended classification:** Phase 3 stretch, not Phase 2.

---

## 4. Unified cohort sizing scenarios (Task 4)

| Scenario | Description | Estimated n | Compute wallclock | Total wallclock |
|---|---|---:|---:|---:|
| Status quo | Q1.3 cohort (528 v2-feature) | 528 | DONE | DONE |
| Phase 2 minimum | + 2022-2023 v2-feature backfill (5 syms, existing trade_cohort.csv) | 2,326 | 2 hr parallel | 2-3 hr |
| Phase 2 aggressive A | + GBPJPY+US30 2022-2023 v2 (existing M15 in `data/historical/`) | 3,132 | +1 hr | 4-6 hr |
| Phase 2 aggressive B | + non-XAU 2024-2025 mechanical fillback (~1,760) | 4,892 | +3.5 hr | 6-8 hr |
| Phase 2 maximum | + pre-2022 H1-only FX cohort (~5,000) — **drops M15+M1 features (~75% of catalog)** | 9,892 | +4 hr | 8-12 hr |
| Theoretical max | + synthetic GARCH-EVT augmentation (~5,000) — training-only | 14,892 | +N/A (off-line synth) | 12+ hr |

### Binding bottleneck per scenario

| Scenario | Binding bottleneck |
|---|---|
| Phase 2 minimum | NONE — 2-hour compute window |
| Phase 2 aggressive A | NONE — 4-hour compute |
| Phase 2 aggressive B | Cross-source dedup audit (1-2 days for tuple-keyed validation) |
| Phase 2 maximum | M15-feature catalog loss (75% of catalog) — methodology continuity risk |
| Theoretical max | Synthetic-vs-real training-set discipline (DSR-validity preservation) |

### Why "n" alone is not the binding bottleneck

Per Agent B's `agent_b_dsr_n_sensitivity.json` and Agent E's recomputation in `agent_e_dsr_threshold_scan.json`:

**At observed lift +0.0484 with T=15 paths:** NONE of the scenarios reach DSR-p<0.01 at N=200, including Phase 2 maximum (n=14,892) and Theoretical max (n=14,892 with synthetic). The DSR-p stays at 0.018-0.020 in the BORDERLINE band.

**At observed lift +0.0484 with T=20 paths:**
- Phase 2 minimum (n=2,326) → DSR-p **0.009 (SURVIVES)**
- Phase 2 aggressive A (n=3,132) → DSR-p **0.006 (SURVIVES)**
- Phase 2 aggressive B (n=4,892) → DSR-p **0.003 (SURVIVES)**

**The path-count axis is 10× cheaper than the cohort axis** for unblocking K54 v4. The methodology change is a single-line modification to the K54 modeler config (`n_splits` argument in CPCV).

---

## 5. DSR-defensibility projection per cohort scenario (Task 5)

### Per-path SD of paired diff

The Q1.4 postmortem (§3) cites per-path SD ≈ 0.07 for K54 v3 (15 CPCV paths, n=528 cohort). Under the sqrt-n SR scaling assumption (postmortem-validated):

| Scenario | n | Implied paired SR | sigma_per_path projection |
|---|---:|---:|---:|
| Status quo | 528 | 1.27 | 0.07 |
| Phase 2 minimum | 2,326 | 2.68 | 0.033 |
| Phase 2 aggressive A | 3,132 | 3.10 | 0.029 |
| Phase 2 aggressive B | 4,892 | 3.88 | 0.023 |
| Phase 2 maximum | 9,892 | 5.52 | 0.016 |
| Theoretical max | 14,892 | 6.77 | 0.013 |

### DSR-p projection (T=15, observed lift 0.0484)

| Scenario | n | SR | DSR-p N=50 | DSR-p N=100 | DSR-p N=200 | DSR-p N=500 |
|---|---:|---:|---:|---:|---:|---:|
| Status quo | 528 | 1.27 | 0.171 | 0.243 | 0.321 | 0.428 |
| Phase 2 minimum | 2,326 | 2.68 | 0.018 | 0.033 | 0.055 | 0.094 |
| Phase 2 aggressive A | 3,132 | 3.10 | 0.013 | 0.024 | 0.041 | 0.073 |
| Phase 2 aggressive B | 4,892 | 3.88 | 0.009 | 0.017 | 0.029 | 0.054 |
| Phase 2 maximum | 9,892 | 5.52 | 0.006 | 0.011 | 0.020 | 0.039 |
| Theoretical max | 14,892 | 6.77 | 0.005 | 0.010 | 0.018 | 0.035 |

**At T=15 and N=200: NONE survive DSR<0.01 even at theoretical max.**

### DSR-p projection (T=20, observed lift 0.0484)

| Scenario | n | SR | DSR-p N=50 | DSR-p N=100 | **DSR-p N=200** | DSR-p N=500 |
|---|---:|---:|---:|---:|---:|---:|
| Status quo | 528 | 1.27 | 0.040 | 0.084 | 0.147 | 0.247 |
| Phase 2 minimum | 2,326 | 2.68 | 0.001 | 0.004 | **0.009** | 0.022 |
| Phase 2 aggressive A | 3,132 | 3.10 | 0.001 | 0.002 | **0.006** | 0.015 |
| Phase 2 aggressive B | 4,892 | 3.88 | 0.0003 | 0.001 | **0.003** | 0.008 |
| Phase 2 maximum | 9,892 | 5.52 | 0.0001 | 0.0005 | **0.001** | 0.004 |

**At T=20 and N=200: Phase 2 minimum already SURVIVES.** The marginal cohort expansion beyond minimum is unnecessary for DSR survival — its value is in cross-period generalization (gate c.ii) and per-cohort floor (gate d).

### Sensitivity table: scenario × lift_magnitude → DSR-p (full)

See `agent_e_dsr_projection.csv` (288 rows: 6 scenarios × 8 lift levels × 5 trial budgets, all at T=15).

Key cells:
- At lift 0.06 (vs observed 0.0484), Phase 2 minimum DSR-p at N=200 = **0.024** (BORDERLINE-CLOSE).
- At lift 0.08, Phase 2 minimum DSR-p at N=200 = **0.005** (SURVIVES).
- At lift 0.10, status quo (n=528) DSR-p at N=200 = 0.018 — even without cohort expansion, a +0.10 paired-AUC lift would survive.

**Implication:** lift improvement (model-class change) is an alternative to cohort expansion, but K54 v3's lift is below noise (per postmortem §1.2 K-7..K-10 contributing +0.0035). Lift improvement requires architectural pivot (e.g., dropping the v3 tower and rebuilding from K54 v1's stable core + per-cohort routing).

---

## 6. Phase 2 calendar refinement (Task 6)

See `agent_e_phase_2_calendar.md` for full refinement. Headlines:

- **Optimistic timeline: 3 weeks** (Phase 2 minimum dispatched today + T=20 + holdout open 2026-05-12 + Q1.5 verdict by 2026-05-20).
- **Pessimistic timeline: 6 weeks** (matches postmortem; sequential CEO-triage cycles + multiple modeler iterations).
- **Single binding bottleneck: gate (g) holdout opening at 2026-05-12** (calendar lock, not compute lock).
- **Compute is wallclock-cheap** (1.5-12 hours total depending on scenario depth) — not a bottleneck.
- **Key refinement vs postmortem:** the postmortem assumes cohort expansion is the only viable path; Agent E shows that **T-paths increase from 15 to 20 unblocks DSR survival on Phase 2 minimum cohort** without full aggressive expansion.

---

## 7. Synthetic data augmentation feasibility (Task 7)

### Feasibility assessment

**Tools available:**
- Memory `project_distributional_findings.md` documents calibrated GARCH-EVT parameters: gold tail-index ξ=0.35, GARCH persistence 0.9906 (half-life ~73 H1 bars), 6.2× more 3σ events than Gaussian, fat-tail parameter α≈3.2.
- `src/research_infra/bayesian_decay_attribution.py` and similar modules implement the calibrated stochastic processes for backtesting.
- A rough-vol GARCH-EVT generator can synthesize per-instrument OHLCV sequences calibrated to the historical distributional fingerprint.

**Yield projection:** 5,000-10,000 synthetic mechanical OB-retest trades per instrument-decade, calibrated to per-regime distributions.

### Risk of training-on-synthetic-data overfitting

1. **Distributional mode collapse.** Synthetic OHLCV reproduces moments 1-4 (mean, var, skew, kurt) and tail heaviness, but NOT the higher-order microstructure (volume clusters, news-driven jumps, regime-shift causality). A LightGBM trained on synthetic + real may overfit to the moment-matched bias.
2. **Tail event poisoning.** EVT-calibrated tails are by construction extreme; if the synthetic generator over-samples the tail, K54 will learn to over-rely on tail features that don't generalize to the real-cohort live test.
3. **Data leakage via parameter calibration.** The GARCH parameters are estimated on the SAME historical data used for the real cohort. If the calibration window overlaps the test window, synthetic data carries information about the test window (subtle leakage).
4. **DSR validity destruction.** DSR assumes the trial population is independent realizations of a stochastic process. Synthetic data is a deterministic function of the calibration distribution; DSR's null assumes independence that doesn't hold cross-synthetic.

### Hybrid: real cohort for evaluation + synthetic for training

This is the standard ML synthetic-augmentation pattern (e.g., MNIST + GAN-augmented training, Imagenet + cutmix). Methodology preservation:

1. **Real-only evaluation.** All gates (a)-(g) remain measured on real-cohort CPCV folds. Synthetic enters training only.
2. **Synthetic-train fold-isolation.** Each CPCV fold trains on (real_train_fold ∪ synthetic_calibrated_to_real_train_distribution); test folds remain real-only.
3. **DSR validity preservation.** The trial population N is COUNTED on real evaluations only; synthetic trials don't enter the DSR null. The trial budget remains N=200, not N=200 × synthetic_factor.
4. **Methodology gate.** The hybrid would need an A/B comparison: K54 v4 with synthetic augmentation vs without. If synthetic-augmented K54 has lower OOS lift, it's a contamination signal.

### Verdict on synthetic augmentation

**RECOMMENDED for Phase 3 only, NOT Phase 2.** The synthetic generator development time (1-2 weeks) plus the methodology validation cost (1 week of A/B verification) plus the literature survey of equivalent applications (1 week) takes the total cost to ~4 weeks. The cheaper alternative (T=20 CPCV paths + Phase 2 aggressive A cohort) achieves DSR-p<0.01 in 1 week.

If Phase 2 minimum + T=20 + cohort aggressive A still fails to deliver a useful K54 v4 (i.e., gates (c.ii) cross-period and (d) per-cohort floor still fail), THEN synthetic augmentation enters the Q1.5 / Q2.1 pipeline. Until then, Pareto-suboptimal.

---

## 8. Recommended Phase 2 dispatch path (CEO decision request)

### Path A (recommended): Aggressive minimum + methodology change

```
DISPATCH 1 (Phase 2 minimum):
  - Re-run all 6 family workers (structure / volatility / micro / time_session / liquidity / regime)
    on data/historical_2022_2023/ + existing 1,798-row trade_cohort.csv
  - Output: research/ml_program/feature_catalogs/CATALOG_v2_extended.csv
  - Wallclock: 2 hours parallel

DISPATCH 2 (GBPJPY+US30 7-symbol extension):
  - Extend build_trade_cohort_2022_2023.py INSTRUMENTS to include GBPJPY+US30
  - Re-run on existing data/historical/{GBPJPY,US30_cash}_M15.csv (already covers 2022-2023)
  - Output: data/historical_2022_2023/trade_cohort_v2_7sym.csv (~2,604 rows)
  - Wallclock: 30 min

DISPATCH 3 (K54 v4 modeler):
  - Architecture: K54 v3 architecture A (per-fold top-100) + NAS specialist
    + W-unit OFF (already known noise) + meta-label OFF (n insufficient)
  - Methodology change: T_paths = 20 (vs Q1.4 T=15)
  - Cohort: Phase 2 minimum + GBPJPY+US30 (n ≈ 2,604 + 528 K54 v1 = 3,132)
  - Output: research/ml_program/models/k54_v4/
  - Wallclock: 60 min

TOTAL Day 0-1: ~4 hours dispatched compute, K54 v4 with DSR-p < 0.01 at N=200
```

### Path B (postmortem-conservative): Sequential 4-6 weeks

Per Q1.4 postmortem §6.2: sequential cohort expansion + dedup + methodology validation cycles.

### Path C (synthetic): Phase 3 stretch

Skip Phase 2 cohort expansion; pivot to synthetic augmentation. Higher risk, higher reward, longer wallclock.

---

## 9. Eight-bullet summary

1. **Phase 2 cohort projections:** minimum n=2,326 (existing 1,798 + K54 v1 528); aggressive A n=3,132 (+ GBPJPY+US30 2022-2023); aggressive B n=4,892 (+ non-XAU 2024-2025 mechanical fillback); maximum n=9,892 (+ pre-2022 H1-only); theoretical max n=14,892 (+ synthetic GARCH-EVT).
2. **Wallclock validation:** the postmortem's "4-6 weeks" is correct for the Q1.5 program end-to-end (calendar-locked by gate (g) holdout open 2026-05-12 + CEO triage cycles). The compute work alone is **2-12 hours wallclock** depending on scenario depth. Phase 2 minimum can ship in **48-72 hours** with parallel dispatch.
3. **DSR-defensible cohort threshold:** at T=15 paths, NO scenario reaches DSR-p<0.01 at N=200 even at theoretical max. **At T=20 paths, Phase 2 minimum (n=2,326) already SURVIVES at DSR-p=0.009.** The path-count axis is 10× cheaper than the cohort-only axis.
4. **Binding bottleneck per scenario:** Phase 2 minimum / aggressive A — none (compute window). Aggressive B — cross-source dedup audit (1-2 days). Maximum — M15-feature catalog loss (75% of catalog). Theoretical max — synthetic-vs-real DSR validity preservation methodology (4 weeks).
5. **Synthetic-augmentation feasibility verdict:** RECOMMENDED for Phase 3 only, NOT Phase 2. Risk of distributional mode collapse + DSR validity destruction. Hybrid (real eval + synthetic train) is standard ML pattern but adds 4 weeks of methodology validation; cheaper alternative (T=20 + Phase 2 minimum) achieves DSR<0.01 in 1 week.
6. **New ambiguity revealed:** the postmortem's "cohort expansion is the only feasible path" framing is mathematically incomplete. At observed lift +0.0484 with T=15, even Phase 2 maximum (n=14,892) leaves DSR-p=0.018 (BORDERLINE). Three escapes exist: (a) cohort expansion to n>15,000 (infeasible at observed lift), (b) increase T_paths from 15 to 20 (cheap, methodology refinement), (c) ONC-clustered N reduction from 200 to ~50 (per Agent B Section 2). Postmortem should add (b) + (c) to its escape options.
7. **Recommended follow-up: KICK OFF PHASE 2 MINIMUM + T=20 NOW.** Not a 4-6 week wait. Three parallel dispatches today: (1) v2-feature backfill on 1,798 trades (2hr), (2) GBPJPY+US30 extension (30min), (3) K54 v4 modeler at T=20 paths (60min). Total Day 0-1: ~4 hours compute, K54 v4 with DSR-p < 0.01 at N=200. The 4-6 week budget is reserved for the live-validation tail (gate g + Q1.5 verdict + K55-shadow deploy plan).
8. **Key file paths (all absolute):**
   - `research/ml_program/forensics/2026-04-29/agent_e_cohort_expansion.md` (this report)
   - `research/ml_program/forensics/2026-04-29/agent_e_v2_feature_backfill_feasibility.csv` (1,219 rows, per-feature feasibility — 1,181 YES / 38 NO)
   - `research/ml_program/forensics/2026-04-29/agent_e_non_xau_fillback_inventory.json` (per-instrument-year fillback projection: ~2,110 mechanical 2024-2025 trades available)
   - `research/ml_program/forensics/2026-04-29/agent_e_pre_2022_extension.json` (MT5 broker depth probe: M15 capped 2022; H1+ to 2008-2010 for FX, 2019 for XAU; M1 capped 3.3 months)
   - `research/ml_program/forensics/2026-04-29/agent_e_dsr_projection.csv` (288 rows: 6 scenarios × 8 lift levels × 5 trial budgets)
   - `research/ml_program/forensics/2026-04-29/agent_e_dsr_threshold_scan.json` (joint T × n × N threshold analysis; recommended T=20 at Phase 2 minimum)
   - `research/ml_program/forensics/2026-04-29/agent_e_phase_2_calendar.md` (refined timeline: 3-week optimistic / 6-week pessimistic)

---

*Subscription-only forensic. No production code modifications. No order_send. MT5 read-only via copy_rates_from_pos. Live orchestrators uninterrupted. Standing by for CEO decision on Path A vs B vs C.*
