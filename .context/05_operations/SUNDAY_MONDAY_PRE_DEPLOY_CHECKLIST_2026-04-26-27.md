# Sunday 2026-04-26 + Monday 2026-04-27 Pre-Deploy Checklist

**Purpose:** Concrete step-by-step for the GO and STAY branches, post-CEO-decision on v2-active detector flip. Execute on Sunday evening + Monday AM.

**Main HEAD at start of pre-deploy:** capture dynamically. Run:
```bash
HEAD_SHA=$(git rev-parse --short HEAD)
echo "Current HEAD: $HEAD_SHA"
# Verify it's >= the session 40 close (b907f6c) — any later commit is OK.
```
Original session-39-close baseline was `6b85287`; subsequent merges (session 40 close, ADR-006, B.1, C.3, fleet-expansion) have advanced HEAD. Trust `git rev-parse HEAD` over any hard-coded SHA in this document.

---

## Branch A — GO (flip to v2 ACTIVE)

### Sunday 2026-04-26 evening (CEO local time)

1. **Verify CEO GO decision is explicit.** No "maybe" — need a clear yes.

2. **Pre-flip verification** (~10 min):
   ```bash
   python scripts/generate_live_state.py
   cat .context/LIVE_STATE.md | head -30   # confirm HEAD matches `git rev-parse --short HEAD`
   python -m pytest tests/ -q              # verify 2043+/5/1 green
   python scripts/mt5_preflight.py         # 8-check sanity (account, symbols, API)
   ```
   If any fails → HALT, investigate before proceeding.

3. **Canary regression test** (~5 min, ~$2 API):
   ```bash
   python scripts/canary_test.py
   ```
   Expect 59/60 or 60/60 match against the baseline. If <55/60 → abort the flip.

4. **Flip detector in config** (~1 min):
   ```yaml
   # config/agent_config.yaml
   market_state:
     detector_version: v2        # was v2_shadow
   ```
   ```bash
   git add config/agent_config.yaml
   git commit -m "config(detector): flip v2_shadow -> v2 ACTIVE for Monday challenge"
   ```

5. **Rolling restart the fleet** (~5 min):

   > **NOTE:** `scripts/watchdog.ps1` has NO `-Action` CLI verb — it is a
   > supervisor loop (called every ~15 min by Task Scheduler) that respawns
   > dead orchestrators based on PID lock files in `knowledge_base/meta/`.
   > To "stop all" we kill processes manually; to "restart all" we let the
   > next watchdog tick respawn under the new env-var profile, OR launch
   > `start_all.bat` directly. Both paths respect `GTOS_PROFILE` + `GTOS_MODE`
   > set in step 9b (Option A commit `c21d702`).

   ```bash
   # --- Stop all background processes ---
   # 7 orchestrators (each tagged with its symbol via cmd.exe window title or
   # via the PID lock file) + displacement logger + heartbeat monitor +
   # 7 tick-capture daemons.
   #
   # Cleanest: read each PID from its lock file and kill it. The watchdog's
   # Stop-AllTradingProcesses helper already does this — invoke it via:
   pwsh -File scripts/watchdog.ps1
   # When run during the dead zone (01:15-07:45 local) the watchdog short-
   # circuits into Stop-AllTradingProcesses + exit. Outside the dead zone it
   # restarts dead processes; for a forced stop at any time, kill manually:
   for s in XAUUSD US30_cash USDJPY GBPJPY GBPUSD XAGUSD NAS100; do
     LOCK="knowledge_base/meta/.orchestrator_${s}.lock"
     [ -f "$LOCK" ] && PID=$(python -c "import json,sys;print(json.load(open(sys.argv[1]))['pid'])" "$LOCK") && taskkill //F //PID "$PID" 2>/dev/null
   done
   # Displacement logger + heartbeat monitor + tick-capture daemons:
   for L in knowledge_base/meta/.displacement_logger.lock knowledge_base/meta/.heartbeat_monitor.lock knowledge_base/meta/.tick_capture_*.lock; do
     [ -f "$L" ] && PID=$(cat "$L") && taskkill //F //PID "$PID" 2>/dev/null
   done

   # --- Start all (preferred path: start_all.bat) ---
   # start_all.bat reads %GTOS_PROFILE% + %GTOS_MODE% (set in step 9b) and
   # launches all 7 orchestrators + displacement logger. Heartbeat monitor +
   # tick-capture daemons are launched by the next watchdog tick.
   start_all.bat

   # --- OR start manually (if start_all.bat fails) ---
   # Replace `<PROFILE>` with `ftmo` (paid challenge) or `redacted_account` (demo).
   python run_agent.py --mode live --symbol XAUUSD     --profile ftmo &
   python run_agent.py --mode live --symbol US30_cash  --profile ftmo &
   python run_agent.py --mode live --symbol USDJPY     --profile ftmo &
   python run_agent.py --mode live --symbol GBPJPY     --profile ftmo &
   python run_agent.py --mode live --symbol GBPUSD     --profile ftmo &
   python run_agent.py --mode live --symbol XAGUSD     --profile ftmo &
   python run_agent.py --mode live --symbol NAS100     --profile ftmo &
   # Displacement logger (no `--profile` flag — runs continuously, broker-agnostic):
   python scripts/displacement_logger.py --continuous &
   # Heartbeat monitor (module path; no script entry point exists at scripts/):
   python -m src.safety.heartbeat_monitor &
   ```

   > **NOTE:** Both `displacement_logger.py --continuous` and
   > `python -m src.safety.heartbeat_monitor` are auto-launched by the
   > watchdog (`scripts/watchdog.ps1` lines 307 + 412). Manual restart is
   > needed only if the watchdog tick has not fired yet.

