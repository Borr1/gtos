# L55 — Incremental T7 Backtest Engine

Re-evaluates only the candles whose AI-evaluation inputs (or the prompt or the
config-relevant subset) changed since a prior T7 run, then merges fresh results
back onto unchanged ones. Saves ~90% wall clock on iterative prompt work
compared to a full T7 rerun.

This file documents the engine's hashing contract, the config-relevant subset
whitelist, when to use it (and when NOT to), a worked example, and the
``--dry-run`` pattern. Module: ``src.research_infra.incremental_engine``.
CLI: ``scripts/research/simulate_t7_incremental.py``.

---

## When to use vs when to NOT use

### Use this engine when

- You are iterating a **prompt change** (new no-trade reason, reworded
  instruction, additional framework section). The MSO inputs are unchanged
  for every candle, only the AI's answer might differ. → 100% of prior
  candles are re-evaluated, but you skip the deterministic gates +
  pre-AI prescreen on candles whose inputs are stable. The savings come from
  not re-extracting candles, not re-applying gates, and from being able to
  cherry-pick which date ranges to spawn the inner simulator over.
- You are iterating a **whitelisted config knob** (e.g.
  ``gate1.touch_count_reject_threshold``, ``risk.min_rr``). Same shape:
  every candle re-evaluated, but only the changed knob touched.
- You are iterating an **input-side fix** (e.g. fixed an MSO field that
  affected only certain candles). Then *only* those candles bust their
  hash and the rest are reused.

### Do NOT use this engine when

- You are running a **fresh window** (no prior all_results.json). Use
  ``scripts/simulate_t7_parallel.py`` directly. The incremental engine
  needs a baseline.
- You changed something **not in the whitelist**, but you want it to flow
  into the AI's behavior. Either (a) it actually doesn't flow into AI
  behavior — the engine is correct to ignore it; or (b) it does, and you
  must add it to ``CONFIG_RELEVANT_KEYS`` in
  ``src/research_infra/incremental_engine.py`` with a one-line rationale
  comment.
- You changed the **MT5 export**, the candle data itself, or the M15 close
  prices. The engine hashes the recorded MSO from the prior run, NOT the
  raw data the MSO was built from. If the underlying CSV changed but the
  resulting MSO field for a candle happens to match (e.g. swing detection
  is robust to the change), the engine will incorrectly reuse. Re-run the
  full T7 instead.
- You suspect a **hash collision** or a **bug**. Run
  ``scripts/simulate_t7_parallel.py`` for the suspect window, byte-diff
  the merged JSON, and root-cause before trusting the incremental output.

---

## Hashing contract

Three hashes drive the diff:

### 1. `hash_candle_inputs(raw_data: dict) -> str`

A sha256 over a **canonical JSON dump** of a small subset of the candle's
input dict. The subset is the constant
``CANDLE_INPUT_HASH_KEYS = (candle_time, symbol, kill_zone, market_state,
prescreen, bias, bias_source, ob_proximity, candle_close)``.

Properties:
- **Deterministic** across processes and OSes. Keys sorted, no whitespace,
  ``sort_keys=True`` in the dump.
- **Sensitive** to: any change in MSO content (swing list, OB list, FVGs,
  liquidity), the prescreen pass/fail wording, the deterministic D1/H4
  bias, the OB-proximity gate's verdict, the candle close price.
- **INSENSITIVE** to: ``decision``, ``cost``, ``p2a_*`` comparison fields,
  ``l2_passed`` / ``l2_reason``, outcome metadata (``r_realized`` etc),
  free-form ``generated_at`` timestamps, ``debug_*`` blobs. These are
  RESULTS, not inputs. Including them would bust reuse on every prompt
  change.

If a key from ``CANDLE_INPUT_HASH_KEYS`` is **absent** from the record, it
is folded in as the sentinel string ``"<absent>"``. So `bias` set to
`None` and `bias` deleted produce DIFFERENT hashes — the absence is itself
part of the input identity.

### 2. `hash_prompt(prompt_path: str | Path) -> str`

