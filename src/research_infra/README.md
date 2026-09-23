# GTOS Research Infrastructure (Phase 1)

This package holds shared infrastructure for the Phase 1-4 research
program: cost tracking, batch-API helpers, prompt-cache helpers, model
routing, and related tooling. It is RESEARCH-only — production trading
code (`src/llm_backend.py`, `src/components/primary_analyzer.py`) MUST
NOT depend on anything in here.

Phase 1 ships **infrastructure only** — no API calls, no cost spend. Real
API work begins in Phase 2 once the Wave 1 modules are merged and CEO has
authorized the budget.

---

## Batch API wrapper (T0.1)

Module: `src/research_infra/batch_client.py`
Smoke:  `scripts/research/batch_smoke.py`

The wrapper in `batch_client.py` is an **additive** facade over
`client.messages.batches.*`. It does NOT touch the production
trading-decision path (`src/llm_backend.py` →
`src/components/primary_analyzer.py`), and it MUST NOT be used to
issue live trading-decision calls.

### When to use batch vs sync

Use this `BatchClient` when:

- **Latency is not critical.** The batch API has a 24h SLA; in practice most
  jobs return in under an hour, but anything under a few minutes is *not*
  the right shape.
- **The job is large enough to amortize polling overhead.** Below ~10
  requests, the sync API is simpler and only marginally more expensive. Above
  ~50, batch wins on both cost and rate-limit headroom.
- **Cost matters.** Batch input + output tokens are 50% cheaper than the sync
  API. Phase 2-4 backtests in particular are 2× cheaper through this wrapper.

Use the **sync** path (`src/llm_backend.py`) when:

- The call is part of the live trading pipeline (`primary_analyzer.py` →
  `Sonnet 4.6 effort=max`). Trading decisions stay synchronous.
- You need a result within seconds (interactive debugging, smoke checks of a
  prompt change, single-fixture canary runs).
- The call must hit a feature the batch API does not yet expose
  (the wrapper is sync-equivalent on `messages` shape, but always check the
  Anthropic changelog before assuming parity for esoteric flags).

### Equivalence contract

A batch request and a sync request are **semantically equivalent** when:

1. Both use the same `model` identifier (e.g.
   `claude-haiku-4-5-20251001`).
2. Both pass identical `messages` and `system` content blocks (byte-for-byte
   — the wrapper does not rewrite, normalize, or strip content). This is the
   property that lets prompt caching span batch + sync calls.
3. Both pass identical `max_tokens`, `temperature`, and `output_config`.
4. The cache state is identical at the moment of execution. (Cache writes
   in one path are visible to the other path because cache keys are over
   *content* not over *transport*.)

Under those conditions the wrapper produces a `BatchResult` whose
`content_text`, `stop_reason`, and `usage` match what the sync API would
return — modulo the same non-determinism that `effort=max` already exhibits
in the sync path. **Do not** treat batch + sync results as bit-identical;
treat them as draws from the same model+context distribution.

The wrapper does NOT alter:

- Cache control blocks. `cache_control: {"type": "ephemeral"}` (5m default)
  and `cache_control: {"type": "ephemeral", "ttl": "1h"}` are forwarded
  verbatim. The `cache_ttl` field on `BatchRequest` is informational only —
  it documents which TTL the caller intended, for cost / observability
  joins. The actual cache contract lives inside the content blocks.
- `output_config={"effort": "max"}`. Forwarded as `params.output_config`.

### Cost characteristics

- **50% discount** on both input and output tokens vs the sync API. (See
  Anthropic pricing for the current per-million-token table.)
- **Cache hits remain effective.** A 1h-cached system block written by a
  sync call is read for the discounted rate by a batch call (and vice versa)
  as long as the content matches.
- **No additional batch fee.** The discount is the only structural change.
- **No retry-induced double billing.** The wrapper retries only on
  network-class transients (APIConnectionError, APITimeoutError,
  InternalServerError, and 5xx APIStatusError). The retried calls are the
  *create* call to the batches endpoint, not the per-request work itself —
  no per-request charges accrue until the batch is accepted.

Cost / cache observability lives in T0.2 (separate module, see below). T0.2 hooks the
`progress_callback` parameter of `wait_and_fetch` to record per-batch usage
and cache-hit rates.

### Limits

- **Batch size:** up to **100,000** requests per batch (the wrapper
  enforces this via `MAX_REQUESTS_PER_BATCH`).