6. **Smoke-trade verification** (~5 min):
   ```bash
   python scripts/fn_smoke_trade.py   # validates 7-symbol E2E
   ```
   Expect: order placed → fill → Telegram notification → chart signal → clean close.

7. **Verify v2 is actually producing labels** (~2 min):
   ```bash
   tail -f shadow_logs/structure_detector_divergences.jsonl
   # Within a few M15 candles, should see mso_h1_structure_direction outputs
   # that are NOT 100% bullish (if market regime allows bearish)
   ```

### Monday 2026-04-27 AM

8. **CEO purchases FTMO $100K challenge** (~$500). Match demo settings ($100K tier, 2% risk profile overrides to 0.5% XAUUSD + 1% FX via `config/profiles/redacted_account.yaml` equivalent — confirm `ftmo.yaml` overrides match).

9. **Update `config/profiles/ftmo.yaml`** with new account credentials (MT5 login + password). Commit.

### Step 9b — Set environment variables for autostart (Tuesday onwards)

After Step 9 credentials update + commit, set the persistent env vars
so Task Scheduler's `start_all.bat` autostart + `watchdog.ps1` respawns
pick up FTMO live without further script edits:
```bat
setx GTOS_PROFILE ftmo
setx GTOS_MODE live
```
These take effect in NEW shell sessions, including the next scheduled
`start_all.bat` invocation. Verify in a fresh shell:
```bat
echo %GTOS_PROFILE%
echo %GTOS_MODE%
```
Expect `ftmo` and `live`. The Monday rolling restart in step 10 is the
first invocation that picks them up.

To revert (e.g. abort to demo):
```bat
setx GTOS_PROFILE redacted_account
setx GTOS_MODE demo
```

10. **Rolling restart under ftmo profile** (if different from demo):
    With `GTOS_PROFILE=ftmo` + `GTOS_MODE=live` set persistently in step 9b,
    the next watchdog tick (≤15 min) auto-respawns all dead orchestrators
    under the new profile. To force an immediate restart, follow step 5's
    stop + `start_all.bat` sequence after the env vars are confirmed in
    a fresh shell. The watchdog has no `-Action`/`--profile` CLI verbs;
    profile/mode flow through `%GTOS_PROFILE%` / `%GTOS_MODE%`.

11. **First-hour observation** (active monitoring):
    - Watch for first CANDs via Telegram
    - Verify `shadow_logs/structure_detector_divergences.jsonl` shows v2 activity
    - If multiple CANDs emerge with high WR → confirm edge is alive
    - If flood of CANDs (>25% of M15 candles) → abort, investigate

12. **LONG-WR-watch SPRT gate** (mandatory) — XAUUSD-only, original v2-active gate:
    - After trade #10: log XAUUSD LONG WR; if <30% → halt, CEO council
    - After trade #20: log XAUUSD LONG WR; if <40% → halt, CEO council
    - Document the gate in CLAUDE.md unresolved item #12 before end of day Monday

12b. **Class-aware LONG-WR-watch SPRT gate** (C.3, additive to step 12):
    Run after each tracked instrument's trade #10 and trade #20 in manual mode:
    ```bash
    python -m src.safety.sprt_class_halt_check <SYMBOL> <LONG_n> <LONG_wins>
    # exit 0 = OK / INSUFFICIENT_DATA / CLASS_EXCLUDED  (no action)
    # exit 1 = EARLY_WARNING                            (monitor + flag CEO)
    # exit 2 = HALT_TRIGGERED                           (stop instrument)
    ```
    Class thresholds (Wilson 95% LB - safety margin):
      - **metals** (XAUUSD, XAGUSD): halt <55% / early-warn <50%
      - **indices** (US30_cash, NAS100): halt <40% / early-warn <35%
      - **jpy_pairs** (USDJPY, GBPJPY): halt <45% / early-warn <40%
      - **tight_fx** (GBPUSD): EXCLUDED (n=5 too thin)
    On HALT_TRIGGERED: stop ALL instruments in that class, paste formatted
    Telegram message (`format_telegram_alert(...)`) into @gold_trader_os_bot,
    convene CEO council. Manual enforcement Monday; week-1 automation flips
    `sprt_halt.automation_enabled: true` once orchestrator callback is wired.
    Full playbook: `.context/05_operations/c3_sprt_class_halt_playbook.md`.