A sha256 over the prompt file's content with **CRLF normalized to LF**
before hashing. A Windows checkout (CRLF) and a Unix checkout (LF) of the
same prompt produce the same hash; otherwise reuse would be permanently
busted on cross-OS workflows.

### 3. `hash_config_subset(config: dict) -> str`

A sha256 over a hand-curated whitelist of agent_config.yaml dotted keys.
Edits to ANY key in ``CONFIG_RELEVANT_KEYS`` bust reuse. Edits to keys
NOT in that list (telegram, monitoring port, retrieval cache size, etc.)
are silently ignored.

---

## Config-relevant subset whitelist

Defined in ``src/research_infra/incremental_engine.py`` as the
``CONFIG_RELEVANT_KEYS`` tuple. Each key is annotated inline; this section
groups them for review.

### Model identity & sampling

| Key                          | Why it matters                                  |
|------------------------------|-------------------------------------------------|
| `ai.primary_model`           | Which Sonnet/Opus checkpoint the gate calls     |
| `ai.primary_effort`          | min/max effort changes the answer               |
| `ai.api_timeout_seconds`     | Too-short timeout = systematic empty answers    |

### Framework selection (changes prompt + L2 path)

| Key                                  | Why it matters                  |
|--------------------------------------|---------------------------------|
| `model_a.enabled_frameworks`         | Adds/removes prompt sections    |
| `model_a.bias_timeframes`            | Bias-derivation TFs             |
| `model_a.setup_timeframe`            | Setup TF                        |
| `model_a.entry_timeframe`            | Entry TF                        |
| `model_a.ote_zone_fib_top`           | Quoted in prompt                |
| `model_a.ote_zone_fib_bottom`        | Quoted in prompt                |
| `model_a.displacement_min_ratio`     | Affects displacement detection  |
| `model_a.equal_level_tolerance`      | Affects liquidity-pool detection|

### Prompt-level substitutions (`build_system_prompt`)

| Key                                    | Why it matters             |
|----------------------------------------|----------------------------|
| `market.symbol`                        | Per-instrument prompt slug |
| `market.kill_zones`                    | KZ display block in prompt |
| `prompt.zone_width_max`                | Prompt-quoted threshold    |
| `prompt.ob_buffer`                     | Prompt-quoted buffer       |
| `prompt.price_format`                  | Decimal-place directive    |
| `risk.sl_absolute_min`                 | Quoted as SL minimum       |
| `risk.sl_buffer_atr_multiplier`        | Substituted into prompt    |
| `risk.sl_buffer_breaker_atr_multiplier`| Substituted into prompt    |
| `risk.sl_buffer_min_ticks`             | Substituted into prompt    |

### Pre-AI gates (run BEFORE the AI call)

| Key                                              | Why it matters                          |
|--------------------------------------------------|-----------------------------------------|
| `filters.max_gap_pct`                            | OB-gap prescreen verdict                |
| `skip_first_ny_candle`                           | 13:00 NY skip                           |
| `session_memory_enabled`                         | Adds prior-candle context               |
| `confidence_filter_mode`                         | Shadow vs active                        |
| `cross_instrument_context_disabled_for`          | XAU bleed control                       |
| `cross_instrument_context.correlation_gate_threshold` | Block-gate threshold                |
| `market_state.detector_version`                  | v1 vs v2 vs v2_shadow swings            |

### Post-AI gates that change the recorded decision

| Key                                              | Why it matters                          |
|--------------------------------------------------|-----------------------------------------|
| `verification.enabled`                           | L2 layer on/off                         |
| `verification.ob_price_tolerance_pct`            | OB-match tolerance                      |
| `verification.strict_zone_check`                 | WARN vs FAIL                            |
| `verification.sl_beyond_ob_tick_floor`           | ADR-006 tolerance tier                  |
| `verification.sl_beyond_ob_tolerance_enabled`    | Rollback flag                           |
| `gate1.touch_count_reject_threshold`             | ADR-005 touch-count reject              |
| `gate1.ob_retest_sl_exception`                   | Bypass sl_floor when SL at OB boundary  |
| `gate1.ob_retest_sl_min_buffer_atr`              | Min SL distance beyond OB               |
| `gate1.sl_liquidity_cluster_enabled`             | Pool-clearance reject                   |
| `gate1.sl_liquidity_cluster_margin_atr`          | Pool-clearance margin                   |
| `risk.min_rr`                                    | Inverted-TP geometry uses this          |
| `drawdown_reduction.min_rr`                      | Active when DD-mode set                 |

