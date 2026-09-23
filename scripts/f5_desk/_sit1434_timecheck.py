import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta
mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
tc = mt5.symbol_info_tick("XAUUSD")
# TimeCurrent via terminal
print("tick_time", tc.time, datetime.fromtimestamp(tc.time, tz=timezone.utc).isoformat())
print("tick_time_msc", getattr(tc, "time_msc", None))
print("now_utc", datetime.now(timezone.utc).isoformat())
# last few deals any symbol
frm = datetime(2026, 9, 8, 0, 0, tzinfo=timezone.utc)
to = datetime.now(timezone.utc) + timedelta(hours=6)
deals = mt5.history_deals_get(frm, to) or []
print("deals_today_n", len(deals))
# show last 8
for d in deals[-8:]:
    print(json.dumps({
        "t": d.time,
        "utc": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
        "ict": datetime.fromtimestamp(d.time, tz=timezone(timedelta(hours=7))).strftime("%H:%M:%S"),
        "sym": d.symbol, "pos": d.position_id, "entry": int(d.entry), "profit": d.profit,
        "comment": d.comment, "reason": int(d.reason),
    }))
mt5.shutdown()
