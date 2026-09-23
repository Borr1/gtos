import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5
TERM=r"C:\MT5\FTMO\terminal64.exe"
mt5.initialize(path=TERM)
ICT=timezone(timedelta(hours=7))
# M5 from 02:00 UTC Sep 1 (09:00 ICT) through 08:00 UTC
start=datetime(2026,9,1,2,0,tzinfo=timezone.utc)
r=mt5.copy_rates_from("XAUUSD", mt5.TIMEFRAME_M5, start, 80)
rows=[]
hit_tp=False
tp=4428.06
take=4447.67
mfe_low=4436.27
low_after=None
if r is not None:
    for x in r:
        t=datetime.fromtimestamp(int(x['time']), tz=timezone.utc).astimezone(ICT)
        lo=float(x['low']); hi=float(x['high'])
        rows.append({"t":t.strftime("%H:%M"),"l":round(lo,2),"h":round(hi,2),"c":round(float(x['close']),2)})
        if t.strftime("%H:%M")>="09:22":
            if low_after is None or lo<low_after: low_after=lo
            if lo<=tp: hit_tp=True
print(json.dumps({"hit_tp_after_take":hit_tp,"low_after_0922":None if low_after is None else round(low_after,2),"tp":tp,"take":take,"mfe_before":mfe_low,"bars":rows[:40]}))
mt5.shutdown()
