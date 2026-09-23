# sl_too_tight Buffer Distribution Study — Primary Analysis
Date: 2026-04-18 | Analyst: Opus 4.7 primary | Status: awaiting replication

## Executive summary

Five candidate configurations of the `sl_too_tight` gate were evaluated on
two datasets. The retest CSV (n=726, simulated geometry-A SLs) produces a
narrow buffer distribution — 99.7% of rows fall between 0.4 and 3.0 × M15
ATR, with a single row below 0.5 and none below 0.3. **This means Options
C (impl-A), D, and E are statistically indistinguishable on this dataset
— each admits at most 3 extra trades beyond Baseline.** The only
configuration that meaningfully differs from Baseline is Current-live
(buffer ≥ 0.3, no upper), which admits all 102 SL_dist<1.5×ATR rows.

Those 102 admits have WR=45.5% but expectancy **+0.83R/trade** (winners
average +3.0R). The retest dataset therefore supports a buffer-LOWER-band
exception (like Current-live) and is NEUTRAL on the 0.5 upper cap —
upper-cap behavior must be judged on live-trading logs, not this dataset.

- Gate semantics: `src/components/permissions.py:642-648`
- Exception: `src/components/permissions.py:238-344`

## Data summary

| Dataset | Path | Rows | Date range | Notes |
|---|---|---|---|---|
| Retest CSV (primary) | `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` | 726 | 2026-01-01 → 2026-04-17 | 5 symbols. Deterministic geometry-A SL at OB_edge ± 0.5×H1_ATR. |
| Batch JSON (secondary) | `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` | 111 (101 ob_retest) | 2024-04-01 → 2026-03-30 | XAUUSD only, AI-chosen SLs. No OB_edge or M15_ATR fields. |

Per-symbol retest counts: GBPJPY 150, GBPUSD 150, XAUUSD 147, US30_cash 143,
USDJPY 136. Outcomes: CONTINUED 528, REVERSED 179, UNRESOLVED 19.

**M15 ATR derivation**: the retest CSV carries only `h1_atr_at_retest`.
Real per-row M15 ATR(14) was computed from `data/historical/{SYMBOL}_M15.csv`
via as-of merge at `retest_ts` (backward within 1h). All 726 rows matched
(source="real", zero fallbacks). Empirical median M15/H1 ATR ratio per
symbol: XAUUSD 0.481, US30 0.493, USDJPY 0.482, GBPJPY 0.496, GBPUSD 0.483.

**OB edge derivation**: back-solved from geometry-A construction.
`sl_a = ob_edge ± 0.5 × H1_ATR`, so `ob_edge = sl_a ± 0.5 × H1_ATR`
(sign per direction). `buffer = |sl_a - ob_edge| = 0.5 × H1_ATR` by
construction. `sl_beyond_edge` is tautologically True for 726/726 rows
under this geometry (SL sits 0.5 ATR outside OB on the safe side).

## Buffer distribution

Buffer in M15-ATR units = `0.5 × H1_ATR / M15_ATR`. Because the
H1:M15 ATR ratio clusters near 2.0 (median 0.48 inverse), buffer_atr
clusters near 1.04 ATR.

Buffer_atr statistics across n=726:
- mean 1.056, std 0.374, min 0.402, p25 0.813, p50 0.973, p75 1.201, max 4.029.

Histogram (0.1 ATR bins, winners vs losers, where WR = wins/(wins+losses)):

