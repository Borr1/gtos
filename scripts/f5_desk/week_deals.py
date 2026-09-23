import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5
TERM = r"C:\MT5\FTMO\terminal64.exe"
LIVE = 0
if not mt5.initialize(path=TERM):
    print(json.dumps({"ok": False, "err": str(mt5.last_error())}))
    raise SystemExit(3)
try:
    acc = mt5.account_info()
    if acc is None or int(acc.login) != LIVE:
        print(json.dumps({"ok": False, "login": None if acc is None else int(acc.login)}))
        raise SystemExit(4)
    ICT = timezone(timedelta(hours=7))
    start = datetime(2026, 8, 31, 17, 0, tzinfo=timezone.utc)  # Mon Sep 1 00:00 ICT
    end = datetime.now(timezone.utc)
    deals = mt5.history_deals_get(start, end) or []
    pos = {}
    closes = []
    for d in deals:
        if int(d.magic) not in (0, 0) and d.magic:
            pass
        comment = str(d.comment or "")
        if d.entry == 0:  # in
            pos[int(d.position_id)] = {
                "in_deal": int(d.ticket),
                "order": int(d.order),
                "symbol": d.symbol,
                "vol": float(d.volume),
                "price": float(d.price),
                "comment": comment,
                "magic": int(d.magic),
                "in_ict": datetime.fromtimestamp(int(d.time), tz=timezone.utc).astimezone(ICT).strftime("%m-%d %H:%M"),
            }
        elif d.entry == 1:  # out
            rec = pos.get(int(d.position_id), {})
            profit = float(d.profit) + float(d.swap) + float(d.commission)
            closes.append({
                "ticket": int(d.position_id),
                "symbol": d.symbol,
                "comment": rec.get("comment") or comment,
                "magic": rec.get("magic", int(d.magic)),
                "in_ict": rec.get("in_ict"),
                "out_ict": datetime.fromtimestamp(int(d.time), tz=timezone.utc).astimezone(ICT).strftime("%m-%d %H:%M"),
                "profit": round(float(d.profit), 2),
                "comm": round(float(d.commission), 2),
                "net": round(profit, 2),
                "out_comment": comment,
            })
    # F5-ish: magic 0 or F5: comments or tickets >= 180000000
    f5 = [c for c in closes if c.get("magic")==0 or str(c.get("comment","")).startswith("F5:") or (c["ticket"]>=180000000)]
    wins = [c for c in f5 if c["net"]>0]
    losses = [c for c in f5 if c["net"]<0]
    flat = [c for c in f5 if c["net"]==0]
    # consecutive losses from the end
    streak = 0
    for c in reversed(f5):
        if c["net"] < 0:
            streak += 1
        elif c["net"] > 1:  # ignore tiny
            break
        else:
            break
    openp = [{"t":int(p.ticket),"s":p.symbol,"pnl":round(float(p.profit),2)} for p in (mt5.positions_get() or [])]
    out = {
        "ok": True,
        "login": int(acc.login),
        "bal": round(float(acc.balance),2),
        "eq": round(float(acc.equity),2),
        "n_f5": len(f5),
        "n_win": len(wins),
        "n_loss": len(losses),
        "n_flat": len(flat),
        "sum_win": round(sum(c["net"] for c in wins),2),
        "sum_loss": round(sum(c["net"] for c in losses),2),
        "sum_net": round(sum(c["net"] for c in f5),2),
        "loss_streak_now": streak,
        "open": openp,
        "closes": f5,
    }
    print(json.dumps(out))
finally:
    mt5.shutdown()