- **Batch payload:** up to **256 MB** total request size. The wrapper does
  NOT pre-validate this — the SDK / API rejects oversize payloads. Callers
  building massive prompts should chunk into smaller batches.
- **Expiry:** batches expire **24 hours** after creation if not all results
  have been processed. The wrapper's `max_wait_seconds` defaults to 24h and
  raises `BatchTimeoutError` if the deadline passes. (`results_url` also
  becomes unavailable after archival.)
- **Custom IDs:** must be **unique within a batch**. The wrapper rejects
  duplicates and empty strings before any network call.
- **Cancellation:** `client.messages.batches.cancel(...)` is supported by
  the SDK. The wrapper does not currently expose a cancellation surface —
  add it when a use case demands.

### Surface summary

```python
from src.research_infra.batch_client import BatchClient, BatchRequest

client = BatchClient(polling_interval_seconds=60, max_wait_seconds=86400)

requests = [
    BatchRequest(
        custom_id=f"slice-{i:04d}",
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "..."}],
        system=[{
            "type": "text",
            "text": "...",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }],
        max_tokens=2000,
        cache_ttl="1h",                     # informational
        output_config={"effort": "max"},    # passthrough
    )
    for i in range(N)
]

batch_id = client.submit_batch(requests)
results = client.wait_and_fetch(
    batch_id,
    progress_callback=lambda status, counts: print(status, counts),
)

for cid, r in results.items():
    if r.error is not None:
        ...  # handle per-request failure (errored / canceled / expired)
    else:
        ...  # r.content_text, r.usage, r.stop_reason
```

Operator smoke script: `scripts/research/batch_smoke.py` (5 Haiku requests,
runs end-to-end against the real API, fractions of a cent).

---

## Cost Tracking (T0.2)

Module: `src/research_infra/cost_tracker.py`
CLI:    `scripts/research/cost_report.py`
Audit log: `shadow_logs/research_cost.jsonl` (default sink)

### What it does

`CostTracker.log_call` takes one Anthropic API call's `usage` block,
computes the four-component cost breakdown (input / output / cache_write
/ cache_read) using the rates in `PRICING_USD_PER_MTOK`, and atomically
appends one JSONL row to the audit log. `aggregate(run_tag, since,
until)` reads the JSONL back and returns a `CostReport` with totals and
a per-model breakdown. `set_budget_alert(run_tag, budget_usd, callback)`
fires the callback once when the per-tag aggregate crosses the
threshold.

### `usage` block fields

The tracker accepts the Anthropic SDK's native `usage` shape. Pull these
from `response.usage`:

- `input_tokens` (int) — non-cached input tokens
- `output_tokens` (int) — generated output tokens
- `cache_read_input_tokens` (int) — tokens served from cache (cheap)
- `cache_creation_input_tokens` (int) — tokens written into cache (priced
  at `cache_write_5m` or `cache_write_1h` depending on TTL)

Missing fields are coerced to zero — real responses sometimes omit cache
fields entirely on a non-cached call, and the tracker tolerates that
without warning.

### Pricing assumptions

Pricing values in `PRICING_USD_PER_MTOK` are USD per million tokens, as
of 2026-04, sourced from the T0.2 brief (which cites Anthropic's public
pricing as of that date). Per-model rates currently encoded:

| Model              | input | output | cache_write_5m | cache_write_1h | cache_read |
| ------------------ | ----: | -----: | -------------: | -------------: | ---------: |
| claude-sonnet-4-6  |  3.00 |  15.00 |           3.75 |           6.00 |       0.30 |
| claude-opus-4-7    | 15.00 |  75.00 |          18.75 |          30.00 |       1.50 |
| claude-haiku-4-5   |  1.00 |   5.00 |           1.25 |           2.00 |       0.10 |

The Batch API applies a 50% discount to input + output tokens; cache
pricing is unchanged. This is encoded as `BATCH_DISCOUNT_INPUT_OUTPUT =
0.50` in the module.

