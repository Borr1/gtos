# AI Companion Cycle Digest

Window: `2026-06-19T08:07:34.906339Z` to `2026-06-19T09:07:35.590166Z`
Runtime effect boundary: `read_only_log_pipeline_state_parse_no_broker_mutation_no_order_action_no_runtime_reload`
OK: `True`

## Cycle Causes

- `cost_screen`: `1` cycles.
- `cost_screen_with_profile_hygiene`: `1` cycles.
- `duplicate_protection`: `1` cycles.
- `duplicate_protection_with_profile_hygiene`: `1` cycles.
- `no_candidates`: `4` cycles.

## Companion Queues

- Cost-screen review events: `2`.
  - `redacted_account_live_bee34003` `GBPUSD` `asian_fade` `2026-06-19T08:15:00+00:00`: `cost_screen_spread_r:0.105>0.100 (spread 0.0001 vs asian_fade stop 0.0007)`.
  - `operator_profile` `GBPUSD` `asian_fade` `2026-06-19T08:15:00+00:00`: `cost_screen_spread_r:0.105>0.100 (spread 0.0001 vs asian_fade stop 0.0007)`.
- Duplicate-protection events: `2`.
  - `redacted_account_live_bee34003` `US30_cash` `idxrev` `2026-06-19T05:00:00+00:00`: `already_placed_today`.
  - `operator_profile` `US30_cash` `idxrev` `2026-06-19T05:00:00+00:00`: `already_placed_today`.
- Broker-profile hygiene symbols: `{'DASHUSD': 4, 'XAGAUD': 1, 'XAGEUR': 1, 'XAUAUD': 1, 'XAUEUR': 1, 'XPDUSD': 4, 'XTZUSD': 4}`.
- Active/nonclosed lifecycle normalizations: `3`.
  - `operator_profile` `JP225` `idxrev` raw=`None` companion=`active_nonclosed`.
  - `operator_profile` `US30_cash` `idxrev` raw=`None` companion=`active_nonclosed`.
  - `redacted_account_live_bee34003` `US30_cash` `idxrev` raw=`None` companion=`active_nonclosed`.

## Boundary

- This digest is read-only and does not override gates, place orders, reload workers, or mutate broker state.
