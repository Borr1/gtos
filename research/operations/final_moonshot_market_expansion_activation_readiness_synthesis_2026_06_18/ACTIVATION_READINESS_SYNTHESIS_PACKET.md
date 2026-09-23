# Market Expansion Activation Readiness Synthesis

Decision: `MARKET_EXPANSION_ACTIVATION_READINESS_SYNTHESIS_READY_DEFAULT_OFF_NOT_PROMOTED`

Runtime effect: `none_default_off_activation_readiness_synthesis_only`

## Current Numbers

- Active A8 baseline Sharpe `0.147757`, monthly `2.646%`, MC pass `0.99055`.
- Armed candidate book Sharpe `0.277408`, monthly `4.969%`, MC pass `0.9999`.
- Candidate plus market-expansion seed 0.025 under cost3 Sharpe `0.279324`, monthly `5.003%`, MC pass `0.99975`, max-DD fail `0.00025`, worst day `-2.156%`.

## Authority Matrix Summary

- Default-off code package ready rows: `14/14`.
- Live-authority ready rows: `0/14`.
- Explicit session-table rows closed: `0/14`.
- Observed M1 session proxy rows: `14/14`.
- Direct fill-slippage rows: `7/14`.
- Direct-or-family commission evidence rows: `14/14`.
- Direct commission authority rows: `7/14`.
- Point-mode swap conversion rows: `11/14`.
- Mode-5 swap formula-required rows: `3/14`.

## Boundary

This route says the market-expansion package is materially built as a default-off code/research package, but not live authority. No config patch was applied, no broker/order/account/deal/position mutation occurred, no orderflow/depth data was used, no remote push occurred, and no VPS reload occurred.

## Remaining Requirements

- `MX-READINESS-REQ-001`: explicit broker trading-session table or platform-source proof - not_closed.
- `MX-READINESS-REQ-002`: broker-exact prospective limit-fill and market-fill authority - not_closed.
- `MX-READINESS-REQ-003`: broker-exact commission schedule or accepted family-transfer production rule - partial_proxy_repair_not_closed.
- `MX-READINESS-REQ-004`: exact swap-to-R holding-time, rollover, and mode-5 formula model - partial_proxy_repair_not_closed.
- `MX-READINESS-REQ-005`: VPS packet parity, monitoring, rollback, and owner-approved promotion execution - not_executed_by_mac_route.
