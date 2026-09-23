"""w0-capture STEP 2: is the gap-through fill the engine's own marketable-limit handler
misfiring, and how much of the pool is structurally untakeable?"""
import sys, json, math
from collections import defaultdict, Counter
D = "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0, D); import w0_ws

rows = {w0_ws.key(r): r for r in w0_ws.load()}
fav_at_touch, touch_bar, mfe_pre_stop, mfe_from_touch, r_end = {}, {}, {}, {}, {}
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    if k not in rows: continue
    fav, adv = rp["fav"], rp["adv"]
    t = next((i for i,a in enumerate(adv) if a <= 1e-12), None)
    touch_bar[k] = t
    if t is None: continue
    fav_at_touch[k] = fav[t]
    run = -9e9; m = None
    for j in range(t, len(fav)):
        run = max(run, fav[j])
        if adv[j] <= -1.0+1e-9: m = run; break
    mfe_pre_stop[k] = m
    mfe_from_touch[k] = max(fav[t:])
    r_end[k] = rp["cls"][-1]

def cls(k):
    t = touch_bar.get(k)
    if t is None: return "never"
    return "gap" if fav_at_touch[k] < 0 else "clean"

def stat(vals):
    v=sorted(x for x in vals if x is not None and math.isfinite(x))
    if not v: return None
    n=len(v); q=lambda p: v[min(n-1,int(p*n))]
    return {"n":n,"mean":sum(v)/n,"p05":q(.05),"p25":q(.25),"median":q(.5),"p75":q(.75),"p90":q(.9),"p95":q(.95),"max":v[-1],"min":v[0]}

out={}
# ---- 1. engine's own marketable flag vs measured geometry ----
ct=defaultdict(int); recR=defaultdict(list)
for k,r in rows.items():
    flag = r.get("limit_marketable_at_decision")
    ct[(str(flag), cls(k))] += 1
    recR[(str(flag), cls(k))].append(r.get("gross_r"))
out["marketable_flag_x_measured_fill"] = {f"{a}|{b}": {"n":v,"engine_gross_mean_R": (sum(x for x in recR[(a,b)] if x is not None)/max(1,len([x for x in recR[(a,b)] if x is not None])))} for (a,b),v in sorted(ct.items())}
out["effective_order_type_census"] = dict(Counter(str(r.get("effective_order_type")) for r in rows.values()))
ot=defaultdict(lambda: defaultdict(int))
for k,r in rows.items(): ot[str(r.get("effective_order_type"))][cls(k)] += 1
out["effective_order_type_x_fill"] = {a:dict(b) for a,b in ot.items()}

# ---- 2. structurally untakeable: fill bar lies entirely BEYOND the stop ----
unt = [k for k in rows if cls(k)=="gap" and fav_at_touch[k] <= -1.0]
gap = [k for k in rows if cls(k)=="gap"]
g = lambda ks: [rows[k]["gross_r"] for k in ks if rows[k].get("gross_r") is not None]
out["untakeable_stop_already_gone"] = {
  "n": len(unt), "share_of_pool": len(unt)/len(rows), "share_of_gap": len(unt)/len(gap),
  "engine_gross_mean_R": sum(g(unt))/len(g(unt)),
  "engine_total_R": sum(g(unt)),
  "R_per_pool_trade_if_never_traded": -sum(g(unt))/len(rows),
  "fav_at_touch": stat([fav_at_touch[k] for k in unt]),
  "engine_win_rate": sum(1 for x in g(unt) if x>1e-3)/len(g(unt))}
mild = [k for k in gap if fav_at_touch[k] > -1.0]
out["gap_but_stop_intact"] = {"n": len(mild), "engine_gross_mean_R": sum(g(mild))/len(g(mild)),
  "engine_win_rate": sum(1 for x in g(mild) if x>1e-3)/len(g(mild)),
  "R_per_pool_trade_if_never_traded": -sum(g(mild))/len(rows)}

# ---- 3. never-touched phantom ----
nev=[k for k in rows if cls(k)=="never"]
out["phantom_never_touched"] = {"n":len(nev), "engine_gross_mean_R": sum(g(nev))/len(g(nev)),
  "engine_total_R": sum(g(nev)), "engine_win_rate": sum(1 for x in g(nev) if x>1e-3)/len(g(nev)),
  "R_per_pool_trade_if_scored_zero": -sum(g(nev))/len(rows),
  "outcome_bands": dict(Counter(rows[k].get("outcome_band") for k in nev))}

# ---- 4. METHOD-4 sub-target winners ----
tgt = lambda r: float(r.get("policy_target_r") or 2.0)
stw = [k for k,r in rows.items() if r.get("gross_r") is not None and 1e-3 < r["gross_r"] < tgt(r)-1e-3]
out["sub_target_winners"] = {
  "n": len(stw), "share_of_pool": len(stw)/len(rows),
  "engine_recorded_R": stat([rows[k]["gross_r"] for k in stw]),
  "fill_class": dict(Counter(cls(k) for k in stw)),
  "mfe_inside_120m_from_touch": stat([mfe_from_touch.get(k) for k in stw]),
  "reached_2R_inside_120m": sum(1 for k in stw if (mfe_from_touch.get(k) or -9) >= tgt(rows[k])-1e-9),
  "reached_1R_inside_120m": sum(1 for k in stw if (mfe_from_touch.get(k) or -9) >= 1.0),
  "r_at_path_end": stat([r_end.get(k) for k in stw])}

# ---- 5. METHOD-5 full stops: money on the table ----
fs = [k for k,r in rows.items() if r.get("gross_r") is not None and r["gross_r"] <= -1.0+1e-3]
mf = [mfe_pre_stop.get(k) for k in fs]
out["full_stops"] = {"n": len(fs), "share_of_pool": len(fs)/len(rows),
  "fill_class": dict(Counter(cls(k) for k in fs)),
  "mfe_before_stop": stat(mf),
  "share_mfe_ge_0.25R": sum(1 for x in mf if x is not None and x>=0.25)/len(fs),
  "share_mfe_ge_0.5R": sum(1 for x in mf if x is not None and x>=0.5)/len(fs),
  "share_mfe_ge_1.0R": sum(1 for x in mf if x is not None and x>=1.0)/len(fs),
  "share_mfe_ge_2.0R": sum(1 for x in mf if x is not None and x>=2.0)/len(fs),
  "share_no_stop_in_path_or_gap": sum(1 for x in mf if x is None)/len(fs),
  "R_per_pool_if_exit_at_1R_when_mfe_ge_1R": sum(2.0 for x in mf if x is not None and x>=1.0)/len(rows),
  "R_per_pool_if_exit_at_0.5R_when_mfe_ge_0.5R": sum(1.5 for x in mf if x is not None and x>=0.5)/len(rows)}

json.dump(out, open(D+"/W0CAP_MECHANISM_V1.json","w"), indent=1, default=str)
print("MARKETABLE FLAG x FILL:"); [print("  ",a,v) for a,v in out["marketable_flag_x_measured_fill"].items()]
print("ORDER TYPE x FILL:", out["effective_order_type_x_fill"])
for kk in ["untakeable_stop_already_gone","gap_but_stop_intact","phantom_never_touched"]:
    print(kk.upper()+":"); [print("   ",a,"=",str(b)[:150]) for a,b in out[kk].items()]
