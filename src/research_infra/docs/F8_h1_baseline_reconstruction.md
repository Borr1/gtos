# F8 — H1 baseline reconstruction from agent_*.log files

This module-adjacent doc covers the F8 reconstruction pipeline:

* `scripts/research/reconstruct_h1_evaluations.py` — parser + writer
* `tests/scripts/test_reconstruct_h1_evaluations.py` — 12 tests
* B7 module additions (`PeriodStrategy`, `_assign_period(strategy=...)`,
  `measure_from_disk(extra_live_evaluations_dirs=..., period_strategy=...)`)
* `research/ai_behavior/B7_hallucination_h1_h2_delta/` — re-run output

## Purpose

B7 (commit `9611c58`) computed AI hallucination rates over the
April-2026 corpus that lives in `knowledge_base/live_evaluations/` and
`knowledge_base/trade_records/`. Both directories start at 2026-04-06.
The H1→H2 hallucination delta needed by the K54 handoff cannot be
computed without an earlier baseline.

F8's mandate was to extract the missing baseline from the production
agent logs (`logs/agent_*.log`). Empirically, the agent logs span only
**2026-04-05 to 2026-04-27** — there is **no pre-April 2026 evaluation
data on disk**. F8 still produces a meaningful baseline by:

1. Parsing structured event lines from `knowledge_base/logs/agent_*_demo.log`
   (and `logs/agent_*.log` if present on the host).
2. Reconstructing partial evaluation records and writing them to
   `knowledge_base/live_evaluations_h1_reconstructed/{SYMBOL}/{DATE}.jsonl`.
3. Splitting April into "H1" (Apr 5-15) vs "H2" (Apr 16-27) via a new
   `period_strategy="intra_april_2026"` parameter on the B7 measurement
   pipeline.

## Log format assumptions

Each agent log line has the shape:

```
YYYY-MM-DD HH:MM:SS,mmm LEVEL [logger.name] message...
```

Multi-line tracebacks ARE allowed; continuation lines without the
prefix shape are silently skipped (no parse error). The parser
recognizes the following structured events as one-of-line "facts" that
attach to the currently-open evaluation cycle:

| Event line | Captured |
|---|---|
| `Processing candle - <KZ> KZ` | Begins a new cycle; flushes the previous one |
| `Align score: <s>/<t> <bias> ...` | `align_score`, `align_total`, fallback `daily_bias_direction` |
| `Deterministic bias: <bias> (source=<src>)` | `daily_bias_direction`, `daily_bias_source` |
| `Pre-screen FAILED: <reason>` | `pre_screen_fail` |
| `Pre-AI gate skip: <reason>` | `pre_ai_skip` |
| `POST https://api.anthropic.com/v1/messages "HTTP/1.1 <status>"` | `ai_called=True`, `ai_http_status` |
| `Malformed response - retrying` | `malformed_responses` += 1 |
| `TP1 placement warning: ... (entry=X, SL=Y, TP1=Z)` | `entry_price`, `stop_loss`, `take_profit_1` |
| `Displacement ratio mismatch: AI=X MSO=Y` | `displacement_ai`, `displacement_mso` |
| `L2 verification FAILED: <rule> - SL X is NOT (below|above) OB (low|high) Y` | `l2_fail_rule`, `l2_sl_value`, `l2_ob_value` |
| `PROXIMITY_SHADOW: ... proximity=X dist_atr=Y` | `proximity`, `dist_atr` |
| `Confidence: grade=X price_levels=N hesitation=N multiplier=M` | `confidence_grade`, `confidence_multiplier`, `confidence_price_levels` |
| `Trade record saved: .../<SYMBOL>/<filename>` | `trade_record_path` (provenance link) |

A cycle is flushed at the next `Processing candle` line OR end-of-file.
Cycles with no useful signal (only bootstrap/teardown lines, no AI
call, no pre-screen verdict, no proximity event) are FILTERED OUT.

