"""
hunt_key_level_reaction_v2.py
=============================
Sharper key-level reaction hunter. v1 (naive: fire on any touch of any level)
was uniformly NEGATIVE in train AND forward across every level family and exit,
long and short symmetric -> pure cost bleed, no raw edge surfaced.

v2 adds:
  (1) NO-COST diagnostic: does ANY raw geometric edge exist before cost?
  (2) Tight quality filters: rejection wick strength, decisive close-back,
      level "freshness" (recently created / few prior touches), bar range sanity.
  (3) Regime filter: fade only counter to weak momentum; break-retest only with trend.
  (4) Confluence: require >=2 level families coincide within a tolerance.
  (5) Per-asset-class & per-year forward reporting, long/short separate.

ALL fills via tested geometry_lib.simulate. Real per-asset cost.
TRAIN 2022-2024 / FORWARD 2025-2026.
"""
from __future__ import annotations
import sys, os, csv, json, math
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GLOBAL_COST = COSTMAP["_global_median"]
def cost_for(sym): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(sym), GLOBAL_COST)

def load(sym):
    path = f"{DATA}/{sym}_H4.csv"
    if not os.path.exists(path): return None, None
    times, bars = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                bars.append(Bar(float(row["open"]),float(row["high"]),float(row["low"]),
                                float(row["close"]),float(row.get("volume",0) or 0)))
                times.append(t)
            except Exception: continue
    return times, bars

SYMBOLS = [fn[:-7] for fn in sorted(os.listdir(DATA)) if fn.endswith("_H4.csv")]

def build_day_week_levels(times, bars):
    n=len(bars)
    day_key=[t.date() for t in times]; week_key=[t.isocalendar()[:2] for t in times]
    pdh=[None]*n; pdl=[None]*n; pwh=[None]*n; pwl=[None]*n
    cur_day=None;cdh=cdl=None;ldh=ldl=None
    cur_w=None;cwh=cwl=None;lwh=lwl=None
    for i in range(n):
        if day_key[i]!=cur_day:
            if cur_day is not None: ldh=cdh; ldl=cdl
            cur_day=day_key[i]; cdh=bars[i].h; cdl=bars[i].l
        else: cdh=max(cdh,bars[i].h); cdl=min(cdl,bars[i].l)
        if week_key[i]!=cur_w:
            if cur_w is not None: lwh=cwh; lwl=cwl
            cur_w=week_key[i]; cwh=bars[i].h; cwl=bars[i].l
        else: cwh=max(cwh,bars[i].h); cwl=min(cwl,bars[i].l)
        pdh[i]=ldh; pdl[i]=ldl; pwh[i]=lwh; pwl[i]=lwl
    return pdh,pdl,pwh,pwl

def round_levels_near(price):
    if price<=0: return None,None
    mag=math.floor(math.log10(abs(price))); step=10**(mag-1)
    if step<=0: return None,None
    below=math.floor(price/step)*step; return below, below+step

