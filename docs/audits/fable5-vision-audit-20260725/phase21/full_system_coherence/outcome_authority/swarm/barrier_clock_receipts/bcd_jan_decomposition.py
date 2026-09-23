#!/usr/bin/env python3
"""BARRIER-CLOCK DEFECT — three-arm decomposition on the sealed January pool.

ARM A  DECISION_ANCHORED : barriers walk from the SUBMISSION M1 bar (obs 0). The defect as walked.
ARM B  CAUSAL_MARKET     : barriers walk from the first COMPLETE successor bar (obs 1).
                           Isolates sub-defect (i): the submission interval is not causal.
                           This is the correct contract for a MARKET order (quote_side.py:1281-1290).
ARM C  FILL_ANCHORED     : for a resting limit, the clock starts when the limit is touched,
                           searching from obs 1; never touched -> NO_FILL.
                           This is the correct contract for a LIMIT order (quote_side.py:1291-1330).
Read-only. Writes /private/tmp/bcd/BCD_DECOMP_JAN.json
"""
import gzip, json, math
from collections import defaultdict
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
POOL = f"{REPO}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
SIDE = f"{REPO}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
TOL = 1e-9
LIMFAM = {"current_ob_retest", "current_fvg_fill", "current_breaker_re_entry"}

rows = []
n = 0
for pl, sl in zip(gzip.open(POOL, 'rt'), gzip.open(SIDE, 'rt')):
    if not pl.strip(): continue
    p = json.loads(pl); s = json.loads(sl); n += 1
    assert str(p["candidate_id"]) == str(s["candidate_id"])
    E = float(p["entry_price"]); S = float(p["stop_loss"]); T = float(p["take_profit_1"])
    D = abs(E - S)
    obs = s["ordered_path_observations"]
    if not (math.isfinite(D) and D > 0) or len(obs) < 2: continue
    sgn = 1.0 if str(p["side"]).upper() == "LONG" else -1.0
    rows.append(dict(fam=str(p["origin_family"]), ot=str(p.get("effective_order_type")),
        frc=str(p.get("fill_realism_class")), sgn=sgn, E=E, S=S, T=T, D=D, rr=abs(T-E)/D,
        hi=np.fromiter((float(o["high"]) for o in obs), np.float64),
        lo=np.fromiter((float(o["low"]) for o in obs), np.float64),
        op=np.fromiter((float(o["open"]) for o in obs), np.float64),
        cl=float(obs[-1]["close"]), cost=float(p.get("cost_r") or 0.0),
        day=str(p["decision_time_utc"])[:10]))
print("walked", len(rows), "of", n)

def walk(r, start):
    hi, lo = r["hi"][start:], r["lo"][start:]
    if len(hi) == 0: return None, "NO_PATH"
    sgn, S, T, E, D = r["sgn"], r["S"], r["T"], r["E"], r["D"]
    hs = (lo <= S + TOL) if sgn > 0 else (hi >= S - TOL)
    ht = (hi >= T - TOL) if sgn > 0 else (lo <= T + TOL)
    si = int(np.argmax(hs)) if hs.any() else len(hi)
    ti = int(np.argmax(ht)) if ht.any() else len(hi)
    if si == len(hi) and ti == len(hi): return (r["cl"] - E) * sgn / D, "HORIZON"
    if ti < si: return r["rr"], "TARGET"
    return -1.0, ("STOP" if si < ti else "AMBIG")

def touch_from(r, start):
    lo, hi = r["lo"][start:], r["hi"][start:]
    w = np.flatnonzero(lo <= r["E"] + TOL) if r["sgn"] > 0 else np.flatnonzero(hi >= r["E"] - TOL)
    return (start + int(w[0])) if len(w) else None

for r in rows:
    r["A"], r["Ao"] = walk(r, 0)
    r["B"], r["Bo"] = walk(r, 1)
    f = touch_from(r, 1); r["f"] = f
    r["C"], r["Co"] = (walk(r, f) if f is not None else (None, "NO_FILL"))
    r["marketable_at_submission"] = bool(
        (r["lo"][0] <= r["E"] + TOL) if r["sgn"] > 0 else (r["hi"][0] >= r["E"] - TOL))
    r["inst_target_A"] = bool((r["hi"][0] >= r["T"] - TOL) if r["sgn"] > 0 else (r["lo"][0] <= r["T"] + TOL))
    r["disp0"] = (r["op"][0] - r["E"]) * r["sgn"] / r["D"]

def boot(x, days, draws=4000):
    u = sorted(set(days.tolist())); rng = np.random.default_rng(20260811)
    by = {d: x[days == d] for d in u}; o = []
    for _ in range(draws):
        pick = rng.choice(len(u), len(u), replace=True)
        o.append(np.concatenate([by[u[i]] for i in pick]).mean())
    o = np.sort(np.asarray(o)); return [float(o[int(.025*draws)]), float(o[int(.975*draws)-1])]

