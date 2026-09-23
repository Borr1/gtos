# Demo Deployment Verification
Date: 2026-04-02
Machine: Windows 11 Pro (UTC+8)

## Phase 1: Environment
- [x] Python version: 3.13.1
- [x] All dependencies installed (MetaTrader5 5.0.5640, anthropic 0.87.0, pydantic 2.12.5, numpy 2.4.4, python-dotenv 1.2.2, lancedb 0.30.2, sentence-transformers 5.3.0)
- [x] API key present and valid (sk-ant-api03... confirmed working with API call)
- [x] Test suite: 291/292 passing (1 pre-existing market_state integration test — known)

## Phase 2: Code Fixes
- [x] TP1 2.5R rule in prompt: PRESENT (lines 42, 80, 102 of primary_analyzer_prompt.py)
- [x] Max SL distance gate (2.5%): PRESENT (line 136-143 of permissions.py)
- [x] TP1/SL ratio check (min 2.0R): PRESENT (line 109-122 of permissions.py)
- [x] Null params guard: PRESENT (line 217-218, 494-504 of primary_analyzer.py)
- [x] Config correct: London KZ 07:00-09:30, max_trades=2, min_rr=2.5
- [x] Config FIXED: budget monthly_cap_usd 25->50, deployment phase 1->2
- [x] enabled_frameworks: ["ob_retest"] only — breaker_retest disabled
- [x] Breaker sections stripped from prompt via _strip_breaker_sections() in primary_analyzer.py
- [x] MT5 timeframe constants correct (TF_H1=16385, etc. with try/except fallback)
- [x] compute_session_levels: fully implemented (asian H/L, PDH/PDL)
- [x] file_versioning.py: present

## Phase 3: MT5 Connection
- [x] MT5 connected to DEMO account (trade_mode=0)
- [x] MT5 version: 500.5724 (1 Apr 2026)
- [x] Account: 0, Balance: $100,000.00, Server: MetaQuotes-Demo
- [x] Symbol: XAUUSD
- [x] Contract size: 100 (STANDARD)
- [x] Volume: min=0.01, max=100.0, step=0.01
- [x] Data available: M15 672/672, H1 168/168, H4 80/80, D1 30/30 (all 100%)
- [x] Spread: 17.0 cents (well under 30 limit)
- [ ] **BLOCKER: AutoTrading disabled in MT5 client** — must enable "Algo Trading" button before launching
- [x] Filling mode: ORDER_FILLING_IOC (matches execution.py)
- [x] No orphaned positions

## Phase 4: Pipeline Test
- [x] Mock mode starts cleanly (no import errors, logs bootstrap complete)
- [x] Integration test: data ingestion OK (all timeframes, session levels computed)
- [x] Integration test: MSO computation OK (MarketStateObject returned)
- [x] Integration test: pre-screen result: PASS
- [x] Integration test: API call: OK — returned NO_TRADE (grade C, D1 transitional/ranging)

## Phase 5: Execution Engine
- [x] safe_place_order check-before-retry: verified (sleeps 2s, queries positions, adopts or returns None)
- [x] Filling mode: ORDER_FILLING_IOC (matches broker)
- [x] MAGIC_NUMBER: 20260401 (in mt5_interface.py)
- [x] Partial close logic: queries new ticket, re-applies SL (breakeven) and TP2
- [x] Demo mode uses RealMT5, places actual orders (no skip logic)

## Status: BLOCKED — Enable AutoTrading in MT5

### To unblock:
1. Open MetaTrader 5
2. Click "Algo Trading" button in toolbar (top bar) — it should turn GREEN
3. Re-run: `python scripts/mt5_preflight.py` — Test 5 should show "OK: Test order placed"
4. Then launch: `python run_agent.py --mode demo`

### Next kill zones (from UTC+8):
- London KZ: 15:00-17:30 local (07:00-09:30 UTC) — TODAY
- NY KZ: 21:00-23:30 local (13:00-15:30 UTC) — TODAY
