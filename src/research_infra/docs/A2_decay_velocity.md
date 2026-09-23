# A2 — Per-Instrument Rolling-Window Decay Velocity

Research-only infrastructure for measuring decay velocity in realised
WR / Expectancy on a per-instrument basis.

**Branch:** `feat/research-a2-decay-velocity`
**Module:** `src/research_infra/decay_velocity.py`
**CLI:** `scripts/research/run_a2_decay_velocity.py`
**Tests:** `tests/research_infra/test_decay_velocity.py` (34 tests)
**No AI calls.** Pure-Python (no third-party deps in the core module).

---

## What this answers

For each of the 7 instruments the GTOS fleet trades (XAUUSD, US30,
USDJPY, GBPJPY, GBPUSD, XAGUSD, NAS100), **how fast is realised WR /
Expectancy decaying over the full historical period?** Is decay uniform
across the fleet, or concentrated on specific instruments?

This complements **A1** (system-vs-regime). A2 surfaces _where_ decay is
happening; A1 surfaces _why_.

---

## Formula

Given a per-instrument trade list sorted ascending by timestamp, the
module:

1. **Drops trades without a usable realised R**. Realised-R lives in any
   of `realized_r`, `realized_R`, `actual_r`, `actual_R`, `r_multiple`,
   `rR` — at top level or inside `trade["exit"]`. This matches the v1.1
   instrumentation schema (`research/a3_trade_record_instrumentation/README.md`)
   plus the legacy `_trade_index.json` schema (`r_multiple`).

2. **Buckets the remaining trades into non-overlapping windows of size
   N (default 50)**. Window k covers trades `[k*N, (k+1)*N)`. A
   non-overlapping decomposition gives independent samples for the
   downstream regression — overlapping windows would inflate the
   apparent regression d.o.f. and break the slope p-value's calibration.

3. For each window emits a `WindowPoint` carrying:
   - `timestamp` — the wall-clock timestamp of the *last* trade in the
     window.
   - `wr` — fraction of window trades with `r > 0`.
   - `exp_r` — mean realised R per trade.
   - `n` — window size (always == N for full windows).
   - `window_index` — 0-based.

4. Runs OLS on `(window_index, wr)` to get a raw slope. The slope is
   re-scaled to per-30-day via the mean wall-clock duration between
   consecutive window endpoints.

