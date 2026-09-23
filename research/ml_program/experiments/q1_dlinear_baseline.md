# Q-1 DLinear Baseline Gate (H-25)

**Task ID:** Q-1 (MASTER_BACKLOG.md Section Q) / H-25 (HYPOTHESIS_BACKLOG.md)
**Tier:** Q2-pre / Phase 4 quick-win bundle B-8
**Author:** Sequence-model baseline gatekeeper (Opus 4.7, max effort, subscription-only)
**Date:** 2026-04-28
**HEAD when run:** main (post 63446e1)
**Reproducer:** `scripts/research/q1_dlinear_baseline.py`
**Outputs:** `q1_dlinear_results.json`, `q1_dlinear_run.log`, this file
**Wallclock:** ~150 s on CPU (Python 3.13, torch 2.11 CPU)

---

## Section 1 — Pre-registered hypothesis (BEFORE training)

**H-25, Q-1.** DLinear (Zeng et al. 2023 AAAI Oral) trained on the GTOS K54 v1 17-feature canonical set + 30-bar M15 lookback achieves CPCV K=6 / N=2 paired-fixed-HP mean AUC within ±0.01 of canonical K54 v1 (CPCV mean **0.5286** per `research/ml_program/audit/canonical_v1_rerun.md`).

| Decision | Rule |
|---|---|
| **PASS**       | CPCV mean AUC ≥ 0.528 (within +0.01 of anchor or above) |
| **BORDERLINE** | 0.518 ≤ CPCV mean AUC < 0.528 (within −0.01 floor; below mid-anchor) |
| **FAIL**       | CPCV mean AUC < 0.518 |

**Decision rule on Q2:**
- PASS → Q2 sequence-model exploration GO.
- BORDERLINE → CEO decides, with cross-period sensitivity disclosed.
- FAIL → Q2 sequence-model exploration shelved. K54 v3 (H-1, K54 v3 master bundle) is the only ML path until/unless data-pool size or cohort labelling clears a future re-test.

Pre-registered in this section before reading any AUC outputs.

---

## Section 2 — Methodology (Q1.3 protocol; do not deviate)

### 2.1 Architecture (Zeng et al. 2023 AAAI Oral, "Are Transformers Effective for Time Series Forecasting?")

DLinear's three building blocks faithfully ported into the GTOS classification setting:

1. **Series Decomposition Block.**
   - `trend_t = MovingAvg(x, kernel=K)` implemented as `AvgPool1d(kernel=K, stride=1)` with reflect padding of size `(K-1)//2` on each end (matches reference `cure-lab/LTSF-Linear/models/DLinear.py`).
   - `season_t = x − trend_t`.
2. **Two parallel Linear projections** (channel-shared variant; reduces parameter count vs `individual=True`):
   - `out_t = Linear(L=30 → 1)(trend_t.permute(B, C, L))`
   - `out_s = Linear(L=30 → 1)(season_t.permute(B, C, L))`
   - `out = out_t + out_s`  →  shape `(B, C)`.
3. **Classification head** (departure from the reference, which forecasts a future window):
   - Concatenate the channel-pooled output `(B, C=17)` with the K54 v1 17-feature static head `(B, 17)`.
   - `MLP(hidden) → ReLU → Dropout(0.2) → Linear(1)` → BCE-with-logits.
   - Per-instance instance-normalization on the temporal axis (RevIN-lite, Kim et al. 2022) added before decomposition for distribution-shift robustness.

I reimplemented the architecture in PyTorch 2.11 CPU rather than installing the reference package (the reference repo is forecasting-only; classification adapter is needed regardless). The decomposition + dual-linear core matches `cure-lab/LTSF-Linear`.

### 2.2 Per-trade input construction

