"""P0 existential checks on the microstructure book (H4 deep data 2022-2026).

Attacks two red-team criticals on data already on disk:
 (1) GAP-INFLATED STOP: the engine filled stops at EXACTLY -2.5R. Here a stop
     touch fills at the WORSE of the stop or the bar's actual open/extreme
     (gap-through), plus a slippage buffer -> realized worst-case R. Re-measure
     each book leg's expectancy under honest tail fills.
 (2) BETA-NEUTRALIZED ATTRIBUTION: regress each leg's per-trade R on its
     asset-class trend factor (sign of SMA20-50 * forward move); report alpha
     (intercept), alpha t-stat, and beta. A leg whose edge is just regime beta
     has alpha ~0.

Run on the 2 book detectors (S4 absorption, S5 vdelta) across H4 deep history.
Replay/proxy; no broker calls.
"""
import csv, json, math, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GCOST = COST.get("_global_median", 0.095)
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
STOP_ATR = 2.5
SLIP_R = 0.10  # fixed adverse slippage buffer on stop fills (R)
H = 24


def main():
    # naive stop (-2.5R) vs gap-inflated stop, per (family, ac, side); plus beta attribution
    naive = collections.defaultdict(list); gapd = collections.defaultdict(list)
    legreturns = collections.defaultdict(list)   # (fam,ac,side)-> [(net, trendfactor)]
    for f in sorted(D.glob("*_H4.csv")):
        sym = f.name[:-7]; ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None: continue
        c = float(COST.get(ac, GCOST))
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"])) for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows) < 250: continue
        O=[x[1] for x in rows];Hh=[x[2] for x in rows];L=[x[3] for x in rows];C=[x[4] for x in rows];V=[x[5] for x in rows]
        rng=[Hh[i]-L[i] for i in range(len(rows))]; tr=[0.0]*len(rows)
        for i in range(1,len(rows)): tr[i]=max(Hh[i]-L[i],abs(Hh[i]-C[i-1]),abs(L[i]-C[i-1]))
        vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(len(rows))]
        prev=None
        for i in range(60,len(rows)-H):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            m20=sum(C[i-19:i+1])/20; m50=sum(C[i-49:i+1])/50
            hi,lo=max(Hh[i-47:i+1]),min(L[i-47:i+1]); pos=(C[i]-lo)/(hi-lo) if hi>lo else .5
            posb="low" if pos<.25 else ("high" if pos>.75 else "mid")
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1)
            eff=rng[i]/V[i] if V[i]>0 else 0
            beff=sum((rng[k]/V[k] if V[k]>0 else 0) for k in range(i-19,i+1))/20
            absb= eff<=0.6*beff if beff>0 else False
            vdacc=sum(vd[i-2:i+1])
            is_entry=(m20>m50,posb,relv>=1.5)!=prev; prev=(m20>m50,posb,relv>=1.5)
            if not is_entry or posb=="mid": continue
            cands=[]
            if absb and posb=="low": cands.append((+1,"S4_absorption"))
            if absb and posb=="high": cands.append((-1,"S4_absorption"))
            if posb=="high" and vdacc<0: cands.append((-1,"S5_vdelta"))
            if posb=="low" and vdacc>0: cands.append((+1,"S5_vdelta"))
            trend_up = m20>m50
            for d,fam in cands:
                stop = C[i]-d*STOP_ATR*atr
                # naive: stop hit -> -2.5R
                naive_net=None; gap_net=None
                for j in range(i+1,i+H+1):
                    if d>0 and L[j]<=stop:
                        naive_net=-STOP_ATR-c
                        fill=min(stop,O[j]) if O[j]<stop else stop  # gap-through at open
                        gap_net=d*(fill-C[i])/atr - c - SLIP_R; break
                    if d<0 and Hh[j]>=stop:
                        naive_net=-STOP_ATR-c
                        fill=max(stop,O[j]) if O[j]>stop else stop
                        gap_net=d*(fill-C[i])/atr - c - SLIP_R; break
                if naive_net is None:
                    naive_net=d*(C[i+H]-C[i])/atr-c; gap_net=naive_net
                key=(fam,ac,"long" if d>0 else "short")
                naive[key].append(naive_net); gapd[key].append(gap_net)
                # beta factor: did price trend continue in trade direction? sign(trend)*fwd
                fwd=(C[i+H]-C[i])/atr
                tf = fwd if trend_up else -fwd  # trend-aligned forward move (the beta)
                legreturns[key].append((naive_net, tf))
    out=[]
    for key in sorted(naive, key=lambda k:-statistics.fmean(gapd[k])):
        nv=naive[key]; gp=gapd[key]
        if len(nv)<60: continue
        # OLS alpha = mean(net) - beta*mean(tf); beta = cov/var
        nets=[x[0] for x in legreturns[key]]; tfs=[x[1] for x in legreturns[key]]
        mt=statistics.fmean(tfs); mn=statistics.fmean(nets)
        var=sum((t-mt)**2 for t in tfs)/len(tfs)
        cov=sum((nets[i]-mn)*(tfs[i]-mt) for i in range(len(nets)))/len(nets)
        beta=cov/var if var>0 else 0.0; alpha=mn-beta*mt
        resid=[nets[i]-(alpha+beta*tfs[i]) for i in range(len(nets))]
        sd_res=statistics.pstdev(resid) or 1e-9
        alpha_t=alpha/(sd_res/math.sqrt(len(nets)))
        out.append({"key":list(key),"n":len(nv),
                    "naive_mean_r":round(statistics.fmean(nv),4),
                    "gap_inflated_mean_r":round(statistics.fmean(gp),4),
                    "tail_cost_of_gaps_r":round(statistics.fmean(nv)-statistics.fmean(gp),4),
                    "beta":round(beta,4),"alpha_r":round(alpha,4),"alpha_t":round(alpha_t,2)})
    res={"schema_version":"p0_tail_and_beta_v1","stop_atr":STOP_ATR,"slip_buffer_r":SLIP_R,
         "horizon_h4":H,"rows":out,
         "legs_alpha_positive_t2":sum(1 for r in out if r["alpha_t"]>=2 and r["alpha_r"]>0),
         "legs_gap_inflated_positive":sum(1 for r in out if r["gap_inflated_mean_r"]>0),
         "broker_operation":False,"paid_api_or_vendor_call":False,"broker_runtime_change_status":False,
         "validation_result_status":False,"outcome_result_rows_status":False}
    (ROUTE/"ULTIMATE_P0_TAIL_AND_BETA.json").write_text(json.dumps(res,indent=1,sort_keys=True))
    print(json.dumps({k:res[k] for k in ("legs_alpha_positive_t2","legs_gap_inflated_positive")},sort_keys=True))
    for r in out[:20]:
        print(f"  {r['key']}  naive {r['naive_mean_r']:+.3f} gap {r['gap_inflated_mean_r']:+.3f} (tail -{r['tail_cost_of_gaps_r']:.3f}) | beta {r['beta']:+.3f} alpha {r['alpha_r']:+.3f} t={r['alpha_t']}")


if __name__=="__main__":
    main()
