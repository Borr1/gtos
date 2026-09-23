# Live Monitoring Handoff - 2026-05-01 NY Session

**Session date:** 2026-05-01, monitored through NY close at 17:00 UTC  
**Handoff written:** 2026-05-02 KL time  
**Latest monitoring fix commit:** `56d5553 fix(live): repair edge monitor state recovery`  
**Purpose:** preserve operational context for the next live-monitoring KZ session.

## Required Preflight For Next Monitoring Session

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read this handoff.
4. Read `.context/00_core/quick_reference_card.md`.
5. Run the live checks below before making any claim about health:

```powershell
python scripts/_live_monitor_iter.py manual
git status --short
```

MT5 + internal pending intent check:

```powershell
@'
import pickle, pathlib, MetaTrader5 as mt5
for p in sorted(pathlib.Path('knowledge_base/meta').glob('pending_intent_*.pkl')):
    v=pickle.loads(p.read_bytes())
    print('intent', p.name, v.direction, v.limit_price, v.stop_loss,
          getattr(v,'take_profit_1',None), 'risk', v.risk_pct,
          'balance_attr', getattr(v,'account_balance',None),
          'elapsed', v.candles_elapsed, v.trade_id)
if not mt5.initialize():
    print('mt5_init_failed', mt5.last_error())
    raise SystemExit(1)
try:
    ps=mt5.positions_get(); os=mt5.orders_get(); ai=mt5.account_info()
    print('positions', 0 if ps is None else len(ps))
    if ps:
        for p in ps: print('POSITION', p.ticket,p.symbol,p.type,p.volume,p.price_open,p.sl,p.tp,p.profit,p.magic,p.comment)
    print('orders', 0 if os is None else len(os))
    if os:
        for o in os: print('ORDER', o.ticket,o.symbol,o.type,o.volume_initial,o.volume_current,o.price_open,o.sl,o.tp,o.magic,o.comment)
    print('account', None if ai is None else (ai.balance, ai.equity, ai.margin, ai.margin_free, ai.profit))
finally:
    mt5.shutdown()
'@ | python -
```

Duplicate process check:

```powershell
@'
import psutil, collections, re
counts=collections.Counter(); rows=[]
for p in psutil.process_iter(['pid','name','cmdline']):
    try:
        name=(p.info.get('name') or '').lower(); cmd=' '.join(p.info.get('cmdline') or [])
    except Exception:
        continue
    if name!='python.exe': continue
    key=None
    if 'run_agent.py --symbol' in cmd:
        m=re.search(r'--symbol\s+(\S+)',cmd); key=f'orchestrator:{m.group(1) if m else "?"}'
    elif 'src.components.tick_capture' in cmd or 'tick_capture' in cmd:
        m=re.search(r'--symbol\s+(\S+)',cmd); key=f'tick:{m.group(1) if m else "?"}'
    elif 'heartbeat_monitor' in cmd: key='heartbeat'
    elif 'displacement_logger' in cmd: key='displacement'
    elif 'notification_queue' in cmd: key='notification'
    if key: counts[key]+=1; rows.append((key,p.info['pid']))
for k,pid in sorted(rows): print(k,pid)
print('duplicates', [k for k,v in counts.items() if v != 1])
'@ | python -
```

## End State At NY Close

At 17:00 UTC on 2026-05-01:

- MT5 positions: `0`
- MT5 broker-native orders: `0`
- Account balance/equity: `$101,223.36`
- Duplicate live processes: none
- XAGUSD, US30_cash, USDJPY, GBPJPY, GBPUSD shut down cleanly after their KZ windows.
- XAUUSD and NAS100 remained alive after KZ because they had internal pending intents to manage. This was considered acceptable by the CEO.

Internal pending intents observed near close:

- `pending_intent_XAUUSD.pkl`: SHORT, limit `4668.45`, SL `4681.93`, TP `4648.23`, risk `1.0`, balance persisted as `101223.36`, trade id `lim_2026-05-01_1545`.
- `pending_intent_NAS100.pkl`: LONG, limit `27300.0`, SL `27196.3`, TP `27455.5`, risk `0.125`, old pickle with `balance_attr=0.0`, trade id `lim_2026-05-01_0815`. The fallback fix below protects old pickles if triggered.

## What Happened During The Session

### XAGUSD Outside-KZ Limit Miss

The system had an internal short limit intent:

- trade id `lim_2026-05-01_0830`
- SHORT limit `74.088`
- SL `74.688`
- TP `73.188`

Issue:

- The old outside-KZ pending checker marked a forming candle as checked before the final high touched the limit.
- MT5 candle timestamps also needed broker-offset correction after restart.
- After the fix, the checker saw the relevant closed candle, but price had already moved beyond SL, so it aborted instead of entering.

Important interpretation:

