import json, collections
import l9_lib as L
rows=L.load()
res=[r for r in rows if r["born_state"]=="resting"]
def fb(fp):
    if fp is None: return "null"
    for hi,lab in [(0.10,"a<0.10"),(0.20,"b0.10-0.20"),(0.30,"c0.20-0.30"),(0.40,"d0.30-0.40"),
                   (0.50,"e0.40-0.50"),(0.60,"f0.50-0.60"),(0.70,"g0.60-0.70"),(0.80,"h0.70-0.80"),
                   (0.9199,"i0.80-0.92"),(2.0,"j>=0.92")]:
        if fp<hi: return lab
    return "j>=0.92"
OUT={}
def decomp(sub,label):
    by=collections.defaultdict(list)
    for r in sub: by[fb(r.get("execution_fill_probability"))].append(r)
    t={}
    for k in sorted(by):
        v=by[k]; n=len(v)
        wc=collections.Counter(r.get("fill_honest_which_came_first") for r in v)
        resolved=[r for r in v if r.get("fill_honest_which_came_first") in ("stop","target")]
        neither=[r for r in v if r.get("fill_honest_which_came_first")=="neither"]
        t[k]={"n":n,"honest":L.mean([r.get("fill_honest_walk_r") for r in v]),
              "pct_target":100*wc["target"]/n,"pct_stop":100*wc["stop"]/n,
              "pct_neither":100*wc["neither"]/n,"pct_nofill":100*wc["no_fill"]/n,
              "resolved_n":len(resolved),
              "resolved_mean":L.mean([r.get("fill_honest_walk_r") for r in resolved]),
              "resolved_winrate":(sum(1 for r in resolved if r.get("fill_honest_which_came_first")=="target")/len(resolved)) if resolved else None,
              "neither_mean":L.mean([r.get("fill_honest_walk_r") for r in neither]),
              "bars_to_entry":L.mean([r.get("bars_to_entry_touch") for r in v]),
              "bars_left":L.mean([(r.get("path_bars") or 120)-(r.get("bars_to_entry_touch") or 0) for r in v]),
              "risk_dist_pct":L.mean([100*r["risk_distance"]/r["entry_price"] for r in v if r.get("entry_price")]),
              "mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
              "gross_r":L.mean([r["gross_r"] for r in v])}
    OUT.setdefault("decomp",{})[label]=t
    return t
decomp(res,"RESTING")
decomp([r for r in rows if r["takeable"]],"TAKEABLE")
# per-cycle argmin cohort profile
g={t:v for t,v in L.groups([r for r in rows if r["takeable"]]).items() if len(v)>=2}
picks=[min(v,key=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else 9)) for v in g.values()]
wc=collections.Counter(r.get("fill_honest_which_came_first") for r in picks)
OUT["argmin_fp_cohort"]={"n":len(picks),"honest":L.mean([r.get("fill_honest_walk_r") for r in picks]),
  "gross_r":L.mean([r["gross_r"] for r in picks]),
  "mean_fp":L.mean([r.get("execution_fill_probability") for r in picks]),
  "median_fp":sorted(r.get("execution_fill_probability") or 9 for r in picks)[len(picks)//2],
  "which_came_first":dict(wc),"mean_rank":L.mean([r["risk_finalizer_rank"] for r in picks]),
  "share_resting":sum(1 for r in picks if r["born_state"]=="resting")/len(picks),
  "bars_to_entry":L.mean([r.get("bars_to_entry_touch") for r in picks])}
json.dump(OUT,open("L9_FPDECOMP_V1.json","w"),indent=1,default=str)
for lab in ["RESTING","TAKEABLE"]:
    print("==",lab)
    t=OUT["decomp"][lab]
    print(f"{'fp':>12} {'n':>6} {'honest':>8} {'tgt%':>6} {'stp%':>6} {'nei%':>6} {'nof%':>5} {'resN':>6} {'resMean':>8} {'resWin%':>7} {'neiMean':>8} {'bEnt':>6} {'bLeft':>6} {'rdpct':>7} {'rank':>5}")
    for k in sorted(t):
        d=t[k]
        print(f"{k:>12} {d['n']:>6} {d['honest']:>8.4f} {d['pct_target']:>6.1f} {d['pct_stop']:>6.1f} {d['pct_neither']:>6.1f} {d['pct_nofill']:>5.1f} {d['resolved_n']:>6} {(d['resolved_mean'] or 0):>8.4f} {100*(d['resolved_winrate'] or 0):>7.1f} {(d['neither_mean'] or 0):>8.4f} {(d['bars_to_entry'] or 0):>6.1f} {(d['bars_left'] or 0):>6.1f} {(d['risk_dist_pct'] or 0):>7.4f} {d['mean_rank']:>5.1f}")
print("argmin cohort:",{k:(round(v,4) if isinstance(v,float) else v) for k,v in OUT["argmin_fp_cohort"].items()})
