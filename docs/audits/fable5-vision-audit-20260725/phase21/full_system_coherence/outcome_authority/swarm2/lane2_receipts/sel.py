#!/usr/bin/env python3
"""(D) the portfolio price of a longer hold: symbol-blocking under the sealed selector.

`w21_score_feb_market_top_r2.select()` (:226-256) blocks a symbol while a selected trade
is active. Longer holds therefore cost TRADES. This replays that blocking rule with the
month-boundary ridge prediction in the puzzle cache and the walk's own per-horizon exit
time, so the trade-count effect is measured rather than assumed.
"""
import gzip,pickle,json,datetime as dt
from collections import defaultdict,Counter
import numpy as np
MIN_R=0.10   # r.m.MIN_EXPECTED_NET_R, pinned below
MONTHS=["feb","apr","may","jun","jul"]
HS=["h1","h2","h4","h8","hInf"]
W={}
for m in MONTHS:
    for r in pickle.load(gzip.open(f"walk_{m}.pkl.gz","rb")): W[r["k"]]=r
rows=[]
for m in MONTHS:
    for c in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")):
        if c.get("pred_month_boundary") is None: continue
        rows.append(c)
print("eligible predicted rows",len(rows))
EP=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
def mn(s): return int((dt.datetime.fromisoformat(str(s))-EP).total_seconds()//60)
byw=defaultdict(list)
for c in rows: byw[c["decision_window_id"]].append(c)
order=sorted(byw.values(), key=lambda v:(min(mn(x["label_span_start_utc"]) for x in v), v[0]["decision_window_id"]))
out={}
for h in HS:
    active={}; sel=[]; disp=Counter()
    for cands in order:
        at=min(mn(x["label_span_start_utc"]) for x in cands)
        active={s:e for s,e in active.items() if e>at}
        avail=[c for c in cands if c["symbol"] not in active]
        if not avail: disp["no_available"]+=1; continue
        top=max(avail,key=lambda c:(float(c["pred_month_boundary"]),-float(c["cost_r"]),c["candidate_occurrence_key"]))
        if float(top["pred_month_boundary"])<MIN_R: disp["top_below_0p10"]+=1; continue
        if top["proposed_order_type"]!="MARKET": disp["top_limit_abstain"]+=1; continue
        w=W.get(top["candidate_occurrence_key"])
        if w is None or w.get("fi") is None or not w.get(h) or w[h]["gross"] is None:
            disp["unresolved"]+=1
            end=mn(top["expiry_utc"])
        else:
            sel.append((top,w[h]["gross"]-w["ded"],w[h]["end"]-w["fill_min"],w[h]["kind"]))
            end=w[h]["end"]
        active[top["symbol"]]=end
        disp["trade"]+=1
    nets=np.array([x[1] for x in sel]); holds=np.array([x[2] for x in sel],dtype=float)
    days=len({x[0]["trading_day"] for x in sel})
    kk=Counter(x[3] for x in sel)
    out[h]={"n_trades":len(sel),"total_net_r":float(nets.sum()),"mean_net_r":float(nets.mean()),
            "r_per_day":float(nets.sum()/days),"days":days,"mean_hold_min":float(holds.mean()),
            "median_hold_min":float(np.median(holds)),"kinds":dict(kk),"dispositions":dict(disp)}
    print(h,json.dumps(out[h]),flush=True)
json.dump(out,open("SELECTOR_TURNOVER.json","w"),indent=1)
