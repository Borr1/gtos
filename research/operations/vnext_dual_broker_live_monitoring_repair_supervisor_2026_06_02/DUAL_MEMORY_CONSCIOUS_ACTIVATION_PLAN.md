# Dual-Broker Memory-Conscious Activation Plan

Recorded: 2026-06-02
Updated: 2026-06-02T08:52:38.9003718Z

## Current Evidence Boundary

- VPS restart invalidated all pre-restart process assumptions.
- Post-reboot checkpoints regenerated `LIVE_STATE` and route runtime evidence before any assistant launch.
- Current observed process footprint is:
  - 24 redacted_account `run_agent.py` workers;
  - 24 redacted_account tick-capture workers;
  - 1 redacted_account M1 capture worker;
  - 1 account-scoped redacted_account notification queue worker;
  - 1 redacted_account MT5 terminal;
  - 1 dual-broker trade-record projector;
  - 1 order-capable FTMO execution follower;
  - 1 FTMO portable MT5 terminal;
  - 0 FTMO `run_agent.py` workers.
- Latest route process checkpoint recorded 46.26% free physical memory and classified memory as healthy.
- Current read-only MT5 probe passed for both accounts. redacted_account has 10 open positions and 0 orders. FTMO has 0 positions and 0 orders.
- No manual broker order, position, or deal mutation has been performed or authorized.

## Correct Architecture

The live market-intelligence stack should run once, on the primary redacted_account surface. The second account should not run a duplicate 24-symbol market brain.

The correct dual-account shape is:

1. redacted_account remains the canonical strategy/data producer.
2. redacted_account emits a broker-neutral canonical intent only after a real live execution path exists:
   - market entry intent after primary `open_trade` succeeds;
   - internal limit intent after primary `set_limit_intent` succeeds.
3. A lightweight projector reads redacted_account trade records and writes canonical intent rows.
4. FTMO runs one lightweight execution follower process.
5. The follower consumes canonical intents, maps symbols through the FTMO profile, verifies the FTMO account/terminal contract, reads the FTMO current tick/candles for the target symbol, recomputes FTMO lot sizing/risk from FTMO broker geometry, and executes or manages only when the target account is locally valid.
6. FTMO does not start 24 orchestrators, 24 tick capture daemons, an all-symbol M1 capture daemon, or a duplicate notification worker.
7. Duplicate follower notifications are suppressed. Audit goes to the follower action JSONL ledger.

## Resource Design

- redacted_account keeps the full V3/vNext/moonshot runtime and is not constrained to make dual-account operation fit.
- FTMO is a downstream execution surface, not a second research/orchestration brain.
- FTMO symbol tick subscription is lazy. The follower checks/selects only the target symbol when a real intent needs target-account price validation.
- Missing FTMO ticks on unselected non-target symbols are not a defect by themselves. They become actionable only when a fresh intent needs that target symbol and the follower cannot get a valid quote inside the configured wait window.
- If free memory drops below the watchdog guard or pressure recurs, stop widening ledgers and repair the process footprint before any additional launch.

## Rejected Paths

- Full FTMO fleet duplication is rejected. It doubles memory and MT5 load while producing nearly the same decisions, and it competes with the primary live system for resources.
- Blind broker order copying is rejected. It risks copying the primary account's lot, fill, symbol, contract, spread, tick value, margin, and challenge assumptions into a broker with different geometry.
- Limiting the primary engine to fit two accounts is rejected. The primary system must continue running the vNext/moonshot stack as designed; dual-account behavior belongs in a downstream account-specific execution surface.
- Mass-selecting all FTMO symbols just to make a readiness probe look green is rejected. The probe must distinguish instrument existence from target-symbol tick readiness.

## Active Runtime Target

Primary role:

- profile: `redacted_account`
- namespace: `redacted_account_live_bee34003`
- role: `primary_full`
- components: 24 orchestrators, 24 tick capture daemons, one M1 capture daemon, one notification queue worker, current maintenance monitors, and the dual-broker projector bridge.

Secondary role:

- profile: `operator_profile`
- namespace: `operator_profile`
- role: `secondary_execution_follower`
- components: one `scripts/dual_broker_execution_follower.py` process and the FTMO portable terminal only.
- no duplicate tick fleet, M1 capture fleet, full orchestrator fleet, or notification queue worker.

## Active Guards

- Notification queue is account-scoped for redacted_account and suppressed for the FTMO follower.
- `run_live_monitoring_maintenance.py` skips widening maintenance while dual-broker activation guard heartbeat paths exist.
- `scripts/watchdog.ps1` primary mode supervises only the lightweight dual-broker bridge for FTMO: projector plus follower.
- Follower target-tick guard defers fresh market intents when FTMO lacks a valid target quote, then expires stale rows so later rows are not blocked forever.
- `src/mt5/mt5_real.py` ignores invalid zero/inverted ticks for broker-time offset detection and lazily selects only the requested symbol after an invalid tick read.

## Next Proof

The next unresolved live proof is the first post-activation redacted_account execution intent and the corresponding FTMO follower result. After that event, reconcile both accounts read-only from canonical intent, follower action ledger, MT5 order/position/deal state, and any BE/SL/TP modification records.
