"""Adversarial robustness dossier for top microstructure-engine candidates.

For each candidate (ac, setup, direction, horizon, exit_mode) from the H4
developed book, recompute the full episode stream tagged by symbol+date and
run the gauntlet that killed every prior false positive:

  - bootstrap_ci    : 2000x resample of episode nets -> edge 5th pct (must be >0)
  - per_symbol      : edge by symbol (is it 1 symbol or the whole class?)
  - subperiod       : net by 2022H1/H2/2023/24/25 + validation 2026
  - cost_stress     : edge at 1.0x / 1.5x / 2.0x real cost
  - beta_robust     : edge over a TREND-CONDITIONAL baseline (only count
                      unconditional exposure in the same trend regime) — the
                      fairest beta, the one that killed metals continuation.

Deterministic bootstrap (seeded by index, no RNG). Research/proxy evidence.
"""
import csv, json, math, statistics, sys, collections
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GLOBAL_COST = COST.get("_global_median", 0.095)
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
STOP_ATR = 2.5
HORIZONS = (3, 6, 12, 24)
MAXH = 24


def cost_for(ac): return float(COST.get(ac, GLOBAL_COST))


def detect(O, H, L, C, V, rng, tr, vd, i):
    def sma(a, n): return sum(a[i - n + 1:i + 1]) / n
    atr = sum(tr[i - 13:i + 1]) / 14
    if atr <= 0: return None, []
    m20, m50 = sma(C, 20), sma(C, 50)
    trend = "up" if m20 > m50 * 1.001 else ("down" if m20 < m50 * 0.999 else "flat")
    hi, lo = max(H[i - 47:i + 1]), min(L[i - 47:i + 1])
    pos = (C[i] - lo) / (hi - lo) if hi > lo else 0.5
    posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    relv = V[i] / (sma(V, 20) or 1)
    eff = rng[i] / V[i] if V[i] > 0 else 0
    beff = (sum((rng[k] / V[k] if V[k] > 0 else 0) for k in range(i - 19, i + 1)) / 20)
    absb = eff <= beff * 0.6 if beff > 0 else False
    expb = eff >= beff * 1.4 if beff > 0 else False
    ph, pl = max(H[i - 20:i]), min(L[i - 20:i])
    swh = H[i] > ph and C[i] < ph and relv >= 1.5
    swl = L[i] < pl and C[i] > pl and relv >= 1.5
    vdacc = sum(vd[i - 2:i + 1])
    cands = []
    if swl: cands.append((+1, "S1_stop_run_reversal"))
    if swh: cands.append((-1, "S1_stop_run_reversal"))
    if relv <= 0.6 and trend == "down" and posb == "low": cands.append((+1, "S2_dry_exhaustion"))
    if relv <= 0.6 and trend == "up" and posb == "high": cands.append((-1, "S2_dry_exhaustion"))
    if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]: cands.append((+1, "S3_participation_break"))
    if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]: cands.append((-1, "S3_participation_break"))
    if absb and posb == "low": cands.append((+1, "S4_absorption_reversal"))
    if absb and posb == "high": cands.append((-1, "S4_absorption_reversal"))
    if posb == "high" and vdacc < 0: cands.append((-1, "S5_vdelta_divergence"))
    if posb == "low" and vdacc > 0: cands.append((+1, "S5_vdelta_divergence"))
    return trend, cands


def net_for(O, H, L, C, V, rng, tr, vd, i, atr, d, mode, h, c):
    def sma(a, n): return sum(a[i - n + 1:i + 1]) / n
    stop = C[i] - d * STOP_ATR * atr
    end = min(i + h, len(C) - 1)
    for j in range(i + 1, end + 1):
        if d > 0 and L[j] <= stop: return -STOP_ATR - c
        if d < 0 and H[j] >= stop: return -STOP_ATR - c
        if mode == "vol_exhaust" and j >= i + 2:
            relv = V[j] / (sum(V[j - 19:j + 1]) / 20 or 1)
            base = sum(V[j - 19:j + 1]) / 20 or 1
            if relv < 0.7 or (d > 0 and vd[j] < 0 and abs(vd[j]) > 0.5 * base) \
               or (d < 0 and vd[j] > 0 and abs(vd[j]) > 0.5 * base):
                return d * (C[j] - C[i]) / atr - c
        if mode == "atr_trail":
            if d > 0: stop = max(stop, H[j] - 1.0 * atr)
            else: stop = min(stop, L[j] + 1.0 * atr)
    return d * (C[end] - C[i]) / atr - c