| Buffer band | n | Wins | Losses | Mean R | WR |
|---|---|---|---|---|---|
| [0.4, 0.5) | 2 | 1 | 1 | -0.46 | 0.500 |
| [0.5, 0.6) | 18 | 17 | 1 | +0.51 | 0.944 |
| [0.6, 0.7) | 45 | 30 | 15 | +1.58 | 0.667 |
| [0.7, 0.8) | 98 | 75 | 23 | +0.05 | 0.765 |
| [0.8, 0.9) | 103 | 81 | 22 | +0.00 | 0.786 |
| [0.9, 1.0) | 119 | 89 | 30 | +0.07 | 0.748 |
| [1.0, 1.1) | 73 | 49 | 24 | -0.09 | 0.671 |
| [1.1, 1.2) | 76 | 55 | 21 | +0.13 | 0.724 |
| [1.2, 1.3) | 52 | 41 | 11 | -0.02 | 0.788 |
| [1.3, 1.4) | 22 | 17 | 5 | -0.02 | 0.773 |
| [1.4, 1.5) | 31 | 22 | 9 | -0.11 | 0.710 |
| [1.5, 1.6) | 17 | 12 | 5 | -0.06 | 0.706 |
| [1.6, 1.7) | 16 | 12 | 4 | +0.10 | 0.750 |
| [1.7, 1.8) | 9 | 6 | 3 | -0.09 | 0.667 |
| [1.8, 1.9) | 5 | 4 | 1 | +0.14 | 0.800 |
| [1.9, 2.0) | 2 | 2 | 0 | +0.13 | 1.000 |
| [2.0, 3.0) | 16 | 11 | 4 | +0.04 | 0.733 |

Band-aggregated WR by wider buckets:

| Band | n | WR | Expectancy |
|---|---|---|---|
| [0.4, 0.6) | 20 | 0.900 | +0.416R |
| [0.6, 0.8) | 143 | 0.734 | +0.531R |
| [0.8, 1.0) | 222 | 0.766 | +0.038R |
| [1.0, 1.2) | 149 | 0.698 | +0.022R |
| [1.2, 1.5) | 105 | 0.762 | -0.047R |
| [1.5, 2.0) | 49 | 0.735 | +0.012R |
| [2.0, 5.0) | 19 | 0.789 | +0.001R |

Correlation: `buffer_atr × is_win = -0.006` (essentially zero). The buffer
does NOT predict direction outcome on this dataset; what it predicts is
**expectancy magnitude** — tight buffers give bigger R when they work.

## Gate configuration results

### Retest dataset (n=726)

