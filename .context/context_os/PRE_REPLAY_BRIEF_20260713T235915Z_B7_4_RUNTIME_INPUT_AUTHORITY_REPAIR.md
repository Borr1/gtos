# B7.4 Runtime-Input Authority Repair Pre-Replay Brief

Generated UTC: 2026-07-13T23:59:15Z.

## Decision

Commit the verified runtime-input authority checkpoint, then run one unchanged
V253 broad proof over 2026-06-01..19. Do not tune policy before parsing it.
Broker/live/final remain false; local replay and all 82 sleeves retain full
authority.

## Current State

- HEAD before this checkpoint: `0f9b7472a`.
- No replay, pytest, builder, verifier, or git-maintenance process is active.
- Latest route-certified broad replay remains V250 over 2026-06-01..05:
  35,191 candidates, 480 scorecards, 30 order events, 14 terminal orders,
  13 physical trades, 8/5/0, +7.82542991R gross/final,
  +7.03578717R net, -$68.02401535 cash, 2.10% summed risk.
- Hostile historical comparators V89D/V90/V92 remain window-specific:
  56/+34.84520454R, 51/+28.84201157R, and 51/+29.35570236R.
  They are not the V253 denominator.
- V249 remains the current route-certified hostile proof: 18 ordered-tick
  headline trades and +0.28044419R net.

## V251 Failure And Root Cause

V251 completed only its June 1-5 chunk before intentional interruption. It
preserved V250's 35,191 candidates and 480 scorecards but produced 35,191
missed rows and zero order/trade/oracle rows. This was not a policy result.

Sparse checkout retained the 82-row sleeve registry but dematerialized
`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`, the 1,101-row member-axis surface
consumed directly by executable package admission. The old runtime loader
silently returned no axes. Raw selector diagnostics survived, while signed
member-axis execution authority disappeared and every window went zero-trade.

All eight invalid V251 JSONLs were row-counted and SHA-256 bound in the B7.4
storage manifest before deletion. Its summary and partial summary remain.

## Same-Root Repair

Affected files/components:

- broad harness: exact-count/schema/identity/hash runtime-input preflight,
  stale-prefix reset, fail-before-`run_campaign`, partial/final provenance;
- route verifier: current compact-relational summary enforcement;
- focused tests: valid, missing, empty, corrupt, real hydrated, and execution-
  boundary fail-closed cases;
- storage retention: both runtime inputs protected against sparse cleanup.

Classification: execution correctness plus proof correctness. With valid
inputs, behavior is intentionally unchanged. With invalid inputs, the run now
fails explicitly instead of producing false zero-trade evidence.

Focused proof: compile and diff check pass; 588 tests pass. No subagent finding
is active or unreconciled.

## V252T Targeted Proof

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V252T_B7_4_RUNTIME_INPUT_AUTHORITY_REPAIR_20260602_XAUUSD`

- runtime inputs: 82 sleeves and 1,101 unique member axes at committed hashes;
- candidate -> scorecard -> pre-finalizer selection -> final selection ->
  terminal fill: `490 -> 92 -> 7 -> 1 -> 1`;
- order events / physical trade / missed: `2 / 1 / 489`;
- exact relational candidate union: 490/490, zero missing or duplicates;
- selected candidate: `broadorigin_2b237405cd0bdab19abdfa5a` at 10:15 UTC,
  XAUUSD SHORT, axis `member_axis:b7675740a77eb12478f575d2`;
- cost PASSED, signed authority valid, replay risk 0.10%, executed
  REFUSED/source-gap/unsigned rows `0/0/0`;
- M1-proxy diagnostic result: +2.0R gross, +1.96363578R net;
- headline result: zero rows because June 2 XAUUSD lacks ordered-tick terminal
  authority. This proves the local authority repair, not economic robustness.

## Root-Cause Chain

| Stage | State before V253 |
| --- | --- |
| source-bound -> candidate | Candidate surface intact; full 82-sleeve registry bound. |
| candidate -> selector | Raw action/quality truth preserved. |
| selector -> scheduler | Member-axis execution authority restored and signed. |
| scheduler -> risk | Seven targeted pre-finalizer entries, one valid final selection; risk provenance retained. |
| risk -> order/fill/lifecycle | One PASSED-cost signed order filled; no refused/source-gap execution. |
| fill -> exit | Targeted M1 proxy is diagnostic because ordered ticks do not cover June 2. |
| ledger/verifier | Exact relational union plus runtime-input contract green. |

## V253 Acceptance

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V253_B7_4_BROAD_JUNE_RUNTIME_INPUT_AUTHORITY_REPAIRED_20260601_20260619_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID`

Run repaired profile only, all configured symbols, full decision grid, compact
decision/scorecard/missed ledgers, candidate and candidate-index ledgers
omitted under the exact missed/order/trade union, and packet sidecar omitted.

The nested June 1-5 chunk must reproduce V250's behavior checksum:

- candidates / scorecards / order events / terminal orders / physical trades /
  missed: `35191 / 480 / 30 / 14 / 13 / 35177`;
- physical W/L/F and gross/final/net:
  `8/5/0`, `+7.82542991/+7.82542991/+7.03578717R`;
- no executed REFUSED, source-gap, or unsigned-authority row;
- exact candidate relational union and valid 82/1,101 runtime-input contract.

The full 19-day result must report candidate-to-scorecard/order/fill transfer,
missed positive/negative R, physical versus ordered-tick headline results,
cash, risk, W/L/F, stress/MC, full/reduced risk, and source-bound parity for
that exact window. A first-chunk mismatch fails behavior-neutrality and exposes
the next deeper flaw. A matching first chunk plus completed 19-day artifacts
closes the runtime-input repair and supplies the evidence for the next Fable
B7 bottleneck. Neither outcome opens broker/live/final authority.
