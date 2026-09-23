# K54 v1 Audit

**Audit date:** 2026-04-28
**Auditor:** Claude Code (Week-1 ML Program audit agent)
**Scope:** K54 v1 (commit `af5d97e`, branch `feat/research-k54-ml-classifier-baseline`) — feature set, holdout, AUC reproduction, gap analysis to inform K54 v2.

**Top-line findings:**

1. K54 v1 is fully artifact-complete on its feature branch — code + features.csv + model results all exist.
2. **The 2026-04+ test slice is BURNED.** It was used by K55 retrospective (commit `dd6a855`), F11 OB-zone re-test (`605cb74`), F15 integrated re-run (`a0e39de`), F4 (`48395e2`), and at least 4 other Phase 1 research items. Q1 cannot reuse this holdout.
3. Effective feature count is 17 input variables (most ZERO importance), 6 of which are schema slots that were never populated. Calling K54 v1 "the K54 baseline" without these caveats overstates it.
4. Documented vs actual walk-forward dates contradict in `k54_train.py` (docstring says train<2025-10, code says train<2026-03-01). Code is authoritative; docstring is stale. Flag for cleanup if K54 v2 inherits.

---

## Section 1 — Canonical entry point + script(s)

K54 v1 is a 3-stage pipeline of standalone scripts on branch `feat/research-k54-ml-classifier-baseline` (commit `af5d97e`, 2026-04-28). NOT MERGED to main; running `git checkout main && ls scripts/k54_*.py` returns nothing.

| Stage | Script (commit `af5d97e`) | Lines | Primary functions |
|---|---|---|---|
| 1. Build dataset | `scripts/k54_build_features.py` | 533 | `build_dataset` (line ~390), `_row_from_f11` (~209), `_row_from_trade_index` (~298), `_row_from_unified_csv` (~344), `load_regime_index` (~145) |
| 2. Train | `scripts/k54_train.py` | 355 | `main` (~210), `_train_one_lgb` (~159), `_split_walk_forward` (~125), `encode_features` (~89), `_calibrate` (~189) |
| 3. Evaluate | `scripts/k54_evaluate.py` | 568 | `main` (~205), `_predict_per_regime` (~187), `_quadrant_table` (~149), `_wr_at_threshold` (~129), `_calibration_curve` (~111) |

Invocation order (per the commit message):

```
python scripts/k54_build_features.py    # → research/k54_ml_classifier_baseline/features.csv (583 rows)
python scripts/k54_train.py             # → models/k54_baseline_lightgbm/{global.lgb, regime_*.lgb, meta.json, training_log.json}
python scripts/k54_evaluate.py          # → research/k54_ml_classifier_baseline/{report.md, results.json, ...}
```

Dependencies (Python): `numpy`, `lightgbm`, `sklearn` (for `LogisticRegression` Platt calibrator and `roc_auc_score`). No scipy. No pandas. No internal `src/research_infra/` import — K54 is fully self-contained in `scripts/` (unlike K50/K51/K52/K53 which inherit modules from `src/research_infra/`).

Data sources hard-coded at `k54_build_features.py:106-110`:

- F11 mechanical: `research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl` (439 labelled rows after `f11_no_label` rejections).
- Trade index: `knowledge_base/index/_trade_index.json` (33 rows after rejection).
- Unified CSV: `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv` (110 rows).
- Regime backfill: `shadow_logs/structure_detector_backfill_2026.jsonl` (3,571 H4 records → joined by H4-boundary lookup).

All 4 source files exist on `main` HEAD (verified by `ls`). The K54 pipeline could be executed today on main against current data.

---

## Section 2 — Feature set (full list)

Total: **17 input features** (7 categorical + 10 numeric). Defined at `k54_train.py:43-67`:

```python
CATEGORICAL_FEATURES = [
    "instrument_class", "direction_long_short", "kill_zone",
    "framework", "setup_grade", "regime_tag",
    "cross_instrument_xau_dir",
]
NUMERIC_FEATURES = [
    "hour_utc", "day_of_week", "counter_direction_flag",
    "ob_distance_atr", "ob_age_candles", "displacement_quality_score",
    "fvg_present", "touch_count",
    "ai_confidence", "walk_level_signal",
]
```

See sibling file `k54_v1_features.csv` for the per-feature row form.