### Adding a new key

Open ``src/research_infra/incremental_engine.py`` and add the dotted-path
string to the ``CONFIG_RELEVANT_KEYS`` tuple. Keep this list tight:
false-positives (key in list, doesn't actually flow into AI) cost ~$30 per
full unnecessary rerun; false-negatives (key NOT in list, but does flow
into AI) cause stale results to sneak through.

The acceptance bar is: demonstrate that flipping the key changes either
the **system prompt content**, the **user-message content**, the
**model identity**, a **deterministic gate that runs before the AI**, or
the **decision recorded in the result** (e.g. an L2 gate that overrides
the AI's answer).

---

## Worked example — prompt iteration loop

Day 0, full T7 baseline (one-time):

```bash
set -a && source .env && set +a
python scripts/simulate_t7_parallel.py \
  --source csv --data-dir data/historical_2026 \
  --start 2026-01-02 --end 2026-04-13 --symbol XAUUSD \
  --slices 12 --budget 30 \
  --output-dir research/t7_v3_baseline
```

This produces `research/t7_v3_baseline/t7_parallel_XAUUSD_2026-01-02_2026-04-13.json`,
which we treat as the prior for incremental runs. Rename it (or symlink it) to
``all_results.json`` if your tooling expects that name. (The incremental
engine accepts both the parallel-wrapper consolidated shape and the inner
simulator's `all_results.json` shape — both have a ``results`` list.)

Day 1, iterate a prompt change:

```bash
# Edit src/prompts/primary_analyzer_prompt.py — say, add a new
# enumerated NO_TRADE reason.

# Plan the diff first (no API spend).
python scripts/research/simulate_t7_incremental.py \
  --prior-results research/t7_v3_baseline/all_results.json \
  --prompt src/prompts/primary_analyzer_prompt.py \
  --config config/agent_config.yaml \
  --start 2026-01-02 --end 2026-04-13 --symbol XAUUSD \
  --output-dir research/t7_v4_iter1 \
  --dry-run
```

The dry-run output will look like:

```
==============================================================================
INCREMENTAL T7 PLAN
==============================================================================
Total candles in prior   : 1304
Unchanged (will skip)    : 0
Changed (will re-evaluate): 1304
Reuse ratio              : 0.00%
Prompt changed           : True
Config-subset changed    : False
Prior prompt hash        : 5f8c...
Current prompt hash      : 9a2b...
Prior config hash        : c4e1...
Current config hash      : c4e1...
------------------------------------------------------------------------------
Slices                   : 12
  [2026-01-02_2026-01-08] 117 candles
  ...
DRY RUN -- no subprocesses will be spawned. Done.
```

A pure prompt iteration *will* re-evaluate every candle (the AI may answer
differently for any of them). The savings come from:

1. **Dry-run gating**: the plan emits cost expectations *before* a single
   API call, so a typo'd config edit no longer wastes $30.
2. **Slice-aware date ranges**: instead of running the inner sim from
   ``--start 2026-01-02 --end 2026-04-13`` continuously, the changed-candle
   list is grouped into contiguous date runs. Sparse changes (e.g. only
   weekends differ for some reason) produce small slices, not 4-month
   reruns.
3. **Reuse on input-side fixes**: when an MSO field changes for *some*
   candles only (e.g. you fixed swing detection on Tuesdays), only those
   candles bust. Reuse ratio jumps to >90%.

Drop ``--dry-run`` to spawn the inner simulator:

```bash
python scripts/research/simulate_t7_incremental.py \
  --prior-results research/t7_v3_baseline/all_results.json \
  --prompt src/prompts/primary_analyzer_prompt.py \
  --config config/agent_config.yaml \
  --start 2026-01-02 --end 2026-04-13 --symbol XAUUSD \
  --output-dir research/t7_v4_iter1
```

Output layout:

```
research/t7_v4_iter1/
  incremental_plan.json                                # the plan (always)
  incremental_XAUUSD_2026-01-02_2026-04-13.json        # consolidated
  _slices/
    2026-01-02_2026-01-08/
      all_results.json                                  # inner sim output
      run.log                                            # captured stdout/stderr
    2026-01-09_2026-01-15/
      ...
```

The consolidated file has the same shape as the inner sim's
``all_results.json`` PLUS an ``incremental_meta`` block (counts, hashes,
failed-slice list). Each per-candle record gets an
``incremental_source`` tag (``"prior"`` or ``"fresh"``).

---

## Dry-run pattern

Always dry-run before spawning. The CLI guarantees:

1. ``--dry-run`` exits 0 with a parseable plan printed to stdout.
2. ``--dry-run`` does NOT call ``subprocess.run`` (verified in tests).
3. ``--dry-run`` writes ``incremental_plan.json`` to ``--output-dir`` so
   the plan can be diffed across iterations.

If the plan reports ``reuse_ratio: 100.00%``, your edit is a no-op as far
as the engine can tell; either the engine is missing a key in the
whitelist, or the edit truly does not affect AI behavior.

---

## Running this from a Claude Code agent

Per memory `feedback_long_running_subprocess_pattern.md`: agent threads kill
their Python children when they return. The inner T7 simulator can take
several minutes per slice (each slice runs the full deterministic gates +
the AI calls), so a multi-slice incremental run can easily exceed 30 min.

Pattern:
1. Build the plan in the agent (cheap; pure-Python). Print it.
2. If the plan says spawn, dispatch the live run from **Bash with
   `run_in_background: true`** in the MAIN thread. The Bash parent stays
   alive for the children's lifetime.

This script never calls the Anthropic API directly; only the inner T7
simulator does, and only for the slices the plan asked for. Tests
monkeypatch ``subprocess.run`` to a fake — no real spawn happens in CI.

---

## Caveats

### `input_hash` emission gap (Wave 1 known limitation)

`incremental_engine.py:561` reads `record.get("input_hash")` from each prior
record in `all_results.json`. The current `scripts/simulate_t7_live_period.py`
does **NOT** yet emit this field on per-candle records. Consequence: when both
`prompt_changed=False` and `config_changed=False`, the engine treats every
candle as input-unchanged regardless of whether the underlying MSO inputs
actually drifted, and fully reuses the prior result.

**What this means in practice:**
- **Prompt iteration:** works as designed. Change a prompt → all candles get
  re-evaluated. No staleness risk.
- **Config iteration on a whitelisted key:** works as designed. Change e.g.
  `gate1.touch_count_reject_threshold` → re-evaluation triggered for all
  candles touching that gate.
- **Pure data-input drift** (e.g. you re-extract historical MT5 data with
  fresh ticks, regenerating MSO inputs without changing prompt or config):
  the engine cannot detect the drift today. It will reuse the prior
  evaluation. **Do a full T7 rerun** in this case until the inner simulator
  emits `input_hash`.

**Follow-up to close the gap:** add a one-line `record["input_hash"] =
hash_candle_inputs(record)` to `simulate_t7_live_period.py` where it builds
the per-candle result dict. Intentionally not done in L55 because the brief
forbade modifying `simulate_t7_live_period.py`. Track as a Phase 1 follow-up.

---

## See also

- ``scripts/simulate_t7_live_period.py`` — inner T7 simulator (production-faithful)
- ``scripts/simulate_t7_parallel.py`` — L54 parallel wrapper (12-slice canonical)
- ``src/research_infra/cache_helper.py`` — T0.3 1h-TTL cache (separate concern)
- ``src/research_infra/cost_tracker.py`` — T0.2 cost tracker (no AI calls here, but if you wire fresh-cost reporting through it later, route via `CostTracker.record(...)`)
