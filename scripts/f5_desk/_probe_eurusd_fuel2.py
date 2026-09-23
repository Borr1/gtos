import json, MetaTrader5 as mt5, datetime as dt
out={}
mt5.initialize()
# US30 deals for 180770382 today
from_dt = dt.datetime(2026,9,2,0,0,tzinfo=dt.timezone.utc)
deals = mt5.history_deals_get(from_dt, dt.datetime.now(dt.timezone.utc)) or []
us30=[]
for d in deals:
  if d.position_id==180770382 or d.order==180770382:
    us30.append({"deal":d.ticket,"order":d.order,"pos":d.position_id,"entry":d.entry,"price":d.price,"profit":d.profit,"vol":d.volume,"comment":d.comment,"time":dt.datetime.fromtimestamp(d.time,tz=dt.timezone.utc).isoformat(),"commission":d.commission})
out["us30_180770382"]=us30
# EURUSD M15 last 3
rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 4)
bars=[]
if rates is not None:
  for r in rates:
    bars.append({"t":dt.datetime.fromtimestamp(int(r["time"]),tz=dt.timezone.utc).isoformat(),"o":float(r["open"]),"h":float(r["high"]),"l":float(r["low"]),"c":float(r["close"])})
out["eurusd_m15"]=bars
# gbpusd tick for occupied completeness
t=mt5.symbol_info_tick("GBPUSD")
if t: out["gbpusd"]= {"bid":t.bid,"ask":t.ask,"spread":round(t.ask-t.bid,5)}
# day net approx from deals
day_profit=sum(d.profit+d.commission+d.swap for d in deals)
out["day_deals_pnl_approx"]=round(day_profit,2)
# R calc confirm
entry,sl,tp,lots=1.15674,1.15624,1.15974,3.0
sl_dist=round(entry-sl,5); tp_dist=round(tp-entry,5)
tick_val=mt5.symbol_info("EURUSD").trade_tick_value
tick_sz=mt5.symbol_info("EURUSD").trade_tick_size
r_usd=lots*(sl_dist/tick_sz)*tick_val
out["geo"]={"sl_dist":sl_dist,"tp_dist":tp_dist,"tp_r":round(tp_dist/sl_dist,2),"r_usd":round(r_usd,2),"gap_to_ask":round(1.15703-entry,5) if True else None}
# look slate on disk for this family
import pathlib
slate=pathlib.Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
latest=pathlib.Path(r"host-local\redacted_host\repo\judgment\live\latest.json")
for label,p in [("slate",slate),("latest",latest)]:
  if p.exists():
    raw=p.read_text(encoding="utf-8",errors="replace")
    out[label+"_has_eurusd"]=("EURUSD" in raw and "xa_huge" in raw)
    out[label+"_has_ticket"]=("180775761" in raw)
    # extract a small window around xa_huge_20_extreme EURUSD if present
    i=raw.find("xa_huge_20_extreme")
    if i>=0:
      out[label+"_snip"]=raw[max(0,i-120):i+400]
mt5.shutdown()
print(json.dumps(out,default=str)[:8000])