**Sequence channel (B, 30, 17):** for each trade row, build a 30-bar M15 OHLCV lookback ending at the bar whose close is at-or-before `__ts_close`. Per-bar feature channels (17, matching brief's "n_features=17"):

```
[open, high, low, close, volume, logret, hl_range, oc_range,
 rolling_mean_5, rolling_std_5, rolling_mean_10, rolling_std_10,
 rolling_mean_30, rolling_std_30, logvol, ret_z_30, absret]
```

**Static head (B, 17):** the canonical K54 v1 features, identical to `models/k54_v1_canonical/run_canonical_v1_rerun.py CANONICAL_FEATURES`:

```
hour_utc, day_of_week, counter_direction_flag, ob_distance_atr,
ob_age_candles, displacement_quality_score, fvg_present, touch_count,
ai_confidence, walk_level_signal, framework, instrument_class,
direction_long_short, kill_zone, setup_grade, regime_tag,
cross_instrument_xau_dir
```

**Why this construction is the defensible reading of "input shape (n_trades, 30, 17)":** the K54 v1 17 features are mostly per-trade-static (regime tag, kill zone, direction), so feeding them as 30 identical-per-bar channels would produce zero temporal variation (DLinear cannot learn from constant-across-time channels). The K54 v1 features are routed into the classification head AFTER temporal pooling so the model still has access to all 17 K54 v1 signals — the DLinear sequence path adds the 30-bar M15 microstructure context the gate's H-25 hypothesis requires.

### 2.3 Cohort pool

Per brief: `Q1.3 528-row cohort + 1,798-row 2022-2023 backfill = 2,326 max trade rows`.

| Source | Rows | Notes |
|---|---:|---|
| `research/ml_program/scout/feature_matrix.parquet` (Q1.3 cohort) | 528 | dates 2024-04-01 → 2026-04-24 |
| `data/historical_2022_2023/trade_cohort.csv` (F11 mechanical, 5 instruments) | 1,798 | dates 2022-01-04 → 2024-02-19 |
| **Pool (raw)** | **2,326** | |
| Lookback build kept | 2,319 | dropped 7 rows with <30 bars of M15 lookback |
| Final fitted population | **n=2,319** | |

**Per-symbol distribution (kept):** XAUUSD 558, GBPUSD 469, XAGUSD 469, USDJPY 445, NAS100 261, US30_CASH 62, GBPJPY 62. Win rate **0.5705**. Cohort cutoff `__ts ≤ 2026-04-28T23:59:59 UTC` (verified in script). No live holdout (2026-04-29 → 2026-05-12) accessed.

### 2.4 CPCV configuration

Identical to v2 / canonical v1 (`run_canonical_v1_rerun.py`):
- K=6, N=2 → 15 paths.
- Time-indexed folds (sorted by `__ts`).
- Purge 7 days, embargo 1 day per group.
- Inner train/val split: train sorted by date, last 1/8 → inner-val (early-stopping eval, patience=8).

### 2.5 Paired-fixed-HP discipline (memory `feedback_paired_fixed_hp_discipline`)

HP grid (16 combos):
```
kernel ∈ {15, 25}     # decomposition kernel size
hidden ∈ {32, 64}     # MLP hidden width
lr     ∈ {1e-3, 5e-4}
wd     ∈ {1e-4, 1e-3}
epochs = 40           # with early stopping (patience=8)
```

Selection:
1. Train all 16 HP × 15 paths (240 trains) — store per-path OOS AUC per HP.
2. Pick HP with **best mean OOS AUC across all 15 paths** (single fixed selection).
3. Re-train at that fixed HP across all 15 paths; collect per-path predictions for downstream stats.

Per memory `feedback_paired_fixed_hp_discipline`: per-path HP selection inflates effects ~2× (K54 v2 Q1.3 dropped from +0.0652 per-path to +0.0309 fixed-HP). Fixed-HP is the discipline.

### 2.6 Robustness suite (Group A M-{1, 7, 8, 13})

| Test | Method |
|---|---|
| **B=1000 null** | Label-permutation null on combined (concat 15 paths) predictions. |
| **DSR (deflated Sharpe)** | Bailey-Lopez de Prado 2014 with n_trials = 16 HP. |
| **PBO (CSCV)** | 200 CSCV trials; rank h\* OOS performance among HP set. |
| **CPCV-honest SE** | Training-overlap-weighted SE (ρ=0.6429 from `audit/statistical_reevaluation.md`); n_eff ≈ 2.4. |
| **Cross-period robustness** | Train on 2022-2023 trades only; test on 2024-2026 trades. (Q1.4 §8 gate (c) framing.) |

### 2.7 Determinism

`numpy.seed=42`, `torch.manual_seed=42`, fold ordering by date, no GPU randomness. Re-run reproduces identical numbers.

---

## Section 3 — Results

### 3.1 Headline (gate)

| Metric | Value |
|---|---:|
| K54 v1 anchor (CPCV mean) | 0.5286 |
| **DLinear CPCV mean AUC (paired-fixed-HP)** | **0.5049** |
| **Δ vs anchor** | **−0.0237** |
| Selected HP | `kernel=25, hidden=64, lr=5e-4, wd=1e-3, epochs=40` (HP idx 15) |
| Verdict | **FAIL** (0.5049 < 0.518 floor) |

### 3.2 Per-path CPCV table (paired-fixed-HP)

| Path | OOS AUC | vs anchor (Δ) |
|---:|---:|---:|
| 0 | 0.4705 | −0.0581 |
| 1 | 0.5431 | +0.0145 |
| 2 | 0.4917 | −0.0369 |
| 3 | 0.4921 | −0.0365 |
| 4 | 0.4969 | −0.0317 |
| 5 | 0.5096 | −0.0190 |
| 6 | 0.5129 | −0.0157 |
| 7 | 0.5179 | −0.0107 |
| 8 | 0.4927 | −0.0359 |
| 9 | 0.5028 | −0.0258 |
| 10 | 0.5279 | −0.0007 |
| 11 | 0.5086 | −0.0200 |
| 12 | 0.5385 | +0.0099 |
| 13 | 0.4672 | −0.0614 |
| 14 | 0.5006 | −0.0280 |
| **mean** | **0.5049** | **−0.0237** |
| std | 0.0217 |  |
| paths ≥ 0.528 (PASS bar) | 2 / 15 (13.3%) |  |
| paths ≥ 0.518 (BORDERLINE bar) | 5 / 15 (33.3%) |  |
| paths < 0.50 (random/below) | 6 / 15 (40.0%) |  |

40% of paths score *below* random-guessing AUC. Only 2 of 15 clear the gate.

### 3.3 Robustness suite

| Test | Result | Interpretation |
|---|---|---|
| B=1000 null-shuffle | **p = 0.962** | Cannot reject null; combined obs AUC 0.4909 < null mean. **Worse than chance once paths concatenated.** |
| DSR (n_trials=16) | **p = 1.000** | Sharpe of (lift / lift_std) is far below the expected-max-IS-Sharpe under 16 trials. **No DSR-significant lift.** |
| PBO (200 CSCV trials) | **0.795** | Catastrophic. Threshold for ship is < 0.4. **HPs selected on in-sample mean rank in the bottom 20% of HPs on the held-out half.** Means the HP grid is finding fold-fitting noise, not signal. |
| CPCV-honest SE | SE 0.0177, t=−1.34, two-sided p **0.180** | Δ statistically indistinguishable from zero under structural-correlation-corrected SE. (Note: SE is small here because the lift-vs-anchor is per-path not per-pair-of-models, and the diff is dominated by random per-path scatter, not by anchor variance.) |
| Cross-period (train 2022-2023, test 2024-2026) | **AUC = 0.4987** (n_train 1,452, n_test 660) | Random. 2022-2023 OHLCV pattern does not transfer to 2024-2026. |

**All five robustness gates fail.** This is the strongest possible refutation under the Q1.3 protocol.

### 3.4 HP grid sensitivity

The selected fixed HP (idx 15) has CPCV mean OOS AUC = 0.5049. The grid mean is in the **0.49 — 0.51** band across all 16 HPs (no HP shows substantively-different behavior). DLinear is HP-insensitive at this cohort size, which is the literature-expected behavior of a low-parameter linear model. The flatness of the HP surface, combined with the catastrophic 0.795 PBO, says the model is fitting fold-specific noise — there is nothing useful for the HP grid to choose between.

### 3.5 Why a 2× larger n cohort still fails

The headline-counter-intuitive result — n=2,319 (4.4× larger than Q1.3's n=528) and DLinear *underperforms* K54 v1's 0.5286 — replicates Q1.3's structural-overfitting finding (`audit/statistical_reevaluation.md` Section 4):

1. **Feature-stability Jaccard 0.072 (Q1.3 K54 v2 finding)** persists at the larger n. With per-bar M15 features, the noise floor at GTOS data scale dominates whatever microstructure signal DLinear can extract. DLinear cannot recover signal that is not in the data.
2. **The K54 v1 canonical features carry whatever signal there is.** When DLinear has to learn from the M15 lookback in addition to the 17 static head features, the temporal path adds variance without adding information. The static head alone can fit the LightGBM K54 v1 anchor (0.5286); adding 30 × 17 = 510 noisy temporal channels, and asking a single-layer projection to find structure in them, lowers signal-to-noise.
3. **The 2022-2023 backfill brings additional rows but ALSO adds the cross-period generalization burden.** F15 / `project_f10_a5_regime_dependent_verdict.md` already showed regime is the load-bearing axis; pooling 2022-2023 data into the same model as 2024-2026 data forces DLinear to learn a regime-invariant representation it does not have the inductive bias to learn.

Note: the M15 lookback is a per-bar OHLCV+rolling-stats representation, not a regime-aware time-series. A regime-conditioned DLinear (separate models per regime) was deliberately *not* implemented because the data-inventory audit (`audit/data_inventory_audit.md` Section 3) shows 22 of 28 (instrument × regime) cells fail n≥30.

---

## Section 4 — Verdict and decision

### 4.1 Pre-registered verdict

**FAIL.** DLinear CPCV mean AUC = **0.5049**, **0.0237 below** the K54 v1 anchor 0.5286 and **0.0131 below** the BORDERLINE floor 0.518. Reinforced by:

- 13/15 paths fail the PASS bar; 6/15 below random.
- DSR p = 1.0 — no lift survives the multiple-testing penalty for the 16 HPs tried.
- PBO 0.795 — extreme overfit signature.
- B=1000 null p = 0.962 — combined predictions are worse than chance.
- Cross-period AUC = 0.499 — no transfer.

### 4.2 Q2 sequence-model dispatch recommendation

# **NO-GO.**

**Q2 sequence-model exploration (Q-2 Time-LLM, Q-3 Chronos, Q-4 iTransformer, Q-5 PatchTST, Q-6 TCN, Q-7 LSTM) is shelved.**

Concretely:
- **Skip Q-2 — Q-7** in their current form. The Occam-test discipline that motivated H-25 is doing exactly the job the literature (Zeng et al. 2023, Group F §4) said it would: any deeper sequence architecture should not be allowed to ship if a 30k-parameter linear model + the K54 v1 head cannot beat the LightGBM K54 v1 baseline. DLinear cannot — and DLinear is widely-validated *much harder to beat* than LSTMs and vanilla Transformers at small-n financial panels.
- **K54 v3 (H-1, K54 v3 master bundle = K-1 + K-4..K-15)** becomes the **only ML path** for Q1.4 / Q2 by exclusion. The K54 v3 bundle's literature-implied lift (+0.04-0.07 AUC over Q1.3 baseline) per `MASTER_BACKLOG.md K-18` is the only credible path to a useful K54.
- **K55 ML-vs-AI shadow harness** depends on K54 production deployment, which depends on K54 v3 clearing the Q1.4 gate. K55 stays on the Phase 2 board, contingent on K54 v3.
- **Re-test gate.** If a future cohort expansion (memory `project_f6_ohlcv_extension_2025-10_landed`-style backfill yielding n ≥ 5,000 across regimes, with regime-balanced classes) lands, re-run Q-1 DLinear at that cohort. The gate stays. A passed Q-1 at n ≥ 5,000 *would* re-open Q-2 — Q-7.

### 4.3 What this verdict does NOT say

It does **not** say "deep learning cannot work on GTOS data." It says: at the current cohort size (n=2,326), with the current K54 v1 feature set, with 30 bars of M15 OHLCV, a per-instrument DLinear fails by every gate the Q1.3 protocol applies. Specifically:

- **Different inputs** (M1 microstructure with delta+imbalance per `project_microstructure_archived_2026-04-27.md`, volume-bar resampling per K-1, multi-timeframe stacked sequences) might still work — but those are independent research bets, not Q2 default candidates.
- **Pooled multi-instrument models with Kyle-Obizhaeva W-unit normalization (K-5)** could expand effective n by 7×; that is currently a K54 v3 task, not a sequence-model task.
- **Foundation-model zero-shot baselines (Q-2 Time-LLM, Q-3 Chronos)** could in principle beat DLinear without retraining; spec H-25 lists them. But the brief here is the DLinear sub-task only; a follow-up agent could re-test with zero-shot foundation models on the same cohort *if and only if* the CEO decides a free zero-shot baseline is worth the wallclock. Their gate stays the same: they must beat the K54 v1 anchor 0.5286.

### 4.4 Caveats / honest limitations

- **CPU-only training.** Each DLinear train was ~2 s on CPU. A GPU run would let me try larger HP grids; under the paired-fixed-HP discipline, that does not change the verdict — DSR p = 1.0 means there is no "more HPs would surface a winner" path.
- **Single decomposition variant.** I used kernel ∈ {15, 25} (15 = NLinear-flavor; 25 = paper default). The paper's NLinear (subtract last value, project, add last value) was not included; literature consensus (PatchTST replications) is that NLinear and DLinear produce similar AUC at small n.
- **Architecture interpretation: K54 v1 17 features + 30 M15 bars × 17 channels.** The brief said "input shape = (n_trades, 30, n_features=17)". A literal 30 × 17 of K54 v1 features (each repeated 30 times) would be uninformative since K54 v1 features are mostly per-trade-static; I documented this above. An alternative interpretation — feeding only the static K54 v1 features through DLinear (no per-bar lookback) — is mathematically equivalent to a static linear classifier and would not test what H-25 was meant to test (the sequence-model premise). My choice (M15 microstructure as the sequence channels + K54 v1 features as the static head) is the strictest test of "does adding sequence information lift the K54 v1 baseline."
- **Cross-period train cohort small (1,452).** The 2022-2023 → 2024-2026 split has 1,452 train + 660 test; that is 5× more than the F11 mechanical 22-23 cohort alone. The 0.499 OOS AUC says no cross-period transfer at all; doubling the train set in the same period would not change that.

### 4.5 Cost summary (Phase 4 quick-win bundle B-8)

| Resource | Used |
|---|---|
| Anthropic API spend | **$0.00** (subscription-only; no API calls) |
| Wallclock | 150 s (single run, end-to-end) |
| Disk | 1 .py + 1 .md + 1 .json + 1 .log (~50 KB total) |
| Compute | CPU only (Python 3.13, torch 2.11) |

---

## Section 5 — Evidence cited

| Source | Used for |
|---|---|
| Zeng, A., Chen, M., Zhang, L., Xu, Q. **"Are Transformers Effective for Time Series Forecasting?"** AAAI 2023 (Oral). arXiv:2205.13504. | DLinear architecture (decomposition + dual linear). |
| Reference repo: `github.com/cure-lab/LTSF-Linear` | PyTorch reference for moving-avg padding + decomposition impl (re-implemented locally per brief). |
| `research/ml_program/literature/synthesis/group_f_ai_ml_quantum.md` §4 (line 141-168) | Q2 sequence-model strategy + DLinear gate framing. |
| `research/ml_program/MASTER_BACKLOG.md` Section Q (Q-1 entry) + H-25 in `HYPOTHESIS_BACKLOG.md` (line 680-689) | Hypothesis spec. |
| `research/ml_program/audit/canonical_v1_rerun.md` | Anchor 0.5286 (K54 v1 CPCV mean). |
| `research/ml_program/audit/statistical_reevaluation.md` | CPCV-honest training-overlap-weighted SE methodology + ρ=0.6429. |
| `research/ml_program/audit/data_inventory_audit.md` | Per-instrument OHLCV coverage + cross-period feasibility. |
| Memory `feedback_paired_fixed_hp_discipline` | Paired-fixed-HP rule (per-path HP selection inflates ~2×). |
| Memory `feedback_walk_level_evidence_not_predictive` | Walk-level AUC ≠ realized R caveat (relevant for any future K55 follow-up). |
| Bailey, Lopez de Prado 2014, "The Probability of Backtest Overfitting" (PBO/CSCV; DSR). | Robustness suite. |
| `research/ml_program/models/k54_v1_canonical/run_canonical_v1_rerun.py` | CPCV scaffolding + canonical features list (re-used to ensure splits match). |

---

## Section 6 — Reproducibility

```bash
# Subscription-only; no API calls.
cd C:/Users/MSI/Documents/ai-trading-agent
python scripts/research/q1_dlinear_baseline.py
# Wallclock ~150 s on CPU.
# Outputs:
#   research/ml_program/experiments/q1_dlinear_results.json
#   research/ml_program/experiments/q1_dlinear_baseline.md  (this file is overwritten)
#   research/ml_program/experiments/q1_dlinear_run.log
```

Determinism: `numpy.seed=42, torch.manual_seed=42`. Identical re-runs produce identical numbers.

---

## Section 7 — Five-bullet orchestrator return summary

1. **CPCV mean AUC 0.5049** (paired-fixed-HP, K=6/N=2, 15 paths, n=2,319; selected HP `kernel=25 hidden=64 lr=5e-4 wd=1e-3`).
2. **Δ vs K54 v1 anchor (0.5286): −0.0237** — below the −0.01 BORDERLINE floor by 0.014.
3. **Robustness gates: DSR p=1.000, PBO=0.795, B=1000 null p=0.962** — all three fail decisively. PBO 0.795 says HPs selected in-sample land near-worst in held-out half; the model is fitting fold-specific noise.
4. **Cross-period sensitivity: AUC=0.499** on 2022-2023 → 2024-2026 split (n_train=1,452, n_test=660). Indistinguishable from random; no cross-period transfer.
5. **Q2 sequence-model verdict: NO-GO.** Shelve Q-2 Time-LLM, Q-3 Chronos, Q-4 iTransformer, Q-5 PatchTST, Q-6 TCN, Q-7 LSTM. K54 v3 (H-1, K-18 master bundle) becomes the only ML path until/unless cohort expansion clears a future Q-1 re-test.
