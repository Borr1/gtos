# L-6 + L-7 Logger Design — HALLUC-2 Token Usage + Q71 Slippage

**Status:** DESIGN-ONLY (READ-ONLY for `src/`).
**Author:** B-8 dispatch agent (Phase 4 quick-win bundle), 2026-04-29.
**Spec source:** `research/ml_program/MASTER_BACKLOG.md` lines 196 (L-6), 197 (L-7), 242 (O-6), 243 (O-7), 290 (B-5 AI-grounding bundle), 293 (B-8 quick-win bundle).
**Related memories:** `project_halluc_1_precision_bug_class_2026-04-27` (L-6 motivation: token usage is a prerequisite for tool-grounding L-1 work and cost-attribution audit). `project_anthropic_billing_auto_reload_disabled` ($50-60 hard cap → cost telemetry is not optional).
**Reference impls (this dispatch):**
- `research/ml_program/experiments/l6_token_usage_logger.py`
- `research/ml_program/experiments/l7_slippage_logger.py`

---

## 0. TL;DR

- **L-7 IS ALREADY SHIPPED** in production. `src/components/slippage_shadow_logger.py` was committed at `6b049ab` (`feat(shadow): Q71 slippage shadow logger -- captures requested vs fill price`), wired into `src/components/execution.py:502` inside `ExecutionEngine.open_trade`. It writes to `shadow_logs/slippage.jsonl` (1 row currently). The design problem for L-7 is therefore not "build a new logger", it is **schema extension** — the shipped logger captures fill-side only (entry slippage); Q71's full deliverable also requires SL/TP-realized telemetry on close, which the current schema does NOT carry. This doc proposes an additive extension path that preserves byte-level historical compatibility.
- **L-6 is NOT shipped** as a dedicated logger. There is partial coverage via `evaluation_logger.log_evaluation(usage=...)` (commit `e1bc085` `feat(halluc-2): add usage block to evaluation_logger schema`) which writes a `usage` block per CANDIDATE evaluation row. But that block is missing: (1) cost in USD, (2) latency, (3) prompt-hash for cache-debug, (4) role-tag for retry-vs-first-call separation, (5) call_id correlation key. The dedicated L-6 logger proposed here is a **call-grain** record (one row per Anthropic API call, not per evaluation), which is the grain HALLUC-2's research questions actually need.
- **HALLUC-2 framing.** "HALLUC-2" in this dispatch refers to the same precision-bug class as HALLUC-1 (commit `2c75f98` etc) — the broader goal is to give Phase 2's tool-grounding (L-1) and AI-misbehavior research (L-2) work the API-call-grain telemetry needed to attribute cache hit/miss patterns, retry rates, and per-symbol cost to specific code paths.

---

## 1. Existing `shadow_logs/slippage.jsonl` analysis

### Current state (as of 2026-04-29)

```jsonl
{"ts": "2026-04-28T09:30:05.343157+00:00", "ticket": 233955223, "symbol": "GBPJPY", "direction": "LONG", "requested_price": 215.274, "fill_price": 0.0, "slippage_price": -215.274, "slippage_directional": -215.274, "slippage_pips": -21527.4, "spread_at_request": 1.4000000000010004, "kill_zone": null, "trigger": "limit_fill", "notes": "Request executed"}
```

**One row total.** The single row is the GBPJPY 2026-04-28 09:30 UTC trade referenced in memory `project_2026-04-29_post_deploy_watchlist`.

### Schema currently in use (parsed)

| Field | Type | Source | Notes |
|---|---|---|---|
| `ts` | ISO-8601 UTC | `datetime.now(timezone.utc).isoformat()` | log-emission time |
| `ticket` | int | `OrderResult.order` | MT5 ticket |
| `symbol` | str | `self._persist_symbol` | internal symbol key (e.g. `GBPJPY`) |
| `direction` | str | `trade_params["direction"]` | `LONG` / `SHORT` |
| `requested_price` | float | `entry_price` (current ask/bid at submission) | NEVER null |
| `fill_price` | float | `OrderResult.price` | **0.0 in this row** — broker returned 0.0 on success; logged verbatim |
| `slippage_price` | float | `round(fill - req, 8)` | sign-preserving raw delta |
| `slippage_directional` | float | adverse-positive convention | LONG: `fill-req`; SHORT: `req-fill` |
| `slippage_pips` | float\|null | `slippage_directional / pip_size` | null when symbol pip unknown |
| `spread_at_request` | float\|null | `tick.spread_cents = (ask-bid)*100` | null on missing tick |
| `kill_zone` | str\|null | orchestrator-supplied | `"london"` / `"ny"` / `"tokyo"` / null |
| `trigger` | str\|null | orchestrator-supplied | `"limit_fill"` / `"candidate_market"` / etc. |
| `notes` | str\|null | `OrderResult.comment` | "Request executed" in this row |

