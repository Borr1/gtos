# V3 Reentry Risk Accounting

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Status

V3 is design-only. It is blocked until V2b produces resolved post-cutoff OB-boundary/J46 pairs or rejects the OB-boundary level-quality hypothesis.

Current V2b forward artifact:

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.md`
- status: `BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS`
- post-cutoff event rows: `264`
- wanted OB-boundary/J46 rows: `110`
- resolved wanted rows: `0`

## Hard Invariant

For one setup, the aggregate worst-case loss after every initial fill, reentry fill, pending order, stop, and cost assumption must remain `>= -1.0R`.

Accounting equation:

```text
aggregate_worst_case_r =
  realized_closed_leg_r
  + sum(open_leg_stop_if_hit_r)
  - estimated_remaining_cost_r
```

A new leg is allowed only if the equation remains `>= -1.0R` after that new leg is stopped out.

## Required Ledger

Every V3 row needs these fields before replay can be trusted:

| Field | Reason |
| --- | --- |
| `setup_id` | Groups initial and reentry legs under one risk budget. |
| `leg_id` | Separates initial and reentry cost/outcome accounting. |
| `state_before` / `state_after` | Makes the path state machine auditable. |
| `fill_status` | Prevents unfilled pending intents from becoming realized trades. |
| `fill_time_utc` / `fill_price` | Required for no-leak lower-timeframe path walking. |
| `stop_if_hit_r` | Required for aggregate worst-case check. |
| `realized_leg_r` | Required after each close. |
| `estimated_cost_r` | Costs must accumulate per fill/exit, not once per setup. |
| `risk_bank_before` / `risk_bank_after` | Shows why a reentry was allowed or blocked. |
| `ambiguity_flags` | Same-bar, missing fill, missing cost, or stale telemetry cannot be hidden. |

## Non-Negotiable Blocks

- No V3 outcome mining before V2b answers the level-quality question.
- No generic trailing stop.
- No reentry if pending-limit lifecycle telemetry is missing.
- No use of Databento/orderflow as a label unless actual broker R, synthetic path R, and fill/no-fill labels are separated.
- No promotion claim from V3 replay without a future pre-registered validation lane, DSR correction, PBO, effective-N, and `NO_PROMOTION_VERDICT` removal by a separate approval dossier.

## Next Work

1. Keep collecting/replaying V2b until resolved post-cutoff pairs exist.
2. Add pending-limit lifecycle telemetry before any V3 fill/reentry replay.
3. Build unit tests for the risk-bank invariant before implementing a replay engine.
4. Register the V3 reentry trigger family only after V2b resolves whether OB-boundary is valid enough to act as the level source.
