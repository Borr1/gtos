# A1 — Full Historical Dumb-Baseline Replay

**Module:** `src/research_infra/dumb_baseline.py`
**CLI:** `scripts/research/run_a1_dumb_baseline.py`
**Tests:** `tests/research_infra/test_dumb_baseline.py`
**Phase:** Phase 1 ($0 API; pure OHLCV replay)
**Branch:** `feat/research-a1-dumb-baseline`

---

## What this answers

The strategic question (CEO's #1 concern, memory `feedback_decay_is_ceo_number_one_concern`):

> Is the H2-2026 XAUUSD WR decay (64.5% H1 → 24.0% H2, χ²=0.006) AI-side or
> regime-side?

We answer it by comparing the AI's realized R to a mechanical OB-pullback
baseline over the same CANDs. If the gap stays ~30-40pp throughout the year,
the AI lost something the market still rewards (system decay). If the gap
narrows or crosses (mechanical also collapses), the market changed (regime
decay).

Memory `feedback_walk_level_evidence_not_predictive`: walk-level decision
diffs are NOT predictive of realized R. This module emits realized-R deltas
per CAND for both arms and aggregates per-month per-instrument so downstream
analysis can join either dimension without re-running the replay.

A6's prior dumb-momentum baseline (April 2026, XAUUSD-only Jan-Apr) found
mechanical Apr WR 50% vs GTOS Apr WR 10% — pointed at SYSTEM_DECAY. A1
extends that across the full historical window × 7 instruments.

---

## Mechanical entry rules

Canonical 80%-retrace OB-pullback. Same convention used in A6's
`baseline_simulator.py` and `src/components/dumb_baseline_shadow_logger.py`:

1. **Side**: take the AI's recorded direction. We're testing whether the
   mechanical arm wins or loses on the SAME setup the AI considered, not
   whether mechanical would have picked a different side.
2. **Target OB** (H1 timeframe): pick the most-recent unmitigated OB
   matching the side from the captured MSO `timeframes.H1.order_blocks`.
   * `LONG` → bullish OB (demand)
   * `SHORT` → bearish OB (supply)
   * Filter: `formation_time < candle_close_time` (no future leakage),
     `mitigated == False`. If multiple survive, latest formation_time wins.
3. **Mechanical entry** — 80% retrace into the OB:
   * `LONG`:  `entry = OB.low + 0.80 * (OB.high - OB.low)`
   * `SHORT`: `entry = OB.high - 0.80 * (OB.high - OB.low)`
4. **Mechanical SL** — buffer beyond the protective OB edge:
   * `buffer = max(sl_buffer_atr_multiplier * H1_ATR(14),
                   sl_buffer_min_ticks * tick)`
   * `LONG`:  `SL = OB.low - buffer`
   * `SHORT`: `SL = OB.high + buffer`
5. **Mechanical TP** — nearest opposing swing with implied RR ≥ 1.5:
   * `LONG`: nearest swing high above entry; if RR < 1.5 → `entry + 1.5 * (entry - SL)`
   * `SHORT`: nearest swing low below entry; if RR < 1.5 → `entry - 1.5 * (SL - entry)`
   * `tp_source` field on `MechanicalSetup` distinguishes `swing` vs `rr_floor`.

### Why use the AI's side rather than mechanical-side selection

We could compute side from H4/D1 bias the way the live system does. We
deliberately don't, because:

* The strategic question is "would mechanical-after-AI's-direction-call have
  fared differently than AI?" — we hold direction constant to isolate
  zone-precision and SL/TP differences.
* Direction-emission is the subject of A.2 (`shadow_logs/direction_emission_xau_audit.jsonl`)
  and is out of scope for A1.

### Configuration

Defaults loaded from `config/agent_config.yaml`:

| Knob | Default | Source |
|---|---|---|
| `sl_buffer_atr_multiplier` | 0.25 | `risk.sl_buffer_atr_multiplier` |
| `sl_buffer_min_ticks` | 5 | `risk.sl_buffer_min_ticks` |
| `min_rr` | 1.5 | `risk.min_rr` |
| `retrace_pct` | 0.80 | A6 canonical |
| `max_hold_bars` | 96 (24h) | A1 internal |

`tick_size` per instrument (XAUUSD=0.01, USDJPY=0.001, GBPUSD=0.00001 etc.)
mirrors `mechanical_backtest.get_pip_size` and the live system's tick map.

---

## Outcome resolution

For each `(entry, SL, TP, side, candle_close_time)` setup we walk forward
through `data/historical_2026/{SYMBOL}_M15.csv`:

* `LONG`:  `low <= SL` → SL hit, R=-1; `high >= TP` → TP hit, R=+RR
* `SHORT`: `high >= SL` → SL hit, R=-1; `low <= TP` → TP hit, R=+RR
* Both-hit on same bar: **SL-first conservative** (matches A6).
* Neither hit within `max_hold_bars` (default 96 = 24h):
  `outcome=TIMEOUT`, R = `(close - entry) / sl_dist` signed by direction.
* Empty / missing OHLCV: `outcome=NO_DATA`, R=None.

Note on `US30_cash`: the trade-records dir uses `US30_cash`, the OHLCV file
is `US30_cash_M15.csv`. The module's `OHLCV_STEM` dict normalizes both
`US30` and `US30_cash` to the same file.

---

## Joining contract

Realized AI-R join key:

```
(SYMBOL_UPPER, candle_close_time_minute_utc, side_or_None)
```

Mirrors L56 (prompt A/B harness) + L58 (F3-replay engine). Trade records
carry the AI's direction under `decision_pipeline.ai_direction` and
realized R under `decision_pipeline.outcome.r_multiple` / `exit.r_multiple`.

`_extract_realized_r_from_trade_record` checks the locations in order:

1. `decision_pipeline.outcome.r_multiple`
2. `exit.r_multiple`
3. top-level `r_multiple`

Side-less fallback (`None` for side) lets us join when the trade record
omitted direction (rare; matches L58 behavior).

A CAND with no recorded R is excluded from per-month per-instrument
matched-pair aggregates, never fabricated to zero.

---

## Output schema

### `results.jsonl` — one line per CAND

```json
{
  "cand_id": "XAUUSD|2026-04-15T13:15:00+00:00",
  "symbol": "XAUUSD",
  "candle_close_time": "2026-04-15T13:15:00+00:00",
  "period_month": "2026-04",
  "side": "LONG",
  "framework": "ob_retest",
  "kill_zone": "ny",

  "ai_decision": "CANDIDATE",
  "ai_realized_r": -1.0,
  "ai_outcome_resolved": true,

  "mechanical_skip_reason": null,
  "mechanical_entry": 4774.4,
  "mechanical_sl": 4760.5,
  "mechanical_tp": 4795.2,
  "mechanical_rr": 1.5,
  "mechanical_outcome": "TP",
  "mechanical_realized_r": 1.5,
  "mechanical_bars_in_trade": 12,
  "mechanical_fired": true,
  "realized_r_gap": -2.5
}
```

Field semantics:

* `ai_realized_r` — joined from trade record's `decision_pipeline.outcome` /
  `exit` block. `None` if no fill or no outcome captured.
* `ai_outcome_resolved` — boolean shorthand for `ai_realized_r is not None`.
* `mechanical_skip_reason` — `None` on a fired hypothesis. Otherwise one of:
  * `INVALID_SIDE`, `UNSUPPORTED_FRAMEWORK`,
  * `NO_OBS`, `NO_BULLISH_OB`, `NO_BEARISH_OB`,
  * `ALL_FUTURE_OR_UNDATED`, `ALL_MITIGATED`,
  * `BAD_OB_PRICES`, `DEGENERATE_OB`, `BAD_SL_BUFFER`, `DEGENERATE_SL`.
* `mechanical_outcome` — `TP` / `SL` / `TIMEOUT` / `NO_DATA` / `INVALID`.
* `mechanical_realized_r` — exact +RR / -1.0 on TP/SL, MTM on TIMEOUT,
  `None` on NO_DATA / INVALID.
* `realized_r_gap = ai_realized_r - mechanical_realized_r`. `None` when
  either arm has no value.
* `mechanical_fired` — walk-level decision-level diff hint: did the
  mechanical arm find a usable OB at all?

### `summary.json`

```jsonc
{
  "harness_version": "A1-v1",
  "n_rows_total": <int>,
  "per_cell": [
    {
      "period_month": "2026-04",
      "symbol": "XAUUSD",
      "n_rows": <int>,
      "n_cand": <int>,
      "ai_n": <int>,           // CANDs with realized AI R
      "ai_mean_r": <float|null>,
      "ai_wr": <float|null>,
      "mechanical_fired": <int>,
      "mechanical_n": <int>,    // CANDs with realized mech R
      "mechanical_mean_r": <float|null>,
      "mechanical_wr": <float|null>,
      "matched_pairs": <int>,
      "matched_ai_mean_r": <float|null>,
      "matched_mechanical_mean_r": <float|null>,
      "matched_gap_mean_r": <float|null>,
      "skip_reasons": {"NO_OBS": 1, ...}
    },
    ...
  ],
  "halves": {
    "H1": {n, ai_mean_r, mechanical_mean_r, ai_wr, mechanical_wr,
           gap_mean_r, gap_wr_pp},
    "H2": {...}
  },
  "monthly_gap_stddev_pp": <float>,
  "verdict": {
    "diagnosis": "SYSTEM_DECAY|REGIME_DECAY|MIXED|INCONCLUSIVE",
    "reasoning": "<2-4 sentence explanation>",
    "h1_gap_wr_pp": <float>,
    "h2_gap_wr_pp": <float>,
    "gap_delta_pp": <float>,
    "gap_stddev_pp": <float>,
    "h1_mechanical_mean_r": <float>,
    "h2_mechanical_mean_r": <float>
  },
  "per_instrument_coverage": {
    "XAUUSD": {n_cand_replayed, n_mechanical_fired, n_matched_pairs},
    ...
  },
  "run_metadata": { harness_version, output_dir, symbols_filter, start, end,
                    config, record_count, row_count }
}
```

### `report.md` — human-readable

Sections:

1. Coverage table
2. Per-month per-instrument table (CAND n, AI mean R / WR, mechanical mean R / WR, matched gap)
3. H1 vs H2 matched-pair comparison
4. **Strategic verdict block** in the format the brief specifies:

```
## Strategic verdict
- AI vs mechanical gap H1-2026: <pp>
- AI vs mechanical gap H2-2026: <pp>
- Gap delta H1→H2: <pp>
- Gap stability across months: <stddev>

Diagnosis: <SYSTEM_DECAY | REGIME_DECAY | MIXED | INCONCLUSIVE>
Reasoning: <2-4 sentences citing the gap numbers>
```

---

## Diagnosis decision tree

`_diagnose(h1, h2, gap_stddev_pp)`:

1. **INCONCLUSIVE** if either half has fewer than 10 matched pairs.
   Per the brief: "small per-instrument samples (n<10) flagged
   INCONCLUSIVE not DECAY".
2. **SYSTEM_DECAY** if:
   * the WR pp gap drops by ≥10pp H1→H2, OR
   * the R gap drops by ≥0.30 H1→H2, OR
   * the gap REVERSES (was ≥0pp H1, ≤-5pp H2).
   Interpretation: AI lost selectivity that the market continues to reward.
3. **REGIME_DECAY** if mechanical mean R dropped ≥0.20 H1→H2 AND the gap
   delta is small (≤5pp). Interpretation: market regime supports OB-zone
   trades less; both arms collapsed together.
4. **MIXED** otherwise.

The threshold values are documented in code so the call is mechanical.
They are NOT tuned to make any particular dataset come out a particular way.

---

## Strategic interpretation guide

Once the report runs, read it as follows:

* **SYSTEM_DECAY**: the AI is the problem. Investigation should focus on
  prompt drift, MSO changes, or framework dispatch (D-track items in
  the research program).
* **REGIME_DECAY**: the market changed. Investigation should focus on
  D.2 regime classifier promotion / regime-aware sizing (H38) /
  what specific regime feature changed (volatility, autocorrelation,
  fat-tail incidence — see memory `project_distributional_findings`).
* **MIXED**: both effects in play. Probably the highest-effort branch —
  decompose by per-instrument and per-side.
* **INCONCLUSIVE**: don't promote a recommendation. Wait for more data
  or run a higher-power method (longer window / more instruments).

The verdict block is INPUT to a CEO decision; A1 surfaces data, it does
NOT recommend system changes.

---

## Running

Default full historical replay (no API; reads everything under
`knowledge_base/trade_records/` + `data/historical_2026/`):

```bash
python scripts/research/run_a1_dumb_baseline.py \
    --output-dir research/decay_diagnostic/A1_dumb_baseline
```

Filtered run:

```bash
python scripts/research/run_a1_dumb_baseline.py \
    --output-dir research/decay_diagnostic/A1_dumb_baseline_xau \
    --symbols XAUUSD,USDJPY \
    --start 2026-01-01 --end 2026-04-30
```

Dry-run plan only (no writes; useful for CI):

```bash
python scripts/research/run_a1_dumb_baseline.py \
    --output-dir /tmp/scratch --dry-run
```

### `.env` note

Per memory `project_research_scripts_missing_dotenv`, research scripts do
NOT auto-load `.env`. This script does not read ANY environment variable
(no API keys are needed — Phase 1 is $0). Run it directly. If a future
iteration adds env-driven config, prefix with:

```bash
set -a && source .env && set +a
python scripts/research/run_a1_dumb_baseline.py ...
```

---

## Out of scope / non-goals

* **No AI calls.** This module never imports `anthropic` or any HTTP
  client. Phase 1 = $0 API.
* **No production-code dependencies.** No imports from `src/components/`
  or `src/safety/`. Read-only on `knowledge_base/` + `data/`.
* **No multi-framework dispatch.** `fvg_fill` and `breaker_re_entry` are
  D-track items. A non-`ob_retest` framework on a CAND produces
  `skip_reason=UNSUPPORTED_FRAMEWORK` so the report can show how many
  rows we excluded for that reason.
* **No system-change recommendations.** Per the brief: "your job is to
  surface the data, not to recommend system changes."
* **No new shadow-log writes.** This is a one-shot analysis. The
  ongoing live-shadow comparator is `dumb_baseline_shadow_logger.py`;
  A1 is the historical retro-replay companion.