### What's MISSING for full Q71 Phase-1 deliverable

The shipped logger answers: **how much did the entry slip vs the requested price?** Q71's full ask requires answering:

1. **Did the SL fill at the modeled price, or did it gap?** — needed for fat-tail Monte Carlo backtests; SL slippage is the dominant tail-risk driver in gold (memory `project_distributional_findings`).
2. **What was the realized TP1 fill?** — needed for partial-close P&L attribution; J46-J49 policy assumes 3R TP1 hits at $X but real fills can be off by 5-15 ticks.
3. **What was the broker state at fill?** — connection-status / weekend-edge / dead-zone tagging for fill-quality forensics.
4. **What fill-type did the broker use?** — IOC vs FOK vs partial; affects requote behavior modelling.

The current schema has no place for any of these. The proposed extension at §3 below adds them ADDITIVELY (new fields appended, never renamed), which preserves the existing single row as still-valid data.

### Why is there only 1 row?

Hypotheses (NOT confirmed — investigation gap, recommend a follow-up grep of `live_evaluations/` for CANDIDATE rows per symbol):

- **H1 — Most CANDIDATEs are pending limits, not market fills.** `record_slippage` only fires from `ExecutionEngine.open_trade` (execution.py:502). If most April orders entered as limit-intent and the limit never filled (KZ expiry / 48-hour limit), no row gets logged. This is consistent with the very low live trade frequency (~1/week current cohort) and the 2026-04-28 GBPJPY +0.74R close being the only filled trade in the observation window.
- **H2 — Logger only shipped recently.** Commit `6b049ab` lands the logger; if it merged into main close to 2026-04-28, only the GBPJPY trade fired post-merge. `git log --oneline 6b049ab` would confirm.
- **H3 — Other fills were in dry-run / smoke-test code paths** that bypass `open_trade`. `fn_smoke_*.json` files in `shadow_logs/` confirm fn_smoke uses a separate path; those would not write to `slippage.jsonl`.

**Recommendation:** main-thread integration audit should grep `git log src/components/slippage_shadow_logger.py shadow_logs/slippage.jsonl` and `_trade_index.json` for the actual fill count April 27-29 and confirm H1 (limits unfilled) is the dominant explanation.

### Migration path to extended schema

The existing logger uses **schema-stable, additive-only field discipline** (see `src/components/slippage_shadow_logger.py:56`). Three rules govern the extension:

1. **Never rename or remove** existing fields. The 1 historical row keeps loading without modification.
2. **Add new fields at the END** of the dict literal in `record_slippage`. Consumers test on `key in row` rather than schema-version dict shape.
3. **Optional fields stay optional.** Code that only logs entry-side fills writes the same shape as today (with new fields absent / null) and is forward-compatible.

The extended schema (§3) follows all three rules. The migration is a 6-line additive patch in `record_slippage` plus a new `record_close_slippage` helper for close-side telemetry; no data conversion is required for historical rows.

---

## 2. L-6 — HALLUC-2 token-usage logger schema

### Schema (one JSONL row per Anthropic API call, NOT per evaluation)

```json
{
  "timestamp": "2026-04-29T08:15:00.123456+00:00",
  "call_id": "01JXY7K3M2N4P9R0T7V8W9XAB1",
  "symbol": "XAUUSD",
  "kill_zone": "london",
  "candle_time": "2026-04-29T08:15:00+00:00",
  "model": "claude-sonnet-4-6",
  "primary_effort": "max",
  "role": "primary",
  "attempt": 1,
  "input_tokens": 145,
  "cache_read_tokens": 12480,
  "cache_creation_tokens": 0,
  "output_tokens": 870,
  "cache_ttl": "1h",
  "is_batch": false,
  "cost_usd_breakdown": {"input": 0.000435, "output": 0.013050, "cache_write": 0.0, "cache_read": 0.003744},
  "total_cost_usd": 0.017229,
  "latency_ms": 14820,
  "prompt_hash": "a7f4c2d9",
  "served_model_id": "claude-sonnet-4-6-20260201",
  "response_id": "msg_01ABCD...",
  "backend_mode": "api"
}
```

