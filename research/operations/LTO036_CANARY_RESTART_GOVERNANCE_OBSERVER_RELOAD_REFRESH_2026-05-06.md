# LTO-036 Canary Restart Governance - 2026-05-05

**Schema:** `lto036_canary_restart_governance_v1`
**Generated:** `2026-05-05T21:16:34.812921+00:00`
**Status:** `OK_CANARY_RESTART_GOVERNANCE_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Status

- Governance status: `OWNER_SKIP_ACTIVE_COST_OVERRIDE_VISIBLE`
- Marker status: `OWNER_SKIP_ACTIVE`
- Valid until UTC: `2026-12-31T23:59:59+00:00`
- Owner reason: `Owner instructed boot-time live canary removal/minimization on 2026-05-05 after excessive API spend; explicit operational cost override, not a canary PASS cache.`
- Latest canary cache completed at UTC: `2026-05-05T08:06:26.545438+00:00`
- Cache age hours: `13.169`
- Cache stale after skip expiry: `True`
- Action-required codes: `[]`

## Counts

- Status rows available: `5`
- Status rows appended this run: `1`
- Action required: `0`

## Restart Policy

```json
{
  "canary_calls": "MANUAL_OR_OWNER_APPROVED_ONLY_WHEN_EXPENSIVE",
  "pre_restart_checks": [
    "NO_OPEN_POSITIONS",
    "NO_PENDING_BROKER_ORDERS",
    "OWNER_SKIP_OR_FRESH_CANARY_STATUS_VISIBLE"
  ],
  "restart_scope": "TARGETED_COMPONENT_ONLY_UNLESS_FLEET_WIDE_FAILURE"
}
```

## Boundary

This row documents canary-skip and restart governance only. It is not a canary PASS cache and does not approve trading behavior.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
