# Operator's Decision Playbook — Final Version

**Version:** 3.0 — 7-instrument fleet + ADR-006 + B.1 + C.3 + heartbeat per-symbol
**Date:** April 26, 2026
**Operator:** Borhen (Kuala Lumpur, UTC+8)
**System:** 7-instrument autonomous XAUUSD/US30/USDJPY/GBPJPY/GBPUSD/XAGUSD/NAS100 agent on FTMO $100K live (Monday 2026-04-27 launch)
**Access:** SSH or TeamViewer to Windows machine

---

## Quick Reference — Severity Definitions

| Severity | Meaning | Response Time |
|----------|---------|---------------|
| CRITICAL | Capital at risk or system integrity compromised | Immediate — within 5 minutes |
| HIGH | Trading capability degraded or rule violation occurred | Within 30 minutes |
| MEDIUM | Suboptimal operation, no capital risk | Next scheduled check |
| LOW | Administrative, no operational impact | Within 24 hours |

## Quick Reference — Key Paths and Commands

```
Codebase:       ~/Documents/ai-trading-agent/
Config:         config/agent_config.yaml
Logs:           logs/agent_{SYMBOL}_demo.log
PID locks:      knowledge_base/meta/.orchestrator_{SYMBOL}.lock
Trade records:  knowledge_base/trade_records/{SYMBOL}/
Session files:  knowledge_base/live_sessions/{SYMBOL}/
Crash data:     knowledge_base/meta/last_crash.json
Pipeline state: pipeline_state/

Start one:      cd ~/Documents/ai-trading-agent && python run_agent.py --mode demo --symbol XAUUSD
Start all:      for s in XAUUSD US30_cash USDJPY GBPJPY GBPUSD; do python run_agent.py --mode demo --symbol $s & done
Check running:  ps aux | grep run_agent
Kill one:       kill $(cat knowledge_base/meta/.orchestrator_XAUUSD.lock | python -c "import sys,json;print(json.load(sys.stdin)['pid'])")
Kill all:       pkill -f run_agent.py
Check MT5:      python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.terminal_info()); mt5.shutdown()"
Check positions: python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.positions_get()); mt5.shutdown()"
Tail log:       tail -50 logs/agent_XAUUSD_demo.log
Grep errors:    grep -i "ERROR\|CRITICAL\|Exception" logs/agent_XAUUSD_demo.log | tail -20
Today's trades: grep "CANDIDATE\|order_send\|TRADE_OPEN" logs/agent_XAUUSD_demo.log
MAGIC_NUMBER:   20260401
```

---

# CATEGORY 1: SYSTEM FAILURES

---

## Scenario 1: One Process Crashes During Market Hours

**Trigger:** One instrument stops logging candle evaluations. Log file shows a Python traceback or stops updating. Other 4 processes continue normally.

**Severity:** HIGH

**Immediate action:** Check if the crashed instrument has an open trade on MT5.

**Full response:**
1. Run `python -c "import MetaTrader5 as mt5; mt5.initialize(); print([p for p in mt5.positions_get() if p.magic == 20260401]); mt5.shutdown()"` — identify any open positions for the crashed symbol.
2. If open position exists: do nothing to the position. SL and TP are broker-side. The trade is protected. Note the ticket number.
3. Check the log: `tail -100 logs/agent_{SYMBOL}_demo.log` — find the traceback. Note the error type.
4. Delete the stale PID lock: `rm knowledge_base/meta/.orchestrator_{SYMBOL}.lock`
5. Restart the process: `cd ~/Documents/ai-trading-agent && python run_agent.py --mode demo --symbol {SYMBOL} &`

**What NOT to do:** Do not manually close the open trade. Do not restart all 5 processes. Do not modify any config or code.

**Resume criteria:** The restarted process logs a candle evaluation within the next M15 close. If it had an open trade, it picks it up via crash recovery (checks for positions with MAGIC_NUMBER on startup).

---

## Scenario 2: All Processes Crash Simultaneously

**Trigger:** All 5 log files stop updating at the same time. No candle evaluations across any instrument.

**Severity:** CRITICAL

**Immediate action:** Check if the Windows machine is still responsive via TeamViewer or SSH.

**Full response:**
1. SSH in and run `ps aux | grep python` — confirm no agent processes running.
2. Run `python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.positions_get()); mt5.shutdown()"` — check for any open positions. All have broker-side SL/TP.
3. Check the most recent log: `tail -100 logs/agent_XAUUSD_demo.log` — likely cause is MT5 crash, API outage, or Windows restart.
4. Check if MT5 terminal is running: look in Task Manager or run `tasklist | findstr terminal64` from CMD.
5. If MT5 is down: restart MT5 terminal, wait 30 seconds for connection, enable AutoTrading, then restart all processes. If MT5 is up: delete all PID locks (`rm knowledge_base/meta/.orchestrator_*.lock`) and restart all processes.

**What NOT to do:** Do not close any open positions manually. Do not run `pkill` if processes might still be running (check first).

**Resume criteria:** All 5 processes log candle evaluations at the next M15 close. Any open trades are adopted by the restarted processes.

---

## Scenario 3: MT5 Disconnects During an Open Trade

**Trigger:** Log shows `MT5 disconnected` or `terminal_info().connected == False`. An open trade exists.

**Severity:** MEDIUM

**Immediate action:** Do nothing to the trade. SL and TP are server-side at the broker. The trade is protected even if MT5 is offline.

**Full response:**
1. Confirm the trade is protected: the broker holds the SL/TP regardless of MT5 connectivity. This is a feature of MT5's architecture.
2. Check internet on the Windows machine: `ping 8.8.8.8` — if no response, go to Scenario 5.
3. Check if MT5 auto-reconnects: wait 2-3 minutes, then run the MT5 check command. Most disconnections are transient.
4. If MT5 stays disconnected for 10+ minutes: restart the MT5 terminal application manually via TeamViewer.
5. The agent process has a built-in MT5 disconnect block in Gate 3 — it will not attempt new trades until MT5 reconnects. Once reconnected, it resumes automatically.

**What NOT to do:** Do not close the trade through the MT5 mobile app or web terminal. Do not restart the agent process — it handles reconnection.

**Resume criteria:** MT5 shows `connected == True` and the agent process logs resume.

---

## Scenario 4: MT5 Disconnects Before Market Open — Processes Can't Start

**Trigger:** Processes start but log `MT5 initialization failed` or similar. No candle data available.

**Severity:** HIGH (if within 30 minutes of kill zone open)

**Immediate action:** Check if MT5 terminal is running and logged in.

**Full response:**
1. TeamViewer into the Windows machine. Open MT5 terminal. Check if it shows "No Connection" in the bottom right.
2. If MT5 login expired or got logged out: re-enter credentials in File → Login to Trade Account. Wait for "Connected" status.
3. Verify AutoTrading is enabled (the AutoAlgo button in the toolbar must be green/active).
4. Verify all 5 symbols are in Market Watch: XAUUSD, US30.cash, USDJPY, GBPJPY, GBPUSD. If missing: right-click Market Watch → Symbols → add.
5. Kill all agent processes, delete PID locks, restart all: `pkill -f run_agent.py && rm knowledge_base/meta/.orchestrator_*.lock && sleep 5` then start all processes.

**What NOT to do:** Do not start agent processes before MT5 shows connected status. Do not skip the Market Watch symbol check.

**Resume criteria:** All 5 processes log successful MT5 initialization and begin waiting for the next M15 candle.

---

## Scenario 5: Windows Machine Loses Internet

**Trigger:** Cannot SSH or TeamViewer into the machine. Ping fails.

**Severity:** HIGH

**Immediate action:** If open trades exist, do nothing. Broker-side SL/TP protect all positions. Wait for internet to restore.