13. **Monthly-decay monitor first run**:
    ```bash
    python scripts/monthly_decay_monitor.py --output research/monthly_decay_monitor/2026-04_report.md
    ```
    Will include first live trades from Monday if A3 instrumentation captures them.

### Monday EOD

14. **Capture Monday summary**:
    - # CANDs emitted per symbol
    - # fills, outcomes, realized R
    - Any halts, errors, E2E issues
    - Update `.context/LIVE_STATE.md` via regeneration script
    - Brief Telegram recap

---

## Branch B — STAY (keep v2_shadow through another week)

### Sunday 2026-04-26 evening

1. **Verify CEO STAY decision is explicit.**

2. **Same pre-deploy verification as GO step 2** (tests, preflight, canary).

3. **No config changes.** `detector_version: v2_shadow` stays.

4. **Rolling restart OPTIONAL** — only if:
   - Logger expansion (A1 merge) should go live
   - Trade-record instrumentation (A3 merge) should go live
   - Any other infrastructure deferred since last restart
   Otherwise skip restart; fleet continues on current code.

5. **If restart:** follow steps 5-7 of GO branch but `--detector-version v2_shadow` stays current.

### Monday 2026-04-27 AM

6. **CEO still buys FTMO $100K challenge** (per Session 39 plan).

7. **Fleet deploys on v2_shadow (v1 production decisions)**. Live outcomes start flowing into A3 v1.1-instrumented trade records.

8. **Watch for continued decay signal** — if Monday's XAUUSD WR is in the 10-25% range consistent with Apr v1 data, that's a STAY red flag. Re-evaluate detector decision by midweek.

### Saturday 2026-05-02

9. **Re-run A2 methodology** with the week's new live data + A3 instrumentation. Compare LONG WR under v1 production vs A2's v2-active numbers. If v1 live LONG WR < v2 A2 (33%), flip to v2 next Sunday.

---

## Shared (regardless of GO/STAY)

- **Monthly-decay shadow monitor** runs passively from day 1. Alerts on threshold breach.
- **v2_shadow divergence sampler** (shipped session 38) keeps accumulating weekly classifications → promotion-gate data even if detector stays v2_shadow.
- **Remote agent `trig_014gGA722efDJXD6K64iH9i1`** fires 2026-06-02 14:00 UTC for v2 promotion check — still scheduled regardless of Monday decision.

---

## Emergency contacts / abort procedures

If anything breaks Monday:

1. **Stop fleet:** there is no `-Action stop-all` CLI verb on `scripts/watchdog.ps1`.
   Manual procedure:
   ```bash
   for s in XAUUSD US30_cash USDJPY GBPJPY GBPUSD XAGUSD NAS100; do
     LOCK="knowledge_base/meta/.orchestrator_${s}.lock"
     [ -f "$LOCK" ] && PID=$(python -c "import json,sys;print(json.load(open(sys.argv[1]))['pid'])" "$LOCK") && taskkill //F //PID "$PID" 2>/dev/null
   done
   for L in knowledge_base/meta/.displacement_logger.lock knowledge_base/meta/.heartbeat_monitor.lock knowledge_base/meta/.tick_capture_*.lock; do
     [ -f "$L" ] && PID=$(cat "$L") && taskkill //F //PID "$PID" 2>/dev/null
   done
   # Disable the Task Scheduler watchdog tick so it does not auto-respawn:
   schtasks //Change //TN "GTOS Watchdog" //Disable
   ```
2. **Close open positions** — no `flatten_positions.py` script exists. Manual procedure via MT5 terminal:
   1. Open the MT5 terminal "Trade" tab.
   2. For each open position with magic number 20260401: right-click → "Close Position" (market close).
   3. For each pending order with the same magic: right-click → "Delete" (cancel).
   4. Verify all positions closed via MT5 → View → Reports → P/L summary.
   5. (A script-based flatten tool is a post-Monday research candidate — not implemented as of session 40 close.)
3. **Revert detector flip:** `git revert HEAD` on the config commit → rolling restart per step 5 sequence above.
4. **CEO Telegram notification:** halt reason + current account balance.
5. **Investigate** — no trading until root cause identified + council-approved re-deploy. Re-enable the watchdog Task Scheduler entry only after re-deploy is approved.

---

*Checklist prepared session 39 close 2026-04-25. Valid for Sunday 2026-04-26 + Monday 2026-04-27 only. Refresh if delayed.*
