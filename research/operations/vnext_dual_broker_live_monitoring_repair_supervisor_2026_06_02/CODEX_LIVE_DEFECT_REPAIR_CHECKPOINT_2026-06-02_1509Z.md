# Codex Live Defect Repair Checkpoint - 2026-06-02 15:09 UTC

Status: post-reload verified. No manual broker order, deal, or position mutation was performed.

## Fixed

- FTMO follower exact pretrade refusal observability.
- Dual trade-record projector seen/outcome state and hash signatures.
- redacted_account open-position stop-loss cash risk exposure in prop-safe selector state.
- Recovered partial BE geometry denominator and invalid recovered TP repair guard.
- Orchestrator terminal exit/shadow/notification immutable R denominator guard.
- XAGUSD corrupted local R/PnL/shadow evidence repaired from read-only redacted_account MT5 history.

## XAGUSD Repair

- Position: 242557352.
- Deals: entry 226347672, TP1 226391720, final 226402820.
- Immutable geometry: entry 76.02000000000001, SL 76.593, 1R distance 0.573.
- Result: TP1 +1.1815R on 50%, final +0.2845R on 50%, weighted +0.7330R.
- Broker net: +167.51 USD.
- Daily PnL after repair: -10.6999R, +125.86 USD.

## Verification

- py_compile passed for orchestrator, execution, follower, projector.
- Focused pytest: 29 passed.
- Post-reload shape: 24 redacted_account workers, 0 FTMO workers, 1 FTMO follower, 1 projector, 24 tick captures, 1 M1 capture, 1 notification worker, 2 MT5 terminals.
- MT5 read-only probe after reload: redacted_account orders 0 / positions 13; FTMO orders 0 / positions 9.
- Bad impossible-R signature scan: clean outside the intentional before-repair checkpoint.

## Remaining

Broker-local management architecture remains to design/implement as a separate scoped change: shared redacted_account intent brain with broker-local execution/management for each account, instead of a passive FTMO copy-only lifecycle.