def _stats(rs):
    if not rs: return {"n":0,"mean_R":0.0,"win%":0.0,"sum_R":0.0,"median_R":0.0}
    n=len(rs); s=sum(rs); w=sum(1 for r in rs if r>0); sr=sorted(rs)
    return {"n":n,"mean_R":round(s/n,4),"win%":round(100*w/n,1),"sum_R":round(s,1),
            "median_R":round(sr[n//2],4)}

def run_config(cfg):
    levels=cfg["levels"]; mode=cfg["mode"]; tol_atr=cfg["tol_atr"]
    stop_mult=cfg["stop_mult"]; exit_mode=cfg["exit"]
    wick_min=cfg.get("wick_min",0.0)        # rejection wick >= wick_min*atr
    closeback=cfg.get("closeback",0.0)      # close must be >= closeback*atr past level (back inside)
    body_max=cfg.get("body_max",1e9)        # body <= body_max*atr (reject = small body big wick)
    confluence=cfg.get("confluence",1)      # min # level families coinciding
    conf_tol_atr=cfg.get("conf_tol_atr",0.5)
    regime=cfg.get("regime",None)           # None / 'fade_weak' / 'trend'
    regime_lb=cfg.get("regime_lb",10)
    fresh_max_touch=cfg.get("fresh_max_touch",1e9)  # eqhl: max prior touches (freshness)
    eqhl_lb=cfg.get("eqhl_lb",3); eqhl_tol_atr=cfg.get("eqhl_tol_atr",0.15)
    diag_nocost=cfg.get("diag_nocost",False)

    agg=defaultdict(list); by_class=defaultdict(lambda:defaultdict(list)); by_year=defaultdict(lambda:defaultdict(list))

    for sym in SYMBOLS:
        times,bars=load(sym)
        if not bars or len(bars)<200: continue
        ac=ASSET_CLASS_BY_SYMBOL.get(sym,"?"); cost=0.0 if diag_nocost else cost_for(sym)
        n=len(bars); pdh,pdl,pwh,pwl=build_day_week_levels(times,bars)
        atrs=[atr14(bars,i) for i in range(n)]

        sw_hi=[]; sw_lo=[]
        for k in range(eqhl_lb,n-eqhl_lb):
            seg=bars[k-eqhl_lb:k+eqhl_lb+1]
            if bars[k].h==max(b.h for b in seg) and bars[k].h>bars[k-1].h and bars[k].h>=bars[k+1].h: sw_hi.append(k)
            if bars[k].l==min(b.l for b in seg) and bars[k].l<bars[k-1].l and bars[k].l<=bars[k+1].l: sw_lo.append(k)
        sw_hi.sort(); sw_lo.sort()
        hp=lp=0; ch=[]; chk=[]; cl=[]; clk=[]

        for i in range(60,n-1):
            atr=atrs[i]
            if atr<=0: continue
            b=bars[i]; price=b.c
            while hp<len(sw_hi) and sw_hi[hp]+eqhl_lb<i: ch.append(bars[sw_hi[hp]].h); chk.append(sw_hi[hp]); hp+=1
            while lp<len(sw_lo) and sw_lo[lp]+eqhl_lb<i: cl.append(bars[sw_lo[lp]].l); clk.append(sw_lo[lp]); lp+=1
            tol=tol_atr*atr; ctol=conf_tol_atr*atr; etol=eqhl_tol_atr*atr

            res=[]; sup=[]
            if 'pd' in levels:
                if pdh[i] is not None: res.append(('pdh',pdh[i]))
                if pdl[i] is not None: sup.append(('pdl',pdl[i]))
            if 'pw' in levels:
                if pwh[i] is not None: res.append(('pwh',pwh[i]))
                if pwl[i] is not None: sup.append(('pwl',pwl[i]))
            if 'round' in levels:
                bel,ab=round_levels_near(price)
                if ab is not None: res.append(('rnd',ab))
                if bel is not None: sup.append(('rnd',bel))
            if 'eqhl' in levels:
                cand=[(p,k) for p,k in zip(ch,chk) if p>=price-tol]
                if cand:
                    cand.sort(); lvl=cand[0][0]
                    nt=sum(1 for p in ch if abs(p-lvl)<=etol)
                    if nt<=fresh_max_touch: res.append(('eqh',lvl))
                cand=[(p,k) for p,k in zip(cl,clk) if p<=price+tol]
                if cand:
                    cand.sort(reverse=True); lvl=cand[0][0]
                    nt=sum(1 for p in cl if abs(p-lvl)<=etol)
                    if nt<=fresh_max_touch: sup.append(('eql',lvl))

            yr=times[i].year

            # regime: momentum over last regime_lb bars (close vs close)
            mom=0.0
            if i-regime_lb>=0: mom=(b.c-bars[i-regime_lb].c)/atr

            # ---- REJECTION ----
            if mode=='reject':
                # overhead resistance -> SHORT
                for name,lvl in res:
                    if b.h>=lvl-tol:
                        upwick=b.h-max(b.o,b.c)
                        body=abs(b.c-b.o)
                        if upwick>=wick_min*atr and body<=body_max*atr and (lvl-b.c)>=closeback*atr and b.c<lvl and b.c<b.o:
                            if confluence>1:
                                nconf=sum(1 for nm,lv in res if abs(lv-lvl)<=ctol)
                                if nconf<confluence: continue
                            if regime=='fade_weak' and mom>1.0: continue   # don't fade strong up-trend
                            if regime=='trend' and mom>-0.5: continue
                            sd=stop_mult*atr if stop_mult else max((b.h-b.c)+0.25*atr,0.2*atr)
                            _emit(-1,sym,ac,'short',i,bars,sd,exit_mode,cost,agg,by_class,by_year,yr,diag_nocost)
                # underfoot support -> LONG
                for name,lvl in sup:
                    if b.l<=lvl+tol:
                        dnwick=min(b.o,b.c)-b.l
                        body=abs(b.c-b.o)
                        if dnwick>=wick_min*atr and body<=body_max*atr and (b.c-lvl)>=closeback*atr and b.c>lvl and b.c>b.o:
                            if confluence>1:
                                nconf=sum(1 for nm,lv in sup if abs(lv-lvl)<=ctol)
                                if nconf<confluence: continue
                            if regime=='fade_weak' and mom<-1.0: continue
                            if regime=='trend' and mom<0.5: continue
                            sd=stop_mult*atr if stop_mult else max((b.c-b.l)+0.25*atr,0.2*atr)
                            _emit(+1,sym,ac,'long',i,bars,sd,exit_mode,cost,agg,by_class,by_year,yr,diag_nocost)

            # ---- BREAK-RETEST ----
            elif mode=='breakretest':
                W=cfg.get("retest_window",6)
                for name,lvl in res:
                    broke=any(bars[j].c>lvl+0.1*tol for j in range(max(0,i-W),i))
                    if broke and b.l<=lvl+tol and b.c>lvl and b.c>b.o:
                        if regime=='trend' and mom<0.5: continue
                        sd=stop_mult*atr if stop_mult else max(b.c-min(b.l,lvl-0.25*atr),0.2*atr)
                        _emit(+1,sym,ac,'long',i,bars,sd,exit_mode,cost,agg,by_class,by_year,yr,diag_nocost)
                for name,lvl in sup:
                    broke=any(bars[j].c<lvl-0.1*tol for j in range(max(0,i-W),i))
                    if broke and b.h>=lvl-tol and b.c<lvl and b.c<b.o:
                        if regime=='trend' and mom>-0.5: continue
                        sd=stop_mult*atr if stop_mult else max(max(b.h,lvl+0.25*atr)-b.c,0.2*atr)
                        _emit(-1,sym,ac,'short',i,bars,sd,exit_mode,cost,agg,by_class,by_year,yr,diag_nocost)

    return _summarize(agg,by_class,by_year)

def _emit(direction,sym,ac,side,i,bars,sd,exit_mode,cost,agg,by_class,by_year,yr,diag):
    if sd<=0: return
    if exit_mode[0]=='target':
        r=simulate(bars,i,direction,stop_dist=sd,target_dist=exit_mode[1]*sd,cost=cost)
    else:
        r=simulate(bars,i,direction,stop_dist=sd,trail_arm=exit_mode[1]*sd,trail_gap=exit_mode[2]*sd,cost=cost)
    period='train' if yr<=2024 else 'forward'
    agg[(period,side)].append(r); agg[(period,'all')].append(r)
    by_class[ac][(period,side)].append(r); by_class[ac][(period,'all')].append(r)
    by_year[yr][side].append(r); by_year[yr]['all'].append(r)

def _summarize(agg,by_class,by_year):
    out={"overall":{},"by_class":{},"by_year":{}}
    for k in [('train','all'),('train','long'),('train','short'),('forward','all'),('forward','long'),('forward','short')]:
        out["overall"]["_".join(k)]=_stats(agg.get(k,[]))
    for ac,d in by_class.items():
        out["by_class"][ac]={"forward_all":_stats(d.get(('forward','all'),[])),
            "forward_long":_stats(d.get(('forward','long'),[])),
            "forward_short":_stats(d.get(('forward','short'),[])),
            "train_all":_stats(d.get(('train','all'),[]))}
    for yr,d in sorted(by_year.items()):
        out["by_year"][str(yr)]={"all":_stats(d.get('all',[])),"long":_stats(d.get('long',[])),"short":_stats(d.get('short',[]))}
    return out

def pl(tag,res):
    ov=res["overall"]
    print(f"=== {tag} ===")
    print(f"  TRAIN  all n={ov['train_all']['n']:6d} R={ov['train_all']['mean_R']:+.4f} w={ov['train_all']['win%']:.1f}%")
    print(f"  FWD    all n={ov['forward_all']['n']:6d} R={ov['forward_all']['mean_R']:+.4f} w={ov['forward_all']['win%']:.1f}%"
          f"  | long n={ov['forward_long']['n']:5d} R={ov['forward_long']['mean_R']:+.4f}"
          f"  | short n={ov['forward_short']['n']:5d} R={ov['forward_short']['mean_R']:+.4f}")

def main():
    results={}
    # ---------- (1) NO-COST diagnostic: any raw edge in the geometry? ----------
    print("\n########## NO-COST DIAGNOSTIC (does raw geometry have ANY edge?) ##########")
    for lv in [('pd','pw'),('eqhl',),('pd','pw','round','eqhl')]:
        for ex in [('target',1.0),('target',2.0),('trail',2.0,1.0)]:
            cfg={"levels":lv,"mode":"reject","tol_atr":0.25,"stop_mult":0.5,"exit":ex,
                 "diag_nocost":True,"eqhl_lb":3,"multitouch":1}
            tag=f"NOCOST reject|{'+'.join(lv)}|{ex}"
            res=run_config(cfg); pl(tag,res); results[tag]={"cfg":{k:v for k,v in cfg.items()},"result":res}

    # ---------- (2) Tight quality-filtered rejection (with cost) ----------
    print("\n########## TIGHT QUALITY REJECTION (with real cost) ##########")
    grid=[]
    for lv in [('pd','pw'),('eqhl',),('pd','pw','round','eqhl')]:
        for wick in [0.5,0.8]:
            for cb in [0.1,0.3]:
                for ex in [('target',2.0),('trail',2.0,1.0)]:
                    grid.append({"levels":lv,"mode":"reject","tol_atr":0.20,"stop_mult":0.5,"exit":ex,
                        "wick_min":wick,"closeback":cb,"body_max":0.6,
                        "regime":"fade_weak","regime_lb":10,
                        "eqhl_lb":3,"eqhl_tol_atr":0.15,"fresh_max_touch":3})
    for cfg in grid:
        tag=f"Qrej|{'+'.join(cfg['levels'])}|wick{cfg['wick_min']}|cb{cfg['closeback']}|{cfg['exit']}"
        res=run_config(cfg); pl(tag,res); results[tag]={"cfg":cfg,"result":res}

    # ---------- (3) Confluence rejection ----------
    print("\n########## CONFLUENCE REJECTION (>=2 families, with cost) ##########")
    for ex in [('target',2.0),('trail',2.0,1.0)]:
        cfg={"levels":('pd','pw','round','eqhl'),"mode":"reject","tol_atr":0.25,"stop_mult":0.5,"exit":ex,
             "wick_min":0.5,"closeback":0.1,"body_max":0.7,"confluence":2,"conf_tol_atr":0.5,
             "regime":"fade_weak","regime_lb":10,"eqhl_lb":3,"fresh_max_touch":3}
        tag=f"CONFLUENCE|{cfg['exit']}"
        res=run_config(cfg); pl(tag,res); results[tag]={"cfg":cfg,"result":res}

    # ---------- (4) Trend break-retest ----------
    print("\n########## TREND BREAK-RETEST (with cost) ##########")
    for lv in [('pd','pw'),('eqhl',),('pd','pw','round','eqhl')]:
        for ex in [('target',2.0),('trail',2.0,1.0)]:
            cfg={"levels":lv,"mode":"breakretest","tol_atr":0.25,"stop_mult":0.5,"exit":ex,
                 "regime":"trend","regime_lb":10,"retest_window":6,"eqhl_lb":3,"fresh_max_touch":5}
            tag=f"TRENDbr|{'+'.join(lv)}|{ex}"
            res=run_config(cfg); pl(tag,res); results[tag]={"cfg":cfg,"result":res}

    with open(EDGE+"/HUNT_KEY_LEVEL_REACTION_V2_RESULT.json","w") as f:
        json.dump(results,f,indent=1)
    print("\nWROTE HUNT_KEY_LEVEL_REACTION_V2_RESULT.json")

if __name__=="__main__":
    main()
