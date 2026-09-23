import json, collections
import l9_lib as L
rows = L.load()
OUT={}
OUT["fill_honest_which_came_first"]=dict(collections.Counter(r.get("fill_honest_which_came_first") for r in rows))
nf=[r for r in rows if r.get("fill_honest_which_came_first")=="no_fill"]
OUT["no_fill_rows"]={"n":len(nf),"mean_fill_honest_walk_r":L.mean([r.get("fill_honest_walk_r") for r in nf]),
                     "distinct_vals":sorted(set(round(r.get("fill_honest_walk_r") or 0,6) for r in nf))[:5]}
def buck(r):
    fp=r.get("execution_fill_probability")
    if fp is None: return "null"
    if fp>=0.949: return "H_0.95"
    if abs(fp-0.92)<1e-9: return "G_0.92_marketable"
    for lo,hi,lab in [(0.80,0.92,"F_0.80-0.92"),(0.70,0.80,"E_0.70-0.80"),(0.60,0.70,"D_0.60-0.70"),
                      (0.50,0.60,"C_0.50-0.60"),(0.30,0.50,"B_0.30-0.50"),(0.0,0.30,"A_0.03-0.30")]:
        if lo<=fp<hi: return lab
    return "other"
def tab(sub,label):
    by=collections.defaultdict(list)
    for r in sub: by[buck(r)].append(r)
    t={}
    for k in sorted(by):
        v=by[k]
        filled=[r for r in v if r.get("fill_honest_which_came_first")!="no_fill"]
        t[k]={"n":len(v),
              "fill_honest_walk_r":L.mean([r.get("fill_honest_walk_r") for r in v]),
              "gross_r":L.mean([r["gross_r"] for r in v]),
              "plain_walk_r":L.mean([r.get("plain_walk_r") for r in v]),
              "fill_rate":len(filled)/len(v),
              "mean_r_given_filled":L.mean([r.get("fill_honest_walk_r") for r in filled]),
              "mean_bars_to_entry_touch":L.mean([r.get("bars_to_entry_touch") for r in v]),
              "cost_r":L.mean([r["cost_r"] for r in v]),
              "spread_r":L.mean([r["spread_r"] for r in v]),
              "share_past_stop":sum(1 for r in v if r["born_state"]=="past_stop")/len(v),
              "mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
              "full_stop_rate":sum(1 for r in v if (r.get("fill_honest_walk_r") or 0)<=-1+1e-3)/len(v)}
    OUT.setdefault("fillprob_table",{})[label]=t
    return t
tab(rows,"ALL"); tab([r for r in rows if r["takeable"]],"TAKEABLE")
tab([r for r in rows if r["born_state"]=="resting"],"RESTING_only")
OUT["fill_realism_class"]={}
for cls in set(r.get("fill_realism_class") for r in rows):
    v=[r for r in rows if r.get("fill_realism_class")==cls]
    OUT["fill_realism_class"][str(cls)]={"n":len(v),"fill_honest_walk_r":L.mean([r.get("fill_honest_walk_r") for r in v]),
        "gross_r":L.mean([r["gross_r"] for r in v]),"mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
        "share_past_stop":sum(1 for r in v if r["born_state"]=="past_stop")/len(v)}
json.dump(OUT,open("L9_FILLPROB_V1.json","w"),indent=1,default=str)
print("which_came_first:",OUT["fill_honest_which_came_first"])
print("no_fill:",OUT["no_fill_rows"])
for lab in ["TAKEABLE","RESTING_only"]:
    print("==",lab)
    t=OUT["fillprob_table"][lab]
    print(f"{'bucket':>18} {'n':>6} {'honest':>8} {'gross':>8} {'fill%':>6} {'R|fill':>8} {'bars':>6} {'cost':>6} {'stop%':>6} {'rank':>6}")
    for k in sorted(t):
        d=t[k]
        print(f"{k:>18} {d['n']:>6} {d['fill_honest_walk_r']:>8.4f} {d['gross_r']:>8.4f} {100*d['fill_rate']:>6.1f} {(d['mean_r_given_filled'] or 0):>8.4f} {(d['mean_bars_to_entry_touch'] or 0):>6.1f} {d['cost_r']:>6.3f} {100*d['full_stop_rate']:>6.1f} {d['mean_rank']:>6.1f}")
print("fill_realism_class:",{k:(v['n'],round(v['fill_honest_walk_r'],4),round(v['mean_rank'],1)) for k,v in OUT["fill_realism_class"].items()})
