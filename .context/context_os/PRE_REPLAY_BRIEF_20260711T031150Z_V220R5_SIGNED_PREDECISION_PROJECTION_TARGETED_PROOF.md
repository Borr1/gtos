# V220R5 Signed Predecision Projection Targeted Proof

Generated UTC: 2026-07-11T03:11:50Z.

## Snapshot And Running State

- Base commit: `cc4bf946a`; the current B7.2 implementation remains a scoped
  dirty batch.
- No replay, pytest, compiler, builder, verifier, or subagent process is
  running.
- V220R4 completed its bounded campaign and wrote the source, decision,
  candidate, scorecard, missed, bucket, packet-sidecar, and partial-summary
  artifacts. It did not write a certifiable final summary.
- V220R4 row counts are source/decision/candidate/scorecard/order/trade/missed
  `29/4608/1651/192/0/0/1651`.
- Broker/live/final remain false. Local replay/package authority remains full.

This smoke proves or disproves the local signed-authority consumer repair. It
does not prove hostile five-day value, broad holdout performance, total
reservoir conversion, final selection, or live readiness.

## Baselines And Scope

The newest completed broad behavioral replay remains V219 hostile five-day:

- candidate/scorecard/order/trade/missed `25006/288/68/23/24972`;
- W/L/F `14/9/0`;
- net/gross/final R `-2.82440031/-0.79141028/-0.79141028`;
- cash PnL `+204.17530212`;
- full/reduced fills `17/6`;
- executed REFUSED/source-gap `0/0`.

V218 is the direct two-day/three-symbol behavioral comparator: 3 trades,
W/L/F `3/0/0`, net/gross/final R
`+1.10761535/+1.35101129/+1.35101129`, cash PnL `+989.52983936`, and
full/reduced fills `1/2`.

V89D, V90, and V92 are five-day hostile comparators, not denominator-equivalent
to this bounded proof:

| Run | Candidate / scorecard / order / trade | W/L/F | Net / gross / final R | Cash PnL |
| --- | --- | --- | --- | --- |
| V89D | `25006/288/243/56` | `41/15/0` | `34.84520454/39.93441037/39.93441037` | `8178.90660707` |
| V90 | `25006/288/233/51` | `37/14/0` | `28.84201157/33.36349114/33.36349114` | `6371.80465431` |
| V92 | `25006/288/239/51` | `37/14/0` | `29.35570236/33.93212860/33.93212860` | `6228.63096022` |

These broad baselines remain transfer references only until current code runs
on the same five-day denominator.

## V220R4 Root Evidence

V220R4 removed the nested fill-source sentinel defect but exposed two later
consumer-contract failures:

1. Final serialization could leave current effective executable aliases true
   on a final-blocked row and could evaluate a designated envelope through
   stale outer projections. Current code demotes only current effective aliases,
   preserves pre-final truth, and canonicalizes the designated signed envelope
   from its own payload and hash.
2. Eight scorecard rows had a valid exact-instance signed payload and signed
   order authority but risk finalization rejected them because mutable
   `selected_policy_expected_net_calibration_required=false` overrode the
   immutable signed value `true`.

Frozen V220R4 audit under current code:

- candidate signed projections `12/12` valid;
- scorecard signed projections `8/8` valid;
- missed signed projections `12/12` valid;
- calibration projection matches `12/12`, `8/8`, and `12/12` respectively;
- zero post-projection hash or selected-policy mismatch.

## Same-Root Repair Contract

The signature freezes exact candidate identity and causal predecision quality.
It does not freeze later broker-cost, lifecycle, fill-floor, or order-permission
outcomes.

- Immutable payload identity, member axes, expected net R, probability,
  confidence, source completeness, execution-fillability tuple, and
  selected-policy calibration project to candidate, packet, option,
  decision-input, probe, risk-finalizer, and order-materialization consumers.
- Signed admission-time cost and order triplets remain available under prefixed
  attribution fields for proof.
- Current broker-cost, fill-floor, lifecycle, and order denials remain the
  effective authority and may fail closed without mutating the signature.
- The route verifier rejects a valid signed order authority that is later
  blocked by `current_signed_authority_projection_mismatch:*`.
- No date, symbol, session, outcome, or loss-bucket rule was added.

