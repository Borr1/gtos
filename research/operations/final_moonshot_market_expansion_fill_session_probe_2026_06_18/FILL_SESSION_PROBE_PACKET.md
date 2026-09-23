# Market Expansion Fill/Session Probe Packet

Decision: `FILL_SESSION_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED`

This package improves fill/session evidence without promoting market expansion.
It used read-only history order/deal aggregates and observed M1 quote-session
availability. Raw ticket/order/deal identifiers are not stored.

What improved:

- Direct historical order/deal fill-slippage evidence exists for `7/14` symbols.
- Joined entry-deal rows: `57`.
- Max observed absolute slippage across direct symbols: `0.0690393422R`.
- Observed M1 quote-session proxy exists for `14/14` symbols.

What remains open:

- `MX-FILL-SESSION-REQ-001`: explicit broker trading-session table or platform-source proof
- `MX-FILL-SESSION-REQ-002`: broker-exact prospective limit-fill and market-fill authority
- `MX-FILL-SESSION-REQ-003`: direct fill/slippage evidence for every activation symbol
- `MX-FILL-SESSION-REQ-004`: broker-exact commission and swap authority from prior broker-authority route
- `MX-FILL-SESSION-REQ-005`: owner-approved VPS promotion and monitoring execution

Runtime boundary:

- `live_authority=false`
- `deployment_ready=false`
- `promotion_ready=false`
- `runtime_effect=none_market_expansion_default_off_fill_session_probe_only`
