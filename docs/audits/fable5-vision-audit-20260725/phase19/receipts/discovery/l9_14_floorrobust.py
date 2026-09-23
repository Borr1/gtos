import json, collections
import l9_lib as L
rows=L.load()
fp=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else None)
def hz(r):
    w=r.get("fill_honest_which_came_first")
    return 0.0 if w in ("neither","no_fill") else (r.get("fill_honest_walk_r") or 0.0)
OUT={}
def floor_delta(sub,label,floor=0.45):
    b=[r for r in sub if fp(r) is not None and fp(r)<floor]
    a=[r for r in sub if fp(r) is not None and fp(r)>=floor]
    if not b or not a: return
    sb=L.stats([r.get("fill_honest_walk_r") for r in b]); sa=L.stats([r.get("fill_honest_walk_r") for r in a])
    zb=L.stats([hz(r) for r in b]); za=L.stats([hz(r) for r in a])
    OUT.setdefault(f"floor_{floor}_delta",{})[label]={
      "n_below":len(b),"n_above":len(a),"below_honest":sb["mean"],"above_honest":sa["mean"],
      "delta_honest":sb["mean"]-sa["mean"],
      "below_zn":zb["mean"],"above_zn":za["mean"],"delta_zn":zb["mean"]-za["mean"],
      "se_delta":(sb["se"]**2+sa["se"]**2)**0.5,
      "t_delta":(sb["mean"]-sa["mean"])/((sb["se"]**2+sa["se"]**2)**0.5)}
tk=[r for r in rows if r["takeable"]]
floor_delta(tk,"TAKEABLE_all")
floor_delta([r for r in tk if r.get("is_first_emission")],"TAKEABLE_first_emission_only")
floor_delta([r for r in tk if r["born_state"]=="resting"],"RESTING")
floor_delta([r for r in tk if r["born_state"]=="resting" and r.get("is_first_emission")],"RESTING_first_emission")
floor_delta(rows,"ALL_incl_past_stop")
for fam in sorted(set(r.get("origin_family") for r in tk)):
    floor_delta([r for r in tk if r.get("origin_family")==fam],f"fam:{fam}")
for wk in ["2026-01-0","2026-01-1","2026-01-2","2026-01-3"]:
    floor_delta([r for r in tk if r["decision_time_utc"].startswith(wk)],f"period:{wk}x")
for f in [0.25,0.35,0.80]:
    floor_delta(tk,"TAKEABLE_all",floor=f)
    floor_delta([r for r in tk if r.get("is_first_emission")],"TAKEABLE_first_emission_only",floor=f)
json.dump(OUT,open("L9_FLOORROBUST_V1.json","w"),indent=1,default=str)
for k in sorted(OUT):
    print("==",k)
    for lab,v in OUT[k].items():
        print(f"   {lab:>34} nB={v['n_below']:>5} nA={v['n_above']:>6} below={v['below_honest']:+.4f} above={v['above_honest']:+.4f} d={v['delta_honest']:+.4f} t={v['t_delta']:+5.2f} | dZN={v['delta_zn']:+.4f}")
