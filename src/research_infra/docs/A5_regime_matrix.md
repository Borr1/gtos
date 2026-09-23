# A5 — Regime-Stratified WR Matrix

**Question.** Are some regimes (range / trending / reversal) systematically high-WR for OB-zone trades, and others systematically low-WR? If yes, that is a regime-aware sizing opportunity (H38 follow-up). If no (uniform WR across regimes), then the OB edge is regime-agnostic and decay must come from elsewhere.

**Output.** `(instrument, regime) -> {n, WR, ExpR, median_R, Wilson 95% CI}` matrix; per-CAND JSONL feature file for K54 ML classifier; markdown verdict report.

---

## Inputs

| Source | Purpose |
|--------|---------|
| `shadow_logs/structure_detector_divergences.jsonl` | Per-M15-close H4 regime tags emitted by `src/components/structure_detector_shadow_logger.py`. Gitignored (runtime-only). |
| `shadow_logs/structure_detector_backfill_*.jsonl` | Offline backfill produced by `scripts/research/backfill_v2_regime.py` covering H4 boundaries the live log never saw. 3,571 rows for 2026-01-21 → 2026-04-24 across 9 instruments. |
| `research/archive/structure_detector_divergences/*.jsonl.gz` | Rotated archives from the live log's `RotatingJsonlWriter`. Discovered automatically by the shared loader. |
| `research/**/all_results*.json` | All offline backtest / simulation outputs containing CANDIDATE rows with realized `r_multiple`. Includes a2/f3/t7/instrument_expansion/lira/v4/b_deep_audit subfolders. |

The shared loader at `src/research_infra/structure_log_loader.py` walks the live log + every companion above and merges them with latest-write-wins semantics. See `src/research_infra/docs/structure_log_loader.md` for the discovery rules + fingerprint cache.

---

## Regime selection priority

For each H4 row in the structure log:

1. `v2_direction` if non-empty (canonical, per ADR-004 + A2 GO 2026-04-26).
2. `production_label` as a fallback if v2 is missing.
3. Otherwise the row is dropped (counted in `h4_rows_skipped_no_regime`).

Regime values follow the v2 detector taxonomy: `bullish`, `bearish`, `transitional`. The `UNTAGGED` sentinel is used for CANDs that cannot be joined to any in-window H4 row (see freshness rule below).

Empty-`symbol` rows (~5k under the live_v2 promotion-window) cannot be joined to any instrument and are dropped during indexing (counted in `h4_rows_skipped_no_symbol`). CANDs whose H4 lookup falls only into empty-symbol rows surface as `UNTAGGED`.

---

## H4-window join rule

For a CAND at candle close `t`:

1. Find the **latest** H4 row with `ts <= t` for the same `symbol` (binary search over the per-symbol sorted timestamp list).
2. If that row is older than `freshness_hours` (default 6 h, covers a full H4 bar plus dead-zone slack), tag the CAND `UNTAGGED`.
3. Otherwise tag the CAND with the row's regime.

This rule deliberately does NOT require the CAND to fall on a canonical 4h boundary because the structure detector emits H4 verdicts at every M15 close during active sessions — so the latest-at-or-before lookup always finds a fresh row inside any active KZ window.

---

## Cell statistics

For each `(instrument, regime)` cell with `n >= 1` CANDs:

| Field | Definition |
|-------|------------|
| `n` | Number of realized CANDs in the cell. |
| `wins` | Count of CANDs with `r_multiple > 0`. |
| `wr` | `wins / n`. |
| `exp_r_arith` | Arithmetic mean of `r_multiple`. |
| `median_r` | Median of `r_multiple`. Per memory `project_distributional_findings.md`, fat-tail outcomes argue for emitting both the mean and the median so a single 1.5R outlier doesn't dominate a 5-CAND cell's expectancy. |
| `min_r`, `max_r` | Range bounds for the cell. |
| `wilson_ci_95` | Two-sided Wilson score interval at 95% confidence. No continuity correction. Robust at extreme `p` (k=0 or k=n) and at small n where the normal approximation collapses. Per the project's stated low-n caveat ("don't claim significance at n<20"), Wilson is the cheap, principled default. |
| `low_n` | True iff `n < LOW_N_THRESHOLD` (10). |

