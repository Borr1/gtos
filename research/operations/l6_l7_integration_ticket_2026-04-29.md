# L-6 + L-7 Logger Integration Ticket (B-8 Phase 4 deliverable handoff)

**Filed:** 2026-04-29 (post B-8 dispatch close)
**Source:** `research/ml_program/experiments/l6_l7_logger_design.md` (361-line design doc, B-8 deliverable)
**Status:** AWAITING MAIN-THREAD INTEGRATION
**CEO approval:** 2026-04-29 Day-2 sync (recorded in dispatch_log.md and conversation 2026-04-29)
**Owner:** Main-thread engineer (post-Q1.4 K54 v3 modeler dispatch close)

## TL;DR

Two observability hooks are designed and unit-tested but NOT integrated into production. The B-8 design dispatch produced ready-to-apply reference impls + integration line counts.

- **L-6:** HALLUC-2 token-usage logger. Per-API-call grain (not per-evaluation). Captures `{cost, latency, role, call_id, prompt_hash, served_model_id, response_id, backend_mode, cache_ttl}`. Currently NOT shipped — only partial coverage via `evaluation_logger`'s `usage` block per evaluation row.
- **L-7 extension:** Q71 close-side slippage telemetry. The entry-side L-7 (`src/components/slippage_shadow_logger.py`) IS already shipped (commit `6b049ab`); this ticket extends it with `record_close_slippage` API + 9 close-side fields + `event` discriminator.

## Why L-6 first

- HALLUC-1 NAS100 93% precision-bug class was deterministic (memory `project_halluc_1_precision_bug_class_2026-04-27`). Without L-6, we have no per-call cost-attribution + no cache-hit-rate analytics to drive tool-grounding (L-1) work.
- Pre-requisite for cost optimization measurement.
- Smaller (~12 LOC), single file, lower-risk.

## Why L-7 close-side extension is valuable

- Production has 1 row in `shadow_logs/slippage.jsonl` (the GBPJPY 2026-04-28 force-closed trade, `fill_price=0.0` broker quirk per memory `project_2026-04-29_post_deploy_watchlist`). Most April CANDIDATEs entered as pending limits and never filled, so no `record_slippage` fires.
- Once limit-fill cadence increases, entry-side rows accumulate. But CLOSE-SIDE slippage (SL fills, TP1 partials, BE moves, J46-J49 time-stops, force-closes) is currently NOT logged anywhere.
- Q71 spec needs both ends.

## Integration line counts

### L-6 (HALLUC-2 token-usage)

**File:** `src/components/primary_analyzer.py`
- Init at line ~117 (1 LOC).
- `_call_claude` API success path lines 397/408 (2 LOC).
- `_call_claude` failure branches lines 421-444 (~5 LOC for try/except wrap with timing).
- `_call_claude_subscription` success path lines 459/472 (2 LOC).

**TOTAL: ~12 LOC, single file.** Zero LOC change in `src/components/orchestrator.py`. Reuse `src/research_infra/cost_tracker.compute_cost` for pricing math.

### L-7 close-side extension

**File 1:** `src/components/slippage_shadow_logger.py`
- Extend `record_slippage` signature with 9 new entry-side fields (~10 LOC).
- Add new `record_close_slippage` sibling function (~40 LOC) with `event` discriminator.

**File 2:** `src/components/execution.py`
- Extend existing entry-side call at line 502 with 5 added args (~5 LOC).
- Add 5 new close-side calls:
  - Line 840 (TP1 partial fill).
  - Lines 869, 916, 953, 1005 (BE moves; 4 sites).
  - Lines 1022-1062 (full close in `close_position`; 1 site).

**TOTAL across both files: ~50-60 LOC.**

## Reference impls (committed; main-thread can copy)

- `research/ml_program/experiments/l6_token_usage_logger.py` (~310 LOC + 12 unit tests; all passing).
- `research/ml_program/experiments/l7_slippage_logger.py` (~360 LOC + 11 unit tests; all passing; backward-compat verified vs historical 1-row).