def agg(sel, label):
    sel = [r for r in sel if r["A"] is not None and r["B"] is not None]
    if len(sel) < 5: return None
    days = np.array([r["day"] for r in sel]); cst = np.array([r["cost"] for r in sel])
    A = np.array([r["A"] for r in sel]); B = np.array([r["B"] for r in sel])
    filled = np.array([r["f"] is not None for r in sel])
    C = np.array([(r["C"] if r["C"] is not None else 0.0) for r in sel])
    nA, nB, nC = A - cst, B - cst, C - cst * filled
    return dict(label=label, n=len(sel), n_days=len(set(days.tolist())),
        A_decision_anchored=dict(gross=float(A.mean()), net=float(nA.mean()), net_ci95=boot(nA, days)),
        B_causal_market=dict(gross=float(B.mean()), net=float(nB.mean()), net_ci95=boot(nB, days)),
        C_fill_anchored=dict(gross=float(C.mean()), net=float(nC.mean()), net_ci95=boot(nC, days),
                             no_fill=int((~filled).sum()), no_fill_frac=float((~filled).mean())),
        delta_A_minus_B=float(nA.mean() - nB.mean()),
        delta_A_minus_C=float(nA.mean() - nC.mean()),
        delta_B_minus_C=float(nB.mean() - nC.mean()),
        delta_A_minus_C_ci95=boot(nA - nC, days),
        marketable_at_submission_frac=float(np.mean([r["marketable_at_submission"] for r in sel])),
        instant_target_at_submission_frac=float(np.mean([r["inst_target_A"] for r in sel])),
        signed_disp0_D=dict(mean=float(np.mean([r["disp0"] for r in sel])),
                            median=float(np.median([r["disp0"] for r in sel])),
                            frac_favourable=float(np.mean([r["disp0"] > 0 for r in sel]))))

res = {}
res["ALL"] = agg(rows, "ALL")
res["ORDER_TYPE_limit"] = agg([r for r in rows if r["ot"] == "limit"], "effective_order_type=limit")
res["ORDER_TYPE_none"] = agg([r for r in rows if r["ot"] == "none"], "effective_order_type=none")
res["RESTING_limit_measured"] = agg([r for r in rows if r["ot"] == "limit" and not r["marketable_at_submission"]],
                                    "limit AND not marketable at submission (MEASURED)")
res["MARKETABLE_limit_measured"] = agg([r for r in rows if r["ot"] == "limit" and r["marketable_at_submission"]],
                                       "limit AND marketable at submission (MEASURED)")
res["LANEG_LIMIT_FAM"] = agg([r for r in rows if r["fam"] in LIMFAM], "laneG LIMIT families")
res["LANEG_MARKET_FAM"] = agg([r for r in rows if r["fam"] not in LIMFAM], "laneG MARKET families")
res["LANEG_MARKET_FAM_but_limit_row"] = agg(
    [r for r in rows if r["fam"] not in LIMFAM and r["ot"] == "limit"], "laneG MARKET fam, row=limit")
res["LANEG_MARKET_FAM_but_resting_limit"] = agg(
    [r for r in rows if r["fam"] not in LIMFAM and r["ot"] == "limit" and not r["marketable_at_submission"]],
    "laneG MARKET fam, RESTING limit")
for fam in sorted({r["fam"] for r in rows}):
    res["FAM_" + fam] = agg([r for r in rows if r["fam"] == fam], fam)
    res["FAMRESTING_" + fam] = agg(
        [r for r in rows if r["fam"] == fam and r["ot"] == "limit" and not r["marketable_at_submission"]],
        fam + " | resting limit")
res["_meta"] = dict(pool=POOL, sidecar=SIDE, n_pool=n, n_walked=len(rows),
    arms="A=obs0 (as walked)  B=obs1 first complete successor (market-correct)  C=limit touch from obs1 (limit-correct)",
    geometry="row-own entry_price/stop_loss/take_profit_1", tie_rule="stop_wins", ci="day-block bootstrap 4000")
json.dump(res, open(__file__.rsplit("/",1)[0] + "/BCD_DECOMP_JAN.json", "w"), indent=1)

def line(k):
    v = res.get(k)
    if not v: return
    print(f"{v['label'][:44]:44s} n={v['n']:6d} mkt@sub {v['marketable_at_submission_frac']*100:5.1f}% "
          f"instT {v['instant_target_at_submission_frac']*100:5.2f}% | netA {v['A_decision_anchored']['net']:+8.4f} "
          f"netB {v['B_causal_market']['net']:+8.4f} netC {v['C_fill_anchored']['net']:+8.4f} | "
          f"A-B {v['delta_A_minus_B']:+7.4f}  A-C {v['delta_A_minus_C']:+7.4f}")
for k in ["ALL","ORDER_TYPE_limit","ORDER_TYPE_none","RESTING_limit_measured","MARKETABLE_limit_measured",
          "LANEG_LIMIT_FAM","LANEG_MARKET_FAM","LANEG_MARKET_FAM_but_limit_row","LANEG_MARKET_FAM_but_resting_limit"]:
    line(k)
print()
for fam in sorted({r["fam"] for r in rows}):
    line("FAM_" + fam); line("FAMRESTING_" + fam)