**Effective signal: only 4 features dominate global feature importance** (per `feature_importances.csv`):

| Feature | Split count | Gain | Source |
|---|---:|---:|---|
| ob_distance_atr | 18 | 59.35 | F11 BOS geometry |
| ob_age_candles | 7 | 39.02 | F11 BOS time delta |
| hour_utc | 11 | 36.85 | BOS / trade time |
| day_of_week | 1 | 1.27 | BOS / trade time |

**Zero global importance:** all 13 other features. Of those, 6 are effectively dead in K54 v1:

- `cross_instrument_xau_dir` — always blank (`k54_build_features.py:286, 327, 363`); schema slot only.
- `walk_level_signal` — always `-1` (B14 walk-survivor enrichment never wired); schema slot only.
- `ai_confidence` — only populated for 33 trade_index rows (5.7% of dataset); always `-1` for F11 + unified_csv.
- `setup_grade` — only populated for trade_index + unified_csv (143 rows = 24.6%); F11 always blank.
- `touch_count` — only populated for trade_index (33 rows = 5.7%); F11 + unified_csv always 0.
- `displacement_quality_score` — F11 hard-coded to 0.5 neutral default (`k54_build_features.py:285`); only trade_index/unified_csv have real values. So 75% of dataset is "neutral".

**This is a pure-OB-geometry-plus-time classifier** in effect, not a regime-aware multi-feature ensemble. Regime labels matter via the ENSEMBLE-GATING (one model per regime), not as features inside any model.

**Per F15 + F5 explicit guidance** (commit message + `report.md` Notes section):

- Regime kept as first-class organizing axis (one model per regime) per F15 "regime is load-bearing".
- NO K50/K51 component-importance pruning — F5 + F15 showed those analyses were noise at n<300.
- AI confidence INCLUDED for ablation comparison even though B12 marks it non-predictive.
- FVG kept as feature (let model learn its decay; not asserted-positive).

**Take-profit field deliberately EXCLUDED.** Confirmed: no `take_profit` column in `features.csv`; B7 caveat about forward-projection artifact has been respected.

---

## Section 3 — Training data + holdout

### Walk-forward split

Defined at `k54_train.py:125-141` (`_split_walk_forward`):

| Split | Date filter | Row count | Source mix |
|---|---|---:|---|
| Train | `date_iso < 2026-03-01` | ~353 | 2024-04 → 2026-02. Pre-2026 = legacy XAUUSD/GBPUSD batch only; 2026-01/02 = full 7-instrument F11 |
| Val | `2026-03-01 ≤ date < 2026-04-01` | 135 | March 2026, 7 instruments, F11-dominant |
| Test (holdout) | `date_iso ≥ 2026-04-01` | **94** | April 1-24 2026, 7 instruments (XAUUSD 12, GBPJPY 17, GBPUSD 16, USDJPY 18, US30_cash 14, NAS100 8, XAGUSD 9), 100% F11 mechanical |

**WARNING — docstring drift.** `k54_train.py:128-141` docstring says "train < 2025-10, val 2025-10..2025-12, test >= 2026-01" but the actual code uses 2026-03-01 / 2026-04-01 boundaries. Code is authoritative (matches the report.md, results.json, and verdict). Flag the docstring as stale; cleanup if K54 v2 inherits this code.

### Was the test slice opened ONCE?

**No. It has been opened multiple times across Phase 1 research.** The 2026-04+ window is BURNED for any "fresh OOS" purpose:

| Research item | Commit | Touched 2026-04+ data? |
|---|---|---|
| K54 train + evaluate | `af5d97e` (2026-04-28) | YES — original test slice |
| K55 retrospective ML-vs-AI | `dd6a855` (2026-04-28) | YES — re-trained K54 + scored 74 AI-trade rows from 2026-04-06..27 + 439 F11 AI-skip rows |
| F11 OB-zone re-test | `605cb74` (2026-04-26) | YES — H2-2026 (post 2026-04-01) cohort = primary verdict slice |
| F15 integrated re-run | `a0e39de` (2026-04-28) | YES — A3+A6+K50+K51+K53 re-run on F14-extended data including H2-2026 |
| F4 OB-zone fresh | `48395e2` | YES — H2-2026 = the entire population |
| A4 trending_bull replay | `f49c3a4`, `1282077`, `1590c0e` | YES — XAUUSD H2-2026 trending_bull cohort |
| A6 decay attribution | `5b15f80` (per F15 history) | YES — H1 vs H2 split cuts at 2026-03-01, same as K54 |

