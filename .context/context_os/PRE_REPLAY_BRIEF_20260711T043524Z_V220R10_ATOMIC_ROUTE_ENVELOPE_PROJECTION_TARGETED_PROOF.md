# V220R10 Atomic Route Envelope Projection Targeted Proof

Generated UTC: 2026-07-11T04:35:24Z.

## Snapshot

- Base commit: `cc4bf946a`; B7.2 authority-integrity changes remain a scoped
  dirty integration batch.
- No replay, test, builder, verifier, or subagent process is running.
- V220R9 is completed and must not be duplicated.
- Broker/live/final remain false; local replay/package authority remains full.

This smoke proves one local producer/consumer repair. It cannot prove broad
value, holdout strength, full reservoir conversion, final selection, or live
readiness.

## Baseline And Latest Result

V219 remains the hostile-five-day value baseline: 23 trades, W/L/F `14/9/0`,
net/gross/final R `-2.82440031/-0.79141028/-0.79141028`, cash PnL
`+204.17530212`, full/reduced trades `17/6`, executed REFUSED/source-gap `0/0`.

V220R9 completed and certified with local source/decision/candidate/scorecard/
order/trade/missed `29/4608/1651/192/0/0/1651`, diagnostic scoreable missed
`366/-118.10784844R`, zero terminal R/cash/stress/MC, and unchanged risk-finalizer
reasons. It preserved the V220R8 session repair but did not transfer an order.

## Exact Root

The current risk authority stores one atomic nested route envelope. For each of
the seven signed current-allowed probes, that envelope has `allowed=true` and
`immediate_marketable_limit_route_allowed=true`. It intentionally does not
repeat the two flat package aliases.

Order materialization selected the current nested object, then filled its
missing flat aliases independently from lower-priority scheduler inputs. Those
stale inputs carried false/false. V220R9 therefore correctly reported the
`current_flat_package_marketable_route` tier but still consumed stale false
atoms. Four scorecard windows containing all seven probes reproduce the exact
precedence drift.

## Same-Root Repair

Route object and flat route atoms now come from one highest-priority surface:

1. select the first nonempty nested route from current risk, selected option
   quality, selected option, scheduler inputs, decision inputs, packets, then
   original candidate;
2. project the exact nested object plus effective route and immediate-route
   atoms from that same surface;
3. do not backfill those coupled atoms from a lower-priority surface;
4. preserve status/reason and generic router-refusal fields separately;
5. preserve explicit current route false and raw off-session provenance.

Both finalizer preflight and actual order simulation consume this same repaired
surface. Focused fixtures cover current nested true with stale selected false,
generic false, signed authority, configured session, and explicit current
denial.

Classification: correctness, executable-transfer, and diagnostic repair. It
adds no suppression, outcome-fit rule, cost/risk bypass, or live authority.

## Chain And Verification

- source-bound -> candidate -> selector -> scheduler -> risk: fixed/preserve;
- risk -> order: atomic route envelope repaired for V220R10;
- order -> lifecycle/fill: next honest stage after transfer;
- fill -> exit: deferred until fills exist;
- ledger/verifier: session and route-precedence drift remain distinguishable.

Python compile and exact contracts pass. The full scheduler/runtime/
materialization/package/bridge/parity/verifier barrier is `1645 passed`. No
active or unreconciled subagent return remains. Scoped diff check and post-run
route audits remain checkpoint work.

## Acceptance

- Candidate/scorecard counts stay near `1651/192`; deletion is failure.
- Seven signed current-allowed routes consume current risk atomic route true,
  bypass passive-only handling, and reach order/lifecycle/fill.
- The two cost-ceiling and three unit-risk/ATR denials remain closed.
- Executed REFUSED/source-gap remains `0/0`.
- Report orders/trades, W/L/F, net/gross/final R, cash, risk cash/pct,
  full/reduced risk, selected/skipped/delayed/expired/filled, missed positive/
  negative R, stress/MC, and the next exact blocker.
- A later honest lifecycle, cluster, expiry, ordered-tick, or exit block exposes
  the next stage and does not invalidate this truth repair.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R10_ATOMIC_ROUTE_ENVELOPE_PROJECTION_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Artifact protection extends through V220R10. No deletion, move, eviction, or
Git-clean is authorized during this bounded proof. A fresh bounded storage
review remains mandatory before any later broad replay.
