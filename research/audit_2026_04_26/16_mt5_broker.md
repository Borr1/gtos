# AUDIT 16: MT5-BROKER

## 5 HIGH-priority issues for Monday
1. Tick daemon never started — manual spawn required (or watchdog hook)
2. `fn_smoke_trade.py` defaults to 5 symbols not 7 (XAGUSD/NAS100 untested)
3. FTMO `trade_expert` flag not confirmed (preflight Test 6 logs warning only)
4. M5 data optional but unchecked
5. US30_cash mt5_symbol override disabled in redacted_account.yaml (interim, intentional)

## Profile semantics correct
- FTMO 2% pin
- FN 1% pin
- per-instrument overrides

## MT5 timeframe constants safe
- H1=16385 etc with fallback

## Magic numbers
- 20260401 GTOS
- 99887766 smoke

## Other findings
- Symbol resolution clean (canonical ↔ broker)
- Order types/retcodes/SL handling correct

## Status
GREEN with 5 caveats — all resolvable in <1 hour pre-launch.
