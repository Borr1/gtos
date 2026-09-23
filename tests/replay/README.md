# tests/replay — Replay-Based Regression Tests

Permanent test infrastructure that every PR can leverage. Catches regressions
by replaying existing historical live data through proposed code changes.

**Cost:** zero API, seconds-to-minutes runtime.

**Run all replay tests:**

```bash
pytest tests/replay/ -v
```

**Run only the replay marker across the full suite:**

```bash
pytest -m replay -v
```

---

## Test files

| File | Purpose | When to run it |
|------|---------|----------------|
| `test_decision_invariance.py` | Re-run current code against every recent CAND trade_record and assert the decision matches live outcome. | Any PR marked "bug fix / no trading-logic change". |
| `test_new_guard_demotion_rate.py` | Apply a proposed post-AI guard to historical CANDIDATEs; fail if it would demote an actual fill or exceed a demotion-rate threshold. | PR adding a new `guard_candidate_*` or post-AI validator. |
| `test_structure_detector_labels.py` | Assert `identify_structure` labels are not dominated by a single direction across 168-bar H1 windows + synthetic fixtures. | PR touching `market_state.identify_structure`. One test is marked `xfail` for a known structural-bias bug — remove once fixed. |
| `test_counterfactual_fills.py` | Replay every historical fill through the pipeline and assert nothing is rejected. Smoke-tests the replay harness itself. | PR modifying any code between CAND production and fill (guards, permissions, verification, M5 refinement). |
| `counterfactual_fills.py` | Library: `CounterfactualFill`, `run_counterfactual`, `current_pipeline`. Import from other tests. | Importable from any replay test; no direct pytest collection (backing tests live in `test_counterfactual_fills.py`). |
| `helpers.py` | Shared fixtures + data loaders + pydantic reconstruction. | Importable only. |
| `conftest.py` | Fixtures: `live_eval_rows`, `trade_records`, `historical_fills`, `baseline_cand_rate`, `replay_config`, `mock_mt5`, `h1_windows`. | Automatic — pytest picks it up. |

---

## Data sources

### `knowledge_base/live_evaluations/{symbol}/{YYYY-MM-DD}.jsonl`

- One row per AI evaluation (CANDIDATE / NO_TRADE / WAIT).
- ~1,000 rows fleet-wide for the last 30 days (April 2026).
- **Thin metadata only:** extracted fields from the AI response + decision.
  No MSO, no full reasoning text (except sampled CANDIDATEs).
- Use when you need volume for statistics (baseline CAND rate, no_trade reasons, decision distributions).

### `knowledge_base/trade_records/{symbol}/{YYYY-MM-DD}_{kz}_{hhmm}.json`

- One file per CANDIDATE-reaching evaluation.
- **Full fidelity:** MSO (all TFs, OBs, swings, pools), full AI response,
  full decision pipeline (L2, Gate 1, Gate 3), trade_parameters, limit_intent,
  shadow data.
- ~90 records fleet-wide for the last 30 days.
- Use when you need to replay the full pipeline end-to-end.

### `data/historical_2026/{symbol}_{timeframe}.csv`

- Raw OHLCV for 6 instruments × 4 timeframes (D1/H4/H1/M15).
- Coverage: Jan 2 – Apr 10, 2026 (M15), 1,700+ H1 bars.
- Use for market-state algorithms that need raw bars (swing detection,
  structure labels, ATR).

---

## Schema assumptions

The fixtures are defensive: any row that fails Pydantic reconstruction is
skipped with a stderr warning, not a test failure. Document drift below
when you find it.