### Field rationale

| Field | Type | Rationale |
|---|---|---|
| `timestamp` | ISO-8601 UTC | log-emission time, joinable to `live_evaluations/*.json` `timestamp_utc` |
| `call_id` | ULID/UUID | Generated client-side at call time; correlates retries (attempt=1, attempt=2) and the eval log row. ULID is monotonic and 26-char; UUID4 also fine. |
| `symbol` | str | Per-symbol cost attribution. Sourced from orchestrator `self._symbol`. Required for HALLUC-2 per-instrument breakdown. |
| `kill_zone` | str\|null | Same string the orchestrator passes to slippage logger. `"london"` / `"ny"` / `"tokyo"` / null. Cost-by-KZ is a Phase 2 question. |
| `candle_time` | ISO-8601 UTC\|null | M15 candle close timestamp from `mso.timestamp_utc`. NULL is acceptable for non-candle calls (e.g. canary, batch). |
| `model` | str | Primary key for joining `cost_tracker.PRICING_USD_PER_MTOK` rows. Always lower-case canonical model id (`claude-sonnet-4-6` not `claude-sonnet-4-6-20260201` — the served-model variant goes in `served_model_id`). |
| `primary_effort` | str\|null | `"max"` / `"high"` / null. From `ai.primary_effort`. Effort affects token count (max = more reasoning tokens), so it must be on the row to interpret per-call cost. |
| `role` | str | `"primary"` / `"primary_retry_format"` / `"primary_retry_timeout"` / `"primary_retry_rate_limit"` / `"primary_retry_500"` / `"batch"` / `"canary"`. Distinguishes first-call cost from retry waste. |
| `attempt` | int | 1 = first call; 2 = format-correction retry; 3+ = SDK-internal timeout/500/rate-limit retries. Without this field, retry waste is invisible. |
| `input_tokens` | int | Anthropic SDK `response.usage.input_tokens`. Coerced to int; null → 0. |
| `cache_read_tokens` | int | `response.usage.cache_read_input_tokens`. The cache-hit signal — high values mean the 1h ephemeral cache is working; near-zero values mean every call is a cold-cache rewrite (~$15-18 per fleet-stall event observed 2026-04-27). |
| `cache_creation_tokens` | int | `response.usage.cache_creation_input_tokens`. Cache-miss signal; high values mean the cache is being re-created (TTL expired or cache-key changed). |
| `output_tokens` | int | `response.usage.output_tokens`. |
| `cache_ttl` | str | `"5m"` / `"1h"` / `"none"`. Read from the `cache_control` block in the system prompt — current production is `"1h"` (primary_analyzer.py:238). Drives cache_write pricing in `cost_tracker.compute_cost`. |
| `is_batch` | bool | True for `messages.batches.create` calls (50% input/output discount). False for live + canary. |
| `cost_usd_breakdown` | dict[str,float] | Four-component breakdown (`input` / `output` / `cache_write` / `cache_read`). Reused from `src/research_infra/cost_tracker.compute_cost`. Keeping the breakdown alongside `total_cost_usd` lets analysts answer "are we cache-bound or output-bound?" without re-running pricing math. |
| `total_cost_usd` | float | sum(cost_usd_breakdown.values()). Rounded to 8 decimals. Subscription-mode rows write `0.0` (CLI route doesn't bill against the $50/mo cap; memory `feedback_billing_tracks_distinction`). |
| `latency_ms` | int | `time.perf_counter_ns()` delta from immediately-before `client.messages.create()` to immediately-after. Used for fleet-stall detection (Windows OS canary fanout fix; commit `a44f39d`) and timeout-retry-config tuning (`ai.timeout_retry_enabled`). |
| `prompt_hash` | str | SHA-256 hex truncated to 16 chars over the system-prompt blocks (joined). Cache-debug field — when `cache_read_tokens=0` despite `cache_ttl="1h"`, comparing two consecutive `prompt_hash` values quickly tells whether the cache key actually changed (D1/H4 direction flip per primary_analyzer.py:200) or whether something else broke. |
| `served_model_id` | str\|null | `response.model` from the SDK. Differs from `model` when Anthropic auto-routes to a snapshot id (e.g. `claude-sonnet-4-6-20260201`). Drift-alerts already record this elsewhere via `_model_pin.record_served_model`; mirroring it here keeps the cost row self-contained. |
| `response_id` | str\|null | `response.id`. Cross-references Anthropic's server-side log for support escalation. |
| `backend_mode` | str | `"api"` / `"subscription"`. Subscription-mode token counts are estimates (CLI doesn't return real `usage`); having the mode on the row lets analysts filter out the estimates when computing actual API spend. |

### What's intentionally NOT in the schema

- **Raw prompt text.** That's `live_evaluations/{symbol}/{timestamp}.json` job. Repeating it here would 10×–100× the log size.
- **Decision outcome (CANDIDATE / NO_TRADE / WAIT).** Already on the eval row; join via `(symbol, candle_time)` or `call_id`.
- **Realized R.** Lives in `_trade_index.json` / `trade_records/`. Joins via ticket → call_id → eval row.

This is deliberately the **call-grain** record. One evaluation can produce 1-3 rows (first call + format-correction retry + rare SDK-internal retry); each is a separate API call with its own cost, and the join key on the analyst side is `(symbol, candle_time)` or `call_id`.

---

## 3. L-7 — Q71 slippage logger extended schema

### Existing 13 fields (KEEP unchanged — schema stability contract)

`ts`, `ticket`, `symbol`, `direction`, `requested_price`, `fill_price`, `slippage_price`, `slippage_directional`, `slippage_pips`, `spread_at_request`, `kill_zone`, `trigger`, `notes`.

### NEW additive fields (entry-side enrichment)

| Field | Type | Rationale |
|---|---|---|
| `event` | str | `"entry_fill"` / `"sl_fill"` / `"tp1_partial_fill"` / `"tp2_full_fill"` / `"close_other"`. Distinguishes entry from close events — without this, `record_slippage` rows and `record_close_slippage` rows can't be told apart. Default `"entry_fill"` for backward compatibility. |
| `expected_sl` | float\|null | The SL price the AI declared (from `trade_params["stop_loss"]`). Logged at entry so close events can compute `realized_sl - expected_sl`. |
| `expected_tp1` | float\|null | The original AI TP1 (`original_ai_tp1`) — NOT the J46-J49-overridden 6R broker TP. |
| `slippage_pct_atr` | float\|null | `slippage_directional / m15_atr` if M15 ATR is available from the MSO. Lets analysts compare slippage across instruments without per-symbol tick-size scaling. |
| `fill_type` | str\|null | `"IOC"` / `"FOK"` / `"market"` / `"limit_fill"` from `request["type_filling"]`. Required for 10026-class retcode forensics (memory `project_redacted_account_free_trial_ea_excluded`). |
| `broker_state` | dict\|null | `{"connected": bool, "trade_allowed": bool, "spread_cents": float, "server_time_offset_sec": int}`. Connection forensics for fill-quality. |
| `mt5_retcode` | int\|null | `OrderResult.retcode`. Already implicit in `success` but explicit retcode lets analysts distinguish 10009 (success) from 10025 (no quotes) etc. |
| `request_volume` | float\|null | Lots requested. Joins to position-sizing forensics (H29 drawdown size reduction). |
| `realized_volume` | float\|null | `OrderResult.volume`. Differs from `request_volume` on partial fills. |

### NEW additive fields (close-side, NEW `record_close_slippage` API)

These fields are written by the proposed `record_close_slippage` helper at close time. The same JSONL file (`shadow_logs/slippage.jsonl`) receives the rows; the `event` field discriminates them.

| Field | Type | Rationale |
|---|---|---|
| `event` | str | `"sl_fill"` / `"tp1_partial_fill"` / `"tp2_full_fill"` / `"be_close"` / `"j46_j49_time_stop"` / `"manual_close"` / `"force_close"`. |
| `expected_close_price` | float\|null | The price the close was MEANT to fire at — for SL hits this is the modeled SL; for TP1 partials this is `trade.take_profit_1`; for BE moves this is the entry price. |
| `realized_close_price` | float\|null | `OrderResult.price` from `close_position` / partial close (with the existing 0.0 fallback to `tick.bid`/`tick.ask` already in `execution.py:1037-1060`). |
| `realized_sl` | float\|null | When `event=="sl_fill"`, the actual broker fill price. |
| `realized_tp1` | float\|null | When `event=="tp1_partial_fill"`, the actual partial-close price. |
| `realized_tp2` | float\|null | When `event=="tp2_full_fill"`, the actual full-close price. |
| `slippage_close_price` | float\|null | `realized_close_price - expected_close_price`. Sign-preserving. |
| `slippage_close_directional` | float\|null | Adverse-positive: for LONG SL `expected - realized`; for LONG TP `expected - realized` (TP slips against you when below); SHORT inverted. |
| `slippage_close_pips` | float\|null | `slippage_close_directional / pip_size`. |
| `time_in_trade_sec` | int\|null | `(close_time - entry_time).total_seconds()`. Joins to time-in-trade shadow logger. |
| `close_reason` | str\|null | The same `reason` string `close_position` writes to `_record_close`. Free-form. |
| `entry_ticket` | int\|null | Same ticket as the entry row — provides O(n) join key without needing to scan `_trade_index.json`. |

### Migration path (concrete diff target)

The migration is **two patches** to `src/components/slippage_shadow_logger.py`:

1. Add new keyword arguments with default `None` to `record_slippage` (entry-side enrichment fields above).
2. Add a sibling function `record_close_slippage(*, event, ticket, symbol, direction, expected_close_price, realized_close_price, ...)` that writes a row with `event != "entry_fill"`.

Plus **two integration patches** in `src/components/execution.py`:

1. `open_trade` (entry — file:line=502): pass the new fields. Cost: ~10 added arguments.
2. `close_position` (file:line=1022) + `_check_partial_close` paths (lines 840 / 869 / 916 / 953 / 1005): one `record_close_slippage(...)` call each. Cost: ~5 call sites × 8-10 lines.

Combined LOC budget: ~50-60 LOC for full L-7 close-side coverage. The original "30 LOC" backlog estimate accounts only for entry-side enrichment.

---

## 4. Integration points (file:line)

### L-6 token-usage logger

| Site | File | Line | Action |
|---|---|---|---|
| **API mode** — first/successful call | `src/components/primary_analyzer.py` | 397 (call) → 408 (after _last_usage update) | Wrap `client.messages.create(**create_kwargs)` with a pre-call `t0 = time.perf_counter_ns()` and a post-call `log_call(...)`. Pass `attempt=attempt+1`, `role="primary_retry_format"` if this is the format-correction retry path (analyze() flag), else `"primary"`. |
| **API mode** — timeout/rate-limit/500 retry | `src/components/primary_analyzer.py` | 421-444 | Each `except ...` branch already raises after `attempt < self.max_retries` decision. Log a row with `role="primary_retry_timeout"` etc. + `total_cost_usd=0.0` + `latency_ms = perf_counter_ns - t0` so a failed call's cost is still in the audit trail. |
| **Subscription mode** | `src/components/primary_analyzer.py` | 459 (call) → 472 (after _last_usage update) | Same wrap. `backend_mode="subscription"`; `total_cost_usd=0.0` because CLI doesn't bill against `$50/mo` cap (memory `feedback_billing_tracks_distinction`). |
| **Format-correction retry** (one-shot) | `src/components/primary_analyzer.py` | 329 (analyze body) | The retry call goes back through `_call_claude` so it's already covered by sites above; the only thing the analyze level needs is to flag `role="primary_retry_format"` (see decoration plan below). |

**Implementation pattern.** The cleanest hook is a **decorator-style wrapper** on `_call_claude`/`_call_claude_subscription`, which avoids dirtying every retry branch. Reference impl shows the standalone-module API; a thin adapter in `primary_analyzer.py` would be:

```python
# AT TOP OF FILE (proposed; main thread implements):
from research.ml_program.experiments.l6_token_usage_logger import TokenUsageLogger
self._token_logger = TokenUsageLogger()  # in __init__

# AROUND the create_kwargs call (post-PR location):
call_id = self._token_logger.start_call(
    symbol=self._symbol(),
    kill_zone=self._current_kz(),
    candle_time=self._current_candle_time(),
    model=self.model,
    primary_effort=self.effort,
    role="primary",
    attempt=attempt + 1,
    backend_mode=self.backend.mode,
)
try:
    response = self.client.messages.create(**create_kwargs)
    self._token_logger.log_success(call_id, response, cache_ttl="1h")
    return response.content[0].text
except (AnthropicTimeoutError, AnthropicRateLimitError, AnthropicServerError) as exc:
    self._token_logger.log_failure(call_id, type(exc).__name__)
    raise
```

The orchestrator (`src/components/orchestrator.py:612` PrimaryAnalyzer init) does NOT need a code change — the logger is owned by PrimaryAnalyzer.

**LOC budget for L-6 main-thread integration:** ~12 LOC in `primary_analyzer.py` (init + 3 call sites: API mode success, API mode failure, subscription mode). Matches the backlog "~10 LOC" target.

### L-7 slippage logger (extended)

| Site | File | Line | Action |
|---|---|---|---|
| **Entry fill** | `src/components/execution.py` | 502 | Existing call — extend with new keyword args (`expected_sl=sl`, `expected_tp1=original_ai_tp1`, `mt5_retcode=result.retcode`, `request_volume=lots`, `realized_volume=result.volume`, `fill_type=...`, `broker_state=...`, `slippage_pct_atr=...`). |
| **TP1 partial close** | `src/components/execution.py` | 840 (`partial_close_events.append`) | After the broker confirms the partial, add `record_close_slippage(event="tp1_partial_fill", expected_close_price=trade.take_profit_1, realized_close_price=close_result.price, ...)`. |
| **TP2 full close** | `src/components/execution.py` | 1018 (`tp2_full_close`) | Same pattern. `event="tp2_full_fill"`, `expected_close_price=trade.take_profit_2`. |
| **SL hit / manual close** | `src/components/execution.py` | 1062 (`_record_close(reason)`) | After `_record_close`, before `self.active_trade = None`, add `record_close_slippage(event=reason, ...)`. The `reason` string is already standardized — `"sl_hit"` / `"manual"` / `"j46_j49_time_stop"` / `"sl_modification_failed"` / `"be_close"`. |
| **BE move** | `src/components/execution.py` | 869 / 916 / 953 / 1005 | Each event-append site. `event="be_close"` when `reason == "be_close"`. |

**Orchestrator wiring:** the orchestrator does NOT instantiate the slippage logger — it's a stateless function (`record_slippage` / `record_close_slippage`). The orchestrator already passes `kill_zone` + `trigger` through `open_trade(...)` (orchestrator.py call sites elsewhere); the close-side hook is fully internal to ExecutionEngine and doesn't need orchestrator changes.

**LOC budget for L-7 main-thread integration:** ~25-35 LOC across the 5 call sites + new keyword args at entry site. Matches the backlog "~30 LOC" target if close-side is in scope (which it should be — entry-only is what's already shipped).

### Common: `shadow_logs/` write discipline

Both loggers MUST follow the canonical pattern from `src/components/touch_count_gate_logger.py:230-237` and `src/components/slippage_shadow_logger.py:247-256`:

```python
path = Path(log_path or SHADOW_LOG_PATH)
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
```

- **Append mode** (`"a"`) — atomic for short writes on POSIX/Windows when the line fits in a single OS write buffer.
- **No fsync** on the hot path (latency budget < 1 ms; durability acceptable to lose at most the last 1-3 rows on a crash).
- **Module-level `SHADOW_LOG_PATH` constant** read at call time so tests can monkey-patch the module attribute.

---

## 5. Edge cases handled

### L-6 token-usage logger

1. **Cache hits.** `cache_read_tokens > 0` and `input_tokens` is the small delta. Logger records both; analyst computes `cache_hit_ratio = cache_read_tokens / (cache_read_tokens + cache_creation_tokens + input_tokens)`.
2. **Cache misses (first call after deploy).** `cache_creation_tokens > 0` and `cache_read_tokens == 0`. Logger records both. The 1h TTL cost is amortized over the next ~5 reads (rationale at primary_analyzer.py:233).
3. **Retries.** Each retry is its OWN row with a fresh `call_id`, `attempt > 1`, distinct `role`. The format-correction retry (analyze() level) and the SDK-internal retries (`_call_claude` level) are both visible in the log.
4. **Subscription mode (CLI).** `usage` block is partially populated by `LLMBackend` (input_tokens/output_tokens approximated; `cache_read_tokens` is 0 because the CLI doesn't expose it). Logger writes `total_cost_usd=0.0` and `backend_mode="subscription"` so cost reports filter these out.
5. **Failed calls.** Timeout / 500 / rate-limit raise before `response.usage` is available. Logger writes a row with `total_cost_usd=0.0`, `latency_ms`=actual elapsed, `role` carrying the exception class. This is the prerequisite for "what % of fleet stalls cause cold-cache rewrites?" analysis.
6. **Unknown model.** The shipped `cost_tracker.compute_cost` raises `UnknownModelError` (cost_tracker.py:187) on a model not in the pricing table. The L-6 logger MUST catch that and write a row with `total_cost_usd=null` + `notes="unknown_model:claude-foo-9-9"` rather than crash trade flow. **Fail-open contract** matches `record_slippage`.
7. **Effort=max + max_tokens=2000 with reasoning tokens.** Anthropic SDK exposes `output_tokens` as the total (visible + thinking). Logger does not need to split — current pricing applies the same rate to both.
8. **Concurrent calls (multi-symbol orchestrators).** 7 orchestrators × 1 call/15min = ~28 calls/hour peak. The OS append-write is atomic for our ~600-byte rows; the in-process `threading.Lock` from `cost_tracker._LOG_LOCK` is NOT strictly needed but is cheap insurance.
9. **Prompt-hash collisions.** SHA-256 truncated to 16 hex chars has ~10^-12 birthday-collision probability over our expected lifetime row count (10^7 rows). Acceptable.
10. **API key absent / wrong env.** This is a launch-time error and never reaches `_call_claude` in production. No special handling needed.

### L-7 slippage logger

1. **Limit-fill (no slippage at submission).** Already handled by current logger — `trigger="limit_fill_inside_kz"` etc., `requested_price` is the submitted price.
2. **`OrderResult.price == 0.0` (broker quirk).** Already handled at execution.py:454 — fallback to `tick.ask`/`tick.bid`. Logger captures the raw 0.0 so analysts can see the pattern.
3. **MT5 returns `success=False` with a partial fill.** Edge case; `realized_volume < request_volume`. Logger captures both.
4. **Partial close fires multiple times for one trade.** Each TP1 partial / BE move / TP2 fires its own `record_close_slippage`. Joinable by `entry_ticket`.
5. **SL modification failure → forced close.** `reason="sl_modification_failed"` (execution.py:1000). Logger fires once with `event="sl_modification_failed"`.
6. **J46-J49 time stop closes (12-bar timer).** `reason="j46_j49_time_stop"` (execution.py:1182). Logger fires once.
7. **Trade closed mid-restart by orchestrator state-machine recovery.** The state-machine recovery doesn't go through `close_position` so the close-side log is missed. **Open question:** should the orchestrator state-machine recovery also fire `record_close_slippage`? Recommend yes; tracking issue is out of scope for this design dispatch. Documented as caveat in the integration brief.
8. **Symbol with unknown `pip_size`.** Existing handling — `slippage_pips=null`, raw `slippage_price` always present.
9. **Negative directional slippage (favorable fill).** Already handled — sign-preserving convention.
10. **Multi-symbol concurrent fills.** Single-process orchestrator per-symbol; no shared lock needed across processes (POSIX `O_APPEND` atomicity). On Windows, 7 processes appending to the same file: tested behavior per execution.py:255 comment is "atomic for short writes". Risk of interleaving ~600-byte rows is non-zero but acceptable for shadow-only data; if it becomes a problem the upgrade is per-symbol jsonl files (`slippage_{SYMBOL}.jsonl`).

---

## 6. Tests

Both reference impls include `pytest`-importable unit tests in the same file (`if __name__ == "__main__": pytest.main([__file__])` pattern) covering:

### L-6 (`l6_token_usage_logger.py`)

- `test_log_success_writes_canonical_schema` — synthetic SDK-shaped response object → assert all 19 fields present in jsonl row.
- `test_log_success_handles_cache_hit` — cache_read_tokens > 0 → assert correct cost math.
- `test_log_success_handles_cache_miss` — cache_creation_tokens > 0, cache_ttl="1h" → assert cache_write rate matches table.
- `test_log_failure_writes_zero_cost` — exception path → assert `total_cost_usd == 0.0` and `role` carries class name.
- `test_log_subscription_mode_writes_zero_cost` — backend_mode="subscription" → assert cost is 0.
- `test_log_unknown_model_does_not_raise` — unknown model → row written with `total_cost_usd=null`, notes carrying error.
- `test_call_id_unique_across_retries` — three calls in a row → three distinct call_ids.
- `test_prompt_hash_stable_for_same_prompt` — same prompt → same hash.
- `test_log_path_override_for_isolation` — `log_path=tmp_path/...` → writes to that path, not the default.

### L-7 (`l7_slippage_logger.py`)

- `test_record_entry_fill_extended_schema` — synthetic OrderResult → all 22 fields (13 existing + 9 new) present.
- `test_record_close_slippage_sl_hit` — synthetic SL fill → `event="sl_fill"`, correct `slippage_close_directional` sign.
- `test_record_close_slippage_tp1_partial` — synthetic partial close → `event="tp1_partial_fill"`.
- `test_close_slippage_handles_zero_realized_price` — broker returns 0.0 → falls back to expected_close_price for forensic clarity, raw 0.0 logged.
- `test_close_slippage_pip_resolution` — XAUUSD/USDJPY/NAS100 → correct pip sizes from the existing `_PIP_SIZE_BY_SYMBOL` table.
- `test_join_via_entry_ticket` — write entry row + close row → assert `entry_ticket` in close row equals `ticket` in entry row.
- `test_failure_open_on_disk_error` — log_path pointed at unwritable location → no exception raised, warning logged.
- `test_jsonl_lines_parse_individually` — write 5 rows → each line parses to a valid dict.
- `test_backward_compat_with_existing_row` — replay the 1 production row from 2026-04-28 → loader accepts it without error (new fields default to null on read).

---

## 7. Open caveats / out-of-scope

1. **State-machine recovery close-path** (edge case 7 above) — not covered. Recommend a follow-up issue: register a checkpoint hook in `ExecutionEngine._record_close` that also fires `record_close_slippage` so recovery-driven closes are still logged.
2. **Subscription-mode token-count accuracy.** CLI returns approximate input_tokens (estimated from prompt length) and 0 cache_read_tokens. The L-6 row's `total_cost_usd` is correctly 0.0 in that mode, but `input_tokens`/`output_tokens` are not directly comparable to API-mode rows. Documented inline in the reference impl.
3. **Cache-hit ratio is NOT a pre-built metric.** The schema gives all the inputs (`input_tokens`, `cache_read_tokens`, `cache_creation_tokens`); the analyst computes the ratio downstream. This is deliberate — different analyses want different denominators (per-call vs. per-symbol-day vs. per-fleet-stall-event).
4. **Sub-call grain (tool-use).** When L-1 (tool-use grounding research) wires `tool_use` calls in PrimaryAnalyzer, each tool round-trip is a separate `client.messages.create(...)` invocation. The L-6 logger schema natively supports this (each call is its own row, joinable by `call_id` parent-child if a `parent_call_id` field is added at L-1 time). No schema change needed at L-6 ship time.
5. **Production cost-tracker reuse.** `src/research_infra/cost_tracker.py` is RESEARCH-INFRA (per its docstring) and explicitly does NOT modify the production trading path. The L-6 logger SHOULD reuse `cost_tracker.compute_cost` for pricing math (single source of truth) but write to a SEPARATE jsonl path (`shadow_logs/token_usage.jsonl`) so it is observable from the production-watchdog tooling. The reference impl imports `compute_cost` and bundles its own `record_token_usage` writer.
6. **Decision authority.** This dispatch is design-only. CEO approval and the WF-1 discipline gate apply before main-thread integration ships any of this. Trading-logic-affecting changes: NONE in this design. Production-code changes: NONE in this design.

---

## 8. Quick reference for main-thread integration

When the CEO approves and main-thread integrates:

1. **Copy reference impls into `src/components/`** (recommended: `src/components/token_usage_logger.py` mirroring naming convention of `slippage_shadow_logger.py`).
2. **Apply 3 edits to `src/components/primary_analyzer.py`** — init + API success + API failure paths (~12 LOC total). Subscription mode gets the same wrap.
3. **Apply 5 edits to `src/components/execution.py`** — extend `record_slippage` call args at line 502; add 4 new `record_close_slippage` calls at lines 840 / 869 / 916 / 953 / 1005 / 1062 (~30 LOC total).
4. **Add fields to `src/components/slippage_shadow_logger.py`** record_slippage signature + add `record_close_slippage` sibling function (~40 LOC).
5. **Run pytest** on the new shadow_logger test file + on the integration tests (out of scope for this dispatch — main thread spec).
6. **Update `.context/LIVE_STATE.md`** auto-generator if it scans for shadow log file presence (currently only counts files; new files will be auto-detected).
7. **Update `CLAUDE.md`** "What is working" — add the two new loggers to the shadow loggers list.

End of design.