- Later XAGUSD moved down, but the valid system short would have been stopped out first based on the SL path. This was not a missed clean winner; it was a bug that avoided an already-invalid fill by the time the fix ran.

Documented in:

- `knowledge_base/postmortems/2026-05-01_xagusd_outside_kz_limit_miss.md`
- commit `412d378 fix(live): harden limit monitoring from monitoring session`

### XAUUSD Restarted Limit Sizing Bug

London pending intent:

- SHORT XAUUSD limit `4617.78`
- SL `4636.02`
- original AI TP1 `4590.42`
- J46/J49 broker TP override `4567.77`

Observed broker result:

- Open deal true UTC `14:00:05`, order `235112399`, XAUUSD SELL, `0.01` lot, price around `4626.25`, magic `20260401`.
- Close deal true UTC `14:00:39`, order `235113710`, price `4636.10`, SL comment `[sl 4636.02]`.
- Approx net result: about `-$9.92`.

Root cause:

- Restart restored the pending intent but did not restore `_pending_account_balance`.
- Position sizing saw balance `0`, calculated zero volume, then clamped to min lot `0.01`.
- This is why the loss was only about $10. Without restart, intended risk sizing would likely have been larger.

Fixed in:

- `src/components/execution.py`: `PendingLimitIntent.account_balance`, restore `_pending_account_balance`, fallback to current MT5 account balance when old pickles have no balance.
- `src/mt5/mt5_real.py`: broker-offset-aware `get_history_deals()`.
- `src/components/orchestrator.py`: ASCII SPRT log text.

Documented in:

- `knowledge_base/postmortems/2026-05-01_xauusd_restarted_limit_minlot_sl.md`
- commit `ef70ed9 fix(live): repair restarted limit sizing`

### XAUUSD Late NY Pending Intent

At 15:45 UTC the system placed a new internal XAUUSD short limit:

- SHORT limit `4668.45`
- SL `4681.93`
- TP `4648.23`
- risk `1.0%`
- account balance persisted correctly as `101223.36`

This was not a broker-native order. MT5 remained flat. The intent was still active after the 17:00 UTC session boundary; CEO accepted that pending-intent behavior is fine.

### NAS100 Pending Intent

NAS100 had an internal long limit from London:

- LONG limit `27300.0`
- SL `27196.3`
- TP `27455.5`
- risk `0.125`
- old pickle with `balance_attr=0.0`

It never filled during the monitored NY window. The old balance field is still visible on that pickle, but `ef70ed9` protects execution by falling back to current MT5 balance if needed.

### NDX / Market Move

NDX/NAS100 moved sharply around the NY period, but no broker trade was placed. The NAS intent remained far below market for much of the monitored window.

### Round-Number Concern

CEO flagged entries around obvious levels like `27300`, `25050`.

Operational decision:

- Do not change live trading logic yet.
- Treat this as a research/shadow hypothesis.

Documented in:

- `knowledge_base/monitoring/2026-05-01_round_number_entry_observation.md`
- commit `ef70ed9`

## Fixes Shipped From This Monitoring Session

### `412d378 fix(live): harden limit monitoring from monitoring session`

Primary fixes:

- `scripts/watchdog.ps1`: validates PID command lines so duplicate/invalid live processes are less likely to be trusted.
- `src/components/orchestrator.py`: outside-KZ limit checker uses closed candles only.
- `src/mt5/mt5_real.py`: broker offset warmup before candle conversion.
- `tests/test_integration_live.py`: regression coverage.
- `knowledge_base/postmortems/2026-05-01_xagusd_outside_kz_limit_miss.md`: incident record.

### `ef70ed9 fix(live): repair restarted limit sizing`

Primary fixes:

- Persist/restore pending-intent account balance.
- Fallback to current MT5 account balance for old-format intents.
- Broker-offset-aware historical deal queries.
- ASCII SPRT logging.
- Tests: `tests/test_limit_order_flow.py`, `tests/test_mt5.py`.
- Postmortem: `knowledge_base/postmortems/2026-05-01_xauusd_restarted_limit_minlot_sl.md`.
- Observation: `knowledge_base/monitoring/2026-05-01_round_number_entry_observation.md`.

Focused verification passed:

```powershell
python -m pytest tests/test_limit_order_flow.py tests/test_mt5.py -q --basetemp C:\tmp\gtos_pytest_xau_incident_full -p no:cacheprovider
```

Result: `34 passed`.

### `2d7bf6e fix(monitoring): suppress ended-session false criticals`

Problem:

- `scripts/_live_monitor_iter.py` raised false criticals when FX/Jpy orchestrators cleanly deleted their heartbeat files after their KZ ended.

Fix:

- Missing heartbeat is critical only while the symbol is in active KZ.
- Expected alive process count uses active KZ symbols only.

