import json, collections, math
import l9_lib as L
rows=L.load()
tk=[r for r in rows if r["takeable"]]
g={t:v for t,v in L.groups(tk).items() if len(v)>=5}
def fp(r): 
    v=r.get("execution_fill_probability")
    return v if v is not None else 9.0
pos1=[]; posrest=[]
for t,v in g.items():
    o=sorted(v,key=fp); pos1.append(o[0]); posrest.extend(o[1:])
OUT={}
def prof(v,label):
    wc=collections.Counter(r.get("fill_honest_which_came_first") for r in v)
    def m(sel): 
        s=[r for r in v if r.get("fill_honest_which_came_first")==sel]
        return len(s), L.mean([r.get("fill_honest_walk_r") for r in s])
    z=[0.0 if r.get("fill_honest_which_came_first")in("neither","no_fill") else (r.get("fill_honest_walk_r") or 0.0) for r in v]
    s=L.stats([r.get("fill_honest_walk_r") for r in v]); sz=L.stats(z)
    OUT.setdefault("profiles",{})[label]={
      "n":len(v),"honest_mean":s["mean"],"se":s["se"],"t":s["t"],
      "honest_zero_neither_mean":sz["mean"],"zn_se":sz["se"],"zn_t":sz["t"],
      "gross_r":L.mean([r["gross_r"] for r in v]),
      "plain_walk_r":L.mean([r.get("plain_walk_r") for r in v]),
      "which":dict(wc),
      "target":m("target"),"stop":m("stop"),"neither":m("neither"),"no_fill":m("no_fill"),
      "mean_fp":L.mean([fp(r) for r in v]),"mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
      "mean_bars_to_entry":L.mean([r.get("bars_to_entry_touch") for r in v]),
      "mean_cost_r":L.mean([r["cost_r"] for r in v]),
      "net_at_frozen_cost":L.mean([(r.get("fill_honest_walk_r") or 0)-r["cost_r"] for r in v]),
      "net_at_spread_div_8":L.mean([(r.get("fill_honest_walk_r") or 0)-(r["cost_r"]-r["spread_r"]*(1-1/8.0)) for r in v]),
    }
prof(pos1,"POS1_most_passive"); prof(posrest,"POS2plus")
# temporal + symbol stability of pos1
def by(keyf,label,sub):
    d=collections.defaultdict(list)
    for r in sub: d[keyf(r)].append(r)
    t={}
    for k in sorted(d,key=str):
        v=d[k]; s=L.stats([r.get("fill_honest_walk_r") for r in v])
        t[str(k)]={"n":len(v),"honest":s["mean"],"se":s["se"],"t":s["t"]}
    OUT.setdefault(label,{}).update(t)
by(lambda r:r["decision_time_utc"][:10],"pos1_by_day",pos1)
by(lambda r:r["symbol"],"pos1_by_symbol",pos1)
by(lambda r:r.get("origin_family"),"pos1_by_family",pos1)
pos_days=[v["honest"] for v in OUT["pos1_by_day"].values()]
OUT["pos1_day_positivity"]={"days":len(pos_days),"positive_days":sum(1 for x in pos_days if x>0),
                            "median_day":sorted(pos_days)[len(pos_days)//2]}
json.dump(OUT,open("L9_POS1_V1.json","w"),indent=1,default=str)
for k,v in OUT["profiles"].items():
    print("==",k,"n",v["n"])
    print("   honest",round(v["honest_mean"],4),"se",round(v["se"],4),"t",round(v["t"],2),
          "| zero-neither",round(v["honest_zero_neither_mean"],4),"t",round(v["zn_t"],2),
          "| gross",round(v["gross_r"],4),"| plain",round(v["plain_walk_r"],4))
    print("   which",v["which"],"tgt",[round(x,4) if isinstance(x,float) else x for x in v["target"]],
          "stp",[round(x,4) if isinstance(x,float) else x for x in v["stop"]],
          "nei",[round(x,4) if isinstance(x,float) else x for x in v["neither"]])
    print("   fp",round(v["mean_fp"],3),"rank",round(v["mean_rank"],1),"barsEnt",round(v["mean_bars_to_entry"],1),
          "cost",round(v["mean_cost_r"],3),"net@frozen",round(v["net_at_frozen_cost"],4),"net@spread/8",round(v["net_at_spread_div_8"],4))
print("pos1 day positivity:",OUT["pos1_day_positivity"])
print("pos1 by symbol (top/bottom 6):")
sy=sorted(OUT["pos1_by_symbol"].items(),key=lambda kv:-kv[1]["honest"])
for k,v in sy[:6]+sy[-6:]: print(f"   {k:>12} n={v['n']:>4} {v['honest']:+.4f} t={(v['t'] or 0):+.2f}")