| Assumption | Source | Brittle? |
|------------|--------|----------|
| `trade_record["mso"]` is a full `MarketStateObject` dump | `src.components.trade_capture` | Yes — any new optional field must have a default or reconstruction will skip. |
| `trade_record["ai_response"]` validates against `PrimaryAnalysisOutput` | `src.components.primary_analyzer` | Yes — new `Literal` enum values break reconstruction. |
| `trade_record["metadata"]["candle_time"]` is ISO-8601 UTC | `src.components.trade_capture` | Moderate — handles `Z` suffix explicitly. |
| Live_evaluations filename is `YYYY-MM-DD.jsonl` | `src.components.evaluation_logger._write` | Low — pattern test is simple. |
| A "fill" is identified by `record["execution"]["filled_at"]` | `src.components.orchestrator._capture_execution` (check there if fills suddenly aren't being detected) | **High — schema in flux April 2026.** See `helpers.is_historical_fill` if detection logic drifts. |

If you adjust the fill-detection logic, update `helpers.is_historical_fill`
**in this directory**, not in `src/`.

---

## Adding a new replay test

1. Write `tests/replay/test_<name>.py`. Add `pytestmark = pytest.mark.replay`.
2. Use the fixtures from `conftest.py`. Don't re-read JSONL files manually —
   the fixtures already handle filtering, skipping, and counting.
3. Print a one-line summary (total / matched / diverged / skipped) on every
   test, even on PASS. CI logs show scope that way.
4. Keep each test file under ~100 lines. If you need heavy logic, push it
   into `helpers.py` or a new helper module in this directory.
5. If the test depends on a hypothesized fix (like the structural-bias bug
   in `test_structure_detector_labels`), use `@pytest.mark.xfail(strict=True)`
   so the CI fails loud when the fix lands.

**Never modify `src/` from a replay test.** Helpers go in `tests/replay/helpers.py`.

---

## Counterfactual fills — how to use the harness

```python
from tests.replay.counterfactual_fills import (
    load_historical_fills,
    run_counterfactual,
    current_pipeline,
)

# Replay one fill through the current pipeline (identity):
fills = load_historical_fills(window_days=30)
for fill in fills:
    result = run_counterfactual(fill, pipeline_fn=current_pipeline)
    assert not result.outcome_changed

# Replay through a proposed change:
def my_patched_pipeline(pa, mso, config):
    pa = my_new_guard(pa)
    if pa.decision != "CANDIDATE":
        return None
    return current_pipeline(pa, mso, config)

for fill in fills:
    result = run_counterfactual(fill, pipeline_fn=my_patched_pipeline)
    if result.outcome_changed:
        print(f"Would have blocked: {fill.trade_id} ({result.blocked_by})")
```

The harness answers "would this CAND still be reachable?" — not "what R
would it earn?" (we don't have tick data post-fill). For post-fill analysis,
use `scripts/simulate_t7_live_period.py` (which burns API) or add a
tick-replay module as future work.

---

## Known limitations

- **Low fill count.** April 2026 has ~9 LIMIT_PLACED orders fleet-wide but
  very few actually filled. Counterfactual tests may skip with "no fills in
  window" until volume accrues. Widen `window_days` if needed.
- **Schema drift.** Every reconstruction is best-effort. A Pydantic
  ValidationError skips the record — this is the correct behavior (we
  don't want to mask drift with fake pass/fail), but you lose coverage
  silently. Watch for the "skipped N malformed rows" stderr message in CI.
- **No tick replay.** We can't simulate SL-vs-TP races without tick data.
  Counterfactual replay stops at CAND production.
- **One marker-opt-in.** Tests use `@pytest.mark.replay` so CI can run
  `pytest -m replay` separately. The marker is registered in `conftest.py`
  via `pytest_configure`.

---

## Future work

- Tick-replay for post-fill outcome simulation (requires historical M1 or
  tick data; not in repo as of April 2026).
- GBPUSD observer mode: currently treated identically to trade-firing
  instruments; add an "observer_only" filter to fixtures once GBPUSD's
  role in live is formalized.
- Rolling-window OB continuation replay (currently only live via
  `scripts/ob_continuation_monitor.py`).
- Test that asserts pre-AI gate saves N% of API calls on a historical window —
  right now we assert it doesn't *incorrectly* skip, not that it actually
  does save.
