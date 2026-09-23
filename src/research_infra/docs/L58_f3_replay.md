# L58 — F3-replay engine

**Phase:** 1
**Module:** `src/research_infra/f3_replay_engine.py`
**CLI:** `scripts/research/f3_replay.py`
**Tests:** `tests/scripts/test_f3_replay.py`
**Status:** Wave 1 — seam shipped, mocked-only.
**Forward pointer:** D.3 (Phase 3 — tool-use grounding) wires a tool-use
evaluator that subclasses `ReplayEvaluator`. This module is the seam that
makes that injection a one-file research change with zero production-path
modification.

---

## What is "F3-replay"?

F3 stands for **Forward, Frozen, Faithful**. Three properties that make a
replay safe to use as research evidence:

- **Forward** — the replay re-ingests the same market-state inputs that
  produced a historical decision and runs them forward through a
  configurable evaluator. The chronology of the replay matches the
  chronology of the live decisions; nothing in the replay can see a future
  candle. The loader sorts candidates by `(candle_close_time, symbol)` so
  the iteration order of the replay matches the iteration order of the
  original live runs.

- **Frozen** — the replay does not mutate any historical artifact.
  `knowledge_base/live_evaluations/` and `knowledge_base/trade_records/`
  are read-only inputs. The replay writes ONLY to the caller-supplied
  output directory; the engine refuses to point at any prefix under
  `knowledge_base/`, `shadow_logs/`, `pipeline_state/`, or `logs/` (the
  same protected list the conftest write-guard uses; memory
  `feedback_engineer_systemic_not_patches.md`).

- **Faithful** — when `LiveReplayEvaluator` is opted into (NOT in Wave 1),
  it calls the real `primary_analyzer` surface with the same system blocks
  + user message it would have built at decision time. Mocked +
  `RecordedReplayEvaluator` are deterministic ground-truth evaluators
  used in the seam tests.

---

## When to use replay vs ablation vs A/B

| Tool | Use when | What it does |
|---|---|---|
| **Replay** (this module) | You want to compare TWO evaluators on the SAME historical input set, joined to realized R, no live API spend (mocked Wave 1; live in Phase 3). | Pairs evaluator A and evaluator B against each `HistoricalCandidate`; emits `replay_results.jsonl` + `replay_summary.md`. |
| **Ablation** (sweep tooling) | You want to disable / re-tune ONE knob (e.g. SL buffer, touch-count threshold, framework selection) and re-score historical fills. | Runs the gating logic of one module variant against a corpus; emits a per-decision delta. |
| **A/B** (`scripts/research/prompt_ab_harness.py`, L56) | You want to compare TWO prompts on the same fixture set with pre-registered metrics + Bonferroni correction. | Pairs prompt A and prompt B per fixture; emits a metrics report with paired t / McNemar / sign / Wilcoxon stats. |

Replay is the right tool when the experimental change you want to test is
**at the evaluator level** — i.e. the WHOLE primary-analyzer call surface
shifts (different model, tool-use scaffolding, alternate decision
pipeline). For prompt-only changes, prefer L56's A/B harness.

---

## Walk-level vs realized-R discipline

Per memory `feedback_walk_level_evidence_not_predictive.md`: **walk-level
metrics (CR rate, decision-flip rate, side-agreement rate) reverse on
realized-R analysis.** Track A's touch-count study had walk p=5e-16 but
A1 realized-R inverted the signal.

Replay outputs are walk-level by default. The engine joins realized R
when the caller provides a `trade_records_dir`, but it does NOT promote a
walk-level pattern to evidence. Downstream analysis (see L56 `compute_metrics`
or any task-specific analyzer) is responsible for the realized-R
hypothesis test.

The minimum bar before a replay-derived divergence becomes evidence:

1. Both evaluators ran on the SAME candidate set (engine guarantees this).
2. Realized R is joined for ≥20 fixtures (`min_sample` in metrics yamls).
3. A pre-registered paired test (paired-t / Wilcoxon / sign) produces
   p < (alpha / Bonferroni denominator).
4. Walk-level CR-flip + realized-R direction AGREE.

---

## The hookable callback contract

```python
ReplayHook = Callable[
    [HistoricalCandidate, ReplayEvaluator, dict],
    None,
]
```

`ReplayRun` accepts two optional hooks:

- `before_evaluate(cand, evaluator, ctx) -> None`
- `after_evaluate(cand, evaluator, ctx) -> None`

Each hook fires **once per evaluator pass per candidate**. For a run with
A and B, that's 2 × n_candidates calls per registered hook. The `ctx`
dict persists for the lifetime of the run — it is the reserved channel
for D.3 (Phase 3) to record tool-use trace fragments and assemble them
post-run. The engine itself never inspects the ctx dict.

`after_evaluate` injects `ctx["last_decision"]` so the hook can read the
just-produced `ReplayDecision` without recomputing it.

### What hooks may NOT do

- Mutate the candidate (Frozen — input must be re-runnable).
- Call the API directly (each evaluator owns its own API budget; hooks
  are observation-only).
