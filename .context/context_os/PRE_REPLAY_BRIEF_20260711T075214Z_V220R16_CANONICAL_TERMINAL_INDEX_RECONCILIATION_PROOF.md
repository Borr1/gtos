# V220R16 Canonical Terminal-Index Reconciliation Proof

Generated UTC: 2026-07-11T07:52:14Z.

## Current State

- V220R15 is the latest completed bounded replay. It exactly reproduced V220R14
  behavior: `29/4608/1651/192/6/3/1648` source/decision/candidate/scorecard/
  order-event/trade/missed rows; W/L/F `2/1/0`; net/gross/final R
  `+0.18799082/+0.29037839/+0.29037839`; cash PnL `+18.79934014`; 3 reduced-risk
  source-safe immediate fills; no guarded fallback or executed REFUSED/source-gap.
- The V220R15 terminal proof failed before parity/build/verifier reruns: terminal
  indexing consumed raw order/trade rows before their canonical ledger
  normalizer had derived `order_bound`/`trade_bound`. It therefore selected an
  order-stage surface and later serialization restored `final_blocked` on the 3
  selected candidate and scorecard rows.
- No behavior policy changed. V220R15 summary behavior remains valid bounded
  evidence; its terminal reconciliation fields are failed partial proof only.

## Repair And Focused Proof

Terminal indexing now canonicalizes a deep copy of each raw order/trade row
before ranking or projecting it. A filled trade therefore outranks its order
events and supplies exact current authority, order/trade IDs, fill truth, and
terminal status to the matching candidate and single-selected scorecard.

- The raw-terminal regression passes.
- In-memory application to the exact V220R15 artifact set yields 3 reconciled
  candidates and 3 reconciled scorecards, all `trade_bound`, current executable
  true, source ledger `trade`.
- Python compile passes.
- The full scheduler/runtime/materialization/bridge/parity/verifier barrier
  passes: `1623 passed, 1 warning`.

Classification: ledger truth correctness; behavior-neutral.

## Acceptance

- Exact V220R15 behavior and stress/MC numbers.
- Exactly 3 candidate and 3 scorecard rows reconcile from exact terminal trade
  bindings; all are `trade_bound`, current executable true, and retain prior
  false aliases under pre-reconciliation fields.
- Exactly 12 valid signed envelopes and zero cross-stage signature conflicts.
- Exactly 9 signed blocked candidates remain missed/current non-executable with
  explicit blockers and immutable proposal true.
- Selected/candidate-bearing context is complete; zero-trade scorecards are not
  context-required.
- Route transfer/context verifier bad counts are empty.
- Broker/live/final remain false; broker-real lifecycle truth remains honestly
  false and is not substituted by local replay truth.

This is a local structural proof, not broad or live-readiness evidence.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R16_CANONICAL_TERMINAL_INDEX_RECONCILIATION_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

No deletion, move, eviction, or Git-clean is authorized during this bounded
proof. A fresh storage checkpoint remains mandatory before any broad replay.
