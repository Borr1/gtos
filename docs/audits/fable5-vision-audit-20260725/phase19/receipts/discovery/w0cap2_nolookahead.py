"""Robustness: repeat the born-state split using ONLY the last FULLY CLOSED M1 bar strictly
before the decision minute (mkt_r_prev_close).  Zero look-ahead by construction."""
import sys,os,json,gzip
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
rows=w0_ws.load(); anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def mean(v):
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None
out={}
for lbl,fld in (("ANCHOR_decision_minute_close","mkt_r_close"),("NO_LOOKAHEAD_prev_closed_bar","mkt_r_prev_close")):
    g={}
    for r in rows:
        a=anch.get(w0_ws.key(r))
        if a is None: continue
        g.setdefault(bo(a[fld]),[]).append(r.get("gross_r"))
    tot=sum(len(v) for v in g.values())
    out[lbl]={bs:{"n":len(v),"share_pct":round(100*len(v)/tot,3),"engine_gross_r":mean(v),
                  "win_pct":round(100*sum(1 for x in v if x and x>0)/len(v),3),
                  "contribution_to_pool":round(sum(x for x in v if x is not None)/tot,5)}
              for bs,v in sorted(g.items())}
# agreement matrix
agree=sum(1 for r in rows if w0_ws.key(r) in anch and bo(anch[w0_ws.key(r)]["mkt_r_close"])==bo(anch[w0_ws.key(r)]["mkt_r_prev_close"]))
n=sum(1 for r in rows if w0_ws.key(r) in anch)
out["classifier_agreement"]={"n":n,"agree":agree,"agree_pct":round(100*agree/n,3)}
json.dump(out,open(os.path.join(D,"W0CAP2_NOLOOKAHEAD_V1.json"),"w"),indent=1)
for lbl in out:
    if lbl=="classifier_agreement": continue
    print(lbl)
    for bs,v in out[lbl].items():
        print(f'  {bs:18s} n{v["n"]:6d} {v["share_pct"]:5.2f}% gross{v["engine_gross_r"]:+8.4f} win{v["win_pct"]:5.1f}% contrib{v["contribution_to_pool"]:+8.5f}')
print("AGREEMENT",out["classifier_agreement"])
