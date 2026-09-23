# Wave1C Dual-Broker Runtime Path Map

Generated: 2026-06-04T14:44:14.292094+00:00

Final runtime model: `redacted_account_primary_full_ftmo_follower_projector`.

redacted_account is the only full-runtime source authority. It owns the 24-symbol
primary brain, account-local order authority for redacted_account only, source trade
records, and canonical intent emission.

FTMO is follower/projector only. It consumes canonical intents, maps symbols to
FTMO broker symbols, applies FTMO broker-local risk/exposure gates, executes only
through the FTMO profile when order-enabled, and then manages target-local
lifecycle state through `dual_broker_target_trade_state.json`.

Rows preserved:

- source inventory rows: 1248
- broker/profile rows: 75
- cost/spec/session rows: 72
- authority rows: 7
- lifecycle rows: 7
- risk rows: 5
- target namespace rows: 27
- crash/halt rows: 6

No broker/account/order/deal/position mutation, credential mutation, paid API
call, remote publish, or live VPS restart was performed by this builder.
