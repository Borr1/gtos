# Wave 1 Pilot — Empirical Verification Report

- Generated: 2026-04-26T08:24:18.832944+00:00
- Mode: LIVE API
- Model: `claude-haiku-4-5-20251001`
- N evals per run: 50
- Budget cap: $5.00

## Verdict

**Phase 0 verdict:** `COMPLETE`

## Per-run breakdown

| Run | n_calls | input_tok | output_tok | cache_read_tok | cache_create_tok | total_usd |
|---|---|---|---|---|---|---|
| A — sync no cache | 50 | 231350 | 300 | 0 | 0 | $0.232850 |
| B — sync 1h cache | 50 | 1100 | 300 | 230250 | 0 | $0.025625 |
| C — batch 1h cache | 50 | 1100 | 300 | 230250 | 0 | $0.024325 |

## Cache hit rates

- Run A (no cache, sanity baseline = 0.0): 0.0000
- Run B overall: 0.9952; post-warmup (skip first 5): 0.9952
- Run C overall: 0.9952; post-warmup (skip first 5): 0.9952

## Cost deltas

- Per-call cost: A=$0.00465700, B=$0.00051250, C=$0.00048650
- B vs A savings: 89.00% (cache effect)
- C vs A savings: 89.55% (cache + batch combined)
- C vs B savings: 5.07% (batch discount alone)
- Batch discount on input+output only: 50.00% (target 50% — verdict gate)
- Batch discount on TOTAL Run C cost: 5.07% (informational; dominated by cache_read which is NOT discounted by batch API)

## Cost reconciliation

- Overall PASS: True
- Max delta vs aggregate: $0.00000000

| Run | per-call sum (USD) | tracker aggregate (USD) | delta (USD) | budget (USD) | pass |
|---|---|---|---|---|---|
| pilot_run_a_sync_nocache | $0.23285000 | $0.23285000 | $0.00000000 | $0.00500000 | True |
| pilot_run_b_sync_cache1h | $0.02562500 | $0.02562500 | $0.00000000 | $0.00500000 | True |
| pilot_run_c_batch_cache1h | $0.02432500 | $0.02432500 | $0.00000000 | $0.00500000 | True |

## Per-run cost breakdown (USD)

| Run | input | output | cache_write | cache_read |
|---|---|---|---|---|
| A — sync no cache | $0.23135000 | $0.00150000 | $0.00000000 | $0.00000000 |
| B — sync 1h cache | $0.00110000 | $0.00150000 | $0.00000000 | $0.02302500 |
| C — batch 1h cache | $0.00055000 | $0.00075000 | $0.00000000 | $0.02302500 |

## Caveats

- Sample size: small N (default 50 per run). Adequate for plumbing verification, 
  not for statistical claims about the production-prompt cache hit rate.
- Single instrument prompt class (synthetic responder). The 2-3KB system block 
  is meaningful but smaller than the production primary-analyzer prompt.
- Pricing snapshot: PRICING_USD_PER_MTOK in cost_tracker reflects 2026-04 rates; 
  re-verify if Anthropic publishes revisions before a long-running campaign.
- Mocked-only runs synthesize the cache-read profile and cannot confirm Anthropic 
  side-real cache hits; only LIVE mode does that.

## Phase 0 completion criteria

- Run B per-call cost < Run A per-call cost: PASS
- Run C per-call cost < Run B per-call cost: PASS
- Run B cache hit rate post-warmup >= 80%: PASS
- Cost reconciliation: PASS
- Batch input+output discount in [40%, 60%]: PASS

## Mechanism interpretation

Run A is the no-cache baseline at $0.004657/call. Run B with sync 1h-TTL cache is $0.000513/call (89.0% cheaper than A). Run C with batch + 1h-TTL cache is $0.000487/call.

Run C cost less than Run B as expected. The batch + 1h-TTL cache stack delivers additive savings on this workload.