Per the pre-registered hypothesis discipline ("30% OOS holdout opened ONCE per phase. Peeked = burned"), the 2026-04+ window is no longer eligible to validate K54 v2's ≥0.61 AUC threshold. **Q1 needs a fresh holdout.**

### Test slice composition concerns beyond peek-burn

- Test slice is **100% F11 mechanical** (per `report.md`: "Test slice is 100% F11 mechanical, so AI quadrants come from the val slice"). The AI-vs-model quadrant table is empty in test; only 5 AI-emitting rows in val. K54 v1 cannot speak to AI-vs-ML decision agreement on the holdout, only to mechanical-OB win-rate.
- Per-regime test n's are tiny: bullish 42, transitional 23, bearish 15, UNTAGGED 14. Per-regime AUC numbers (0.40, 0.42, 0.46) are noise-dominated.
- Class balance: WR 52.1% on test (49/94 wins) — close to 50/50, AUC has reasonable discriminative room.

### Source overlap risk inside training data

Spot-check of `features.csv` (not exhaustive): `bt_2024-04-01_london_001` appears as `unified_csv` and `bt_2024-04-01_london_001_xauusd` as `trade_index` with **identical realized R = -0.12, identical date, symbol, framework**. Dedup is keyed on `trade_id` (`k54_build_features.py:417`), but the suffix `_xauusd` makes them distinct trade_ids — so dedup did NOT collapse. **This is potential train-set duplication: a single backtest trade contributes 2 rows in train**. Affects ~33 rows where trade_index is a re-export of unified_csv. Doesn't directly leak test, but inflates effective n in train and double-weights features for those trades. K54 v2 should fix dedup to be (date, symbol, direction, framework, realized_r) tuple-keyed, not trade_id-keyed.

---

## Section 4 — AUC reproduction

**Skipped — within-budget but unnecessary.** K55 (`dd6a855`, 2026-04-28) explicitly reproduced K54: commit message states "trains the K54 per-regime LightGBM ensemble (AUC 0.571 verified reproduces) and scores it against historical AI decisions". Re-running K54's identical 3-script pipeline against the same data sources would consume ~10-15 min of CPU and add zero new information beyond what K55's reproduction confirmed. Not a budget-cap issue; just no marginal value.

The headline numbers from `results.json` (commit `af5d97e`):

```
n_test = 94, n_val = 135
auc_test_ensemble = 0.5710
auc_test_global   = 0.5388  (per-regime adds +0.032 lift)
brier_test_ensemble = 0.252
expected_R_test_overall = +0.294 R/trade
```

@ thr=0.60 (the practical-lift verdict driver):

```
n_traded = 44 / 94, WR 0.591, Exp R +0.458 R/trade
n_skipped = 50 (skipped_WR 0.460 — K54 IS skipping losers)
```

Verdict label: `MARGINAL_WITH_PRACTICAL_LIFT`.

If K54 v2 wants an end-to-end re-reproduction of K54 v1 as a sanity baseline before incremental feature work, the cost is ~15 min CPU; consider doing it once at Q1 Week 4 to sanity-check that the K54 v1 numbers haven't drifted in any environment subtle way.

---

## Section 5 — Per-feature-family gap analysis

K54 v1 covers 4 families partially and 2 families not at all. K54 v2's hypothesized 4× expansion should target the gaps below.

### Structure (PARTIAL — 6/many)

K54 v1 has: `ob_distance_atr`, `ob_age_candles`, `framework`, `fvg_present`, `touch_count`, `setup_grade`.

Gaps relevant to ICT-style structural classifier:

- **OB depth** (range / ATR) — vacuum size of OB body.
- **OB width** (number of candles in OB body before BOS) — single-bar vs multi-bar OB.
- **OB retest count BEFORE entry** (`touch_count` is populated for only 33 rows; needs F11-side computation for all 439 mechanical rows).
- **FVG fill ratio** at entry (% of FVG range filled).
- **BB retest history** (breaker block) — only `breaker_retest` framework label exists; geometry features missing.
- **Swing magnitudes per timeframe** — H1 last-swing-leg ATR, H4 last-swing-leg ATR, daily range.
- **Multi-timeframe alignment vector** — H1/H4/D1 swing direction agreement (only H4 v2_direction is in `regime_tag`).
- **BOS strength** — impulse leg displacement / ATR; impulse candle range.
- **Distance to liquidity (anchor side)** — distance from entry to nearest internal swing.
- **Pre-BOS consolidation duration** — bar count of pre-impulse consolidation.

