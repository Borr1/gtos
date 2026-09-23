# Phase A — Trade Record Recon

**Session 39 / A3 — Trade Record Instrumentation**

## 1. Current write path

`src/components/trade_capture.py`:

- `create_trade_record(symbol, kill_zone, candle_time, mso, prompt_system, prompt_user, ai_response, cross_instrument_context, session_memory, config)` — builds the initial dict at CANDIDATE time. Stored in-memory until a persistence event.
- `update_verification(record, verification_result)` — appends L2 check details.
- `update_gate_results(record, gate3_result, gate1_result)` — appends gate results.
- `update_execution(record, execution_data)` — **imported by orchestrator but never called**. No entry-fill capture wiring today.
- `update_exit(record, exit_data)` — appended at `_finalize_exit` (orchestrator.py:1668+).
- `save_trade_record(record, base_path)` — atomic write to `{base_path}/{symbol}/{date}_{kz}_{hhmm}.json`.

## 2. Current schema (from `src/components/trade_capture.py::create_trade_record`)

```
{
  "metadata": { trade_id, date, symbol, kill_zone, candle_time, capture_version, system_version },
  "decision_pipeline": {
    ai_decision, ai_grade, ai_confidence, ai_direction, ai_framework,
    level2_verification: { passed, checks[], blocked_by },
    gate3_result: { passed, checks_run, details },
    gate1_result: { passed, checks_run, details },
    final_outcome,
  },
  "context_at_decision": { cross_instrument_context, session_memory },
  "mso": {...},                  # full MarketStateObject dump
  "prompt": { system_prompt, user_message },
  "ai_response": {...},          # raw AI JSON response
  "trade_parameters": {...},     # direction, entry, sl, tp1-3, sl_buffer_applied, rr, size
  "execution": null,             # NEVER populated today (update_execution unused)
  "exit": null,                  # populated at _finalize_exit
  "shadow_data": {               # orchestrator.py:799+ enrichment (CAND time)
    session_memory_count, align_score, spread_at_entry, candle_index_in_kz,
    h1_poi_type, h1_fib_pct, h1_causing_event, h1_zone,
    sweep_detected, sweep_type,
    m15_displacement_quality, m15_displacement_ratio,
  },
  "shadow": {                    # orchestrator.py various enrichments
    proximity, be_shadow, time_in_trade, partial_close, ...
  },
  "limit_intent": {              # orchestrator.py:1061+ (LIMIT_PLACED path)
    trade_id, limit_price, stop_loss, take_profit_1, expiry_candles,
  },
}
```

### Exit dict (when populated by `_finalize_exit`):

```
{ exit_type, exit_price, exit_time, actual_r, hold_time_minutes,
  mfe_price, mfe_r, mae_price, mae_r, partial_closes[] }
```

Plus M5 excursion keys: `mfe_r_m5`, `mae_r_m5`, `mfe_time_minutes`, `mae_time_minutes`.

## 3. Data source mapping for new fields

| Target field | Source | Where reachable at CAND time |
|---|---|---|
| `target_ob_touch_count` | `matched_ob.touch_count` from `verification._find_matching_ob` | Need to surface `matched_ob` on `VerificationResult`. Populated on every H1 OB in MSO via `market_state.py:1013-1016` (`_count_touches`). |
| `m5_refined` | `m5_out["applied"]` in orchestrator.py:922 | Populated after 6c block; currently only persisted to `pipeline_state/m5_refinement.json` (overwritten per candle). |
| `m5_refinement_details` | `m5_out["overrides"]` | Same place; contains `m5_quality`, `m5_raw_sl_dist`, `sl_distance`, `take_profit_1`, etc. |
| `sl_source` | Decision on whether OB structural SL exception applied + presence of ATR floor override | `permissions.py:_ob_retest_sl_exception_applies()` returns bool; rationalize from `analysis.framework == "ob_retest"` + gate decision path. For CAND we emit `"ob"` (ob_retest structural), `"atr_fallback"` (when floor clamped), `"structural"` (generic swing), `"unknown"` default. Simplest: read from `analysis.framework` + post-clamp inspection. |
| `sl_buffer_applied` | `analysis.trade_parameters.sl_buffer_applied` | Already in `trade_parameters`; add alias at top level for Phase 2 query convenience. |
| `h1_fvg_unfilled_count` | `sum(1 for fvg in mso.timeframes["H1"].fair_value_gaps if not fvg.filled)` | MSO structure. |
| `m15_fvg_unfilled_count` | Same over M15. | MSO structure. |
| `h1_opp_ob_touch` | Find nearest OPPOSING-direction H1 OB to AI entry; return its `touch_count`. | MSO structure. |
| `detector_version_at_eval` | `config["market_state"]["detector_version"]` or direct config get | config lookup. |
| `kill_zone_bucket_15min` | Derived from `candle_time`: `{kz}_{HHMM}` e.g. `london_0715`. | Trivially derivable in `create_trade_record` once we accept `kill_zone` and `candle_time`. |
| `realized_R` | existing `exit.actual_r` | Add canonical alias `realized_R` at top level + in `exit`. |
| `time_in_trade_minutes` | existing `exit.hold_time_minutes` | Alias. |
| `exit_reason` | `exit_type` mapped to canonical enum | New enum `TP1/TP2/SL/BE/TIMEOUT/MANUAL` derived from `exit_type`. |