Run tests:
```bash
cd C:/Users/MSI/Documents/ai-trading-agent
python -m pytest research/ml_program/experiments/l6_token_usage_logger.py -v
python -m pytest research/ml_program/experiments/l7_slippage_logger.py -v
```
Both should report 12 + 11 = 23 passing.

## Final schemas

### L-6 schema (per-API-call grain)

```json
{
  "timestamp": "ISO-8601 UTC",
  "call_id": "uuid",
  "symbol": "XAUUSD",
  "kill_zone": "london | ny | tokyo | none",
  "candle_time": "M15 close timestamp",
  "model": "claude-sonnet-4-6",
  "primary_effort": "max",
  "role": "primary_analyzer | confidence_filter | etc.",
  "attempt": 1,
  "input_tokens": 12345,
  "cache_read_tokens": 11000,
  "cache_creation_tokens": 0,
  "output_tokens": 567,
  "cache_ttl": "5m | 1h",
  "is_batch": false,
  "cost_usd_breakdown": {"input": 0.001, "cache_read": 0.0001, "output": 0.0085},
  "total_cost_usd": 0.0096,
  "latency_ms": 1250,
  "prompt_hash": "sha256-prefix",
  "served_model_id": "claude-sonnet-4-6-20251022",
  "response_id": "msg_abc",
  "backend_mode": "api | subscription",
  "outcome": "ok | timeout | error",
  "exception_class": null,
  "notes": ""
}
```

### L-7 extension (preserves all 13 existing entry-side fields; adds 9 entry + 17 close)

- **Entry-side new:** `event="entry_fill"`, `expected_sl`, `expected_tp1`, `slippage_pct_atr`, `fill_type`, `broker_state`, `mt5_retcode`, `request_volume`, `realized_volume`.
- **Close-side new:** `event ∈ {"sl_fill", "tp1_partial_fill", "tp2_full_fill", "be_close", "j46_j49_time_stop", "manual_close", "force_close", "sl_modification_failed"}`, plus 17 close-side fields (expected vs realized close prices, signed slippage, `entry_ticket` join key, `time_in_trade_sec`, etc.).

## Edge cases handled (23 unit tests, all passing)

**L-6:** cache hits ($0 marginal cost rows), cache misses (1h cache_write rate), retries with distinct call_ids, subscription mode (cost=0), unknown model (no crash, notes carries error), prompt-hash stability for cache-debug, fail-open on disk errors.

**L-7:** limit-fill (existing `trigger="limit_fill"` flow), broker `OrderResult.price=0.0` (logged verbatim plus production tick fallback at execution.py:454), partial fills via multiple `record_close_slippage` calls per trade joined by `entry_ticket`, J46-J49 time-stop closes, SL-modification-failure forced closes, unknown direction (null directional), historical 1-row backward-compat replay.

## Open caveat (out-of-scope follow-up)

Orchestrator-recovery close paths (state-machine restart mid-close) bypass `close_position` and would miss the close-side log. Flagged in design §7.1; design doc proposes idempotent close-fill detection via ticket polling on orchestrator restart but defers implementation.

## Recommended order of operations

1. **L-6 first** (smaller, single-file, lower-risk, prerequisite for cost analytics).
2. **L-7 close-side extension** (multi-site; verify each TP1/BE/close path with smoke trade in DRY-RUN before live).
3. **Smoke test:** trigger one canary trade through entry → BE move → TP1 partial → close, verify all 4-5 expected rows appear in `shadow_logs/slippage.jsonl`.

## WF-1 compliance

- Production code modification requires CEO approval per CLAUDE.md WF-1 discipline.
- This ticket records CEO approval (2026-04-29 Day-2 sync).
- Both files (`primary_analyzer.py` + `slippage_shadow_logger.py` + `execution.py`) are within the "trading logic / evaluation behavior" scope; the logger hooks are observation-only and additive (no decision impact), but main-thread engineer should still smoke-test in DRY-RUN before live.

---

*Ticket end. Main thread: claim when ready; close by linking the integration commit and the smoke-test verification.*