## Reconstruction methodology

### Schema mapping (reconstructed -> live_evaluations)

The reconstructed JSONL keeps the same flat shape as `live_evaluations/`
records. Fields the canonical corpus has but the log doesn't surface
are emitted as `null`:

| Field | Source | Notes |
|---|---|---|
| `timestamp` / `candle_time` | "Processing candle" line timestamp, truncated to whole-minute UTC | |
| `symbol` | log filename stem | Canonicalized via `_extract_symbol_from_filename` |
| `kill_zone` | "Processing candle" line capture group | Lower-case ('london'/'ny'/'tokyo') |
| `decision` | derived | CANDIDATE if entry+SL surfaced; NO_TRADE if AI called or pre-screen fail; UNKNOWN otherwise |
| `daily_bias_direction` | "Deterministic bias:" line, fallback "Align score:" line | "transitional" → "ranging" to match v1 labels |
| `daily_bias_confidence` | NOT IN LOGS | `null` |
| `h4_aligned` | NOT IN LOGS | `null` |
| `h1_poi_identified` | derived (false if `pre_ai_skip == 'no_unmitigated_h1_pois'`) | `null` otherwise |
| `m15_displacement_ratio` | "Displacement ratio mismatch:" AI side | 0.0 when no displacement event |
| `align_score` | "Align score:" line | |
| `no_trade_reason` | First non-null of: `pre_screen_fail`, `pre_ai_skip`, `l2_fail_rule` | |
| `overall_reasoning` | **synthesized** | See below |
| `record_source` | constant `"agent_log_reconstructed"` | F8-only field |
| `log_file` | log filename | F8-only field for provenance |
| `reconstructed_*` | various | F8-only debug fields preserving raw extracts |

### Synthesized `overall_reasoning`

To make the reconstructed records compatible with B7's downstream
parser (`_extract_text_prices` in `hallucination_measurement.py`), we
embed AI-cited prices in a synthetic free-text string. Format:

```
Reconstructed from agent log. Price at <ENTRY>. SL placed at <STOP>. TP1 at <TARGET>. L2 verification noted SL <X> relative to OB at <Y>-<Y>. Displacement AI=<X> MSO=<Y>. Proximity dist_atr=<X>.
```

The "Price at X" / "SL placed at X" / "TP1 at X" patterns match the
existing B7 EXPLANATION_PATTERNS regex rules — so the reconstructed
reasoning text feeds directly into the same hallucination
classification pipeline as canonical records, without modifying the
B7 parser. The only B7-side change is wiring the new corpus dir
through `extra_live_evaluations_dirs`.

### Dedup

Records that already exist in canonical `live_evaluations/` are
skipped. Dedup key is `(symbol, candle_time_iso_minute_utc)`. This
suppresses double-counting when a log entry covers a candle that the
canonical pipeline already logged.

In the F8 production run (Apr 27, 2026), the parser found 2,098
candle-cycle starts in the logs, of which 1,435 were emitted, 165
were deduped against canonical records, and 498 were filtered as
no-useful-signal cycles.

### Window filter

The `--start` / `--end` flags filter cycles by **timestamp**. The
default is `2026-01-01` to `2026-04-05` per the F8 brief — this would
emit ONLY pre-April-6 records (the gap between log start and canonical
corpus start). For the post-merge B7 re-run, the F8 production run
used `--start 2026-01-01 --end 2026-04-30` to fold ALL log-derived
data into the corpus (the dedup pass then filters anything canonical
already has).

## Schema divergence vs canonical `live_evaluations`

1. **`record_source`**: reconstructed records carry
   `"agent_log_reconstructed"`; canonical records have no such field
   (the field defaults to None when reading canonical JSONL through
   `_iter_live_evaluations`).
2. **Log-only fields**: many canonical fields (`daily_bias_confidence`,
   `h4_aligned`, `setup_grade`, `confidence_score`, `framework`,
   `session_memory_count`, `spread`, `candle_index_in_kz`, etc.) are
   `null` in reconstructed records.
