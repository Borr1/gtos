# V220R7 Immediate Route Materialization Targeted Proof

Generated UTC: 2026-07-11T03:50:00Z.

## Snapshot

- Base commit: `cc4bf946a`; current B7.2 implementation remains a scoped dirty
  batch.
- No replay, test, builder, verifier, or subagent process is running.
- V220R6 is the latest completed targeted replay and is fully certified.
- Broker/live/final remain false. Local replay/package authority remains full.

This smoke proves or disproves the semantic-source and selected immediate-route
materialization batch. It does not prove five-day value, broad holdout
performance, reservoir conversion, final selection, or live readiness.

## V220R6 Result

- source/decision/candidate/scorecard/order/trade/missed:
  `29/4608/1651/192/0/0/1651`;
- W/L/F, net/gross/final R, cash, risk cash/pct: all zero because no order or
  fill materialized;
- diagnostic scoreable missed rows/R: `366/-118.10784844R`;
- stress/MC trade counts: `0/0`;
- executed REFUSED/source-gap: `0/0`.

The V220R6 repair succeeded: selected-policy calibration hash failures fell
from `7` to `0`. Those same seven candidates then failed
`passive_limit_too_close_predecision_guard`.

## Exact Root

The passive guard was a downstream symptom:

1. The signed payload uses source status `complete`; the selected bridge/runtime
   normalizer uses `source_completeness_present`. Both represent the same
   complete evidence state, but raw-string hashing invalidated all 12 signed
   envelopes at immediate-fill validation.
2. The scheduler/risk probe held the exact selected
   `package_marketable_entry_guard_replay_route`, including a concrete execution
   session and immediate-route decision. Order materialization did not copy that
   route object or flat route flags into the preflight candidate.
3. Without a valid signed immediate route, the seven marketable limits were
   misclassified as passive waiting orders and hit the passive-too-close guard.

The 12 risk-bearing candidates have two independent groups:

- 7 immediate routes authorized by scheduler quality, signed order authority,
  source-safe closed-M15 price/time, broker cost, and concrete execution
  session;
- 5 current denials that remain closed: 2 exceed the broker-calibrated expected
  cost ceiling and 3 exceed the immediate-entry unit-risk/ATR quality ceiling.

## Same-Root Repair

- Canonicalize only known positive source-completeness labels (`complete`,
  `source_complete`, `source_completeness_present`, and
  `source_complete_for_timewarp_candidate`) to one semantic value for signed
  projection comparison.
- Missing, degraded, source-gap, and incomplete labels remain distinct and
  fail closed.
- Project exact selected marketable-route objects, flat route flags, and
  execution-session aliases from scheduler/risk into order materialization.
- Current risk-route fields have precedence over stale option/candidate fields;
  an explicit current false still wins.
- Preserve exact signed-validation failures in immediate-fill and preflight
  diagnostics instead of collapsing them to a generic invalid-signature label.

Classification: correctness, executable-transfer, and diagnostic repair. It
adds no suppression, cost bypass, outcome bucket, or live authority.

## Frozen V220R6 Proof Under Current Code

- valid signed authority: `12/12`;
- selected marketable route allowed: `7/12`;
- source-safe immediate fill applied: `7/12`;
- preserved current denials: `5/12`;
- immediate-fill reasons: 7
  `source_safe_predecision_limit_marketable_at_decision`, 5
  `off_configured_session_immediate_marketable_limit_disabled` after current
  route denial;
- no signed validation failure remains on the seven authorized routes.

## Verification

- Direct semantic-source, route materialization, current-denial, passive-limit,
  and exact-diagnostic tests: passed.
- Six-file scheduler/runtime/materialization/bridge/parity/verifier barrier:
  `1608 passed`.
- Python compile and scoped `git diff --check`: passed.
- No active or unreconciled subagent remains.

## Acceptance

- Candidate/scorecard counts remain near `1651/192`; suppression fails.
- Selected-policy hash mismatch and semantic source-status mismatch remain zero.
- The seven authorized routes must bypass the passive-wait-only guard and reach
  order/lifecycle/fill handling.
- The 2 cost-ceiling and 3 unit-risk/ATR-quality denials remain closed.
- Explicit current route false remains authoritative.
- Executed REFUSED/source-gap remains `0/0`.
- Report order/fill/trade counts, selected/skipped/delayed/expired, missed
  positive/negative R, W/L/F, net/gross/final R, cash, risk cash/pct,
  full/reduced risk, stress, MC, and any next exact blocker.
- Success: `7` authorized immediate paths advance, current denials remain, and
  no opportunity is deleted.
- Failure: passive-too-close still blocks marketable routes, route/session truth
  disappears, current denials reopen, or certification fails.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R7_IMMEDIATE_ROUTE_MATERIALIZATION_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Existing storage protection extends through V220R7. No cleanup is authorized
during this bounded run. A fresh bounded storage review remains mandatory before
any later broad replay.
