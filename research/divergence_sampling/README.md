# Divergence classification weekly sampler

This directory holds the weekly classification batches used to decide
whether `market_state.detector_version` can be promoted from `v2_shadow`
(current live state since 2026-04-24) to `v2` (production).

## What lives here

- `week_YYYY-WW.md` — one markdown file per ISO week, each with ~25
  divergences sampled from `shadow_logs/structure_detector_divergences.jsonl`.
  Each sample shows the v1 vs v2 detector labels, the score/dead_zone
  metadata, and a 50-candle window-context snippet. The CEO ticks one of
  four classification checkboxes per sample.
- `SUMMARY.md` — optional aggregated report produced by
  `python scripts/divergence_classification_summary.py --output research/divergence_sampling/SUMMARY.md`.

## How you use this directory

Every Monday morning a new `week_YYYY-WW.md` file appears (automated
Task Scheduler job — see `scripts/install_divergence_sampler_task.ps1`).
To process the week:

1. Open the new `week_YYYY-WW.md` in your editor.
2. For each `## Sample N` block, read the v1/v2 labels and the window
   context. Decide which option is right:
   - **v1 correct** — the v1 bullish call was the right read.
   - **v2 correct** — the v2 bearish/transitional call was the right read.
   - **both wrong** — neither label matches what actually happened;
     should have been transitional/ranging.
   - **ambiguous** — genuinely could go either way, no clean call.
3. Change exactly one `- [ ]` to `- [x]` for each sample. If you are
   unsure, mark `ambiguous` — it's an explicit "can't decide" bucket and
   does NOT hurt the v2-correct rate (ambiguous is excluded from the
   denominator).
4. `git add research/divergence_sampling/week_YYYY-WW.md && git commit`.

Each classification takes ~30 seconds with the rendered context. A full
weekly batch (~25 samples) should take ~12 minutes.

## Checking progress toward v2 promotion

Run this any time:

```
python scripts/divergence_classification_summary.py
```

Or write to a persistent file:

```
python scripts/divergence_classification_summary.py --output research/divergence_sampling/SUMMARY.md
```

The output shows:

- Total classifications to date.
- Per-outcome counts (v1_correct / v2_correct / both_wrong / ambiguous).
- Per-instrument and per-timeframe breakdowns.
- Overall v2-correct rate (ambiguous excluded).
- A **READY / NOT READY** verdict for the promotion gate.

## Promotion gate criteria

From ADR-004 §7.3 + session 38 handoff:

1. ≥100 manually-classified divergences total.
2. ≥80% overall v2-correct rate (v2_correct / (v2_correct + v1_correct + both_wrong)).
3. ≥60% v2-correct rate per instrument with any decisive classifications
   (symmetry floor — guards against one bad instrument dragging the
   overall rate up while another silently regresses).
4. ≥14 days of live v2_shadow data (tracked via the logged_at spread in
   the shadow log, not by this aggregator).
5. No production regression observed in live fleet metrics (tracked
   separately via `scripts/ob_continuation_monitor.py` and the usual
   shadow loggers).

When the aggregator prints `Status: READY`, summon the `v2_cutover` agent
(or dispatch a new one) to:

- Flip `config/agent_config.yaml` → `market_state.detector_version: v2`.
- Commit + rolling restart the fleet.
- Announce on Telegram.

## Limitations

- The sampler filters on `mode == "shadow"` — the F3 backtest rows with
  `mode: "live_v2"` (~4976 historical rows) are deliberately excluded;
  they are not production observations.
- Window context uses `data/historical_2026/{SYMBOL}_{TF}.csv` which was
  exported for Jan 2 – Apr 10 2026. For divergences on dates outside
  this range, the "no window context" fallback renders. Future
  refresh of this CSV is out of scope for the sampler.
- `logged_at` cutoff advances to the max of the loaded pool, not the
  max of the sampled batch. Rows that miss a stratum cut stay
  unclassified forever. With 25/week over ~14+ weeks this is not a
  correctness problem — we only need 100 classifications total, not
  100% coverage.