**Full response:**
1. If you have physical access or a secondary remote method (phone hotspot, neighbor's WiFi): restore connectivity.
2. If no access: wait. All trades have broker-side protection. The worst case is missing trading opportunities during the outage, not losing money.
3. Once internet restores: SSH in, check `ps aux | grep python` for running processes. Check `python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.positions_get()); mt5.shutdown()"` for open positions.
4. If processes died during outage: follow Scenario 2 restart procedure.
5. Log the outage duration and any missed kill zones for the daily review.

**What NOT to do:** Do not try to trade manually from your phone to "compensate" for missed signals. Do not change the system after reconnection.

**Resume criteria:** SSH access restored, all processes running, MT5 connected.

---

## Scenario 6: Windows Machine Goes to Sleep or Restarts

**Trigger:** Machine is unreachable. After reconnecting, uptime shows a restart. Or Windows Update notification was pending.

**Severity:** HIGH

**Immediate action:** Reconnect via TeamViewer, check for open trades, check if processes survived.

**Full response:**
1. Verify Windows power settings are set to "Never sleep" for both plugged in and battery: Settings → System → Power & Sleep → Screen: Never, Sleep: Never.
2. Disable automatic Windows Update restarts: Settings → Windows Update → Advanced Options → Active Hours → set 00:00 to 23:59.
3. Open MT5 terminal. Enable AutoTrading.
4. Check for open positions (run the positions check command). Note any trades.
5. Delete all stale PID locks: `rm knowledge_base/meta/.orchestrator_*.lock`
6. Restart all 5 processes.
7. Verify Market Watch has all symbols.

**What NOT to do:** Do not leave Windows Update set to auto-restart. Do not assume sleep settings are correct — verify them every time this happens.

**Resume criteria:** Power settings confirmed as "Never sleep," processes running, MT5 connected with AutoTrading enabled.

---

## Scenario 7: API Key Rejected or API Balance Hits Zero Mid-Session

**Trigger:** Log shows `AuthenticationError`, `401`, `InsufficientFundsError`, or `rate_limit_error` from the Claude API.

**Severity:** CRITICAL

**Immediate action:** Check the Anthropic console at console.anthropic.com for API credit balance and key status.

**Full response:**
1. If balance is zero: add credits immediately. The system cannot evaluate candles without API access. Every missed M15 candle is a potential missed trade.
2. If API key was revoked/rotated: update the key in the environment variable or `.env` file on the Windows machine. Check `echo $ANTHROPIC_API_KEY` (Git Bash) or the environment variable in the config.
3. If rate limited: this is transient. The system should retry. Check logs for retry logic. If it's hitting rate limits consistently, reduce from 5 simultaneous processes — stagger start times by 60 seconds.
4. Once fixed: restart any processes that died due to the error.
5. Budget check: at ~$2.72/day for 5 instruments, a $85 balance lasts ~31 days. Set a calendar reminder to top up when balance drops below $30.

**What NOT to do:** Do not let the balance hit zero during market hours. Do not reduce the number of instruments to save money without an explicit decision.

**Resume criteria:** API call succeeds. Processes resume candle evaluation.

---

## Scenario 8: Trade Execution Timeout — Order Sent But No Confirmation

**Trigger:** Log shows `order_send timeout` or similar. The `safe_place_order` function hit its 10-second timeout.

**Severity:** HIGH

**Immediate action:** Do NOT manually send another order. The system handles this.

**Full response:**
1. The `safe_place_order` logic already handles this: after timeout, it sleeps 2 seconds, then queries MT5 positions. If the order filled despite the timeout, it adopts the position. If no position exists, it gives up. It NEVER retries.
2. Check the log: `grep "timeout\|adopt\|give_up" logs/agent_{SYMBOL}_demo.log | tail -10` — confirm which path was taken.
3. Independently verify on MT5: `python -c "import MetaTrader5 as mt5; mt5.initialize(); print([p for p in mt5.positions_get() if p.magic == 20260401]); mt5.shutdown()"`
4. If the log says "adopted" and MT5 shows the position: everything is correct. The system manages the trade normally.
5. If the log says "gave up" and MT5 shows NO position: the trade was missed. Log it. Do not intervene.

**What NOT to do:** NEVER manually place the trade the system missed. NEVER add manual retry logic. The `safe_place_order` pattern exists specifically to prevent duplicate orders.

**Resume criteria:** System logs confirm either adoption or abandonment. No manual intervention needed.

---

## Scenario 8A: Owner Re-Approves An Expired POI / Discretionary Setup

**Trigger:** A prior `LIMIT_PLACED` setup expired or was cancelled, the owner points to the same old POI/entry as still valid, and price is approaching or reacting from that level.

**Severity:** HIGH if price is within 1R or within 5 minutes of KZ open/close; otherwise MEDIUM.

**Immediate action:** Determine whether a production execution path exists right now.

**Full response:**
1. Check for a fresh candidate/trade record for the current session.
2. Check `knowledge_base/meta/pending_intent_{SYMBOL}.pkl`.
3. Check MT5 positions and broker orders.
4. If no fresh candidate, no active pending intent, no broker order, and no open position exist, state immediately: `No GTOS execution path exists for this expired POI right now. If you want this discretionary trade, place it manually or use a pre-approved override runbook.`
5. Quote old entry, old SL, old TP, current bid/ask, and current RR if entered now.
6. If current RR is below `risk.min_rr`, state that the original trade is gone and a new entry is a different trade.
7. Log the event as `EXPIRED_POI_REAPPROVAL_LIMITATION` in the monitoring observation ledger.

**What NOT to do:** Do not silently narrate the move while the entry is being lost. Do not claim owner approval alone creates an approved automated execution path. Do not rearm an expired intent, place a manual order, or bypass L2/Gate1 unless a separate pre-approved override tool/runbook exists and all of its checks pass.

**Resume criteria:** The owner either manually acts outside GTOS, a fresh system candidate appears and passes normal checks, or the event is logged as a missed discretionary opportunity with current RR/path evidence.

Reference: `.context/05_operations/GTOS_LIMITATION_EXPIRED_POI_REAPPROVAL_2026-05-06.md`

---

# CATEGORY 2: TRADE ANOMALIES

---

## Scenario 9: Position Size Is Wrong

**Trigger:** MT5 shows a lot size that doesn't match expected. At 1% risk ($1,000) with a given SL distance, the lot size should produce approximately $1,000 loss if SL is hit.

**Severity:** CRITICAL

**Immediate action:** If the lot size is MORE than 2x expected: close the trade immediately from MT5 terminal.

**Full response:**
1. Calculate expected lot size: `risk_dollars / (SL_distance_in_price * contract_size * tick_value)`. For XAUUSD with $5 SL: $1,000 / ($5 * 100 * 1) = 2.0 lots. For USDJPY the calculation uses `trade_tick_value` from MT5 (this was the Bug #7 fix — verify `_calculate_lots()` is using MT5's `symbol_info().trade_tick_value`).
2. If lot size is 2-5x too large: close immediately. This is a position sizing bug. Stop the process for that instrument. Do NOT restart until the bug is identified.
3. If lot size is 2x too small: the trade is safe but underperforming. Let it run. Investigate after market close.
4. Check `grep "lot_size\|calculate_lots\|position_size" logs/agent_{SYMBOL}_demo.log | tail -20` for the calculation trail.
5. If this is a JPY pair: verify the Bug #7 fix is deployed. Run `git log --oneline -5` to confirm the lot sizing commit is present.

**What NOT to do:** Do not let an oversized position run. Do not assume "it's just a demo" — the whole point of demo is to find these bugs before funded.

**Resume criteria:** Root cause identified and fixed. Lot size calculation verified against manual calculation for that instrument. Restart the process.

---

## Scenario 10: Trade Opens Outside Kill Zone

**Trigger:** Trade timestamp is outside all configured kill zones. London: 07:00-10:30 UTC. NY: 13:00-15:30 UTC. Tokyo: 00:00-03:00 UTC (JPY only).

**Severity:** CRITICAL — this is Emergency Stop Condition #4.

**Immediate action:** Stop ALL trading across ALL instruments. This is a logic bug, not a one-off.

**Full response:**
1. Close any position that was opened outside kill zones if it is still open.
2. Kill all 5 processes: `pkill -f run_agent.py`
3. Check the log for the offending trade: `grep "CANDIDATE\|order_send\|kill_zone\|_get_active_kill_zone" logs/agent_{SYMBOL}_demo.log | tail -30`
4. Likely cause: `_get_active_kill_zone()` in `orchestrator.py` is not correctly identifying KZ boundaries, OR the M15 candle timestamp is in local time instead of UTC. Verify timezone handling.
5. Do NOT resume any instrument until the root cause is found and fixed. This is a Gate 3 rule violation.
6. **Note:** XAUUSD is configured to skip the 13:00 UTC candle (`skip_first_ny_candle: true` in config). If you see XAUUSD NOT evaluating the 13:00 candle while other instruments do evaluate it, this is BY DESIGN — not a bug. The 13:00 UTC candle showed 0% WR (n=7) with 4 converging microstructural explanations. The skip applies only to XAUUSD unless configured otherwise per instrument.

**What NOT to do:** Do not resume just the "good" instruments. If one broke the KZ rule, the logic may be wrong for all. Do not confuse the intentional 13:00 XAUUSD skip with a KZ violation.

**Resume criteria:** Root cause identified. Fix committed. Tested with a simulated candle at the boundary times. All processes restarted.

---

## Scenario 11: More Than 1 Trade Triggers in a Single Kill Zone

**Trigger:** Two or more trades for the same instrument within one kill zone window. Gate 3 allows max 1 per KZ.

**Severity:** CRITICAL — Emergency Stop Condition #3.

**Immediate action:** Close the second trade immediately if still open. Stop that instrument's process.

**Full response:**
1. Verify both trades are for the same instrument AND same kill zone (not one in London and one in NY).
2. Close the second trade (the later one) from MT5 terminal.
3. Kill that instrument's process.
4. Check `grep "TRADE_OPEN\|max_trades\|kz_trade_count" logs/agent_{SYMBOL}_demo.log | tail -20` — the Gate 3 check should have blocked this.
5. Root cause is likely: the `max_trades_per_kz` counter reset incorrectly, or the crash recovery adopted a position AND then the system took another trade.

**What NOT to do:** Do not let multiple trades run simultaneously for one instrument. The risk model assumes one trade per KZ.

**Resume criteria:** Gate 3 counter logic verified. Fix applied. Restarted.

---

## Scenario 12: Two Correlated Instruments Signal Simultaneously

**Trigger:** USDJPY and GBPJPY both produce CANDIDATE within the same kill zone.

**Severity:** MEDIUM

**Immediate action:** Check logs for `CORRELATION_ADJUSTMENT` entry confirming reduced position size.

**Full response:**
1. The system automatically reduces position size for the second correlated trade via `portfolio_risk.py`. First trade = full 1% risk. Second = 0.5% risk (1.5% combined max).
2. Verify log shows `RISK_REDUCED_CORRELATION: GBPJPY 1.0% → 0.5% (USDJPY position open)` or equivalent.
3. Verify actual MT5 lot size matches the reduced risk amount.
4. If no `CORRELATION_ADJUSTMENT` log entry but both trades at full size: this is a bug. Combined exposure is 2% on correlated instruments. Manually close the second trade's position to half size on MT5.
5. Report the bug for immediate fix.

**What NOT to do:** Don't manually prevent the second trade. Don't override the AI's CANDIDATE decision. Just verify sizing is correct.

**Resume criteria:** Once correlation adjustment confirmed in logs or manually corrected.

---

## Scenario 13: SL or TP Doesn't Match System Output

**Trigger:** The SL or TP on the MT5 position differs from what the AI specified in its CANDIDATE output.

**Severity:** HIGH

**Immediate action:** Check if the discrepancy favors or endangers the account.

**Full response:**
1. Pull the AI's output: `cat knowledge_base/trade_records/{SYMBOL}/{date}_{kz}_{time}.json | python -m json.tool | grep -A5 "sl\|tp\|stop_loss\|take_profit"`
2. Compare to MT5 position: run the positions check command and note SL/TP values.
3. If SL is WIDER than specified (more risk): close the trade immediately. This means more than 1% risk.
4. If SL is TIGHTER than specified: the trade is safer but may get stopped prematurely. Let it run.
5. If TP is different: less critical, but investigate. Check `execution.py` for rounding or price adjustment logic. MT5 may adjust levels to tick precision.

**What NOT to do:** Do not manually adjust SL/TP to match the AI output unless the SL is provably wider than intended. The execution engine may have legitimate reasons for adjustments (minimum stop distance broker rules, tick size rounding).

**Resume criteria:** Discrepancy explained. If it's a rounding/tick issue: document and move on. If it's a bug: fix before the next trade.

---

## Scenario 14: Trade Closes at an Unexpected Level

**Trigger:** Position closed at a price that isn't TP1, TP2, TP3, SL, or the BE trailing stop. No partial close sequence visible.

**Severity:** MEDIUM

**Immediate action:** Check if a timeout trailing stop triggered.

**Full response:**
1. Check the log: `grep "timeout\|trailing\|BE_stop\|close\|partial" logs/agent_{SYMBOL}_demo.log | tail -30`
2. Possible legitimate causes: (a) Timeout trailing — after 2 hours past KZ close, system moves SL to break-even. If price reverses to BE, the trade closes at entry. (b) Broker-side margin close. (c) Partial close changed the ticket, and the new ticket wasn't tracked.
3. If the close matches the timeout BE level: this is working as designed. Log the outcome.
4. If the close matches no known level: check for ticket number changes (MT5 changes tickets on partial closes). Run `grep "ticket\|partial" logs/agent_{SYMBOL}_demo.log | tail -20`.
5. If you cannot explain the close: save all logs, note the exact close time and price, investigate after market hours.

**What NOT to do:** Do not re-enter the trade manually. Do not assume the system is broken — investigate first.

**Resume criteria:** Close reason identified. If it's a bug: fix and restart. If it's designed behavior: document and continue.

---

## Scenario 15: AI Produces CANDIDATE with Gibberish or Contradictory Reasoning

**Trigger:** The AI's JSON output contains contradictions (e.g., `direction: LONG` but reasoning says "bearish structure"), nonsensical price levels, or garbled text.

**Severity:** HIGH

**Immediate action:** If Gate 1 passed the trade and it's already on MT5 — let it run (SL protects it). If not yet executed — check if the process rejected it.

**Full response:**
1. Check the trade record: `cat knowledge_base/trade_records/{SYMBOL}/{date}_{kz}_{time}.json | python -m json.tool`
2. The system has strict enum validation on direction, grade, and framework fields. If the AI returned invalid values, the system should have rejected it and treated it as NO_TRADE.
3. If the trade was executed despite contradictory reasoning: Gate 1 checks (grade, direction, RR, SL) all passed, meaning the numbers were valid even if the text was confused. The trade is legitimate by the rules.
4. Save the full AI response for analysis. Check if the API model version changed: `grep "model\|claude" logs/agent_{SYMBOL}_demo.log | tail -5`
5. If gibberish outputs happen 3+ times in one session: check if you're hitting token limits (`max_tokens` too low), or if the prompt was corrupted.

**What NOT to do:** Do not change the prompt based on one gibberish output. Do not manually close a trade that passed all gates just because the reasoning text reads poorly.

**Resume criteria:** Isolated incident → continue. 3+ occurrences in a day → halt that instrument, investigate prompt and API response.

---

# CATEGORY 3: PERFORMANCE SCENARIOS

---

## Scenario 16: 3 Consecutive Losses on One Instrument

**Trigger:** SPRT tracking shows 3 straight losses for a single instrument.

**Severity:** LOW

**Immediate action:** Do nothing. This is within normal variance. Update SPRT.

**Full response:**
1. Update the SPRT cumulative log-likelihood for that instrument. After each loss: `Λ += log((1-p₁) / (1-p₀))` where p₁ = batch WR, p₀ = breakeven WR.
2. Check the SPRT table: at 3 losses from 3 trades, no instrument's kill boundary is reached (kill requires ≤3 wins from 10+ trades for most instruments).
3. Review the 3 losing trades' reasoning: `ls -la knowledge_base/trade_records/{SYMBOL}/ | tail -3` and read each file. Look for common failure patterns (same structure error, same KZ, same direction).
4. If all 3 losses share a pattern (e.g., all NY opens, all SHORT): note it in the monitoring log. Do NOT filter based on 3 data points.
5. Continue trading. This is not statistically meaningful.

**What NOT to do:** Do not reduce risk. Do not skip the next trade. Do not change the prompt. Three losses is a 1-in-8 event at 50% WR. It happens.

**Resume criteria:** Already running. No intervention needed.

---

## Scenario 17: 5 Consecutive Losses on One Instrument

**Trigger:** 5 straight losses for one instrument. This hits the instrument-specific halt condition.

**Severity:** HIGH

**Immediate action:** Halt trading on that instrument. Kill its process.

**Full response:**
1. Kill the process: find PID from `ps aux | grep {SYMBOL}` and `kill {PID}`.
2. Update SPRT. At 0 wins from 5 trades: check if the kill boundary is crossed (for XAUUSD, kill at ≤3 from 10 — not crossed yet, but heading there fast).
3. Review ALL 5 losing trades' records. Categorize: were they all the same direction? Same KZ? Same market regime? Did the AI identify the same setup type?
4. Cross-check against the batch data: did the batch ever produce 5 consecutive losses? If the batch worst streak was 5 at -3.22R, this is at the tail but within historical range.
5. Keep the instrument halted for 5 trading days. After the halt, restart and monitor the next 5 trades closely. If the first 2 of those 5 lose: halt permanently until walk-forward window review.

**What NOT to do:** Do not change the prompt. Do not add filters. Do not start manually trading that instrument. The 3-month walk-forward window is sacred.

**Resume criteria:** 5 trading day cool-off period. Restart with heightened monitoring.

---

## Scenario 18: SPRT Approaches Kill Boundary for an Instrument

**Trigger:** Cumulative SPRT score is within 1 trade of crossing the kill boundary (S_n approaching ≤ -1.556).

**Severity:** HIGH

**Immediate action:** Continue trading. SPRT is designed to make mechanical decisions — approaching the boundary is not crossing it.

**Full response:**
1. Calculate exact S_n value. If one more loss would cross the kill boundary: continue. The whole point of SPRT is removing emotion from this decision.
2. Review the instrument's full trade record against the SPRT table. Example: XAUUSD at 20 trades needs ≤8 wins to kill. If you're at 9 wins from 19 trades, one more loss puts you at 9/20 → still in continue range.
3. Prepare mentally for the kill. If the next trade is a loss and the boundary crosses: you follow Scenario 19. No second-guessing.
4. Check if other instruments are also approaching their kill boundaries. If 2+ instruments are near kill: the portfolio-level SPRT matters more — check that table.

**What NOT to do:** Do not reduce position size "just in case." Do not trade with extra caution. Do not preemptively kill the instrument.

**Resume criteria:** Already running. Next trade either keeps you in continue range or triggers Scenario 19.

---

## Scenario 19: SPRT Crosses Kill Boundary

**Trigger:** Cumulative SPRT score S_n ≤ -1.556 for an instrument.

**Severity:** CRITICAL

**Immediate action:** Kill that instrument's process immediately and permanently for this walk-forward window.

**Full response:**
1. Kill the process: `kill $(cat knowledge_base/meta/.orchestrator_{SYMBOL}.lock | python -c "import sys,json;print(json.load(sys.stdin)['pid'])")`
2. Delete the PID lock: `rm knowledge_base/meta/.orchestrator_{SYMBOL}.lock`
3. Close any open position for that instrument. This is the ONE time you close a trade manually.
4. Record the kill decision: total trades, total wins, final S_n value, date. Write it to a file: `echo "{SYMBOL} killed at trade {N}, {W} wins, S_n={X}, $(date)" >> knowledge_base/meta/sprt_kills.log`
5. Do NOT restart this instrument until the current 3-month walk-forward window closes (WF-1 ends June 2026). At the window boundary, re-evaluate: run a fresh batch test on new data, check if market regime changed, decide whether to re-deploy.

**What NOT to do:** Do not "give it one more chance." Do not rationalize why the losses were bad luck. The SPRT decision is pre-committed and non-negotiable. This is the entire point of having SPRT — it removes the temptation to override with emotion.

**Resume criteria:** Not until the next walk-forward window. Re-deployment requires a fresh batch test showing positive expectancy on data from the period when the instrument was killed.

---

## Scenario 20: Portfolio Drawdown Hits 3%

**Trigger:** Account equity drops to $97,000 or below ($3,000 loss from $100,000 starting).

**Severity:** HIGH

**Immediate action:** Reduce risk on all instruments from 1.0% to 0.5% until equity recovers above $98,000.

**Full response:**
1. Update `config/agent_config.yaml`: change `risk_percent: 1.0` to `risk_percent: 0.5` for all instruments.
2. Restart all processes to pick up the config change.
3. Review the drawdown composition: which instruments contributed? Is it concentrated (one instrument doing all the damage) or distributed?
4. If one instrument is responsible for >60% of the drawdown: consider halting it early (don't wait for SPRT kill).
5. At 0.5% risk, you need ~10% equity growth to recover the 3%, which takes longer. This is intentional — protect capital first.

**What NOT to do:** Do not increase risk to "recover faster." Do not close all positions. Do not stop all trading. A 3% drawdown is uncomfortable but survivable.

**Resume criteria:** Equity recovers above $98,000. Restore risk to 1.0%.

---

## Scenario 21: Portfolio Drawdown Hits 4%

**Trigger:** Account equity drops to $96,000 or below. Approaching FTMO's 5% daily loss limit.

**Severity:** CRITICAL — Emergency Stop Condition #1.

**Immediate action:** HALT ALL TRADING. Kill all 5 processes immediately.

**Full response:**
1. `pkill -f run_agent.py` — stop everything.
2. Do NOT close existing positions unless they are currently losing and would breach 5% if they hit SL. If all positions have tight stops, let them play out. If any position's SL would push total loss past 5%: close that position.
3. Review the full sequence of events: how did you get to 4%? Was it a single large loss (position sizing bug?), or accumulated small losses?
4. Calculate: how many R of remaining risk are in open positions? If open positions can lose another 1%, you're at 5% = FTMO breach. Close enough positions to ensure worst-case stays under 5%.
5. Do NOT resume trading today. Wait until the next trading day. When resuming: use 0.5% risk until equity recovers above $97,000.

**What NOT to do:** Do not try to recover the drawdown with a bigger position. Do not override FTMO rules. Breaching 5% daily means you fail the challenge.

**Resume criteria:** Next trading day. 0.5% risk. Sustained recovery to $97,000 before restoring 1.0%.

---

## Scenario 22: Zero Trades for an Entire Week Across All Instruments

**Trigger:** Five full trading days pass. All instruments evaluated candles normally but every evaluation was NO_TRADE.

**Severity:** MEDIUM

**Immediate action:** Check that the system is actually evaluating candles, not silently blocked.

**Full response:**
1. For each instrument, verify candle evaluations are happening: `grep "EVALUATING\|NO_TRADE\|pre_screen" logs/agent_{SYMBOL}_demo.log | tail -20`. You should see dozens of evaluations per day per instrument.
2. If evaluations ARE happening and all are NO_TRADE: the market is in a low-conviction regime. This is the system working correctly — it's being selective.
3. Sample 5-10 NO_TRADE decisions across instruments. Read the AI's reasoning. Is it citing legitimate structural concerns (unclear D1, no OB retests, conflicting HTF signals)? If yes: the system is right.
4. Check D1 structure for each instrument. If D1 is "transitional" or "unclear" for all 5 instruments simultaneously: the entire market is in regime transition. This is normal around holidays, pre-FOMC, or during major geopolitical uncertainty.
5. At the 4.5 trades/month/instrument average, a zero-trade week has ~15-20% probability for individual instruments and ~3-5% for the portfolio. It happens.

**What NOT to do:** Do not lower the grade filter. Do not reduce the minimum RR. Do not add new instruments to increase frequency. The system's selectivity IS the edge.

**Resume criteria:** No action needed. Trades will come when market conditions align.

---

## Scenario 23: Zero Trades for 2+ Weeks

**Trigger:** 10+ trading days with zero trades across all instruments.

**Severity:** HIGH

**Immediate action:** Verify the system is not silently broken.

**Full response:**
1. Run a comprehensive check: for each instrument, verify (a) candle evaluations are logged, (b) pre-screen is not rejecting everything, (c) the AI is being called (API charges should reflect this), (d) no Gate 1 or Gate 3 is permanently blocking.
2. Check API billing: at ~$2.72/day, 2 weeks = ~$38. If billing shows $0: the system is not calling the API. Find the block.
3. If the system IS evaluating and the API IS being called: pull 20 NO_TRADE decisions across different instruments and days. Categorize the rejection reasons.
4. If every rejection cites the same reason (e.g., "D1 structure unclear"): verify Component 2 is computing D1 structure correctly. A bug in structure detection could make D1 appear "unclear" permanently.
5. If rejections are diverse and legitimate: this is a genuine extended low-conviction market. Rare but possible (happened in July 2025 for gold). Continue.

**What NOT to do:** Do not change the prompt to be less selective. Do not force trades. The worst thing you can do is relax filters during a genuine low-conviction period — that's when false signals are most common.

**Resume criteria:** If system is verified working: continue waiting. If a bug is found: fix and restart. If this extends to 3+ weeks: run a quick batch test on recent dates ($5-10) to verify the prompt still produces CANDIDATEs on recent data.

---

## Scenario 24: One Instrument Has 0 Trades While Others Are Active

**Trigger:** After 2+ weeks, one instrument shows zero trades while others have 3+ trades each. No crashes or errors logged.

**Severity:** HIGH — potential silent failure.

**Immediate action:** Check that instrument's logs for the last 48 hours of evaluations.

**Full response:**
1. `grep "EVALUATING\|pre_screen\|NO_TRADE\|API\|spread" logs/agent_{SYMBOL}_demo.log | tail -50` — verify the full pipeline is running.
2. If pre-screen rejects EVERY candle: check D1 bias computation. If D1 has been "unclear" or "transitional" for 2+ weeks for that instrument specifically while others show clear bias: the instrument may be in a genuine ranging regime.
3. If candle evaluations happen but the AI always returns NO_TRADE: sample 5 NO_TRADE decisions. Is the AI citing the same objection every time? This could indicate a prompt calibration issue for that instrument.
4. If the spread gate is blocking: `grep "spread" logs/agent_{SYMBOL}_demo.log | tail -20`. The spread gate values were recalibrated in the Bug #3 fix — verify the config values are correct for this instrument.
5. If nothing is logged for that instrument at all: the process crashed silently. Check `ps aux | grep {SYMBOL}`. If dead: follow Scenario 1.

**What NOT to do:** Do not assume it's "just a slow instrument." GBPUSD averaging 0.8 trades/month is the only instrument where 2 weeks of zero trades is expected. For the others, this warrants investigation.

**Resume criteria:** Root cause identified. Either (a) the instrument is legitimately in a no-trade regime (document and continue), or (b) a bug is found and fixed.

---

## Scenario 25: Win Rate Is 45% After 15 Trades on an Instrument

**Trigger:** 6 or 7 wins from 15 trades (40-47% WR) on a specific instrument.

**Severity:** MEDIUM

**Immediate action:** Check the SPRT table. At 15 trades, this is still in the "continue" range for most instruments.

**Full response:**
1. SPRT check for that instrument. Example — XAUUSD at 15 trades: kill at ≤5 wins, confirm at ≥10. At 7 wins: continue range. The system has NOT failed yet.
2. However, 45% WR is below breakeven for all instruments (breakeven ranges from 34-42%). If this persists, the instrument will eventually hit the SPRT kill boundary.
3. Decompose the losses: are they concentrated in one KZ, one direction, or one market regime? `grep "WIN\|LOSS" knowledge_base/trade_records/{SYMBOL}/* | tail -15` (or read each trade record).
4. If losses are clustered (e.g., 5/7 losses all in NY session): note this for the walk-forward review. Do NOT filter based on 15 trades.
5. Continue trading. At 45% WR, the SPRT will reach the kill boundary at roughly trade 20-25. Let it play out mechanically.

**What NOT to do:** Do not preemptively kill the instrument. Do not change the prompt. Do not add filters. 15 trades is not enough to distinguish bad luck from bad edge. Let SPRT decide.

**Resume criteria:** Already running. SPRT makes the decision.

---

# CATEGORY 4: MARKET REGIME EVENTS

---

## Scenario 26: Gold Drops 3%+ in a Single Day

**Trigger:** XAUUSD intraday move exceeds 3% (approximately $60-90 at current prices). This is a flash crash, war escalation, or central bank shock.

**Severity:** MEDIUM (if no open gold position) / CRITICAL (if long gold)

**Immediate action:** Check if the system has an open XAUUSD position. If LONG in gold: it's already hit SL or is deeply underwater.

**Full response:**
1. If LONG gold with SL: the SL should have triggered. Verify on MT5. If SL executed: loss is capped at 1%. Log it and continue.
2. If SL didn't execute (gap through SL): the loss exceeds 1%. Calculate actual loss. This is the gap risk documented in the architecture. At $5 SL, a $30 gap = 6x expected loss = 6%. Check total account drawdown.
3. If the system had no gold position: the 3% move creates opportunity. D1 structure will shift. The system will adapt on the next trading day. Let it.
4. Check other instruments: a gold flash crash may coincide with JPY strength (safe haven) and equity weakness (US30 drop). Correlated moves could mean 2-3 instruments have open positions.
5. If total portfolio loss from this event exceeds 4%: follow Scenario 21 (halt all trading).

**What NOT to do:** Do not manually enter a "recovery trade." Do not blame the system for gap risk — it's inherent in leveraged markets. Do not panic-close other instruments' positions unless they're also deeply negative.

**Resume criteria:** Wait for the next trading session. Let D1 structure update. If drawdown is manageable: resume normally. If drawdown exceeds 4%: follow halt procedures.

---

## Scenario 27: NFP or FOMC Day

**Trigger:** Calendar shows Non-Farm Payrolls (first Friday of month) or FOMC rate decision day.

**Severity:** LOW

**Immediate action:** No special handling needed. The system operates normally.

**Full response:**
1. The Monte Carlo analysis confirmed: news day WR is 68% vs non-news 64%. News days are NOT worse.
2. The kill zones are designed to capture post-news displacement moves, which are often the cleanest setups of the month. NFP at 13:30 UTC falls within NY KZ (13:00-15:30). FOMC at 19:00 UTC falls outside KZ — no trades.
3. The system's pre-screen and AI evaluation naturally account for extreme volatility. Wider ATR = wider SL = smaller position size (the position sizing formula adapts).
4. If you're paranoid about a specific event: you may manually reduce risk to 0.5% for that day ONLY via config change. But the data does not support this.
5. After the event: expect higher-quality setups. The displacement from news events creates exactly the kind of structure the system thrives on.

**What NOT to do:** Do not skip trading on news days. Do not manually close trades before the announcement. Do not add a news event filter without backtesting it.

**Resume criteria:** No action needed. The system handles this.

---

## Scenario 28: Broad Market Stress (VIX Spike, Correlation Breakdown)

**Trigger:** VIX spikes above 30. Normally uncorrelated instruments start moving in lockstep. Risk-off across all markets.

**Severity:** MEDIUM

**Immediate action:** Monitor total portfolio exposure. If multiple instruments have open trades: calculate aggregate risk.

**Full response:**
1. During extreme stress, correlations spike toward 1.0. Your XAUUSD ↔ USDJPY natural hedge (-0.42) may break. Gold and JPY may move in opposite directions than normal.
2. Count open positions across all instruments. If 3+ positions are open simultaneously: total risk could be 3%+ even though each is independently 1%. The correlation assumption of independence no longer holds.
3. If 3+ positions open AND all in the same direction relative to USD: consider closing the most recent (smallest edge) position to reduce aggregate exposure.
4. Check the 2% daily loss circuit breaker is active. If P&L for the day is already -1.5%: manually halt new trades by setting `risk_percent: 0` in config.
5. This is temporary. Stress regimes typically last 1-3 days for the acute phase. Resume normal operations when VIX drops below 25.

**What NOT to do:** Do not shut down the system entirely — stress events often produce the highest-quality displacement setups in the recovery phase. Do not add a VIX filter without backtesting.

**Resume criteria:** Aggregate portfolio exposure is within 2% simultaneously. VIX subsides.

---

## Scenario 29: Gold Enters Persistent Ranging Regime

**Trigger:** D1 structure for XAUUSD shows no clear HH/HL or LH/LL for 15+ consecutive trading days. D1 bias is "transitional" or "unclear."

**Severity:** MEDIUM

**Immediate action:** Let the system handle it. The pre-screen will filter out low-conviction setups.

**Full response:**
1. The system's pre-screen requires clear D1 bias. During ranging, most gold candle evaluations will be rejected at the pre-screen level (no API cost).
2. Gold trade frequency will drop from ~4.5/month to ~1-2/month. This is the system protecting you from low-probability trades in unfavorable conditions.
3. Other instruments may still be trending. Check US30, USDJPY, GBPJPY — they don't correlate with gold. The portfolio provides diversification precisely for this scenario.
4. Monitor the range boundaries. When gold eventually breaks out of the range (with displacement + BOS), the system will re-engage. The first BOS after a range is often a high-R setup.
5. If ranging persists for 30+ days: verify that the D1 structure computation is correct. A bug could make D1 appear unclear even during trending conditions.

**What NOT to do:** Do not override the pre-screen to force gold trades during ranging. Do not switch to a "range trading" strategy. The system's edge is trend-following OB retests — it does not have an edge in ranges.

**Resume criteria:** D1 structure shows clear directional bias. Trades will flow naturally.

---

## Scenario 30: Suspected Regime Transition (Bull → Bear)

**Trigger:** D1 structure shifts from bullish (HH/HL) to bearish (LH/LL) over 5-10 trading days. The system should start producing SHORT CANDIDATEs.

**Severity:** MEDIUM

**Immediate action:** Monitor. The system is designed to trade both directions.

**Full response:**
1. Check if the system produces SHORT CANDIDATEs: `grep "direction.*SHORT\|LONG" logs/agent_XAUUSD_demo.log | tail -20`. If SHORTs appear: the system is adapting. The batch validated SHORTs at 87.5% WR (3/3 wins).
2. Expect a transition period of 5-10 days where D1 is "transitional" and trade frequency drops. This is normal.
3. Once bearish D1 establishes: the system applies the same OB retest logic to bearish structure. The setup rules are direction-agnostic.
4. Track SHORT performance separately. The system has limited SHORT data (7 total across all batches). First 5 live SHORTs are pure calibration — don't draw conclusions.
5. Update the CUSUM tracker: if the system starts losing on SHORTs (WR < 40% on 10+ SHORT trades), it may indicate the OB retest edge is LONG-only. This would be a significant finding.

**What NOT to do:** Do not disable SHORT trading. Do not manually filter to LONG-only. Do not change the prompt. Let the system trade as designed and collect data.

**Resume criteria:** No intervention. Data collection mode for SHORT trades.

---

# CATEGORY 5: OPERATOR PSYCHOLOGY

---

## Scenario 31: You Disagree with a Trade the AI Took

**Trigger:** You look at the chart on TradingView and think "this is a terrible setup." The AI took it anyway.

**Severity:** LOW

**Immediate action:** Do nothing. Note your disagreement in a separate file.

**Full response:**
1. Write your objection: `echo "$(date) - {SYMBOL} - I disagreed because: {your reasoning}" >> knowledge_base/meta/operator_disagreements.log`
2. Let the trade play out. Your job is MONITORING, not TRADING. The AI evaluated the full MSO — you're looking at a chart with human bias.
3. After the trade closes (win or loss), read the AI's full reasoning from the trade record. Compare your objection to its analysis.
4. Track your disagreement accuracy over 20+ trades. If you're right >70% of the time: there's signal in your objections worth formalizing. If you're right <50%: your chart reading has more bias than you think.
5. This data becomes input for the walk-forward review. It does NOT become input for prompt changes mid-window.

**What NOT to do:** Do not close the trade. Do not reduce position size. Do not override the system. One disagreement teaches nothing. 20 disagreements is data.

**Resume criteria:** Already running. Your job is to record, not to react.

---

## Scenario 32: You Want to Override the System and Close a Trade Early

**Trigger:** An open trade is at +0.5R or moving against you, and you feel the urge to close it manually.

**Severity:** LOW (for the trade) / HIGH (for your discipline)

**Immediate action:** Step away from the computer for 15 minutes.

**Full response:**
1. The system has mechanical exit rules: 50%/25%/25% partial closes, timeout trailing, SL. Every possible exit is pre-defined.
2. If you close early, you corrupt the walk-forward data. The trade's outcome will not reflect the system's rules. You'll never know if the system would have won or lost.
3. Every early close moves you further from statistical validation. You need 44 clean trades per walk-forward window. Every corrupted trade extends the timeline.
4. Ask yourself: "Do I have NEW INFORMATION the system doesn't have?" If the answer is "no, I'm just nervous" — walk away. If the answer is "yes, there's a specific event not in the system's data" (e.g., breaking news of a central bank intervention): then closing is justified. Log why.
5. If you override: record it in the disagreement log with full reasoning. Track whether your overrides improve or degrade the system's returns over time.

**What NOT to do:** Do not close trades based on P&L anxiety. Do not "take partial profits early" outside the system's rules. Do not convince yourself that "this time is different."

**Resume criteria:** You either stepped away and the urge passed, or you overrode with documented reasoning. Either way, the system continues.

---

## Scenario 33: You're Tempted to Change the Prompt After a Loss Streak

**Trigger:** 3-5 consecutive losses. You think you see the problem. You want to add a filter or modify the evaluation criteria.

**Severity:** CRITICAL — for your process discipline.

**Immediate action:** STOP. Read this scenario. Then close the prompt file.

**Full response:**
1. The walk-forward protocol is NON-NEGOTIABLE: NO prompt changes during the 3-month test window (WF-1: April-June 2026).
2. Loss streaks are expected. The Monte Carlo showed a worst streak of 5 losses (-3.22R). At 60% WR, a 3-loss streak has ~6.4% probability per 10-trade sequence. It will happen roughly every 15-20 trades.
3. If you change the prompt now, you restart the walk-forward clock. The next 44 trades don't count because the prompt changed. You've wasted all prior live data.
4. Write your idea in a file: `echo "$(date) - Prompt change idea: {description}" >> knowledge_base/meta/deferred_prompt_changes.log`. At the walk-forward boundary (June 2026), review all deferred ideas, batch-test the best ones, and implement the winners.
5. The urge to fix the prompt after losses is the #1 destroyer of systematic trading. It's curve-fitting to noise. You are better than this.

**What NOT to do:** Do not open `primary_analyzer_prompt.py`. Do not "just test a small change." Do not convince yourself this is a "bug fix" when it's actually a filter addition. Bug fixes (crashes, data errors) are allowed. Strategy changes are not.

**Resume criteria:** The urge passes. The walk-forward window is intact. Your deferred ideas file grows. You'll thank yourself in June.

---

## Scenario 34: You're Tempted to Increase Risk After a Win Streak

**Trigger:** 5+ consecutive wins. Account is up 3-5%. You want to increase from 1% to 1.5% or 2% per trade.

**Severity:** HIGH — for your risk management.

**Immediate action:** Do not change the risk. Re-read the Monte Carlo results.

**Full response:**
1. At 1.5% risk, there's a 7.1% chance of a 10% drawdown (prop firm ruin). At 2%, that probability rises to ~15-20%. The math is not in your favor.
2. A 5-win streak at 60% WR has ~7.8% probability. It happens. It doesn't mean the edge got better.
3. The funded account plan is: 0.75% initially, scale to 1.0% after SPRT confirmation. There is no scenario where going above 1.0% on a single account is justified by the data.
4. If you want to scale: add another funded account with the same system at 0.75-1.0% risk. Multiple accounts at moderate risk beats one account at high risk.
5. The win streak will end. When it does, you'll be glad you didn't increase risk.

**What NOT to do:** Do not change `risk_percent` in config. Do not add "just one larger trade." Do not confuse a hot streak with improved skill.

**Resume criteria:** Already running at 1.0%. The config stays as is.

---

## Scenario 35: You Haven't Checked the System in 2 Days

**Trigger:** Life happened. You didn't monitor the system for 48 hours.

**Severity:** MEDIUM

**Immediate action:** Check in this order: (1) account equity, (2) open positions, (3) process health.

**Full response:**
1. Account equity: log into FTMO dashboard or check MT5. Is equity still above $96,000? If yes: you're fine. If no: follow the drawdown scenarios.
2. Open positions: `python -c "import MetaTrader5 as mt5; mt5.initialize(); print([p for p in mt5.positions_get() if p.magic == 20260401]); mt5.shutdown()"` — are there any orphaned positions (SL/TP missing)?
3. Process health: `ps aux | grep run_agent | wc -l` — should show 5 processes (plus the grep itself). If fewer: some crashed. Follow Scenario 1 for each.
4. Trade log: `grep "TRADE_OPEN\|TRADE_CLOSE" logs/agent_*_demo.log | tail -20` — review what happened while you were away.
5. SPRT update: count wins/losses from the last 48 hours, update all instrument-level and portfolio-level SPRT trackers.

**What NOT to do:** Do not panic about what you missed. The system ran autonomously — that's the entire point. Do not compensate by over-monitoring for the next 48 hours.

**Resume criteria:** All 5 processes running. No drawdown breaches. SPRT updated. Resume normal monitoring schedule.

---

# CATEGORY 6: ADMINISTRATIVE

---

## Scenario 36: API Balance Running Low

**Trigger:** Anthropic console shows balance below $30. At ~$2.72/day for 5 instruments, this is ~11 days of runway.

**Severity:** MEDIUM

**Immediate action:** Top up the API balance.

**Full response:**
1. Current burn rate: ~$60/month for live trading (5 instruments). Batch tests are extra.
2. Minimum safe balance: $60 (1 month runway). Ideal: $120 (2 months).
3. Top up at console.anthropic.com → Billing → Add credits.
4. If budget is tight: GBPUSD contributes ~0.8 trades/month. It's the lowest-value instrument. Stopping it saves ~$0.40/day ($12/month). Not worth the complexity unless truly broke.
5. Track monthly spend in a simple spreadsheet. If spend exceeds $80/month: investigate — something is making more API calls than expected.

**What NOT to do:** Do not let the balance hit zero during market hours (see Scenario 7). Do not disable instruments to save money without explicit analysis.

**Resume criteria:** Balance above $60. Set a calendar reminder for the next check.

---

## Scenario 37: FTMO Demo Period Expiring

**Trigger:** FTMO notifies that the free trial or demo period is ending.

**Severity:** MEDIUM

**Immediate action:** Decide: extend demo, switch to funded challenge, or move to another broker's demo.

**Full response:**
1. Check total live trades executed. If <30 total portfolio trades: you don't have enough data. Extend demo or start a new one.
2. If 30+ trades with portfolio WR ≥ 55%: you're ready for the funded challenge. The Monte Carlo supports this.
3. Prerequisites for funded (ALL must be met): (a) portfolio SPRT not at kill boundary, (b) no single instrument killed, (c) max drawdown <3% on demo, (d) no emergency stops triggered, (e) system running ≥4 weeks without manual intervention, (f) WR across all instruments ≥50%.
4. If transitioning to funded: change `risk_percent` to 0.75% (not 1.0%). Set circuit breakers tighter: daily loss halt at 1.5% (not 2%), because FTMO's 5% daily limit leaves less margin.
5. FTMO challenge cost: ~$500. Treat it as a $500 experiment, not a do-or-die bet.

**What NOT to do:** Do not rush to funded before meeting all prerequisites. Do not start the challenge during a loss streak. Do not pay for the challenge if demo data is insufficient.

**Resume criteria:** Prerequisites met. Funded account configured with tighter circuit breakers.

---

## Scenario 38: Time to Transition from Demo to Funded Account

**Trigger:** All funded prerequisites met (Scenario 37, step 3). Decision made to go live with capital.

**Severity:** HIGH

**Immediate action:** Create a pre-flight checklist and execute it systematically.

**Full response:**
1. Pre-flight checklist:
   - [ ] Change `risk_percent` to `0.75` in config
   - [ ] Change daily loss halt from 2% to 1.5% in circuit breaker config
   - [ ] Verify FTMO symbol names match config (XAUUSD may be different on funded vs demo)
   - [ ] Verify `mt5_symbol` mappings for all instruments
   - [ ] Update MAGIC_NUMBER to a new value (distinguish funded trades from demo trades)
   - [ ] Verify API key is on production billing (not trial credits)
   - [ ] Verify spread gates are appropriate for the funded account's broker (spreads may differ)
   - [ ] Run one London KZ on funded with `risk_percent: 0.001` (minimum position) to verify execution path
   - [ ] Confirm no open positions from demo remain
2. First week on funded: monitor every KZ (same as Day 1 protocol from handoff).
3. FTMO rules to hardcode: 5% max daily loss, 10% max total drawdown. Your circuit breakers must be TIGHTER than these.
4. Scale-up plan: 0.75% for first 30 trades → 1.0% after SPRT continues or confirms for 2+ instruments.
5. Document the transition date and starting equity for SPRT tracking.

**What NOT to do:** Do not go from demo to funded at 1.0% risk. Do not skip the minimum-position verification trade. Do not assume demo and funded use identical symbol names or spreads.

**Resume criteria:** First real trade executes with correct lot size, correct SL/TP, correct symbol. Verify lot size manually against the 0.75% risk calculation.

---

## Scenario 39: Monthly Performance Review Process

**Trigger:** Calendar reminder at month end. Or after 15+ new trades in a month.

**Severity:** LOW (but non-negotiable)

**Immediate action:** Block 1 hour. Gather data. Compute metrics.

**Full response:**
1. Compute per-instrument metrics:
   - Win rate (rolling last 10 and cumulative)
   - Expectancy in R
   - Average winner / average loser
   - LONG vs SHORT split
   - KZ performance split (London vs NY vs Tokyo)
2. Update SPRT for every instrument and the portfolio.
3. Update CUSUM tracker: compute S_t for both deterioration and improvement directions.
4. Check 20-period H1 return autocorrelation for gold: if trending toward zero, flag for edge decay monitoring.
5. Review deferred prompt changes log (`knowledge_base/meta/deferred_prompt_changes.log`): any patterns emerging across multiple months?
6. Review operator disagreements log: track your prediction accuracy.
7. Check system cost: API spend, infrastructure, compare to budget.
8. Write a one-page summary: `echo "Month: {month}, Trades: {n}, WR: {x}%, Expectancy: {y}R, SPRT: {status}, Notes: {notes}" >> knowledge_base/meta/monthly_reviews.log`

**What NOT to do:** Do not skip this. Do not change anything based on one month's data. Do not compare to batch performance without noting the sample size.

**Resume criteria:** Review completed and logged. No changes to the system unless an emergency condition was discovered during review.

---

## Scenario 40: Quarterly Walk-Forward Window Boundary Reached

**Trigger:** WF-1 ends June 2026. Time to evaluate and potentially modify the system.

**Severity:** HIGH

**Immediate action:** Block an entire evening. This is the most important review.

**Full response:**
1. Compile ALL data from the walk-forward window: every trade, every SPRT update, every CUSUM value, every deferred prompt change.
2. Per-instrument assessment:
   - Is SPRT in confirm, kill, or continue? If confirm: excellent. If kill: remove the instrument. If continue: keep trading.
   - Is the observed WR within the Wilson 95% CI of the batch WR? If yes: batch performance is validated. If no: the edge may have degraded.
3. Review deferred prompt changes. For each candidate change: estimate expected impact, design a batch test, budget the cost.
4. If making prompt changes: test on data from the walk-forward period (which is now "in-sample" for the new window). NEVER test changes on the upcoming window's data.
5. Begin WF-2 with: updated prompt (if changes made), fresh SPRT tracking from trade 1, updated CUSUM baseline, any new instruments that passed batch testing.
6. If the system is profitable and stable: consider scaling from 0.75% to 1.0% risk on funded.
7. Write a full walk-forward report: what worked, what didn't, what changed, what's deferred to WF-3.

**What NOT to do:** Do not skip the walk-forward review. Do not carry over SPRT counts from the previous window (each window starts fresh). Do not change more than 2 things simultaneously — each change needs isolation for attribution.

**Resume criteria:** WF-2 begins with documented changes, fresh tracking, and updated confidence levels.

---

## Scenario 41: Claude API Model Deprecated or Changed

**Trigger:** API errors mentioning model version, Anthropic announces model deprecation, or you notice different reasoning quality in AI outputs.

**Severity:** CRITICAL

**Immediate action:** Check the model string in `config/agent_config.yaml` — currently `claude-sonnet-4-20250514`. Verify it matches what the API is actually serving.

**Full response:**
1. Run: `python -c "import anthropic; c = anthropic.Anthropic(); print(c.messages.create(model='claude-sonnet-4-20250514', max_tokens=10, messages=[{'role':'user','content':'test'}]).model)"`
2. If model rejected or returns a different model: HALT ALL TRADING IMMEDIATELY.
3. Do NOT switch to a new model without batch testing. Even a minor model update can change WR by 10pp+.
4. Freeze the walk-forward window. All live data collected so far remains valid.
5. Batch test the new model on 30-50 historical dates ($10-15) before resuming.
6. If new model WR within 5pp of old model: resume with new model, reset walk-forward window.
7. If WR drops >5pp: investigate further before deploying.

**What NOT to do:** Don't assume a new model version will perform the same. Don't just update the model string and continue trading. Don't ignore deprecation warnings in API responses.

**Resume criteria:** New model batch-tested, WR within 5pp of original, walk-forward window reset.

---

# APPENDIX A: SPRT Quick Reference Tables

## XAUUSD (H0: 35.7%, H1: 62.0%)

| Trades | Wins to CONFIRM | Wins to KILL | Continue |
|--------|-----------------|--------------|----------|
| 10 | ≥ 8 | ≤ 3 | 4-7 |
| 15 | ≥ 10 | ≤ 5 | 6-9 |
| 20 | ≥ 13 | ≤ 8 | 9-12 |
| 25 | ≥ 15 | ≤ 10 | 11-14 |
| 30 | ≥ 18 | ≤ 13 | 14-17 |

## Portfolio Level (H0: 37.7%, H1: 62.8%)

| Trades | Wins to CONFIRM | Wins to KILL | Continue |
|--------|-----------------|--------------|----------|
| 10 | ≥ 8 | ≤ 3 | 4-7 |
| 15 | ≥ 11 | ≤ 6 | 7-10 |
| 20 | ≥ 13 | ≤ 8 | 9-12 |
| 30 | ≥ 18 | ≤ 13 | 14-17 |
| 50 | ≥ 28 | ≤ 23 | 24-27 |

## GBPJPY (H0: 41.7%, H1: 57.1%) — Widest Continue Range

| Trades | Wins to CONFIRM | Wins to KILL | Continue |
|--------|-----------------|--------------|----------|
| 10 | ≥ 10 | ≤ 2 | 3-9 |
| 20 | ≥ 15 | ≤ 7 | 8-14 |
| 30 | ≥ 20 | ≤ 12 | 13-19 |
| 50 | ≥ 30 | ≤ 22 | 23-29 |

## SPRT Update Formula
After each trade: `S_n += log(p₁/p₀)` if win, `S_n += log((1-p₁)/(1-p₀))` if loss.
CONFIRM if S_n ≥ 2.773. KILL if S_n ≤ -1.556.

---

# APPENDIX B: Emergency Stop Conditions (One Page)

## HALT ALL TRADING IMMEDIATELY IF:
1. Portfolio drawdown exceeds 4%
2. Any single trade loses > 1.5R
3. More than 2 trades in a single kill zone for one instrument
4. Trade placed outside kill zones
5. MT5 shows different position than system logs
6. Total correlation-adjusted risk exceeds 1.5% for JPY group or 2% total portfolio simultaneously. Correlation groups are defined in `config/agent_config.yaml` under `correlation_groups`. The `portfolio_risk.py` module enforces this automatically — if the limit is exceeded despite the module, check for a bug in the risk override chain from portfolio_risk → orchestrator → execution engine.

## HALT ONE INSTRUMENT IF:
1. SPRT crosses kill boundary
2. 5 consecutive losses
3. Spread consistently exceeds spread gate during kill zones

## AFTER ANY HALT:
1. Kill relevant process(es)
2. Secure open positions (verify SL exists)
3. Investigate root cause
4. Do not resume until cause identified and fixed
5. Document everything

---

# APPENDIX C: Daily Monitoring Checklist

```
□ All 5 processes running? (ps aux | grep run_agent)
□ MT5 connected? (terminal shows connected)
□ AutoTrading enabled? (toolbar button green)
□ Any open positions? (note symbols, SL/TP, current P&L)
□ Account equity > $96,000? (4% drawdown threshold)
□ API balance > $30?
□ Any ERROR lines in logs? (grep -i ERROR logs/agent_*_demo.log | tail -5)
□ Candle evaluations happening? (grep EVALUATING logs/agent_XAUUSD_demo.log | tail -3)
□ Trades today? (grep TRADE_OPEN logs/agent_*_demo.log | grep $(date +%Y-%m-%d))
□ SPRT updated for any new trades?
```

---

# APPENDIX D: Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | April 5, 2026 | Initial 40-scenario playbook |
| 2.0 | April 5, 2026 | Red Team review: replaced Scenario 12 (correlation sizing now automated via portfolio_risk.py), added Scenario 41 (API model deprecation), added 13:00 UTC skip note to Scenario 10, updated Appendix B emergency condition #6 (JPY group 1.5% limit + module traceability) |
| 3.0 | April 26, 2026 | 7-instrument fleet (added XAGUSD live + NAS100 live-OBSERVE); ADR-006 SL geometry tolerance gate; B.1 cross_instrument_context |corr|≥0.4 gate; C.3 class-aware SPRT halt thresholds (manual mode Monday); heartbeat per-symbol architecture; tick capture daemon (shadow-only Monday); 10 new scenarios added (#42-#51) |

---

## v3 Additions for 7-instrument fleet + ADR-006/B.1/C.3

The following scenarios extend the 41-scenario v2 playbook for the Monday 2026-04-27 FTMO paid challenge launch. Same severity definitions and key paths apply (XAGUSD logs at `logs/agent_XAGUSD_demo.log`; NAS100 at `logs/agent_NAS100_demo.log`). Tick-capture parquet files land under `data/ticks/{SYMBOL}/`. Heartbeat per-symbol files live at `pipeline_state/heartbeat_{SYMBOL}.json`.

---

### Scenario 42: XAGUSD Trade Fills at 0.5% — First 5 Trades

**Trigger:** First 5 XAGUSD fills post-Monday launch.

**Severity:** MEDIUM (observation phase)

**Expected:** WR ≥40% across the 5 fills (n is too small for class-aware SPRT to fire; XAGUSD shares the metals-class threshold with XAUUSD via C.3 but only counts toward the joint LONG-WR sample once volume accumulates).

**Action:**
1. Log each fill's outcome to `knowledge_base/trade_records/XAGUSD/` and confirm magic number 20260401.
2. After trade #5 review the realized R distribution. Compute WR + average R.
3. Continue without intervention unless catastrophic: 3 consecutive losses each >2R against XAGUSD constitutes operator halt — kill the XAGUSD orchestrator and convene CEO.

**Decision authority:** Operator continues observation autonomously; only catastrophic 3×>2R chain triggers an operator halt + CEO notification.

**Rationale:** XAGUSD was added live at 0.5% on 2026-04-25 per Tier 2 verdict (commit `d2a31d0`). First 5 fills are a small-n sanity check, not a statistical confirmation. Class-aware SPRT (Scenario 46) starts firing at n=10 within the metals class.

---

### Scenario 43: NAS100 3-Day Live-Observe Verdict (2026-04-30 EOD)

**Trigger:** 3 calendar days of NAS100 0.25% live operation (Monday 2026-04-27 → Wednesday 2026-04-30 EOD).

**Severity:** HIGH (decision gate)

**Expected:** Operator + CEO make one of three decisions: promote NAS100 to 0.5% live, extend observe window for another 3-7 days, or revert to backtest-only / disable.

**Action:**
1. Pull NAS100 fills from `knowledge_base/trade_records/NAS100/` for the 3-day window.
2. Compute realized R per trade + cumulative R, WR, and any halts.
3. Compare against the 3-day observation pre-registered thresholds: ≥3 fills, cumulative R > 0R, WR ≥45%, no class-SPRT halts triggered.
4. If all 4 thresholds met → promote to 0.5% via `config/profiles/ftmo.yaml` `risk_per_trade_pct` override + commit + restart.
5. If 1-2 thresholds missed → CEO council on extend vs revert.
6. If 3+ thresholds missed or fewer than 3 fills materialized → revert to backtest-only (set `trading_enabled: false` for NAS100 via per-symbol override).

**Decision authority:** CEO. Operator prepares the data pack (fills + R distribution + halts log) for council.

**Rationale:** NAS100 added live-OBSERVE at 0.25% on 2026-04-25 per Tier 2 verdict (commit `d2a31d0`). 3-day window is the pre-registered evaluation period — past Wednesday EOD continued operation requires explicit decision.

---

### Scenario 44: ADR-006 SL Geometry Tolerance Gate Post-Launch Monitoring

**Trigger:** First-week of live trading post-launch (2026-04-27 through 2026-05-04).

**Severity:** MEDIUM (observability)

**Expected:** Live `sl_beyond_ob` rejection rate <20% per ADR-006 audit chairman pre-registered tolerance. Rate >30% indicates a regression in the tolerance-tier rollback knob.

**Action:**
1. Daily mine `shadow_logs/sl_beyond_ob_decisions.jsonl` (one line per AI candidate evaluated against the gate).
2. Compute daily rejection rate: `count(rejected) / count(total_evaluations)`.
3. Cumulative weekly view: rolling 7-day rejection rate.
4. Alert CEO if daily rate >30% on any single day OR weekly cumulative >20%.
5. If alert fires: pull the rejected-candidate sample, classify by instrument + framework + tolerance-tier, brief CEO with the breakdown.

**Decision authority:** Operator monitors autonomously; CEO involvement only on threshold breach. Threshold breach does NOT auto-halt — it's a flag for ADR-006 follow-up review.

**Rationale:** ADR-006 SL geometry tolerance gate shipped with rollback knob (`gate1.sl_geometry_tolerance_tier`) — the audit chairman pre-registered <20% rejection rate as the "no regression" threshold. Sustained >30% indicates the tolerance tier needs adjustment.

---

### Scenario 45: B.1 |corr|≥0.4 Gate Effect on Indices

**Trigger:** First-week direction-emission balance (2026-04-27 through 2026-05-04).

**Severity:** MEDIUM (observability)

**Expected:** Indices (US30, NAS100) show >5% SHORT emission share post-B.1 (vs ~0% under v1, where XAU-D1 cross-instrument context anchor was unconditionally injected and biased all CANDIDATEs LONG).

**Action:**
1. Daily mine `shadow_logs/direction_emission_xau_audit.jsonl` (logs every CANDIDATE's direction + whether the cross-instrument context paragraph was injected per the B.1 |corr|≥0.4 gate).
2. Compute per-instrument SHORT emission share: `count(direction=SHORT) / count(direction in {LONG,SHORT})`.
3. Track US30 + NAS100 SHORT share through trade #20.
4. If SHORT share <2% by trade #20 on either index → escalate to CEO. Likely the |corr|≥0.4 gate is too tight for indices (which have lower XAU correlation than the FX pairs the gate was tuned for) and needs adjustment.

**Decision authority:** Operator monitors; CEO if SHORT share drops below the 2% escalation threshold.

**Rationale:** B.1 (commit `df70694`) gates the cross-instrument XAU-D1 context paragraph by `|corr|≥0.4`. Pre-fix, ALL CANDIDATEs received the XAU-anchor block and indices showed 0% SHORT bias. Post-fix, indices should decouple. This scenario validates that decoupling.

---

### Scenario 46: C.3 SPRT Class-Halt — Metals (XAUUSD + XAGUSD) WR <55% in First 20 LONG Trades

**Trigger:** First 20 LONG trades on metals (XAUUSD + XAGUSD combined) post-Monday launch.

**Severity:** CRITICAL on HALT_TRIGGERED

**Action:**
1. After each metals LONG trade #10 and #20, run:
   ```bash
   python -m src.safety.sprt_class_halt_check XAUUSD <LONG_n> <LONG_wins>
   ```
   (XAUUSD is the canonical metals-class symbol; XAGUSD shares the threshold.)
2. Exit codes:
   - 0 = OK / INSUFFICIENT_DATA / CLASS_EXCLUDED → no action
   - 1 = EARLY_WARNING (WR <50% Wilson 95% LB) → monitor closely + flag CEO
   - 2 = HALT_TRIGGERED (WR <55% Wilson 95% LB) → halt metals class, send Telegram alert via `format_telegram_alert(check_result)` to @gold_trader_os_bot, convene CEO council
3. To halt the metals class manually: kill the XAUUSD + XAGUSD orchestrator processes (via Scenario 1 procedure per symbol); leave US30/USDJPY/GBPJPY/GBPUSD/NAS100 running.

**Decision authority:** Auto-halt + CEO council. Operator does NOT decide whether the halt was correct; only CEO can re-enable metals trading after council.

**Rationale:** C.3 class-aware LONG-WR-watch SPRT halt thresholds (commit `048b2e7`). Metals threshold is 55% Wilson 95% LB (tighter than indices/JPY because metals carry the bulk of historical volume + WR). Manual mode Monday → automation flips post-Monday once orchestrator callback is wired.

---

### Scenario 47: C.3 SPRT Class-Halt — Indices (US30 + NAS100) WR <40% in First 20 LONG Trades

**Trigger:** First 20 LONG trades on indices (US30 + NAS100 combined).

**Severity:** CRITICAL on HALT_TRIGGERED

**Action:** Same workflow as Scenario 46 but threshold is 40% (Wilson 95% LB).
```bash
python -m src.safety.sprt_class_halt_check US30_cash <LONG_n> <LONG_wins>
```
HALT_TRIGGERED → halt US30 + NAS100 orchestrators, Telegram alert, CEO council.

**Decision authority:** Auto-halt + CEO council.

**Rationale:** Indices class threshold is loosened to 40% (vs metals 55%) because the historical sample is thinner + indices carry higher volatility per R unit. Same module + alert flow as Scenario 46.

---

### Scenario 48: C.3 SPRT Class-Halt — JPY Pairs (USDJPY + GBPJPY) WR <45% in First 20 LONG Trades

**Trigger:** First 20 LONG trades on JPY pairs (USDJPY + GBPJPY combined).

**Severity:** CRITICAL on HALT_TRIGGERED

**Action:** Same workflow as Scenario 46 but threshold is 45% (Wilson 95% LB).
```bash
python -m src.safety.sprt_class_halt_check USDJPY <LONG_n> <LONG_wins>
```
HALT_TRIGGERED → halt USDJPY + GBPJPY orchestrators, Telegram alert, CEO council.

**Decision authority:** Auto-halt + CEO council.

**Rationale:** JPY-pairs threshold is 45% — between metals (55%) and indices (40%). Reflects historical USDJPY 75.8% WR + GBPJPY 57.1% WR sample average + safety margin.

> **NOTE:** GBPUSD (the only `tight_fx` class member) is EXCLUDED from C.3 SPRT because n=5 historical sample is too thin. GBPUSD remains observer-only as of session 40 close — no fills, no halt eligibility.

---

### Scenario 49: Heartbeat Per-Symbol Architecture — Detect Single-Symbol Stall

**Trigger:** `pipeline_state/heartbeat_{SYMBOL}.json` shows `oldest_age_seconds > 300` during trading hours for any symbol.

**Severity:** HIGH (per-symbol stall, fleet-wide otherwise OK)

**Expected:** The Task Scheduler watchdog tick (every ~15 min) auto-detects the stale lock, kills the dead orchestrator if any, and respawns it via `scripts/watchdog.ps1`. Recovery should complete within 15 min of the stall.

**Action:**
1. Verify the stall via `cat pipeline_state/heartbeat_{SYMBOL}.json` — confirm `last_heartbeat_utc` is >5 min stale.
2. Check the orchestrator log: `tail -100 logs/agent_{SYMBOL}_demo.log` — find the traceback or hang signature.
3. Wait ≤15 min for the next watchdog tick to auto-respawn.
4. If watchdog does NOT auto-restart within 15 min: manual restart per Scenario 1 procedure (delete stale lock + relaunch).
5. If multiple symbols stall simultaneously → escalate to Scenario 2 (all-process crash) — likely shared dependency failure (MT5 disconnect, machine sleep).

**Decision authority:** Operator + watchdog auto-recovery. CEO involvement only if fleet-wide degradation (≥3 symbols stalled simultaneously).

**Rationale:** Per-symbol heartbeat architecture (shipped 2026-04-26) replaces the shared single-heartbeat file — a single-symbol stall no longer triggers fleet-wide flatten. Hypothesis F root cause of 2026-04-24/25 staleness incident also requires Task Scheduler "Wake the computer to run this task" enabled (see CLAUDE.md unresolved item #1).

---

### Scenario 50: Tick Capture Daemon Health — First Parquet on Monday

**Trigger:** 30 min after Monday market open (07:45 local time / Monday 2026-04-27 first KZ entry).

**Severity:** LOW (shadow-only, does not block trading)

**Expected:** 7 parquet files appearing in `data/ticks/{SYMBOL}/2026-04-27.parquet` — one per traded symbol. Each daemon (`tick_capture_{SYMBOL}.log` per symbol) emits a startup banner + tick count summary.

**Action:**
1. After 07:45 local: `ls data/ticks/*/2026-04-27.parquet` — should list 7 files.
2. For any symbol missing a parquet file: `tail -50 logs/tick_capture_{SYMBOL}.log` — find the daemon startup error.
3. If a daemon failed to start: the watchdog will respawn it on the next tick (≤15 min). Verify recovery by re-running the `ls` check after the next watchdog tick.
4. If a daemon repeatedly fails (3 consecutive watchdog ticks): escalate to operator manual restart of `python -m src.components.tick_capture --symbol {SYMBOL} --mt5-symbol {BROKER_ALIAS}`.

**Decision authority:** Operator monitors. Tick features are shadow-only Monday (D.1 deferred — `tick_features.py` runs additively on M15 close but the merged features are observation-only, not gating). Missing parquet does NOT block trading; it only delays the tick-feature shadow log.

**Rationale:** Tick capture daemon shipped 2026-04-25 (commit `f1654f3`, vision Layer 1). Tick-features merge into `raw_data` is fail-open — `tick_features=None` on any failure path. Daemon health is observability, not safety.

---

### Scenario 51: FTMO-vs-redacted_account Profile Mismatch Detection

**Trigger:** Trade fills at unexpected risk size (e.g., 1.0% on XAUUSD where 0.5% expected, or 2.0% on FX where 1.0% expected).

**Severity:** CRITICAL (capital at risk — sizing is the most consequential profile difference)

**Expected:** Under FTMO paid challenge profile, all fills must size as: XAUUSD 0.5%, XAGUSD 0.5%, NAS100 0.25% (live-OBSERVE), all FX (USDJPY, GBPJPY, GBPUSD, US30) 1.0%.

**Action:**
1. **HALT FLEET IMMEDIATELY** if a mismatch is detected and persists past one trade. Use the manual stop sequence from Scenario 1 (per-symbol kill via PID lock files).
2. Verify environment variables in a fresh shell:
   ```bash
   echo $env:GTOS_PROFILE   # should be "ftmo"
   echo $env:GTOS_MODE      # should be "live"
   ```
3. Verify `config/profiles/ftmo.yaml` matches expected risk overrides (XAUUSD 0.5%, XAGUSD 0.5%, NAS100 0.25%, FX 1.0%). Do NOT edit live; verify against `git log` HEAD.
4. Verify `config/profiles/ftmo.yaml` MT5 credentials (login + password) match the FTMO paid challenge account.
5. Restart the fleet via `start_all.bat` after env vars confirmed in a fresh shell (env var changes do NOT propagate to running processes — only NEW shell sessions pick them up).
6. Smoke-test with `python scripts/fn_smoke_trade.py` before re-enabling full fleet trading.
7. Document the incident: cause (env var mismatch, profile YAML drift, etc.), recovery time, any fills that occurred under wrong sizing.

**Decision authority:** Operator halts immediately on first detected mismatch. CEO involvement post-recovery for incident review + any drawdown-impact assessment.

**Rationale:** FTMO paid challenge launches Monday 2026-04-27 with strict per-instrument sizing per `config/profiles/ftmo.yaml`. A profile mismatch (e.g., still on `redacted_account` demo profile or a YAML drift) means trading at wrong risk per trade — directly violates FTMO challenge rules + risks immediate disqualification on outsized loss. Sizing mismatch is the single highest-severity Monday-morning failure mode.

---

*Operator Decision Playbook v3.0 — 2026-04-26
Updates from v2.0 (Apr 5):
- 7-instrument fleet (added XAGUSD live, NAS100 live-OBSERVE)
- ADR-006 SL geometry tolerance gate
- B.1 cross_instrument_context |corr|≥0.4 gate
- C.3 class-aware SPRT halt thresholds (manual mode Monday)
- Heartbeat per-symbol architecture
- Tick capture daemon (shadow-only Monday)
- 10 new scenarios added (#42-#51)*

---

*End of Operator's Decision Playbook v3.0 — 51 scenarios. Last updated April 26, 2026.*