When Anthropic publishes revised rates, update `PRICING_USD_PER_MTOK` in
a separate commit (don't mix with code changes) so historical JSONL rows
remain reconcilable with the rates that were live when they were
written.

### Run-tag convention

Pick a stable tag of the form `phase1_<task_id>` for every research
backtest. Examples:

- `phase1_a1_dumb_baseline`
- `phase1_b3_ensemble_judge`
- `phase1_c2_haiku_classifier`

Aggregation is per-tag; the CLI takes `--run-tag` and prints totals.
Don't reuse tags across tasks — a re-run of an old task should append
a `_v2` suffix so the original cost is preserved as an audit trail.

### Setting a budget alert

```python
from src.research_infra.cost_tracker import CostTracker, CostReport

tracker = CostTracker()  # default sink: shadow_logs/research_cost.jsonl

def alert(report: CostReport):
    # Send Telegram message, raise an exception, write a halt file, etc.
    print(f"BUDGET BREACH: {report.run_tag} hit ${report.total_usd:.2f}")

tracker.set_budget_alert(
    run_tag="phase1_a1_dumb_baseline",
    budget_usd=10.00,
    callback=alert,
)

# Inside the research backtest loop:
response = client.messages.create(...)
tracker.log_call(
    model="claude-sonnet-4-6",
    usage=response.usage.__dict__,  # or however your SDK exposes it
    run_tag="phase1_a1_dumb_baseline",
    custom_id=f"candidate_{i}",
)
```

The callback fires **at most once per registration**. Re-register (or
call `clear_budget_alert(tag)` then re-register) to reset.

The callback runs synchronously on the logging thread; raised exceptions
propagate to the caller of `log_call`.

### Relationship to production budget cap

This tracker DOES NOT enforce `config.budget.monthly_cap_usd` (the $50-60
production hard cap from `agent_config.yaml`). That cap remains the
responsibility of the existing production code path. The research
tracker is a parallel, additive audit + early-warning layer that lets
research backtests have their own per-task budgets independent of the
production knob.

CEO disabled Anthropic auto-reload (memory
`project_anthropic_billing_auto_reload_disabled`); the $50-60 prepaid
balance IS the hard cap. Cost tracker is the audit trail above that hard
cap, not a replacement for it.

### Concurrency

`log_call` uses a module-level `threading.Lock` plus
`open('a') + flush + os.fsync` to make in-process appends atomic. Tests
verify 8 threads × 25 calls produces exactly 200 well-formed JSONL lines
with no overwrites.

Cross-process safety on POSIX relies on `O_APPEND` semantics (atomic up
to PIPE_BUF). On Windows, multi-process writers should use disjoint
`log_path` values or coordinate externally — the in-process lock only
serializes within one Python interpreter.

### CLI

```
python scripts/research/cost_report.py --run-tag phase1_a1_dumb_baseline
python scripts/research/cost_report.py --run-tag phase1_a1_dumb_baseline \
    --since 2026-04-26 --until 2026-04-27
```

`--since` / `--until` accept any ISO 8601 string (`2026-04-26`,
`2026-04-26T08:00:00+00:00`, etc.). Naive datetimes are interpreted as
UTC. The CLI does not call any APIs; it only reads the JSONL log.

---

## Cache Helper (T0.3)

Module: `src/research_infra/cache_helper.py`
Demo:   `scripts/research/cache_pilot.py`

### 5-minute vs 1-hour TTL economics

Anthropic's prompt-cache exposes two TTL knobs, both via the same
`cache_control` block on a request's `system` content:

| TTL | Write cost | Read cost | Break-even reads |
|-----|-----------|-----------|-------------------|
| 5m (default) | 1.25× base | 0.10× base | ~2 reads |
| 1h           | 2.00× base | 0.10× base | 2 reads |

(Costs are multipliers vs base-input price. Output is unchanged by caching.)

**Production live trading stays at 5m.** Each instrument runs a 15-minute
cadence — at 4 calls/hour the cache typically goes cold between calls, and
the 5m default protects the rare edge case where the 5m window is used
multiple times.

**Research/backtest workloads switch to 1h.** A 50-1000+ call batch run
sends the same system prompt every call. With the 5m default, the cache is
recreated every ~5 minutes during the run, eating most of the savings. With
1h, one write covers the entire batch.

Estimated Phase 1-4 savings vs 5m default: **$380-600** when combined with
the batch API rebate.

### When to use 1h

Use `ttl="1h"`:

- Multi-hour batch backtests against historical fixtures.
- Sweep runs that re-evaluate the same prompt under varying user-message
  parameters.
- Replay tests that hit hundreds of fixtures consecutively.

Use `ttl="5m"`:

- Production live trading (the system prompt only changes on D1/H4 direction
  flips, but inter-call gaps are 15 min — 1h offers no benefit and the 2×
  write fee is wasted on the inevitable per-flip rebuild).
- Ad-hoc "fire 5 prompts and inspect" scripts where the run finishes in well
  under 5 minutes.

Use `ttl="none"`:

- Diagnostic runs where you want to measure uncached baseline cost.
- Sanity checks that the system prompt isn't drifting between calls.

### Cache-priming pattern

```python
from src.research_infra.cache_helper import (
    annotate_system_blocks,
    CacheMetrics,
)

# 1) Build the annotated request body once. Mirrors production shape:
#    [{"type": "text", "text": "...", "cache_control": {...}}]
system_blocks = annotate_system_blocks(my_system_text, ttl="1h")

# 2) Reuse the same `system_blocks` list across every call in the batch.
#    Anthropic hashes the block contents — keep them byte-identical or the
#    cache misses.
metrics = CacheMetrics()
for fixture in fixtures:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        system=system_blocks,        # <-- annotated once, reused N times
        messages=[{"role": "user", "content": fixture.user_prompt}],
        max_tokens=2000,
        temperature=0,
    )
    metrics.record(response.usage.model_dump())  # or .__dict__, depending on SDK

# 3) Inspect the hit-rate after the run.
print(metrics.summary(ttl_used="1h"))
```

### Hit-rate measurement

`CacheMetrics` accumulates the four input-token buckets Anthropic reports:

- `input_tokens` — uncached input (NOT cached, NOT a cache hit).
- `cache_creation_input_tokens` — written to cache this call.
- `cache_read_input_tokens` — served from cache this call (the "win").
- `output_tokens` — output (cache-agnostic).

Hit-rate formula:

```
hit_rate = cache_read / (cache_read + cache_create + uncached_input)
```

Interpretation thresholds (rules of thumb for batch workloads):

- `>0.95` — excellent: system prompt is stable and cache is being reused
  across nearly every call.
- `0.80 - 0.95` — good: occasional cache rebuilds (e.g. config flips, prompt
  edits between fixtures).
- `<0.50` — poor: investigate. Likely the system block content is differing
  between calls (whitespace? injected timestamp? non-deterministic format).

### Annotation contract

`annotate_system_blocks` accepts:

- A plain string → wrapped into a single text block.
- A list of content blocks → only the **last** block is annotated (cache
  breakpoint). Pre-existing `cache_control` keys on earlier blocks are
  stripped to avoid mixed-annotation surprises on the bill.

The function is **pure**: it deep-copies the input and returns a new list.
The caller's list and inner dicts are never mutated.

### What this module does NOT do

- Does NOT call the Anthropic API.
- Does NOT change production cache behavior. `src/components/primary_analyzer.py:219`
  stays byte-identical on this branch.
- Does NOT implement batch-API submission (T0.1).
- Does NOT implement USD cost translation (T0.2). `summary()` reports
  base-input-token-equivalents — multiply by your model's per-token price
  externally.

---

## Model Router (T0.4)

Module: `src/research_infra/model_router.py`
A/B harness: `scripts/research/haiku_quality_check.py`
Fixtures: `scripts/research/fixtures/regime_classification_50.jsonl`

`model_router.py` is the central decision point for *which model* a
research-LLM call uses. It exists because Phase 1 will spawn many
ad-hoc analysis scripts — without a router each script tends to pick
its own model (expensive + inconsistent) and could silently drift a
trading-decision call onto a cheaper model.

### TaskType taxonomy

| TaskType                | Default model                  | Default effort | When to use                                                                                           |
| ----------------------- | ------------------------------ | -------------- | ----------------------------------------------------------------------------------------------------- |
| `trading_decision`      | `claude-sonnet-4-6` (immutable)| `max`          | The MSO-gate primary-analyzer call (Component 3A). **Never override.**                                |
| `regime_classification` | `claude-haiku-4-5-20251001`    | `high`         | Labeling H4-swing regime windows (range / trending / reversal) given features.                        |
| `metadata_extraction`   | `claude-haiku-4-5-20251001`    | `medium`       | Pulling structured fields out of free-text rationale, postmortem notes.                               |
| `decay_analysis`        | `claude-haiku-4-5-20251001`    | `high`         | Summarising/labeling time-sliced trade-outcome cohorts during decay-diagnostic studies.                |
| `summary_aggregation`   | `claude-haiku-4-5-20251001`    | `medium`       | Aggregating multi-document or multi-trade summaries (monthly-decay narrative, council digests).        |
| `other`                 | `claude-sonnet-4-6`            | `high`         | Conservative escape hatch. Callers must opt in explicitly — the router never falls back here silently. |

### Hard rule — `trading_decision` is immutable

The MSO-gate (Component 3A primary-analyzer) call **must** continue to
use Sonnet 4.6 effort=max. Empirical evidence (memory
`project_opus_vs_sonnet_p2c.md`):

- CR 38% (Sonnet) vs 19% (Opus)
- WR 69.6% (Sonnet) vs 60.9% (Opus)
- 4.4× cheaper than Opus

Any constructed routing table whose `trading_decision` value does not
match the immutable `(claude-sonnet-4-6, max)` entry is rejected at
construction time with `RouterMisconfigurationError`. There is no
recovery path — this is intentional. A silent default that allowed
Haiku for trading decisions would degrade edge quality below detection.

### When to route to Haiku

- Task is **not** a trading decision.
- The task is **classification or extraction**, not synthesis or
  reasoning over the system's edge.
- An A/B agreement check (`scripts/research/haiku_quality_check.py`)
  has been run with at least 50 fixtures and Haiku-vs-Sonnet agreement
  is `≥ 0.85`.
- The task's downstream consumer is itself a research artifact, not a
  live trading decision.

### When to escalate (back to Sonnet 4.6)

- A/B agreement falls below 0.85 on the live fixture set.
- The task type begins to influence trading decisions (e.g. a regime
  feature gets wired into `permissions.py`). At that point it ceases
  to be "non-trading research" and the routing should escalate.
- The fixture distribution shifts materially (new instruments, new
  session windows). Re-run the A/B before continuing to route to
  Haiku.

### Dry-run pattern

```python
from src.research_infra.model_router import ModelRouter

router = ModelRouter(dry_run=True)
model_id, effort = router.route("regime_classification")
# Logs:  WARNING [DRY-RUN] Router would route task_type='regime_classification'
#        to model='claude-haiku-4-5-20251001' effort='high' — caller is
#        responsible for skipping the live API call.
if router.dry_run:
    label = "stubbed_label"
else:
    label = call_anthropic(model_id, effort, prompt)
```

The router itself never calls the API. Honoring `dry_run` is the
caller's responsibility — the router just returns the *intended*
routing tuple and logs the `[DRY-RUN]` warning.

### A/B validation gate (before promoting a Haiku target)

Run `scripts/research/haiku_quality_check.py` with the appropriate
`--task-type` and confirm the printed summary shows:

- `n_evals ≥ 50`
- `Haiku vs Sonnet ≥ 0.85`
- `Promotion threshold ... MET`

The harness writes a JSON sidecar (`*_50.ab_summary.json`) next to the
fixture file. Commit the sidecar so future sessions can audit when a
routing decision was last validated.

The shipped harness runs **mocked-only**. Real-API mode is intentionally
disabled in this commit; unblocking it requires:

1. Explicit CEO authorization for the API spend.
2. Production-faithful prompt templates wired into the harness.
3. The T0.2 cost-tracking wrapper (Phase 0 Week 1).

When all three land, set
`GTOS_HAIKU_QUALITY_CHECK_ALLOW_LIVE=1` and pass `--live`. Until then
the harness exits with code 2 and a clear message.

### Adding a new TaskType

1. Add the new literal to `TaskType` and `VALID_TASK_TYPES` in
   `model_router.py` (synced).
2. Add a default routing entry to `DEFAULT_ROUTING_TABLE` (default to
   Sonnet 4.6 effort=high until A/B-validated).
3. Add the new pin to the test in
   `tests/research_infra/test_model_router.py::TestDefaultTablePin`.
4. If the new task type is a Haiku promotion candidate, ship a
   `scripts/research/fixtures/<task_type>_50.jsonl` fixture file
   (≥ 50 entries) and run the harness.

---

## Out of scope (Wave 1)

Each Wave 1 module ships strictly additive — no production code path is
modified. Production trading-decision calls remain on the live
`primary_analyzer.py` → Sonnet 4.6 effort=max path. The infra in this
package is for offline / shadow research workloads only.