Classification: correctness and executable-transfer repair. It is not a cost
bypass and not opportunity suppression.

## Current Dirty Snapshot

Active implementation/test ownership for this batch:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_timewarp_scheduler_materialization.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_build_source_bound_execution_parity.py`
- `tests/test_denominator_to_deployment_verifier.py`

The worktree also contains pre-existing unrelated Context OS, selector,
origin-generator, source-lifecycle, route-harness/analyzer/builder/comparator,
test, verification-result, and historical-ledger deletion changes. They remain
preserved and are outside this checkpoint's staging boundary.

## Subagent Reconciliation

- Mendel: candidate-instance identity and signed-envelope ownership findings are
  incorporated and covered by exact-instance/hash tests.
- Herschel: alias/source-boundary and immutable-versus-current authority
  findings are incorporated in producer, consumer, and verifier contracts.
- Wegener: exact-time/fillability provenance findings are incorporated in the
  atomic fill tuple and nested-source precedence tests.
- No subagent process or unreconciled return remains for this checkpoint.

## Root-Cause Chain

| Stage | State | Current contract |
| --- | --- | --- |
| source-bound -> candidate | FIXED/PRESERVE | Exact matched member axes authorize; unmatched carried IDs are diagnostic. |
| candidate -> selector | FIXED/PRESERVE | Candidate-instance packet and causal nested fillability outrank weak stale aliases. |
| selector -> scheduler | FIXED/PRESERVE | One exact-instance finalized signature owns quality, identity, order, and fill atoms. |
| scheduler -> risk | REPAIRED/PENDING REPLAY | Immutable signed predecision atoms project to every finalizer consumer; later current gates are not overwritten. |
| risk -> order | REPAIRED/PENDING REPLAY | Signed triplet and current effective denial remain separate; either signed denial or current denial fails closed. |
| order -> lifecycle -> fill | OPEN AFTER TRANSFER | Honest fill-floor/lifecycle denial remains; V220R5 must expose the next exact blocker if no order/fill transfers. |
| fill -> exit | DEFERRED B7 | No V220R4 fills exist; exit policy is not tuned from a zero-fill slice. |
| ledger/verifier | REPAIRED/PENDING REPLAY | Final-blocked aliases are demoted without mutating the signed envelope; verifier scans projection drift. |

## Verification Barrier

- Python compile: passed.
- Six-file scheduler/runtime/materialization/bridge/parity/verifier barrier:
  `1602 passed`.
- Seven directly affected authority/current-denial contracts: `7 passed`.
- Scoped `git diff --check`: passed.
- Only warning is the existing unknown pytest `asyncio_mode` option.

## Expected Effect And Decision Rule

- Candidate and scorecard counts should remain near `1651/192`; deleting
  opportunity is a failure.
- The eight valid signed scorecard rows must no longer fail for stale
  selected-policy projection.
- Candidate -> scorecard transfer should remain stable; scorecard -> risk/order
  transfer should increase, or each surviving row must expose a different exact
  causal blocker.
- Current cost REFUSED/source-gap rows remain non-executable and executed counts
  must remain `0/0`.
- Current fill-floor/lifecycle/order denials must remain effective even when the
  admission-time signed order triplet was true.
- Order -> fill and fill -> trade effects are not precommitted; ordered ticks,
  current lifecycle, and current risk remain authoritative.
- Report candidate/scorecard/order/fill/trade transfer, missed positive and
  negative R, selected/skipped/delayed/expired/filled, full/reduced risk,
  risk cash/pct, net/gross/final R, cash PnL, W/L/F, stress, and Monte Carlo.
- Help: final summary certifies; projection mismatch is zero; signed candidates
  reach the next honest stage; no cost/source-gap execution; opportunity is not
  suppressed.
- Fail: the same mutable projection mismatch recurs, the run cannot certify,
  current denials are reopened, or opportunity disappears to manufacture a
  headline.
- Expose-next-root: projection is clean but transfer stops at a different exact
  risk/order/lifecycle/fill blocker. That blocker becomes the next B7 batch.

## Targeted Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R5_SIGNED_PREDECISION_PROJECTION_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Existing V220R2 storage protections carry forward to V220R5. No cleanup is
authorized inside this active targeted batch. Before any later broad replay,
record the then-current active artifact requirements and perform a new bounded
storage review.