3. **`reconstructed_*` debug fields**: the reconstructed records carry
   extra fields prefixed `reconstructed_` (entry_price, stop_loss,
   take_profit_1, displacement_ai, displacement_mso, l2_fail_rule,
   proximity, dist_atr, confidence_grade, etc.). These are
   debug-provenance only — B7 ignores them. They let downstream
   forensic code reconstruct the raw events.

## B7 module integration

The B7 module (`src/research_infra/hallucination_measurement.py`) was
modified surgically:

1. Added `PeriodStrategy` literal type and `DEFAULT_PERIOD_STRATEGY`
   constant.
2. Added `strategy` keyword arg to `_assign_period`. Default behavior
   is unchanged (calendar-half).
3. Added `period_strategy` keyword arg to `_check_trade_record`,
   `_check_live_evaluation`, `measure_hallucination_rate`, and
   `measure_from_disk`. All default to calendar-half so existing
   callers (B7 standard run) see no change.
4. Added `extra_live_evaluations_dirs` keyword arg to
   `measure_from_disk`. Default is empty tuple.

The CLI driver (`scripts/research/run_b7_hallucination.py`) gained:

* `--extra-live-evaluations-dir <path>` (repeatable)
* `--period-strategy {calendar_half,intra_april_2026}`

All existing B7 tests (`tests/research_infra/test_hallucination_measurement.py`)
continue to pass after these additions (verified 20/20 green).

## How to re-run

```bash
# 1. Regenerate the reconstructed corpus from current logs
python scripts/research/reconstruct_h1_evaluations.py \
    --logs-dir C:/Users/MSI/Documents/ai-trading-agent/knowledge_base/logs \
    --output knowledge_base/live_evaluations_h1_reconstructed \
    --start 2026-01-01 --end 2026-04-30

# 2. Re-run B7 with the F8 split
python scripts/research/run_b7_hallucination.py \
    --output-dir research/ai_behavior/B7_hallucination_h1_h2_delta \
    --extra-live-evaluations-dir knowledge_base/live_evaluations_h1_reconstructed \
    --period-strategy intra_april_2026
```

The `F8_VERDICT.md` overlay in the output dir is a manually-curated
narrative complementing the auto-generated `report.md`.

## Limitations / open questions

1. **No pre-Apr 5 data on disk.** The F8 brief assumed agent_*.log
   files would carry Jan-Mar 2026 traces. They do not. The reconstruction
   only adds Apr 5 (one day pre-canonical) plus mid-cycle events that
   live_evaluations dropped. The H1->H2 split is therefore intra-April
   (5-15 vs 16-27), not calendar half-year.
2. **Coarse classification arm.** Reconstructed records lack the
   role-tagged MSO that `trade_records/` carries. B7 falls back to the
   OHLCV-window stand-in (~7 days of H1 candles), which collapses the
   ACCURATE/MISATTRIBUTED distinction — the reconstructed arm only
   emits ACCURATE / HALLUCINATED, never MISATTRIBUTED.
3. **AI-emitted prices are partial.** Only entry/SL/TP1 + displacement
   AI/MSO + L2 SL/OB values are logged. The richer set captured in
   `trade_records/` (poi_price_level, protected_swing_level,
   sweep_price, the explanation paragraph, etc.) is not in the logs.
   So per-role hallucination rates from reconstructed records are
   biased toward those four roles.
4. **Decision derivation is heuristic.** The canonical decision field
   lives in the AI response JSON which is not logged. The
   reconstruction labels TP1-emitted cycles as CANDIDATE; this may
   over-count CANDIDATEs that the canonical pipeline ultimately
   classified NO_TRADE after L2 rejection.

For follow-ups see the F8 verdict file
(`research/ai_behavior/B7_hallucination_h1_h2_delta/F8_VERDICT.md`).