def collect(targets):
    # targets: set of (ac,setup,direction,h,mode)
    streams = collections.defaultdict(list)   # target -> [(symbol,date,net,trend)]
    beta_trend = collections.defaultdict(list)  # (ac,h,dir,trend) -> net (unconditional)
    for f in sorted(D.glob("*_H4.csv")):
        symbol = f.name[:-7]; ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
        if ac is None: continue
        if not any(t[0] == ac for t in targets): continue
        c = cost_for(ac)
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"]))
                for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows) < 250: continue
        T=[x[0] for x in rows];O=[x[1] for x in rows];H=[x[2] for x in rows]
        L=[x[3] for x in rows];C=[x[4] for x in rows];V=[x[5] for x in rows]
        rng=[H[k]-L[k] for k in range(len(rows))]; tr=[0.0]*len(rows)
        for i in range(1,len(rows)): tr[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
        vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(len(rows))]
        prev=None
        for i in range(60,len(rows)-MAXH):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            res=detect(O,H,L,C,V,rng,tr,vd,i)
            if res[0] is None: continue
            trend,cands=res
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1)
            ph,pl=max(H[i-20:i]),min(L[i-20:i])
            swh=H[i]>ph and C[i]<ph and relv>=1.5; swl=L[i]<pl and C[i]>pl and relv>=1.5
            m20=sum(C[i-19:i+1])/20; m50=sum(C[i-49:i+1])/50
            hi,lo=max(H[i-47:i+1]),min(L[i-47:i+1]); pos=(C[i]-lo)/(hi-lo) if hi>lo else .5
            posb="low" if pos<.25 else ("high" if pos>.75 else "mid")
            is_entry=(trend,posb,relv>=1.5,bool(swh or swl))!=prev
            prev=(trend,posb,relv>=1.5,bool(swh or swl))
            for h in HORIZONS:
                if i%MAXH==0:
                    beta_trend[(ac,h,"long",trend)].append(net_for(O,H,L,C,V,rng,tr,vd,i,atr,+1,"fixed",h,c))
                    beta_trend[(ac,h,"short",trend)].append(net_for(O,H,L,C,V,rng,tr,vd,i,atr,-1,"fixed",h,c))
            if not is_entry: continue
            for d,name in cands:
                for h in HORIZONS:
                    for mode in ("fixed","vol_exhaust","atr_trail"):
                        key=(ac,name,"long" if d>0 else "short",h,mode)
                        if key in targets:
                            streams[key].append((symbol,T[i][:10],net_for(O,H,L,C,V,rng,tr,vd,i,atr,d,mode,h,c),trend))
    return streams, beta_trend


def boot_ci(vals, lo_pct=5, n=2000):
    # genuine with-replacement resample via deterministic LCG (repeats allowed)
    if len(vals) < 20: return None
    L=len(vals); means=[]; state=2463534242
    for b in range(n):
        s=0.0
        for k in range(L):
            state=(state*1103515245+12345)&0x7fffffff
            s+=vals[state % L]
        means.append(s/L)
    means.sort()
    return round(means[int(lo_pct/100*n)],4)


def period(dt): return "2022H1" if dt<"2022-07" else ("2022H2" if dt<"2023-01" else dt[:4])


def main():
    eng=json.loads((ROUTE/"ULTIMATE_MICROSTRUCTURE_ENGINE_H4.json").read_text())
    # top 15 by edge among large-enough, stable book entries
    book=[b for b in eng["book"] if b["n"]>=80 and (b["subperiod_stability"] or 0)>=0.5]
    book=book[:15]
    targets={tuple(b["key"]) for b in book}
    streams,beta_trend=collect(targets)
    dossier=[]
    for b in book:
        key=tuple(b["key"]); ac,name,direction,h,mode=key
        rows=streams.get(key,[])
        train=[r for r in rows if r[1]<"2026-01"]; val=[r for r in rows if r[1]>="2026-01" and r[1]<"2026-05"]
        tn=[r[2] for r in train]; vn=[r[2] for r in val]
        # trend-conditional beta: avg over the trends actually traded
        trends=collections.Counter(r[3] for r in train)
        bt=[]
        for tr_,cnt in trends.items():
            base=beta_trend.get((ac,h,direction,tr_),[])
            if base: bt += base*1
        beta=statistics.fmean(bt) if bt else 0.0
        edge=statistics.fmean(tn)-beta if tn else None
        persym=collections.defaultdict(list)
        for s,_,nt,_ in train: persym[s].append(nt)
        sym_edge={s:round(statistics.fmean(v)-beta,3) for s,v in persym.items() if len(v)>=20}
        sub={}
        pp=collections.defaultdict(list)
        for _,dt,nt,_ in train: pp[period(dt)].append(nt)
        for per,v in pp.items():
            if len(v)>=15: sub[per]=round(statistics.fmean(v)-beta,3)
        c=cost_for(ac)
        def edge_at(mult):
            extra=(mult-1)*c
            return round(statistics.fmean([x-extra for x in tn])-beta,4) if tn else None
        dossier.append({"key":list(key),"train_n":len(tn),"val_n":len(vn),
            "trend_conditional_beta":round(beta,4),
            "edge_vs_trend_beta":round(edge,4) if edge is not None else None,
            "bootstrap_edge_p05":boot_ci([x-beta for x in tn]),
            "val_edge":round(statistics.fmean(vn)-beta,4) if vn else None,
            "per_symbol_edge":sym_edge,"n_symbols_positive":sum(1 for e in sym_edge.values() if e>0),
            "n_symbols":len(sym_edge),"subperiod_edge":sub,
            "cost_stress":{"1.0x":edge_at(1.0),"1.5x":edge_at(1.5),"2.0x":edge_at(2.0)}})
    out={"schema_version":"microstructure_verification_dossier_v1","candidates":dossier,
         "broker_operation":False,"paid_api_or_vendor_call":False,"broker_runtime_change_status":False,
         "validation_result_status":False,"outcome_result_rows_status":False}
    (ROUTE/"ULTIMATE_MICROSTRUCTURE_VERIFICATION.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    for d in dossier:
        print(f"  {d['key']}  edge_vs_trendbeta {d['edge_vs_trend_beta']:+.3f} boot_p05 {d['bootstrap_edge_p05']} "
              f"val {d['val_edge']} syms+{d['n_symbols_positive']}/{d['n_symbols']} cost2x {d['cost_stress']['2.0x']}")


if __name__=="__main__":
    main()