Verification:

- Before fix at 15:30 UTC: `crit=4 pids=4 open_pos=0`.
- After fix at same checkpoint: `crit=0 anom=0 pids=4 open_pos=0`.

### `56d5553 fix(live): repair edge monitor state recovery`

Problem:

- `EdgeMonitor update failed (non-blocking): operands could not be broadcast together with shapes (43,) (46,)`.
- Root cause was corrupt/mismatched persisted BOCPD vectors in `knowledge_base/monitoring/edge_monitor_state.json`.

Fix:

- `EdgeMonitor.load_state()` detects inconsistent BOCPD vector lengths and rebuilds BOCPD from saved `trade_history`.
- Keeps SR/CUSUM monitor state intact.

Also changed:

- `guard_candidate_null_params()` now demotes null `CANDIDATE.trade_parameters` to `NO_TRADE` using allowed reason `ai_output_malformed`, not custom `null_trade_parameters`.
- Log severity changed from error to warning because this path is handled and non-trading.

Verification:

```powershell
python -m py_compile src\components\edge_monitor.py src\components\primary_analyzer.py
python -m pytest tests/test_primary_analyzer.py tests/test_edge_monitor.py tests/test_bugfixes_0.py::TestNullTradeParamsGuard -q --basetemp C:\tmp\gtos_pytest_remaining_fixes_20260502b -p no:cacheprovider
```

Result: `46 passed`.

Live-state reproduction:

- Before fix, loading current `edge_monitor_state.json` then updating crashed.
- After fix, it loads as `n=42`, repairs BOCPD to consistent vector lengths, and next update returns `n=43`.

## Logs And Files To Inspect Next Session

Primary live logs:

- `logs/xauusd.log`
- `logs/xagusd.log`
- `logs/nas100.log`
- `logs/us30.log`
- `logs/usdjpy.log`
- `logs/gbpjpy.log`
- `logs/gbpusd.log`

Runtime state:

- `pipeline_state/heartbeat_{SYMBOL}.json`
- `pipeline_state/.orch_shutdown_{SYMBOL}.json`
- `knowledge_base/meta/pending_intent_*.pkl`
- `knowledge_base/sessions/2026-05-01_live_session.json`
- `knowledge_base/live_sessions/{SYMBOL}/2026-05-01_*_summary.json`

Trade records from the incident day:

- `knowledge_base/trade_records/XAUUSD/2026-05-01_london_0815.json`
- `knowledge_base/trade_records/XAUUSD/2026-05-01_ny_1545.json`
- `knowledge_base/trade_records/XAGUSD/2026-05-01_london_0830.json`
- `knowledge_base/trade_records/NAS100/2026-05-01_london_0815.json`

Postmortems and monitoring notes:

- `knowledge_base/postmortems/2026-05-01_xagusd_outside_kz_limit_miss.md`
- `knowledge_base/postmortems/2026-05-01_xauusd_restarted_limit_minlot_sl.md`
- `knowledge_base/monitoring/2026-05-01_round_number_entry_observation.md`

Shadow logs that mattered today:

- `shadow_logs/live_monitor.jsonl` - main monitoring loop output.
- `shadow_logs/live_monitor_alerts.jsonl` - includes the pre-fix false criticals at 15:30 UTC.
- `shadow_logs/slippage.jsonl` - broker execution/slippage records.
- `shadow_logs/daily_pnl.json` and `shadow_logs/daily_pnl_history.jsonl` - daily PnL state.
- `shadow_logs/j46_j49_shadow_outcomes.jsonl` - outcome shadow records; watch for backup/runtime churn.
- `shadow_logs/touch_count_gate_decisions.jsonl` - touch-count pass/reject rows.
- `shadow_logs/candidate_features_log.jsonl` - candidate feature stream.
- `shadow_logs/proximity_shadow_log.jsonl` - proximity stream.
- `shadow_logs/regime_classifications.jsonl` - regime stream.
- `shadow_logs/structure_detector_divergences.jsonl` - structure divergence stream.
- `shadow_logs/malformed_responses.jsonl` - raw malformed AI responses. Note: null `trade_parameters` CANDIDATE is now handled as `ai_output_malformed`; it may not always appear here unless parse failed.

Fixed vs not fixed:

- Fixed: false live monitor criticals for clean post-KZ shutdowns.
- Fixed: EdgeMonitor BOCPD vector corruption recovery.
- Fixed: restarted pending-limit sizing fallback.
- Fixed: outside-KZ closed-candle pending-limit checks.
- Fixed: broker-offset-aware deal history lookups.
- Still observation-only: round-number entry risk.
- Still expected noise: occasional AI null/malformed candidates get demoted safely.
- Still expected: pending internal intents can keep orchestrators alive after KZ; CEO said this is fine.