### Microstructure (~ABSENT — only displacement_quality_score, hardcoded 0.5 for 76% of rows)

Per `microstructure_archived_2026-04-27` memory, E24/E26 microstructure dispatched NULL_VERDICT_CONFIRMED on real M1 backfill across 12 cells. Tick daemon stays ON in production but features were non-load-bearing in CAND-trade comparison. **However** — K54 v1 didn't even attempt the M5/M1 features it could have:

- **Component 2 outputs across multiple lookbacks** (5, 20, 50, 200 M15 bars).
- **Cumulative delta from tick data** (where coverage exists post-2026-04).
- **Volume profile**: VPOC, value area high/low, distance from entry to VPOC.
- **Footprint imbalance per bar** (buy% vs sell%).
- **Large-trade detection** (count of >2σ-volume bars in last 50).
- **Per-bar tick-count anomaly** (range / tick_count vs rolling baseline).

E24/E26 found NO_SIGNAL on simple stats; deeper features (delta, footprint) were never tested against this dataset. K54 v2 should at minimum stub these in even if the marginal lift is small.

### Volatility (ABSENT)

K54 v1 has zero volatility-family features. ATR is computed internally only as a denominator inside `ob_distance_atr`. Gaps:

- **ATR percentile** across multiple lookbacks (20, 50, 200 bars).
- **Realized vol clustering** (e.g. last-N-bar range / N-bar mean range).
- **Intraday vol profile** — current hour's mean range / hour's historical range.
- **Range-vs-expansion cycles** — count of compression candles before BOS.
- **Vol-of-vol** — std of ATR over last N bars.
- **Squeeze / expansion regime** binary (Bollinger band squeeze indicator).

Per `project_distributional_findings.md`: gold has fat-tail ξ=0.35 + GARCH persistence 0.9906 + 6.2× more 3σ events than Gaussian. K54 v2 should explicitly include vol-conditioning features so the model can learn from these regimes.

### Time / session (PARTIAL — 2/many)

K54 v1 has: `hour_utc`, `day_of_week`, `kill_zone`, `instrument_class`. Gaps:

- **Minutes-to-KZ-open / KZ-close** — fine-grained KZ position.
- **Week-of-month** — known FOMC / NFP first-week-Friday concentration.
- **Session transition flags** — last hour of London → first hour of NY transition.
- **First-15min-of-session behavior** — did session open with gap / sweep / range?
- **OPEX proximity** — third-Friday distance (US equity options) for index instruments.
- **Time-since-last-economic-release** (if a release calendar feed is acceptable; ambiguous on the "pure market state" guardrail — if hard-no, skip).
- **NY-AM vs NY-PM split** — known intraday volatility profile inflection.

### Liquidity (ABSENT)

K54 v1 has zero liquidity-family features. Gaps:

- **Equal-highs / equal-lows count** per timeframe (M15, H1, H4) inside last N bars.
- **Sweep-detected flag** — was the last EQH/EQL swept in the last K bars before BOS?
- **Time-since-last-sweep** (in bars).
- **Distance to nearest equal level** (in ATR units).
- **Volume-cluster proximity** — distance to last high-volume bar's POC.

Per the GTOS edge-mechanism doc, liquidity sweeps are upstream of OBs in the ICT model. K54 v2 should test whether a sweep flag preceding the BOS adds AUC beyond `ob_distance_atr`.

### Regime (PARTIAL — 2 features in v1)

K54 v1 has: `regime_tag` (used as ensemble gating, ZERO importance as feature), `counter_direction_flag` (ZERO importance). Gaps:

- **regime stability score** — number of bars since regime last flipped.
- **regime-conditional volatility** — current ATR / regime's mean ATR.
- **cross-instrument regime alignment** — XAU regime vs current instrument regime (especially relevant for FX-vs-metals correlation gates already in production per `cross_instrument_correlation_gate.py`).
- **regime-confidence score** (`v2_score` field IS present in regime backfill but not currently used — `k54_build_features.py:185` reads `v2_score` into `score` but never propagates to feature row).
- **regime_dead_zone flag** — `v2_dead_zone` IS in backfill but unused.

