import MetaTrader5 as mt5, json
from datetime import datetime, timezone
mt5.initialize()
REASON={0:"CLIENT",1:"MOBILE",2:"WEB",3:"EXPERT",4:"SL",5:"TP",6:"SO",7:"ROLLOVER",8:"EXT_CLIENT",9:"VMARGIN",10:"SPLIT",11:"EXT_SERVICE",12:"CLOSE_BY"}
ai=mt5.account_info()
print("LOGIN", ai.login, "BAL", ai.balance, "EQ", ai.equity, "FLOAT", round(ai.profit,2))
print("NOW", datetime.now(timezone.utc).isoformat())
for pos in (181316091, 181295784, 181349120):
    print("===POSITION", pos)
    for d in (mt5.history_deals_get(position=pos) or []):
        print("DEAL", json.dumps({"deal":d.ticket,"order":d.order,"pos":d.position_id,"sym":d.symbol,
          "type":int(d.type),"entry":int(d.entry),"vol":d.volume,"price":d.price,"profit":d.profit,
          "swap":d.swap,"comm":d.commission,"reason":int(d.reason),"rname":REASON.get(int(d.reason),"?"),
          "comment":d.comment,"magic":d.magic,
          "t":datetime.fromtimestamp(d.time,tz=timezone.utc).isoformat()}, default=str))
    for o in (mt5.history_orders_get(position=pos) or []):
        print("ORDER", json.dumps({"order":o.ticket,"pos":o.position_id,"sym":o.symbol,"type":int(o.type),
          "state":int(o.state),"vol":o.volume_initial,"pop":o.price_open,"sl":o.sl,"tp":o.tp,
          "comment":o.comment,"magic":o.magic,
          "setup":datetime.fromtimestamp(o.time_setup,tz=timezone.utc).isoformat(),
          "done":datetime.fromtimestamp(o.time_done,tz=timezone.utc).isoformat() if o.time_done else None}, default=str))
print("===OPEN NOW===")
for p in (mt5.positions_get() or []):
    t=mt5.symbol_info_tick(p.symbol); sp=(t.ask-t.bid) if t else None
    sd=abs(p.price_open-p.sl) if p.sl else None
    print("POS", json.dumps({"ticket":p.ticket,"sym":p.symbol,"side":"LONG" if p.type==0 else "SHORT",
      "vol":p.volume,"entry":p.price_open,"sl":p.sl,"tp":p.tp,"profit":round(p.profit,2),
      "spread":sp,"spread_vs_R":(sp/sd if sp and sd else None),
      "opened":datetime.fromtimestamp(p.time,tz=timezone.utc).isoformat()}, default=str))
print("PENDING", len(mt5.orders_get() or []))
for o in (mt5.orders_get() or []):
    print("PEND", json.dumps({"order":o.ticket,"sym":o.symbol,"type":int(o.type),"vol":o.volume_current,
      "pop":o.price_open,"sl":o.sl,"tp":o.tp,"exp":datetime.fromtimestamp(o.time_expiration,tz=timezone.utc).isoformat() if o.time_expiration else None,
      "comment":o.comment}, default=str))
xau=[p.ticket for p in (mt5.positions_get() or []) if p.symbol.upper().startswith("XAUUSD")]
print("XAUUSD_OPEN", xau)
mt5.shutdown()
