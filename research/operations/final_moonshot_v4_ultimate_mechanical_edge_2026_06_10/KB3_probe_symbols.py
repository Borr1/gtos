"""KB3 (track: deepen_val2) — probe broker for true earliest H1/M15/H4 history.
Targets the D6 caveat symbols: crypto cascade (BTCUSD,DASHUSD), energy cascade
(USOIL,UKOIL,NATGAS), grains (WHEAT,SOYBEAN), forward-only energy (HEATOIL,COTTON).
Read-only: only copy_rates_from_pos / symbol_select. No orders."""
import sys, datetime as dt
from siliconmetatrader5 import MetaTrader5

cli = MetaTrader5(host="localhost", port=8001, keepalive=True)
assert cli.initialize(), cli.last_error()

# candidate broker names per logical symbol (try suffixes)
CANDS = {
 "BTCUSD": ["BTCUSD","BTCUSD.cash","BTC.cash"],
 "DASHUSD": ["DASHUSD","DASHUSD.cash","DASH.cash"],
 "USOIL": ["USOIL.cash","USOIL","USOIL.c","WTI.cash"],
 "UKOIL": ["UKOIL.cash","UKOIL","UKOIL.c","BRENT.cash"],
 "NATGAS": ["NATGAS.cash","NATGAS","NATGAS.c","NGAS.cash"],
 "WHEAT": ["WHEAT.c","WHEAT_c","WHEAT","WHEAT.cash"],
 "SOYBEAN": ["SOYBEAN.c","SOYBEAN_c","SOYBEAN","SOYBEAN.cash","SOYBEANS.c"],
 "HEATOIL": ["HEATOIL.c","HEATOIL","HEATOIL.cash"],
 "COTTON": ["COTTON.c","COTTON","COTTON.cash"],
 "CORN": ["CORN.c","CORN"],  # control: known to exist
}

TF = {"H1": MetaTrader5.TIMEFRAME_H1, "M15": MetaTrader5.TIMEFRAME_M15, "H4": MetaTrader5.TIMEFRAME_H4}

def earliest(sym, tf):
    # copy_rates_from_pos with a large count from pos 0 returns most-recent N;
    # to find the earliest, request from far-back start via copy_rates_range.
    start = dt.datetime(2013,1,1, tzinfo=dt.timezone.utc)
    end = dt.datetime(2026,6,15, tzinfo=dt.timezone.utc)
    r = cli.copy_rates_range(sym, tf, start, end)
    if r is None or len(r)==0:
        return None, 0
    ts = [int(x['time']) if hasattr(x,'__getitem__') else int(x.time) for x in r]
    first = dt.datetime.fromtimestamp(min(ts), tz=dt.timezone.utc)
    last = dt.datetime.fromtimestamp(max(ts), tz=dt.timezone.utc)
    return (first.date().isoformat(), last.date().isoformat(), len(r))

for logical, cands in CANDS.items():
    found = None
    for c in cands:
        sel = cli.symbol_select(c, True)
        if sel:
            found = c
            break
    if not found:
        print(f"{logical:9s}  NO BROKER SYMBOL (tried {cands})")
        continue
    line = f"{logical:9s} -> {found:14s}"
    for tfn, tf in TF.items():
        res = earliest(found, tf)
        if res is None or res[0] is None:
            line += f"  {tfn}:none"
        else:
            line += f"  {tfn}:{res[0]}..{res[1]}(n={res[2]})"
    print(line)

cli.close()