- Write to `knowledge_base/`, `shadow_logs/`, `pipeline_state/`, or
  `logs/`. They may write to the run's `output_dir` if necessary; D.3
  will use the ctx dict + a final flush in `after_evaluate` for the
  last candidate.

---

## Realized-R join requirement

When `trade_records_dir` is supplied to `load_historical_candidates`,
each candidate's `realized_r` is populated via L56's join contract:

```
key = (SYMBOL, candle_close_time_minute_utc, side)
fallback = (SYMBOL, candle_close_time_minute_utc, None)
```

The side-less fallback exists because some trade records do not carry
direction (older format) — direction-mismatched lookups still succeed.

Trade records must have either:

- `decision_pipeline.outcome.r_multiple` (current schema), or
- `exit.r_multiple` (intermediate schema), or
- top-level `r_multiple` (T7-sim flat shape).

Records lacking any of these are dropped from the index with no warning;
the candidate's `realized_r` stays `None` and downstream metrics flag
the row as "missing realized R".

The minute-truncated key normalizes microsecond drift between
live_evaluations (often `:00.000000`) and trade_records (often
`:42.123456`).

---

## D.3 forward pointer (Phase 3)

Phase 3 task D.3 wires Anthropic tool-use scaffolding into the live
evaluation path. The integration plan:

1. Subclass `ReplayEvaluator` (or implement the Protocol fresh) with a
   `ToolUseReplayEvaluator` that calls `primary_analyzer._call_claude`
   under a tool-use config.
2. Use `before_evaluate` / `after_evaluate` to capture tool-use traces
   into the run context.
3. Compare `ToolUseReplayEvaluator` against `RecordedReplayEvaluator`
   over a 30-day historical window with realized-R join.
4. Promote to live only after the realized-R paired t-test crosses the
   pre-registered Bonferroni-corrected threshold AND the walk-level CR
   shift agrees in direction.

L58 ships the seam. D.3 is the consumer. No production-path edit is
required for either step.

---

## CLI quickstart

```bash
# Dry-run: prints planned candidates + counts, no API, no writes.
python scripts/research/f3_replay.py \
    --evaluator-a recorded \
    --evaluator-b mock_seed_42 \
    --since 2026-04-01 --until 2026-04-25 \
    --instruments XAUUSD,GBPJPY \
    --output research/f3_replay_smoke \
    --dry-run

# Real run (mocked-only — Wave 1).
python scripts/research/f3_replay.py \
    --evaluator-a recorded \
    --evaluator-b mock_seed_1 \
    --instruments XAUUSD \
    --output research/f3_replay_xau_baseline \
    --realized-r-join knowledge_base/trade_records \
    --run-tag phase1_l58_xau_smoke
```

Built-in evaluator names:

- `recorded` — return the historical decision verbatim
  (`RecordedReplayEvaluator`).
- `mock_seed_<N>` — deterministic mock, seed `N`.
- `live` — gated behind `GTOS_F3_REPLAY_ALLOW_LIVE=1` AND
  `ANTHROPIC_API_KEY`. NOT exercised in Wave 1.

---

## Output artifacts

The run writes three files into `--output`:

- **`replay_results.jsonl`** — one row per candidate. Fields: `cand_id`,
  `symbol`, `candle_close_time`, `kill_zone`, `framework_recorded`,
  `realized_r`, `evaluator_a` (id/decision/side/error), `evaluator_b`
  (same shape).
- **`replay_summary.md`** — human-readable walk-level CR + decision-diff
  + realized-R sums table. Each summary explicitly cites memory
  `feedback_walk_level_evidence_not_predictive.md` so the reader is
  reminded that walk-level evidence alone does NOT promote to evidence.
- **`run_metadata.json`** — CLI args, evaluator IDs, harness version
  (`HARNESS_VERSION`), n_candidates, n_decision_diff,
  n_with_realized_r, run_tag.

---

## Tests

`tests/scripts/test_f3_replay.py` (~30+ tests) covers:

- Loader: 5-fixture roundtrip, deterministic ordering, date filter,
  instrument filter, malformed-row tolerance.
- Realized-R join: 3-of-5 partial join, microsecond normalization.
- `RecordedReplayEvaluator` bit-exact verbatim, zero divergence when
  paired with itself.
- `MockReplayEvaluator(seed=N)` determinism.
- `ReplayRun` end-to-end: artifact set + counts + protected-path
  refusal.
- Hooks: before / after fire once per evaluator pass per candidate;
  `ctx["last_decision"]` populated.
- CLI: `--dry-run` exits 0 without writes; real run writes all three
  artifacts; unknown evaluator → exit 2; no candidates → exit 2;
  `live` evaluator blocked without env gate.
- Time normalization helpers (Z suffix, microseconds, naive UTC,
  garbage input).
- `LiveReplayEvaluator` gate (env + client both required).

Synthetic fixtures only — never real production rows
(`tests/scripts/fixtures/f3_replay_test_candidates.jsonl`).
