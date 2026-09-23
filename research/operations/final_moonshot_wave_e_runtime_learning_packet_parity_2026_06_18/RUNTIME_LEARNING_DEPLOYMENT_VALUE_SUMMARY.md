# Wave E Runtime-Learning Packet Parity Checkpoint

This checkpoint turns the ultimate-book runtime from status-only launcher rows into a canonical, append-only learning packet ledger.

Value for VPS:

- every cycle can emit `cycle_no_decision`, `cycle_no_candidates`, `unit_shadow`, `unit_admitted`, `unit_skipped`, and `unit_placed` packets;
- every management pass can emit `position_adopted`, `position_managed`, `position_closed`, `position_out_of_universe`, `position_management_error`, and `breach_flatten` packets;
- bridge policy context, active candidate/market-expansion policy, risk/sizing flags, skip reasons, decision bars, and placement status are joined in one schema;
- raw broker tickets, account logins, server names, passwords, tokens, and API keys are never written raw;
- packet writing is best-effort and non-fatal, so telemetry cannot stop trading or management;
- active config enables the observation-only packet ledger at `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.

Evidence class: production-code observation layer and VPS parity handoff. This is not broker-real PnL and does not mutate broker/account/order/deal/position state.