Empty cells (`n == 0`) are not emitted — the matrix is sparse on the regime axis when an instrument has zero CANDs in a regime.

### Low-n threshold rationale

The project's standard rule is "no significance at n<20"; the matrix is decomposed (instrument x regime), so we relax to **n<10 for the LOW_N flag**. This preserves visibility into thin cells (e.g. SHORT/bearish under v1, where the detector emitted ~0% bearish for 8k+ windows) without misleading anyone into treating them as significant.

The `summary()` view excludes LOW_N cells from the cross-instrument regime ranking — so a single n=4 USDJPY cell cannot drown out a n=50 XAUUSD cell when computing "best vs worst regime average WR."

---

## K54 feature handoff

`cands_with_regime.jsonl` is the K54 ML classifier feature input. Each row carries the original CAND fields (subset, see `_cand_to_jsonl` in `scripts/research/run_a5_regime_matrix.py`) plus a `regime` field with values from `{bullish, bearish, transitional, UNTAGGED}`.

Recommended downstream contract:
- Treat `regime` as a 4-level categorical feature (one-hot encode).
- Filter `UNTAGGED` rows out of training fold IF the K54 model is trained on regime-aware features; otherwise keep them with regime as the explicit "missing" level.

---

## Verdict thresholds

The strategic verdict (printed in `report.md`) classifies the matrix as:

| Diagnosis | Trigger |
|-----------|---------|
| `REGIME_DEPENDENT` | WR delta between best and worst regime >= 15pp (avg across instruments, LOW_N cells excluded). |
| `REGIME_AGNOSTIC` | WR delta < 5pp. |
| `INCONCLUSIVE` | WR delta in [5pp, 15pp), or no regime has any non-LOW_N cell. |

These thresholds are heuristic; the consumer (A6, K54, H38) should re-examine the raw matrix.json + cell CIs rather than treat the verdict as authoritative.

---

## Out of scope

- No production-code modifications. The pipeline (orchestrator, primary_analyzer, permissions) is untouched.
- No prompt changes, no config changes.
- No AI / Anthropic API calls. Pure offline replay over committed JSON / JSONL.
- Sizing logic (H38) is a separate research follow-up; this deliverable provides the regime stratification only.

---

## Running locally

```bash
# From the project root, with shadow_logs/structure_detector_divergences.jsonl present:
python scripts/research/run_a5_regime_matrix.py \
    --output-dir research/decay_diagnostic/A5_regime_matrix \
    --verbose

# Outputs:
#   research/decay_diagnostic/A5_regime_matrix/matrix.json
#   research/decay_diagnostic/A5_regime_matrix/cands_with_regime.jsonl
#   research/decay_diagnostic/A5_regime_matrix/report.md
```

---

## F10 — loader unification (2026-04-27)

Background: A3's `_load_structure_log` was extended in commit `e4bf7b9` to consume rotated `.jsonl.gz` archives + the offline backfill sibling. A5's `load_regime_index` was NOT updated, which collapsed A5's first re-run to UNTAGGED=100% after the live log rotated to its current ~12-line state.

F10 extracts the shared discovery + parse + cache pipeline into `src/research_infra/structure_log_loader.py` and refactors both A3 and A5 to import from it. The systemic fix per memory note `feedback_engineer_systemic_not_patches`: any future rotation/backfill change applies to A3 + A5 (and any future research consumer) in one place.

`load_regime_index` now:

