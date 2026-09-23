"""w0-capture VERIFY: independent re-derivation of the entry-fill mechanism.

Offline. Reads only the wave-0 working set + R-paths (both derived from CJ pool + CQ sidecar).
No broker module, no sealed route write, no April/May pack.

Sign convention (w0_WORKING_SET_README): fav=(high-entry)/d LONG, (entry-low)/d SHORT;
adv=(low-entry)/d LONG, (entry-high)/d SHORT.  d=|entry-stop|>0.  Both signed for the side.

  limit TOUCH at bar k      <=>  adv(k) <= 0        (price reaches the limit from either side)
  GAP-THROUGH at that bar   <=>  fav(k) <  0        (the WHOLE bar is past the limit -> the
                                                     market was already on the far side; a
                                                     resting limit could not have been there)
"""
import sys, json, math, statistics as st
from collections import defaultdict
D = "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0, D)
import w0_ws

rows = {w0_ws.key(r): r for r in w0_ws.load()}
TOL = 1e-3

def dist(v):
    v = sorted(v)
    if not v: return None
    n = len(v)
    q = lambda p: v[min(n-1, int(p*n))]
    return {"n": n, "mean": sum(v)/n, "p05": q(.05), "p25": q(.25), "median": q(.50),
            "p75": q(.75), "p90": q(.90), "p95": q(.95), "min": v[0], "max": v[-1]}

def walk(fav, adv, start, target, wall):
    """plain 2R/-1R first-touch walk from bar `start` (inclusive), wall = last bar index+1."""
    end = min(len(fav), wall)
    for k in range(start, end):
        t = fav[k] >= target - 1e-9
        s = adv[k] <= -1.0 + 1e-9
        if t and s: return -1.0, "same_bar_conservative_stop", k
        if t: return target, "target", k
        if s: return -1.0, "stop_1R", k
    if end <= start: return None, "no_bars", None
    return None, "mark", end-1   # caller supplies close mark

out = {}
cls = {}          # key -> dict of fill facts
markr = {}
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = rows.get(k)
    if r is None: continue
    fav, adv, clsr = rp["fav"], rp["adv"], rp["cls"]
    tgt = r.get("policy_target_r") or 2.0
    tgt = float(tgt)
    # --- entry-fill classification ---
    touch = None
    for i, a in enumerate(adv):
        if a <= 0.0 + 1e-12:
            touch = i; break
    if touch is None:
        cls[k] = {"fill": "never", "touch": None, "gap": None}
        continue
    gap = fav[touch] < 0.0
    cls[k] = {"fill": "gap" if gap else "clean", "touch": touch, "gap": gap,
              "fav_at_touch": fav[touch]}
    # --- three walks from the touch bar, wall at 120 bars ---
    W = len(fav)
    fr, reason, bar = walk(fav, adv, touch, tgt, W)
    if fr is None and reason == "mark":
        fr = max(-1.0, min(clsr[bar], tgt)); reason = "mark_at_horizon"
    cls[k]["strict_r"] = fr; cls[k]["strict_reason"] = reason
    # engine-equivalent: walk from bar 0 (the engine does not wait for the limit)
    fr0, reason0, bar0 = walk(fav, adv, 0, tgt, W)
    if fr0 is None and reason0 == "mark":
        fr0 = max(-1.0, min(clsr[bar0], tgt)); reason0 = "mark_at_horizon"
    cls[k]["frombar0_r"] = fr0; cls[k]["frombar0_reason"] = reason0
    # mfe before first stop, from the touch bar
    mfe_pre_stop = None
    run = -9e9
    for j in range(touch, W):
        run = max(run, fav[j])
        if adv[j] <= -1.0 + 1e-9:
            mfe_pre_stop = run; break
    cls[k]["mfe_before_stop_from_touch"] = mfe_pre_stop
    cls[k]["mfe_from_touch"] = max(fav[touch:]) if touch < W else None

json.dump({"n_classified": len(cls)}, open("/dev/null","w"))

# ---------------- books ----------------
def book(sel, field="gross_r", src=None):
    g = []
    for k, r in rows.items():
        if not sel(k, r): continue
        v = r.get(field) if src is None else src(k)
        if v is None or not isinstance(v,(int,float)) or not math.isfinite(v): continue
        g.append(float(v))
    if not g: return None
    n = len(g); w = [x for x in g if x > TOL]; l = [x for x in g if x <= TOL]
    mw = sum(w)/len(w) if w else 0.0; ml = sum(l)/len(l) if l else 0.0
    be = (-ml)/(mw-ml) if (mw-ml) else None
    return {"n": n, "gross_mean_R": sum(g)/n, "win_rate": len(w)/n,
            "mean_winner_R": mw, "mean_loser_R": ml,
            "payoff": (mw/-ml) if ml else None, "breakeven_win_rate": be,
            "win_minus_breakeven_pp": (len(w)/n - be)*100 if be else None}

C = lambda k: cls.get(k, {})
res = {}
res["ENGINE_recorded_ALL"]        = book(lambda k,r: True)
res["ENGINE_recorded_CLEAN"]      = book(lambda k,r: C(k).get("fill")=="clean")
res["ENGINE_recorded_GAP"]        = book(lambda k,r: C(k).get("fill")=="gap")
res["ENGINE_recorded_NEVERTOUCH"] = book(lambda k,r: C(k).get("fill")=="never")
res["STRICT_clean_only_filled"]   = book(lambda k,r: C(k).get("fill")=="clean", src=lambda k: C(k).get("strict_r"))
res["STRICT_clean_unfilled_as_0"] = book(lambda k,r: True,
        src=lambda k: C(k).get("strict_r") if C(k).get("fill")=="clean" else 0.0)
res["WALKFROMBAR0_ALL"]           = book(lambda k,r: True, src=lambda k: C(k).get("frombar0_r"))
res["WALKFROMTOUCH_ALL_incl_gap"] = book(lambda k,r: C(k).get("fill") in ("clean","gap"), src=lambda k: C(k).get("strict_r"))

fillcnt = defaultdict(int)
for k in rows: fillcnt[C(k).get("fill")] += 1
res["_fill_census"] = dict(fillcnt)
res["_touch_bar_dist_clean"] = dist([C(k)["touch"]+1 for k in rows if C(k).get("fill")=="clean"])
res["_fav_at_touch_gap"] = dist([C(k)["fav_at_touch"] for k in rows if C(k).get("fill")=="gap"])
rr = defaultdict(int)
for k in rows:
    if C(k).get("fill")=="clean": rr[C(k).get("strict_reason")] += 1
res["_strict_exit_reasons_clean"] = dict(rr)
rr0 = defaultdict(int)
for k in rows: rr0[C(k).get("frombar0_reason")] += 1
res["_frombar0_exit_reasons"] = dict(rr0)

json.dump(res, open(D+"/W0CAP_VERIFY_V1.json","w"), indent=1, default=str)
for k,v in res.items():
    if k.startswith("_"): print(k, "=", str(v)[:200])
    else: print(f"{k:32s} n={v['n']:6d} gross={v['gross_mean_R']:+.4f} win={v['win_rate']:.4f} "
                f"be={v['breakeven_win_rate']:.4f} W={v['mean_winner_R']:+.3f} L={v['mean_loser_R']:+.3f}")
