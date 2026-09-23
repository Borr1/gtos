# GOLIVE_vps — VPS deployment package + monitoring + kill-switch (findings)

Track: VPS deployment package + monitoring + kill-switch. Posture: PREPARE-DON'T-FLIP,
default-off, fail-closed, fully tested. Nothing here connects a broker or places an order.
The system stays hard-halted; the halt flags remain the physical control.

Date: 2026-06-15. Author: deployment-engineer track. Dev surface: this Mac. Live surface: VPS.

## 1. What I built (all under `GOLIVE_vps_deploy/`, NEW default-off files)

| area | file | summary |
|---|---|---|
| process manager (systemd) | `systemd/gtos-live@.service` | per-account trader unit; NOT enabled; `ExecStartPre` runs the kill-switch state check and refuses to start while halted; waits on `time-sync.target`; crash-loop guard |
| process manager (systemd) | `systemd/gtos-monitor.{service,timer}` | monitor sidecar on a 60s timer; read/append-only, broker-free |
| process manager (docker) | `docker/docker-compose.yml` + `docker/Dockerfile` | container alternative; live trader services are opt-in (`--profile live`), monitor is the default CMD; documents the Windows-MT5/bridge transport constraint |
| MT5/bridge ADAPTER | `adapters/bridge_adapter.py` | `BridgeAdapter` ABC mirroring `src/mt5/mt5_interface.MT5Interface`; `NullBridgeAdapter` (default, fail-closed); `SiliconBridgeAdapter` (nmetatrader5 localhost:8001 seam) gated behind triple-gate + halt-clear + `live_connect_allowed` + ENV creds; `nmetatrader5` import deferred to `connect()`; import is side-effect-free |
| env/secrets | `config/env.template` | creds via ENV only (never committed); bridge host/port; profile/namespace; sizing dial; `GTOS_LIVE_CONNECT_ALLOWED=false` default |
| deps | `config/requirements-vps.txt` | pinned VPS runtime subset; excludes research ML deps (shap/lightgbm/sklearn/lancedb/plotly/databento) |
| monitoring | `monitoring/monitor.py` | (1) live-vs-replay parity ledger w/ warn 0.15R / de-risk 0.30R bands; (2) daily-DD watch vs the deploy module `GovernorLimits` (soft -3% / hard -5% / max-DD de-risk 7-10%); (3) governor circuit-breaker re-check sharing the execution governor; (4) pluggable owner alert hook (JSONL+stderr default, `GTOS_ALERT_WEBHOOK` hook); `run_monitor_cycle()` ties them together w/ alert routing |
| kill-switch | `monitoring/kill_switch.py` | writes the physical hard-halt flag AND a `size_cap_override=0` sidecar (two redundant stops, either flattens new entries); `disengage` requires an owner token and never auto-removes the halt flag; corrupt sidecar reads as fully engaged (fail-closed); CLI `engage|disengage|state` |
| deploy/push | `deploy/push.sh` | syncs a committed branch to the VPS + runs the test matrix + kill-switch state check ONLY; never writes creds, never starts the trader, never removes the halt flag; fails closed on missing owner values |
| entrypoint | `deploy/run_monitor_cycle.py` | systemd/docker entrypoint; loads the deploy module `DEFAULT_LIMITS` as the single governor truth; reports halted/no-snapshot safely |
| Phase A patch (STAGED) | `patches/0001-disable-broad-selector-v4.patch` | flips `selector_v4_{enabled,apply_to_execution,live_activation_allowed}` -> false. Reviewed unified diff, NOT auto-applied. `git apply --check` passes. |
| Phase A patch (STAGED) | `patches/0002-disable-broad-scheduler-v4.patch` | flips the broad `scheduler_v4_best_trade_allocator` triple-gate -> false (the "scheduler equivalent" in GO_LIVE_SEQUENCE Phase A.1). NOT auto-applied; `git apply --check` passes. |
| tests | `tests/test_golive_vps_package.py` | 18 tests: kill-switch (engage/disengage/token/fail-closed/audit), monitor (parity verdicts/DD states/alert routing/governor fail-closed), adapter (default null/order fail-closed/gate enforcement/import-safety) |
| runbook | `README.md` | layout, ready-vs-blocked, go-live order, reverting, test commands |

## 2. Deploy-module change (allowed: route-dir module edit + tests)

