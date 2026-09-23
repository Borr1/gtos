import json
import l9_lib as L
rows=L.load()
fp=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else None)
def hz(r):
    w=r.get("fill_honest_which_came_first")
    return 0.0 if w in ("neither","no_fill") else (r.get("fill_honest_walk_r") or 0.0)
def passes(r,div):
    sp=r["spread_r"]/div; tot=r["cost_r"]-r["spread_r"]+sp
    return sp<=0.10 and tot<=0.15
def netr(r,h,div):
    sp=r["spread_r"]/div
    return h-(r["cost_r"]-r["spread_r"]+sp)
def book(sub,label,div):
    if not sub: return
    S=L.stats
    h=[r.get("fill_honest_walk_r") or 0.0 for r in sub]; z=[hz(r) for r in sub]
    n1=[netr(r,r.get("fill_honest_walk_r") or 0.0,div) for r in sub]
    n2=[netr(r,hz(r),div) for r in sub]
    OUT[label]={"n":len(sub),"honest":S(h)["mean"],"honest_t":S(h)["t"],
      "honest_zn":S(z)["mean"],"zn_t":S(z)["t"],
      f"net_div{div}":S(n1)["mean"],f"net_div{div}_t":S(n1)["t"],
      f"netzn_div{div}":S(n2)["mean"],
      "total_R_honest":sum(h),"total_R_net":sum(n1),
      "mean_fp":L.mean([fp(r) for r in sub]),"pct_past_stop_in_book":0.0}
OUT={}
tk=[r for r in rows if r["takeable"]]
book([r for r in tk if passes(r,1.0) and (fp(r) or 0)>=0.45],"A_frozen_cost_plus_floor045",1.0)
book([r for r in tk if passes(r,7.3) and (fp(r) or 0)>=0.45],"B_repaired_cost_plus_floor045",7.3)
book([r for r in tk if passes(r,7.3)],"C_repaired_cost_no_floor",7.3)
book([r for r in tk if passes(r,7.3) and (fp(r) or 1)<0.45],"D_repaired_cost_passive_only",7.3)
book([r for r in tk if (fp(r) or 1)<0.45],"E_passive_only_no_cost_gate",7.3)
book([r for r in rows if passes(r,7.3) and (fp(r) or 0)>=0.45],"F_repaired_cost_floor045_NO_stop_guard",7.3)
json.dump(OUT,open("L9_BOOKS_V1.json","w"),indent=1,default=str)
print(f"{'book':>42} {'n':>6} {'honest':>8} {'t':>6} {'hZN':>8} {'net':>8} {'t':>6} {'netZN':>8} {'totR':>10} {'fp':>6}")
for k,v in OUT.items():
    nk=[x for x in v if x.startswith("net_div")][0]; nzk=[x for x in v if x.startswith("netzn_div")][0]
    print(f"{k:>42} {v['n']:>6} {v['honest']:>8.4f} {(v['honest_t'] or 0):>6.2f} {v['honest_zn']:>8.4f} {v[nk]:>8.4f} {(v[nk+'_t'] or 0):>6.2f} {v[nzk]:>8.4f} {v['total_R_honest']:>10.1f} {(v['mean_fp'] or 0):>6.3f}")
