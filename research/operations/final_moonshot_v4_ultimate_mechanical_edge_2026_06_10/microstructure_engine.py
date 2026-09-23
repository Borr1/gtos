"""Microstructure engine v2 — the market-maker-wave layer, recalibrated.

Recalibrations from owner feedback (2026-06-13):
  - REAL per-asset-class cost from ULTIMATE_REAL_COST_MAP.json (filled trades),
    not the inflated 0.17 proxy. fx .16 / jpy .11 / index .064 / metals .046 /
    energy .037.
  - DEVELOP candidates: BH is a confidence LABEL, not a kill switch. Output a
    ranked book of every setup x exit with reconciled real-cost numbers,
    edge-over-beta, out-of-sample, and sub-period stability so nothing dies on
    a single strict gate.

Setups (named directional hypotheses), volume-aware:
  S1 stop_run_reversal : sweep prior 20-extreme on rel_vol>=1.5, close back
                         inside -> fade the grab.
  S2 dry_exhaustion    : trend + range-extreme on DRY volume -> reversion
                         (the jpy finding from v1).
  S3 participation_break: pos crosses extreme on volume SURGE + expansion ->
                         continuation (momentum WITH participation).
  S4 absorption_reversal: range-extreme + absorption (big vol, small range) ->
                         reversion (limit wall).
  S5 vdelta_divergence : new price extreme but volume-delta proxy weakening ->
                         reversal.

Exits compared per setup: fixed-time(H); vol_exhaustion (exit when rel_vol
fades < 0.7 after elevation, or an opposing volume-delta bar); atr_trail.

Episode semantics; regime baseline (always-long/short per asset class,horizon)
subtracted; TRAIN 2022..2025, VALIDATION 2026-01..04, 2026-05+ untouched.
Replay/proxy evidence; research-only; no broker calls.
"""
import csv, json, math, statistics, sys, collections, argparse
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GLOBAL_COST = COST.get("_global_median", 0.095)
STOP_ATR = 2.5
BH_Q = 0.10


def cost_for(ac):
    return float(COST.get(ac, GLOBAL_COST))


def load(f):
    rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]), float(r["low"]),
             float(r["close"]), float(r["volume"]))
            for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
    return rows