Added the owner's first-cycle sizing dial to `ultimate_book_live_package.py`:
- `clean3_firstcycle_eff1p18` = 1.25% nominal x CLEAN3_VOL_SCALE (0.948) = 1.185% effective.
  Documented MC (PORTFOLIO_BUILD_W7_FINAL.md §3a/§6): P(pass) 99.36%, P(maxDD) 0.65%,
  ~79 median days, 2-acct balanced P(both) base 99.28% / stress 63.7%, daily-breach 0% even
  under 1.5x stress. Intended pairing: `kelly_lite=True, kelly_conservative=True` (half-Kelly,
  breach-free), `stress_derisk=True`.
- This fills the gap between `clean3_balanced_eff0p71` and `clean3_growth_eff1p42` so the owner
  dial (1.25% first cycle -> 1.5% after first clears -> 2.0% ceiling) has an exact profile for
  each step. The growth (1.5%) and aggressive-ceiling (2.0% via 1.66% eff) profiles already
  existed.
- +2 tests added; the suite is now 94 passing (was 78; the user's reformat plus the additive
  Wave-7 tests account for the rest). Default surface unchanged (DEFAULT_PROFILE still
  `balanced_0p75`, all upgrade flags default-off).

## 3. How the kill-switch / triple-gate compose (the safety chain)

A new order requires ALL of: (a) no halt flag present (`src/safety/runtime_halt`), (b) the repo
triple-gate ON for the active surface, (c) the bridge `live_connect_allowed=True` + ENV creds,
(d) the deploy-module governor `allow_new_entries=True` (which folds the operator
circuit-breaker / `size_cap_override`). The kill-switch trips (a) AND (d) simultaneously, so a
single owner command (`kill_switch.py engage`) flattens new entries by two independent
mechanisms. Verified against the REAL repo: with the current halt flags present,
`kill_switch.py state` reports `kill_switch_engaged: true, new_entries_allowed: false`, and the
monitor cycle reports `action: halted_no_monitor_trade_action`.

## 4. READY now (scaffolding/scripts, tested) vs BLOCKED on owner/broker/VPS

READY (this Mac, no broker):
- All process-manager units, the adapter interface + gated seam, monitoring + kill-switch +
  alert hook, the deploy/push + monitor-cycle scripts, env/deps templates, the two staged
  Phase A patches, and the first-cycle sizing profile. 18 VPS tests + 94 deploy-module tests
  pass. Production `config/agent_config.yaml` and `src/` are UNTOUCHED.

BLOCKED — needs owner / broker / VPS input:
- VPS host + user + repo dir (fill `<PLACEHOLDER>`s in push.sh env, systemd units, compose).
- FTMO broker creds in the VPS `.env` / `.env.<ns>` (two accounts), ENV only.
- Bridge endpoint: `GTOS_BRIDGE_HOST`/`PORT` (default 8001); install `nmetatrader5` (bridge
  client) + `MetaTrader5` on the Windows MT5 host; confirm READ-ONLY connect first.
- NTP time-sync on the VPS.
- Phase A: `git apply` the two patches after review; flip the `ultimate_book_*` triple-gate ON.
- Phase C broker/runtime authority (hard-halt forensic join, V3-vs-live gap, dual-broker audit,
  production-return dossier) — the actual live gate, NOT done here.
- Real alert sink (email/Telegram/Slack/push) via `GTOS_ALERT_WEBHOOK` or a custom sink.

## 5. Caveats / honest notes

- The `SiliconBridgeAdapter.connect()` body targets the `nmetatrader5` API shape inferred from
  `scripts/export_mt5_research_ohlcv.py` (host/port client + `initialize`/`symbol_info_tick`/
  `positions_get`/`order_send`/`account_info`/`history_deals_get`). The owner must reconcile the
  exact method signatures against the installed bridge build on the VPS before live use; it is a
  reviewed seam, not a live-verified driver (we cannot verify it here without the bridge + creds).
- At go-live the reviewed adapter should be promoted into `src/mt5/` (a follow-up patch) so the
  runtime imports it as a first-class `MT5Interface`; today it lives in the route dir as
  scaffolding.
- The first-cycle profile's MC figures are transcribed from PORTFOLIO_BUILD_W7_FINAL.md (not
  re-simulated here); the W7 integrator is the authority for those numbers.
- docker path runs the Python runtime/monitoring only; MT5 itself is Windows-native and reached
  over the bridge — if MT5+bridge are on the same Windows VPS, prefer the systemd/native path.

## Tests

```
ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE python3 -m pytest $ROUTE/test_ultimate_book_live_package.py -q   # 94 passed
python3 -m pytest $ROUTE/GOLIVE_vps_deploy/tests -q                                       # 18 passed
git apply --check $ROUTE/GOLIVE_vps_deploy/patches/0001-*.patch $ROUTE/GOLIVE_vps_deploy/patches/0002-*.patch  # clean, NOT applied
```
