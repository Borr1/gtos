# V220R8 Session Namespace Route Projection Targeted Proof

Generated UTC: 2026-07-11T04:13:14Z.

## Snapshot And Process State

- Base commit: `cc4bf946a`; the B7.2 authority-integrity implementation is a
  scoped dirty batch.
- No replay, test, builder, verifier, or subagent process is running.
- V220R7 is the latest completed targeted replay. It completed and certified;
  it must not be restarted or duplicated.
- Broker/live/final remain false. Local replay/package authority remains full.

This smoke proves or disproves one local producer-to-consumer repair. It does
not prove hostile-five-day value, non-hostile value, broad holdout performance,
reservoir conversion, final selection, or live readiness.

## Baselines And Latest Result

V219 remains the latest hostile-five-day value baseline: 23 trades, W/L/F
`14/9/0`, net/gross/final R `-2.82440031/-0.79141028/-0.79141028`, cash PnL
`+204.17530212`, full/reduced trades `17/6`, and executed REFUSED/source-gap
`0/0`.

V220R6 and V220R7 are the same bounded 2026-05-13..14, XAUUSD/USDCAD/USDJPY
structural slice. Both produced source/decision/candidate/scorecard/order/trade/
missed `29/4608/1651/192/0/0/1651`, diagnostic scoreable missed
`366/-118.10784844R`, no stress/MC trades, and zero R/cash because no order
materialized. V220R7 therefore did not improve transfer.

The V220R7 risk-finalizer reasons remained:

- broker-cost authority blocked/non-executable: `857` probes;
- package executable authority required/not met: `769` probes;
- honest marketable quality denials: `5` probes, split into 2 cost-ceiling and
  3 unit-risk/ATR denials;
- passive-limit-too-close preflight: `7` probes.

## Exact Same-Root Failure

V220R7 proved that the signed route object reaches the finalizer, but the route
session did not reach the immediate-fill consumer atomically:

1. Four scorecard windows contain the seven affected finalizer probes.
2. Each affected probe has a valid exact-instance signature, current route
   permission `true`, and a route envelope with a concrete configured session.
3. The envelope carries `route_session=moonshot_hNN_NN`, while the order row
   retained only raw provenance `route_session=off_configured_session`.
4. Shared hour-token consumers incorrectly required `hNN_NN` length 7; the
   real canonical form has length 6. Derived execution-session authority was
   therefore discarded across scheduler, replay, package, bridge, parity, and
   builder consumers.
5. Immediate fill returned
   `off_configured_session_immediate_marketable_limit_disabled`; only then did
   the passive-only guard fire.

## Same-Root Batch

Files/components changed:

- `src/components/session_namespace.py`: one canonical consecutive-hour token
  and alias contract;
- `src/components/ultimate_candidate_package.py`: package session aliases;
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: configured
  execution-session recognition;
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: selected
  route-envelope session projection, immediate-fill consumption, and finalizer
  proof aliases;
- selected-package bridge, source-bound parity builder, and denominator builder:
  identical session aliases;
- route verifier: rejects signed immediate routes stranded by stale session
  projection, including nested historical probe rows;
- focused tests across all producers and consumers.

Classification: correctness, executable-transfer, and diagnostic/ledger repair.
It adds no suppression, outcome-fit bucket, cost bypass, risk bypass, or live
authority.

Current explicit route denial still wins. Route-session projection occurs only
when the current flat route flags and the selected nested route all allow the
immediate path. Raw off-session provenance remains preserved separately.

## Chain Status

- source-bound -> candidate: fixed/preserve exact member-axis identity;
- candidate -> selector: fixed/preserve atomic predecision fillability;
- selector -> scheduler: fixed/preserve immutable signed authority;
- scheduler -> risk: fixed/preserve selected-policy and risk expression;
- risk -> order: V220R7 failed session projection; repaired for V220R8;
- order -> lifecycle/fill: next honest stage after V220R8 transfer;
- fill -> exit: deferred until this slice produces terminal fills;
- ledger/verifier: repaired to expose preflight session atoms and reject drift.

No active or unreconciled subagent return remains. Earlier Mendel, Herschel, and
Wegener findings remain incorporated; no new agent wave is allowed before this
checkpoint is parsed.

## Verification Before Replay

- Python compile: passed.
- Exact focused contracts: `14 passed`.
- Full scheduler/runtime/materialization/package/bridge/parity/verifier barrier:
  `1645 passed`.
- Frozen V220R7 verifier audit: four scorecard windows containing seven probes
  reproduce `signed_immediate_marketable_route_concrete_session_projection_drift`.
- Scoped diff check and post-run route audits remain to run at the checkpoint
  barrier.

## Expected Measurable Effect

- Candidate and scorecard rows remain near `1651/192`; deleting opportunity is
  failure.
- Seven signed current-allowed routes no longer report off-configured-session or
  passive-limit-too-close; they advance to order/lifecycle/fill handling.
- The 2 cost-ceiling and 3 unit-risk/ATR denials remain closed.
- Candidate -> scorecard is behavior-neutral; scorecard -> order should increase
  from zero if no deeper current blocker exists; order -> fill is measured, not
  assumed.
- Executed REFUSED/source-gap remains `0/0`.
- Full/reduced risk, missed positive/negative R, trade count, W/L/F,
  net/gross/final R, cash PnL, risk cash/pct, stress, and MC are reported even if
  the next honest lifecycle/fill blocker keeps terminal trades at zero.

Pass: the seven exact routes advance and current denials remain closed.
Failure: session/passive drift remains, current denials reopen, opportunity is
deleted, or certification fails. If the route advances but a later lifecycle,
cluster, expiry, ordered-tick, or exit constraint blocks it, that exact stage is
the next deeper flaw rather than grounds to revert this truth repair.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R8_SESSION_NAMESPACE_ROUTE_PROJECTION_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Existing protected artifact requirements extend through V220R8. No deletion,
move, eviction, or Git-clean is authorized during this bounded proof. A fresh
bounded storage review remains mandatory before any later broad replay.
