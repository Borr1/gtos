# V146 B7 Unresolved Fill-Floor Targeted Behavior Report

Generated UTC: 2026-07-07T07:24:00Z

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED`

Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.

This is a bounded B7 targeted repair proof. It does not prove total reservoir conversion and must not be compared directly to the global 1.249M R diagnostic reservoir.

## Headline

- Candidate rows: 6633.
- Scorecard rows: 480.
- Order rows: 10.
- Filled trades: 2.
- Missed-opportunity rows: 6628.
- Packet sidecar rows: 7118.
- Source-universe rows: 62.
- Net R: `+0.55358905`.
- Gross R / final R: `+0.72340378` / `+0.72340378`.
- Cost R: `+0.16981473`.
- Cash PnL: `+55.36532564`.
- W/L/F: `2/0/0`.
- Order statuses: `pending_accepted=5`, `expired_unfilled=3`, `filled=2`.
- Risk decisions on filled trades: `open-reduced-risk=2`.
- Broker mutation, live broker authority, and final selection: false.

## Trade Rows

| Key | Time | Symbol | Side | Session | Action | Order Policy | Net R | Gross/Final R | Cost R | Cash PnL | Risk % |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `broadorigin_e59c330b1467251e45c3fd09@@2026-06-04T18:15:00+00:00` | 2026-06-04 18:15Z | XAUUSD | SHORT | `moonshot_h18_19` | `open-reduced-risk` | `limit_first_reduced_risk` | `+0.38818935` | `+0.47173923` / `+0.47173923` | `0.08354988` | `+38.81893500` | `0.1` |
| `broadorigin_a143179e468040fcc9bd5c71@@2026-06-05T19:00:00+00:00` | 2026-06-05 19:00Z | XAUUSD | SHORT | `moonshot_h18_19` | `open-reduced-risk` | `limit_first_reduced_risk` | `+0.16539970` | `+0.25166455` / `+0.25166455` | `0.08626485` | `+16.54639064` | `0.1` |

## Delta Versus V145

- Trade delta: `-1`.
- Net R delta: `+0.37023550`.
- Gross/final R delta: `+0.23987444` / `+0.23987444`.
- Cost R delta: `-0.13036105`.
- Cash PnL delta: `+35.11107348`.
- Added: one V144 winner restored, `e59c...18:15`, `+0.38818935R`.
- Removed unresolved-fill-floor V145 trades:
  - `b8a...14:30`, `-1.10446455R`.
  - `bf1a...07:30`, `+1.12241840R`.
- Interpretation: behavior improved versus V145 because the correctness repair removed both an unresolved-fill-floor loser and an unresolved-fill-floor winner, while restoring one valid prior winner. This is not positive-by-suppression proof because the removed rows carried unresolved fill-floor execution-authority failures and are now scoreable/missed only.

## Delta Versus V144

- Trade delta: `-1`.
- Net R delta: `-0.29090804`.
- Gross/final R delta: `-0.37189100` / `-0.37189100`.
- Cost R delta: `-0.08098295`.
- Cash PnL delta: `-29.09561561`.
- Removed V144 valid winner: `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, XAUUSD LONG, `moonshot_h17_18`, `+0.29090804R`.
- Interpretation: V146 closes the unresolved fill-floor leak, but B7 transfer recovery remains open because a valid prior winner no longer reaches fill.

## Truth Contract Result

- V145 order ledger unresolved fill-floor failures: 6 rows / 3 unique keys.
- V145 trade ledger unresolved fill-floor failures: 2 rows / 2 unique keys.
- V146 order ledger unresolved fill-floor failures: 0 rows.
- V146 trade ledger unresolved fill-floor failures: 0 rows.
- V146 scorecard/missed rows can still carry unresolved fill-floor reasons as diagnostic or missed-opportunity evidence; they no longer bind executable orders/trades.

## Companion Artifacts

- Flow summary: `BROAD_LIVE_AS_IF_REPLAY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED_FLOW_DIAGNOSTIC_SUMMARY.json`.
- Flow bucket ledger: `BROAD_LIVE_AS_IF_REPLAY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED_FLOW_BUCKET_LEDGER.jsonl`.
- Parity summary: `SOURCE_BOUND_TO_EXECUTED_PARITY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED_SUMMARY.json`.
- Leakage bucket ledger: `EXECUTION_LEAKAGE_BUCKET_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED_LEDGER.jsonl`.
- Repair plan: `EXECUTION_LEAKAGE_REPAIR_PLAN_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED.json`.
- Strict parse: `.context/context_os/V146_B7_UNRESOLVED_FILL_FLOOR_TARGETED_STRICT_PARSE.json`.
- Route verifier: `VERIFICATION_RESULT.json`, `ok=true`, `issue_count=0`, verified at 2026-07-07T07:19:06Z.

## Next B7 Blocker

The next highest-leverage class is transfer recovery after truthful unresolved-fill-floor demotion:

- Explain or recover the removed V144 valid winner `62cb...17:45` without re-opening unresolved fill-floor execution.
- Rank V146 leakage buckets by recoverable missed positive R and correctness impact.
- Patch the next same-root scheduler/reallocation/order/lifecycle/exit leak across producer, consumer, ledger, verifier, and tests before any new replay.
