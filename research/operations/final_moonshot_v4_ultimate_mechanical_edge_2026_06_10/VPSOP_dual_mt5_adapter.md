# VPSOP — Dual-MT5 Live Adapter (FTMO-primary / redacted_account-follower)

Track: on-VPS operator bundle — replace the bridge-based live adapter with a DUAL-MT5
adapter per `DUAL_MT5_ARCHITECTURE.md`.

## What was built

- **`GOLIVE_vps_deploy/adapters/dual_mt5_adapter.py`** — the new dual-terminal live
  adapter. DEFAULT-OFF, fail-closed, import side-effect-free, NO broker / NO orders /
  NO network on import or by default.
- **`GOLIVE_vps_deploy/tests/test_dual_mt5_adapter.py`** — 27 broker-free tests (fakes
  in-memory transports; SiliconBridgeAdapter never connected). Full package suite:
  **45 passed** (18 existing kill-switch/monitor/bridge + 27 new).

Files (absolute):
- `/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_vps_deploy/adapters/dual_mt5_adapter.py`
- `/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_vps_deploy/tests/test_dual_mt5_adapter.py`

## How it supersedes the bridge adapter for live

`bridge_adapter.py` is a SINGLE-terminal seam pointed at the dev-only siliconmetatrader5
bridge (`SiliconBridgeAdapter`, host/port :8001). On the VPS there is **no bridge** —
two local MT5 terminals. The dual adapter:

1. **Reuses** the bridge adapter as the per-terminal transport (one `BridgeAdapter`
   handle per terminal via `make_bridge_adapter`). It does NOT duplicate connect/order
   logic — the already-tested gated, fail-closed transport seam is the leg primitive, so
   there is a single fail-closed gate path. The default terminal `transport` is set to
   `"local_mt5"` (host-local), not the dev bridge.
2. Wraps two of those handles into a **PRIMARY (FTMO)** and **FOLLOWER (redacted_account)**
   pair with role invariants enforced at config construction.
3. At go-live the owner promotes the reviewed dual adapter (alongside the reviewed
   single-terminal transport) into `src/mt5/`, supplies TWO terminal paths + TWO sets of
   ENV creds, and the runtime calls `make_dual_mt5_adapter(...)` instead of the single
   `make_bridge_adapter(...)`. The bridge adapter remains the per-leg transport; the dual
   adapter is the new top-level live surface.

Required ENV additions (separate creds per terminal — owner adds to the VPS `.env`):
`GTOS_FTMO_MT5_LOGIN/PASSWORD/SERVER`, `GTOS_redacted_account_MT5_LOGIN/PASSWORD/SERVER`.
(The existing single-key `GTOS_MT5_*` in `env.template` is the legacy bridge path; the
dual adapter uses the per-broker names so the two terminals never share credentials.)

## Architecture mapped to code (DUAL_MT5_ARCHITECTURE.md)

- **FTMO PRIMARY** — `get_primary_tick()` reads OHLC/tick from the FTMO terminal (the
  native validated distribution); `execute_decision()` sends the FTMO order. The decision
  engine (deploy book) is fed from the primary leg. `FTMO_SYMBOL_MAP` uses the book's
  canonical names + the MEASURED per-symbol tick floors from
  `ultimate_book_live_package.TICK_SPREAD_FLOOR_R` (those floors were measured on the
  FTMO-fed bridge).
- **redacted_account FOLLOWER** — `_mirror_to_follower()` replicates each FILLED primary
  decision, spec-translated; it never re-decides. `redacted_account_SYMBOL_MAP` carries the
  different native naming (suffix hazards: `USOIL.cash`→`USOIL.c`, `UKOIL.cash`→`UKOIL.c`)
  and leaves `spread_floor_r=None` where it has NOT been re-measured on redacted_account (the
  architecture requires per-broker re-measurement; an unverified floor near the wall is
  skipped until measured).
- **Per-broker symbol/spec/spread-floor map** — `SymbolSpec` (canonical, broker_symbol,
  contract_size, digits, spread_floor_r, tradeable) + `BrokerSymbolMap`. `translate_to_follower()`
  resolves canonical→follower-native and returns a skip reason for missing/untradeable/
  unverified-floor symbols. `symbol_coverage()` reports mirrorable vs skipped across the
  primary universe (GBPJPY is intentionally absent from redacted_account to exercise the
  missing-symbol path).
