# scripts/research/

Phase 1 research-program scripts. Code under this directory is dispatched
by the CEO + research agents — **NOT** by the live orchestrator. Anything
here is research infrastructure (parallelisation, slicing, plotting,
post-hoc analysis, prompt comparison) — never live trading code. Modules
here MUST be additive: never imported from `src/` or `run_agent.py`.

---

## simulate_t7_parallel.py — parallel T7 historical simulator (L54)

`scripts/simulate_t7_parallel.py` is an additive wrapper around the
single-process T7 simulator (`scripts/simulate_t7_live_period.py`). It
splits a date window into N contiguous slices and runs the inner
simulator once per slice as an isolated subprocess, then merges the
results deterministically.

### When to use parallel vs sequential

Use the **parallel** wrapper when:

* You have a window of >2 weeks AND want the result in <10 min.
* You're sweeping many configurations / detector versions and the
  per-config wall clock matters.
* You need partial results / per-slice diagnostics (the parallel runner
  writes a per-slice subdir with full inner-simulator output preserved
  so you can inspect any individual slice's `t7_live_simulation_report.md`).

Use the **sequential** simulator (`scripts/simulate_t7_live_period.py`
directly) when:

* The window is short enough that a single process finishes in <5 min.
* You want a single combined report (the parallel wrapper outputs a
  consolidated JSON, NOT a single combined Markdown report — each
  slice's report stays in its slice subdir).
* You need any of the inner simulator's flags that the wrapper does
  NOT pass through (e.g. `--detector-version`, `--a1-backtest-log-path`,
  `--slice-tag`). The wrapper deliberately keeps its own surface small;
  if you need those flags per slice, invoke the inner simulator manually
  or extend `build_command()` first.

### Slice count tuning

| Window | Recommended `--slices` | Notes |
|--------|-----------------------|-------|
| ≤2 weeks | 1 (use sequential) | Subprocess overhead dominates. |
| 2-4 weeks | 4-6 | One slice per workweek is the sweet spot. |
| 1-2 months | 8 | Even slices, balanced. |
| 3-4 months | **12** (canonical) | Matches Phase 1 decay-diagnostic spec. |
| 6+ months | 16-24 | Tier-4 still has headroom, but watch for monthly-budget overshoot — each slice gets the full `--budget` independently. |

`--max-concurrent` defaults to `min(slices, os.cpu_count(), 16)`. The
hard cap of 16 is conservative for Anthropic tier 4: the input-token
bucket comfortably accommodates 16 concurrent Sonnet 4.6 `effort=max`
inferences per second, but each slice has its own 1 req/s inner
cadence so 16 outer × 1 inner = 16 req/s aggregate. Bump
`MAX_CONCURRENT_HARD_CAP` in the script if you have explicit
confirmation that more headroom exists.

### Resumability

`--resume` skips any slice whose `all_results.json` is already on disk
and parseable. Use it after a partial failure to re-run only the
crashed slices. Slices with corrupt (non-JSON) output files are NOT
skipped — they're treated as failed and re-run. To force a complete
re-run, delete the slice's output directory or pick a fresh
`--output-dir`.

### Output file naming

For `--output-dir <DIR>`, `--symbol <SYM>`, `--start <S>`, `--end <E>`:

```
<DIR>/
  slice_001_<S>_<S+slice0>/
    all_results.json                 # written by inner simulator
    XAUUSD_t7_simulation.json        # per-symbol output
    t7_live_simulation_report.md     # per-slice human-readable report
    run.log                          # captured stdout+stderr
  slice_002_*/
    ...
  t7_parallel_<SYM>_<S>_<E>.json     # consolidated, deterministic
```

The consolidated JSON has the same shape as the inner simulator's
`all_results.json` plus three extra fields:

* `n_slices_planned`, `n_slices_succeeded`, `n_slices_failed` — counts.
* `failed_slices: [...]` — empty on a clean run, otherwise one entry
  per failed slice with `index`, `start`, `end`, `returncode`,
  `stdout_path` (where to inspect the captured run.log).
* `slice_manifest: [...]` — sorted by index, lists every planned slice
  for downstream tooling.

The `results` array is sorted by `(candle_time, symbol, kill_zone)` so
the consolidated output is deterministic regardless of which slice
finished first.

### Exit codes

* `0` — every slice exited cleanly.
* `1` — one or more slices failed (consolidated JSON is still written;
  re-run with `--resume` after fixing the cause).
* `2` — argument / planning error (no subprocesses spawned).

### Helper

`scripts/research/t7_parallel_dryrun.sh` is the canonical
dry-run invocation. It's a 4-line shell script that sources `.env` and
calls the wrapper with the canonical 4-month slice plan. Useful as a
copy-paste starting point for new sweeps.

### Recipe — running a full 4-month XAUUSD parallel sim

```bash
# 1) Verify the plan first.
bash scripts/research/t7_parallel_dryrun.sh

# 2) Once happy, drop --dry-run. For a multi-hour run, use bash
#    run_in_background: true via the agent harness so the parent
#    doesn't kill children on early return (memory
#    feedback_long_running_subprocess_pattern.md).
set -a && source .env && set +a
python scripts/simulate_t7_parallel.py \
  --source csv \
  --data-dir data/historical_2026 \
  --start 2026-01-02 --end 2026-04-13 \
  --symbol XAUUSD --slices 12 --budget 30 \
  --output-dir research/t7_parallel_xauusd_2026q1q2

# 3) On partial failure, --resume finishes only the missing slices.
python scripts/simulate_t7_parallel.py \
  --source csv \
  --data-dir data/historical_2026 \
  --start 2026-01-02 --end 2026-04-13 \
  --symbol XAUUSD --slices 12 --budget 30 \
  --output-dir research/t7_parallel_xauusd_2026q1q2 \
  --resume
```

---

## prompt_ab_harness.py — Prompt A/B Harness (L56)

**File:** `prompt_ab_harness.py`
**Default metrics:** `metrics/prompt_ab_default.yaml`
**Tests:** `tests/scripts/test_prompt_ab_harness.py`

### When to use

You have two prompts (the production V3 baseline + a candidate V4 / V5 /
cascade-resurrection variant) and you want to test whether the candidate
performs differently on a fixed fixture set. Use this harness instead of
ad hoc prompt comparisons when you need:

- Pre-registered statistical inference (paired tests, Bonferroni
  correction).
- A realized-R join — i.e., you want to know whether prompt-B's
  CANDIDATE flips translate into actually-better realized R, not just
  more (or fewer) CANDIDATEs.
- Reproducibility under a deterministic mocked engine before paying for
  real-API runs.

### When NOT to use

- One-off prompt sanity checks (<= 5 fixtures): use a small custom JSONL
  fixture file and run this harness in mocked mode.
- Single-prompt simulation across a date range: that's
  `scripts/simulate_t7_live_period.py`.

### CLI reference

```bash
python scripts/research/prompt_ab_harness.py \
    --prompt-a <prompt-a-path> \
    --prompt-b <prompt-b-path> \
    --fixtures <named-set-or-path> \
    --metrics scripts/research/metrics/prompt_ab_default.yaml \
    --output research/<run-id> \
    [--realized-r-join <trade-records-dir-or-all_results.json>] \
    [--seed N] [--live] [--dry-run] [--verbose]
```

#### Inputs

| Flag | Required | What it accepts |
|---|---|---|
| `--prompt-a` / `--prompt-b` | yes | A `.md`/`.txt` (system-only) OR a `.yaml` with `system:` (str) and optional `user_template:` (str with `{{fixture_user}}` substitution). |
| `--fixtures` | yes | Named set: `historical_cands`. Or a path to a custom JSONL file (one JSON per line, must have `label`, `user_message`; `symbol`, `candle_time`, `side_hint`, `expected_decision` optional). |
| `--metrics` | yes | Path to a pre-registered metrics YAML (see `metrics/prompt_ab_default.yaml`). |
| `--output` | yes | Output directory. Created if missing. |
| `--realized-r-join` | no | Path to a `knowledge_base/trade_records/`-style directory OR an `all_results.json`-style file with `r_multiple` per trade. Enables realized-R metrics. |
| `--seed` | no | Mocked-mode determinism seed. Default 1. |
| `--live` | no | Use real Anthropic API. Default OFF (mocked). Wave-1 default. |
| `--dry-run` | no | Print plan and exit; nothing written, no API calls. |

#### Outputs

| File | Contents |
|---|---|
| `results.jsonl` | One row per fixture with `decision_a`, `side_a`, `decision_b`, `side_b`, `realized_r_a`, `realized_r_b`. |
| `metrics_report.json` | Per-metric statistics including `n`, `p_value`, `alpha_raw`, `alpha_bonferroni`, `significant_raw`, `significant_corrected`, `underpowered`. Also `prompt_a/b` sha + `metrics_yaml_path` for reproducibility. |
| `decision_diff.md` | Human-readable side-by-side for diverging fixtures only. |
| `run_metadata.json` | CLI args, prompt SHAs, harness version, fixture count. |

### Pre-registration contract — DO NOT VIOLATE

CLAUDE.md "Prohibited behaviors" #5 bans **post-hoc hypothesis
formation**. This harness's pre-registration contract has TWO layers:

1. **The metrics YAML is committed BEFORE the run.** If you author a new
   metrics pack for an experiment, give it a new filename
   (`prompt_ab_v4_vs_v3.yaml`, `prompt_ab_cascade_resurrection.yaml`,
   etc.) and reference its commit SHA in the run log.

2. **The default `prompt_ab_default.yaml` MUST NOT be edited in place.**
   `tests/scripts/test_prompt_ab_harness.py::test_pre_registration_sentinel`
   pins the exact metrics list and `metrics_set_id`. If you need to add a
   new metric or change a threshold, bump the `metrics_set_id` AND save
   under a new filename — the test failure is intentional.

**Anti-patterns that count as post-hoc fishing:**
- Running the harness, seeing prompt-B has a higher CR than prompt-A,
  then editing the YAML to add a "CR-favorable" metric.
- Tightening `min_sample` from 20 to 10 to flip an "underpowered"
  metric to "significant".
- Removing `bonferroni_corrected: true` from a metric that flipped sign
  under correction.
- Re-running with a different `--seed` and reporting whichever seed
  gives the desired conclusion.

If you catch yourself doing any of the above, STOP — the correct path
is a NEW metrics-pack file with a NEW `metrics_set_id`, dispatched
BEFORE the next harness run.

### Realized-R join contract

The harness joins each fixture's decision to a realized R record by
the tuple `(symbol, normalized_candle_time, side)`:

- `symbol` — uppercase, normalized (`US30_cash` preserved as-is).
- `normalized_candle_time` — fixture timestamp truncated to whole-minute
  UTC. Microsecond precision in trade records is normalized down.
- `side` — `LONG` / `SHORT` from the prompt's emitted `direction` field.
  A side-less fallback key (`*`) lets a side-mismatch lookup still find
  the trade record (a CANDIDATE on the wrong side gets the matched
  trade's R, not None).

**Memory `feedback_walk_level_evidence_not_predictive.md`** — this is
the only metric family that joins decisions to realized outcomes.
Walk-level decision deltas (CR, label flips) are NOT predictive of
realized R. If you draw an inference that "prompt-B is better than
prompt-A" without the realized-R join, that inference is unsound.

### Determinism

- **Mocked mode** (default): pure function of
  `(seed, prompt.sha256, fixture.label)`. Identical prompts produce
  identical decisions; same seed reproduces same run bit-exact.
- **Real-API mode** (`--live`, NOT used in Wave 1): non-determinism
  is unavoidable for `effort=max`. Anthropic does not provide a seed
  parameter for extended thinking budgets. For variance estimation,
  re-run multiple times and report mean ± stddev.

### Future extensibility — batch wrapper seam

The harness's `_real_api_decision()` mirrors the EXACT call signature
used by `src/components/primary_analyzer.py:341` (`_call_claude`). When
the T0.1 batch API client lands, swapping in a batched seam is a
two-line change in `evaluate_pair()` (`_real_api_decision` →
`_batch_real_api_decisions`). No harness logic, metrics math, or
output format needs to change.

### Worked examples

#### Self-test (identical prompts, mocked)

```bash
python scripts/research/prompt_ab_harness.py \
    --prompt-a tests/scripts/fixtures/prompt_ab_test_fixtures.jsonl \
    --prompt-b tests/scripts/fixtures/prompt_ab_test_fixtures.jsonl \
    --fixtures tests/scripts/fixtures/prompt_ab_test_fixtures.jsonl \
    --metrics scripts/research/metrics/prompt_ab_default.yaml \
    --output /tmp/self_test \
    --seed 1
# Expected: zero divergent decisions; all p-values 1.0; all metrics
# significant_corrected=False.
```

#### Real prompt vs candidate (still mocked — Wave 1)

```bash
python scripts/research/prompt_ab_harness.py \
    --prompt-a prompts/v3_baseline.md \
    --prompt-b prompts/v4_candidate.md \
    --fixtures historical_cands \
    --metrics scripts/research/metrics/prompt_ab_default.yaml \
    --realized-r-join knowledge_base/trade_records \
    --output research/v3_v4_paired_run \
    --seed 1
```

The `historical_cands` set rebuilds fixtures from the trade-records
corpus, which means the realized-R join hits ~100% on filled CANDs
(N≈75 XAU + N≈40 fleet). This is the intended Wave 2 dispatch.

### Author a custom metrics pack

If a downstream task (e.g. cascade resurrection) needs a different
metric mix, copy `metrics/prompt_ab_default.yaml` to a new filename,
bump `metrics_set_id`, and edit. The harness reads whatever YAML you
pass via `--metrics`. Do NOT edit the v1 file in place — the
`test_pre_registration_sentinel` will fail and the failure is the
guardrail working as designed.

### Tests

```bash
pytest tests/scripts/test_prompt_ab_harness.py -v
# 20 tests cover: identical prompts → zero diff sanity, McNemar math,
# Bonferroni propagation, realized-R join (incl. microsecond
# normalization), --dry-run, end-to-end main(), pre-registration
# sentinel.
```
