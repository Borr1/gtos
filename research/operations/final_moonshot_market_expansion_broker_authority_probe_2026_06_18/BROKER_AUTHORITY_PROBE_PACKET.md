# Market Expansion Broker-Authority Probe Packet

Decision: `BROKER_AUTHORITY_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED`

This package improves the broker-authority picture without promoting market expansion.
It used only redacted/aggregate read-only bridge evidence and calculation functions.

What improved:

- `order_calc_profit` conversion now closes for `14/14` market-expansion symbols.
- Direct deal-history commission evidence exists for `7/14` symbols.
- Nonzero direct commission was observed for `2` symbols; direct zero-commission history was observed for `5` symbols.
- Point-mode swap-to-R conversion was computed for `22/28` side rows.

What is still not live authority:

- `MX-BROKER-AUTH-REQ-001`: explicit broker trading-session table or platform-source proof
- `MX-BROKER-AUTH-REQ-002`: broker-exact commission schedule or direct authority for every activation symbol
- `MX-BROKER-AUTH-REQ-003`: broker-exact slippage, limit-fill, and market-fill authority
- `MX-BROKER-AUTH-REQ-004`: exact swap-to-R holding-time and rollover model for all market-expansion symbols
- `MX-BROKER-AUTH-REQ-005`: owner-approved VPS promotion and monitoring execution

Runtime boundary:

- `live_authority=false`
- `deployment_ready=false`
- `promotion_ready=false`
- `runtime_effect=none_market_expansion_default_off_broker_authority_probe_only`

Do not apply the market-expansion patch from the promotion-boundary route until
these requirements are closed on the VPS/runtime namespace and the owner
explicitly approves activation.
