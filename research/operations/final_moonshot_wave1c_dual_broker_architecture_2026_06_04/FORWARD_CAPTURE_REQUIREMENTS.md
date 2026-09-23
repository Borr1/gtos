# Wave1C Forward Capture Requirements

- Persist target-side broker cash risk at FTMO entry for every copied position.
- Preserve target action log, checkpoint, and target trade state under the target
  runtime namespace for every ticket.
- Capture broker-local spread, commission, swap, slippage, contract size,
  session/closure state, and symbol mapping snapshots before target order send.
- Join broker-real PnL/cash only from explicit account-history exports; do not
  infer broker-real R from projected or target-state rows.
- Record source intent id, source record path, target ticket, target namespace,
  source namespace, and architecture contract status on every target lifecycle
  action.
- Keep maintenance run state even when an explicit suppression flag skips the
  chain, so suppressed capture gaps are visible.
