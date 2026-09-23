# V220R9 Exact Package Route Precedence Targeted Proof

Generated UTC: 2026-07-11T04:24:42Z.

## Snapshot And Process State

- Base commit: `cc4bf946a`; current B7.2 implementation remains a scoped dirty
  integration batch.
- No replay, test, builder, verifier, or subagent process is running.
- V220R8 is the latest completed targeted replay and must not be duplicated.
- Broker/live/final remain false. Local replay/package authority remains full.

This is a two-day, three-symbol local transfer proof. It cannot prove hostile
five-day value, non-hostile value, broad holdout, total reservoir conversion,
final selection, or live readiness.

## Baseline And V220R8 Result

V219 remains the hostile-five-day value baseline: 23 trades, W/L/F `14/9/0`,
net/gross/final R `-2.82440031/-0.79141028/-0.79141028`, cash PnL
`+204.17530212`, full/reduced trades `17/6`, and executed REFUSED/source-gap
`0/0`.

V220R8 completed and certified with unchanged local counts:

- source/decision/candidate/scorecard/order/trade/missed:
  `29/4608/1651/192/0/0/1651`;
- W/L/F, net/gross/final R, cash, risk cash/pct, stress, and MC: all zero due
  to zero terminal execution;
- diagnostic scoreable missed rows/R: `366/-118.10784844R`;
- risk-finalizer reasons: cost blocked `857`, package authority not met `769`,
  honest marketable quality denials `5`, passive-too-close `7`;
- executed REFUSED/source-gap: `0/0`.

V220R8 did repair the preceding layer: all seven signed current-allowed probes
now resolve a concrete configured execution session, sourced from `kill_zone`.
No V220R7-style session projection drift remains.

## Exact Remaining Root

For all seven routes, V220R8 records:

- exact-instance signed authority valid with no validation failures;
- signed selector action `open-reduced-risk`;
- concrete configured execution session true;
- selected package marketable route allowed true;
- expected route reason;
- immediate consumer route authority false.

The immediate consumer read auxiliary
`router_refusal_immediate_marketable_execution_authority_allowed=false` before
the exact package route's true fields. That auxiliary false means one route
derivation was not used; it is not a current package execution denial. Four
scorecard windows containing all seven probes reproduce
`signed_immediate_marketable_exact_route_overridden_by_auxiliary_false`.

## Same-Root Repair

The immediate-fill consumer now uses this authority order:

1. current flat exact package route fields; any explicit false remains terminal;
2. selected nested package route fields when current flat fields are absent;
3. generic/router-refusal fields only when no package route decision exists.

The consumer and flattened finalizer ledger record the deciding tier plus flat,
nested, and generic atoms. Current route-denial fixtures still fail closed;
exact package true with generic false now passes. The verifier distinguishes
session projection drift from auxiliary-route precedence drift.

Classification: correctness, executable-transfer, and diagnostic/ledger repair.
It adds no suppression, risk/cost bypass, outcome-fit rule, or live authority.

## Chain Status And Files

- source-bound -> candidate -> selector -> scheduler -> risk: fixed/preserve;
- risk -> order: session projection fixed in V220R8; exact route precedence
  repaired for V220R9;
- order -> lifecycle/fill: next honest stage if these routes advance;
- fill -> exit: deferred until this bounded slice produces fills;
- ledger/verifier: exact precedence source and atoms are now proof-visible.

Affected files remain the current shared session/package/scheduler/timewarp,
selected bridge, parity/builder, verifier, and focused-test batch recorded in
the root-cause map. No active or unreconciled subagent finding remains.

## Verification Before Replay

- Python compile: passed.
- Exact route/session and verifier contracts: passed.
- Full scheduler/runtime/materialization/package/bridge/parity/verifier barrier:
  `1645 passed`.
- Frozen V220R8 verifier audit: session drift `0`; exact-route auxiliary-false
  precedence drift in 4 scorecard windows containing 7 probes.
- Scoped diff check and post-run route audits remain checkpoint work.

## Acceptance And Expected Effect

- Candidate/scorecard counts stay near `1651/192`; deletion is failure.
- The seven signed current-allowed routes report exact package route authority
  source, bypass passive-only handling, and reach order/lifecycle/fill.
- The two broker-cost-ceiling and three unit-risk/ATR denials remain closed.
- Executed REFUSED/source-gap stays `0/0`.
- Report order/trade count, W/L/F, net/gross/final R, cash PnL, risk cash/pct,
  full/reduced risk, selected/skipped/delayed/expired/filled, missed
  positive/negative R, stress, MC, and the next exact blocker.
- If the seven routes advance but a current lifecycle, cluster, expiry,
  ordered-tick, or exit constraint blocks them, that is the next deeper stage;
  it does not invalidate the truth repair.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R9_EXACT_PACKAGE_ROUTE_PRECEDENCE_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Existing artifact protection extends through V220R9. No deletion, move,
eviction, or Git-clean is authorized during this bounded proof. A fresh bounded
storage review remains mandatory before any later broad replay.
