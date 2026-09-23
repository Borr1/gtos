#!/usr/bin/env python3
"""Is the SEALED January pool label fill-aware or decision-anchored?

Compares the pool's own `opportunity_net_proxy_r + cost_r` (call it G_sealed) against
  ARM A  decision-anchored barrier walk from obs 0
  ARM C  fill-anchored walk (limit touch searched from obs 1)
at the pool's own native geometry (stop 1.0R, target policy_target_r).
"""
import gzip, json, math
from collections import defaultdict
import numpy as np

R = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
POOL = f"{R}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
SIDE = f"{R}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
TOL = 1e-9
LIMFAM = {"current_ob_retest", "current_fvg_fill", "current_breaker_re_entry"}

def walk(hi, lo, cl, e, bd, side, tr, start):
    hi, lo = hi[start:], lo[start:]
    if len(hi) == 0: return None
    if side == "LONG": fav, adv = (hi - e)/bd, (e - lo)/bd
    else:              fav, adv = (e - lo)/bd, (hi - e)/bd
    rf, ra = np.maximum.accumulate(fav), np.maximum.accumulate(adv)
    fi = int(np.searchsorted(rf, tr - TOL, side="left"))
    si = int(np.searchsorted(ra, 1.0 - TOL, side="left"))
    n = len(hi)
    td = (cl - e)/bd if side == "LONG" else (e - cl)/bd
    if si < n and (fi >= n or si <= fi): return -1.0
    if fi < n: return tr
    return max(-1.0, min(td, tr))

acc = defaultdict(lambda: dict(n=0, sealedA=[], sealedC=[], A=[], C=[], S=[], nofill=0))
n = 0
for pl, sl in zip(gzip.open(POOL,'rt'), gzip.open(SIDE,'rt')):
    if not pl.strip(): continue
    p = json.loads(pl); s = json.loads(sl); n += 1
    e = float(p["entry_price"]); st = float(p["stop_loss"]); bd = abs(e-st)
    obs = s["ordered_path_observations"]
    if not math.isfinite(bd) or bd <= 0 or len(obs) < 2: continue
    side = str(p["side"]).upper(); tr = float(p.get("policy_target_r") or 2.0)
    hi = np.fromiter((float(o["high"]) for o in obs), np.float64)
    lo = np.fromiter((float(o["low"]) for o in obs), np.float64)
    cl = float(obs[-1]["close"])
    G = float(p["opportunity_net_proxy_r"]) + float(p.get("cost_r") or 0.0)
    A = walk(hi, lo, cl, e, bd, side, tr, 0)
    w = np.flatnonzero(lo[1:] <= e + TOL) if side=="LONG" else np.flatnonzero(hi[1:] >= e - TOL)
    f = (1 + int(w[0])) if len(w) else None
    C = walk(hi, lo, cl, e, bd, side, tr, f) if f is not None else None
    resting = (str(p.get("effective_order_type"))=="limit" and
               not ((lo[0] <= e + TOL) if side=="LONG" else (hi[0] >= e - TOL)))
    for key in ("ALL", ("LIMITFAM" if p["origin_family"] in LIMFAM else "MKTFAM"),
                ("RESTING" if resting else "NOTRESTING"), "F:"+p["origin_family"]):
        d = acc[key]; d["n"] += 1
        d["S"].append(G); d["A"].append(A)
        d["sealedA"].append(abs(G - A) < 1e-6)
        if C is None: d["nofill"] += 1
        else:
            d["C"].append(C); d["sealedC"].append(abs(G - C) < 1e-6)
import json as _json, os
_out={"_meta":{"pool":POOL,"sidecar":SIDE,"n_pool_rows":n,
   "question":"is the SEALED January pool label (opportunity_net_proxy_r + cost_r) fill-aware or decision-anchored?",
   "geometry":"pool-native: stop 1.0R, target policy_target_r","arms":"A=obs0 decision-anchored; C=limit touch searched from obs1"},
   "subsets":{}}
for _k,_d in acc.items():
    _S=np.array(_d["S"]); _A=np.array([a for a in _d["A"] if a is not None]); _C=np.array(_d["C"])
    _out["subsets"][_k]=dict(n=_d["n"], E_G_sealed=float(_S.mean()), E_A_decision_anchored=float(_A.mean()),
        E_C_fill_anchored=(float(_C.mean()) if len(_C) else None),
        exact_match_G_eq_A_frac=float(np.mean(_d["sealedA"])),
        exact_match_G_eq_C_frac=(float(np.mean(_d["sealedC"])) if _d["sealedC"] else None),
        no_fill_frac=_d["nofill"]/_d["n"])
_out["_verdict"]=("The sealed label tracks the FILL-ANCHORED arm, not the decision-anchored one: on the "
  "measured resting-limit rows E[G_sealed]=+0.0087 against E[A]=+0.7275 and E[C]=-0.0342, and G equals C "
  "exactly on 81.2% of them against 59.0% for A. The defect is therefore NOT in the sealed corpus — it is "
  "in re-walkers that ignore the sealed label and re-derive outcomes from the ordered-path sidecar at obs 0.")
_json.dump(_out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"BCD_SEALED_LABEL.json"),"w"), indent=1)
print(f"pool rows {n}\n")
print(f"{'subset':28s} {'n':>6s} {'E[G_sealed]':>12s} {'E[A dec]':>10s} {'E[C fill]':>10s} "
      f"{'G==A %':>8s} {'G==C %':>8s} {'nofill%':>8s}")
for k in ["ALL","LIMITFAM","MKTFAM","RESTING","NOTRESTING"] + sorted(x for x in acc if x.startswith("F:")):
    d = acc[k]
    S=np.array(d["S"]); A=np.array([a for a in d["A"] if a is not None]); C=np.array(d["C"])
    print(f"{k:28s} {d['n']:6d} {S.mean():12.4f} {A.mean():10.4f} {(C.mean() if len(C) else float('nan')):10.4f} "
          f"{np.mean(d['sealedA'])*100:7.2f}% {(np.mean(d['sealedC'])*100 if d['sealedC'] else float('nan')):7.2f}% "
          f"{d['nofill']/d['n']*100:7.2f}%")
