# GTOS go-live — VPS deployment package (PREP, default-off)

This Mac is dev/research. Live runs on a VPS connected to FTMO. Everything here is
**scaffolding and staged patches** — nothing connects a broker or places an order.
The system is hard-halted; the halt flags are the physical control. New behaviour is
default-off behind the repo triple-gate (`enabled AND apply_to_execution AND
live_activation_allowed`) plus the local halt flags plus the bridge `live_connect_allowed`.

## Layout

```
GOLIVE_vps_deploy/
  adapters/bridge_adapter.py     MT5/bridge adapter (interface + nmetatrader5 seam, fail-closed)
  monitoring/kill_switch.py      kill-switch: halt file + size_cap=0 (CLI: engage/disengage/state)
  monitoring/monitor.py          parity ledger + daily-DD watch + governor check + alert hook
  operator/operator_toolkit.py   ACTIVE-operator toolkit: health/freshness, dual parity, null-guard,
                                 chronology, LFS/param check, live-trade miner wiring, escalation
  deploy/run_monitor_cycle.py    systemd/docker entrypoint for the monitor cycle (no broker)
  deploy/push.sh                 deploy/push to VPS + self-verify ONLY (no live start, no creds)
  systemd/gtos-live@.service     per-account trader unit (default-off, halt-guarded ExecStartPre)
  systemd/gtos-monitor.{service,timer}   monitor sidecar on a 60s timer
  docker/{Dockerfile,docker-compose.yml} container alternative (live svc is opt-in `--profile live`)
  config/env.template            secrets/env TEMPLATE (creds via ENV only, never committed)
  config/requirements-vps.txt    pinned VPS runtime deps (excludes research ML deps)
  patches/0001-disable-broad-selector-v4.patch   STAGED Phase A selector disable (apply by hand)
  tests/test_golive_vps_package.py   18 tests (kill-switch, monitor, adapter fail-closed)
```

## What is READY now (scaffolding/scripts, tested)

- Process manager: systemd units (`gtos-live@.service` per account + monitor timer) AND a
  docker-compose alternative. The live trader is NOT enabled/auto-started; `ExecStartPre`
  refuses to start while the kill-switch/halt flag is engaged.
- Bridge adapter: `BridgeAdapter` ABC mirrors `src/mt5/mt5_interface.MT5Interface`; default
  factory returns the fail-closed `NullBridgeAdapter`; the `SiliconBridgeAdapter`
  (nmetatrader5 localhost:8001 seam) refuses to `connect()` unless the triple-gate +
  halt-clear + `live_connect_allowed` + ENV creds all pass. Import is side-effect free.
- Monitoring + alerting: live-vs-replay parity ledger (warn 0.15R / de-risk 0.30R bands),
  daily-DD watch against the deploy module's `GovernorLimits` (soft -3% / hard -5% / max-DD
  de-risk 7-10%), governor circuit-breaker re-check sharing the execution governor, and a
  pluggable owner alert hook (JSONL + stderr default; webhook via `GTOS_ALERT_WEBHOOK`).
- Kill-switch: writes the physical hard-halt flag AND a `size_cap_override=0` sidecar; either
  alone flattens new entries. Disengage requires an explicit owner token and never auto-removes
  the halt flag. Verified against the REAL repo: with the current halt flags present it reports
  `kill_switch_engaged: true, new_entries_allowed: false`.
- Deploy/push script: syncs a committed branch to the VPS and runs the test matrix +
  kill-switch state check ONLY. Never writes creds, never starts the trader, never removes halt.
- Env/secrets template + pinned requirements.
- First-cycle sizing profile `clean3_firstcycle_eff1p18` added to the deploy module (1.25%
  nominal half-Kelly owner dial) with tests.

## What NEEDS owner / broker / VPS input (the real gate)

1. **VPS host + user + repo dir** — fill `<PLACEHOLDER>`s in `push.sh` env, the systemd units,
   and docker-compose.
2. **Broker creds** — FTMO login/password/server in the VPS `.env` (ENV only). Two accounts ->
   `.env.ftmo_acct_a`, `.env.ftmo_acct_b`.
3. **Bridge endpoint** — `GTOS_BRIDGE_HOST` / `GTOS_BRIDGE_PORT` (default 8001) and confirm
   `nmetatrader5` connects READ-ONLY first; install `MetaTrader5` on the Windows MT5 host.
4. **NTP time-sync** on the VPS (broker time-sensitive; systemd unit waits on `time-sync.target`).
5. **Phase A config flip** — apply `patches/0001-disable-broad-selector-v4.patch` by hand
   (`git apply ...`) after review; flip the `ultimate_book_*` triple-gate ON when ready.
6. **Phase C broker/runtime authority** — the actual live gate (hard-halt forensic join,
   V3-vs-live gap audit, dual-broker audit, production-return dossier). NOT done here.
7. **Real alert sink** — wire email/Telegram/Slack/push via `GTOS_ALERT_WEBHOOK` or a custom sink.

## Go-live order (deliberate, owner-driven)

1. `push.sh` -> VPS gets the committed branch; tests pass; kill-switch reports engaged.
2. Owner creates `.env*`, provisions MT5 + bridge, confirms read-only bridge connect.
3. Owner applies Phase A patch + flips the `ultimate_book_*` gate ON (still halt-blocked).
4. Phase C authority cleared -> owner `kill_switch.py disengage --approval-token <t>` AND
   removes the halt flag.
5. Start ONE account small (`clean3_firstcycle_eff1p18`, half-Kelly): `systemctl start
   gtos-live@ftmo_acct_a`. Monitor parity for a few days.
6. Parity-confirmed -> step to `clean3_growth_eff1p42` (1.5%), add the second account; ceiling
   `clean3_aggressive_eff1p66` capped at 2.0%/account.

## Reverting

- Selector disable: `git apply -R patches/0001-disable-broad-selector-v4.patch`.
- Kill-switch: leave engaged (safe). To clear: disengage with token, then manually remove the
  halt flag.
- All scaffolding lives in this route dir; deleting it changes no production behaviour.

## Tests

```
ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE python3 -m pytest $ROUTE/test_ultimate_book_live_package.py -q   # core book
PYTHONPATH=$ROOT:$ROUTE python3 -m pytest $ROUTE/GOLIVE_vps_deploy/tests -q              # package + operator
```

The operator toolkit (`operator/operator_toolkit.py`) is the resident VPS Claude's active-operation
surface per `VPS_OPERATOR_CHARTER.md`; per-failure-mode repair procedures are in
`../../OPERATOR_REPAIR_PLAYBOOK.md`. It is broker-free, default-off, fail-closed, and de-risk-only
(never engages the kill-switch unless the owner opts in; never raises risk beyond the dial).
