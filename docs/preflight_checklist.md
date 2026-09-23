# Pre-Flight Checklist — Funded Account Launch

## Before First Session

### MT5 Setup
- [ ] MT5 connected and logged in to funded account
- [ ] Verify symbol name in Market Watch — is it "XAUUSD", "GOLD", "XAUUSDm", or other? Update `config/agent_config.yaml` → `market.symbol` and all hardcoded references in `src/components/execution.py` if different
- [ ] Verify lot sizing: place a 0.01 lot test trade manually, check margin required matches expectations ($100/point for standard lots)
- [ ] MAGIC_NUMBER in `src/mt5/mt5_interface.py` set to unique value (currently 20260401)
- [ ] No other EAs running on the same symbol with the same MAGIC_NUMBER

### API & Config
- [ ] `ANTHROPIC_API_KEY` environment variable set (check with `echo $ANTHROPIC_API_KEY | head -c 10`)
- [ ] `config/agent_config.yaml` → `ai.billing_mode: "api"`
- [ ] `config/agent_config.yaml` → `ai.primary_model: "claude-opus-4-20250514"` (or sonnet for cost savings)
- [ ] `config/agent_config.yaml` → `deployment.phase: 3` (live_micro)
- [ ] `config/agent_config.yaml` → `risk.risk_per_trade_pct: 1.0` (or lower for initial period)
- [ ] `config/agent_config.yaml` → `model_a.enabled_frameworks: ["ob_retest"]`
- [ ] Budget cap set: `budget.monthly_cap_usd` appropriate for expected API usage

### Prop Firm Rules
- [ ] Daily drawdown limit in config (2%) is MORE conservative than prop firm's limit — confirm prop firm limit
- [ ] Max trades per day (2) is within prop firm rules
- [ ] Trading hours (London 07:00-09:30, NY 13:00-15:30 UTC) are within prop firm allowed hours
- [ ] Weekend holding: our system closes all positions same day — no weekend risk

### System
- [ ] Clock synchronized to UTC (`date -u` on Mac/Linux)
- [ ] Log directory exists and is writable: `knowledge_base/` and subdirectories
- [ ] PID lock file cleaned: `rm -f knowledge_base/meta/.orchestrator.lock`
- [ ] No stale execution checkpoint: `rm -f knowledge_base/meta/execution_checkpoint.json`
- [ ] Run tests: `python3 -m pytest tests/ -q` — all pass (except known test_market_state)

### Final Verification
- [ ] Run a dry session to verify pipeline: start orchestrator, wait for one candle, check logs
- [ ] Verify correct model being called (check log for model name in API response)

---

## First Session (Monitor Closely)

### Startup
- [ ] `python3 -m src.components.orchestrator` starts without errors
- [ ] Log shows "Bootstrap complete — ready to trade"
- [ ] Log shows correct account balance
- [ ] Log shows "MT5 connected"

### During Kill Zone
- [ ] Pre-screen runs (log shows D1/H4 assessment for each candle)
- [ ] If candle passes pre-screen: API call succeeds (check log for Claude response)
- [ ] If CANDIDATE produced: verify in log that entry/SL/TP1 are reasonable
  - TP1 should be ~2.5× SL distance from entry
  - SL should be $10-$60 range (not $400+)
  - Direction should match D1 bias logged in pre-screen
- [ ] If safety check rejects: log shows clear reason
- [ ] If trade placed: verify in MT5 terminal that position exists with correct SL/TP

### After Trade (if any)
- [ ] Position shows correct lot size in MT5
- [ ] SL and TP1 levels match what the log shows
- [ ] If TP1 hit: verify partial close executed (check MT5 trade history)
- [ ] After partial close: verify new ticket has SL at breakeven

### End of Session
- [ ] System logs "All kill zones complete" and ends cleanly
- [ ] No orphaned positions in MT5
- [ ] Session manifest saved to `knowledge_base/sessions/`
- [ ] PID lock file cleaned up

---

## Daily Checks

- [ ] No orphaned positions (MT5 positions should match agent state)
- [ ] Daily P&L within prop firm limits
- [ ] Check API cost: `grep "cost" research/archive/root_legacy_artifacts_2026_05_31/generated/logs/backtest.log | tail -5` (legacy backtest target ~$0.50-1.50/day with Sonnet, ~$2-5 with Opus)
- [ ] Log file not growing excessively (should be <5MB/day)
- [ ] No ERROR lines in today's log: `grep ERROR knowledge_base/sessions/*_live_session.json`

---

## Emergency Procedures

### If System Crashes Mid-Trade
1. Check MT5 for open positions immediately
2. The SL is your protection — position will close at SL if price moves against
3. On restart, `reconcile_on_startup` will detect and adopt orphaned positions
4. If you need to close manually: use MT5 terminal directly

### If API Key Exhausted / Rate Limited
1. System falls back to NO_TRADE on API errors — safe
2. Check `budget.monthly_cap_usd` and Anthropic billing dashboard
3. Active positions are protected by broker-side SL — they don't need the API

### If Prop Firm Drawdown Approaching Limit
1. Our 2% circuit breaker fires first — system stops trading
2. If close to prop firm limit: `kill $(cat knowledge_base/meta/.orchestrator.lock | python3 -c "import json,sys; print(json.load(sys.stdin)['pid'])")`
3. Close all positions manually in MT5