## 4. Missing fields vs target

All 13 target fields are unpopulated today. Specifically:

1. `target_ob_touch_count` — **unreachable** (MSO has `touch_count` on each OB but `_find_matching_ob` discards the match beyond the local verification check).
2. `m5_refined` / `m5_refinement_details` — **unreachable** (pipeline_state overwritten).
3. `sl_source` — **never emitted**.
4. `sl_buffer_applied` — **reachable** (already in `trade_parameters`) but not surfaced at top level for easy Phase 2 query.
5. `h1_fvg_unfilled_count` / `m15_fvg_unfilled_count` — **reachable** (MSO) but not emitted.
6. `h1_opp_ob_touch` — **reachable** (MSO) but not emitted.
7. `detector_version_at_eval` — **reachable** (config) but not snapshot.
8. `kill_zone_bucket_15min` — **reachable** (candle_time) but not emitted.
9. `realized_R` — **reachable** (as `actual_r`) but no canonical top-level alias.
10. `time_in_trade_minutes` — same.
11. `exit_reason` — **reachable** (as `exit_type`) but no canonical enum normalization.

## 5. Persistence points

Orchestrator `save_trade_record` calls (per grep):

- Line 880 (REJECTED_L2)
- Line 937 (REJECTED_L2_POST_M5)
- Line 965 (SKIP_NEWS_EVENT / BLOCKED_CALENDAR)
- Line 989 (REJECTED GATE fail)
- Line 1017 (SKIPPED_CORRELATION)
- Line 1071 (LIMIT_PLACED — **canonical** — stores path in `_pending_trade_record_path`)
- Line 1087 (LIMIT_INTENT_FAILED)
- Line 1822 (FINAL save at `_finalize_exit`)

All go through `create_trade_record` + `update_*` helpers. Minimal invasive approach: enrich `create_trade_record` + add `update_m5_refinement` helper + fix `_finalize_exit` to map `exit_type` → `exit_reason`.

## 6. Key paths

- `src/components/trade_capture.py` — the only schema authority. Changes here propagate to every persistence call site.
- `src/components/verification.py` — expose `matched_ob` on `VerificationResult` so touch_count flows.
- `src/components/orchestrator.py` — call sites for `create_trade_record`, M5 result capture, `_finalize_exit`.
- `tests/test_trade_capture.py` — existing schema tests; new instrumentation tests live at `tests/components/test_trade_record_instrumentation.py`.

## 7. Backward-compat requirements

- All new fields MUST default to `None` / empty / appropriate nullable, so pre-instrumentation records load without `KeyError`.
- Existing callers (`update_verification`, `update_gate_results`, `update_execution`, `update_exit`) unchanged in signature.
- Existing field types / names unchanged.

## 8. Known blockers for Phase 2 (NOT fixable by A3)

- **FTMO free-trial EA exclusion** means live fills won't materialize until CEO moves to a paid challenge. All 20 existing live records have `execution: None` + `exit: None`. New instrumentation captures fields that WILL populate once fills fire.
- **Retroactive backfill impossible for historical MSO snapshots** — we only have current-state MSOs for live records; re-deriving `touch_count` for Jan-Apr 2026 batch trades would require replaying `_count_touches` against historical H1 windows (possible but out-of-scope for A3).