1. Calls `discover_structure_log_paths` to enumerate the live log + every companion archive + the offline backfill.
2. Streams rows via `load_structure_log_rows`.
3. Filters to `timeframe == "H4"`, applies the v2-priority `_select_regime` rule, and stages each `(symbol, ts_iso)` into a per-symbol sorted list — preserving the binary-search lookup contract.

### Re-run results (post-F10, 2026-04-27)

| Metric | Pre-fix (Wave 2A) | F1 attempt (live log only) | F10 (shared loader, full data) |
|---|---|---|---|
| Total CANDs | 335 | 335 | 335 |
| UNTAGGED rate | 64.8% | 100% | **15.5%** (52 / 335) |
| H4 rows indexed | 15,255 | 12 (post-rotation) | 3,575 |
| Best regime cell | bullish 60% (n=15) | n/a | **bearish 84.6% (n=39, contributing cells=1)** |
| Worst regime cell | transitional 48.5% (n=80) | n/a | **transitional 46.4% (n=70, contributing cells=3)** |
| WR delta | 11.5pp | n/a | **38.2pp** |
| Verdict | INCONCLUSIVE | INCONCLUSIVE | **REGIME_DEPENDENT** |

The 15.5% residual UNTAGGED is the genuine data limit: 52 CANDs whose candle-close fell more than 6 H4 freshness-hours after the most recent indexed H4 row for that symbol. Most of these are early-2026-January CANDs inside the backfill's 80-candle warm-up window where the backfill emits nothing (the production min-bars + lookback gate refuses to label until the H4 window has enough swings). Confirmed: extending the freshness window or running the backfill from 2025-Q4 forward would compress this further, but the regime verdict is already stable.

### Diagnosis

**REGIME_DEPENDENT.** Bearish-trend cohort (n=39 across XAUUSD/GER40/XAGUSD ⚠ low-n cells) carries an 84.6% WR vs 46.4% transitional WR — a 38.2pp gap above the 15pp threshold. With contributing-cell breakdown:
- bearish: 1 contributing cell (XAUUSD n=13, WR 84.6%) — single-instrument signal, NOT cross-instrument robust.
- bullish: 5 contributing cells (USDJPY/UK100/GER40/XAGUSD/XAUUSD); avg 49.4%.
- transitional: 3 contributing cells (USDJPY/GER40/XAUUSD); avg 46.4%.

The single-cell "bearish 84.6%" verdict is a small-sample warning flag — the cross-instrument coverage is too thin to claim a portfolio-wide bearish-regime tailwind. Recommended follow-up: A6 (Bayesian decay attribution) to weight by per-cell n + posterior, plus extend the backfill earlier to thicken the bearish cohort.

The pre-F10 verdict was INCONCLUSIVE because UNTAGGED dominated 64.8% of the population and absorbed cross-regime variance; F10's loader unification surfaces a real signal that the previous data depth obscured.

## Tests

`tests/research_infra/test_regime_matrix.py`:
- `load_regime_index`: 5-row synthetic JSONL -> 5 entries indexed; non-H4 rows ignored; malformed lines skipped; missing file -> empty index.
- `assign_regime_to_cand`: H4 boundary alignment (CAND inside window -> tagged; before any row -> UNTAGGED; outside freshness -> UNTAGGED; latest-at-or-before semantics; symbol mismatch -> UNTAGGED; missing time field -> UNTAGGED).
- `build_wr_matrix`: 30 synthetic CANDs across 2 instruments x 2 regimes -> 4 cells with correct n + WR; unrealized CANDs skipped; UNTAGGED counted.
- `wilson_ci`: hand-verified on (k=8, n=10), (k=0, n=10), (k=10, n=10), and (k=0, n=0); raises on out-of-range k.
- LOW_N flagging: cells with n<10 marked LOW_N in the dataframe view; summary's best/worst ranking excludes LOW_N cells.
- `_select_regime`: v2_direction priority over production_label; fallback when v2 missing.
- `RegimeIndex.lookup`: naive datetime treated as UTC.
