"""Portfolio-capture test — the corrected lens (no leg-by-leg rejection).

The owner's insight: the moves go the right way (exit-oracle +0.72R bound,
76.8% paths positive) but we GIVE THEM BACK at the exit, and gating leg-by-leg
throws away the portfolio. So measure the FULL opportunity set as ONE managed
portfolio with CAPTURE exits, across the deep multi-regime history.

For ALL detected setups (S1 stop-run, S2 dry-exhaustion, S3 participation-
break [momentum], S4 absorption, S5 vdelta) on every symbol/side, compare two
exits on the same entries:
  GIVE_BACK : fixed close at horizon H (what we were measuring)
  CAPTURE   : trail after +1.0R trigger giving 0.5R back, cap 6R, disaster 2.5R
Real per-asset-class cost. Combine into a daily PORTFOLIO R, report per YEAR
(regime robustness) and per family contribution. No rejection — just: what
does the broad, well-managed book make?
"""
import csv, json, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GCOST = COST.get("_global_median", 0.095)
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
STOP_ATR = 2.5
H_GIVEBACK = 12
TRAIL_TRIG, TRAIL_GAP, CAP = 1.0, 0.5, 6.0


def capture_exit(O, Hh, L, C, i, d, atr, c, n):
    """Trail after +TRAIL_TRIG R: lock in, run to CAP, disaster at -STOP_ATR."""
    stop = C[i] - d * STOP_ATR * atr
    trailing = False
    end = min(i + 200, n - 1)
    for j in range(i + 1, end + 1):
        prog = d * (C[j] - C[i]) / atr
        # disaster / trail stop hit intrabar (use bar extreme against us)
        adverse = (L[j] if d > 0 else Hh[j])
        if (d > 0 and adverse <= stop) or (d < 0 and adverse >= stop):
            return d * (stop - C[i]) / atr - c
        if not trailing and prog >= TRAIL_TRIG:
            trailing = True
        if trailing:
            newstop = C[j] - d * TRAIL_GAP * atr
            stop = max(stop, newstop) if d > 0 else min(stop, newstop)
        if prog >= CAP:
            return CAP - c
    return d * (C[end] - C[i]) / atr - c


def giveback_exit(C, i, d, atr, c, n):
    end = min(i + H_GIVEBACK, n - 1)
    return d * (C[end] - C[i]) / atr - c


def main():
    # daily portfolio R under each exit; per-family/per-year contribution
    day_give = collections.defaultdict(float); day_cap = collections.defaultdict(float)
    fam_cap = collections.defaultdict(float); fam_give = collections.defaultdict(float)
    year_cap = collections.defaultdict(float); year_give = collections.defaultdict(float)
    n_trades = 0
    for f in sorted(D.glob("*_H4.csv")):
        sym = f.name[:-7]; ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None: continue
        c = float(COST.get(ac, GCOST))
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"])) for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows) < 250: continue
        n = len(rows)
        T=[x[0] for x in rows];O=[x[1] for x in rows];Hh=[x[2] for x in rows];L=[x[3] for x in rows];C=[x[4] for x in rows];V=[x[5] for x in rows]
        rng=[Hh[i]-L[i] for i in range(n)]; tr=[0.0]*n
        for i in range(1,n): tr[i]=max(Hh[i]-L[i],abs(Hh[i]-C[i-1]),abs(L[i]-C[i-1]))
        vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(n)]
        prev=None
        for i in range(60, n-1):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            m20=sum(C[i-19:i+1])/20; m50=sum(C[i-49:i+1])/50
            trend="up" if m20>m50*1.001 else ("down" if m20<m50*0.999 else "flat")
            hi,lo=max(Hh[i-47:i+1]),min(L[i-47:i+1]); pos=(C[i]-lo)/(hi-lo) if hi>lo else .5
            posb="low" if pos<.25 else ("high" if pos>.75 else "mid")
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1)
            eff=rng[i]/V[i] if V[i]>0 else 0; beff=sum((rng[k]/V[k] if V[k]>0 else 0) for k in range(i-19,i+1))/20
            absb= eff<=0.6*beff if beff>0 else False; expb= eff>=1.4*beff if beff>0 else False
            ph,pl=max(Hh[i-20:i]),min(L[i-20:i])
            swh=Hh[i]>ph and C[i]<ph and relv>=1.5; swl=L[i]<pl and C[i]>pl and relv>=1.5
            vdacc=sum(vd[i-2:i+1])
            is_entry=(trend,posb,relv>=1.5,bool(swh or swl))!=prev
            prev=(trend,posb,relv>=1.5,bool(swh or swl))
            if not is_entry: continue
            cands=[]
            if swl: cands.append((+1,"S1_stoprun"));
            if swh: cands.append((-1,"S1_stoprun"))
            if relv<=0.6 and trend=="down" and posb=="low": cands.append((+1,"S2_dryexh"))
            if relv<=0.6 and trend=="up" and posb=="high": cands.append((-1,"S2_dryexh"))
            if relv>=1.8 and expb and posb=="high" and C[i]>O[i]: cands.append((+1,"S3_partbreak"))
            if relv>=1.8 and expb and posb=="low" and C[i]<O[i]: cands.append((-1,"S3_partbreak"))
            if absb and posb=="low": cands.append((+1,"S4_absorb"))
            if absb and posb=="high": cands.append((-1,"S4_absorb"))
            if posb=="high" and vdacc<0: cands.append((-1,"S5_vdelta"))
            if posb=="low" and vdacc>0: cands.append((+1,"S5_vdelta"))
            day=T[i][:10]; yr=T[i][:4]
            for d,fam in cands:
                g=giveback_exit(C,i,d,atr,c,n); cap=capture_exit(O,Hh,L,C,i,d,atr,c,n)
                day_give[day]+=g; day_cap[day]+=cap
                fam_give[fam]+=g; fam_cap[fam]+=cap
                year_give[yr]+=g; year_cap[yr]+=cap
                n_trades+=1
    days=sorted(set(day_give)|set(day_cap))
    def stats(dd):
        vals=[dd[x] for x in days]
        return {"total_R":round(sum(vals),1),"per_day":round(statistics.fmean(vals),3),
                "pos_days_pct":round(sum(1 for v in vals if v>0)/len(vals),3),
                "worst_day":round(min(vals),2),"best_day":round(max(vals),2)}
    out={"schema_version":"portfolio_capture_v1","trades":n_trades,"trading_days":len(days),
         "GIVEBACK_exit":stats(day_give),"CAPTURE_exit":stats(day_cap),
         "by_year":{y:{"giveback_R":round(year_give[y],1),"capture_R":round(year_cap[y],1)} for y in sorted(year_cap)},
         "by_family":{fam:{"giveback_R":round(fam_give[fam],1),"capture_R":round(fam_cap[fam],1)} for fam in sorted(fam_cap)},
         "broker_operation":False,"paid_api_or_vendor_call":False,"broker_runtime_change_status":False,
         "validation_result_status":False,"outcome_result_rows_status":False}
    (ROUTE/"ULTIMATE_PORTFOLIO_CAPTURE.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print("PORTFOLIO (all families, 2022-2026 H4):", json.dumps({"trades":n_trades,"days":len(days)}))
    print("  GIVEBACK exit:", out["GIVEBACK_exit"])
    print("  CAPTURE  exit:", out["CAPTURE_exit"])
    print("  by year:", json.dumps(out["by_year"]))
    print("  by family:", json.dumps(out["by_family"]))


if __name__=="__main__":
    main()