- **UTC clock normalization + startup offset check (TOP watch item)** —
  `evaluate_clock_offset()` + `check_clocks()`. Each terminal's tick time is normalized to
  UTC and compared to a single canonical reference; `|offset| > tolerance` (default 2s) or
  no-time **fails closed**. The PRIMARY clock gates the whole system; a FOLLOWER clock skew
  only skips follower legs (isolation preserved). `startup_self_check()` runs the clock +
  role + coverage gate WITHOUT connecting or trading.
- **Independent per-account governor + DD** — each terminal carries its own `BridgeConfig`
  (own creds, own profile namespace `ftmo_primary` / `redacted_account_follower`), own equity read
  (`get_primary_equity` / `get_follower_equity`). The existing `monitor.py` DD watch and
  `evaluate_governor` are namespaced per account, so each account sizes/tracks DD/halts
  independently — one breaching never forces the other.
- **Follower divergence → skip the leg, never the primary** — every follower failure mode
  (`FOLLOWER_SKIP_REASONS`: missing-symbol, untradeable, large-slip, reject, not-connected,
  spec-mismatch, clock-unsafe, governor-blocked) skips the follower leg and records it; the
  primary order is sent regardless. A follower transport EXCEPTION is caught and contained.
  `max_follower_slippage_r` (default 0.10R, measured against the primary fill via the
  request stop distance) triggers the large-slip skip.
- **Primary-vs-follower parity ledger interface** — `ParityLegRecord` (per decision: did
  redacted_account fill the translated order, at what slip, on the matching symbol?) +
  `ParityLedgerSink` (a callable the owner wires to `monitor.record_parity` at go-live for
  the FTMO-vs-redacted_account ledger). `parity_summary()` gives divergence counts / reasons /
  mean+max slippage. The sink is failure-isolated (a broken sink never breaks execution).

## Safety / guardrail compliance

- DEFAULT-OFF: `make_dual_mt5_adapter()` with the default config builds two
  `NullBridgeAdapter`s — `connect()` returns `live=False`, `execute_decision()` places
  nothing (NullBridgeAdapter `order_send` is fail-closed). A real leg is only built per
  terminal when that terminal's `BridgeConfig.live_connect_allowed=True` AND the owner
  supplies `gate_ok`+`halt_clear`; even then `connect()` re-checks all gates.
- Creds are ENV-only (per-terminal var names); none stored in the file. Halt files remain
  the physical control (the gate/halt callbacks are the same triple-gate + halt path used
  by the bridge adapter). No production `src/` or `config/agent_config.yaml` changes — all
  in the route dir + `GOLIVE_vps_deploy/`.
- Verified: import does not pull `nmetatrader5`/`MetaTrader5`; default config connects to
  nothing and orders nothing; FTMO-primary/redacted_account-follower roles confirmed; clock check
  fails closed without a terminal time.

## Owner TODO before live flip (encoded as skip/fail-closed today)

1. Re-measure the redacted_account per-symbol tick spread floors and fill `spread_floor_r` in
   `redacted_account_SYMBOL_MAP` (today None → conservative skip via canonical fallback).
2. Verify each redacted_account symbol's `contract_size`/`digits` against the live terminal
   (`symbol_info`); the placeholders today should be confirmed, and a verified spec
   mismatch vs the primary should fail the leg closed.
3. Add the per-terminal ENV creds + two terminal paths; set `live_connect_allowed=True`
   per terminal only on owner go; confirm both terminals' UTC offsets via
   `startup_self_check()` (system gate is green only when the primary clock is safe).
4. Wire `parity_sink` to `monitor.record_parity` and the redacted_account follower to its own
   namespaced governor/DD watch.

## Tests

`python3 -m pytest GOLIVE_vps_deploy/tests -q` → **45 passed** (0.10s). New coverage:
default-off/no-broker/import-side-effect-free, role invariants, suffix translation +
missing-symbol skip, unverified-floor skip, UTC clock offset (safe/unsafe/no-time
fail-closed, primary-gates-system/follower-isolated), follower isolation across all
failure modes (missing/reject/exception/large-slip/not-connected, primary-not-filled),
parity ledger + divergence summary + sink-failure isolation, startup self-check
(default-off clean vs primary-clock-skew blocked).
