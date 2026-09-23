# LTO-036 Canary Restart Governance - 2026-05-05

**Schema:** `lto036_canary_restart_governance_v1`
**Generated:** `2026-06-01T09:34:59.474956+00:00`
**Status:** `OK_CANARY_RESTART_GOVERNANCE_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Status

- Governance status: `CANARY_CACHE_HISTORICAL_OPTIONAL_NOT_LIVE_BLOCKER`
- Marker status: `MARKER_ABSENT`
- Valid until UTC: `None`
- Owner reason: `None`
- Latest canary cache completed at UTC: `None`
- Cache age hours: `None`
- Cache stale after skip expiry: `False`
- Action-required codes: `[]`

## Counts

- Status rows available: `7`
- Status rows appended this run: `1`
- Action required: `0`

## Restart Policy

```json
{
  "canary_calls": "NONE_REQUIRED_FOR_HISTORICAL_OPTIONAL_CACHE",
  "pre_restart_checks": [
    "NO_OPEN_POSITIONS",
    "NO_PENDING_BROKER_ORDERS",
    "CANARY_CACHE_HISTORICAL_OPTIONAL_NO_RESTART_BLOCK"
  ],
  "restart_scope": "TARGETED_COMPONENT_ONLY_UNLESS_FLEET_WIDE_FAILURE"
}
```

## Boundary

This row documents that the old AI/API canary cache is a historical optional artifact. It is not a live blocker, does not require canary regeneration, and does not approve trading behavior.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