## Dirty Worktree Warning For Next Session

At handoff time there were uncommitted runtime/generated or other-session files. Do not assume they are monitoring edits:

- `.context/LIVE_STATE.md`
- `pipeline_state/m5_refinement.json`
- `shadow_logs/daily_pnl.json`
- `src/components/tick_capture.py` (likely another session; do not overwrite blindly)
- `pipeline_state/.orch_shutdown_*.json`
- several `shadow_logs/*.jsonl` and `.bak` runtime files

Before committing anything, stage only the files you intentionally changed.

## Next KZ Monitoring Checklist

1. Verify current MT5 positions/orders are zero or match system records.
2. Verify `pending_intent_*.pkl` files and understand whether any old-format `balance_attr=0.0` intents remain.
3. Verify one orchestrator per active symbol, one tick daemon per symbol, and one of each sidecar.
4. Verify tick freshness in `data/ticks/{SYMBOL}/.state.json`; session 47's tick-capture fix should remain healthy.
5. Run `python scripts/_live_monitor_iter.py manual` at each M15 candle close.
6. Tail the active logs after every candle:
   - active symbol logs under `logs/`
   - `shadow_logs/live_monitor.jsonl`
   - `shadow_logs/live_monitor_alerts.jsonl`
7. If a candidate appears, distinguish:
   - AI `CANDIDATE`
   - L2 verified candidate
   - internal pending intent
   - broker-native order
   - actual MT5 position
8. If a trade closes, verify broker deal history and trade record exit reconciliation before trusting fallback bid-based records.
9. If a monitor reports criticals at a KZ boundary, confirm whether the symbol shut down gracefully before treating it as failure.
10. Leave a new file in this folder at the end of the monitoring session.

starter message 
You are starting a fresh GTOS live-monitoring session for the next kill zone.

    Preflight first:
    1. Run `python scripts/generate_live_state.py`
    2. Read `.context/LIVE_STATE.md`
    3. Read `.context/07_live_monitoring_handoffs/README.md`
    4. Read the newest file in `.context/07_live_monitoring_handoffs/`
    5. Read `.context/00_core/quick_reference_card.md`

    Your job is live monitoring only:
    - Understand the current project/live state and the previous live-monitoring handoff.
    - Do not change trading logic unless I explicitly approve.
    - Do not delete or overwrite runtime logs, shadow logs, cache files, or files from other active sessions.
    - If the worktree is dirty, assume unrelated changes may belong to another session.
    - Stage/commit only files you intentionally create or edit.

    Before the next KZ starts:
    - Check current KL/UTC time and identify the next active KZ from the quick reference card.
    - Verify MT5 positions/orders.
    - Verify internal pending intents under `knowledge_base/meta/pending_intent_*.pkl`.
    - Verify live orchestrator/tick daemon/sidecar processes and duplicates.
    - Verify tick freshness from `data/ticks/{SYMBOL}/.state.json`.
    - Tail relevant logs and inspect recent `shadow_logs/live_monitor.jsonl` / `live_monitor_alerts.jsonl`.
    - Then sleep/stay idle until the next KZ monitoring time. Do not busy-work or make changes while waiting.

    During KZ:
    - Monitor every M15 candle close, with a short grace period after each close.
    - Run `python scripts/_live_monitor_iter.py manual` each candle.
    - Check MT5 positions/orders and pending intents each candle.
    - Check duplicate processes each candle or whenever something restarts.
    - Tail active symbol logs after each candle.
    - Distinguish clearly between:
      - AI CANDIDATE
      - L2 verified candidate
      - internal pending intent
      - broker-native order
      - actual MT5 position
    - If a trade opens/closes, verify against broker deal history and trade records before making conclusions.
    - If monitor reports a critical at a KZ boundary, verify whether the symbol shut down gracefully before treating it

    Context from last live-monitoring session:
    - Read `.context/07_live_monitoring_handoffs/2026-05-01_NY_LIVE_MONITORING_HANDOFF.md` carefully.
      - `ef70ed9 fix(live): repair restarted limit sizing`
      - `2d7bf6e fix(monitoring): suppress ended-session false criticals`
      - `56d5553 fix(live): repair edge monitor state recovery`
      - `8fba034 docs(monitoring): add live session handoff`
    - Pending internal intents after last session were acceptable; do not treat them as broker orders.
    - Round-number entries are observation-only for now.
    - EdgeMonitor BOCPD state recovery is fixed; if it reappears, investigate `knowledge_base/monitoring/
    edge_monitor_state.json`.

    At the end of the monitored session:
    - Write a new handoff file under `.context/07_live_monitoring_handoffs/`.
    - Include what happened, exact state, any incidents, logs to inspect, fixes made, tests run, and remaining watch
    items.
    - Commit only your handoff and any intentional fixes.