`admitted` counts UNRESOLVED rows for completeness; WR/expectancy use
only rows with a resolved R. `sweeps_proxy` = REVERSED AND buffer_atr<0.7
AND time_to_MAE ≤ 2 candles (upper bound — true "would've reached TP
if SL wider" cannot be measured without forward OHLC past SL candle).

| # | Name | Admitted | With R | Wins | Losses | WR | Expectancy | Sweeps* |
|---|---|---|---|---|---|---|---|---|
| 1 | Baseline | 624 | 606 | 482 | 124 | 79.5% | +0.012R | 1 |
| 2 | Current-live (buf≥0.3) | 726 | 707 | 528 | 179 | 74.7% | **+0.130R** | 10 |
| 3 | Impl-A (buf≤0.5) | 627 | 608 | 483 | 125 | 79.4% | +0.011R | 2 |
| 4 | Option D (buf≤0.3) | 624 | 606 | 482 | 124 | 79.5% | +0.012R | 1 |
| 5 | Option E (0.3≤buf≤0.5) | 627 | 608 | 483 | 125 | 79.4% | +0.011R | 2 |

\* Proxy — upper bound, not causal.

Observations:
- Options 3, 4, 5 are indistinguishable from Baseline on this dataset
  — they admit 0–3 extra rows because only 3 retests have buffer_atr
  in [0.3, 0.5] and none below 0.3.
- Current-live admits ALL 726 rows because every row has buffer_atr ≥ 0.4.
  The additional 102 trades (vs Baseline) have WR 45.5% / expectancy
  +0.83R: high-ATR environments where the 0.5 H1_ATR buffer is a small
  fraction of M15 ATR, but winners capture huge R (mean winner +3.0R
  because targets are far in ATR terms).

Per-symbol breakdown under Impl-A (same table under Baseline — differs
by ≤3 trades):

| Symbol | Admitted | Wins | Losses | WR | Expectancy |
|---|---|---|---|---|---|
| GBPJPY | 134 | 106 | 25 | 80.9% | +0.040R |
| GBPUSD | 126 | 95 | 26 | 78.5% | -0.036R |
| US30_cash | 116 | 90 | 18 | 83.3% | +0.072R |
| USDJPY | 118 | 94 | 24 | 79.7% | +0.028R |
| XAUUSD | 133 | 98 | 32 | 75.4% | -0.043R |

### Batch dataset (n=101 ob_retest, XAUUSD)

Limitations prevent buffer-conditional analysis. The batch JSON stores
`stop_loss`, `entry_price`, `r_multiple`, but not `ob_edge` or
`m15_atr_at_entry`. Daily-mean M15 ATR was used to compute sl_dist_atr.
With no buffer, all buffer-based exceptions are structurally unreachable
— so all 5 configs collapse to Baseline (no bypass available).

| Config | Admitted | Wins | Losses | WR | Expectancy |
|---|---|---|---|---|---|
| All 5 | 104 | 70 | 31 | 69.3% | +0.259R |

6 trades have sl_dist_atr < 1.5 (would be denied by Baseline if the
gate applied with this M15-ATR proxy). Those 6 are outside scope for
buffer-band analysis on this dataset.

## Sensitivity analysis — Option E floor sweep

| Floor | Ceiling | Admitted | Wins | Losses | WR | Expectancy |
|---|---|---|---|---|---|---|
| 0.2 | 0.5 | 627 | 483 | 125 | 79.4% | +0.011R |
| 0.3 | 0.5 | 627 | 483 | 125 | 79.4% | +0.011R |
| 0.4 | 0.5 | 627 | 483 | 125 | 79.4% | +0.011R |

**Sensitivity is zero** because every retest row satisfies `buffer_atr ≥ 0.4`.
The floor never binds on this dataset. This is geometry-A-specific and does
NOT generalize — live AI-chosen SLs show much more variable buffer_atr
(see Apr 16 incident at 0.12 × M15_ATR).

## Key findings

1. **The retest dataset cannot distinguish Options C/D/E from Baseline.**
   Geometry-A SL at OB_edge + 0.5×H1_ATR produces buffer_atr in a narrow
   window (min 0.40, max 4.03, median 0.97). Only 3 rows fall in [0.3, 0.5]
   and 0 in [0, 0.3]. The upper cap of 0.5 ATR cannot be validated from
   this data — a live-AI-SL dataset is required. Flag this prominently.

2. **Current-live (buf ≥ 0.3 no upper) admits 102 extra trades vs
   Baseline, with WR 45.5% and expectancy +0.83R/trade.** Mean winner in
   that pool is +3.0R because those are high-volatility H1 environments
   where the target (1 OB-body past far edge) is far in ATR terms. Net
   effect on the retest dataset: expectancy rises from +0.012R (Baseline)
   to +0.130R (Current-live) — a 10× improvement IF the additional
   trades' economics transfer to live.

3. **Buffer does NOT predict direction outcome (r=-0.006).** What it
   predicts is expectancy magnitude — thin buffers deliver bigger R when
   they work. This is consistent with the OB edge being the invalidation
   point: SLs slightly beyond the edge either get swept quickly or the
   trade runs the full impulse.

4. **Apr 16 XAUUSD -1R incident (buffer=0.12 × M15_ATR) is NOT
   representable on this dataset.** Geometry A mechanically produces
   buffer ≥ 0.40, so the 0.12 ATR placement reflects an AI-chosen SL that
   hugs the OB edge more tightly than our research construction. The
   0.3 ATR floor Apr 16 committed fix is orthogonal to the Options C/D/E
   upper-cap question — this dataset is silent on it.

5. **Per-symbol variance is material.** Under Impl-A, GBPUSD/XAUUSD have
   negative expectancy (-0.036, -0.043R) while US30 is +0.072R. The gate
   change will hit symbols differently — any cross-instrument rollout
   needs per-symbol shadow validation.

## Recommendation

**Keep Current-live (`buffer ≥ 0.3 × M15_ATR`, no upper cap) as the
production config.** Data-driven reasoning:

- On the retest dataset, Current-live admits 16% more trades (726 vs
  624) and raises expectancy from +0.012 to +0.130R.
- The 102 additional trades have WR 45.5% but expectancy +0.83R/trade —
  net positive even at sub-breakeven WR because winners dominate.
- Options C/D/E (upper cap at 0.3 or 0.5 ATR) look identical to Baseline
  on this dataset — there is NO empirical evidence here to prefer any of
  them over Current-live.

**However**, the retest dataset cannot answer whether an upper cap would
protect against thin-buffer AI SLs (like Apr 16's 0.12 ATR placement).
That question requires:

1. The live production log of AI-chosen SLs with buffer_atr computed at
   decision time (`shadow_logs/` — propose a shadow logger if not already
   present). After ~50+ structural-exception trades live, re-run this
   study on that dataset.
2. Cross-reference the ADR 003 Youden separator (0.53 ATR — on a different
   target metric, not R-outcome). If the separator is structurally sound,
   Option E (0.3 ≤ buf ≤ 0.5) should outperform Current-live on AI SLs —
   but this dataset cannot show it.

**If the CEO wants a buffer upper cap NOW** on the strength of ADR 003 and
the Apr 16 incident, **Option E (0.3 ≤ buf ≤ 0.5)** is preferred over
Option C because it also preserves the Apr 16 floor. Zero empirical
disadvantage vs Baseline on the retest dataset.

**Do NOT adopt Option D** (buf ≤ 0.3) — inconsistent with the Apr 16
floor (0.3 is the floor), would only admit buffers 0≤buf≤0.3 which is
empirically the thin-buffer-sweep zone.

## Methodology notes

- **OB_edge inference**: back-solved from geometry-A construction
  (`sl_a = ob_edge ± 0.5 × H1_ATR`). Any future change to geometry A in
  `A2_v2_validation.py` will invalidate this.
- **M15 ATR source**: real per-row ATR(14) via as-of merge to
  `data/historical/{SYMBOL}_M15.csv`. Zero fallback hits.
- **Sweep proxy**: REVERSED AND buffer_atr<0.7 AND time_to_MAE ≤ 2
  candles. This is an UPPER BOUND — true sweeps (continued to TP after
  wicking SL) cannot be measured without forward OHLC past the SL-hit
  candle in the dataset.
- **Circular labeling check**: the outcome label is OHLC-deterministic
  (walk-forward to SL or TP), independent of the buffer choice EXCEPT
  that the SL level is itself a function of buffer. Changing buffer
  would change outcomes — this study fixes buffer at 0.5 H1_ATR and
  varies the GATE (admit/deny) decision only. No circularity.
- **Batch JSON limits**: no OB_edge, no M15 ATR at decision time → no
  buffer, no directly comparable sl_dist_atr. Used daily-mean M15 ATR
  as an approximation. Batch dataset is a weak secondary — do not rely
  on it for config selection.

## Reproducibility

Analysis script: `research/sl_gate_buffer_analysis/primary_analysis.py`

Run:
```
python research/sl_gate_buffer_analysis/primary_analysis.py
```

Outputs written to `research/sl_gate_buffer_analysis/`:
- `retests_enriched.csv` — 726 rows with derived fields
- `buffer_histogram.csv` — 0.1 ATR bins, winners/losers/WR
- `retest_config_results.csv` — 5 configs, admitted/WR/expectancy
- `retest_per_symbol_impl_a.csv` — per-symbol breakdown under Impl-A
- `option_e_sensitivity.csv` — floor sweep at 0.2, 0.3, 0.4
- `batch_config_results.csv` — batch JSON results (5 configs identical)

Run parameters (no hardcoded secrets):
- Data files read-only
- No network calls
- Deterministic (seed-independent)

Peer verification: an independent run should reproduce the 5-config
admitted counts exactly (624, 726, 627, 624, 627) and WR to 3 decimal
places. Any deviation → investigate M15 ATR data differences.