5. Computes a two-sided Student-t p-value with `df = n_points - 2`. The
   incomplete-beta function uses Numerical Recipes' continued-fraction
   expansion (Lentz's method) so the module stays dependency-free
   (no scipy).

6. Bonferroni-corrects across the family of seven decay-slope tests.
   The denominator is the count of instruments where the raw p-value
   was computable (i.e. `n_points >= 3`); INSUFFICIENT-N instruments do
   not consume α budget.

7. Verdicts:
   - `DECAYING`  — `n_total >= n_min` AND `p_corrected < α` AND slope < 0.
   - `IMPROVING` — `n_total >= n_min` AND `p_corrected < α` AND slope > 0.
   - `INSUFFICIENT_N` — `n_total < n_min`.
   - `STABLE` — `|slope_per_30d| < 1pp/mo` regardless of significance.
   - `INCONCLUSIVE` — none of the above.

---

## Window-size rationale

Default `N = 50`. The reasoning is a tradeoff between:

- **Per-window estimator variance.** With `n=50` and per-trade WR
  variance ≈ 0.5 × 0.5 = 0.25, the Wilson 95% CI half-width on a single
  window's WR ≈ ±13.8pp — tight enough to read trend direction at
  the chunk level.
- **Regression d.o.f.** The slope p-value uses df = `n_windows - 2`. To
  reject H0 with confidence we need ≥ 4 windows (df ≥ 2). With 200+
  filled trades per instrument, `N=50` gives 4–6 windows — exactly the
  minimum useful regression sample.

For sparse instruments (e.g. early-life FTMO-paid fills), pass
`--window 25` or `--window 30` to trade per-window precision for more
points. The CLI accepts arbitrary `--window` ≥ 2.

---

## Bonferroni correction

The family of decay-slope tests run is the *seven instruments the fleet
trades*. Each test's null hypothesis is `slope == 0`. The corrected
p-value is `min(1, p_raw × N_tested)`, where `N_tested` is the number
of instruments that produced a finite raw p-value (i.e. ≥ 3 windows).

Instruments with INSUFFICIENT_N → no test → no α-budget consumption.
This is the canonical Bonferroni denominator.

For the `DECAYING` / `IMPROVING` verdict, the threshold is on the
*corrected* p-value, not the raw p. With α = 0.05 and N = 7, a raw
p-value below ≈ 0.0071 is needed — a stricter bar than typical, which
is the entire point of the correction.

---

## Interpretation guide

| Reading | Meaning | Action |
| --- | --- | --- |
| Slope `< -3pp/mo`, `p_corr < 0.05` | Sharp realised-WR decay, statistically significant after correction. | High-priority research target — the edge is degrading on this instrument. |
| Slope `< -1pp/mo`, `p_corr < 0.05` | Mild but significant decay. | Watch list. Combine with A1 system-vs-regime to triage. |
| `|slope| < 1pp/mo`, p_corr ≥ α | No meaningful trend. | STABLE. Edge appears intact for this instrument. |
| Slope significant but `n_total < 20` | INSUFFICIENT_N — verdict suppressed. | Need more fills. Often reflects FTMO-free-trial EA exclusion (see Caveats). |
| `n_windows < 3` | Cannot compute p-value (df too small). | INCONCLUSIVE. Lower the window size or wait for more fills. |

---

## Caveats

### Walk-level vs realised-R discipline

Slopes here are computed on **actual realised R per filled trade**, not
on walk-level / structural-proxy decay indicators (BOS-retest WR
proxies, sweep-reversal WR proxies, etc.). The latter exist in
`research/instrument_expansion_2026-04-25/02_decay_analysis.py` for the
mechanical-edge view of decay, but they are **NOT predictive of
realised R** in this project's data — see
`feedback_walk_level_evidence_not_predictive` in user memory and the
session-39 finding that p=5e-16 walk-level evidence on touch-count
decay reversed under realised-R analysis.

### Filled-trade availability

The live `trade_records/` JSON pipeline only populates
`exit.realized_R` after a real broker fill. Under the FTMO free-trial
EA exclusion, no live trades have filled yet (see ADR-A3 / 
`research/a3_trade_record_instrumentation/README.md` and the
`feat/a3-trade-record-instrumentation` branch). The realised-R data
the script can find today comes mostly from the legacy
`knowledge_base/index/_trade_index.json` (XAUUSD batch + GBPUSD batch
trades). Expect five of seven fleet instruments to come back as
`INSUFFICIENT_N` until the FTMO paid challenge starts populating fills.

### Non-overlapping windows

Each window is independent (step == window) to keep the regression
p-value calibrated. A window-size of 50 over a 150-trade history
produces exactly 3 windows — the minimum useful regression sample. For
production-grade decay detection, expand the realised-R history first
(more fills) rather than switching to overlapping windows.

### H1/H2 WR split

The H1/H2 WR columns split the **filled trade list** in half by index
(not by calendar date). They give a quick sanity-check on the regression
slope but should not be treated as a separate hypothesis test. The
formal test is the regression slope's p-value with Bonferroni
correction.

---

## Outputs

The CLI writes three files into `--output-dir`:

| File | Purpose |
| --- | --- |
| `series.jsonl` | One row per `(instrument, window_end_date)` carrying `n`, `wr`, `exp_r`, `window_size`, `total_trades`. Stable schema for downstream pipelines. |
| `summary.json` | Per-instrument verdict block (`n_total`, `n_windows`, `h1_wr`, `h2_wr`, `slope_per_30d`, `slope_per_window`, `p_value_raw`, `p_value_bonferroni`, `verdict`) plus fleet-level `decay_concentration` label. |
| `report.md` | Human-readable verdict table + per-instrument narrative + caveats. Use this as the discussion artifact. |

---

## Falsifiability

- `tests/research_infra/test_decay_velocity.py` — 34 tests covering:
  - Hand-verified rolling-window math on 3 synthetic series.
  - Window > N trades → empty series (graceful).
  - Known-slope synthetic series → recovered slope (within tol).
  - Per-instrument aggregation: 3-instrument tmp dir → 3 series.
  - p-value: synthetic null (random R) → high p; strong decay → low p.
  - Bonferroni correction applied + capped at 1.
  - Verdict classification rules.
  - Concentration heuristic.
- Trade-extraction helpers tested for all 6 realised-R field aliases
  + 4 timestamp-field aliases.

---

## Out of scope

- This module **does not** call the AI / Anthropic API.
- It **does not** modify production code, prompts, or config.
- It **does not** recommend system changes — it surfaces data only.
- It **does not** lower the n-min threshold below 20 — small-sample
  verdicts are always flagged INSUFFICIENT_N or INCONCLUSIVE.
