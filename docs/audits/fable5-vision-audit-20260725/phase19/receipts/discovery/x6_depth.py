import json, datetime as dt, statistics
P='/Users/borr/GTOSActive/vps-ticks-20260726/MARKET_DATA_DEPTH_PROBE.json'
d=json.load(open(P))
out={"source":P,"generated_utc":d["generated_utc"],"brokers":{}}
for bk,b in d["brokers"].items():
    if b.get("status")!="ok": continue
    rec={"login":b.get("login"),"server":b.get("server"),"terminal_maxbars":b.get("terminal_maxbars"),
         "traded_symbol_count":b.get("traded_symbol_count"),"symbols":{}}
    m1_days=[]; tick_ok=0; tick_tot=0; tpm=[]
    for sym,s in b.get("symbols",{}).items():
        r=s.get("rates",{}); t=s.get("ticks",{}) or {}
        row={}
        for tf in ("M1","M15","H4","D1"):
            e=r.get(tf,{})
            if not e.get("available"): row[tf]=None; continue
            try:
                a=dt.datetime.fromisoformat(e["earliest_bar_broker"]); z=dt.datetime.fromisoformat(e["latest_bar_broker"])
                span=(z-a).total_seconds()/86400.0
            except Exception: span=None
            row[tf]={"earliest":e.get("earliest_bar_broker"),"latest":e.get("latest_bar_broker"),"span_days":round(span,1) if span else None}
        if row.get("M1") and row["M1"]["span_days"]: m1_days.append(row["M1"]["span_days"])
        tick_tot+=1
        if t.get("deeper_than_2025_10"): tick_ok+=1
        sd=t.get("sampled_day") or {}
        if sd.get("ticks_per_m1_bar"): tpm.append(sd["ticks_per_m1_bar"])
        row["ticks_earliest"]=t.get("earliest_tick_broker"); row["ticks_verdict"]=t.get("realness_verdict")
        row["ticks_per_m1_bar"]=sd.get("ticks_per_m1_bar"); row["tick_rows_sampled_day"]=sd.get("tick_rows")
        rec["symbols"][sym]=row
    rec["summary"]={
      "n_symbols":tick_tot,
      "m1_span_days_min":round(min(m1_days),1) if m1_days else None,
      "m1_span_days_median":round(statistics.median(m1_days),1) if m1_days else None,
      "m1_span_days_max":round(max(m1_days),1) if m1_days else None,
      "m1_span_days_n":len(m1_days),
      "maxbars_implied_m1_days_24x5":round(b.get("terminal_maxbars",0)/1440*7/5,1),
      "maxbars_implied_m1_days_24x7":round(b.get("terminal_maxbars",0)/1440,1),
      "symbols_with_ticks_deeper_than_2025_10":f"{tick_ok}/{tick_tot}",
      "ticks_per_m1_bar_median":round(statistics.median(tpm),1) if tpm else None,
      "ticks_per_m1_bar_min":round(min(tpm),1) if tpm else None,
      "ticks_per_m1_bar_max":round(max(tpm),1) if tpm else None,
    }
    out["brokers"][bk]=rec
json.dump(out,open('/tmp/x6/X6_DEPTH_V1.json','w'),indent=1)
for bk,r in out["brokers"].items():
    print(f"=== {bk} ({r['server']}) maxbars={r['terminal_maxbars']} ===")
    for k,v in r["summary"].items(): print(f"   {k}: {v}")
