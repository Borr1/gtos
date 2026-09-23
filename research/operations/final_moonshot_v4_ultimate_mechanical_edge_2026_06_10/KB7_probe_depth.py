"""KB7 probe: bridge tick-history depth per symbol (flushed, per-call timed)."""
import sys, time
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '.')
from siliconmetatrader5 import MetaTrader5

c = MetaTrader5(host='localhost', port=8001, keepalive=True)
c.initialize()
flags = c.COPY_TICKS_ALL

def log(*a):
    print(*a, flush=True)

for s in ['XAUUSD', 'USOIL.cash', 'BTCUSD', 'XAGUSD', 'UKOIL.cash', 'NATGAS.cash', 'HEATOIL.c']:
    c.symbol_select(s, True)
    log('===', s, '===')
    for y, m in [(2026, 4), (2025, 6), (2024, 6), (2023, 6), (2022, 6), (2020, 6), (2018, 6)]:
        start = datetime(y, m, 3, 12, 0, tzinfo=timezone.utc)
        end = start + timedelta(hours=3)
        t0 = time.time()
        try:
            ticks = c.copy_ticks_range(s, start, end, flags)
            n = 0 if ticks is None else len(ticks)
            dt = time.time() - t0
            log(f'  {y}-{m:02d}: n={n} ({dt:.1f}s)')
        except Exception as e:
            log(f'  {y}-{m:02d}: ERR {type(e).__name__} {e}')
log('DONE')