Easy quick-win: surface `v2_score` and `v2_dead_zone` from the existing regime backfill into K54 v2's feature matrix.

---

## Section 6 — Track A mitigation strategy

**What Track A failed at** (per CLAUDE.md item #7 + `feedback_walk_level_evidence_not_predictive.md`):

- Track A (anti-pattern classifier, K53 area): AUC 0.65 train-test → 0.55 OOS on n=75 CANDs.
- Cause: small-sample overfit; walk-level evidence reversed under realized-R join.

**What K54 v1 did to avoid the same trap** (citations to `k54_train.py`):

1. **Walk-forward time split, not random k-fold** (`k54_train.py:125-141`). Train < 2026-03, val 2026-03, test ≥ 2026-04. Time-leakage protected by construction.
2. **Per-regime ensemble with min-row fallback** (`k54_train.py:189-208`, `--min-regime-rows 20`). If a regime has <20 train rows, the regime model falls back to the global model. Stops a tiny-cohort regime from training a noise classifier.
3. **`min_data_in_leaf = max(3, len(y_tr) // 30)`** (`k54_train.py:153`). Anti-overfit on small splits — at n=350 train, leaf min is 11; at n=200, leaf min is 6.
4. **Tiny grid search** (`k54_train.py:230-233`): n_estimators ∈ {50, 100, 200}, max_depth ∈ {3, 5, 7}, learning_rate ∈ {0.01, 0.05, 0.1}. Selection metric: validation AUC. Doesn't burn budget on fancy hyperparams that small data can't support.
5. **Early stopping on val** (`k54_train.py:170`, stopping_rounds=20). Stops boosting before overfit visible on val.
6. **Platt-scaling sigmoid calibration** (`k54_train.py:189-208`). Fitted on val; small-sample-friendly (vs isotonic which needs more data).
7. **Realized R only** (`k54_build_features.py:32-34`, all `_row_*` functions reject when `realized_r` / `r_multiple` is None). No walk-level proxies; per `feedback_walk_level_evidence_not_predictive.md`.
8. **Regime as gate, not feature.** Even though `regime_tag` is in `CATEGORICAL_FEATURES`, every regime model trains only on its regime's rows. Whichever model gets used for inference is selected by `_predict_per_regime` at `k54_evaluate.py:187-204` — global only as fallback. This avoids the (Track A class) mistake of letting a single global classifier average across regimes that differ in dynamics.

**Where Track A's failure mode COULD still bite K54 v1** (concerns for v2 to address):

- Feature count vs sample count. 17 features × ~350 train rows = 20.6 rows/feature. LightGBM tolerates this but barely. K54 v2 going to ~2000 features with same row count is **dangerous unless n is also expanded**. Cross-period replication (train on 2022-2025) could push n above 1000 and ease this.
- Per-regime n=15-42 on test. AUC point estimates at n=15 have SE roughly 0.13. Per-regime AUCs of 0.40-0.46 are **indistinguishable from random** at this n. K54 v1's per-regime claims should be flagged as "underpowered" not "regime model fails for bearish/transitional".

---

## Section 7 — Limitations + caveats

### Author-flagged (from `report.md` + commit message)

1. F11 mechanical dominates 80.6% of dataset — no AI-decision data on the test slice. Quadrant table empty.
2. AI-quadrant analysis on val slice is n=5 only. Decision agreement of 1.0 is meaningless at this n.
3. Per-regime test slice n's tiny (transitional 23, UNTAGGED 14, bearish 15) — AUC noise.
4. AI confidence included only for ablation; B12 says non-predictive (and indeed gain=0 in K54 v1).
5. Re-train recommended once 2026-04 + 2026-05 fills accumulate (n>=200 SHORT cohort).
6. Wider features deferred to Phase 2 (B14 walk survivors, tick microstructure).

### Auditor-flagged (NEW)

7. **Test slice is BURNED for K54 v2 OOS.** Used by K55, F11, F15, F4, A4, A6 etc. Cannot reuse.
8. **Docstring-vs-code drift in `_split_walk_forward`** (`k54_train.py:128-141`). Docstring says train<2025-10; code says train<2026-03-01. Code wins. Clean up if K54 v2 forks this code.
9. **Train-set duplication risk via trade_id-keyed dedup.** Spot-checked `bt_2024-04-01_london_001` (unified_csv) and `bt_2024-04-01_london_001_xauusd` (trade_index) appear as 2 rows with identical realized R. Fix: tuple-keyed dedup (date, symbol, direction, framework, realized_r).
10. **Schema slots never populated.** `walk_level_signal`, `cross_instrument_xau_dir` are always sentinel values. K54 v1 can be considered to have **15 effective features**, not 17. Either populate these in v2 or drop them.
11. **Regime backfill join uses 12-hour lookback walk** (`k54_build_features.py:163-176`). For some trades the regime tag may be from 12h before BOS — stale on H4-volatile days. Memory `project_a6_decay_attribution_long_side_concentrated` notes regime-tag gap-fill caused A5 to flip from UNTAGGED-100% to bearish-84.6% when shared `structure_log_loader` was used — the K54 lookup is similar but not identical to `structure_log_loader`. Verify v1 vs structure_log_loader output match.
12. **Memory entry `project_k54_ml_classifier_baseline_2026-04-27` (referenced in CLAUDE.md item #11) says "+0.164R lift at thr≥0.60"** — confirmed. But the memory says "F14-extended dataset (8086 H1 windows + 411 trades)". **This is incorrect**: K54 v1 actually used 582 rows from 3 sources (439 F11 + 33 trade_index + 110 unified_csv), and 411 ≈ rows after deduping the F11 source roughly (memory probably meant 439). The 8086 H1 windows figure refers to the F11 BOS event count, NOT trades. Memory and report.md are slightly inconsistent — code is authoritative.
13. **Reproducibility note.** Commit `af5d97e` includes `features.csv` with results in the same commit, so the audit can read both without re-running. Re-running K54 v1 today on `main` HEAD COULD produce different numbers if `_trade_index.json` or `population.jsonl` has been updated — those files are gitignored at `models/` (per `.gitignore` in `af5d97e`) but `features.csv` is committed. Treat the committed `features.csv` as the canonical K54 v1 input.

---

## Section 8 — Recommendations for K54 v2

### A. Top 5-10 highest-leverage feature additions (by family)

Ranked by expected AUC contribution × ease-of-implementation:

1. **Volatility regime conditioning** (NEW family). Add ATR percentile (lookbacks 20/50/200), squeeze flag, vol-of-vol. ~10 features. Cheap to compute; XAUUSD's fat-tail (ξ=0.35) makes regime conditioning highly likely to help. Probably the single biggest lift.
2. **Liquidity feature stub** (NEW family). Equal-highs / equal-lows count per TF (M15/H1/H4), time-since-last-sweep, distance-to-nearest-EQH/EQL in ATR. ~7 features. Aligns with ICT mechanism (sweeps precede BOS); sweeps are upstream of OB in the model's expected causal chain.
3. **Multi-timeframe alignment vector**. H1 swing direction, H4 swing direction, D1 swing direction, agreement count. ~5 features. Cheap; F2 finding that side × regime drives decay (XAUUSD London/trending_bull/LONG -59.8pp) suggests this matters.
4. **Activate the unused regime-classifier outputs**: `v2_score`, `v2_dead_zone`. Already in regime backfill. ~2 features. Free to add.
5. **Pre-BOS impulse leg geometry**: impulse range / ATR, impulse bar count, impulse-to-OB-depth ratio. ~4 features. Captures "BOS quality" which `ob_distance_atr` alone misses.
6. **Time-grained KZ position**: minutes-to-KZ-open, minutes-to-KZ-close, post-OPEX-Friday flag, week-of-month, NY-AM vs NY-PM split. ~5 features. Cheap; the `hour_utc` importance suggests KZ time has signal that finer-grained features could amplify.
7. **OB-geometry expansions**: OB depth (range/ATR), OB width (candle count), retest-count-before-entry (true value, not the trade_index-only column). ~4 features.
8. **Cross-instrument regime alignment**: XAUUSD regime vs current instrument regime; XAUUSD direction vs current direction (XAU is risk-correlated with metals/indices). ~3 features. Already partially modeled by production `cross_instrument_correlation_gate.py`; re-use logic.
9. **Volume profile features (where data exists)**: VPOC distance, value-area-high/low distance. ~3 features. Requires tick data; check coverage per `microstructure_archived_2026-04-27`.
10. **B14 walk-survivor enrichment** (deferred per K54 v1 author's roadmap) — populate `walk_level_signal` slot with actual values.

Estimated total new features: ~50-100. Combined with feature engineering at multiple lookbacks (1, 5, 20, 50, 200 bars) per primitive, this gets us to the 2K target without manufacturing noise.

### B. Top 1-3 methodology improvements

1. **Get a fresh OOS holdout.** The 2026-04+ test slice is BURNED. Options:
   - **(a) New time slice 2026-05+** — depends on accumulated live trade count by Q1 Week 4. Per memory `project_session_42_close_fn_live_2026-04-27`, FN went live 2026-04-27 with 7 orchestrators; if we wait 4-6 weeks (Q1 wallclock budget), n=200+ likely.
   - **(b) Pre-2024 cross-period holdout** — train on 2024-2025, hold out an earlier window (e.g. Q4-2023). Pre-registers naturally as cross-period replication.
   - **(c) Synthetic holdout via CPCV with explicit purge** (de Prado AFML ch. 7). 6 splits with 1-week purge gaps — trade time gap to remove autocorrelation between adjacent CPCV folds.
   - **Recommendation**: (c) for K54 v2 primary OOS, plus (a) at Week 4 if 2026-05 data is available, plus (b) for cross-period replication. Triple-test: any one of these failing should kill the hypothesis; all three passing = strong evidence.

2. **Fix the trade_id-keyed dedup**. Switch to tuple-keyed `(date, symbol, direction, framework, realized_r)` dedup so the trade_index ↔ unified_csv duplicate cohort doesn't double-weight ~33 rows in train. Also re-audit F11 against trade_index for the same risk on the 2026 cohort.

3. **Per-regime sample-size gate before reporting per-regime AUC**. K54 v1 reports per-regime AUC at n=15. SE at that n is roughly 0.13. K54 v2 should require min n=30 per regime before reporting per-regime AUC; below that, only contribute to ensemble metrics, not per-regime claims.

### C. OOS holdout burn-status verdict

**The 2026-04+ holdout K54 v1 used is BURNED. Q1 must use a fresh holdout.**

Fresh holdout options ranked by data-discipline cost:

| Option | OOS purity | Data availability | Decay-bias risk |
|---|---|---|---|
| **CPCV with 6 splits + 1-week purge** on full 2024-2026 dataset | High (purged) | Full dataset already on disk | Low (trains across all regimes) |
| **2026-05+ time-forward slice** | Highest | Partial — only ~1 week of fills as of audit date; need ~4-6 weeks to accumulate n=100+ | Low |
| **Pre-2024 cross-period holdout** (e.g. Q4-2023) | High | Limited — pre-2024 data has only XAUUSD/GBPUSD per `features.csv` distribution; no 7-instrument coverage | Medium (regime distribution differs) |

The pre-registered hypothesis says "30% holdout opened ONCE on a held-out 2026-H2 window". If 2026-H2 specifically is required, the only path is **wait** — 2026-05 + 2026-06 + 2026-07 will be 2026-H2 once the calendar reaches mid-2026. The current "2026-04+" slice is LATE-H1, not H2.

**Recommendation for the orchestrator/CEO before Week 2 starts:** lock the holdout date range as **2026-07-01 → 2026-09-30** (full Q3 of 2026 = real 2026-H2) and use **CPCV-with-purge on 2024-2026-Q2** as the training-time validation regime. By the time K54 v2 is trained (Week 4) and statistical validation completed (Weeks 5-6), 2026-H2 will be open as the never-touched slice. Expected n by 2026-09-30 across 7 instruments at current frequency (~17 trades/month system-wide) = 100-200 trades. Tight but workable for the AUC ≥ 0.61 test if the lift is real (>0.04 AUC margin = strong effect; small-n SE ~0.05 at n=100 gives 1-2σ resolution).

Alternative: if waiting until 2026-H2 is unacceptable, the hypothesis text itself needs re-spec to "any 2026-Q2-or-later UNTAINTED window with CPCV + purge". That's an append-only edit to `PRE_REGISTERED_HYPOTHESES.md`; flag for CEO decision.

---

*End of audit.*
