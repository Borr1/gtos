# V104 19D Index-Omit Rerun Pre-Replay Brief

Generated: 2026-07-03T16:38:00Z

## Current Completed Evidence

- V92 hostile comparator `2026-05-13..2026-05-17`: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, W/L/F 37/14/0, 62 expired, 25006 candidate rows, 288 scorecards, 119 order rows, 894 candidate axes, 39 scorecard/order axes, 25 filled axes.
- V97 same-window comparator: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, W/L/F 23/24/0, 51 expired, same 25006 candidate rows and 288 scorecards, 98 order rows, 894 candidate axes, 29 scorecard/order axes, 18 filled axes.
- V97 added 19 trades worth +0.99594545R and removed 23 V92 trades worth +13.53876156R. This was downstream displacement, not candidate starvation.
- V104 hostile 5D: 49 trades, +25.69434914 net R, W/L/F 28/21/0, 6 expired, zero degraded passive distance-breach executions, zero cost/source-gap executions.
- V104 non-May 5D: 46 trades, +14.73101491 net R, W/L/F 26/20/0, 9 expired, zero degraded passive distance-breach executions, zero cost/source-gap executions.

## Interrupted 19D Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260619`
- Intended window: `2026-06-01..2026-06-19`
- Status: interrupted/stalled partial, not final proof.
- Last readable partial observed before filesystem stall: 80 trades, +27.18958285 net R, +33.49629305 gross/final R, W/L/F 44/36/0, 17 expired, missed +5528.09846201R / -19263.26714747R. This partial must not be treated as completed 19-day evidence.
- Failure point: process blocked in a file write to `_CANDIDATE_INDEX_LEDGER.jsonl`; subsequent reads of the interrupted artifact set stalled until stale helpers were killed.

## Infrastructure Repair

- Added `--omit-candidate-index-ledger` to the broad replay harness.
- One-day infra smoke prefix `BROAD_LIVE_AS_IF_REPLAY_CANDIDATE_INDEX_OMIT_INFRA_SMOKE_20260601` completed with final summary, candidate/candidate-index artifacts set to `null`, split stats preserving 7244 candidate rows, 96 scorecards, 13 order rows, 9 trades, +2.30923824 net R.
- This is a replay-infrastructure repair only. It does not change selector/scheduler/risk/order/lifecycle/exit policy.

## Next Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260619_INDEX_OMIT`
- Window: `2026-06-01..2026-06-19`
- Command adds `--omit-candidate-index-ledger` while preserving scorecard, order, trade, oracle, missed, bucket, source, comparison, and summary artifacts.

## Success / Failure Criteria

- Helped: run completes with broker/live/final false; no candidate-index JSONL is written; trade/order/missed/scorecard ledgers and final summary are materialized; zero cost-refused/source-gap executions and zero degraded passive distance-breach executions remain true.
- Failed: run still stalls on scorecard/missed writes or becomes positive only by suppressing opportunity.
- Next root patch after final parse: scheduler/risk-finalizer transfer if scorecard/order axes remain tiny; lifecycle/profit-harvest binding if score/order/fill transfer scales but stop-first/profit-harvest loss remains dominant.

Broker/live/final remain false. Local replay/package authority remains full.
