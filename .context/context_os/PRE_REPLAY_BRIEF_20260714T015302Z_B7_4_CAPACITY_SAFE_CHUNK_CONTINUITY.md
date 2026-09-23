# B7.4 Capacity-Safe Chunk Continuity Pre-Replay Brief

Generated UTC: 2026-07-14T01:53:02Z.

## Decision

Repair broad replay capacity at the chunk boundary, prove one-day chunks are
behavior-identical to V250's five-day campaign, then rerun June 1-19. Do not
tune selector, scheduler, risk, fillability, or exits from the interrupted
V253 partial. Broker/live/final remain false; all 82 sleeves retain local
replay authority.

## Current Process And Evidence

- No replay, builder, verifier, pytest, or git-maintenance process is active.
- Latest completed route-certified replay remains V250 over 2026-06-01..05:
  35,191 candidates, 480 scorecards, 30 order events, 14 terminal orders,
  13 physical trades, 8/5/0, +7.82542991R gross/final, +7.03578717R net,
  -$68.02401535 cash, and 2.10% summed filled-trade risk.
- Historical window-specific comparators remain V89D `56/+34.84520454R`,
  V90 `51/+28.84201157R`, and V92 `51/+29.35570236R`; they are not the June
  denominator.
- V253 is an interrupted partial, not a completed economic proof. Its flushed
  June 1-5 chunk exactly matches V250 at candidate, scorecard, order, trade,
  missed, W/L/F, gross, final, net, headline, and diagnostic behavior.
- V253 was intentionally stopped after the worker retained a 52 GiB object
  graph, swap exceeded 27 GiB, and free disk fell to 5.1 GiB. SIGINT then spent
  more than twenty minutes in generation-2 collection before the catch block.
  The worker was terminated and the deterministic interrupted-summary helper
  promoted the valid partial. Raw partial ledgers were hash-bound before
  bounded deletion; both summaries remain.

## Dirty And Coordination State

- Active route-owned dirt before this batch is the storage retention manifest
  plus the root-map/brief/matrix/cursor updates for this capacity checkpoint.
- Existing runtime/data/knowledge/shadow dirt and `.context/LIVE_STATE.md` are
  unrelated and must not be staged or reverted.
- No subagent is active or unreconciled. Prior findings remain represented in
  the Fable matrix and current root-cause map.

## Root-Cause Chain

| Stage | State |
| --- | --- |
| source-bound -> candidate | Correct for June 1-5; 82/1,101 runtime inputs valid. |
| candidate -> selector -> scheduler | Exact V250 behavior reproduced in V253 first chunk. |
| scheduler -> risk -> order -> fill -> exit | Exact V250 behavior reproduced; zero REFUSED/source-gap/unsigned execution. |
| ledger | Compact relational union exact for 35,191 candidates. |
| chunk/runtime capacity | OPEN: `run_campaign` materializes a large cyclic proof graph; completed chunk result/source caches are not obligatorily collected or evicted before the next chunk. |
| cross-chunk state | PARTIAL: broker account and selected order sequence persist, while the decision core is stateless, but this equivalence is not yet an explicit tested contract. |

## Same-Root Patch Batch

Affected components:

- `run_broad_live_as_if_replay_harness.py`: make completed-chunk source-cache
  release and explicit post-result GC part of capacity-safe execution; expose
  a deterministic chunk-continuity/capacity contract in partial/final output;
  preserve the same `SimulatedBroker` account and monotonic order sequence.
- `tests/test_broad_replay_repair_config.py`: prove cache eviction, explicit
  collection placement, account/order-sequence continuity, and output contract.
- `verify_denominator_to_deployment_execution.py` and focused verifier tests:
  require the capacity contract for the current broad proof without rejecting
  historical summaries.
- current root map, Fable matrix, cursor, and storage manifest: bind the repair
  and its focused/behavioral proof.

Classification:

- correctness repair: prevent an otherwise valid broad proof from terminating
  through host resource exhaustion while preserving state continuity;
- performance/scalability repair: bound completed-chunk object and source-cache
  retention;
- diagnostic/proof repair: record chunk continuity, cache release, and explicit
  collection outcomes for deterministic verification.

## Expected Effect And Acceptance

- Candidate -> scorecard -> order -> fill transfer: exactly V250 on June 1-5.
- Missed positive/negative R and diagnostic scoreability: exactly V250 on that
  same window; no opportunity suppression is accepted.
- Trades and W/L/F: `13` physical and `8/5/0`; headline `4` and `3/1/0`.
- Physical gross/final/net: `+7.82542991/+7.82542991/+7.03578717R`.
- Headline gross/final/net: `+1.92353135/+1.92353135/+1.59506223R`.
- Executed REFUSED/source-gap/unsigned rows: `0/0/0`.
- Full/reduced physical fills: `2/11`.
- One-day chunk mode must keep one broker account object and a monotonic
  selected-order sequence across all five days, evict completed day-scoped
  source caches, and explicitly collect only after result/source references
  are released.
- Helped: focused tests pass and the five one-day chunks reproduce V250 exactly
  without pathological retained memory; then June 1-19 may run.
- Failed: any trade identity/value/count changes, account/order sequence reset,
  cost/source authority leak, or memory still grows cumulatively by chunk.
- Deeper flaw: one-day chunks remain individually bounded but final aggregation
  or JSONL growth still exhausts resources; then the next repair is resumable
  aggregation/output partitioning, not policy tuning.

This proof remains window-bound. It does not prove total source-reservoir
conversion or open broker/live/final authority.

## Focused Implementation Checkpoint

Verified UTC: 2026-07-14T02:08:54Z.

- Capacity-safe chunk cleanup and continuity are implemented across the
  harness producer, route verifier consumer, and focused tests.
- `py_compile` passes for the touched harness, verifier, and test modules.
- The focused harness, source-bound parity, and route-verifier suite passes:
  `592 passed`, zero failures; the only warning is the pre-existing unknown
  `pytest` `asyncio_mode` option.
- Scoped `git diff --check` passes and all updated JSON control artifacts parse.
- This is behavior-neutral focused proof only. Behavioral equivalence remains
  open until V254T reproduces V250 exactly over 2026-06-01..05 with five
  one-day cleanup checkpoints and bounded memory.