def run(timeframe, dirpath, suffix, horizons):
    train = collections.defaultdict(list)
    val = collections.defaultdict(list)
    sub = collections.defaultdict(lambda: collections.defaultdict(list))  # period sign stability
    base_l = collections.defaultdict(list); base_s = collections.defaultdict(list)
    n_eps = 0
    maxh = max(horizons)
    for f in sorted(Path(dirpath).glob(f"*{suffix}")):
        symbol = f.name[:-len(suffix)]
        ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
        if ac is None:
            continue
        c = cost_for(ac)
        rows = load(f)
        if len(rows) < 250:
            continue
        T=[r[0] for r in rows]; O=[r[1] for r in rows]; H=[r[2] for r in rows]
        L=[r[3] for r in rows]; C=[r[4] for r in rows]; V=[r[5] for r in rows]
        rng=[H[k]-L[k] for k in range(len(rows))]
        tr=[0.0]*len(rows)
        for i in range(1,len(rows)):
            tr[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
        # volume-delta proxy: signed participation per bar
        vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(len(rows))]

        def sma(arr,i,n): return sum(arr[i-n+1:i+1])/n

        def exit_net(i, atr, d, mode, h):
            stop = C[i]-d*STOP_ATR*atr
            end = min(i+h, len(rows)-1)
            for j in range(i+1, end+1):
                if d>0 and L[j]<=stop: return -STOP_ATR-c
                if d<0 and H[j]>=stop: return -STOP_ATR-c
                if mode=="vol_exhaust" and j>=i+2:
                    relv=V[j]/(sma(V,j,20) or 1)
                    if relv<0.7 or (d>0 and vd[j]<0 and abs(vd[j])>0.5*(sma(V,j,20) or 1)) \
                       or (d<0 and vd[j]>0 and abs(vd[j])>0.5*(sma(V,j,20) or 1)):
                        return d*(C[j]-C[i])/atr - c
                if mode=="atr_trail":
                    if d>0: stop=max(stop, H[j]-1.0*atr)
                    else:   stop=min(stop, L[j]+1.0*atr)
            return d*(C[end]-C[i])/atr - c

        prev=None
        for i in range(60, len(rows)-maxh):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            mo=T[i][:7]
            if mo>="2026-05": continue
            m20=sma(C,i,20); m50=sma(C,i,50)
            trend="up" if m20>m50*1.001 else ("down" if m20<m50*0.999 else "flat")
            hi,lo=max(H[i-47:i+1]),min(L[i-47:i+1])
            pos=(C[i]-lo)/(hi-lo) if hi>lo else 0.5
            posb="low" if pos<0.25 else ("high" if pos>0.75 else "mid")
            relv=V[i]/(sma(V,i,20) or 1)
            eff=rng[i]/V[i] if V[i]>0 else 0
            beff=sma([rng[k]/V[k] if V[k]>0 else 0 for k in range(i-19,i+1)],19,20) if i>=20 else eff
            absb= eff<=beff*0.6 if beff>0 else False
            expb= eff>=beff*1.4 if beff>0 else False
            ph,pl=max(H[i-20:i]),min(L[i-20:i])
            swh=H[i]>ph and C[i]<ph and relv>=1.5
            swl=L[i]<pl and C[i]>pl and relv>=1.5
            vdacc=sum(vd[i-2:i+1])
            # setups -> (direction, name)
            cands=[]
            if swl: cands.append((+1,"S1_stop_run_reversal"))
            if swh: cands.append((-1,"S1_stop_run_reversal"))
            if relv<=0.6 and trend=="down" and posb=="low": cands.append((+1,"S2_dry_exhaustion"))
            if relv<=0.6 and trend=="up" and posb=="high": cands.append((-1,"S2_dry_exhaustion"))
            if relv>=1.8 and expb and posb=="high" and C[i]>O[i]: cands.append((+1,"S3_participation_break"))
            if relv>=1.8 and expb and posb=="low" and C[i]<O[i]: cands.append((-1,"S3_participation_break"))
            if absb and posb=="low": cands.append((+1,"S4_absorption_reversal"))
            if absb and posb=="high": cands.append((-1,"S4_absorption_reversal"))
            if posb=="high" and vdacc<0: cands.append((-1,"S5_vdelta_divergence"))
            if posb=="low" and vdacc>0: cands.append((+1,"S5_vdelta_divergence"))
            is_entry = (trend,posb,relv>=1.5,bool(swh or swl)) != prev
            prev=(trend,posb,relv>=1.5,bool(swh or swl))
            for h in horizons:
                if i % maxh == 0:
                    base_l[(ac,h)].append(exit_net(i,atr,+1,"fixed",h))
                    base_s[(ac,h)].append(exit_net(i,atr,-1,"fixed",h))
            if not is_entry: continue
            n_eps+=1
            for d,name in cands:
                for h in horizons:
                    for mode in ("fixed","vol_exhaust","atr_trail"):
                        net=exit_net(i,atr,d,mode,h)
                        key=(ac,name,"long" if d>0 else "short",h,mode)
                        (val if mo>="2026-01" else train)[key].append(net)
                        per = "2022H1" if T[i]<"2022-07" else ("2022H2" if T[i]<"2023-01" else T[i][:4])
                        if mo<"2026-01": sub[key][per].append(net)
    bl={k:statistics.fmean(v) for k,v in base_l.items() if v}
    bs={k:statistics.fmean(v) for k,v in base_s.items() if v}
    tested=[]
    for key,vals in train.items():
        if len(vals)<60: continue
        ac,name,direction,h,mode=key
        beta=bl.get((ac,h),0) if direction=="long" else bs.get((ac,h),0)
        m=statistics.fmean(vals); sd=statistics.pstdev(vals)
        if sd<=0: continue
        edge=m-beta; et=edge/(sd/math.sqrt(len(vals)))
        p=2*(1-0.5*(1+math.erf(abs(et)/math.sqrt(2))))
        persign=[1 if statistics.fmean(v)-beta>0 else -1 for v in sub[key].values() if len(v)>=15]
        stab=round(sum(1 for s in persign if s== (1 if edge>0 else -1))/len(persign),2) if persign else None
        v=val.get(key,[])
        vedge=(statistics.fmean(v)-beta) if len(v)>=10 else None
        tested.append({"key":list(key),"n":len(vals),"raw_r":round(m,4),"beta":round(beta,4),
            "edge_r":round(edge,4),"edge_t":round(et,2),"p":p,"subperiod_stability":stab,
            "val_n":len(v),"val_edge_r":round(vedge,4) if vedge is not None else None,
            "val_same_sign":(None if vedge is None else (vedge>0)==(edge>0))})
    tested.sort(key=lambda r:r["p"]); mt=len(tested); mk=0
    for k,r in enumerate(tested,1):
        if r["p"]<=BH_Q*k/mt: mk=k
    for idx,r in enumerate(tested): r["bh_pass"]=idx<mk
    # rank book: positive edge, OOS same-sign, decent stability, sorted by edge
    book=[r for r in tested if r["edge_r"]>0 and r["val_same_sign"] and (r["subperiod_stability"] or 0)>=0.5]
    book.sort(key=lambda r:-r["edge_r"])
    return {"timeframe":timeframe,"episodes":n_eps,"cells_tested":mt,"bh_survivors":mk,
            "developed_book_n":len(book),"book":book[:40],
            "all_positive_oos":sum(1 for r in tested if r["edge_r"]>0 and r["val_same_sign"])}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tf",choices=["h4","m15"],default="h4")
    a=ap.parse_args()
    if a.tf=="h4":
        res=run("H4", REPO_ROOT/"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026","_H4.csv",(3,6,12,24))
        outp=ROUTE/"ULTIMATE_MICROSTRUCTURE_ENGINE_H4.json"
    else:
        # M15: union of standard + ext monthly packages, recent ~year for speed
        import glob
        res={"timeframe":"M15","note":"see per-dir mining"}
        # mine the deep H4 path is primary; M15 handled by separate aggregation if needed
        d=REPO_ROOT/"data/mt5_research_exports"
        res=run("M15", d/"bridge_ftmo_m15_20250601_20260610","_M15.csv",(8,16,32,64))
        outp=ROUTE/"ULTIMATE_MICROSTRUCTURE_ENGINE_M15.json"
    res.update({"real_cost_map":COST,"broker_operation":False,"paid_api_or_vendor_call":False,
                "broker_runtime_change_status":False,"validation_result_status":False,
                "outcome_result_rows_status":False})
    outp.write_text(json.dumps(res,indent=1,sort_keys=True))
    print(json.dumps({k:res[k] for k in ("timeframe","episodes","cells_tested","bh_survivors","developed_book_n","all_positive_oos")},sort_keys=True))
    for r in res["book"][:12]:
        print(f"  {r['key']}  edge {r['edge_r']:+.3f}R t={r['edge_t']} stab={r['subperiod_stability']} val {r['val_edge_r']:+.3f}R n={r['n']}/{r['val_n']} bh={r['bh_pass']}")


if __name__=="__main__":
    main()
